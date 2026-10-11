# Simplify the existing four-bank CR6 implementation

> **For agentic workers:** Use `executing-plans` with a researcher checkpoint after task 3. Adapt the existing implementation and tests. Do not restart extraction, metadata discovery or golden authoring.

**Status:** Approved; executing locally on `feature/simple-cr6`. Researcher clarification during execution: trust framework arithmetic and casts; no application-level precision guards or duplicate numeric validation.

**Goal:** Retain the four-bank research assets and simplify their conformance/publication/reconciliation into dataset-wide Mountainash and three-table Silver.

**Architecture:** Existing extractors, source contracts, retained Bronze and catalogue feed the replacement Mountainash pipeline. Call the working publication functions directly from Python and reconstruct the source tables as dataframes.

**Tech Stack:** Existing Python 3.12/Mountainash/mountainash-data/mountainash-files/pdfplumber environment, retaining the existing dependency pins; Polars dataframes, pytest and Ruff.

**Spec:** [Simple CR6 research design](../specs/2026-10-10-simple-cr6-research-design.md).
**Reuse inventory:** [Existing assets and exact reuse decisions](../../../00.ideation/2026-10-11-cr6-existing-assets-and-reuse.md). Read it before implementation: it identifies both the code and the retained research inputs.

## Global constraints

- Work in `/home/ubuntu/git/discreteds/rwa-analysis`. Confirm the implementation seed branch before starting; use this checkout, not another worktree. Planning edits are currently on `docs/simple-cr6-spec`.
- Reuse baseline `0fc5221` selectively. PR #1 remains a reference demonstration, not a merge candidate.
- Existing goldens, source metadata, catalogue files and Bronze v1 envelopes are inputs, not deliverables to recreate. Preserve their IDs, format, provenance and paths.
- Mountainash owns tabular conversion, joins, projections, validation, analytical queries and reconciliation. Use `ma.relation(db.table(...))` for stored data. Direct SQL remains only for deliberate test corruption/DDL obstruction.
- Keep `Decimal(22,8)`, integral counts and the 10-trillion domain. Retain partial semantics and source missingness.
- Retain existing data-layer module paths. Orchestrate with direct Python calls; no CLI, HTML rendering, page-image generation or browser review. Reconstruction returns typed source-shaped dataframes.

## Review focus

| Risk | Existing owner to retain/adapt |
|---|---|
| Losing independently reviewed values or metadata | Four full golden comparisons and Bronze round-trip checks |
| Losing field meaning while collapsing tables | Catalogue semantic-isolation and conformance tests |
| Rebuild fails to repair edited/deleted Silver | Same-manifest replay regression |
| Publication leaves mixed revisions | Real view-obstruction rollback test |
| Reconstructed tables hide changed Silver values | Adapt existing whole-unit, sub-display and absent-row scenarios to dataframe assertions |

## Task 1 — Restore the source/research foundation unchanged

**Files:** The restore list below. The 17 PDFs and preserved `data/` files are already present. Do not overwrite or regenerate them.

**Interfaces retained:** `run_extractor(script_path, pdf_path)`, bespoke `extract(pdf_path)`, `encode_payload`/`decode_payload`, `BronzeRef`, `save_bronze`/`load_bronze`. Source dataclasses and the existing envelope format remain unchanged.

- [ ] After branch confirmation, restore the exact reusable files. First check for uncommitted edits at these paths; stop on conflicts rather than overwriting them. Then run:

```bash
git restore --source=0fc5221 --worktree -- pyproject.toml uv.lock raw/index.md extractions catalogue docs/00.ideation/2026-10-10-cr6-visual-reconciliation.md src/rwa_analysis/__init__.py src/rwa_analysis/extraction src/rwa_analysis/storage/__init__.py src/rwa_analysis/storage/bronze.py src/rwa_analysis/contracts tests/__init__.py tests/conftest.py tests/support tests/bronze tests/test_extraction_contract.py tests/test_golden_comparison.py tests/integration/test_bronze_storage.py tests/integration/test_mountainash_boundary.py
```

This restores all four actual extractors, their reviews, complete goldens and metadata; the existing source codec, runner and token parsers; original catalogue files; and proven storage/contract boundaries. Do not consolidate or rewrite these modules just to fit a new file map.

- [ ] Remove `[project.scripts]`'s `rwa` entry and the direct `typer` dependency from the restored `pyproject.toml`. Keep the data dependency pins and refresh the lock:

```bash
uv lock
uv sync --frozen
```

