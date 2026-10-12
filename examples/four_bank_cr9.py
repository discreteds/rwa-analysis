"""Capture all four PDFs and reconstruct mixed-domain master from saved stages.

Run: uv run python -i examples/four_bank_cr9.py
Inspect sessions, results, publications, master_publication, output and tables.
A fresh temporary output directory is printed and retained on each invocation.
"""

from pathlib import Path
from tempfile import mkdtemp

import polars as pl

from rwa_analysis.composition import build_consolidator, build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings, ProjectSettings
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
data_root = Path(mkdtemp(prefix="cr9-four-bank-", dir="/tmp/opencode"))
print(f"Retained output directory: {data_root}", flush=True)
sessions, results, publications = {}, {}, []
for org, date in (
    ("cba", "2025-06-30"),
    ("westpac", "2025-09-30"),
    ("nab", "2025-09-30"),
    ("anz", "2025-09-30"),
):
    session = build_session(
        OrganisationSettings(
            project_root=root,
            organisation_id=org,
            bronze_root=data_root / "bronze",
            manifest_root=data_root / "manifests",
            staging_path=data_root / "silver" / f"{org}.duckdb",
        )
    )
    result = session.run(
        documents=(
            DocumentSelection(
                f"extractions/au/{org}/{date}/aps330/extract.py",
                f"raw/{org}-{date}-aps330.pdf",
            ),
        ),
        catalogue=CatalogueSelection(release_path="catalogue/releases/cr6-cr9-v1.json"),
        run_name="four-bank-review",
        revision=f"{org}-four-bank-review",
    )
    sessions[org], results[org] = session, result
    publications.append(result.publication)

master = build_consolidator(
    ProjectSettings(
        project_root=root,
        bronze_root=data_root / "bronze",
        manifest_root=data_root / "manifests",
        master_path=data_root / "silver/master.duckdb",
    )
)
master_publication = master.consolidate(
    tuple(publications), revision="four-bank-review"
)
output = master.store.read(master_publication)
tables = master.reconstruct(master_publication)
readback = data_root / "readback"
readback.mkdir()
print(f"Master: {master_publication.database}")
print(
    f"CR6 rows: {output.cr6.observations.count_rows()}; CR9 rows: {output.cr9.observations.count_rows()}"
)
with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
    for name, table in tables.items():
        table.write_parquet(readback / f"{name.replace('/', '__')}.parquet")
        print(name)
        print(table)
