"""Persisted source-table fidelity at the actual session/storage boundary."""

from dataclasses import replace
from decimal import Decimal

import mountainash as ma
import polars as pl
import pytest
from mountainash_data import IbisBackend

from rwa_analysis.composition import build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection


def test_anz_capture_saved_only_noncell_refinement(project_root, tmp_path):
    """Catch dropped shared metadata and catalogue overrides at DuckDB readback."""
    import json
    import shutil

    from rwa_analysis.domains.source_tables.reconstruction import (
        reconstruct_source_tables,
    )

    authoring = tmp_path / "authoring"
    shutil.copytree(project_root / "extractions/au/anz/2023-09-30/aps330", authoring)
    pdf = tmp_path / "source.pdf"
    shutil.copyfile(project_root / "raw/anz-2023-09-30-aps330.pdf", pdf)
    session = build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id="anz",
            bronze_root=tmp_path / "bronze",
            staging_path=tmp_path / "anz.duckdb",
            manifest_root=tmp_path / "manifests",
        )
    )
    bundles = session.extract(
        (DocumentSelection(str(authoring / "extract.py"), str(pdf)),)
    )
    assert bundles[0].schema_version == "disclosure-v4"
    refs = session.save_bronze(bundles, "metadata-proof")
    inputs = session.load_bronze(refs)
    selection = CatalogueSelection(
        release_path="catalogue/releases/historical-mortgages-v2.json"
    )
    pub = session.publish(
        session.conform(inputs, catalogue=selection), revision="original"
    )
    source = session.silver.read(pub).source_tables
    assert source.cells.count_rows() == 125
    assert source.cells.filter(ma.col("cell_id") == "mortgage/ead_ratio").item(
        "source_number"
    ) == Decimal("1.01")
    comments = source.occurrences.filter(ma.col("kind") == "comment")
    assert comments.filter(ma.col("local_id") == "report-entity").count_rows() == 1
    assert (
        source.occurrence_links.filter(
            (ma.col("owner_id") == "report-entity") & (ma.col("role") == "qualifies")
        ).count_rows()
        == 4
    )
    assert (
        source.contexts.filter(
            ma.col("context_revision_id") == "anz-2023/common@1"
        ).count_rows()
        == 1
    )
    assert (
        source.occurrences.filter(ma.col("local_id") == "matrix/nz/pre").item(
            "source_text"
        )
        == ""
    )
    assert (
        source.occurrences.filter(ma.col("local_id") == "matrix/header/pre").item(
            "source_text"
        )
        == "Rating Approach Pre-Jan 2023"
    )
    assert (
        source.occurrences.filter(ma.col("local_id") == "matrix/header/post").item(
            "source_text"
        )
        == "Rating Approach Post-Jan 2023"
    )
    table = "au/anz/2023-09-30/aps330/table9f-2023-09-30"
    reconstructed = reconstruct_source_tables(source)[table]
    assert (
        reconstructed.metadata.occurrences.filter(
            ma.col("local_id") == "report-entity"
        ).count_rows()
        == 1
    )
    exposure_metadata = reconstruct_source_tables(source)[
        "au/anz/2023-09-30/aps330/table9d-2023-09-30"
    ].metadata
    assert (
        exposure_metadata.occurrences.filter(
            ma.col("local_id") == "lgd-review"
        ).count_rows()
        == 0
    )
    assert (
        source.context_bindings.filter(ma.col("role") == "history_window").count_rows()
        == 5
    )

    # A real retained release, loaded through ordinary catalogue/session APIs.
    root = tmp_path / "catalogue"
    shutil.copytree(project_root / "catalogue", root)
    release_path = root / "releases/historical-mortgages-v2.json"
    release = json.loads(release_path.read_text())
    target = {
        "bundle_key": "au/anz/2023-09-30/aps330",
        "scope": None,
        "kind": "comment",
        "local_id": "lgd-review",
    }
    common = {
        "created_on": "2026-10-13",
        "effective_from": None,
        "effective_to": None,
        "scope": {"targets": [target]},
    }
    mappings = [
        {
            **common,
            "id": "review-interpretation",
            "revision_id": "review@1",
            "attributes": [
                {
                    "name": "qualification_meaning",
                    "value": "whole report",
                    "status": "provisional",
                }
            ],
        },
        {
            **common,
            "id": "review-refinement",
            "revision_id": "review@2",
            "attributes": [
                {
                    "name": "qualification_meaning",
                    "value": "wholesale applicability; mortgage unresolved",
                    "status": "established",
                }
            ],
            "overrides_refs": [{"kind": "mapping", "revision_id": "review@1"}],
            "evidence_refs": [
                {
                    "bundle_key": target["bundle_key"],
                    "document_id": "anz-2023-09-30-aps330",
                    "dataset_id": "",
                    "kind": "comment",
                    "ref_id": "lgd-review",
                }
            ],
        },
    ]
    (root / "refinement.json").write_text(
        json.dumps({"schema_version": "cr6-v1", "members": mappings})
    )
    release["id"] = "anz-refinement"
    release["selection"].extend(
        {"path": "refinement.json", "kind": "mapping", "revision_id": m["revision_id"]}
        for m in mappings
    )
    release_path.write_text(json.dumps(release))
    shutil.rmtree(authoring)
    pdf.unlink()
    saved = session.load_bronze(refs)
    again = session.publish(
        session.conform(
            saved, catalogue=CatalogueSelection(release_path=str(release_path))
        ),
        revision="refined",
    )
    revised = session.silver.read(again).source_tables
    assert (
        revised.cells.select("table_id", "cell_id", "source_number").to_dicts()
        == source.cells.select("table_id", "cell_id", "source_number").to_dicts()
    )
    attrs = revised.attributes.filter(
        (ma.col("owner_kind") == "comment")
        & (ma.col("owner_id") == "lgd-review")
        & (ma.col("name") == "qualification_meaning")
    )
    assert attrs.item("value_text") == "wholesale applicability; mortgage unresolved"
    assert (
        revised.mapping_refs.filter(
            (ma.col("owner_id") == "lgd-review")
            & (ma.col("mapping_revision_ref") == "review@2")
        ).count_rows()
        == 1
    )
    assert (
        revised.attribute_evidence.filter(ma.col("owner_id") == "lgd-review").item(
            "kind"
        )
        == "comment"
    )


