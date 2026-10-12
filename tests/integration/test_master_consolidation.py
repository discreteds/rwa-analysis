"""Master copies selected staging publications and owns its persisted result."""

from decimal import Decimal

from mountainash_data import IbisBackend


def master_store(root):
    from rwa_analysis.composition import build_consolidator
    from rwa_analysis.settings import ProjectSettings

    return build_consolidator(ProjectSettings(project_root=root))


def test_master_retains_staging_values_metadata_and_sources(published_banks, retained):
    from rwa_analysis.domains.cr6.contracts import TABLES
    from rwa_analysis.extraction.cr6 import Cr6Dataset

    root, _ = retained
    master = master_store(root)
    publications = tuple(publication for _, publication in published_banks)
    cba_key = "au/cba/2025-06-30/aps330/cr6-residential-mortgages"
    # Consolidation must copy these persisted values, not rerun Bronze conformance.
    with IbisBackend(dialect="duckdb", database=str(publications[0].database)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.cr6_observations SET ead_amount = 281509000000 "
            "WHERE observation_id = ?",
            [f"{cba_key}/band-1"],
        )
    staging_outputs = [session.silver.read(p).cr6 for session, p in published_banks]
    cr6_keys = {
        f"{bundle.bundle_key}/{ds.id}"
        for session, p in published_banks
        for bundle in session.silver.read_sources(p)
        for ds in bundle.datasets
        if isinstance(ds, Cr6Dataset)
    }
    expected = {
        table.member: [
            row
            for output in staging_outputs
            for row in getattr(output, table.member).to_dicts()
        ]
        for table in TABLES
    }
    publication = master.consolidate(publications, revision="combined")
    output = master.store.read(publication).cr6
    for table in TABLES:
        keys = table.spec.primary_key
        key = lambda row, keys=keys: tuple(row[name] for name in keys)
        actual = getattr(output, table.member).to_dicts()
        assert sorted(actual, key=key) == sorted(expected[table.member], key=key), (
            table.member
        )
    assert output.observations.count_rows() == 36
    assert output.fields.count_rows() == 432
    assert output.field_mappings.count_rows() == 1296
    assert output.relationships.count_rows() == 32
    # Readback uses master values and retained manifests even after staging is gone.
    for staging in publications:
        staging.database.unlink()
    tables = {
        key: table
        for key, table in master.reconstruct(publication).items()
        if key in cr6_keys
    }
    assert len(tables) == 4
    assert tables[cba_key].row(0)[4] == Decimal(281509)
    manifest = master.read_manifest(publication)
    assert manifest.staging_manifests == tuple(p.manifest_path for p in publications)


def test_master_rebuild_replaces_removed_organisations(published_banks, retained):
    from rwa_analysis.storage.tables import DOMAINS

    root, _ = retained
    master = master_store(root)
    publications = tuple(publication for _, publication in published_banks)
    master.consolidate(publications, revision="all")
    publication = master.consolidate(publications[:1], revision="cba-only")
    output = master.store.read(publication)
    expected = published_banks[0][0].silver.read(publications[0])
    for selected_domain in (output.cr6, output.cr9):
        assert selected_domain.contexts.count_rows() == 1
        assert selected_domain.contexts.item("organisation_id") == "cba"
    assert output.source_tables.tables.count_rows() == 0
    for domain, _, tables in DOMAINS:
        actual_domain, expected_domain = (
            getattr(output, domain),
            getattr(expected, domain),
        )
        for table in tables:
            actual = (
                getattr(actual_domain, table.member)
                .to_polars()
                .sort(table.spec.primary_key)
            )
            selected = (
                getattr(expected_domain, table.member)
                .to_polars()
                .sort(table.spec.primary_key)
            )
            assert actual.equals(selected), (domain, table.member)
    publication = master.consolidate((), revision="empty")
    output = master.store.read(publication)
    assert all(
        getattr(getattr(output, domain), table.member).count_rows() == 0
        for domain, _, tables in DOMAINS
        for table in tables
    )
    assert master.reconstruct(publication) == {}


def test_master_owns_cr9_values_temporal_metadata_and_reconstruction(
    published_banks, retained
):
    import polars as pl

    from rwa_analysis.domains.cr9.contracts import TABLES

    root, _ = retained
    master = master_store(root)
    publications = tuple(p for _, p in published_banks)
    westpac_session, westpac = published_banks[1]
    source = westpac_session.silver.read(westpac).cr9
    first = (
        source.observations.to_polars()
        .filter(pl.col("source_record_id") == "band-1")
        .row(0, named=True)
    )
    history = (
        source.temporal_descriptors.to_polars()
        .filter(pl.col("source_descriptor_ref") == "history")["descriptor_id"]
        .item()
    )
    # Deliberate persisted changes prove master copies staging rather than recomputing.
    with IbisBackend(dialect="duckdb", database=str(westpac.database)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.cr9_observations SET historical_annual_default_rate = 0.0007 WHERE observation_id = ?",
            [first["observation_id"]],
        )
        db.raw_driver_connection().execute(
            "UPDATE silver.cr9_temporal_descriptors SET duration_amount = 9 WHERE descriptor_id = ?",
            [history],
        )
    staging = [session.silver.read(p).cr9 for session, p in published_banks]
    publication = master.consolidate(publications, revision="mixed")
    output = master.store.read(publication).cr9
    assert output.observations.count_rows() == 33
    for table in TABLES:
        expected = pl.concat(
            [getattr(part, table.member).to_polars() for part in staging]
        ).sort(table.spec.primary_key)
        assert (
            getattr(output, table.member)
            .to_polars()
            .sort(table.spec.primary_key)
            .equals(expected)
        ), table.member
    for p in publications:
        p.database.unlink()
    tables = master.reconstruct(publication)
    assert len(tables) == 8
    assert tables["au/westpac/2025-09-30/aps330/cr9-residential-mortgages"][
        "Average\nhistorical annual\ndefault rated"
    ][0] == Decimal("0.07")
