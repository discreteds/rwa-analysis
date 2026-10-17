"""Persisted mixed-domain workflow and source-occurrence metadata linkage."""

import json
from dataclasses import replace
from decimal import Decimal

import polars as pl
import pytest
from mountainash_data import IbisBackend

from rwa_analysis.composition import build_session
from rwa_analysis.domains.source_tables.reconstruction import reconstruct_source_tables
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection


@pytest.fixture
def westpac_session(project_root, tmp_path):
    return build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id="westpac",
            bronze_root=tmp_path / "bronze",
            manifest_root=tmp_path / "manifests",
            staging_path=tmp_path / "westpac.duckdb",
        )
    )


CATALOGUE = CatalogueSelection(release_path="catalogue/releases/cr6-cr9-v1.json")


def publish_bundles(session, bundles, revision):
    refs = session.save_bronze(bundles, revision)
    candidate = session.conform(session.load_bronze(refs), catalogue=CATALOGUE)
    return session.publish(candidate, revision)


@pytest.mark.parametrize(
    "org,date,count_columns",
    [
        (
            "cba", "2025-06-30",
            ("previous_year_borrower_count", "current_year_borrower_count"),
        ),
        (
            "westpac", "2025-09-30",
            ("previous_year_borrower_count", "current_year_borrower_count"),
        ),
        (
            "nab", "2025-09-30",
            ("current_year_borrower_count", "previous_year_borrower_count"),
        ),
        (
            "anz", "2025-09-30",
            ("previous_year_borrower_count", "current_year_borrower_count"),
        ),
    ],
)
def test_live_cr9_source_frame_preserves_column_order(
    project_root, tmp_path, org, date, count_columns
):
    # PDF CBA60, Westpac55 and ANZ66 put both rating columns before PDs.
    # NAB61 prints current then previous counts; its ratings are referenced
    # from PDF46, prepended in the retained source projection (not on PDF61).
    session = build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id=org,
            bronze_root=tmp_path / "bronze",
            manifest_root=tmp_path / "manifests",
            staging_path=tmp_path / f"{org}.duckdb",
        )
    )
    result = session.run(
        documents=(
            DocumentSelection(
                f"extractions/au/{org}/{date}/aps330/extract.py",
                f"raw/{org}-{date}-aps330.pdf",
            ),
        ),
        catalogue=CATALOGUE,
        run_name="source-order",
        revision="source-order",
    )
    output = session.silver.read(result.publication)
    source = reconstruct_source_tables(output.source_tables)
    frame = source[f"au/{org}/{date}/aps330/cr9-residential-mortgages"].frame
    assert frame.columns == [
        "source_row_id",
        "source_row",
        "rating-0",
        "rating-1",
        "column-weighted_average_pd",
        "column-arithmetic_average_pd",
        *(f"column-{name}" for name in count_columns),
        "column-defaulted_borrower_count",
        "column-new_defaulted_borrower_count",
        "column-historical_annual_default_rate",
    ]


def test_real_westpac_mixed_run_reconstructs_persisted_numbers(westpac_session):
    session = westpac_session
    result = session.run(
        documents=(
            DocumentSelection(
                "extractions/au/westpac/2025-09-30/aps330/extract.py",
                "raw/westpac-2025-09-30-aps330.pdf",
            ),
        ),
        catalogue=CATALOGUE,
        run_name="mixed-review",
        revision="mixed-review",
    )
    bundle = result.bundles[0]
    assert bundle.schema_version == "disclosure-v4"
    output = session.silver.read(result.publication)
    assert output.cr6.observations.count_rows() == 9
    assert output.cr9.observations.count_rows() == 8
    ds = next(d for d in bundle.datasets if d.metadata.context.source_template == "CR9")
    key = f"{bundle.bundle_key}/{ds.id}"
    first = (
        output.cr9.observations.to_polars()
        .filter(pl.col("source_record_id") == "band-1")
        .row(0, named=True)
    )
    assert first["historical_annual_default_rate"] == Decimal("0.00060000")
    assert first["defaulted_borrower_count"] == 385
    assert first["new_defaulted_borrower_count"] == 7
    # This mutation distinguishes persisted reconstruction from a Bronze/candidate copy.
    with IbisBackend(dialect="duckdb", database=str(result.publication.database)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.cr9_observations SET historical_annual_default_rate = 0.0007 "
            "WHERE observation_id = ?",
            [first["observation_id"]],
        )
    table = session.reconstruct(result.publication)[key]
    binding = next(
        b
        for b in bundle.snapshot.domain_bindings
        if b.ref.scope == ds.id and b.field_key == "historical_annual_default_rate"
    )
    label = next(
        f.source_label
        for f in ds.metadata.published_fields
        if f.id == next(c.field_ref for c in ds.cells if c.id == binding.ref.local_id)
    )
    assert table.height == 8
    assert table[label][0] == Decimal("0.07")
    assert set(result.tables) == {
        f"{bundle.bundle_key}/cr6-residential-mortgages",
        f"{bundle.bundle_key}/cr9-residential-mortgages",
    }
    assert output.source_tables.cells.count_rows() == 185
    assert (
        session.silver.read_manifest(result.publication).selection.catalogue
        == CATALOGUE
    )


