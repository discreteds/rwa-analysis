# RWA disclosure research

**Migration status: blocked, not ready for use.** The new CBA entrypoint is wired,
but native validation/schema defects and unresolved ingress/declaration questions
prevent the executable review checkpoint. The migration plan records the central
Mountainash backlog owners and clearance conditions.
The prior working implementation remains at `feature/simple-cr6` (`3be5e86`).

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

## Configuration and ownership

Load `config/project.yaml` followed by `config/organisations/cba.yaml` with
`OrganisationSettings(config_files=[...], project_root=...)`. Native Mountainash
Settings handles layering and explicit overrides. Paths resolve against the
configured project root, including when working in a notebook elsewhere.

- `composition.py` assembles components from resolved settings.
- `workflow.py` sequences stages and exposes `run()`.
- `domains/cr6/` owns typed models, native contracts, conformance and reconstruction.
- `storage/` owns source transport, retained selections and DuckDB publication.
- `catalogue/` retains semantic definitions and scoped interpretations.

Money is stored as `Decimal(16,2)`, small-valued rates and bands as
`Decimal(16,8)`, and counts as integers. Source precision remains in Bronze.

The current implementation checkpoint is CBA. Four-bank source extractors and
goldens remain supported; configured four-bank staging and master consolidation
follow the CBA review checkpoint.

## Verification

```bash
uv run pytest
uv run ruff check src tests examples extractions
```

Source goldens are independently authored from the disclosures. Domain tests
protect conversions and partial semantics; reconstruction tests compare actual
persisted numbers with the source tables. Runtime execution does not require Git.
