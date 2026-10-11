"""Extract CBA June 2025 from PDF and save a named Bronze run.

Run: uv run python -i examples/cba_extraction.py
Then inspect `bundle`, `dataset.records`, or the saved reference `ref`.
"""

from pathlib import Path

from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.storage.bronze import save_bronze

root = Path(__file__).resolve().parents[1]

# A folder namespace, not a code/schema version. Change this for another saved run.
run_name = "cba-june-extract"

bundle = run_extractor(
    root / "extractions/au/cba/2025-06-30/aps330/extract.py",
    root / "raw/cba-2025-06-30-aps330.pdf",
)
dataset = bundle.datasets[0]
ref = save_bronze(bundle, run_name=run_name, project_root=root)

print(f"Extracted {len(dataset.records)} rows from {dataset.id}")
print(f"Saved: {root / 'data/bronze' / ref.bundle_key / run_name / 'bundle.json'}")
