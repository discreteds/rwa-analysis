"""Independent source expectations for the reform-boundary CBA mortgage panels."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_cba_2023_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    path = project_root / "extractions/au/cba/2023-06-30/aps330/extract.py"
    assert path.exists(), "CBA 2023 source capture is not implemented"
    bundle = run_extractor(path, project_root / "raw/cba-2023-06-30-aps330.pdf")
    assert bundle.schema_version == "disclosure-v3"
    assert bundle.document.document_reporting_date.isoformat() == "2023-06-30"
    assert len(bundle.datasets) == 5
    assert [len(t.cells) for t in bundle.datasets] == [42, 41, 41, 2, 3]
    for table in bundle.datasets:
        meta = table.metadata
        assert (
            meta.context.reporting_entity.value
            == "CBA and its subsidiaries (the Group)"
        )
        assert meta.context.consolidation_scope.value == "Level 2"
        assert meta.context.regulatory_scope.value == "IRB"
        assert meta.context.geography.status == "unresolved"
        assert meta.context.currency.status == "unresolved"
        notes = {q.id: q for q in meta.qualifications}
        for key, page in (
            ("report-entity", 4),
            ("level-2", 4),
            ("regulatory-basis", 45),
        ):
            assert notes[key].evidence[0].pdf_page == page
            assert [(s.kind, s.id) for s in notes[key].scope] == [("dataset", table.id)]
        for q in meta.qualifications:
            if q.id in golden["notes"]:
                assert q.source_text == golden["notes"][q.id]
    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        assert table.id == "table9d-ii-" + expected["date"]
        meta = table.metadata
        assert meta.context.source_date_label == expected["label"]
        axes = {a.id: a for a in meta.axes}
        assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
            "bands"
        ]
        assert axes["band-0"].header_path_refs == ("panel", "pd-bands")
        assert axes["lgd-mortgage"].source_label == expected["lgd_row"]
        fields = {f.id: f for f in meta.published_fields}
        assert (
            set(fields) == {f[0] for f in golden["fields"]} | expected["notes"].keys()
        )
        for spec, marker, tokens in zip(
            golden["fields"], expected["markers"], expected["rows"], strict=True
        ):
            key, label, unit, scale, precision = spec
            f = fields[key]
            assert (f.source_label, f.source_unit, str(f.source_scale)) == (
                label + marker,
                unit,
                scale,
            )
            assert f.header_path_refs == ("panel", key)
            assert f.source_reference.row == label + marker
            assert axes[key + "-mortgage"].header_path_refs == ("panel", key)
            cells = [c for c in table.cells if c.field_ref == key]
            assert [c.value.original_text for c in cells] == tokens
            assert [c.column_ref for c in cells] == [f"band-{i}" for i in range(8)]
            for c, token in zip(cells, tokens, strict=True):
                assert c.row_ref == key + "-mortgage"
                assert c.value.value == Decimal(token.replace(",", ""))
                assert c.value.displayed_precision == precision
                assert c.value.missing_reason is None
                assert c.value.source_reference.pdf_page == expected["page"]
                assert c.value.source_reference.printed_page == str(
                    expected["page"] - 2
                )
        notes = {q.id: q for q in meta.qualifications}
        for key, page in (
            ("pd-horizon", 45),
            ("pd-long-run", 45),
            ("lgd-definition", 46),
            ("lgd-downturn", 46),
            ("default-definition", 46),
            ("ead-definition", 46),
        ):
            assert notes[key].evidence[0].pdf_page == page
        assert [(s.kind, s.id) for s in notes["pd-horizon"].scope] == [
            ("band", f"band-{j}") for j in range(7)
        ]
        assert [(s.kind, s.id) for s in notes["lgd-downturn"].scope] == [
            ("field", "lgd")
        ]
        assert fields["average_ead"].attributes[0].status == "unresolved"
        assert fields["risk_weight"].qualification_refs == ("scaling",)
        assert (
            notes["scaling"].source_text
            == f"Includes {expected['notes']['scaling']} scaling factor."
        )
        assert ("overlay" in notes) == (expected["date"] == "2023-06-30")
        if "overlay" in notes:
            assert [(s.kind, s.id) for s in notes["overlay"].scope] == [
                ("field", "lgd")
            ]
            assert "revised-framework" in meta.context.qualification_refs
        else:
            assert "revised-framework" not in notes
            assert "prior-framework" in meta.context.qualification_refs
            assert notes["prior-framework"].evidence[0].pdf_page == 5
        for key, token in expected["notes"].items():
            c = next(c for c in table.cells if c.field_ref == key)
            assert fields[key].source_form == "note"
            assert (c.row_ref, c.column_ref) == (None, None)
            assert c.qualification_refs == (key,)
            assert c.value.original_text == token
        for b, bounds in zip(
            meta.segmentations[0].bands, golden["bounds"], strict=True
        ):
            assert [
                str(b.lower) if b.lower is not None else None,
                str(b.upper) if b.upper is not None else None,
            ] == bounds
            assert b.lower_inclusive is None
        assert all(b.upper_inclusive is False for b in meta.segmentations[0].bands[:6])
        subsets = [r for r in meta.relationships if r.kind == "subset"]
        assert len(subsets) == 8
        for j, r in enumerate(subsets):
            assert (r.parent.kind, r.parent.id) == ("cell", f"exposure/band-{j}")
            assert [(e.kind, e.id) for e in r.children] == [
                ("cell", f"undrawn/band-{j}")
            ]
            assert r.exhaustive is None and r.mutually_exclusive is None
        assert len([r for r in meta.relationships if r.kind == "total"]) == 5
        assert meta.temporal_descriptors[0].point == expected["date"]
        assert len(meta.temporal_bindings) == len(table.cells)
        assert all(b.role == "measurement" for b in meta.temporal_bindings)
    for table, expected in zip(bundle.datasets[3:], golden["backtesting"], strict=True):
        assert table.id == expected["id"]
        meta = table.metadata
        assert meta.context.source_title == expected["title"]
        assert not meta.segmentations
        axes = {a.id: a for a in meta.axes}
        assert axes["mortgage"].source_label == expected["row"]
        assert axes["mortgage"].header_path_refs == ("panel", "portfolio")
        for c, f, spec in zip(
            table.cells, meta.published_fields, expected["fields"], strict=True
        ):
            key, label, unit, token, precision = spec
            assert (f.id, f.source_label, f.source_unit) == (key, label, unit)
            assert f.header_path_refs == ("panel", key)
            assert (c.row_ref, c.column_ref) == ("mortgage", key)
            assert c.value.original_text == token
            assert c.value.value == Decimal(token)
            assert c.value.displayed_precision == precision
            assert c.value.source_reference.pdf_page == 57
            assert c.value.source_reference.row == expected["row"]
            assert "restatement" in c.qualification_refs
        notes = {q.id: q for q in meta.qualifications}
        assert {
            "framework",
            "restatement",
            "report-entity",
            "level-2",
            "regulatory-basis",
        } <= notes.keys()
        assert [(s.kind, s.id) for s in notes["restatement"].scope] == [
            ("row", "mortgage")
        ]
        assert notes["restatement"].evidence[0].row == expected["row"]
        assert "framework" in meta.context.qualification_refs
        ds = {d.id: d for d in meta.temporal_descriptors}
        if "estimated_pd" in {f.id for f in meta.published_fields}:
            assert {"pd-history", "pd-cohort"} <= notes.keys()
            assert (ds["history"].start, ds["history"].end) == ("2016", None)
        else:
            assert {"lgd-history", "ead-history", "lgd-floor"} <= notes.keys()
            assert (ds["lgd-history"].start, ds["lgd-history"].end) == ("2016", "2022")
            assert ds["ead-history"].start is None and ds["ead-history"].end is None
            assert [(s.kind, s.id) for s in notes["lgd-floor"].scope] == [
                ("field", "estimated_lgd")
            ]
        assert all(b.role == "history_window" for b in meta.temporal_bindings)