- [ ] Run the existing source and transport checks:

```bash
uv run pytest tests/bronze tests/test_extraction_contract.py tests/test_golden_comparison.py tests/integration/test_bronze_storage.py tests/integration/test_mountainash_boundary.py -q
```

Expected: the existing four-bank source comparisons pass without modifying expectations. These are baseline checks, not tests that should be forced red. A failure is investigated against the preserved baseline/environment.

- [ ] Verify the actual migrated Bronze through the retained loader, not a newly generated bundle:

```python
import json
from pathlib import Path
from rwa_analysis.extraction.codec import encode_payload
from rwa_analysis.storage.bronze import BronzeRef, load_bronze

root = Path.cwd()
for bank, date in (("cba", "2025-06-30"), ("westpac", "2025-09-30"),
                   ("nab", "2025-09-30"), ("anz", "2025-09-30")):
    key = f"au/{bank}/{date}/aps330"
    bundle = load_bronze(BronzeRef(key, "v1"), root)
    expected = json.loads((root / f"tests/bronze/{key}/golden.json").read_text())
    assert encode_payload(bundle) == expected
```

Expected: all four existing v1 envelopes load and match. Their original producer revision remains unchanged. Do not run extraction into an already existing `v1` destination.

- [ ] Stage only restored tracked assets and commit `chore: reuse reviewed CR6 source assets and Bronze contracts`.

## Task 2 — Replace per-row conformance with dataset-wide Mountainash

**Files:** Restore then edit `src/rwa_analysis/normalization/{cr6,models,validate}.py`; restore `src/rwa_analysis/catalogue/` and adapt `resolve.py` only where needed for tabular execution. Restore/adapt `tests/silver/test_cr6_conformance.py` and `tests/catalogue/test_cr6_catalogue.py`.

**Interfaces retained:** `conform_cr6(bundles, bronze_refs, catalogue, revision_id, *, evidence_bundles=()) -> SilverCandidate`; catalogue loading continues from `catalogue/releases/cr6-v1.json`. Keep source IDs and the twelve numeric Silver field names. `SilverCandidate.tables` changes to `cr6_observations`, `cr6_fields`, `cr6_relationships`.

- [ ] Restore the working starting code and tests:

```bash
git restore --source=0fc5221 --worktree -- src/rwa_analysis/catalogue src/rwa_analysis/normalization tests/catalogue tests/silver
```

- [ ] Edit the existing source-backed conformance test first to expect the three-table projection. Keep its independent numeric literals, missingness set, source conventions and partial-semantics assertions. Run it red on the old seven-table result:

```bash
uv run pytest tests/silver/test_cr6_conformance.py::test_source_values_and_partial_semantics_survive -q
```

Use Mountainash for the adapted assertions, for example inside that test after constructing its existing candidate:

```python
import mountainash as ma
from decimal import Decimal

observations = ma.relation(candidate.tables["cr6_observations"])
fields = ma.relation(candidate.tables["cr6_fields"])
assert observations.count_rows() == 36
assert fields.count_rows() == 432
assert observations.filter(
    ma.col("observation_id") == observation("cba")
).select("ead_amount", "mean_pd_fraction", "reported_entity_count").to_tuples() == [
    (Decimal("281508000000"), Decimal("0.0008"), 742470)
]
```

`observation()` is the existing helper in that test file; do not create another identity implementation.

- [ ] Read the preserved `data/reference/rwa-layered-spike/spike.py`, especially its whole-dataset source preparation and expression projection. Replace `_convert_row` in `normalization/cr6.py` with that execution shape. Prepare typed source rows once per dataset; create expressions once per column; join mapping/population/band tables through Mountainash. Remove the parallel Python `exact_conversion` computation rather than retaining it as a second ETL pipeline.

```python
# source contains every row in one dataset; FIELD_MAP is already in models.py.
# factors is the selected dataset-field conversion projection from the catalogue.
expressions = []
for source_name, target in FIELD_MAP.items():
    factor = factors[source_name]
    dtype = pl.Int64 if target == "reported_entity_count" else pl.Decimal(22, 8)
    value = ma.col(source_name)
    if factor is None:
        value = ma.lit(None).cast(dtype)
    elif target != "reported_entity_count":
        value = value * ma.lit(factor)
    expressions.append(value.cast(dtype).alias(target))
observations = ma.relation(source).select(
    *[ma.col(name) for name in identity_columns], *expressions
).collect()
```

