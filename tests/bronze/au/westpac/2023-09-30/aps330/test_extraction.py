"""Source-authored values and semantics at the real PDF extraction boundary."""

import json
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor


def assert_value(cell, token, page):
    value = cell.value
    assert value.original_text == token
    assert value.source_reference.pdf_page == page
    assert value.source_reference.printed_page == str(page - 2)
    if token == "N/A":
        assert value.value is None
        assert value.missing_reason == "not_applicable"
        assert value.displayed_precision is None
    else:
        number = Decimal(token.replace(",", "").replace("%", "").strip("()"))
        if token.startswith("("):
            number = -number
        assert value.value == number
        assert value.displayed_precision == max(0, -number.as_tuple().exponent)
        assert value.missing_reason is None


def test_complete_westpac_2023_source(project_root):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text())
    path = project_root / "extractions/au/westpac/2023-09-30/aps330/extract.py"
    assert path.exists(), "Westpac September 2023 capture is not implemented"
    bundle = run_extractor(path, project_root / "raw/westpac-2023-09-30-aps330.pdf")
    assert bundle.schema_version == "disclosure-v4"
    captured = {(f.binding_ref, f.slot): f for f in bundle.fragments}
    occurrences = {
        (b.ref.scope, b.ref.kind, b.ref.local_id): b
        for b in bundle.snapshot.occurrences
    }
    assert all(b.ref.bundle_key == bundle.bundle_key for b in occurrences.values())
    for scope in ("table9d-2023-09-30", "table9d-2023-03-31", "table9d-2022-09-30"):
        b = occurrences[scope, "field", "ead"]
        fragment = captured[b.physical_refs[0].binding_ref, b.physical_refs[0].slot]
        assert fragment.text == "Exposure at Default"
        assert fragment.evidence.pdf_page == 44
    entity = occurrences[None, "comment", "report-entity"]
    assert len(entity.links) == 6
    assert (
        captured[entity.physical_refs[0].binding_ref, "text"].text
        == golden["notes"]["report-entity"][1]
    )
    nz_comments = [
        b
        for b in occurrences.values()
        if b.ref.kind == "comment" and b.ref.local_id == "nz-history"
    ]
    assert {
        (
            captured[b.physical_refs[0].binding_ref, "text"].evidence.pdf_page,
            frozenset(link.target.scope for link in b.links),
        )
        for b in nz_comments
    } == {
        (56, frozenset({"table9f-2023-09-30"})),
        (57, frozenset({"table9f-2023-03-31", "table9f-2022-09-30"})),
    }
    for scope in ("table9f-2023-09-30", "table9f-2023-03-31", "table9f-2022-09-30"):
        for key in ("predicted_pd", "predicted_lgd"):
            b = occurrences[scope, "field", key]
            assert (
                captured[b.physical_refs[0].binding_ref, b.physical_refs[0].slot].text
                == "Predicted"
            )
        cell_binding = occurrences[scope, "cell", "mortgage/observed_pd"]
        assert {r.role for r in cell_binding.temporal_roles} == {
            "history_window",
            "cohort_anchor",
            "outcome_window",
        }
    assert bundle.document.document_reporting_date.isoformat() == "2023-09-30"
    assert bundle.document.source_url == (
        "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/"
        "september-2023-Pillar-3-report.pdf"
    )
    assert len(bundle.datasets) == 6
    assert sum(len(t.cells) for t in bundle.datasets) == 237
    seen = set()
    for table in bundle.datasets:
        meta = table.metadata
        ctx = meta.context
        assert ctx.document_date.isoformat() == "2023-09-30"
        assert ctx.reporting_entity.value == (
            "Westpac Banking Corporation and its controlled entities"
        )
        assert ctx.consolidation_scope.value == "Level 2"
        assert ctx.regulatory_scope.value == "Advanced IRB"
        assert ctx.currency.value == "AUD"
        assert ctx.geography.status == "unresolved"
        notes = {q.id: q for q in meta.qualifications}
        for q in notes.values():
            page, text = golden["notes"][q.id]
            if table.id in ("table9f-2023-03-31", "table9f-2022-09-30") and q.id in (
                "expected-loss-population",
                "negative-variance",
                "nz-history",
            ):
                page = 57
            assert (q.evidence[0].pdf_page, q.source_text) == (page, text)
            assert q.evidence[0].printed_page == ("" if page == 2 else str(page - 2))
            seen.add(q.id)
        assert {
            "report-entity",
            "currency",
            "level-2",
            "regulatory-basis",
            "rounding",
        } <= notes.keys()
    assert seen == golden["notes"].keys()

    for table, expected in zip(bundle.datasets[:3], golden["exposures"], strict=True):
        meta = table.metadata
        assert table.id == "table9d-" + expected["date"]
        assert (
            meta.context.source_title == "Residential mortgages portfolio by PD band¹,²"
        )
        assert meta.context.source_date_label == expected["label"]
        axes = {a.id: a for a in meta.axes}
        assert axes["panel"].source_label == expected["label"]
        assert [a.source_label for a in meta.axes if a.axis == "row"] == golden["bands"]
        fields = {f.id: f for f in meta.published_fields}
        cells = {c.id: c for c in table.cells}
        assert len([c for c in table.cells if c.row_ref]) == 72
        for j, (key, label, unit, qs) in enumerate(golden["exposure_fields"]):
            f = fields[key]
            binding = occurrences[table.id, "field", key]
            fragment = binding.physical_refs[0]
            assert captured[
                fragment.binding_ref, fragment.slot
            ].text == label.translate(str.maketrans("³⁴", "34"))
            assert (f.source_label, f.source_unit, f.header_path_refs) == (
                label,
                unit,
                ("panel", key),
            )
            assert f.source_scale == (1000000 if unit == "$m" else 1)
            assert f.result_kind == ("money" if unit == "$m" else "scalar")
            assert f.qualification_refs == tuple(qs)
            assert axes[key].order == j
            for i, tokens in enumerate(expected["rows"]):
                c = cells[f"band-{i}/{key}"]
                assert (c.field_ref, c.row_ref, c.column_ref) == (key, f"band-{i}", key)
                assert c.segment_refs == (f"band-{i}",)
                assert c.qualification_refs == tuple(qs)
                assert c.value.source_reference.row == golden["bands"][i]
                assert_value(c, tokens[j], 44)
        for i, band in enumerate(meta.segmentations[0].bands):
            assert axes[band.id].header_path_refs == ("panel", "pd-bands")
            assert band.source_label == golden["bands"][i]
            assert band.lower_inclusive is None and band.upper_inclusive is None
            if i < 6:
                assert (str(band.lower), str(band.upper)) == tuple(
                    golden["bands"][i].split(" to ")
                )
                assert band.kind == "interval"
            else:
                assert band.kind == ("default" if i == 7 else "category")
        assert [
            (r.parent.id, [e.id for e in r.children]) for r in meta.relationships
        ] == [
            ("band-6", [f"band-{i}" for i in range(6)]),
            ("band-8", ["band-6", "band-7"]),
        ]
        assert all(
            r.scope[0].id == table.id
            and r.exhaustive is None
            and r.mutually_exclusive is None
            for r in meta.relationships
        )
        notes = {q.id: q for q in meta.qualifications}
        for key in ("pd-bands", "pd-definition"):
            assert [(e.kind, e.id) for e in notes[key].scope] == [("field", "pd")] + [
                ("band", f"band-{i}") for i in range(6)
            ]
        assert [e.id for e in notes["risk-weight-floor"].scope] == [
            "rwa",
            "risk_weight",
        ] + (["risk_weight_floor"] if expected["date"] == "2022-09-30" else [])
        assert ("mortgage-definition" in notes) == (expected["date"] != "2022-09-30")
        default_qs = (
            ("default-pre-2023",)
            if expected["date"] == "2022-09-30"
            else ("default-from-2023", "npe-definition")
        )
        assert axes["band-7"].qualification_refs == default_qs
        assert meta.temporal_descriptors[0].point == expected["date"]
        assert {
            (b.cell_id, b.role, b.descriptor_ref) for b in meta.temporal_bindings
        } == {(c.id, "measurement", "measurement") for c in table.cells}
        supplementary = [c for c in table.cells if c.row_ref is None]
        assert (
            len(supplementary)
            == {"2023-09-30": 2, "2023-03-31": 0, "2022-09-30": 1}[expected["date"]]
        )
        for c, key, token in zip(
            supplementary if expected["date"] == "2023-09-30" else [],
            ("irb_rwa", "standardised_rwa"),
            ("132,238", "209,292"),
        ):
            assert c.field_ref == key and c.column_ref is None
            assert fields[key].source_form == "note"
            assert c.qualification_refs == ("supplementary-rwa",)
            assert_value(c, token, 44)
        if expected["date"] == "2022-09-30":
            c = supplementary[0]
            assert c.field_ref == "risk_weight_floor"
            assert fields[c.field_ref].source_form == "note"
            assert fields[c.field_ref].source_unit == "%"
            assert c.qualification_refs == ("risk-weight-floor",)
            assert_value(c, "25%", 44)

    for table, expected in zip(bundle.datasets[3:], golden["backtesting"], strict=True):
        meta = table.metadata
        assert table.id == "table9f-" + expected["date"]
        assert meta.context.source_date_label == expected["label"]
        assert not meta.segmentations
        assert len(table.cells) == 6
        axes = {a.id: a for a in meta.axes}
        assert axes["panel"].source_label == expected["label"]
        assert axes["default-rate"].source_label == "Default rate"
        assert axes["lgd"].source_label == "Loss Given Default"
        assert axes["mortgage"].source_label == "Residential mortgages"
        for c, f, spec, token in zip(
            table.cells,
            meta.published_fields,
            golden["backtesting_fields"],
            expected["tokens"],
            strict=True,
        ):
            key, label, unit, path, qs = spec
            binding = occurrences[table.id, "field", key]
            fragment = binding.physical_refs[0]
            assert captured[
                fragment.binding_ref, fragment.slot
            ].text == label.translate(str.maketrans("¹²", "12"))
            assert (
                f.id,
                f.source_label,
                f.source_unit,
                list(f.header_path_refs),
                list(f.qualification_refs),
            ) == (key, label, unit, path, qs)
            assert axes[key].header_path_refs == tuple(path[:-1])
            assert c.qualification_refs == tuple(qs)
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
        assert desc["annual-outcome"].duration_amount == 1
        assert desc["annual-outcome"].duration_unit == "year"
        for key in set(desc) - {"measurement"}:
            assert (
                desc[key].point is None
                and desc[key].start is None
                and desc[key].end is None
            )
        assert {
            (b.cell_id, b.role, b.descriptor_ref) for b in meta.temporal_bindings
        } == {
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
