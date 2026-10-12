"""Independent ANZ PDF goldens own complete numbers and source metadata."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_anz_historical_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    bundle = run_extractor(
        project_root / "extractions/au/anz/2024-09-30/aps330/extract.py",
        project_root / "raw/anz-2024-09-30-aps330.pdf",
    )
    assert bundle.schema_version == "disclosure-v3"
    assert len(bundle.datasets) == 4
    assert sum(len(t.cells) for t in bundle.datasets) == 125
    assert bundle.document.document_reporting_date.isoformat() == "2024-09-30"
    for table in bundle.datasets:
        context = table.metadata.context
        assert context.reporting_entity.value == "ANZ BH Pty Ltd (ANZ Bank HoldCo)"
        assert context.consolidation_scope.value == "Level 2"
        assert context.regulatory_scope.value == "AIRB"
        assert context.currency.value == "AUD"
        assert context.geography.status == "unresolved"
        notes = {q.id: q for q in table.metadata.qualifications}
        for key in (
            "report-entity",
            "level-2",
            "currency",
            "suncorp",
            "regulatory-basis",
            "default-definition",
            "ead-net-offsets",
        ):
            assert key in notes
        for key in notes.keys() & golden["notes"].keys():
            page, text = golden["notes"][key]
            assert notes[key].source_text == text
            assert notes[key].evidence[0].pdf_page == page
            assert notes[key].evidence[0].printed_page == str(page - 1)
    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        meta = table.metadata
        assert table.id == "table9d-" + expected["date"]
        assert len(table.cells) == 40
        assert meta.context.source_date_label == expected["label"]
        axes = {a.id: a for a in meta.axes}
        assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
            "bands"
        ]
        assert axes["band-0"].header_path_refs == ("panel",)
        assert axes["band-0"].qualification_refs == ("pd-definition",)
        fields = {f.id: f for f in meta.published_fields}
        assert len(fields) == 5
        for spec, tokens in zip(golden["fields"], expected["rows"], strict=True):
            key, label, unit, scale, precision = spec
            f = fields[key]
            assert (f.source_label, f.source_unit, str(f.source_scale)) == (
                label,
                unit,
                scale,
            )
            assert f.header_path_refs == ("panel", key)
            assert f.source_reference.row == label
            assert f.source_form == "table_body"
            assert axes[key + "-mortgage"].header_path_refs == ("panel", key)
            assert axes[key + "-mortgage"].source_label == "Residential Mortgage"
            cells = [c for c in table.cells if c.field_ref == key]
            assert [c.value.original_text for c in cells] == tokens
            assert [c.column_ref for c in cells] == [f"band-{i}" for i in range(8)]
            for i, (c, token) in enumerate(zip(cells, tokens, strict=True)):
                assert c.row_ref == key + "-mortgage"
                assert c.segment_refs == (f"band-{i}",)
                assert c.value.value == Decimal(token.replace(",", "").rstrip("%"))
                assert c.value.displayed_precision == precision
                assert c.value.missing_reason is None
                assert c.value.source_reference.pdf_page == expected["page"]
                assert c.value.source_reference.column == golden["bands"][i]
        assert fields["average_ead"].attributes[0].status == "unresolved"
        assert "lgd-definition" in fields["lgd"].qualification_refs
        notes = {q.id: q for q in meta.qualifications}
        assert {
            "pd-definition",
            "ead-definition",
            "ead-glossary",
            "lgd-definition",
            "regulatory-adjustments",
        } <= notes.keys()
        assert notes["undrawn"].source_text == "Undrawn commitments (included in above)"
        assert [(e.kind, e.id) for e in notes["undrawn"].scope] == [
            ("field", "undrawn")
        ]
        bands = meta.segmentations[0].bands
        assert [b.source_label for b in bands] == golden["bands"]
        for band, bounds in zip(bands, golden["bounds"], strict=True):
            assert [
                str(v) if v is not None else None for v in (band.lower, band.upper)
            ] == bounds
            assert band.lower_inclusive is None
        assert all(b.upper_inclusive is False for b in bands[:6])
        assert (bands[6].kind, bands[7].kind) == ("default", "category")
        subsets = [r for r in meta.relationships if r.kind == "subset"]
        totals = [r for r in meta.relationships if r.kind == "total"]
        assert len(subsets) == 8 and len(totals) == 5
        for i, rel in enumerate(subsets):
            assert (rel.parent.kind, rel.parent.id) == ("cell", f"exposure/band-{i}")
            assert [(e.kind, e.id) for e in rel.children] == [
                ("cell", f"undrawn/band-{i}")
            ]
        for rel, spec in zip(totals, golden["fields"], strict=True):
            assert (rel.parent.kind, rel.parent.id) == ("cell", spec[0] + "/band-7")
            assert [e.id for e in rel.children] == [
                spec[0] + f"/band-{i}" for i in range(7)
            ]
        assert all(
            r.exhaustive is None and r.mutually_exclusive is None
            for r in meta.relationships
        )
        assert len(meta.temporal_bindings) == 40
        assert all(b.role == "measurement" for b in meta.temporal_bindings)
        assert meta.temporal_descriptors[0].point == expected["date"]

    table = bundle.datasets[3]
    meta = table.metadata
    assert table.id == "table9f-2024-09-30"
    assert not meta.segmentations and not meta.relationships
    assert len(table.cells) == 5
    for c, f, spec in zip(
        table.cells, meta.published_fields, golden["backtesting"], strict=True
    ):
        key, label, unit, token = spec
        assert (f.id, f.source_label, f.source_unit) == (key, label, unit)
        assert f.header_path_refs == ("panel", key)
        assert c.field_ref == key and c.row_ref == "mortgage" and c.column_ref == key
        assert c.value.original_text == token
        assert c.value.value == Decimal(token) and c.value.displayed_precision == 2
        assert c.value.source_reference.pdf_page == 57
    notes = {q.id: q for q in meta.qualifications}
    assert {"pd-history", "ead-history", "lgd-history", "lgd-review"} <= notes.keys()
    assert notes["lgd-review"].scope == ()
    assert notes["lgd-review"].evidence[0].location == "Wholesale Portfolios"
    fields = {f.id: f for f in meta.published_fields}
    assert fields["actual_lgd"].attributes[0].status == "unresolved"
    for key, field_ids in (
        ("pd-history", ["estimated_pd", "actual_pd"]),
        ("ead-history", ["ead_ratio"]),
        ("lgd-history", ["estimated_lgd", "actual_lgd"]),
    ):
        assert [(e.kind, e.id) for e in notes[key].scope] == [
            ("field", f) for f in field_ids
        ]
    ds = {d.id: d for d in meta.temporal_descriptors}
    assert (ds["pd-ead-history"].start, ds["pd-ead-history"].end) == ("2019", "2023")
    assert (ds["lgd-history"].start, ds["lgd-history"].end) == ("2018", "2022")
    assert ds["default-cutoff"].end == "2023-09"
    assert ds["default-cutoff"].start is None
    assert {(b.cell_id, b.role, b.descriptor_ref) for b in meta.temporal_bindings} == {
        ("mortgage/estimated_pd", "history_window", "pd-ead-history"),
        ("mortgage/actual_pd", "history_window", "pd-ead-history"),
        ("mortgage/ead_ratio", "history_window", "pd-ead-history"),
        ("mortgage/estimated_lgd", "history_window", "lgd-history"),
        ("mortgage/actual_lgd", "history_window", "lgd-history"),
        ("mortgage/actual_pd", "outcome_window", "default-cutoff"),
        ("mortgage/estimated_lgd", "outcome_window", "default-cutoff"),
        ("mortgage/actual_lgd", "outcome_window", "default-cutoff"),
    }
