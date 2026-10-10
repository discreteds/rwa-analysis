# Silver rebuild, inspection and recovery

First [extract the reviewed sources](cr6-extraction.md), then run:

```sh
uv run rwa manifest --request config/rebuilds/cr6-2025-v1.json
uv run rwa rebuild --manifest data/manifests/cr6-2025-v1.json
uv run rwa inspect --observation au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1
```

All commands accept `--project-root`; rebuild and inspect accept `--warehouse`.
Relative paths resolve under the project root. The default warehouse is
`data/warehouse.duckdb`. Inspection emits JSON with exact Decimal strings,
integer counts, field statuses, mappings, source occurrence references, original
evidence, context, segment and total relationships. Catalogue definitions and
supporting source metadata accompany the result so unresolved meanings remain
visible. Reads use Mountainash relations through the pinned DuckDB backend.

## Retained selection and publication

The strict [request](../../config/rebuilds/cr6-2025-v1.json) selects explicit
Bronze versions, catalogue release, schema and unique revision ID. Unknown
fields are errors. Commit request/catalogue changes before running `manifest`;
the CLI compares selected bytes and executing code with the committed revision.
Manifests are immutable. Use a new request/revision ID for changed selections,
including corrections or changed source scope. Exact manifest replay is
idempotent; an existing revision with different manifest content is rejected.

[Manifests](../../src/rwa_analysis/storage/manifests.py) retain the request,
full implementation commit, environment, catalogue inventory and input digests.
Supporting Bronze references are pinned separately as `evidence_bronze_refs`.
A release retains full catalogue provenance closure even when a bank is removed
from the published scope: these supporting bundles supply evidence, not extra
Silver rows. New manifests require one unambiguous retained version per
supporting bundle; multiple versions require an explicit selection enhancement
before publication. Rebuild uses the already-pinned references, never latest.

Rebuild and inspection need no PDFs, extractor scripts, goldens or network.
They require saved Bronze, catalogue files, the manifest, retained lock/project
configuration and matching installed code/environment. Source/config history is
needed for implementation verification. Restore missing files at the named
paths rather than editing Silver manually.

[Publication](../../src/rwa_analysis/storage/silver.py) validates the full
candidate and atomically replaces seven `silver` tables plus
`ops.silver_publication` in one DuckDB transaction. Amounts, fractions, years and
band bounds use `DECIMAL(22,8)`; counts use `BIGINT`. Out-of-range or inexact
representations fail before publication. Failed runs leave the prior successful
marker intact. Save stderr diagnostics separately, for example to a new
`data/diagnostics/<attempt-id>.log`; failure logs are not publication status.
Keep a single writer, and close readers before replacing the database.

## Back up retained inputs

The researcher must supply an **existing external durable directory** as
`RWA_BACKUP_ROOT`. An unset/unavailable destination means external backup is not
configured; a local recovery rehearsal does not establish durable retention.
Stop the writer before archiving, keep it stopped until both files are complete,
and ensure all code, extractors, PDFs/index, goldens, catalogue and config changes
referenced by the manifest are committed. Generated Bronze/manifests are ignored
by Git and require the input archive. The database is unnecessary for recovery.

Run this Bash block from the repository root. It reserves a fresh revision-labelled
directory so previous snapshots cannot be overwritten. Choose a new label if
any previous attempt exists, including a failed attempt.

```bash
set -eu
: "${RWA_BACKUP_ROOT:?Set an external durable backup directory}"
test -d "$RWA_BACKUP_ROOT"
test -z "$(git status --porcelain --untracked-files=all)"
snapshot="$RWA_BACKUP_ROOT/cr6-2025-v1"
mkdir "$snapshot"
git bundle create "$snapshot/rwa-code-cr6-2025-v1.bundle" --all
tar -czf "$snapshot/rwa-inputs-cr6-2025-v1.tar.gz" \
  raw data/bronze data/manifests data/reconciliation catalogue config uv.lock
git bundle verify "$snapshot/rwa-code-cr6-2025-v1.bundle"
tar -tzf "$snapshot/rwa-inputs-cr6-2025-v1.tar.gz"
tar -xOzf "$snapshot/rwa-inputs-cr6-2025-v1.tar.gz" \
  data/manifests/cr6-2025-v1.json
```

Both archive and Git bundle are required. Retain old snapshots. Listing and
reopening archives verifies readability; rehearse restoration before calling
recovery verified. The automated [CLI integration test](../../tests/integration/test_cr6_cli.py)
creates these two archive types, restores a different root, removes PDFs and
extractors, and compares observations, interpretations, lineage and relationships.

Include `data/reconciliation` after the final visual review (omit it only when
no review artifacts exist yet). Restored HTML and page images can be opened
directly; compare their bytes with the retained originals during recovery.

## Restore to a different root

Choose a new directory and empty warehouse path. For this example the snapshot
paths are those created above:

```bash
set -eu
: "${RWA_BACKUP_ROOT:?Set the retained backup directory}"
: "${RWA_RESTORE_ROOT:?Set a new restore directory}"
snapshot="$RWA_BACKUP_ROOT/cr6-2025-v1"
test ! -e "$RWA_RESTORE_ROOT"
git clone "$snapshot/rwa-code-cr6-2025-v1.bundle" "$RWA_RESTORE_ROOT"
revision=$(tar -xOzf "$snapshot/rwa-inputs-cr6-2025-v1.tar.gz" \
  data/manifests/cr6-2025-v1.json | python3 -c \
  'import json,sys; print(json.load(sys.stdin)["implementation_revision"])')
git -C "$RWA_RESTORE_ROOT" checkout --detach "$revision"
tar -xzf "$snapshot/rwa-inputs-cr6-2025-v1.tar.gz" -C "$RWA_RESTORE_ROOT"
cd "$RWA_RESTORE_ROOT"
uv sync --locked
test ! -e data/recovered.duckdb
uv run rwa rebuild --manifest data/manifests/cr6-2025-v1.json \
  --warehouse data/recovered.duckdb
uv run rwa inspect --warehouse data/recovered.duckdb \
  --observation au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1
```

Use the recorded Python/environment versions as well as the lockfile; environment
mismatches fail with a restoration instruction. Private Mountainash dependencies
require Git credentials configured externally (for example an OS credential
helper or authenticated GitHub CLI). Never put tokens in Git URLs, config files,
archives or this repository. Dependency installation may require network access
or a populated uv cache; subsequent rebuild/inspection are offline.
