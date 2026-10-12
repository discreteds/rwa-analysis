"""Independent source boundary: every selected Westpac position and its meaning."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def assert_value(cell, token, page):
    assert cell.value.original_text == token
    assert cell.value.source_reference.pdf_page == page
    assert cell.value.source_reference.printed_page == str(page)
    if token == "-":
        assert cell.value.value is None
        assert cell.value.missing_reason == "dash_unresolved"
        assert cell.value.displayed_precision is None
    else:
        number = Decimal(token.replace(",", "").replace("%", "").strip("()"))
        if token.startswith("("):
            number = -number
        assert cell.value.value == number
        assert cell.value.displayed_precision == max(0, -number.as_tuple().exponent)
        assert cell.value.missing_reason is None


def test_complete_westpac_historical_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    extractor = project_root / "extractions/au/westpac/2024-09-30/aps330/extract.py"
    assert extractor.exists(), "Westpac historical capture is not implemented"
    bundle = run_extractor(
        extractor, project_root / "raw/westpac-2024-09-30-aps330.pdf"
    )
    assert bundle.schema_version == "disclosure-v3"
    assert bundle.document.document_reporting_date.isoformat() == "2024-09-30"
    assert len(bundle.datasets) == 6
    assert sum(len(t.cells) for t in bundle.datasets) == 236
    seen_notes = set()
    for table in bundle.datasets:
        context = table.metadata.context
        assert (
            context.reporting_entity.value
            == "Westpac Banking Corporation and its controlled entities"
        )
        assert context.consolidation_scope.value == "Level 2"
        assert context.regulatory_scope.value == "Advanced IRB"
        assert context.currency.value == "AUD"
        assert context.geography.status == "unresolved"
        for note in table.metadata.qualifications:
            if note.id in golden["notes"]:
                page, text = golden["notes"][note.id]
                if table.id == "table9f-2023-09-30" and note.id in (
                    "expected-loss-population",
                    "negative-variance",
                    "nz-history",
                ):
                    page = 58
                assert (note.evidence[0].pdf_page, note.source_text) == (page, text)
                seen_notes.add(note.id)
    assert seen_notes == golden["notes"].keys()

    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        assert table.id == "table9d-" + expected["date"]
        meta = table.metadata
        assert meta.context.source_date_label == expected["label"]
        axes = {a.id: a for a in meta.axes}
        assert [a.source_label for a in meta.axes if a.axis == "row"] == golden["bands"]
        fields = {f.id: f for f in meta.published_fields}
        body = [c for c in table.cells if c.row_ref is not None]
        assert len(body) == 72
        for j, (key, label, unit) in enumerate(golden["exposure_fields"]):
            field = fields[key]
            assert (field.source_label, field.source_unit) == (label, unit)
            assert field.source_scale == (1000000 if unit == "$m" else 1)
            assert field.header_path_refs == ("panel", key)
            assert field.result_kind == ("money" if unit == "$m" else "scalar")
            assert axes[key].order == j
            for i, tokens in enumerate(expected["rows"]):
                cell = next(c for c in body if c.id == f"band-{i}/{key}")
                assert (cell.row_ref, cell.column_ref, cell.field_ref) == (
                    f"band-{i}",
                    key,
                    key,
                )
                assert cell.segment_refs == (f"band-{i}",)
                assert axes[cell.row_ref].header_path_refs == ("panel", "pd-bands")
                assert_value(cell, tokens[j], 45)
                assert cell.value.source_reference.row == golden["bands"][i]
        bands = meta.segmentations[0].bands
        assert [b.source_label for b in bands] == golden["bands"]
        for band, bounds in zip(bands, golden["bounds"], strict=True):
            assert [
                str(band.lower) if band.lower is not None else None,
                str(band.upper) if band.upper is not None else None,
            ] == bounds
            assert band.lower_inclusive is None and band.upper_inclusive is None
        assert [b.kind for b in bands] == ["interval"] * 6 + [
            "category",
            "default",
            "category",
        ]
        assert len(meta.relationships) == 2
        subtotal, total = meta.relationships
        assert (subtotal.kind, subtotal.source_label, subtotal.parent.id) == (
            "total",
            "Subtotal",
            "band-6",
        )
        assert [e.id for e in subtotal.children] == [f"band-{i}" for i in range(6)]
        assert (total.kind, total.parent.id) == ("total", "band-8")
        assert [e.id for e in total.children] == ["band-6", "band-7"]
        assert all(
            r.exhaustive is None and r.mutually_exclusive is None
            for r in meta.relationships
        )
        assert meta.temporal_descriptors[0].point == expected["date"]
        assert all(b.role == "measurement" for b in meta.temporal_bindings)
        assert len(meta.temporal_bindings) == len(table.cells)
        notes = {q.id: q for q in meta.qualifications}
        assert [(e.kind, e.id) for e in notes["expected-loss-definition"].scope] == [
            ("field", "expected_loss")
        ]
        for key in ("pd-definition", "pd-bands"):
            assert [(e.kind, e.id) for e in notes[key].scope] == [("field", "pd")] + [
                ("band", f"band-{i}") for i in range(6)
            ]
        expected_qualifications = {
            "outstandings": ("outstandings",),
            "undrawn": ("undrawn",),
            "ead": ("ead-definition",),
            "pd": ("pd-bands", "pd-definition"),
            "lgd": ("lgd-definition",),
            "expected_loss": ("expected-loss-definition",),
            "rwa": ("rwa-definition",),
            "risk_weight": (),
        }
        for key, qualifiers in expected_qualifications.items():
            assert fields[key].qualification_refs == qualifiers
            assert all(
                c.qualification_refs == qualifiers for c in body if c.field_ref == key
            )
        assert "pd-definition" in axes["band-0"].qualification_refs
        assert "default-definition" in axes["band-7"].qualification_refs
        supplementary = [c for c in table.cells if c.row_ref is None]
        assert len(supplementary) == (2 if expected["date"] == "2024-09-30" else 0)
        for c, key, token in zip(
            supplementary, ("irb_rwa", "standardised_rwa"), ("131,989", "214,081")
        ):
            assert c.field_ref == key and c.column_ref is None
            assert fields[key].source_form == "note"
            assert fields[key].source_scale == 1000000
            assert c.qualification_refs == ("supplementary-rwa",)
            assert_value(c, token, 45)

    for table, expected in zip(bundle.datasets[3:], golden["backtesting"], strict=True):
        assert table.id == "table9f-" + expected["date"]
        meta = table.metadata
        assert meta.context.source_date_label == expected["label"]
        assert not meta.segmentations
        assert len(table.cells) == 6
        axes = {a.id: a for a in meta.axes}
        assert axes["default-rate"].source_label == "Default rate"
        assert axes["lgd"].source_label == "Loss Given Default"
        assert axes["mortgage"].source_label == "Residential Mortgages"
        for c, f, spec, token in zip(
            table.cells,
            meta.published_fields,
            golden["backtesting_fields"],
            expected["tokens"],
            strict=True,
        ):
            key, label, unit, path = spec
            assert (f.id, f.source_label, f.source_unit, list(f.header_path_refs)) == (
                key,
                label,
                unit,
                path,
            )
            assert axes[key].header_path_refs == tuple(path[:-1])
            assert (c.id, c.row_ref, c.column_ref, c.field_ref) == (
                "mortgage/" + key,
                "mortgage",
                key,
                key,
            )
            assert_value(c, token, expected["page"])
        notes = {q.id: q for q in meta.qualifications}
        assert [e.id for e in notes["nz-history"].scope] == [
            "predicted_pd",
            "observed_pd",
            "predicted_lgd",
            "observed_lgd",
            "ead_variance",
        ]
        desc = {d.id: d for d in meta.temporal_descriptors}
        assert desc["measurement"].point == expected["date"]
        for key in (
            "history",
            "lgd-history",
            "ead-history",
            "annual-anchor",
            "annual-outcome",
            "ead-prediction",
        ):
            assert (
                desc[key].point is None
                and desc[key].start is None
                and desc[key].end is None
            )
            assert (
                desc[key].point_status
                == desc[key].start_status
                == desc[key].end_status
                == "unresolved"
            )
        assert desc["annual-outcome"].duration_amount == 1
        bindings = {
            (b.cell_id, b.role, b.descriptor_ref) for b in meta.temporal_bindings
        }
        assert bindings == {
            ("mortgage/expected_loss", "measurement", "measurement"),
            ("mortgage/predicted_pd", "history_window", "history"),
            ("mortgage/observed_pd", "history_window", "history"),
            ("mortgage/predicted_pd", "cohort_anchor", "annual-anchor"),
            ("mortgage/observed_pd", "cohort_anchor", "annual-anchor"),
            ("mortgage/predicted_pd", "rating_assignment", "annual-anchor"),
            ("mortgage/observed_pd", "outcome_window", "annual-outcome"),
            ("mortgage/predicted_lgd", "history_window", "lgd-history"),
            ("mortgage/observed_lgd", "history_window", "lgd-history"),
            ("mortgage/ead_variance", "history_window", "ead-history"),
            ("mortgage/ead_variance", "measurement", "ead-prediction"),
        }
