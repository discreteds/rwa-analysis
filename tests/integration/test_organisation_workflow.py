"""The public session owns a real saved-Bronze → DuckDB → dataframe path."""

from decimal import Decimal


def test_default_storage_paths_follow_project_root(tmp_path):
    from rwa_analysis.settings import OrganisationSettings

    settings = OrganisationSettings(
        project_root=tmp_path,
        organisation_id="cba",
        staging_path="data/silver/staging/cba.duckdb",
    )
    assert settings.bronze_root == tmp_path / "data/bronze"
    assert settings.manifest_root == tmp_path / "data/manifests"
    assert settings.master_path == tmp_path / "data/silver/master.duckdb"
    assert settings.staging_path == tmp_path / "data/silver/staging/cba.duckdb"


def test_cba_run_and_independent_saved_rerun(project_root, tmp_path, monkeypatch):
    from rwa_analysis.composition import build_session
    from rwa_analysis.settings import OrganisationSettings
    from rwa_analysis.storage.manifests import CatalogueSelection
    from rwa_analysis.workflow import DocumentSelection

    settings = OrganisationSettings(
        config_files=[
            project_root / "config/project.yaml",
            project_root / "config/organisations/cba.yaml",
        ],
        project_root=project_root,
        bronze_root=tmp_path / "bronze",
        manifest_root=tmp_path / "manifests",
        staging_path=tmp_path / "cba.duckdb",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "")
    session = build_session(settings)
    result = session.run(
        documents=(
            DocumentSelection(
                extractor_path="extractions/au/cba/2025-06-30/aps330/extract.py",
                pdf_path="raw/cba-2025-06-30-aps330.pdf",
            ),
        ),
        catalogue=CatalogueSelection(release_path="catalogue/releases/cr6-cr9-v1.json"),
        run_name="review",
        revision="first",
    )
    key = "au/cba/2025-06-30/aps330/cr6-residential-mortgages"
    assert result.tables[key].height == 9
    assert result.tables[key].row(0)[4] == Decimal(281508)
    assert result.publication.database == tmp_path / "cba.duckdb"
    assert result.bundles[0].datasets[0].metadata.context.source_template == "CR6"
    output = session.silver.read(result.publication)
    stored = output.cr6
    assert output.cr9.observations.count_rows() == 8
    assert stored.contexts.count_rows() == 1
    assert stored.context_evidence.count_rows() == 2
    assert {r["source_pdf_page"] for r in stored.context_evidence.to_dicts()} == {1, 55}
    assert (
        stored.contexts.item("reporting_entity_value")
        == "CBA and its subsidiaries (the Group)"
    )

    # Another session needs no prior stage history and reads the saved selection.
    other = build_session(settings)
    manifest = other.silver.read_manifest(result.publication)
    inputs = other.load_bronze(manifest.selection.bronze_refs)
    candidate = other.conform(inputs, catalogue=manifest.selection.catalogue)
    publication = other.publish(candidate, revision="second")
    # The storage round-trip must retain every child row, including typed empties.
    import mountainash as ma

    from rwa_analysis.domains.cr6.contracts import TABLES

    reread = other.silver.read(publication).cr6
    for table in TABLES:
        expected = (
            getattr(candidate.cr6, table.member)
            .with_columns(ma.lit("second").alias("silver_revision_id"))
            .to_polars()
        )
        actual = getattr(reread, table.member).to_polars()
        keys = table.spec.primary_key
        assert actual.sort(keys).equals(expected.sort(keys)), table.member
    assert other.reconstruct(publication)[key].equals(result.tables[key])
    assert result.publication.manifest_path.is_file()
    assert publication.manifest_path.is_file()
