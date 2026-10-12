"""CBA PDF → saved Bronze → staging Silver → source-shaped dataframe.

Run: uv run python -i examples/cba_extraction.py
Inspect result, bundle, dataset.exposure_rows, or cba.
"""

from pathlib import Path

import polars as pl

from rwa_analysis.composition import build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.bronze import BronzeRef
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
settings = OrganisationSettings(
    config_files=[root / "config/project.yaml", root / "config/organisations/cba.yaml"],
    project_root=root,
)
session = build_session(settings)

# Choose another name for another extraction; saved Bronze is never overwritten.
run_name = "cba-normalised-review"
result = session.run(
    documents=(
        DocumentSelection(
            extractor_path="extractions/au/cba/2025-06-30/aps330/extract.py",
            pdf_path="raw/cba-2025-06-30-aps330.pdf",
        ),
    ),
    catalogue=CatalogueSelection(
        release_path="catalogue/releases/cr6-cr9-v1.json",
        evidence_refs=tuple(
            BronzeRef(f"au/{org}/2025-09-30/aps330", "v1")
            for org in ("westpac", "nab", "anz")
        ),
    ),
    run_name=run_name,
    revision=run_name,
)
bundle = result.bundles[0]
dataset = bundle.datasets[0]
cba = result.tables[f"{bundle.bundle_key}/{dataset.id}"]
with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
    print(cba)
print(f"Publication: {result.publication}")
