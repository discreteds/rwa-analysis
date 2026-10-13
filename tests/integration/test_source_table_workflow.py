"""Persisted source-table fidelity at the actual session/storage boundary."""

from dataclasses import replace
from decimal import Decimal

import mountainash as ma
import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.composition import build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection


def test_explicit_legacy_publication_keeps_numeric_and_lexical_views(
    project_root, tmp_path, westpac_bundle
):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
    from rwa_analysis.domains.source_tables.reconstruction import (
        reconstruct_source_tables,
    )

    session = build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id="westpac",
            bronze_root=tmp_path / "bronze",
            staging_path=tmp_path / "westpac.duckdb",
            manifest_root=tmp_path / "manifests",
        )
    )
    refs = session.save_bronze((westpac_bundle,), "legacy-view")
    inputs = session.load_bronze(refs)
    selection = CatalogueSelection(release_path="catalogue/releases/cr6-cr9-v1.json")
    candidate = session.conform(inputs, catalogue=selection)
    assert candidate.source_tables.cells.count_rows() == 0
    catalogue = load_catalogue(project_root / selection.release_path)
    candidate = replace(
        candidate, source_tables=SourceTablePipeline().conform(inputs, catalogue)
    )
    assert candidate.source_tables.cells.count_rows() == 180
    publication = session.publish(candidate, revision="explicit")
    assert session.silver.read_manifest(publication).selection.bronze_refs == refs
    source = session.silver.read(publication).source_tables
    assert source.cells.filter(ma.col("original_text") == "N/A").count_rows() == 14
    assert source.cells.filter(ma.col("value_kind") == "text").count_rows() == 16
    assert source.cells.filter(ma.col("source_count") == 564613).count_rows() >= 1
    key = westpac_bundle.bundle_key + "/cr9-residential-mortgages"
    assert source.cells.filter(
        (ma.col("table_id") == key) & (ma.col("original_text") == "")
    ).count_rows() == 5
    frames = reconstruct_source_tables(source)
    assert frames[key].frame["rating-0"].to_list()[:7] == ["N/A"] * 7
    assert frames[key].frame["column-previous_year_borrower_count"][0] == 564613
    assert frames[key].frame.columns.index("rating-1") < frames[
        key
    ].frame.columns.index("column-weighted_average_pd")
    # Public numeric CR9 output retains its original frame despite the same source key.
    numeric = session.reconstruct(publication)[key]
    assert "rating-0" not in numeric.columns
    assert numeric.height == 8


def test_cba_saved_source_tables_reconstruct_persisted_values(project_root, tmp_path):
    from rwa_analysis.domains.source_tables.reconstruction import (
        reconstruct_source_tables,
    )

    session = build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id="cba",
            bronze_root=tmp_path / "bronze",
            staging_path=tmp_path / "cba.duckdb",
            manifest_root=tmp_path / "manifests",
        )
    )
    result = session.run(
        documents=(
            DocumentSelection(
                "extractions/au/cba/2024-06-30/aps330/extract.py",
                "raw/cba-2024-06-30-aps330.pdf",
            ),
        ),
        catalogue=CatalogueSelection(
            release_path="catalogue/releases/historical-mortgages-v1.json"
        ),
        run_name="cba-proof",
        revision="first",
    )
    output = session.silver.read(result.publication)
    source = output.source_tables
    assert output.cr6.observations.count_rows() == 0
    assert output.cr9.observations.count_rows() == 0
    assert source.cells.count_rows() == 131
    table = "au/cba/2024-06-30/aps330/table9d-ii-2024-06-30"
    selected = (ma.col("table_id") == table) & (ma.col("field_id") == "average_ead")
    assert source.cells.filter(selected & (ma.col("column_ref") == "band-0")).item(
        "source_number"
    ) == Decimal("0.359")
    m = source.meanings.filter(
        selected & (ma.col("cell_id") == "average_ead/band-0")
    ).to_dicts()[0]
    assert m["normalised_amount"] == Decimal(359000)
    assert m["measure_revision_ref"] is None
    assert source.fields.filter(ma.col("field_id") == "average_pd").count_rows() == 0
    assert source.meanings.filter(ma.col("field_id") == "overlay").item(
        "normalised_amount", row=0
    ) == Decimal(7400000000)
    assert (
        source.temporal_descriptors.filter(
            ma.col("descriptor_id") == "ead-history"
        ).item("start")
        is None
    )
    assert (
        source.temporal_descriptors.filter(
            ma.col("descriptor_id") == "ead-history"
        ).item("start_status")
        == "unresolved"
    )
    assert (
        source.qualifications.filter(
            ma.col("qualification_id") == "pd-restatement"
        ).count_rows()
        == 1
    )
    assert (
        source.references.filter(
            (ma.col("owner_kind") == "axis")
            & (ma.col("owner_id") == "band-0")
            & (ma.col("member") == "header_path_refs")
        ).count_rows()
        == 6
    )
    assert source.relationships.filter(ma.col("kind") == "subset").count_rows() == 24
    assert (
        source.source_attributes.filter(
            (ma.col("name") == "restatement_applicability")
            & (ma.col("status") == "unresolved")
        ).count_rows()
        == 2
    )
    reconstructed = reconstruct_source_tables(source)
    assert len(reconstructed) == 5
    assert reconstructed[table].frame.height == 5
    assert reconstructed[table].frame["band-0"][2] == Decimal("0.359")
    assert reconstructed[table].metadata.fields.count_rows() == 7
    assert len(result.tables) == 5

    # Mutate an actual persisted value; reconstruction cannot consult its original.
    changed = source.cells.with_columns(
        ma.when(
            (ma.col("table_id") == table) & (ma.col("cell_id") == "average_ead/band-0")
        )
        .then(ma.lit(Decimal("0.777")).cast(pl.Decimal(16, 8)))
        .otherwise(ma.col("source_number"))
        .alias("source_number")
    )
    with IbisBackend(dialect="duckdb", database=str(result.publication.database)) as db:
        db.create_table(
            "source_cells", changed.to_pyarrow(), namespace="silver", overwrite=True
        )
    reread = session.silver.read(result.publication).source_tables
    assert reconstruct_source_tables(reread)[table].frame["band-0"][2] == Decimal(
        "0.777"
    )

    # Selected v3 can be rebuilt independently without reparsing the PDF.
    manifest = session.silver.read_manifest(result.publication)
    fresh = build_session(
        session_settings := OrganisationSettings(
            project_root=project_root,
            organisation_id="cba",
            bronze_root=tmp_path / "bronze",
            staging_path=tmp_path / "rerun.duckdb",
            manifest_root=tmp_path / "rerun-manifests",
        )
    )
    inputs = fresh.load_bronze(manifest.selection.bronze_refs)
    candidate = fresh.conform(inputs, catalogue=manifest.selection.catalogue)
    again = fresh.publish(candidate, revision="rerun")
    assert again.database == session_settings.staging_path
    assert fresh.reconstruct(again)[table]["band-0"][2] == Decimal("0.359")

    from rwa_analysis.composition import build_consolidator
    from rwa_analysis.settings import ProjectSettings

    master = build_consolidator(
        ProjectSettings(
            project_root=project_root,
            master_path=tmp_path / "master.duckdb",
            manifest_root=tmp_path / "master-manifests",
        )
    )
    consolidated = master.consolidate((again,), revision="native-source")
    again.database.unlink()
    assert master.reconstruct(consolidated)[table]["band-0"][2] == Decimal("0.359")
