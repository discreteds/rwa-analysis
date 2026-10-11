# RWA disclosure research

## Extract CBA from its PDF

Run the example script:

```bash
uv run python -i examples/cba_extraction.py
```

It extracts the PDF and saves Bronze under `run_name = "cba-june-extract"`.
Edit that name in the script for another saved run. In the interactive session,
inspect `bundle`, `dataset.records`, or `ref`. Existing runs are not overwritten.

### Call the functions yourself

From the project root, start Python:

```bash
uv run python -i
```

Then run:

```python
from pathlib import Path
from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.storage.bronze import save_bronze

root = Path.cwd()
bundle = run_extractor(
    root / "extractions/au/cba/2025-06-30/aps330/extract.py",
    root / "raw/cba-2025-06-30-aps330.pdf",
)

# Inspect the extracted records before deciding whether to save.
bundle.datasets[0].records

ref = save_bronze(bundle, run_name="cba-june-rerun", project_root=root)
```

**`run_name` is a namespace for a saved extraction**—a folder name you choose,
not a code or schema version. This example saves to:

```text
data/bronze/au/cba/2025-06-30/aps330/cba-june-rerun/bundle.json
```

Choose a new name for another saved run; existing runs are not overwritten.
Earlier runs named `v1` or `v2` follow the same convention. The saved metadata
and `BronzeRef` currently call this name `output_version`.

## Rebuild Silver from the existing CBA extraction

```bash
uv run python -i examples/cr6_research.py
```

This selects the saved run named `v1`, rebuilds Silver, and exposes the
reconstructed dataframe as `cba`. It does not rerun PDF extraction.
