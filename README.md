# RWA disclosure research

The four-bank CR6 workflow publishes normalised organisation staging databases,
consolidates master and reconstructs all four source tables. The CBA example also
demonstrates PDF extraction through publication and reconstruction.

## CBA workflow

```bash
uv run python -i examples/cba_extraction.py
```

`OrganisationSession.run()` extracts the selected PDF, saves and reloads Bronze,
conforms with the selected catalogue, publishes staging Silver and returns
source-shaped numeric dataframes. Inspect `result.tables`, `result.publication`,
or `result.bundles` for the source metadata. In a dataset, rows are
`dataset.exposure_rows`; descriptors and context are under `dataset.metadata`.

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

The demonstrated selection contains 36 observations, 432 fields, 1,296 mapping
references and 32 source relationships. Each reconstructed table has nine rows.

## Configuration and ownership

Load `config/project.yaml` followed by `config/organisations/cba.yaml` with
`OrganisationSettings(config_files=[...], project_root=...)`. Native Mountainash
Settings handles layering and explicit overrides. Paths resolve against the
configured project root, including when working in a notebook elsewhere.

- `composition.py` assembles components from resolved settings.
- `workflow.py` sequences stages and exposes `run()`.
- `domains/cr6/` owns typed models, schema declarations, conformance and reconstruction.
- `storage/` owns source transport, retained selections and DuckDB publication.
- `catalogue/` retains semantic definitions and scoped interpretations.

Money is stored as `Decimal(16,2)`, small-valued rates and bands as
`Decimal(16,8)`, and counts as integers. Source precision remains in Bronze.

Silver stores shared contexts once, scalar observations and field metadata, and
related rows for ordered qualifications, mappings, assertions, alternatives and
supporting evidence. `domains/cr6/contracts.py` declares the complete table inventory.
Metadata projection uses Mountainash expressions. The temporary `asdict()`/full-inference
ingress boundary is tracked for removal in the [techdebt backlog](docs/04.planning/a.backlog/INDEX.md).
Validation is separate and remains undefined; it is not invoked by this workflow.

## Verification

```bash
uv run pytest
uv run ruff check src tests examples extractions
```

Source goldens are independently authored from the disclosures. Domain tests
protect conversions and partial semantics; reconstruction tests compare actual
persisted numbers with the source tables. Runtime execution does not require Git.
