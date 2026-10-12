"""Rebuild four organisation stages from retained Bronze, then consolidate master.

Run: uv run python -i examples/four_bank_research.py
Inspect publications, master_publication, output and tables.
"""

from pathlib import Path

import polars as pl

from rwa_analysis.composition import build_consolidator, build_session
from rwa_analysis.settings import OrganisationSettings, ProjectSettings
from rwa_analysis.storage.bronze import BronzeRef
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
refs = tuple(
    BronzeRef(f"au/{org}/{date}/aps330", "v1")
    for org, date in (
        ("cba", "2025-06-30"),
        ("westpac", "2025-09-30"),
        ("nab", "2025-09-30"),
        ("anz", "2025-09-30"),
    )
)
publications = []
for ref in refs:
    org = ref.bundle_key.split("/")[1]
    session = build_session(
        OrganisationSettings(
            config_files=[
                root / "config/project.yaml",
                root / f"config/organisations/{org}.yaml",
            ],
            project_root=root,
        )
    )
    candidate = session.conform(
        session.load_bronze((ref,)),
        catalogue=CatalogueSelection(
            release_path="catalogue/releases/cr6-v1.json",
            evidence_refs=tuple(other for other in refs if other != ref),
        ),
    )
    publications.append(session.publish(candidate, revision=f"{org}-four-bank-review"))

master = build_consolidator(
    ProjectSettings(
        config_files=[root / "config/project.yaml"],
        project_root=root,
    )
)
master_publication = master.consolidate(
    tuple(publications), revision="four-bank-review"
)
output = master.store.read(master_publication)
tables = master.reconstruct(master_publication)
print(f"Master: {master_publication.database}")
print(
    f"Observations: {output.cr6.observations.count_rows()}, fields: {output.cr6.fields.count_rows()}, "
    f"mappings: {output.cr6.field_mappings.count_rows()}, relationships: {output.cr6.relationships.count_rows()}"
)
with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
    for name, table in tables.items():
        print(name)
        print(table)
