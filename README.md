# RWA disclosure research

The four-bank CR6/CR9 workflow publishes normalised organisation staging databases,
consolidates master and reconstructs all eight source tables. The CBA example also
demonstrates PDF extraction through publication and reconstruction.

The historical workflow captures complete selected 2023 and 2024 mortgage panels as
source-defined tables, including their original structure and supplementary notes.
It also supports an explicitly selected Westpac 2025 structural comparison.

## Documentation

- [Documentation guide](docs/README.md)
- [Current architecture and implementation limits](docs/architecture.md)
- [Durable principles](docs/01.principles/README.md)
- [Mountainash-first coding practices](docs/01.principles/d.coding-practices/mountainash-first.md)

Implemented scope is the selected four-bank 2025 mortgage CR6/CR9 blocks and 2023/2024
mortgage exposure/backtesting panels. Other disclosure
domains, a reusable capital engine and Gold persistence are not yet implemented.

## Environment and retained inputs

Use Python 3.12+ and `uv sync --locked` for the pinned dependency environment.
Source PDFs, extractors, goldens, catalogue and configuration are tracked. Generated
Bronze, manifests and DuckDB files under `data/` are retained separately; a fresh
checkout/worktree does not automatically contain the saved `v1` inputs.

The PDF example below can produce a new CBA extraction. Saved-Bronze examples need
the selected retained bundles. Inspect example roots and run names before execution:
they write Bronze/publications, and each Silver publication replaces its target.

## CBA workflow

```bash
uv run python -i examples/cba_extraction.py
```

`OrganisationSession.run()` extracts the selected PDF, saves and reloads Bronze,
conforms with the selected catalogue, publishes staging Silver and returns
source-shaped numeric dataframes. Inspect `result.tables`, `result.publication`,
or `result.bundles` for the source metadata. New captures expose source-table
`dataset.cells` and `dataset.metadata`, plus bundle-level captured fragments and
definition snapshots. Explicit domain bindings project these cells into named
`output.cr6` and `output.cr9` relations. Retained legacy datasets still expose
`exposure_rows` (CR6) or `backtesting_rows` (CR9).

Change `run_name` for another saved extraction. It names a folder, not a schema
version. Existing Bronze runs (including `v1`) are retained unchanged.

## Rerun selected stages

```bash
uv run python -i examples/cr6_research.py
```

This example uses existing CBA `v1` Bronze without reading its PDF. Its ordinary
Python calls are:

```python
session = build_session(settings)
inputs = session.load_bronze(selected_refs)
candidate = session.conform(inputs, catalogue=selected_catalogue)
publication = session.publish(candidate, revision="review-1")
tables = session.reconstruct(publication)
```

Each method works independently of earlier session history. Publication fully
replaces the organisation's staging tables in a DuckDB transaction. Include all
desired saved inputs in the selection. A publication identifies the database and
its retained rebuild manifest; reconstruction reads persisted numbers and uses
saved Bronze for labels, order, missing-value tokens and source evidence.

## Four-bank staging and master

To capture both domains from all four tracked PDFs into a fresh retained temporary
directory, without needing existing generated Bronze:

```bash
uv run python -i examples/four_bank_cr9.py
```

The example prints its output directory and exposes `sessions`, `results`,
`publications`, `master_publication`, `output` and `tables` for interactive inspection.
It uses `catalogue/releases/cr6-cr9-v1.json`. The demonstrated master holds 36 CR6
rows and 33 CR9 rows (CBA/Westpac/NAB eight each; ANZ nine including its subtotal).
CR9 rates, counts, field timing, evidence and within-row subset relationships remain
source-specific. No annual rates are inferred from historical averages.

For the earlier retained CR6-only selections:

```bash
uv run python -i examples/four_bank_research.py
```

The example rebuilds CBA, Westpac, NAB and ANZ staging from retained `v1` Bronze,
then combines those publications into `data/silver/master.duckdb`:

```python
master = build_consolidator(project_settings)
publication = master.consolidate(tuple(publications), revision="combined-1")
output = master.store.read(publication)
tables = master.reconstruct(publication)
```

Each consolidation replaces all master tables atomically with the selected staging
rows. Producing revisions remain on those rows; the master manifest retains the
selected staging manifests. Reconstruction uses master numbers and retained Bronze
metadata, without depending on live staging databases. Publications refer to mutable
database locations; select the current staging publications when rebuilding master.
Old publication handles do not select historical snapshots or detect a stale revision.
The workflow assumes sequential staging writes followed by consolidation.

The demonstrated selection contains 36 observations, 432 fields, 1,296 mapping
references and 32 source relationships. Each reconstructed table has nine rows.

## 2025 adjustment evidence

```bash
uv run python -i examples/rwa_adjustments.py
```

The four existing 2025 bundles also capture **38 supplementary observations**:
identified RWA/capital adjustments and supporting overview rows. Source tokens,
scales, dates, classifications, portfolio scope, comments and applicability links
are retained in Bronze and the existing source-table Silver/master relations.
Original CR6/CR9 projections still contain 36/33 rows.

