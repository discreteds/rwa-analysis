"""Master copies selected staging publications and owns its persisted result."""

from decimal import Decimal

from mountainash_data import IbisBackend


def master_store(root):
    from rwa_analysis.composition import build_consolidator
    from rwa_analysis.settings import ProjectSettings

    return build_consolidator(ProjectSettings(project_root=root))


def test_master_retains_staging_values_metadata_and_sources(published_cr6, retained):
    from rwa_analysis.domains.cr6.contracts import TABLES

    root, _ = retained
    master = master_store(root)
    publications = tuple(publication for _, publication in published_cr6)
    cba_key = "au/cba/2025-06-30/aps330/cr6-residential-mortgages"
    # Consolidation must copy these persisted values, not rerun Bronze conformance.
    with IbisBackend(dialect="duckdb", database=str(publications[0].database)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.cr6_observations SET ead_amount = 281509000000 "
            "WHERE observation_id = ?",
            [f"{cba_key}/band-1"],
        )
    staging_outputs = [session.silver.read(p) for session, p in published_cr6]
    expected = {
        table.member: [
            row
            for output in staging_outputs
            for row in getattr(output, table.member).to_dicts()
        ]
        for table in TABLES
    }
    publication = master.consolidate(publications, revision="combined")
    output = master.store.read(publication)
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
    tables = master.reconstruct(publication)
    assert len(tables) == 4
    assert tables[cba_key].row(0)[4] == Decimal(281509)
    manifest = master.read_manifest(publication)
    assert manifest.staging_manifests == tuple(p.manifest_path for p in publications)


def test_master_rebuild_replaces_removed_organisations(published_cr6, retained):
    from rwa_analysis.domains.cr6.contracts import TABLES

    root, _ = retained
    master = master_store(root)
    publications = tuple(publication for _, publication in published_cr6)
    master.consolidate(publications, revision="all")
    publication = master.consolidate(publications[:1], revision="cba-only")
    output = master.store.read(publication)
    assert output.contexts.count_rows() == 1
    assert output.contexts.item("organisation_id") == "cba"
    expected = published_cr6[0][0].silver.read(publications[0])
    for table in TABLES:
        actual = getattr(output, table.member).to_polars().sort(table.spec.primary_key)
        selected = (
            getattr(expected, table.member).to_polars().sort(table.spec.primary_key)
        )
        assert actual.equals(selected), table.member
    publication = master.consolidate((), revision="empty")
    output = master.store.read(publication)
    assert all(getattr(output, table.member).count_rows() == 0 for table in TABLES)
    assert master.reconstruct(publication) == {}
