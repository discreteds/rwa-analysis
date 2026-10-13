"""Independent FY23 source expectations, including vintage-specific qualifications."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def test_complete_nab_2023_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    path = project_root / "extractions/au/nab/2023-09-30/aps330/extract.py"
    assert path.exists(), "NAB 2023 extractor is not implemented"
    bundle = run_extractor(path, project_root / "raw/nab-2023-09-30-aps330.pdf")
    assert bundle.schema_version == "disclosure-v3"
    assert len(bundle.datasets) == 8
    assert sum(len(t.cells) for t in bundle.datasets) == 90
    for table, expected in zip(
        bundle.datasets, golden["exposures"] + golden["backtesting"], strict=True
    ):
        meta = table.metadata
        assert meta.context.document_date.isoformat() == "2023-09-30"
        assert meta.context.currency.value == "AUD"
        assert meta.context.consolidation_scope.value == "Level 2"
        assert meta.context.geography.status == "unresolved"
        assert table.id.endswith(expected["date"])
        axes = {a.id: a for a in meta.axes}
        fields = {f.id: f for f in meta.published_fields}
        notes = {q.id: q for q in meta.qualifications}
        descriptors = {d.id: d for d in meta.temporal_descriptors}
        tokens = [token for row in expected["rows"] for token in row]
        assert [c.value.original_text for c in table.cells] == tokens
        for c, token in zip(table.cells, tokens, strict=True):
            value = Decimal(token.replace(",", "").replace("%", ""))
            assert c.value.value == value
            assert c.value.displayed_precision == max(0, -value.as_tuple().exponent)
            assert c.value.missing_reason is None
            assert c.value.source_reference.pdf_page == expected["page"]
            assert c.value.source_reference.printed_page == str(expected["page"] - 2)
            assert c.context_refs == ("context",)
            assert c.value.source_reference.document_id == "nab-2023-09-30-aps330"
        if "kind" not in expected:
            expected_notes = {"undrawn", "average-arrangements", "overlay", "retail-lgd"}
            if expected["date"] == "2023-03-31":
                expected_notes.add("undrawn-restated")
        else:
            expected_notes = {"framework-history", "backtesting-perimeter"}
            expected_notes.update(
                {"pd-cohort", "ead-comparison"}
                if expected["kind"] == "ii"
                else {"lgd-estimate", "lgd-history", "apra-floor", "rbnz-lgd"}
            )
        assert expected_notes <= notes.keys(), (table.id, expected_notes - notes.keys())
        for key in expected_notes:
            assert notes[key].source_text == golden["notes"][key]
        for f in fields.values():
            assert f.source_form == "table_body"
            assert f.source_reference.pdf_page == expected["page"]
            assert f.source_scale == Decimal(1000000 if f.source_unit == "$m" else 1)
            assert f.result_kind == ("money" if f.source_unit == "$m" else "scalar")
        assert "pd-model-change" not in notes
        if "kind" not in expected:
            assert list(fields) == [
                "exposure",
                "undrawn",
                "average_ead",
                "lgd",
                "risk_weight",
            ]
            assert [f.source_label for f in fields.values()] == expected["labels"]
            assert [f.source_unit for f in fields.values()] == [
                "$m",
                "$m",
                "$m",
                "%",
                "%",
            ]
            assert [a.source_label for a in meta.axes if a.axis == "column"] == golden[
                "bands"
            ]
            bands = meta.segmentations[0].bands
            assert [(str(b.lower), str(b.upper)) for b in bands[:-1]] == [
                ("0", "0.1"),
                ("0.1", "0.5"),
                ("0.5", "2.0"),
                ("2.0", "5.0"),
                ("5.0", "99.9"),
            ]
            assert all(b.lower_inclusive is None for b in bands)
            assert bands[-1].kind == "default"
            assert notes["default-definition"].evidence[0].pdf_page == 23
            assert notes["ead-glossary"].evidence[0].pdf_page == 76
            assert (
                "net of eligible financial collateral"
                in notes["ead-glossary"].source_text
            )
            assert fields["average_ead"].qualification_refs == (
                "average-arrangements",
                "ead-definition",
            )
            assert fields["average_ead"].attributes[0].value == "arrangement"
            assert fields["risk_weight"].qualification_refs == ("overlay",)
            for key in fields:
                assert axes[key + "-mortgage"].header_path_refs == (
                    "panel",
                    key,
                    key + "-approach",
                )
            assert len(meta.relationships) == 6
            for j, rel in enumerate(meta.relationships):
                assert rel.parent.id == f"exposure/band-{j}"
                assert [e.id for e in rel.children] == [f"undrawn/band-{j}"]
                assert [e.id for e in rel.scope] == [f"band-{j}"]
                assert rel.exhaustive is None and rel.mutually_exclusive is None
            assert descriptors["measurement"].point == expected["date"]
            assert len(meta.temporal_bindings) == 30
            restated = expected["date"] == "2023-03-31"
            assert ("undrawn-restated" in notes) == restated
            if restated:
                assert [(e.kind, e.id) for e in notes["undrawn-restated"].scope] == [
                    ("field", "undrawn")
                ]
                assert "undrawn-restated" in fields["undrawn"].qualification_refs
                assert all(
                    ("undrawn-restated" in c.qualification_refs)
                    == (c.field_ref == "undrawn")
                    for c in table.cells
                )
        else:
            assert not meta.segmentations and not meta.relationships
            assert notes["framework-history"].evidence[0].pdf_page == 38
            assert notes["backtesting-perimeter"].evidence[0].pdf_page == 38
            assert (
                axes["main-block"].source_label
                == "Exposure type subject to " + expected["approach"] + " approach"
            )
            assert (
                axes["rbnz-block"].source_label == "RBNZ regulated banking subsidiary"
            )
            assert [c.row_ref for c in table.cells] == ["main"] * len(fields) + [
                "rbnz"
            ] * len(fields)
            for population in ("main", "rbnz"):
                assert axes[population].header_path_refs == (
                    "panel",
                    population + "-block",
                )
            if expected["kind"] == "ii":
                assert list(fields) == ["estimated_pd", "actual_pd", "ead_ratio"]
                assert [f.source_label for f in fields.values()] == [
                    "Average estimated PD",
                    "Average actual PD",
                    "Ratio of estimated to actual EaD",
                ]
                assert [f.source_unit for f in fields.values()] == ["%", "%", "ratio"]
                assert {"pd-cohort", "ead-comparison"} <= notes.keys()
                assert descriptors["pd-history"].duration_amount == Decimal(10)
                assert (
                    descriptors["pd-history"].start
                    is descriptors["pd-history"].end
                    is None
                )
                assert not any(
                    b.role == "outcome_window" for b in meta.temporal_bindings
                )
                assert {
                    (b.role, b.descriptor_ref)
                    for b in meta.temporal_bindings
                    if b.cell_id == "main/actual_pd"
                } == {("history_window", "pd-history"), ("cohort_anchor", "pd-anchor")}
                assert {
                    (b.role, b.descriptor_ref)
                    for b in meta.temporal_bindings
                    if b.cell_id == "rbnz/ead_ratio"
                } == {("cohort_anchor", "ead-anchor"), ("measurement", "ead-default")}
            else:
                assert list(fields) == ["estimated_lgd", "actual_lgd"]
                assert [f.source_label for f in fields.values()] == [
                    "Average estimated downturn LGD",
                    "Average actual LGD",
                ]
                assert [f.source_unit for f in fields.values()] == ["%", "%"]
                assert descriptors["lgd-history"].end == expected["date"]
                assert descriptors["lgd-history"].duration_amount == Decimal(10)
                assert descriptors["lgd-estimate"].point is None
                for note, cell in (
                    ("apra-floor", "main/estimated_lgd"),
                    ("rbnz-lgd", "rbnz/estimated_lgd"),
                ):
                    assert [(e.kind, e.id) for e in notes[note].scope] == [
                        ("cell", cell)
                    ]
                    assert [
                        c.id for c in table.cells if note in c.qualification_refs
                    ] == [cell]