def test_temporal_occurrences_and_field_subset_survive_storage(
    westpac_session, westpac_bundle
):
    from rwa_analysis.extraction.codec import decode_payload, encode_payload

    # Synthetic second document/dataset, NOT evidence of a real restatement.
    # Change every document reference through the transport representation.
    payload = encode_payload(westpac_bundle)
    synthetic = json.loads(
        json.dumps(payload).replace(
            westpac_bundle.document.document_id, "synthetic-history-document"
        )
    )
    synthetic["bundle_key"] = "au/westpac/2025-09-30/synthetic-history"
    second = decode_payload(synthetic)
    ds = next(d for d in second.datasets if d.metadata.context.source_template == "CR9")
    descriptors = tuple(
        replace(
            t, duration_amount=Decimal(5), source_label="Synthetic five-year history"
        )
        if t.id == "history"
        else t
        for t in ds.metadata.temporal_descriptors
    )
    second = replace(
        second,
        datasets=(
            replace(
                ds,
                id="synthetic-cr9",
                metadata=replace(ds.metadata, temporal_descriptors=descriptors),
            ),
        ),
    )
    publication = publish_bundles(
        westpac_session, (westpac_bundle, second), "two-occurrences"
    )
    stored = westpac_session.silver.read(publication).cr9
    histories = stored.temporal_descriptors.to_polars().filter(
        pl.col("source_descriptor_ref") == "history"
    )
    assert histories.height == 2
    assert histories["descriptor_id"].n_unique() == 2
    assert set(histories["duration_amount"]) == {Decimal(5), Decimal(10)}
    assert histories["start"].null_count() == 2
    assert histories["end"].null_count() == 2
    linked = (
        stored.temporal_bindings.to_polars()
        .filter(pl.col("role") == "history_window")
        .join(histories, on="descriptor_id")
        .join(
            stored.observations.to_polars().select("observation_id", "context_id"),
            on="observation_id",
            suffix="_observation",
        )
    )
    assert linked.height == 16
    assert linked["context_id"].equals(linked["context_id_observation"])
    assert set(linked.filter(pl.col("duration_amount") == 5)["observation_id"]) == {
        f"{second.bundle_key}/{second.datasets[0].id}/{r.record_id}"
        for r in ds.backtesting_rows
    }
    real_ds = next(
        d
        for d in westpac_bundle.datasets
        if d.metadata.context.source_template == "CR9"
    )
    oid = f"{westpac_bundle.bundle_key}/{real_ds.id}/{real_ds.backtesting_rows[0].record_id}"
    subset = (
        stored.relationships.to_polars()
        .filter(
            (pl.col("parent_observation_id") == oid)
            & (pl.col("child_observation_id") == oid)
        )
        .row(0, named=True)
    )
    assert subset["parent_field_key"] == "defaulted_borrower_count"
    assert subset["child_field_key"] == "new_defaulted_borrower_count"
    assert subset["relationship_kind"] == "subset"
    evidence = stored.relationship_evidence.to_polars().filter(
        pl.col("relationship_id") == subset["relationship_id"]
    )
    assert evidence.height > 0
    assert set(evidence["source_pdf_page"]) <= {55, 56}
    assert stored.temporal_evidence.count_rows() > 0


@pytest.mark.parametrize(
    "retained_domain,removed_domain", [("cr6", "cr9"), ("cr9", "cr6")]
)
def test_rebuild_clears_omitted_domain(
    westpac_session, westpac_bundle, retained_domain, removed_domain
):
    from rwa_analysis.domains.cr6.contracts import TABLES as CR6_TABLES
    from rwa_analysis.domains.cr9.contracts import TABLES as CR9_TABLES

    publish_bundles(westpac_session, (westpac_bundle,), "mixed")
    smaller = replace(
        westpac_bundle,
        datasets=tuple(
            ds
            for ds in westpac_bundle.datasets
            if ds.metadata.context.source_template.lower() == retained_domain
        ),
    )
    publication = publish_bundles(westpac_session, (smaller,), "one-domain")
    output = westpac_session.silver.read(publication)
    assert getattr(output, retained_domain).observations.count_rows() > 0
    removed = getattr(output, removed_domain)
    # Full replacement must clear metadata as well as numbers; these were populated.
    tables = CR9_TABLES if removed_domain == "cr9" else CR6_TABLES
    for table in tables:
        relation = getattr(removed, table.member)
        assert relation.count_rows() == 0, table.member
        assert relation.to_polars().width > 0, table.member
    assert len(westpac_session.reconstruct(publication)) == 1
