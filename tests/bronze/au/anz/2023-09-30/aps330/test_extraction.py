"""Independent PDF expectations for the reform-spanning ANZ mortgage panels."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_anz_2023_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    extractor = project_root / "extractions/au/anz/2023-09-30/aps330/extract.py"
    assert extractor.exists(), "2023 source capture is not implemented"
    bundle = run_extractor(extractor, project_root / "raw/anz-2023-09-30-aps330.pdf")
    assert bundle.schema_version == "disclosure-v4"
    assert len(bundle.datasets) == 4
    assert sum(len(t.cells) for t in bundle.datasets) == 125
    assert bundle.document.document_reporting_date.isoformat() == "2023-09-30"
    captured = {(f.binding_ref, f.slot): f for f in bundle.fragments}
    field_binding = next(
        b
        for b in bundle.snapshot.occurrences
        if b.ref.scope == "table9f-2023-09-30"
        and b.ref.kind == "field"
        and b.ref.local_id == "estimated_pd"
    )
    assert field_binding.physical_refs, (
        "Published headers must be captured, not substituted with declared labels"
    )
    location = field_binding.physical_refs[0]
    assert (
        captured[(location.binding_ref, location.slot)].text == "Average Estimated PD %"
    )
    captured_notes = set()
    for table in bundle.datasets:
        meta = table.metadata
        context = meta.context
        assert context.reporting_entity.value == (
            "Australia and New Zealand Banking Group Limited"
            if table.id == "table9d-2022-09-30"
            else "ANZ BH Pty Ltd (ANZ Bank HoldCo)"
        )
        assert context.reporting_entity.status == "established"
        assert context.consolidation_scope.value == "Level 2"
        assert context.regulatory_scope.value == "AIRB"
        assert context.currency.value == "AUD"
        assert context.geography.status == "unresolved"
        notes = {q.id: q for q in meta.qualifications}
        assert {
            "report-entity",
            "level-2",
            "currency",
            "restructure",
            "comparative-basis",
            "nz-separation",
            "regulatory-basis",
            "default-definition",
        } <= notes.keys()
        assert "3 January 2023" in notes["restructure"].source_text
        for key in notes.keys() & golden["notes"].keys():
            captured_notes.add(key)
            page, text = golden["notes"][key]
            assert notes[key].source_text == text, (table.id, key)
            assert notes[key].evidence[0].pdf_page == page
            assert notes[key].evidence[0].printed_page == str(page - 1)
        assert all(q.scope for q in meta.qualifications if q.id != "lgd-review")
    assert captured_notes == golden["notes"].keys()
    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        meta = table.metadata
        assert table.id == "table9d-" + expected["date"]
        assert meta.context.source_date_label == expected["label"]
        axes = {a.id: a for a in meta.axes}
        assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
            "bands"
        ]
        assert len(table.cells) == 40
        assert len(meta.published_fields) == 5
        for f, spec, tokens in zip(
            meta.published_fields, golden["fields"], expected["rows"], strict=True
        ):
            key, label, unit, scale, precision = spec
            assert (f.id, f.source_label, f.source_unit, str(f.source_scale)) == (
                key,
                label,
                unit,
                scale,
            )
            assert f.header_path_refs == ("panel", key)
            assert f.source_form == "table_body"
            assert axes[key + "-mortgage"].header_path_refs == ("panel", key)
            cells = [c for c in table.cells if c.field_ref == key]
            assert [c.value.original_text for c in cells] == tokens
            for j, (c, token) in enumerate(zip(cells, tokens, strict=True)):
                assert (c.row_ref, c.column_ref, c.segment_refs) == (
                    key + "-mortgage",
                    f"band-{j}",
                    (f"band-{j}",),
                )
                assert c.value.value == Decimal(token.replace(",", "").rstrip("%"))
                assert c.value.displayed_precision == precision
                assert c.value.missing_reason is None
                assert c.value.source_reference.pdf_page == expected["page"]
                assert c.value.source_reference.column == golden["bands"][j]
        assert meta.published_fields[2].attributes[0].status == "unresolved"
        bands = meta.segmentations[0].bands
        assert [b.source_label for b in bands] == golden["bands"]
        assert [
            [str(v) if v is not None else None for v in (b.lower, b.upper)]
            for b in bands
        ] == golden["bounds"]
        assert all(b.lower_inclusive is None for b in bands)
        assert all(b.upper_inclusive is False for b in bands[:6])
        assert (bands[6].kind, bands[7].kind) == ("default", "category")
        subsets = [r for r in meta.relationships if r.kind == "subset"]
        totals = [r for r in meta.relationships if r.kind == "total"]
        assert len(subsets) == 8 and len(totals) == 5
        for j, r in enumerate(subsets):
            assert r.parent.id == f"exposure/band-{j}"
            assert [e.id for e in r.children] == [f"undrawn/band-{j}"]
        for r, spec in zip(totals, golden["fields"], strict=True):
            assert r.parent.id == spec[0] + "/band-7"
            assert [e.id for e in r.children] == [
                spec[0] + f"/band-{j}" for j in range(7)
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
    assert table.id == "table9f-2023-09-30"
    assert not meta.segmentations and not meta.relationships
    for c, f, spec in zip(
        table.cells, meta.published_fields, golden["backtesting"], strict=True
    ):
        key, label, unit, token = spec
        assert (f.id, f.source_label, f.source_unit) == (key, label, unit)
        assert (c.field_ref, c.row_ref, c.column_ref) == (key, "mortgage", key)
        assert c.value.original_text == token
        assert c.value.value == Decimal(token) and c.value.displayed_precision == 2
        assert c.value.source_reference.pdf_page == 56
    notes = {q.id: q for q in meta.qualifications}
    assert notes["lgd-review"].scope == ()
    assert meta.published_fields[-1].attributes[0].status == "unresolved"
    for key, fields in (
        ("pd-history", ["estimated_pd", "actual_pd"]),
        ("ead-history", ["ead_ratio"]),
        ("lgd-history", ["estimated_lgd", "actual_lgd"]),
    ):
        assert [(e.kind, e.id) for e in notes[key].scope] == [
            ("field", f) for f in fields
        ]
    ds = {d.id: d for d in meta.temporal_descriptors}
    assert (ds["pd-history"].start, ds["pd-history"].end) == ("2018", "2022")
    assert (ds["ead-history"].start, ds["ead-history"].end) == ("2018", "2023")
    assert (ds["lgd-history"].start, ds["lgd-history"].end) == ("2017", "2021")
    assert ds["pd-cutoff"].end == "2023-09" and ds["pd-cutoff"].start is None
    assert ds["lgd-cutoff"].end == "2022-09" and ds["lgd-cutoff"].start is None
    assert {(b.cell_id, b.role, b.descriptor_ref) for b in meta.temporal_bindings} == {
        ("mortgage/estimated_pd", "history_window", "pd-history"),
        ("mortgage/actual_pd", "history_window", "pd-history"),
        ("mortgage/ead_ratio", "history_window", "ead-history"),
        ("mortgage/estimated_lgd", "history_window", "lgd-history"),
        ("mortgage/actual_lgd", "history_window", "lgd-history"),
        ("mortgage/actual_pd", "outcome_window", "pd-cutoff"),
        ("mortgage/estimated_lgd", "outcome_window", "lgd-cutoff"),
        ("mortgage/actual_lgd", "outcome_window", "lgd-cutoff"),
    }
