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


def test_source_master_copies_metadata_replaces_inputs_and_survives_staging_removal(
    project_root, tmp_path, cba_2024_bundle, westpac_bundle
):
    from dataclasses import replace

    import mountainash as ma

    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.composition import build_session
    from rwa_analysis.domains.source_tables.contracts import TABLES
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
    from rwa_analysis.domains.source_tables.reconstruction import (
        reconstruct_source_tables,
    )
    from rwa_analysis.settings import OrganisationSettings
    from rwa_analysis.storage.manifests import CatalogueSelection

    publications = []
    sessions = []
    for bundle, release in (
        (cba_2024_bundle, "historical-mortgages-v1"),
        (westpac_bundle, "cr6-cr9-v1"),
    ):
        org = bundle.document.organisation_id
        session = build_session(
            OrganisationSettings(
                project_root=project_root,
                organisation_id=org,
                bronze_root=tmp_path / "bronze",
                staging_path=tmp_path / f"{org}.duckdb",
                manifest_root=tmp_path / "manifests",
            )
        )
        inputs = session.load_bronze(session.save_bronze((bundle,), "master-proof"))
        selection = CatalogueSelection(
            release_path=f"catalogue/releases/{release}.json"
        )
        candidate = session.conform(inputs, catalogue=selection)
        if org == "westpac":
            candidate = replace(
                candidate,
                source_tables=SourceTablePipeline().conform(
                    inputs, load_catalogue(project_root / selection.release_path)
                ),
            )
        publications.append(session.publish(candidate, revision=org))
        sessions.append(session)
    cba_key = cba_2024_bundle.bundle_key + "/table9d-ii-2024-06-30"
    with IbisBackend(dialect="duckdb", database=str(publications[0].database)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.source_cells SET source_number = 0.888 WHERE table_id = ? AND cell_id = ?",
            [cba_key, "average_ead/band-0"],
        )
        db.raw_driver_connection().execute(
            "UPDATE silver.source_qualifications SET source_text = ? WHERE table_id = ? AND qualification_id = ?",
            ["Persisted research correction", cba_key, "pd-horizon"],
        )
    staging = [
        s.silver.read(p).source_tables
        for s, p in zip(sessions, publications, strict=True)
    ]
    master = master_store(tmp_path)
    publication = master.consolidate(tuple(publications), revision="combined-source")
    source = master.store.read(publication).source_tables
    for t in TABLES:
        expected = (
            ma.concat([getattr(s, t.member) for s in staging])
            .sort(*t.spec.primary_key)
            .to_dicts()
        )
        assert (
            getattr(source, t.member).sort(*t.spec.primary_key).to_dicts() == expected
        ), t.member
    for p in publications:
        p.database.unlink()
    tables = master.reconstruct(publication)
    assert tables[cba_key]["band-0"][2] == Decimal("0.888")
    westpac_key = westpac_bundle.bundle_key + "/cr9-residential-mortgages"
    assert "rating-0" not in tables[westpac_key].columns
    assert reconstruct_source_tables(source)[westpac_key].frame["rating-0"][0] == "N/A"
    assert (
        source.qualifications.filter(
            (ma.col("table_id") == cba_key)
            & (ma.col("qualification_id") == "pd-horizon")
        ).item("source_text")
        == "Persisted research correction"
    )
    # Republish the surviving selection from retained inputs; all removed child rows clear.
    session = sessions[0]
    inputs = session.load_bronze(
        session.silver.read_manifest(publications[0]).selection.bronze_refs
    )
    candidate = session.conform(
        inputs,
        catalogue=CatalogueSelection(
            release_path="catalogue/releases/historical-mortgages-v1.json"
        ),
    )
    surviving = session.publish(candidate, revision="cba-again")
    publication = master.consolidate((surviving,), revision="source-cba-only")
    source = master.store.read(publication).source_tables
    for t in TABLES:
        assert all(
            row["table_id"].startswith(cba_2024_bundle.bundle_key + "/")
            for row in getattr(source, t.member).to_dicts()
        ), t.member
    assert source.cells.count_rows() == 131
    publication = master.consolidate((), revision="source-empty")
    assert all(
        getattr(master.store.read(publication).source_tables, t.member).count_rows()
        == 0
        for t in TABLES
    )
