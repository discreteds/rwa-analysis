import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from rwa_analysis.extraction.codec import encode_payload
from rwa_analysis.extraction.runner import run_extractor
from tests.support.captured_golden import assert_capture_bindings, golden_view
from tests.support.golden import assert_golden


def test_complete_anz_source_contract():
    root = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "AGENTS.md").exists() and (p / "raw").is_dir()
    )
    pdf = root / "raw/anz-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/anz/2025-09-30/aps330/extract.py", pdf
    )
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert bundle.schema_version == "disclosure-v4"
    assert_capture_bindings(bundle, 189)
    bundle = golden_view(bundle)
    assert_golden(
        encode_payload(
            replace(bundle, schema_version="cr6-v1", datasets=bundle.datasets[:1])
        ),
        expected,
    )
    assert len(bundle.datasets) == 2
    dataset = bundle.datasets[1]
    golden = json.loads(Path(__file__).with_name("golden-cr9.json").read_text())
    metadata = dataset.metadata
    assert dataset.id == "cr9-residential-mortgages"
    assert metadata.context.source_title == golden["title"]
    assert metadata.context.source_portfolio_label == golden["portfolio"]
    assert metadata.context.regulatory_scope.value == "AIRB"
    fields = {f.id: f for f in metadata.published_fields}
    assert list(fields) == golden["fields"]
    assert [f.source_label for f in fields.values()] == golden["headers"]
    axes = {a.id: a for a in metadata.axes}
    rows = dataset.backtesting_rows
    assert len(rows) == 9
    for i, (row, label, tokens, ratings, source_row) in enumerate(
        zip(
            rows,
            golden["bands"],
            golden["tokens"],
            golden["ratings"],
            golden["source_rows"],
            strict=True,
        )
    ):
        assert axes[row.source_row_ref].source_label == label
        assert row.source_row_role == (label if i == 8 else "band")
        assert row.source_segment_memberships == (
            () if i == 8 else (f"pd-band-{i + 1}",)
        )
        for j, rating in enumerate(ratings):
            axis = axes[f"{row.record_id}-rating-{j}"]
            assert axis.source_label == rating
            assert axis.header_path_refs == (row.record_id, f"rating-{j}")
            assert axis.source_reference.column == golden["agencies"][j]
        for name, token, header in zip(
            golden["fields"], tokens, golden["headers"], strict=True
        ):
            cell = getattr(row, name)
            missing = token in ("", "-")
            assert cell.original_text == token
            assert cell.value == (
                None if missing else Decimal(token.replace(",", "").rstrip("%"))
            )
            assert cell.displayed_precision == (
                None if missing else 0 if name.endswith("count") else 2
            )
            assert cell.missing_reason == (
                ("dash_unresolved" if token == "-" else "blank_unresolved")
                if missing
                else None
            )
            assert cell.source_reference.pdf_page == 66
            assert cell.source_reference.row == source_row
            assert cell.source_reference.column == header
            assert fields[name].source_unit == ("" if name.endswith("count") else "%")
            if not missing:
                assert type(cell.value) is (int if name.endswith("count") else Decimal)
    assert axes["date"].source_label == "Sep 25"
    assert axes["approach"].source_label == "AIRB"
    assert axes["pd-heading"].source_label == "Portfolio/\nPD scale"
    assert axes["borrower-counts"].source_label == "Number of Borrowers"
    for i, agency in enumerate(golden["agencies"]):
        assert axes[f"rating-{i}"].source_label == agency
        assert (
            axes[f"external-ratings-{i}"].source_label == "External rating\nequivalent"
        )
        assert axes[f"rating-{i}"].qualification_refs == ("cr9-ratings",)
    for binding in metadata.bindings:
        assert binding.row_refs == tuple(row.record_id for row in rows)
        assert binding.published_field_ref == binding.typed_field_name
        assert binding.column_refs == ("column-" + binding.typed_field_name,)
    bands = metadata.segmentations[0].bands
    assert len(bands) == 8
    for i, band in enumerate(bands):
        assert band.source_label == golden["bands"][i]
        assert band.kind == ("default" if i == 7 else "interval")
        if i < 7:
            lower, upper = golden["bands"][i].split(" to <")
            assert (band.lower, band.upper) == (Decimal(lower), Decimal(upper))
            assert band.lower_inclusive is True and band.upper_inclusive is False
        else:
            assert band.lower is band.upper is None
            assert band.category == "100.00 (Default)"
    notes = {n.id: n for n in metadata.qualifications}
    for name, text in golden["notes"].items():
        assert notes[name].source_text == text
        assert notes[name].evidence[0].pdf_page == 66
    assert notes["cr9-corporate-history-context"].source_text == golden["appendix"]
    assert notes["cr9-corporate-history-context"].evidence[0].pdf_page == 116
    assert fields["historical_annual_default_rate"].qualification_refs == (
        "cr9-history",
        "cr9-history-exclusions",
        "cr9-corporate-history-context",
    )
    descriptors = {d.id: d for d in metadata.temporal_descriptors}
    assert set(descriptors) == {
        "history",
        "annual",
        "previous-year",
        "current-year",
        "unspecified",
    }
    for descriptor in descriptors.values():
        assert descriptor.point is descriptor.start is descriptor.end is None
        assert (
            descriptor.point_status
            == descriptor.start_status
            == descriptor.end_status
            == "unresolved"
        )
    assert descriptors["history"].duration_amount == Decimal(5)
    assert descriptors["history"].duration_unit == "years"
    assert descriptors["history"].duration_status == "established"
    assert {
        (b.record_id, b.field_key, b.role, b.descriptor_ref)
        for b in metadata.temporal_bindings
    } == {(row.record_id, *role) for row in rows for role in golden["roles"]}
    relationships = {r.id: r for r in metadata.relationships}
    total = relationships.pop("mortgage-subtotal")
    assert total.kind == "total"
    assert total.parent.id == rows[-1].record_id
    assert tuple(c.id for c in total.children) == tuple(r.record_id for r in rows[:-1])
    assert len(relationships) == 8
    for i, row in enumerate(rows):
        if i == 7:
            continue
        subset = relationships["new-defaults-" + row.record_id]
        assert subset.parent.id == "defaulted_borrower_count"
        assert tuple(c.id for c in subset.children) == ("new_defaulted_borrower_count",)
        assert tuple(s.id for s in subset.scope) == (row.record_id,)