`identity_columns` contains source-based observation/revision IDs plus the joined context and band attributes. Where a factor varies by record, join the explicit row mapping and use its factor column instead of the literal. Use Mountainash expressions for band-bound conversion as well.

- [ ] Keep the original catalogue files, IDs, evidence and effective dates. Compile their selected context/field/population entries into dataset-sized mapping tables. Preserve applicable mapping revisions as a collection: the demo has 1,296 applied mapping rows for 432 fields, so a single arbitrary mapping ID per field would lose lineage. In `cr6_fields`, retain all applicable mapping/definition/evidence refs along with interpretation and source occurrence metadata. Source relationships and canonical concept relationships remain distinct.
- [ ] In `models.py`, fold the existing context/segment projection into observations, and interpretation/applied-mapping/lineage projection into fields; keep relationships as the third table. Retain the existing numeric schemas and `SilverCandidate` container. Do not create a separate class/table for every old metadata record.
- [ ] In `validate.py`, express key coverage/reference checks as Mountainash joins/anti-joins and keep `contracts/frames.py` for boundary contracts. Allow nullable semantic refs. Trust framework arithmetic and casts; do not add precision guards, per-column validation execution or a second numeric ETL pass.
- [ ] Adapt, rather than duplicate, these existing tests: `test_missing_scale_blocks_only_its_conversion`, `test_domain_amounts_and_rates_are_exact_under_small_decimal_context`, `test_cba_pd_evidence_does_not_leak_to_lgd`, and `test_source_specific_count_overlay_and_perimeter`. Remove tests whose sole purpose is enforcing application-level precision guards. Keep unresolved semantics/source support; change physical table/query assertions to Mountainash.

```bash
uv run pytest tests/silver/test_cr6_conformance.py tests/catalogue/test_cr6_catalogue.py -q
```

- [ ] Once the adapted suite passes, commit `refactor: conform saved CR6 datasets through Mountainash relations`.

## Task 3 — Publish through Python and reconstruct the CBA dataframe

**Files:** Restore/adapt `src/rwa_analysis/storage/{manifests,silver}.py`. Create `src/rwa_analysis/reporting/{__init__,cr6_tables}.py`, `tests/integration/test_cr6_tables.py` and `examples/cr6_research.py`. Consult the old renderer for source bindings and numeric reconstruction behavior; do not restore its presentation code or the CLI.

**Interfaces retained:** `RebuildRequest`, `save_manifest(request, project_root) -> Path`, `rebuild(manifest_path, project_root, warehouse_path) -> str` and `publish_candidate(...)`. Researcher clarification: code provenance is optional metadata, never a Git runtime prerequisite.

**Reconstruction interface:** `reconstruct_cr6(manifest_path: Path, project_root: Path, warehouse_path: Path) -> dict[str, pl.DataFrame]`. Keys are `bundle_key/dataset_id`. Each dataframe has a `source_row` label column followed by the twelve source-labelled numeric columns in their published order, with rows in source order and values in source units. Preserve nulls; units, original tokens and qualification metadata remain in the selected Bronze bundle. Return exact values, not formatted display strings.

- [ ] Restore the publication files:

```bash
git restore --source=0fc5221 --worktree -- src/rwa_analysis/storage/manifests.py src/rwa_analysis/storage/silver.py
```

- [ ] Change Silver table iteration to the three new tables. Retain the existing `IbisBackend.transaction()` path and the fixed behavior that repopulates every requested rebuild. Validate the candidate once; adapt manifest selection to the simple retained-input workflow without requiring regenerated Bronze or rewriting historical manifests. Name the changed physical contract `cr6-simple-v1`. Ordinary extraction and rebuild calls require no Git executable, commit identifier or repository.

```python
with db.transaction():
    for name in ("cr6_observations", "cr6_fields", "cr6_relationships"):
        db.create_table(name, candidate.tables[name].to_arrow(),
                        namespace="silver", overwrite=True)
    db.create_table("silver_publication", marker.to_arrow(),
                    namespace="ops", overwrite=True)
```

`db`, `candidate` and `marker` are the existing publication variables. Keep the same namespace/marker ownership; only the domain-table projection changes.

- [ ] In `test_cr6_tables.py`, adapt the existing `test_persisted_numeric_mutations_and_absence_are_visible` scenarios before implementing reconstruction. Keep its source-backed values and existing `published_cr6` fixture; replace HTML assertions with numeric dataframe assertions. Obtain the EAD column name from the saved dataset's published-field binding. After the same database mutations, assert:

