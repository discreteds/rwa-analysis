"""Source-specific conformance; persisted behaviour is owned by workflow tests."""

from decimal import Decimal

import polars as pl

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.storage.bronze import BronzeStore


def conformed_cr9(westpac_bundle, project_root, tmp_path):
    datasets = [d for d in westpac_bundle.datasets if hasattr(d, "backtesting_rows")]
    assert len(datasets) == 1, "Westpac's saved source bundle must include CR9"
    from rwa_analysis.domains.cr9.pipeline import Cr9Pipeline

    store = BronzeStore(tmp_path / "bronze")
    ref = store.save(westpac_bundle, "cr9-test")
    catalogue = load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json")
    return Cr9Pipeline().conform((store.load(ref),), catalogue), datasets[0]


def test_westpac_source_measures_and_missing_default_cells(
    westpac_bundle, project_root, tmp_path
):
    output, dataset = conformed_cr9(westpac_bundle, project_root, tmp_path)
    rows = output.observations.to_polars()
    assert rows.height == 8
    first = rows.filter(
        pl.col("source_record_id") == dataset.backtesting_rows[0].record_id
    ).row(0, named=True)
    assert first["weighted_average_pd"] == Decimal("0.00070000")
    assert first["historical_annual_default_rate"] == Decimal("0.00060000")
    assert first["previous_year_borrower_count"] == 564613
    assert first["current_year_borrower_count"] == 571083
    assert first["defaulted_borrower_count"] == 385
    assert first["new_defaulted_borrower_count"] == 7
    default = rows.filter(
        pl.col("source_record_id") == dataset.backtesting_rows[-1].record_id
    ).row(0, named=True)
    assert default["weighted_average_pd"] == Decimal("1.00000000")
    assert default["historical_annual_default_rate"] is None
    assert default["defaulted_borrower_count"] is None
    fields = output.fields.to_polars().filter(
        (pl.col("source_record_id") == dataset.backtesting_rows[-1].record_id)
        & (pl.col("field_key") == "historical_annual_default_rate")
    )
    assert fields["value_state"].item() == "source_missing"
    assert fields["missing_reason"].item() is not None


def test_field_times_and_source_evidence_survive_conformance(
    westpac_bundle, project_root, tmp_path
):
    output, dataset = conformed_cr9(westpac_bundle, project_root, tmp_path)
    oid = (
        output.observations.to_polars()
        .filter(pl.col("source_record_id") == dataset.backtesting_rows[0].record_id)[
            "observation_id"
        ]
        .item()
    )
    tagged = output.temporal_bindings.join(
        output.temporal_descriptors, on="descriptor_id"
    ).to_polars()
    tagged = tagged.filter(pl.col("observation_id") == oid)
    weighted = tagged.filter(
        (pl.col("field_key") == "weighted_average_pd")
        & (pl.col("role") == "measurement")
    )
    assert weighted["point"].item() == "2024-06"
    annual = tagged.filter(
        (pl.col("field_key") == "defaulted_borrower_count")
        & (pl.col("role") == "outcome_window")
    )
    assert annual["start"].item() == "2024-07-01"
    assert annual["end"].item() == "2025-06-30"
    history = tagged.filter(
        (pl.col("field_key") == "historical_annual_default_rate")
        & (pl.col("role") == "history_window")
    )
    assert history["duration_amount"].item() == Decimal(10)
    assert history["start"].item() is None
    assert history["end_status"].item() == "unresolved"
    evidence = output.temporal_evidence.to_polars().filter(
        pl.col("descriptor_id") == history["descriptor_id"].item()
    )
    assert 56 in evidence["source_pdf_page"].to_list()


def test_new_defaults_are_a_field_subset_within_each_row(
    westpac_bundle, project_root, tmp_path
):
    output, _ = conformed_cr9(westpac_bundle, project_root, tmp_path)
    relationships = output.relationships.to_polars().filter(
        pl.col("relationship_kind") == "subset"
    )
    # Seven event-count rows: the default-stock row has no published event counts.
    assert relationships.height == 7
    assert (
        relationships["parent_field_key"].to_list() == ["defaulted_borrower_count"] * 7
    )
    assert (
        relationships["child_field_key"].to_list()
        == ["new_defaulted_borrower_count"] * 7
    )
    assert (
        relationships["parent_observation_id"].to_list()
        == relationships["child_observation_id"].to_list()
    )
    assert output.relationship_evidence.to_polars().height >= 7


def test_reconstruction_preserves_published_measure_column_order(
    westpac_bundle, project_root, tmp_path
):
    from rwa_analysis.domains.cr9.reconstruction import reconstruct_cr9

    output, _ = conformed_cr9(westpac_bundle, project_root, tmp_path)
    table = next(iter(reconstruct_cr9(output, (westpac_bundle,)).values()))
    # Westpac p.55 puts the historical rate after all four count columns.
    assert table.columns == [
        "source_row",
        "Weighted\naverage PDb",
        "Arithmetic\naverage PD\nby borrowers",
        "End of\nprevious year",
        "End of the year",
        "Non-performing\nborrowers in\nthe yearc",
        "of which: new\nNon-performing\nborrowers in\nthe year",
        "Average\nhistorical annual\ndefault rated",
    ]


def test_default_stock_counts_retain_the_row_default_definition(
    westpac_bundle, project_root, tmp_path
):
    output, dataset = conformed_cr9(westpac_bundle, project_root, tmp_path)
    fields = output.fields.to_polars()
    qualifications = output.field_qualifications.to_polars().join(
        fields.select("observation_id", "field_key", "source_record_id"),
        on=["observation_id", "field_key"],
    )
    counts = qualifications.filter(
        pl.col("field_key").is_in(
            ["previous_year_borrower_count", "current_year_borrower_count"]
        )
        & (pl.col("qualification_ref") == "default-definition")
    )
    assert counts.height == 2
    assert set(counts["source_record_id"]) == {dataset.backtesting_rows[-1].record_id}