def test_anz_meanings_keep_history_exclusions_and_unknown_annual_cohort(
    project_root, anz_bundle
):
    """Catch Westpac timing/weighting or corporate history leaking into ANZ."""
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.domains.cr9.semantics import resolve_field

    catalogue = load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json")
    dataset = anz_bundle.datasets[1]
    history = resolve_field(
        catalogue,
        dataset,
        dataset.backtesting_rows[-1],
        "historical_annual_default_rate",
    )
    assert history.unit_factor == Decimal("0.01")
    assert history.attribute("aggregation").value == "historical_average_over_5_years"
    assert (
        history.attribute("population_exclusion").value
        == "technical defaults excluded from numerator; exited obligors excluded from denominator"
    )
    assert history.attribute("denominator").status == "unresolved"
    assert history.attribute("row_role").value == "portfolio_aggregate"
    assert (
        history.attribute("population").value.revision_id
        == "population.residential-mortgages@v1"
    )
    weighted = resolve_field(
        catalogue, dataset, dataset.backtesting_rows[0], "weighted_average_pd"
    )
    assert weighted.attribute("weighting").status == "unresolved"
    assert weighted.attribute("weight_measure").status == "unresolved"
    for i, row in enumerate(dataset.backtesting_rows[:8], 1):
        meaning = resolve_field(catalogue, dataset, row, "weighted_average_pd")
        assert meaning.attribute("pd_band").value.ref_id == f"pd-band-{i}"
        assert meaning.attribute("row_role").value == "band"
    for name in (
        "previous_year_borrower_count",
        "current_year_borrower_count",
        "defaulted_borrower_count",
        "new_defaulted_borrower_count",
    ):
        meaning = resolve_field(catalogue, dataset, dataset.backtesting_rows[0], name)
        assert meaning.unit_factor == Decimal(1)
        assert meaning.attribute("counted_entity").status == "unresolved"
        assert meaning.attribute("cohort_eligibility").status == "unresolved"
        assert meaning.concept_ref.revision_id == "count.reported-borrowers@v1"
