# Historical source tables implementation plan

> **For agentic workers:** Use `executing-plans` for batched delivery with the
> researcher checkpoints below, and `test-driven-development` for real code.
> Tasks are behaviour-sized; the disposable spike is reference only.

Status: **PROPOSED — awaiting researcher approval.** Design approved 2026-10-12.

**Goal:** Capture all selected four-bank 2024 mortgage tables with composable
metadata, persisted source-defined cells and useful structural comparisons.

**Architecture:** Add source-table datasets and one shared Mountainash pipeline to
the existing Bronze/staging/master flow. Reuse catalogue definitions and scoped
composition; keep occurrences independent. Preserve existing typed CR6/CR9 paths
and adapt explicitly selected Westpac 2025 tables for comparison.

**Tech stack:** Existing locked Python/Mountainash ecosystem, pdfplumber, Decimal,
local DuckDB through mountainash-data, pytest and Ruff. No dependency upgrade assumed.

**Spec:** `/home/ubuntu/git/discreteds/rwa-analysis/docs/04.planning/superpowers/specs/2026-10-12-historical-source-tables-design.md`

## Global constraints and start conditions

- Read the approved spec and its linked principles in full. The
  [source inventory](../../../00.ideation/2026-10-12-historical-source-inventory.md)
  guides selection; it is not a golden set.
- 2024 selection: 516 exposure and 58 backtesting body positions, plus supplementary
  numerical notes. Include comparative panels, NAB's explicitly named RBNZ mortgage
  backtesting and Westpac's p.58 continuation. Preserve ambiguous source meaning.
- Preserve `cr6-v1` and `disclosure-v2`; new source-table transport is `disclosure-v3`.
  One PDF owns one bundle. Save fresh output versions; retain existing assets.
- Source Decimal values/tokens/precision remain exact. Source numeric slots use
  `Decimal(16,8)`; conformed money `Decimal(16,2)`, other numeric ratios/rates
  `Decimal(16,8)`, counts integers, lexical values text. No magnitude-based typing.
- Use Mountainash relations/conformance and native storage transactions. No new
  runtime validation or analytical eligibility gate; partial meanings publish.
- No universal diff service, template registry, automatic vintage selection or
  broad legacy migration. Metadata-ingress and constructor-validation debt stay deferred.
- Before coding, confirm seed branch and whether a fresh coding worktree is wanted.
  Recommend current `develop` after the docs PR merges; do not seed from the spike.
  Documentation remains in the base checkout. A fresh worktree must have the four
  newly tracked PDFs and catalogue; generated Bronze is created in a fresh run root.
- Run `uv sync --locked`. Execution uses native batched work with checkpoints because
  the relevant source, catalogue and storage areas have been inspected in this session.
  Keep independent final correctness/complexity review; delegate only if warranted.

## Review focus and test ownership

| Input/risk | Expected behaviour | Primary owner |
|---|---|---|
| Transposed tables, repeated headers and comparative panels | Every selected field/value and full path retained without fabricated columns | Tasks 1/3/4 PDF goldens |
| Blanks, dashes, lexical N/A and negative EAD variance | Distinct source payloads and tokens survive transport and publication | Task 1 codec; Task 3 legacy/persisted cases |
| Shared definitions with differing qualifiers/timing | Occurrences stay separate; unresolved/conflicting attributes and source evidence survive | Task 2 semantic/persistence case |
| Supplementary billion-scale notes versus body totals | Independent typed figures, own scope, exact conversion; no replacement of table totals | Task 2 CBA; Task 3 Westpac |
| Removing inputs or reading master after staging deletion | No stale child rows; master numbers/metadata own reconstruction | Task 5 integration |

Apply `test-audit` when authoring tests: identify observable behaviour, credible
regression, why existing tests cannot detect it and the real production boundary.
Do not add production hooks for tests. Goldens own complete source correctness;
integration owns transport/persistence risks, not another copy of every golden.

## File and interface map

Production module paths below are relative to `src/rwa_analysis/`; paths beginning
with `extractions/`, `tests/`, `catalogue/`, `examples/` or `docs/` are repository-relative.