The example prints its retained directory and master DuckDB path. Its `research/`
directory contains `adjustment-observations.parquet` from persisted readback and
`nab-mortgage-rwa-bridge.json`: the separately classified $50m derived difference,
with input identities and revisions. No derived amount is inserted into Bronze.
ANZ's aggregate overlay inclusion has a retained researcher decision; no band
allocation is inferred. Westpac's October removal is dated separately from its
September capital overlay. See the [source review and decisions](docs/00.ideation/2026-10-17-rwa-adjustment-capture.md).

## Historical source tables

```bash
uv run python -i examples/historical_mortgages.py
```

This starts from the tracked PDFs and retains a fresh `/tmp/opencode` directory.
The 2023 and 2024 reports each contribute 23 dated datasets and 574 body positions;
their numerical notes contribute seven and eight observations respectively. The
modern Westpac capture adds its two mortgage datasets and 180 cells, plus five
supplementary adjustment observations, for **49 source datasets and 1,348 cells**
in master. The example selects
`catalogue/releases/historical-mortgages-v2.json`; the earlier v1 release is retained.

Original observations and later comparatives remain distinct source occurrences.
For example, June 2023 in CBA's 2023 report and June 2023 in its 2024 report both
survive. Do not sum these report vintages as additional exposure. The 2022 comparative
panels retain their earlier regulatory basis, scaling and floor notes; the workflow
does not choose a reporting vintage or impose cross-year semantic equivalence.

Inspect `sessions`, `publications`, `master_publication`, `output`, `source_tables`,
`field_inventory`, `field_paths`, `field_timing`, `field_bands` and `field_mappings`.
`output.source_tables` exposes persisted source values, axes, qualifications, timing
and composed meanings. Each `source_tables[key]` exposes `.frame` and `.metadata`.
Inventory presence includes unmapped and blank fields. Numerical notes are queryable
cells, excluded from body frames. Reports' changing bands and definitions are retained
without automatic equivalence, rebanding or imputation.

All twelve selected source entrypoints now produce `disclosure-v4`, retaining
physical bindings, captured fragments, contexts and occurrence identities. Original
`cr6-v1`, `disclosure-v2` and `disclosure-v3` files remain readable. Ordinary sessions
publish native source relations and declared CR6/CR9 projections. An explicit
`SourceTablePipeline().conform(inputs, catalogue)` also provides source views of
retained legacy typed datasets. Existing numeric frame keys retain their numeric
views; use `reconstruct_source_tables(output.source_tables)` for lexical projections.

Checkpoint A's ANZ September 2023 path retains all-kind context metadata.
Run `uv run python -i examples/anz_metadata_capture.py` for the full 125-cell path
and a saved-only comment reinterpretation after deleting disposable source copies.
It prints a fresh retained `/tmp/opencode` root. Checkpoint A was accepted on
2026-10-14, followed by checkpoint B acceptance of all twelve migrations and domain
projections. Task 7's master lifecycle proof covers retained and current captures:
shared comments and contexts survive staging deletion, and fewer/empty selections
replace every dependent relation. Final independent delivery reviews remain pending.

Source reconstruction uses persisted source relations. Existing CR6/CR9 reconstruction
still uses saved Bronze structure. Preserve all selected inputs and manifests as
described below. The locked Mountainash revision includes PR #377's declared-source
ingress repair, required for late lexical and missingness values.

## Configuration and ownership

Load `config/project.yaml` followed by `config/organisations/cba.yaml` with
`OrganisationSettings(config_files=[...], project_root=...)`. Native Mountainash
Settings handles layering and explicit overrides. Paths resolve against the
configured project root, including when working in a notebook elsewhere.

- `composition.py` assembles components from resolved settings.
- `workflow.py` sequences stages and exposes `run()`.
- `domains/source_tables/` resolves and conforms source content with the catalogue.
- `domains/cr6/` and `domains/cr9/` own typed models, declarations, catalogue-free projections and reconstruction.
- `storage/` owns source transport, retained selections and DuckDB publication.
- `catalogue/` retains semantic definitions and scoped interpretations.

Money is stored as `Decimal(16,2)`, small-valued rates and bands as
`Decimal(16,8)`, and counts as integers. Source precision remains in Bronze.

Silver stores shared contexts once, scalar observations and field metadata, and
related rows for ordered qualifications, mappings, assertions, alternatives and
supporting evidence. Domain `contracts.py` files declare twelve CR6 and fifteen CR9
tables, associated in `storage/tables.py`. CR9 adds field-level temporal descriptors,
bindings and evidence and uses flat typed metadata ingress.
Domain metadata projection uses Mountainash expressions over flat source relations.
Task 5 removed the earlier recursive `asdict()`/full-inference ingress boundary;
its history remains in the [techdebt backlog](docs/04.planning/a.backlog/INDEX.md).
Validation is separate and remains undefined; it is not invoked by this workflow.

Rebuild manifests retain input references, not copies of all referenced assets.
Implementation revision defaults to `unrecorded`; retaining reproducible research
also requires retaining its source inputs, catalogue files and code/environment.
See the [architecture guide](docs/architecture.md) for the exact publication boundary
and the distinction between undefined analytical validation and retained transport checks.

## Verification

```bash
uv run pytest
uv run ruff check src tests examples extractions
```

Source goldens are independently authored from the disclosures. Domain tests
protect conversions and partial semantics; reconstruction tests compare actual
persisted numbers with the source tables. Runtime execution does not require Git.
