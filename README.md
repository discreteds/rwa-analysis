# RWA disclosure research

Python tools for source-traceable disclosure research. Four reviewed mortgage
CR6 extractors preserve published evidence in immutable Bronze bundles. A
versioned semantic catalogue conforms 36 observations into rebuildable DuckDB
Silver through Mountainash, preserving partial meanings and source lineage.

## Install and check

Requires Python 3.12+ and uv. Git access to the Mountainash repositories must be
configured outside this repository. Install from the committed lockfile:

```sh
uv sync --locked
uv run pytest -q
uv run ruff check src tests extractions
uv run ruff format --check src tests extractions
```

## Run

After running the [four extraction commands](docs/workflows/cr6-extraction.md):

```sh
uv run rwa manifest --request config/rebuilds/cr6-2025-v1.json
uv run rwa rebuild --manifest data/manifests/cr6-2025-v1.json
uv run rwa inspect --observation au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1
```

Commands accept `--project-root`; rebuild/inspect accept `--warehouse`.
Production publication requires committed producing code/configuration. Saved
versions are immutable. Silver uses `DECIMAL(22,8)` and integer counts, with
field-specific status, currency and weighting evidence. Rebuild needs retained
Bronze and catalogue, not PDFs or goldens.

Follow [retention and source-only recovery](docs/workflows/silver-rebuild.md)
before relying on ignored generated inputs. Supply an existing external durable
destination through `RWA_BACKUP_ROOT`; no backup location is assumed.

## Verified dependency boundary

Verified on Linux aarch64 with Python 3.13.15, uv 0.12.13, Polars **1.44.2**,
DuckDB **1.5.6**, Ibis **12.0.0** and PyArrow **26.0.0**. `uv.lock` records all
resolved dependencies. Ecosystem packages use immutable Git revisions:

| Repository under `https://github.com/mountainash-io/` | Verified revision |
|---|---|
| mountainash | `3c25bbffe0a3998ef56a9092e54898b3219ce9a2` |
| mountainash-data | `36f4f4a68bc17de51bfc22bbfbd9dd9191db2701` |
| mountainash-files | `13721c33fa5876ba8ee1e69917f3e9ce9f781fc2` |
| mountainash-settings | `e81750960b3fb078ae239696b848054568af6c72` |
| mountainash-auth-client | `1b57247f17deb68c1178635486c05a8bfc6fa83b` |
| mountainash-transport | `f79e3a3729f31c88f148f4c8443657ae68c652ce` |

The original Mountainash candidate `9f43cf818223c02793a6e5f516edaf2924f5339f`
was a local disposable spike commit unavailable remotely. The approved published
develop replacement above passed the required integration checks. Its declared
Polars requirement is `>=1.35.1,<2`, so the spike's Polars 2.0.0 pin was replaced
with verified 1.44.2. No local dependency checkouts or patches are required.

See [boundary workflow and API findings](docs/workflows/mountainash-boundary.md)
and the [CR6 implementation plan](docs/04.planning/superpowers/plans/2026-10-10-cr6-bronze-to-silver.md).