| Persisted first-band EAD | Reconstructed first-band EAD in millions |
|---|---|
| `281509000000` | `Decimal("281509")` |
| `281508000000.01` | `Decimal("281508.00000001")` |
| Deleted first-band observation | Null values in the retained source-labelled row, never a Bronze-value fallback; comparison against the golden detects the lost values |

Use source rows as the left side of reconstruction so missing Silver rows remain visible in the source-shaped result. Adapt the four-bank presentation test's source tokens into numeric/null/order assertions; retain source blank-versus-dash coverage in the independent goldens instead of formatting strings into numeric dataframes.

- [ ] Implement `reconstruct_cr6` using the old `source_binding`/source-ID knowledge and selected Bronze structure. Read persisted tables through Mountainash, join source row/column order and conversion metadata, reverse the factors with sufficient Decimal precision, and materialize only the finished source-shaped table. Retain the old publication-revision mismatch check. A present source value with `not_conformed` stays null in the reconstructed Silver dataframe and remains explainable through field metadata; do not fill it from Bronze.

```python
with IbisBackend(dialect="duckdb", database=str(warehouse_path), read_only=True) as db:
    observations = ma.relation(db.table("cr6_observations", namespace="silver"))
    fields = ma.relation(db.table("cr6_fields", namespace="silver"))
    joined = observations.join(fields, on=["silver_revision_id", "observation_id"])
    cba = joined.filter(ma.col("organisation_id") == "cba")
    # Continue with source-unit expressions and source-order projection,
    # then return a numeric dataframe rather than an HTML rendering.
    frame = cba.to_polars()
```

- [ ] Write the CBA path in `examples/cr6_research.py` as ordinary function calls. It selects the existing v1 bundle; no argument parser, application runner or request JSON is needed:

```python
from pathlib import Path

from rwa_analysis.storage.bronze import BronzeRef
from rwa_analysis.storage.manifests import RebuildRequest, save_manifest
from rwa_analysis.storage.silver import rebuild
from rwa_analysis.reporting.cr6_tables import reconstruct_cr6

root = Path(__file__).resolve().parents[1]
request = RebuildRequest(
    revision_id="simple-cba-v1",
    bronze_refs=(BronzeRef("au/cba/2025-06-30/aps330", "v1"),),
    catalogue_release_path="catalogue/releases/cr6-v1.json",
    conformance_schema_version="cr6-simple-v1",
)
manifest = save_manifest(request, root)
warehouse = root / "data/warehouse-simple-cba-v1.duckdb"
rebuild(manifest, root, warehouse)
tables = reconstruct_cr6(manifest, root, warehouse)
cba = tables["au/cba/2025-06-30/aps330/cr6-residential-mortgages"]
print(cba)
```

Keep supporting-evidence inputs explicit when the selected catalogue references other retained bundles. The original manifest loader already handles this distinction; reuse that knowledge. The historical final-v3 manifest is not runnable under changed code without a new implementation selection.
- [ ] Run the dataframe regression tests and the example. When replaying an already retained manifest, call `rebuild`/`reconstruct_cr6` directly with its existing path rather than recreating the manifest:

```bash
uv run pytest tests/integration/test_cr6_tables.py -q
uv run python examples/cr6_research.py
```

Do not run extraction or overwrite `cr6-2025-final-v3` artifacts. A dataframe viewer may round its display; the actual Decimal values must retain the sub-display difference covered by the test.
- [ ] Commit `refactor: publish and reconcile the simplified CR6 projection`.

**Checkpoint:** Show the reconstructed CBA dataframe, the reused Bronze path and the whole-dataset relation code. This checkpoint reviews new transformation shape, not whether we can rediscover CBA data.

## Task 4 — Run all four retained bundles and adapt the existing lifecycle tests

**Files:** Restore/adapt `tests/integration/test_silver_rebuild.py`; update `tests/conftest.py` only where the changed publication projection/manifest requires it. Extend `examples/cr6_research.py` to all four bundles. Do not import CLI tests.

- [ ] Select all four existing Bronze v1 refs and `catalogue/releases/cr6-v1.json`. No new extractor, golden, catalogue definition or source review is needed for Westpac/NAB/ANZ.
- [ ] Restore the lifecycle tests. Change `TABLES` and expected physical coverage, then retain these behaviors under their existing test names:
  - `test_fresh_rebuild_identity_and_exact_manifest_repeat`: rebuild without PDFs, repeat, delete Silver, repeat again and recover it.
  - `test_real_view_obstruction_rolls_back_all_tables_and_marker`: retarget the obstruction from removed `applied_mappings` to `cr6_fields`; previous tables and marker survive failure.
  - `test_mapping_revision_and_selected_scope_replacement`: changed interpretation keeps observation identity, and removing a selected source removes its observations/fields/relationships.
