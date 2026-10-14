"""Independent source transcription owns NAB values and distinguishing semantics."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_nab_historical_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    path = project_root / "extractions/au/nab/2024-09-30/aps330/extract.py"
    assert path.exists(), "NAB historical extractor is not implemented"
    bundle = run_extractor(path, project_root / "raw/nab-2024-09-30-aps330.pdf")
    assert bundle.schema_version == "disclosure-v4"
    assert bundle.bundle_key == "au/nab/2024-09-30/aps330"
    occurrences = {
        (b.ref.scope, b.ref.kind, b.ref.local_id): b
        for b in bundle.snapshot.occurrences
    }
    fragments = {(f.binding_ref, f.slot): f for f in bundle.fragments}
    assert len([b for b in occurrences.values() if b.cell is not None]) == 90
    assert len(occurrences) == len(bundle.snapshot.occurrences)
    assert all(b.ref.bundle_key == bundle.bundle_key for b in occurrences.values())
    assert len([b for b in occurrences.values() if b.ref.local_id == "pd-cohort"]) == 1
    assert len([b for b in occurrences.values() if b.ref.local_id == "apra-floor"]) == 3
    assert len(bundle.datasets) == 8
    assert sum(len(t.cells) for t in bundle.datasets) == 90
    for table, expected in zip(
        bundle.datasets, golden["exposures"] + golden["backtesting"], strict=True
    ):
        meta = table.metadata
        assert meta.context.document_date.isoformat() == "2024-09-30"
        assert meta.context.currency.value == "AUD"
        assert meta.context.consolidation_scope.value == "Level 2"
        assert meta.context.geography.status == "unresolved"
        prefix = (
            f"table5-1-j-{expected['kind']}-" if "kind" in expected else "table5-3-b-"
        )
        assert table.id == prefix + expected["date"]
        axes = {a.id: a for a in meta.axes}
        notes = {q.id: q for q in meta.qualifications}
        fields = {f.id: f for f in meta.published_fields}
        field_expectations = (
            golden["backtesting_fields"][expected["kind"]]
            if "kind" in expected
            else golden["exposure_fields"]
        )
        for f, (label, unit, scale) in zip(
            fields.values(), field_expectations, strict=True
        ):
            marker = ""
            if "kind" not in expected:
                number = {"undrawn": 1, "average_ead": 2, "risk_weight": 3}.get(f.id)
                if number is not None:
                    marker = f"({number + (expected['page'] == 50)})"
            assert f.source_label == label + marker
            assert f.source_unit == unit and str(f.source_scale) == scale
            assert f.source_form == "table_body"
            assert f.result_kind == ("money" if unit == "$m" else "scalar")
            assert f.source_reference.pdf_page == expected["page"]
            binding = occurrences[table.id, "field", f.id]
            assert binding.physical_refs
            captured = " ".join(
                fragments[r.binding_ref, r.slot].text for r in binding.physical_refs
            )
            assert " ".join(captured.split()) == label + marker
        descriptors = {d.id: d for d in meta.temporal_descriptors}
        tokens = [token for row in expected["rows"] for token in row]
        assert [c.value.original_text for c in table.cells] == tokens
        for c, token in zip(table.cells, tokens, strict=True):
            v = Decimal(token.replace(",", "").replace("%", ""))
            assert c.value.value == v
            assert c.value.displayed_precision == max(0, -v.as_tuple().exponent)
            assert c.value.missing_reason is None
            assert c.value.source_reference.pdf_page == expected["page"]
            assert c.value.source_reference.printed_page == str(expected["page"] - 2)
            assert c.context_refs == ("context",)
            assert c.value.source_reference.document_id == "nab-2024-09-30-aps330"
        required_notes = (
            {"undrawn", "average-arrangements", "overlay", "retail-lgd"}
            if "kind" not in expected
            else {"framework-history", "rbnz-materiality"}
            | (
                {"pd-cohort", "ead-comparison"}
                if expected["kind"] == "ii"
                else {"lgd-estimate", "lgd-history", "apra-floor", "rbnz-lgd"}
            )
        )
        if "kind" not in expected and expected["page"] == 50:
            required_notes.add("pd-model-change")
        assert required_notes <= notes.keys()
        for key in required_notes:
            if key in golden["notes"]:
                assert notes[key].source_text == golden["notes"][key]
            comment = (
                occurrences.get((table.id, "comment", key))
                or occurrences[None, "comment", key]
            )
            assert comment.physical_refs
            for endpoint in notes[key].scope:
                kind = {"dataset": "table", "band": "column"}.get(
                    endpoint.kind, endpoint.kind
                )
                assert any(
                    link.role == "qualifies"
                    and (link.target.scope, link.target.kind, link.target.local_id)
                    == (table.id, kind, endpoint.id)
                    for link in comment.links
                )
        if "kind" not in expected:
            assert list(fields) == [
                "exposure",
                "undrawn",
                "average_ead",
                "lgd",
                "risk_weight",
            ]
            assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
                "bands"
            ]
            assert len(meta.segmentations[0].bands) == 6
            for band, bounds in zip(
                meta.segmentations[0].bands, golden["bounds"], strict=True
            ):
                assert [
                    None if n is None else str(n) for n in (band.lower, band.upper)
                ] == bounds
                assert band.lower_inclusive is None
            assert meta.segmentations[0].bands[-1].kind == "default"
            assert fields["average_ead"].source_scale == Decimal(1000000)
            assert fields["average_ead"].qualification_refs == (
                "average-arrangements",
                "ead-definition",
            )
            assert (
                "EaD is presented net of eligible financial collateral, except where indicated."
                in notes["ead-glossary"].source_text
            )
            assert notes["ead-glossary"].evidence[0].pdf_page == 76
            assert fields["risk_weight"].qualification_refs == ("overlay",)
            for key in fields:
                assert axes[key + "-mortgage"].header_path_refs == (
                    "panel",
                    key,
                    key + "-approach",
                )
            assert axes["band-0"].header_path_refs == ("panel", "pd-bands")
            assert len(meta.relationships) == 6
            for j, rel in enumerate(meta.relationships):
                assert (rel.parent.kind, rel.parent.id) == (
                    "cell",
                    f"exposure/band-{j}",
                )
                assert [(e.kind, e.id) for e in rel.children] == [
                    ("cell", f"undrawn/band-{j}")
                ]
                assert rel.exhaustive is None and rel.mutually_exclusive is None
            assert descriptors["measurement"].point == expected["date"]
            assert len(meta.temporal_bindings) == 30
            assert ("pd-model-change" in notes) == (expected["page"] == 50)
            if expected["page"] == 50:
                assert [(e.kind, e.id) for e in notes["pd-model-change"].scope] == [
                    ("field", "exposure"),
                    ("field", "undrawn"),
                ]
        else:
            assert not meta.segmentations and not meta.relationships
            assert notes["framework-history"].source_text.endswith(
                "to allow sufficient time to complete asset workouts and recognition of any losses."
            )
            assert notes["framework-history"].evidence[0].pdf_page == 38
            assert axes["main"].header_path_refs == ("panel", "main-block")
            assert axes["rbnz"].header_path_refs == ("panel", "rbnz-block")
            assert (
                "RBNZ regulated banking subsidiary" in axes["rbnz-block"].source_label
            )
            assert [c.row_ref for c in table.cells] == ["main"] * len(fields) + [
                "rbnz"
            ] * len(fields)
            assert all(
                fields[c.field_ref].header_path_refs == ("panel", c.field_ref)
                for c in table.cells
            )
            if expected["kind"] == "ii":
                assert list(fields) == ["estimated_pd", "actual_pd", "ead_ratio"]
                assert fields["ead_ratio"].source_unit == "ratio"
                assert descriptors["pd-history"].duration_amount == Decimal(10)
                assert (
                    descriptors["pd-history"].start is None
                    and descriptors["pd-history"].end is None
                )
                assert {
                    "pd-cohort",
                    "ead-comparison",
                    "framework-history",
                } <= notes.keys()
                assert not any(
                    b.role == "history_window" and b.cell_id.endswith("ead_ratio")
                    for b in meta.temporal_bindings
                )
                assert any(
                    b.role == "outcome_window" and b.cell_id == "main/actual_pd"
                    for b in meta.temporal_bindings
                )
                outcome = descriptors["pd-outcome"]
                assert outcome.duration_amount == Decimal(12)
                assert outcome.duration_unit == "month"
                assert outcome.start is outcome.end is None
                actual = occurrences[table.id, "cell", "main/actual_pd"]
                assert {r.role for r in actual.temporal_roles} == {
                    "history_window",
                    "cohort_anchor",
                    "outcome_window",
                }
                assert {
                    (b.role, b.descriptor_ref)
                    for b in meta.temporal_bindings
                    if b.cell_id == "rbnz/ead_ratio"
                } == {("cohort_anchor", "ead-anchor"), ("measurement", "ead-default")}
            else:
                assert list(fields) == ["estimated_lgd", "actual_lgd"]
                assert descriptors["lgd-history"].end == expected["date"]
                assert descriptors["lgd-history"].duration_amount == Decimal(10)
                assert descriptors["lgd-estimate"].point is None
                assert {
                    "lgd-history",
                    "lgd-estimate",
                    "apra-floor",
                    "rbnz-lgd",
                } <= notes.keys()
                assert [(e.kind, e.id) for e in notes["apra-floor"].scope] == [
                    ("cell", "main/estimated_lgd")
                ]
                assert [(e.kind, e.id) for e in notes["rbnz-lgd"].scope] == [
                    ("cell", "rbnz/estimated_lgd")
                ]
                cells = {c.id: c for c in table.cells}
                assert "apra-floor" in cells["main/estimated_lgd"].qualification_refs
                assert "rbnz-lgd" in cells["rbnz/estimated_lgd"].qualification_refs
