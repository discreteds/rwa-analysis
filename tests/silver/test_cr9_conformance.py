"""Source-specific conformance; persisted behaviour is owned by workflow tests."""

from decimal import Decimal

import polars as pl

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.storage.bronze import BronzeStore


def conformed_cr9(westpac_bundle, project_root, tmp_path):
    datasets = [d for d in westpac_bundle.datasets if hasattr(d, "backtesting_rows")]
    assert len(datasets) == 1, "Westpac's saved source bundle must include CR9"
    from rwa_analysis.domains.cr9.projection import project_cr9
    from rwa_analysis.domains.source_tables.legacy import domain_bindings
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline

    store = BronzeStore(tmp_path / "bronze")
    ref = store.save(westpac_bundle, "cr9-test")
    catalogue = load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json")
    loaded = store.load(ref)
    return project_cr9(
        SourceTablePipeline().conform((loaded,), catalogue),
        domain_bindings(loaded.bundle),
    ), datasets[0]


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
    # A band owns its entire source reference, including an unknown column.
    assert first["source_column"] is None
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
    assert relationships.filter(
        pl.col("parent_observation_id").str.ends_with("/band-1")
    )["relationship_id"].item() == (
        "au/westpac/2025-09-30/aps330/cr9-residential-mortgages/context/"
        "new-defaults-band-1/band-1/band-1/new_defaulted_borrower_count"
    )


def test_relationship_endpoints_use_kind_not_local_id_spelling(
    westpac_bundle, project_root
):
    from dataclasses import replace

    from rwa_analysis.domains.cr9.projection import project_cr9
    from rwa_analysis.domains.source_tables.legacy import adapt_legacy, domain_bindings
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
    from rwa_analysis.extraction.models import SourceEndpoint
    from rwa_analysis.storage.bronze import BronzeRef, LoadedBronze

    table = adapt_legacy(westpac_bundle.datasets[1])
    ids = {c.id: f"opaque-{i}" for i, c in enumerate(table.cells)}
    # Two fully explicit cells can connect across rows; they need no slash in IDs.
    original = table.metadata.relationships[0]
    cross = replace(
        original,
        id="cross-cells",
        scope=(),
        parent=SourceEndpoint("cell", ids["band-1/weighted_average_pd"]),
        children=(SourceEndpoint("cell", ids["band-2/weighted_average_pd"]),),
    )
    # Conversely, slashes in FIELD IDs do not make cross-row cell endpoints.
    slash_fields = {
        "defaulted_borrower_count": "events/total",
        "new_defaulted_borrower_count": "events/new",
    }
    within = replace(
        original,
        id="field-subset",
        scope=(),
        parent=SourceEndpoint("field", "events/total"),
        children=(SourceEndpoint("field", "events/new"),),
    )
    table = replace(
        table,
        cells=tuple(
            replace(
                c, id=ids[c.id], field_ref=slash_fields.get(c.field_ref, c.field_ref)
            )
            for c in table.cells
        ),
        metadata=replace(
            table.metadata,
            published_fields=tuple(
                replace(f, id=slash_fields.get(f.id, f.id))
                for f in table.metadata.published_fields
            ),
            relationships=(cross, within),
            temporal_bindings=(),
        ),
    )
    bindings = tuple(
        replace(b, ref=replace(b.ref, local_id=ids[b.ref.local_id]))
        for b in domain_bindings(westpac_bundle)
        if b.domain == "cr9"
    )
    bundle = replace(westpac_bundle, datasets=(table,), schema_version="disclosure-v3")
    source = SourceTablePipeline().conform(
        (LoadedBronze(BronzeRef(bundle.bundle_key, "opaque"), bundle),),
        load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json"),
    )
    edges = project_cr9(source, bindings).relationships.to_polars()
    cross_edges = edges.filter(pl.col("source_relationship_ref") == "cross-cells")
    assert cross_edges.height == 1
    assert cross_edges["parent_observation_id"].item().endswith("/band-1")
    assert cross_edges["child_observation_id"].item().endswith("/band-2")
    within_edges = edges.filter(pl.col("source_relationship_ref") == "field-subset")
    assert within_edges.height == 8
    assert (
        within_edges["parent_observation_id"].to_list()
        == within_edges["child_observation_id"].to_list()
    )


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
