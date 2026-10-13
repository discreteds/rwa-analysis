"""Repeated observations retain separate publication and mapping identities."""

from datetime import date
from decimal import Decimal

import mountainash as ma
import pytest

from rwa_analysis.composition import build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.manifests import CatalogueSelection


@pytest.mark.parametrize(
    "organisation,month_day,dataset,cell,normalised_member,expected",
    [
        (
            "cba",
            "06-30",
            "table9d-ii-2023-06-30",
            "average_ead/band-0",
            "normalised_amount",
            "335000",
        ),
        (
            "westpac",
            "09-30",
            "table9d-2023-09-30",
            "band-0/ead",
            "normalised_amount",
            "112350000000",
        ),
        (
            "nab",
            "09-30",
            "table5-1-j-ii-2023-09-30",
            "main/estimated_pd",
            "normalised_scalar",
            "0.0087",
        ),
        (
            "anz",
            "09-30",
            "table9d-2023-09-30",
            "average_ead/band-0",
            "normalised_amount",
            "290000",
        ),
    ],
)
def test_original_and_comparative_survive_joint_publication(
    project_root,
    tmp_path,
    organisation,
    month_day,
    dataset,
    cell,
    normalised_member,
    expected,
):
    # This boundary catches catalogue-scope collisions and accidental vintage
    # deduplication that per-PDF transcription goldens cannot exercise.
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
        documents=tuple(
            DocumentSelection(
                f"extractions/au/{organisation}/{year}-{month_day}/aps330/extract.py",
                f"raw/{organisation}-{year}-{month_day}-aps330.pdf",
            )
            for year in (2023, 2024)
        ),
        catalogue=CatalogueSelection(
            release_path="catalogue/releases/historical-mortgages-v2.json"
        ),
        run_name="joint-vintages",
        revision="joint-vintages",
    )
    source = session.silver.read(result.publication).source_tables
    keys = ["silver_revision_id", "table_id"]
    observations = (
        source.meanings.filter(ma.col("cell_id") == cell)
        .join(source.tables.filter(ma.col("dataset_id") == dataset), on=keys)
        .select("table_id", "document_date", normalised_member)
        .to_dicts()
    )
    assert {(r["document_date"], r[normalised_member]) for r in observations} == {
        (date.fromisoformat(f"2023-{month_day}"), Decimal(expected)),
        (date.fromisoformat(f"2024-{month_day}"), Decimal(expected)),
    }
    assert len(observations) == 2
    assert len({r["table_id"] for r in observations}) == 2
    mapping_sets = []
    for row in observations:
        mapping_sets.append(
            set(
                source.mapping_refs.filter(
                    ma.col("observation_id") == row["table_id"] + "/" + cell
                )
                .select("mapping_revision_ref")
                .to_polars()["mapping_revision_ref"]
            )
        )
    assert all(mapping_sets)
    assert mapping_sets[0].isdisjoint(mapping_sets[1])
    manifest = session.silver.read_manifest(result.publication)
    assert len(manifest.selection.bronze_refs) == 2