@pytest.mark.parametrize("organisation", ("nab", "anz"))
def test_historical_population_and_field_time_survive_saved_publication(
    project_root, tmp_path, organisation
):
    """Catch metadata collapse during transport/projection, beyond PDF goldens."""
    session = build_session(
        OrganisationSettings(
            project_root=project_root,
            organisation_id=organisation,
            bronze_root=tmp_path / "bronze",
            staging_path=tmp_path / "staging.duckdb",
            manifest_root=tmp_path / "manifests",
        )
    )
    result = session.run(
        documents=(
            DocumentSelection(
                f"extractions/au/{organisation}/2024-09-30/aps330/extract.py",
                f"raw/{organisation}-2024-09-30-aps330.pdf",
            ),
        ),
        catalogue=CatalogueSelection(
            release_path="catalogue/releases/historical-mortgages-v1.json"
        ),
        run_name="semantic-readback",
        revision="semantic-readback",
    )
    source = session.silver.read(result.publication).source_tables
    if organisation == "nab":
        table = "au/nab/2024-09-30/aps330/table5-1-j-iii-2024-09-30"
        cells = source.cells.filter(ma.col("table_id") == table)
        assert set(cells.select("row_ref").to_polars()["row_ref"]) == {"main", "rbnz"}
        scopes = (
            source.references.filter(
                (ma.col("table_id") == table)
                & (ma.col("owner_kind") == "qualification")
                & ma.col("owner_id").is_in(["apra-floor", "rbnz-lgd"])
                & (ma.col("member") == "scope")
            )
            .select("owner_id", "target_kind", "target_id")
            .to_dicts()
        )
        assert sorted(
            (r["owner_id"], r["target_kind"], r["target_id"]) for r in scopes
        ) == [
            ("apra-floor", "cell", "main/estimated_lgd"),
            ("rbnz-lgd", "cell", "rbnz/estimated_lgd"),
        ]
        paths = (
            source.references.filter(
                (ma.col("table_id") == table)
                & (ma.col("owner_kind") == "axis")
                & ma.col("owner_id").is_in(["main", "rbnz"])
                & (ma.col("member") == "header_path_refs")
            )
            .sort("owner_id", "position")
            .select("owner_id", "target_id")
            .to_dicts()
        )
        assert [(r["owner_id"], r["target_id"]) for r in paths] == [
            ("main", "panel"),
            ("main", "main-block"),
            ("rbnz", "panel"),
            ("rbnz", "rbnz-block"),
        ]
    else:
        table = "au/anz/2024-09-30/aps330/table9f-2024-09-30"
        timing = (
            source.temporal_bindings.filter(ma.col("table_id") == table)
            .join(
                source.temporal_descriptors.rename({"descriptor_id": "descriptor_ref"}),
                on=["silver_revision_id", "table_id", "descriptor_ref"],
            )
            .select("cell_id", "role", "start", "end")
            .to_dicts()
        )
        assert {(r["cell_id"], r["role"], r["start"], r["end"]) for r in timing} == {
            ("mortgage/estimated_pd", "history_window", "2019", "2023"),
            ("mortgage/actual_pd", "history_window", "2019", "2023"),
            ("mortgage/ead_ratio", "history_window", "2019", "2023"),
            ("mortgage/estimated_lgd", "history_window", "2018", "2022"),
            ("mortgage/actual_lgd", "history_window", "2018", "2022"),
            ("mortgage/actual_pd", "outcome_window", None, "2023-09"),
            ("mortgage/estimated_lgd", "outcome_window", None, "2023-09"),
            ("mortgage/actual_lgd", "outcome_window", None, "2023-09"),
        }


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
    assert (
        source.cells.filter(
            (ma.col("table_id") == key) & (ma.col("original_text") == "")
        ).count_rows()
        == 5
    )
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
