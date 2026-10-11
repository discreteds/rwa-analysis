"""CBA checkpoint: independently rerun from retained Bronze, without PDFs.

Run: uv run python -i examples/cr6_research.py
"""

from pathlib import Path

import polars as pl

from rwa_analysis.composition import build_session
from rwa_analysis.settings import OrganisationSettings
from rwa_analysis.storage.bronze import BronzeRef
from rwa_analysis.storage.manifests import CatalogueSelection

root = Path(__file__).resolve().parents[1]
settings = OrganisationSettings(
    config_files=[root / "config/project.yaml", root / "config/organisations/cba.yaml"],
    project_root=root,
)
session = build_session(settings)
inputs = session.load_bronze((BronzeRef("au/cba/2025-06-30/aps330", "v1"),))
candidate = session.conform(
    inputs,
    catalogue=CatalogueSelection(
        release_path="catalogue/releases/cr6-v1.json",
        evidence_refs=tuple(
            BronzeRef(f"au/{org}/2025-09-30/aps330", "v1")
            for org in ("westpac", "nab", "anz")
        ),
    ),
)
publication = session.publish(candidate, revision="cba-retained-review")
tables = session.reconstruct(publication)
cba = tables["au/cba/2025-06-30/aps330/cr6-residential-mortgages"]
with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
    print(cba)
print(f"Publication: {publication}")