New production modules follow existing responsibilities:

- `extraction/source_tables.py`: `SourceTable`, context/metadata, published field
  occurrence, typed cell/lexical payload and cell-based temporal binding. Reuse
  existing axes, segmentations, knowledge, qualifications and source references.
- `domains/source_tables/models.py`, `contracts.py`: flat persisted row declarations,
  named `SourceTableOutput`, shared `TABLES` and `empty_output()` factory.
- `domains/source_tables/semantics.py`: source-cell occurrence selection through
  existing `compose_field`, with no new catalogue hierarchy.
- `domains/source_tables/metadata.py`: flat source/meaning inputs for relations,
  preserving ordered paths, scopes and evidence.
- `domains/source_tables/pipeline.py`: `SourceTablePipeline.conform(inputs, catalogue)`.
- `domains/source_tables/legacy.py`: pure `adapt_legacy(dataset, catalogue)` returning
  `(SourceTable, dict[cell_id, FieldMeaning])`, resolving on original CR6/CR9 addresses.
- `domains/source_tables/reconstruction.py`: `reconstruct_source_tables(output)`
  returning `dict[str, ReconstructedSourceTable]`; each value exposes `.frame` and
  `.metadata` (the table's filtered `SourceTableOutput`). Keys are bundle/dataset IDs.

Pipeline inputs are `tuple[LoadedBronze, ...]`, catalogue is `CatalogueRelease`,
result is `SourceTableOutput`. `resolve_cell(catalogue, bundle, table, cell)` returns
`FieldMeaning`; it handles new source tables only. `adapt_legacy` handles the existing
`Cr6Dataset | Cr9Dataset` types with their existing resolvers. No PDF or database I/O
in these functions. `empty_output()` returns declared typed empty relations.

Public `tables`, `fields`, `axes`, `cells` and `meanings` relations serve the concrete
callers below. Preserve ordered axis paths, segmentations/bands/membership,
qualifications/scopes, relationship endpoints, timing and semantic references through
related metadata, reusing compatible existing row types and evidence conventions.
Task 2 derives the actual declared inventory from those relationships; do not require
a separate relation for every metadata type or introduce generic evidence/decision
tables solely to complete a prescribed list. Evidence retains its owner and ordering;
source qualifications remain distinct from researcher assertions.

Modify existing owners: `extraction/datasets.py`, `extraction/codec.py`,
`storage/bronze.py`, `storage/silver.py`, `storage/tables.py`,
`storage/consolidation.py`, `operations.py`, `composition.py`, `workflow.py`.
Only move `model_spec`/`TableDeclaration` to a shared `domains/contracts.py` if needed
to remove new ownership under CR6; preserve existing imports/callers during that move.

New extractors mirror existing paths under `extractions/au/<org>/<2024-date>/aps330/`.
Their independent tests/fixtures mirror that hierarchy under `tests/bronze/`.
Extend `tests/support/golden.py` only for comparison of new source payloads; never
generate expected fixtures from extraction output.

## Task 1 — CBA complete source capture and durable transport

**Files:** Create `extraction/source_tables.py`; create
`extractions/au/cba/2024-06-30/aps330/{extract.py,review.md}` and
`tests/bronze/au/cba/2024-06-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`.
Modify `extraction/{datasets.py,codec.py}`, `storage/bronze.py`,
`tests/integration/test_bronze_storage.py`, `tests/conftest.py` and golden support.

**Consumes:** CBA PDF pp.49–51 and 56 with applicable definitions/notes.
**Produces:** Existing `extract(pdf_path) -> ExtractionBundle` entrypoint returning
`disclosure-v3`; `BronzeStore.save/load` roundtrips it. CBA fixtures expose the real
extractor output as input, not expected answers.

- [ ] Read/render the full selected CBA source and independently author expected
  cells/metadata before implementing the extractor. Separate three exposure panels
  and two backtesting tables. Include 125 body positions plus panel-specific overlay
  and scaling observations; document unknown restatement-note scope and EAD timing.
- [ ] Write failing full-source and transport cases. Use existing complete golden
  comparison where compatible. Example transport assertion at the public boundary:

  ```python
  store = BronzeStore(tmp_path / "bronze")
  ref = store.save(cba_2024_bundle, "historical-test")
  restored = store.load(ref).bundle
  assert restored == cba_2024_bundle
  assert restored.schema_version == "disclosure-v3"
  ```

  Add one independently authored small wire case with Decimal, integer, lexical,
  blank/dash and supplementary-note payloads to catch discriminator coercion.
  Retained old-wire fixture cases continue to assert their original representation.
  Run `uv run pytest tests/bronze/au/cba/2024-06-30/aps330 tests/integration/test_bronze_storage.py -q`
  and establish the intended missing-capability failures before implementation.
- [ ] Implement source-table types and the bespoke extractor fresh. Cell IDs are
  local stable strings; cells bind fields/leaf axes, contexts, bands and qualifiers.
  Note cells have no fabricated table positions. Field occurrences declare source
  form and result kind; no canonical equivalence is encoded by their Python names.
  Widen the `Dataset.metadata` annotation to the two actual metadata container types.
  New temporal bindings address cell ID plus role; retain descriptor statuses.
- [ ] Add explicit v3 dataset/payload dispatch; reuse primitive scalar conversion.
  Keep v1/v2 writers/readers unchanged. Do not attach new constructor checks or
  automatic encode/decode validation to v3. In `BronzeStore.save`, retain old-format
  staged verification for old formats; the new v3 path writes via mountainash-files
  and publishes without adding that automatic comparison. Ordinary explicit load
  decodes the saved payload; tests prove its roundtrip.
- [ ] Run focused cases green, inspect the real saved CBA bundle and commit this
  behaviour as `feat: capture historical CBA tables in source-defined Bronze`.

## Task 2 — Composed semantics through persisted reconstruction

**Files:** Create `domains/source_tables/{__init__.py,models.py,contracts.py,semantics.py,metadata.py,pipeline.py,reconstruction.py}`.
Modify `storage/{silver.py,tables.py}`, `operations.py`, `composition.py`, `workflow.py`.
Create `tests/silver/test_source_table_conformance.py` and
`tests/integration/test_source_table_workflow.py`. Create historical catalogue
definitions/mappings and `catalogue/releases/historical-mortgages-v1.json` using the
existing catalogue file conventions; extend the selected release during later tasks.

**Consumes:** Saved CBA v3 bundles and versioned catalogue selections.
**Produces:** Named `.source_tables` output; source-only ordinary session run;
persisted `reconstruct_source_tables(output.source_tables)` with full metadata.

- [ ] Write failing cases for (1) unmapped average EAD retained with known unit
  conversion, (2) no fabricated average-PD field, (3) two source occurrences sharing
  one reviewed measure revision with distinct evidence, (4) scoped refinement/conflict
  and unknown timing, and (5) complete persisted metadata and value reconstruction.
  Use independently authored synthetic catalogue fixtures to demonstrate conflicts
  when real source evidence does not establish a semantic equivalence or conflict.
  Do not turn those fixtures into production financial interpretations.
- [ ] Exercise the actual public session boundary with temporary storage settings:

  ```python
  result = session.run(
      documents=(DocumentSelection(
          "extractions/au/cba/2024-06-30/aps330/extract.py",
          "raw/cba-2024-06-30-aps330.pdf"),),
      catalogue=CatalogueSelection(
          release_path="catalogue/releases/historical-mortgages-v1.json"),
      run_name="historical-test", revision="cba-first")
  output = session.silver.read(result.publication).source_tables
  average = output.cells.filter(ma.col("field_id") == "average_ead")
  assert Decimal("0.359") in average.to_polars()["source_number"].to_list()
  assert output.meanings.filter(
      ma.col("normalised_amount") == Decimal("359000")
  ).count_rows() >= 1
  ```

  Define `session` through existing `build_session(OrganisationSettings(...))` with
  all generated paths under `tmp_path`. The fixture creates inputs through the real
  CBA extractor; expectations above come from p.49. Independently assert overlay
  amount `7.4` billion converts to `7400000000`, while original tokens remain.
  Run `uv run pytest tests/silver/test_source_table_conformance.py tests/integration/test_source_table_workflow.py -q` red.
- [ ] Implement occurrence selection and compose meanings. Use cell IDs only for new
  source-table mappings; persist concept/measure/mapping revisions, assertions,
  alternatives and decision/evidence references. Unknown meaning never removes cells.
  Project all source metadata including full ordered paths and qualified endpoints.
  Numeric conversions are dataset-sized Mountainash expressions. Declare scale and
  conversion-factor columns with sufficient integer places for `10^9` (e.g.
  `Decimal(16,6)` for these source factors), independently of source-number slots.
  Inspect the pinned API for each used path; do not use unsupported 38-digit
  conformance targets or a local backend workaround.
- [ ] Add `.source_tables` as a trailing defaulted member to existing candidate/output
  dataclasses, using `empty_output`, preserving their existing constructor positions.
  Extend the shared storage declaration inventory. Default `ConformanceOperation`
  passes only native source-table datasets to the new pipeline; old datasets remain
  in their original pipelines. Keep existing independent session calls and `.cr6`/
  `.cr9` results intact. Reconstruction adds native source frames to the existing
  frame mapping; direct source reconstruction exposes `.frame` and `.metadata`.
- [ ] Prove persisted ownership by changing one source number in the test DuckDB via
  native storage, then reconstructing: the frame must show the changed saved value.
  Check scoped evidence, descriptor uncertainty, ordered paths and note/body separation
  on readback; a simple row count is insufficient. Rerun focused cases green and
  `tests/integration/test_organisation_workflow.py` / `test_cr9_workflow.py`.
- [ ] Commit as `feat: persist and reconstruct composed source-table observations`.

**Researcher checkpoint A:** Run the complete real CBA source → saved Bronze →
Silver → reconstructed tables path in a fresh retained temporary root. Present the
five table datasets, supplementary notes, queryable unmapped measure and metadata
composition. Record paths/results here. Pause before Tasks 3–5 for researcher review;
this is the first executable checkpoint, not the end of production scope.

## Task 3 — Westpac historical capture and explicit legacy comparison

**Files:** Create Westpac 2024 `extractions/au/westpac/2024-09-30/aps330/{extract.py,review.md}`
and `tests/bronze/au/westpac/2024-09-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`.
Create `domains/source_tables/legacy.py`, extend pipeline dispatch for explicit calls,
historical catalogue release/mappings, and `tests/integration/test_source_table_workflow.py`.
Create `tests/silver/test_source_table_legacy.py`.

**Consumes:** Westpac 2024 pp.42,45,56–58; saved modern CR6/CR9 datasets and their
existing catalogue definitions. **Produces:** complete 234 historical body positions,
supplementary RWA figures, and explicit source-table projections of selected 2025 inputs.

- [ ] Independently author all source expectations before extraction. Cover all three
  exposure and three backtesting panels, subtotal/default/total roles, two dashes and
  negative September 2023 EAD variance. Keep notes' $131989m and $214081m apart from
  the table's $116228m RWA total; retain backtesting NZ-history scope and unknown dates.
- [ ] Write failing full-source cases and legacy projection tests. Verify original
  count 564613 remains integer, fourteen `N/A` ratings remain lexical, nested label
  paths/order survive, and seven within-row new-default subsets retain endpoints.
  Verify old resolver outputs still supply their original definition/conversion
  references; no fabricated mapping applicability based on document date.
  Run `uv run pytest tests/bronze/au/westpac/2024-09-30/aps330 tests/silver/test_source_table_legacy.py -q` red.
- [ ] Implement the bespoke historical extractor and per-model legacy adapter fresh.
  Resolve legacy meanings using the original rows and field keys before associating
  them with adapted cells. Use actual published bindings and lexical axes, not a
  cross-product of every dataclass member. Convert CR6 snapshot timing only to its
  established measurement role; copy CR9's existing field-level roles.
- [ ] Implement this ordinary explicit composition in the integration example/test:

  ```python
  inputs = session.load_bronze((historical_ref, modern_ref))
  selection = CatalogueSelection(
      release_path="catalogue/releases/historical-mortgages-v1.json")
  candidate = session.conform(inputs, catalogue=selection)
  release = load_catalogue(project_root / selection.release_path)
  candidate = replace(candidate, source_tables=SourceTablePipeline().conform(inputs, release))
  publication = session.publish(candidate, revision="westpac-comparison")
  source = session.silver.read(publication).source_tables
  frames = reconstruct_source_tables(source)
  ```

  Both references are real saved inputs from `BronzeStore`, so candidate selection
  and manifest include every adapted source. Pipeline `.conform` accepts native and
  legacy datasets when directly selected; no flag or implicit all-bank migration.
  A normal modern session without this explicit call still has empty source output.
  Existing session frame mappings retain the old modern numeric frames; explicit
  source frames/metadata remain separately accessible, avoiding duplicate-key overwrite.
- [ ] Run focused tests green plus the persisted comparison. Confirm historical
  portfolio grain versus modern bands and source field inventories independently
  of normalised numbers. Commit as `feat: capture Westpac history and adapt selected legacy tables`.

## Task 4 — Complete NAB/ANZ capture and historical interpretations

**Files:** Create `extractions/au/{nab,anz}/2024-09-30/aps330/{extract.py,review.md}` and
matching `tests/bronze/au/{nab,anz}/2024-09-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`.
Extend catalogue release/definitions/mappings and `tests/silver/test_source_table_conformance.py`.
Each bank is its own source-authoring/red-green/commit unit within this task.

**Consumes:** NAB pp.38,40–42,50–51 and ANZ pp.53–55,57 with applicable definitions.
**Produces:** NAB 90 and ANZ 125 selected body positions; 574 overall plus numerical
notes; complete evidence-backed mappings with explicitly unresolved attributes.

- [ ] Author NAB expectations independently: two exposure panels without a total
  column; three backtesting panels in each of two tables, retaining distinct main and
  RBNZ mortgage populations. Include arrangement-based average EAD, changed PD models,
  continuing-balance cohort restriction and different APRA/RBNZ LGD conventions.
- [ ] Author ANZ expectations independently: three exposure panels with original
  two-line bands and mortgage total column; one backtesting panel. Retain PD/EAD
  2019–2023, LGD 2018–2022 and separate September 2023 cutoff without a unified window.
- [ ] Run each new complete-source test red, implement its bespoke extractor, then
  run green. Use the same source comparison boundary as Task 1, for example:

  ```python
  bundle = run_extractor(extractor_path, pdf_path)
  expected = json.loads(golden_path.read_text())
  assert_golden(encode_payload(bundle), expected)
  ```

  `extractor_path`, `pdf_path`, `golden_path` are the bank-specific paths above, rooted
  through `project_root`; expected JSON is independently source-authored. Run
  `uv run pytest tests/bronze/au/nab/2024-09-30/aps330 tests/bronze/au/anz/2024-09-30/aps330 -q`.
- [ ] Populate the existing catalogue release with reviewed definitions and explicit
  occurrence mappings. Reuse genuine shared concepts; do not force identical average
  EAD counting, EAD-ratio timing or default-rate cohort definitions across banks.
  Record researcher decisions for uncertain financial interpretation; retain unresolved
  attributes until decided. Development fixtures, not invented source facts, establish
  composition behaviour where the real sources do not prove equivalence.
- [ ] Conform actual saved NAB/ANZ bundles and check persisted distinguishability of
  main/RBNZ populations and field-specific time. Add only these new regression risks
  to the shared conformance tests; source tests own full numeric transcription.
  Commit separately as `feat: capture historical NAB mortgage disclosures` and
  `feat: capture historical ANZ mortgage disclosures`.

## Task 5 — Master reconstruction, structural research and delivery

**Files:** Modify `storage/consolidation.py`, `tests/integration/test_master_consolidation.py`;
create `examples/historical_mortgages.py`; update `README.md`, `docs/architecture.md`,
`docs/README.md`, source reviews and this plan's execution evidence. Record concrete
generalisation lessons in `docs/00.ideation/2026-10-12-historical-implementation-lessons.md`.

**Consumes:** Four complete historical publications and explicitly selected modern
Westpac projection. **Produces:** reproducible retained demonstration and interactive
structural inventory from persisted master, with source-shaped frames and metadata.

- [ ] Extend existing master tests with source-table publication: retain values and
  metadata after deleting staging DBs; rebuild with fewer inputs and confirm removed
  source/child rows disappear. Change a persisted value before consolidation and prove
  master copies it. Keep the old CR6/CR9 assertions, without cloning their whole suite.
  Run `uv run pytest tests/integration/test_master_consolidation.py -q` red.
- [ ] Extend the current declared-inventory consolidation and source reconstruction.
  Select source-table outputs from persisted master. Preserve old frame keys; when
  source output includes legacy projections, keep those source frames available via
  `reconstruct_source_tables` rather than overwriting existing numeric frames.
  Do not reinterpret Bronze or introduce automatic snapshot/vintage selection.
- [ ] Build the ordinary interactive example from tracked PDFs into a fresh retained
  `/tmp/opencode` root. Expose `sessions`, `publications`, `master_publication`,
  `output`, `source_tables` and `field_inventory` at module scope for `python -i`.
  Use actual saved inputs and the explicit Task 3 candidate composition for Westpac.
  Join persisted field/axis/meaning relations with Mountainash; include unmapped
  fields and scope/time/revision references. Field presence must not filter on numeric
  non-nullness. Keep multiple definition references visible where a field varies by cell.
  Rebanding, inference and automatic equivalence decisions are not part of this example.
- [ ] Run focused cases green, then the real example:

  ```bash
  uv run python examples/historical_mortgages.py
  uv run pytest
  uv run ruff check src tests examples extractions
  git diff --check
  ```

  Record actual cell counts, supplementary observations, retained paths and structural
  findings. Check each golden's selected scope rather than using 574 alone as a proof
  of completeness. Existing four-bank examples must still work against fresh roots.
- [ ] Update current architecture/README to implemented behaviour only after the
  above proof. Retain lessons about local geometry, shared contracts, legacy metadata
  adaptation and catalogue composition; link any concrete techdebt/upstream finding to
  its owner. Do not create speculative backlogs from every observation.
- [ ] Run independent correctness and complexity reviews of the final diff. Apply
  complexity cuts before triaging defects; repair in-repo defects now. A reproduced
  required dependency defect blocks delivery until its upstream resolution and full
  relevant proof; no unapproved workaround or silent acceptance with follow-ups.
- [ ] Commit as `feat: demonstrate historical mortgage structural research`; open the
  coding PR against `develop`, preserving this approved documentation lineage.
  Offer local/worktree cleanup after review/merge, retaining run artifacts separately.

**Researcher checkpoint B:** Present the full four-bank retained run, real Westpac
cross-vintage structural inventory, independent reviews and remaining explicitly
unresolved source semantics. No claim of general fifteen-year coverage beyond the
implemented selected inputs.

## Evidence and status record

No production code or tests have been written/run under this plan. During planning,
existing dataset/codec, shared composer, source pipelines, session/storage/master and
golden/test boundaries were inspected. The implementation spike remains disposable.
Execution records and checkpoint outcomes are appended here when actually observed.

### Planning reviews — 2026-10-12

- Independent complexity review: keep the five behaviour-sized tasks, early proof,
  named public interfaces and boundary tests. Cut the mandatory nineteen-member
  metadata inventory; preserve required information using actual relationships and
  existing evidence conventions instead. Applied before correctness triage.
- Independent correctness review: no material plan gaps identified. Source fidelity,
  pinned-backend declarations and complete metadata roundtrips remain assigned
  implementation proof, not claims established by planning.
- No required upstream defect was established. No implementation or test execution
  occurred as part of these reviews. Researcher plan approval remains outstanding.