- [ ] Change read/query helpers to Mountainash. For example, replace the existing `read_snapshot` body with:

```python
with IbisBackend(dialect="duckdb", database=str(path)) as db:
    result = {
        name: ma.relation(db.table(name, namespace="silver")).to_polars()
        for name in TABLES
    }
    result["publication"] = ma.relation(
        db.table("silver_publication", namespace="ops")
    ).to_polars()
return result
```

`TABLES` now contains the three domain names. Express test selection/sorting/joining through `ma.relation(...)`; materialized equality assertions are fine. Raw SQL in the obstruction/corruption setup deliberately damages the backend and is not analytics.
- [ ] Run the adapted owner tests; for failures, demonstrate red before changing the owner implementation. Do not re-create the same tests under new names:

```bash
uv run pytest tests/integration/test_silver_rebuild.py tests/integration/test_cr6_tables.py tests/silver -q
```

- [ ] Extend the example's `RebuildRequest` with the same four existing refs from `config/rebuilds/cr6-2025-final-v3.json` at the baseline commit. Set the new revision/warehouse to `simple-cr6-2025-v1`, retaining `cr6-simple-v1`. The request can be constructed directly:

```python
refs = tuple(
    BronzeRef(f"au/{bank}/{date}/aps330", "v1")
    for bank, date in (("cba", "2025-06-30"), ("westpac", "2025-09-30"),
                       ("nab", "2025-09-30"), ("anz", "2025-09-30"))
)
request = RebuildRequest(
    revision_id="simple-cr6-2025-v1", bronze_refs=refs,
    catalogue_release_path="catalogue/releases/cr6-v1.json",
    conformance_schema_version="cr6-simple-v1",
)
manifest = save_manifest(request, root)
warehouse = root / "data/warehouse-simple-cr6-2025-v1.duckdb"
rebuild(manifest, root, warehouse)
tables = reconstruct_cr6(manifest, root, warehouse)
```

Expect 36 observations, 432 field records and 32 source relationship edges; verify applicable mapping lineage survives the collapsed field table. Preserve CBA's June date, NAB agreements/overlay exclusion and ANZ's unresolved CR6 overlay/count semantics.
- [ ] Compare numeric observations against the preserved final-v3 warehouse through Mountainash, matching source-based observation IDs and the twelve existing numeric field names. The old warehouse's seven-table schema is a comparison input, not the new schema's authority. Use full source/semantic tests to check metadata consolidation.
- [ ] Commit `test: retain CR6 rebuild and reconciliation regressions for compact Silver`.

## Task 5 — Inspect the four dataframes and hand over

**Files:** Update `README.md` and relevant existing workflow documentation with direct Python usage. Historical HTML/image artifacts remain preserved reference material.

- [ ] Inspect the four returned dataframes in Python and compare their source order, labels and exact numeric values against the independently authored expectations. The goldens already own original precision, source notes and blank/dash distinctions; reuse that evidence without rebuilding a presentation layer.

```python
for dataset_id, table in tables.items():
    print(dataset_id)
    print(table)
```

Correct actual differences at the source owner. Do not impose accounting reconciliation or resolve previously unknown meaning by assumption. No browser review, screenshot suite, HTML export or mandatory review report is needed.
- [ ] Update operating docs: existing Bronze → retained catalogue selection → saved manifest → direct `rebuild` call → `reconstruct_cr6` dataframes. Include the example and how to inspect field metadata alongside a dataframe. Record persistent input/warehouse paths and reuse provenance. Backup configuration is separate.
- [ ] Run the completed existing/adapted suite and checks once:

```bash
uv run pytest
uv run ruff check .
git diff --check
```

Check local Markdown links. Record actual outcomes, not the historical 152-test result as if it were current.
- [ ] Commit `docs: document reused inputs and Python CR6 workflow`. Present the four dataframes and observed verification results. Push/PR only when requested; target `develop` and leave PR #1 as the demo reference.

## Handoff

The changed work is the Mountainash execution, compact Silver integration and dataframe reconstruction. Source capture, goldens, saved PDFs, metadata, durable semantic knowledge and the storage/test foundation already exist and are explicitly reused above. Review this plan before implementation; begin with tasks 1–3, then the CBA dataframe checkpoint.
