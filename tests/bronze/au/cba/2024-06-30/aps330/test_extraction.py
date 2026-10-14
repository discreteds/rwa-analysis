"""Independent PDF expectations catch omitted panels, metrics and source semantics."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_cba_historical_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    bundle = run_extractor(
        project_root / "extractions/au/cba/2024-06-30/aps330/extract.py",
        project_root / "raw/cba-2024-06-30-aps330.pdf",
    )
    assert bundle.schema_version == "disclosure-v4"
    occurrences = {
        (b.ref.scope, b.ref.kind, b.ref.local_id): b
        for b in bundle.snapshot.occurrences
    }
    fragments = {(f.binding_ref, f.slot): f for f in bundle.fragments}
    assert all(b.ref.bundle_key == bundle.bundle_key for b in occurrences.values())
    assert len(occurrences[None, "comment", "report-entity"].links) == 5
    assert len(bundle.datasets) == 5
    assert bundle.document.document_reporting_date.isoformat() == "2024-06-30"
    assert sum(len(ds.cells) for ds in bundle.datasets) == 131
    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        assert table.id == "table9d-ii-" + expected["date"]
        meta = table.metadata
        assert meta.context.evidence[0].pdf_page == 1
        assert meta.context.evidence[0].printed_page == ""
        assert meta.context.source_date_label == expected["label"]
        assert (
            meta.context.reporting_entity.value
            == "CBA and its subsidiaries (the Group)"
        )
        assert meta.context.consolidation_scope.value == "Level 2"
        assert meta.context.consolidation_scope.qualification_refs == ("level-2",)
        assert meta.context.geography.status == "unresolved"
        assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
            "bands"
        ]
        axes = {a.id: a for a in meta.axes}
        assert axes["band-0"].header_path_refs == ("panel", "pd-bands")
        notes = {q.id: q for q in meta.qualifications}
        for key, page in (
            ("pd-horizon", 43),
            ("pd-long-run", 43),
            ("lgd-downturn", 44),
        ):
            assert notes[key].source_text == golden["notes"][key]
            assert notes[key].evidence[0].pdf_page == page
            targets = [(s.kind, s.id) for s in notes[key].scope]
            assert targets == (
                [("field", "lgd")]
                if key == "lgd-downturn"
                else [("band", f"band-{i}") for i in range(7)]
            )
        assert axes["band-0"].qualification_refs == ("pd-horizon", "pd-long-run")
        assert notes["undrawn"].source_text == golden["notes"]["undrawn"]
        assert notes["scaling"].source_text == golden["notes"]["scaling"]
        assert notes["overlay"].source_text == (
            f"Excludes a $7.4 billion RWA overlay that has been applied at {expected['label']} for regulatory capital purposes."
        )
        assert [(s.kind, s.id) for s in notes["overlay"].scope] == [("field", "lgd")]
        fields = {f.id: f for f in meta.published_fields}
        assert set(fields) == {f[0] for f in golden["fields"]} | {"overlay", "scaling"}
        for definition, tokens in zip(golden["fields"], expected["rows"], strict=True):
            key, label, unit, scale, precision = definition
            field = fields[key]
            assert field.source_reference.row == label
            assert field.source_reference.column is None
            assert (field.source_label, field.source_unit, str(field.source_scale)) == (
                label,
                unit,
                scale,
            )
            assert field.header_path_refs == ("panel", key)
            for kind in ("field", "block"):
                slot = occurrences[table.id, kind, key].physical_refs[0]
                assert fragments[slot.binding_ref, slot.slot].text == label
            cells = [c for c in table.cells if c.field_ref == key]
            assert [c.value.original_text for c in cells] == tokens
            assert [c.column_ref for c in cells] == [f"band-{i}" for i in range(8)]
            assert all(c.row_ref == key + "-mortgage" for c in cells)
            assert axes[key + "-mortgage"].header_path_refs == ("panel", key)
            for cell, token in zip(cells, tokens, strict=True):
                assert cell.value.value == Decimal(token.replace(",", ""))
                assert cell.value.displayed_precision == precision
                assert cell.value.missing_reason is None
                assert cell.value.source_reference.pdf_page == expected["page"]
                assert cell.value.source_reference.printed_page == str(
                    expected["page"] - 2
                )
        assert fields["average_ead"].attributes[0].status == "unresolved"
        assert fields["lgd"].qualification_refs == (
            "overlay",
            "lgd-definition",
            "lgd-downturn",
        )
        assert fields["risk_weight"].qualification_refs == ("scaling",)
        for key, token in (("overlay", "7.4"), ("scaling", "1.10")):
            c = next(c for c in table.cells if c.field_ref == key)
            assert fields[key].source_form == "note"
            assert (c.row_ref, c.column_ref) == (None, None)
            assert c.qualification_refs == (key,)
            assert c.value.original_text == token
            binding = occurrences[table.id, "cell", key]
            assert any(
                link.target == occurrences[table.id, "comment", key].ref
                for link in binding.links
            )
        overlay = occurrences[table.id, "comment", "overlay"]
        assert [(link.target.kind, link.target.local_id) for link in overlay.links] == [
            ("field", "lgd")
        ]
        bands = meta.segmentations[0].bands
        assert [b.source_label for b in bands] == golden["bands"]
        for band, bounds in zip(bands, golden["bounds"], strict=True):
            assert [
                str(band.lower) if band.lower is not None else None,
                str(band.upper) if band.upper is not None else None,
            ] == bounds
            assert band.lower_inclusive is None
        assert all(b.upper_inclusive is False for b in bands[:6])
        assert bands[6].kind == "default" and bands[7].kind == "category"
        subsets = [r for r in meta.relationships if r.kind == "subset"]
        assert len(subsets) == 8
        for i, rel in enumerate(subsets):
            assert (rel.parent.kind, rel.parent.id) == ("cell", f"exposure/band-{i}")
            assert [(e.kind, e.id) for e in rel.children] == [
                ("cell", f"undrawn/band-{i}")
            ]
            assert rel.exhaustive is None and rel.mutually_exclusive is None
        assert len([r for r in meta.relationships if r.kind == "total"]) == 5
        assert len(meta.temporal_bindings) == 42
        assert all(b.role == "measurement" for b in meta.temporal_bindings)
        assert meta.temporal_descriptors[0].point == expected["date"]

    for table, expected in zip(bundle.datasets[3:], golden["backtesting"], strict=True):
        assert table.id == expected["id"]
        assert table.metadata.context.source_title == expected["title"]
        assert {
            f.evidence.row
            for f in bundle.fragments
            if f.evidence.location == expected["title"] and f.evidence.row is not None
        } == {
            "Residential mortgage"
            if table.id.startswith("table9f-ii-")
            else "Residential mortgage ²"
        }
        assert not table.metadata.segmentations
        assert [f.source_label for f in table.metadata.published_fields] == [
            f[1] for f in expected["fields"]
        ]
        for cell, field in zip(table.cells, expected["fields"], strict=True):
            key, label, unit, token, precision = field
            assert cell.field_ref == key
            assert cell.value.original_text == token
            assert cell.value.value == Decimal(token)
            assert cell.value.displayed_precision == precision
            assert cell.value.source_reference.pdf_page == 56
            binding = occurrences[table.id, "cell", cell.id]
            assert [r.role for r in binding.temporal_roles] == ["history_window"]
            header = occurrences[table.id, "field", key].physical_refs[0]
            assert fragments[header.binding_ref, header.slot].text == label
        notes = {q.id: q for q in table.metadata.qualifications}
        for key in notes.keys() & golden["notes"].keys():
            assert notes[key].source_text == golden["notes"][key]
        descriptors = {d.id: d for d in table.metadata.temporal_descriptors}
        if table.id.startswith("table9f-ii-"):
            assert {
                "framework",
                "pd-history",
                "pd-cohort",
                "pd-restatement",
            } <= notes.keys()
            assert descriptors["history"].start == "2016"
            assert descriptors["history"].end is None
            assert notes["pd-restatement"].scope == ()
            assert (
                notes["pd-restatement"].evidence[0].row
                == "RBNZ regulated entities: Retail ²"
            )
        else:
            assert {
                "framework",
                "lgd-history",
                "ead-history",
                "lgd-floor",
                "lgd-restatement",
            } <= notes.keys()
            assert (
                descriptors["lgd-history"].start,
                descriptors["lgd-history"].end,
            ) == ("2016", "2023")
            assert descriptors["ead-history"].start is None
            assert descriptors["ead-history"].end is None
            assert notes["lgd-restatement"].scope == ()
        assert all(b.role == "history_window" for b in table.metadata.temporal_bindings)
