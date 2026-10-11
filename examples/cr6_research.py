"""CBA checkpoint: saved Bronze → compact Silver → source-shaped dataframe.

Run from the checkout with: uv run python examples/cr6_research.py
The returned `tables` dictionary is also available when run in a notebook.
"""

from pathlib import Path

import polars as pl

from rwa_analysis.reporting.cr6_tables import reconstruct_cr6
from rwa_analysis.storage.bronze import BronzeRef
from rwa_analysis.storage.manifests import RebuildRequest, save_manifest
from rwa_analysis.storage.silver import rebuild

root = Path(__file__).resolve().parents[1]
revision = "simple-cba-v2"
manifest = root / f"data/manifests/{revision}.json"
warehouse = root / f"data/warehouse-{revision}.duckdb"
if not manifest.exists():
    manifest = save_manifest(
        RebuildRequest(
            revision_id=revision,
            bronze_refs=(BronzeRef("au/cba/2025-06-30/aps330", "v1"),),
            catalogue_release_path="catalogue/releases/cr6-v1.json",
            conformance_schema_version="cr6-simple-v1",
        ),
        root,
    )
rebuild(manifest, root, warehouse)
tables = reconstruct_cr6(manifest, root, warehouse)
cba = tables["au/cba/2025-06-30/aps330/cr6-residential-mortgages"]
with pl.Config(trim_decimal_zeros=True, tbl_cols=13, tbl_width_chars=200):
    print(cba)
