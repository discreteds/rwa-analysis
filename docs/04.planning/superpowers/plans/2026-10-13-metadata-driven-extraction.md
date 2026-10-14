# Metadata-driven extraction implementation plan

> **For agentic workers:** Use `executing-plans` for batched delivery with the
> checkpoints below and `test-driven-development` for approved production work.
> Use `test-audit` when authoring/changing tests. Tasks are behaviour-sized, not
> micro-steps. Independent correctness and complexity reviews precede delivery.

Status: **APPROVED — Tasks 4–6 complete; checkpoint B awaiting acceptance.** Checkpoint A was accepted on 2026-10-14. The researcher approved the plan,
merged PR #17 and authorised the separate `feature/metadata-driven-extraction`
worktree seeded from `develop` at `2ef55de` on 2026-10-13. Checkpoint A is the
current execution boundary; Tasks 4–7 await that checkpoint review.

**Goal:** Drive all existing selected four-bank captures and their Bronze-to-Silver
journey from singly defined physical, semantic and contextual metadata.

**Architecture:** Separate execution settings, reusable definitions and source binding
declarations from physical operations. Retain typed capture snapshots; resolve all
occurrence kinds through one interpretation owner and project existing named outputs
from those results. Keep saved-format compatibility and existing storage orchestration.

**Tech stack:** Python dataclasses, pdfplumber, existing catalogue composition,
Mountainash relations/TypeSpecs, mountainash-files and mountainash-data/DuckDB.

**Spec:** [Approved design and spike evidence](../specs/2026-10-13-metadata-driven-extraction-design.md).
Read the specification and its governing principles in full before executing.

## Global constraints

- Production code is written afresh. Do not merge/cherry-pick
  `spike/metadata-driven-extraction` or wrap production tests around its code.
- Complete scope is all twelve currently selected source PDFs: four banks in
  2023, 2024 and 2025. No additional portfolios or reports are implied.
- Reuse existing concepts/measures, assertions, qualifiers, band and temporal types.
  Do not adopt the spike's `SimpleNamespace` catalogue or flat temporal attributes.
- Existing `cr6-v1`, `disclosure-v2`, `disclosure-v3` bytes retain their contracts.
  New captures use an explicit `disclosure-v4` representation, not new fields in old bytes.
- Money remains `Decimal(16,2)`, scalar results `Decimal(16,8)`, counts integer;
  retain source tokens/precision and existing wider working arithmetic.
- Unresolved/conflicting meaning is data. No runtime validation, precision checks,
  completeness gates, analytical eligibility gates or automatic date/meaning inference.
- Explicit overrides and whole-mapping supersession retain their different meanings.
  Partial temporal knowledge does not disable independently supported conversion.
- Use native Mountainash for relational work and its data/files/settings packages at
  existing boundaries. No new DSL, package, plugin discovery or revision-store service.
- Single-writer full-replacement staging/master remains. Mutable paths do not become
  historical snapshots. Retain actual inputs, definition revisions and code references.
- Use new output roots/run names for proofs; preserve retained project data and PDFs.
- Before coding, confirm implementation seed branch and whether a worktree is required.
  Use a production feature branch from the approved documentation/integration state,
  never from the spike. Keep associated code/docs in one implementation PR to `develop`.

## Review focus and primary test owners

| Distinct failure mode | Expected behaviour | Owner |
|---|---|---|
| Same local ID on a field/axis or in different reports | Kind/scope/bundle-qualified references remain distinct; equal values do not merge vintages | Tasks 1–2 transport/address and resolver cases |
| Shared comment used by several tables, including numerical notes | One captured passage per physical occurrence; explicit target links and separate note-cell payload survive readback | Task 3 persisted metadata case |
| Unknown time, provisional support or conflicting context | No date fallback or specificity winner; independent conversion remains available | Task 2 resolver cases |
| Legacy count/rating/partial-period metadata routed through the new owner | Same numeric/lexical outputs and source evidence; no second semantic resolution in projections | Task 5 existing domain conformance/projection cases |
| Fewer inputs or deleted staging after consolidation | All dependent published rows are removed/copied consistently; reconstruction uses persisted data | Task 7 existing workflow/master cases |

The authoring gate applies per case: name the observable behaviour, credible
regression, strongest existing owner and why another layer is necessary. Add no
test-only production exports. Goldens own PDF correctness; codec tests own transport;
resolver cases own interpretation; persisted tests own storage and reconstruction.

## Production boundaries to implement

These details were approved with this plan on 2026-10-13. They replace prototype
shortcuts, not the accepted source–meaning–context architecture.

The file map identifies ownership, not a mandatory module count. Keep a small
single-use implementation in its existing owner rather than add forwarding modules.

| File/area | Responsibility |
|---|---|
| New `src/rwa_analysis/extraction/definitions.py` | Frozen authoring declarations, occurrence addresses, explicit bindings and retained snapshot types |
| New `src/rwa_analysis/extraction/capture.py` | Invoke supplied physical operations; assemble captured payloads/structure and snapshot |
| New `src/rwa_analysis/extraction/physical.py` | Only demonstrated shared physical readers; source-local operations remain available |
| Existing `extraction/runner.py`, `operations.py` | Load explicit source declaration/operation files and keep existing selected script entrypoints callable |
| Existing `extraction/codec.py`, `datasets.py`, `storage/bronze.py` | Explicit new captured-bundle variant and lossless v4 transport; old decoders remain |
| Existing `catalogue/models.py`, `load.py`, `resolve.py`; new `catalogue/occurrences.py` | Typed occurrence scopes/contributions and one source/context/semantic resolver |
| Existing `domains/source_tables/` | Normalised metadata, values, occurrence references, conformance and structural reconstruction |
| New `domains/cr6/projection.py`, `domains/cr9/projection.py` | Existing named domain outputs from resolved source relations and declared domain field bindings |
| Existing `storage/tables.py`, `silver.py`, `consolidation.py`, `manifests.py`, `workflow.py` | Persist/reload/copy the declared outputs and retained selections |
| Each dated source directory: `definition.py`, `physical.py`, thin `extract.py` | Reviewed source metadata; geometry operations; compatibility entrypoint |

### Named interfaces and responsibilities

Implement these in the owning files above; exact dataclass field order is not a
public requirement. Use the existing typed source payloads and descriptors rather
than an unrestricted dictionary for semantic content.

- `OccurrenceRef`: bundle key, scope (dataset ID or bundle scope), occurrence kind,
  local ID. Row/column/header/block distinctions remain explicit. Retained references
  also identify the selected Bronze version where a particular capture is intended.
- `PhysicalBinding`: revision reference, selected operation name and serialisable
  physical parameters. `CapturedFragment`: binding/slot, original text and actual
  `SourceReference` evidence. These do not contain inferred financial meaning.
- `ContextDefinition`: revision identity, typed assertions, temporal/segment references
  and evidence. Reuse `TemporalDescriptor` and its named roles, including partial bounds.
- `OccurrenceBinding`: occurrence reference, physical slot references, selected
  definitions/context, explicit structural links and applicable payload/unit metadata.
  Ordinary Python construction can expand the currently reviewed grids without
  duplicating definitions per cell; no general templating or declaration language
  is needed. Captured source headers remain evidence.
- `CaptureDefinition`: one document's reviewed selection and composed bindings.
  `CaptureSnapshot`: serialisable selected definitions and bindings, without callables.
- `CapturedBundle`: new v4 bundle containing that snapshot, typed captured source
  tables and bundle-scoped evidence/occurrences. Keep it distinct from old
  `ExtractionBundle` so adding snapshot members cannot change old wire encoding.
- `ResolvedCapture`: captured input, selected interpretation references and resolved
  meanings/context keyed by `OccurrenceRef`. It is the common input to tabular
  conformance and projections; it is not another stored source copy.
- `DomainFieldBinding`: only where an existing CR6/CR9 projection requires it, retain
  domain name, original record ID and field key for a source cell. This supplies
  original catalogue addressing and named output projection, not financial definitions.

```python
# Approved production signatures; normal Python calls, no discovered registry.
physical_operation(document, binding: PhysicalBinding) -> tuple[CapturedFragment, ...]
capture(pdf_path, definition: CaptureDefinition, operations) -> CapturedBundle
run_capture(definition_path, operations_path, pdf_path) -> CapturedBundle
resolve_capture(loaded_bronze, catalogue) -> ResolvedCapture
project_cr6(source_output, domain_bindings) -> Cr6Output
project_cr9(source_output, domain_bindings) -> Cr9Output
```

`definition.py` exposes `DEFINITION`, whose snapshot contains the selected reusable definitions;
`physical.py` exposes `OPERATIONS`. Neither imports the other. `run_capture` loads
both using the existing explicit module-loading pattern. A dated `extract.py` calls
it with sibling file paths, retaining the current `DocumentSelection` call shape.

Catalogue scope becomes a typed choice between retained `MappingScope` and explicit
occurrence targets. Adapt old record/field addresses before matching, preserving their
date policy. Generalise the existing composer; do not independently reimplement its
conflict/override algorithm. Source/context contributions and interpretation mappings
retain separate provenance while passing through the same composition rules.

Keep `.source_tables.meanings` as the cell numeric/semantic projection for current
research queries. Generalise assertion, mapping, context and evidence relations to
occurrence-qualified owners so non-cell meanings are queryable too. Related context
definitions are stored once with explicit occurrence references. Shared bundle evidence
must be included when reconstructing a table's reachable metadata; filtering every
relation only by `table_id` is insufficient. No second independently resolved semantic
table or canonical definition store is introduced.

## Task 1 — Typed capture declarations and retained transport

**Files:** Create `extraction/definitions.py`; extend `extraction/datasets.py`,
`extraction/codec.py`, `storage/bronze.py`; extend
`tests/integration/test_source_table_transport.py`, `tests/integration/test_bronze_storage.py`
and `tests/conftest.py` only for shared input fixtures.

**Consumes:** Existing payload, axis, qualification, segmentation, temporal and reference types.
**Produces:** `CapturedBundle`/snapshot types and save/load support for `disclosure-v4`.

- [x] Author independent transport cases before code: a shared comment with two
  targets; field/axis same local spelling; Decimal/integer/lexical/blank payloads;
  retained source scope and revision references. The expected payload facts are
  literals or existing source goldens, not generated from the new encoder.
- [x] Run the focused tests and record the intended RED result. Keep existing v1/v2/v3
  cases, including the checkpoint-v3 default metadata case, attached to old-format
  fixtures rather than accidentally converting every input fixture to v4.
- [x] Implement the typed declarations and separate v4 branch of the existing codec.
  Preserve old dispatch and encoding. Extend `LoadedBronze`/store typing to accept the
  new variant; no extra constructor/roundtrip validation on the new path.
- [x] Decode saved snapshots without importing the declaration or physical-operation
  files. Retain selected definition contents, not just mutable file paths.
- [x] Run focused tests to GREEN and commit this behaviour-sized change.

```python
# Extend the existing transport owner with a new typed input fixture.
saved = store.save(captured_bundle, "metadata-transport")
loaded = store.load(saved).bundle
assert loaded.schema_version == "disclosure-v4"
assert loaded.snapshot == captured_bundle.snapshot
# This is transport equality, not a claim of PDF correctness.
assert encode_payload(loaded) == encode_payload(captured_bundle)
assert encode_payload(legacy_bundle) == legacy_payload
```

Run: `uv run pytest tests/integration/test_source_table_transport.py tests/integration/test_bronze_storage.py -q`

## Task 2 — Resolve source, context and meaning for every occurrence kind

**Files:** Extend `catalogue/models.py`, `load.py`, `resolve.py`; create
`catalogue/occurrences.py`; revise `domains/source_tables/semantics.py` and reuse the
CR6/CR9 address/date adapters; create `tests/catalogue/test_occurrence_resolution.py`
and extend existing catalogue tests only where retained addressing is affected.

**Consumes:** Captured snapshots and existing versioned catalogue selections.
**Produces:** `resolve_capture(loaded_bronze, catalogue) -> ResolvedCapture`.

- [x] Author parameterised cases for table/axis/field/cell/comment resolution;
  source-supported context plus selected interpretations; explicit overriding versus
  whole-mapping supersession; provisional/conflicting support; and temporal role
  applicability with an independently usable percent conversion. Include two report
  vintages and one shared comment to expose address or scope collapse.
- [x] Record RED at the resolver boundary before implementing. Use direct typed
  source and mapping inputs, not mocks that calculate the expected interpretation.
- [x] Generalise selection and the current composition core. Existing `compose_field`
  callers and retained catalogue files continue to route through that core. Extend
  typed reference/attribute handling for structural roles and contexts without adopting
  arbitrary spike dictionaries or forcing comments into fake numeric fields.
- [x] Resolve explicit context contributions once; record provenance and alternatives.
  A conflicting/missing temporal role leaves only its dependent attributes unresolved.
  Do not use physical containment or document dates as silent semantic inheritance.
- [x] Run new and existing resolver cases to GREEN; commit.

```text
Same cell + percent conversion + unknown required measurement date
    -> source retained, factor 0.01 available, date-restricted meaning unresolved
Two conflicting entity assertions, no override
    -> conflicting status and both evidence chains
Explicit field refinement over table contribution
    -> only named overridden attributes change; unrelated table assertions survive
Source note + researcher correction revision
    -> original wording preserved, selected resolved meaning changed
```

Run: `uv run pytest tests/catalogue tests/silver/test_historical_catalogue.py -q`

## Task 3 — First production PDF-to-persistence path: ANZ 2023

**Files:** Create `extraction/capture.py`, `extraction/physical.py`; extend
`extraction/runner.py`, `operations.py`, `domains/source_tables/{models,contracts,metadata,pipeline,reconstruction}.py`,
`storage/{tables,silver,manifests}.py` and `workflow.py`; split
`extractions/au/anz/2023-09-30/aps330/{extract,definition,physical}.py`;
extend its existing golden test and `tests/integration/test_source_table_workflow.py`.

**Consumes:** Tasks 1–2 contracts and resolution; actual ANZ PDF and independent goldens.
**Produces:** Full ANZ 2023 selected capture through the ordinary session, saved v4,
contextual Silver and source-shaped readback. This task is the early executable checkpoint.

- [x] Extend existing source/persisted tests before implementing the new path. Preserve
  all 125 financial cells and applicable evidence, not just the spike's five cells.
  Add distinct persisted assertions for shared comments, occurrence-scoped context,
  pre/post-framework headers and the NZ blank. Keep existing field-specific timing
  expectations and all independent source labels, values and relationships.
- [x] Record RED, then implement physical-fragment invocation, capture assembly and
  source declaration loading. Keep execution roots in existing settings; source geometry
  in declaration parameters; semantic/time definitions outside physical operations.
- [x] Declare native flat relations for occurrence/context/reference additions; use
  the current table inventory for publication/readback. Populate current cell meanings
  from the resolved capture; never resolve them again in numeric projection code.
- [x] Make an explicit semantic revision over retained evidence and reconform saved
  Bronze. Load a retained catalogue release containing an occurrence-targeted
  comment/context refinement with an explicit override through the ordinary catalogue
  loader; verify the resolved non-cell meaning and provenance after publication.
  Keep existing old-scope catalogue-loading coverage. This exercises the new saved
  scope representation and override handling, not only direct typed resolver inputs.
  Remove the test's copied PDF and source-authoring files before that rerun;
  use real store/session APIs, not a test-only no-PDF mode. Values and source IDs remain
  fixed while selected interpretation provenance changes.
- [x] Run focused tests and an ordinary retained session example to GREEN. Commit
  and present checkpoint A before migrating more sources.

```python
# Existing persisted workflow pattern, with the independently checked source selection.
refs = session.save_bronze(session.extract(documents), "metadata-proof")
inputs = session.load_bronze(refs)
candidate = session.conform(inputs, catalogue=selected_catalogue)
publication = session.publish(candidate, revision="metadata-proof")
output = session.silver.read(publication).source_tables
assert output.cells.count_rows() == 125
assert output.cells.filter(ma.col("cell_id") == "mortgage/ead_ratio").item(
    "source_number"
) == Decimal("1.01")
```

Run: `uv run pytest tests/bronze/au/anz/2023-09-30 tests/integration/test_source_table_workflow.py -q`

**Checkpoint A:** inspect separate configuration/definitions/operations, actual v4
snapshot, all-kind persisted metadata and the saved-only reinterpretation. Stop for
researcher review; a numeric-only round trip is not sufficient evidence.

## Task 4 — Migrate the remaining seven historical sources

**Files:** The `extract.py` in each directory below becomes a thin entrypoint;
create sibling `definition.py`/`physical.py`. Extend shared physical readers only for
demonstrated reuse. Update the corresponding `tests/bronze/` golden tests and
`tests/integration/test_historical_vintages.py` for retained source identities.
Update source reviews only when their content or references change.

| Source directory under `extractions/au/` | Source differences that must survive |
|---|---|
| `cba/2023-06-30/aps330/` | 1.10 versus 1.06 scalars; June-only $7.4bn note attached to LGD; pre-reform histories/restatements |
| `cba/2024-06-30/aps330/` | Three comparative panels, average-EAD unknown denominator and source-specific overlays |
| `westpac/2023-09-30/aps330/` | Hidden text-layer selection, lexical N/A, 25% floor transition, note/body RWA distinction |
| `westpac/2024-09-30/aps330/` | Different outstandings wording, continuation panels, nested predicted/observed headers |
| `nab/2023-09-30/aps330/` | March undrawn restatement; separate main/RBNZ scopes; unresolved PD outcome bounds |
| `nab/2024-09-30/aps330/` | Its own PD cohort/model wording and population-specific floor qualifications |
| `anz/2024-09-30/aps330/` | Its own history windows/cutoffs; no inferred year-decrement templates |

**Consumes/produces:** Same capture and resolver interfaces as Task 3; no per-bank
conformance branch. Existing selected catalogue members stay authoritative unless
source review establishes a separately approved interpretation change.

- [x] For each source, extend the existing independent golden test to enter the new
  declared path and record RED. Capture all existing cells, structural evidence and
  applicable qualifiers; do not regenerate expected fixtures from new declarations.
- [x] Re-express metadata as explicit bindings; retain source-local physical algorithms
  where required. Share a reviewed definition by reference, not a previous dated extractor.
  Remove superseded semantic construction from each migrated `extract.py`.
- [x] Run that source and its adjacent vintage tests to GREEN. Commit per coherent
  bank migration, keeping one implementation PR.
- [x] Run the joint 2023/2024 publication cases. Preserve the 46 historical datasets,
  1,148 body cells and 15 numeric notes; internal deduplication of shared evidence
  must not deduplicate published financial occurrences.

Run: `uv run pytest tests/bronze tests/integration/test_historical_vintages.py -q`

### Task 4 execution evidence

Task 4 execution evidence (2026-10-14): ANZ 2024 migrated to reviewed
definitions, physical readers and the thin capture entrypoint. Independent source
goldens remain unchanged. Source-owner RED was the expected v3/v4 mismatch;
`/tmp/opencode/anz2024-task4/red.log`. Source/adjacent-vintage GREEN: **2 passed**;
`/tmp/opencode/anz2024-task4/green.log`. Parent joint-vintage publication: **1 passed**;
`/tmp/opencode/metadata-task4-anz-joint-green.log`. Both vintages retain 125 cells,
their original IDs, separate catalogue mappings and bundle-qualified contexts. The
existing vintage test now distinguishes catalogue mapping references from additional
context provenance (`reference_kind`); the latter can reuse local revision names.
The same test checks both persisted bundle owners, preserving its collision coverage.

The pre-modern-migration example retained **36 CR6 / 33 CR9 rows** and eight numeric
frames at `/tmp/opencode/cr9-four-bank-t_lygdja/`, with actual v2 Bronze and diagnostic
relation readback. Log: `/tmp/opencode/metadata-checkpoint-b-modern-baseline.log`.
These artifacts are a compatibility baseline, not generated source expectations.

CBA 2023/2024 now use the same declaration/physical/thin-entrypoint split. They retain
129 and 131 cells respectively, including the June-only LGD overlay, source-specific
scalars and restatement/timing scopes. Independent golden JSON is unchanged. Both
source tests first failed at v3/v4; source plus joint-vintage GREEN: **3 passed**,
`/tmp/opencode/cba-task4-historical-green.log`. Parent's first combined historical
run also passed both CBA sources and their persisted vintage case; that run remains
RED for Westpac's declared numeric `N/A` until the shared capture parser honours
declared missingness. Log: `/tmp/opencode/metadata-task4-joint-first.log`.

NAB 2023/2024 migrated with **16 datasets and 180 cells**, retaining main/RBNZ
population qualifications, March 2023's undrawn restatement and each vintage's
distinct cohort/timing declarations. Unchanged independent goldens own source
fidelity. RED: `/tmp/opencode/nab-task4-red.log` (both producers still v3).
Source and joint-vintage GREEN: **3 passed**;
`/tmp/opencode/nab-task4-historical-green.log`. Scoped Ruff and diff checks passed.

The combined historical owner/joint-publication run now passes **12 tests**:
`/tmp/opencode/metadata-task4-joint-green.log`. Westpac's source tests reproduced
the shared parser's numeric `N/A` failure after their v3/v4 RED; its declared
missingness is now honoured before Decimal conversion. Source tests retain all
237 FY23 and 236 FY24 cells, original tokens, hidden-text selection, floor-transition
and note/body distinctions. Independent golden JSON remains unchanged.

Early ordinary `examples/historical_mortgages.py` execution succeeded at
`/tmp/opencode/historical-mortgages-e5tbazuw/`; log
`/tmp/opencode/metadata-checkpoint-b-historical-early.log`. All eight historical
reports are v4 and retain **46 datasets, 1,148 body cells and 15 numeric notes**.
Including the existing explicit Westpac 2025 view, the persisted/reconstructed
example has **48 tables and 1,343 cells**, nine CR6 rows and eight CR9 rows. This is
early Task 4 evidence; checkpoint B will rerun the examples after Tasks 5–6 finish.

## Task 5 — Existing CR6/CR9 outputs become projections of resolved captures

**Files:** Create `domains/cr6/projection.py`, `domains/cr9/projection.py`; refactor
`domains/source_tables/legacy.py`, `domains/cr6/{pipeline,metadata,reconstruction}.py`,
`domains/cr9/{pipeline,metadata,reconstruction}.py`, `operations.py` and `workflow.py`.
Extend `tests/silver/test_source_table_legacy.py`, existing CR6/CR9 conformance tests
and `tests/integration/test_cr9_workflow.py` / `test_cr6_tables.py` as their boundaries require.

**Consumes:** Resolved source output plus explicit `DomainFieldBinding` records.
**Produces:** `project_cr6` / `project_cr9` and preserved `.cr6` / `.cr9` outputs.

- [x] Author projection regressions before refactoring: NAB arrangement counts versus
  amounts; CR9 lexical ratings/blank positions; partial field timing; explicit
  relationships including within-row subset endpoints. Existing bank goldens supply
  independent expectations, not a self-comparison between two new projections.
- [x] Retain representative old-format inputs before migrating their producers. Keep
  the independently authored v1 fixture and explicit v2/v3 transport fixtures. Existing
  saved files must be readable without source modules or reconstructed fake locators.
- [x] Adapt old typed captures into source occurrences with original record/field
  addresses. Resolve through the shared owner, retaining old CR6 observation-date and
  CR9 partial-time policies. Missing old capture declarations remain explicitly unknown.
- [x] Project resolved numeric values, factors, attributes, timing and evidence into
  named CR6/CR9 relations using native expressions. Projection functions receive no
  catalogue and cannot perform another interpretation pass. Preserve source record
  IDs and public frame keys; never union domain views as extra exposure occurrences.
- [x] Keep ordinary legacy selections' existing numeric views and the explicit legacy
  source-view call. New v4 source captures can expose source structure and their declared
  domain projections; historical captures without domain bindings do not acquire CR6/CR9.
- [x] Run retained-format, projection and reconstruction cases to GREEN; retire the
  redundant old resolution path after its callers use the shared owner. Commit.

```python
# Projection consumes resolved data, not catalogue definitions or a PDF.
cr6 = project_cr6(source_output, domain_bindings)
cr9 = project_cr9(source_output, domain_bindings)
# Existing public outputs remain named, with their current typed rows and metadata.
assert cr9.observations.filter(ma.col("source_record_id") == "band-1").count_rows() == 1
```

Run: `uv run pytest tests/silver tests/catalogue tests/integration/test_cr6_tables.py tests/integration/test_cr9_workflow.py -q`

## Task 6 — Migrate the four modern sources and preserve public examples

**Files:** Split each `extractions/au/{cba/2025-06-30,westpac/2025-09-30,nab/2025-09-30,anz/2025-09-30}/aps330/extract.py`
into the same declaration/physical-operation/thin-entrypoint pattern. Update its
existing golden test and any changed source-review references; update `examples/cba_extraction.py`,
`examples/four_bank_cr9.py`, `examples/four_bank_research.py` and relevant fixtures.

**Consumes:** Complete shared capture/resolution and domain projections.
**Produces:** All twelve current source entrypoints on the accepted metadata-owned path.

- [x] Per bank, pin existing independent CR6/CR9 expectations and record RED for the
  new path. Separate retained-format fixtures from new capture fixtures so old decoder
  evidence is not lost when `extract.py` begins producing v4.
- [x] Declare actual published source content plus explicit domain field/record bindings.
  Bind each field's units, count basis, qualifiers and temporal roles from its source.
  Preserve lexical ratings and cells missing in the source; do not synthesize numeric
  values to fill optional domain projection slots.
- [x] Move only physical mechanics to source-local operations; use shared metadata
  types/readers already proven. No bank/year condition enters shared conformance.
- [x] Run the per-bank source and conformance cases to GREEN. Modern four-bank proof
  must retain 36 CR6 rows, 33 CR9 rows and the existing eight numeric frame identities.
  Update example documentation where fresh bundle internals are now source-shaped;
  retained legacy dataset types remain readable unchanged.
- [x] Commit each coherent bank migration; present checkpoint B after all four pass.

Run: `uv run pytest tests/bronze tests/silver/test_cr9_banks.py tests/integration/test_cr9_workflow.py -q`

**Checkpoint B:** inspect a modern domain output beside its source occurrences and
mapping provenance. Demonstrate that shared definitions drive both, with no second
bank-specific financial interpretation owner.

### Early modern integration evidence — 2026-10-14

All four modern source goldens passed through v4 (**9 tests**), retaining **729 source
cells: 663 numeric positions and 66 lexical rating positions**. Original golden JSON
is unchanged. Log: `/tmp/opencode/metadata-task6-four-bank-iteration.log`.
The first ordinary modern example passed with **36 CR6 rows, 33 CR9 rows and eight
numeric frames**; root `/tmp/opencode/cr9-four-bank-o6ce8c0e/`, log
`/tmp/opencode/metadata-checkpoint-b-modern-first.log`.

Diagnostic comparison against the pre-migration retained run confirms all eight
frames' identities, labels, ordering and values. Arithmetic reconstruction may expose
additional trailing Decimal scale from retained conformed factors; persisted domain
measure types retain their contracts. Log:
`/tmp/opencode/metadata-checkpoint-b-frame-comparison-first.log`.

The same comparison exposed two in-repo metadata regressions, assigned to their
owners before final verification: five missing Westpac default-definition cell
qualifiers, and a CR9 per-column evidence fallback replacing an explicitly null band
column. All old catalogue mappings, semantic assertions and evidence references remain
present when comparing without ordinal positions; v4 adds declared context provenance.
Diagnostic logs: `/tmp/opencode/metadata-checkpoint-b-modern-comparison-first.log`
and `/tmp/opencode/metadata-checkpoint-b-modern-semantic-delta.log`. These early
artifacts are not the final checkpoint B deliverable.

### Checkpoint B execution record — 2026-10-14

Tasks 4–6 are complete across **all twelve sources**. No source scope or acceptance
requirement was cut. All independent source golden JSON files remain unchanged.
The shared owner resolves source occurrences once; catalogue-free domain projections
consume those results. Existing standalone domain pipelines delegate to that owner.
Actual retained v2 inputs for all four modern banks and CBA's v3 input now live in
`tests/fixtures/retained/`, independent of the migrated producers; the independently
authored v1 fixture remains. The accepted checkpoint-A v4 file also reloads unchanged
(four tables, 125 cells, no invented domain bindings).
The retained v2/v3 fixture payloads were captured from pre-migration extractor blobs
before replacing their producers; they are transport inputs, not regenerated goldens.

| Primary test owner | Distinct risk and RED | GREEN evidence |
|---|---|---|
| Source goldens | Each migrated producer initially returned v2/v3; source fragments, full metadata and all values remain checked against independent expectations | Historical owner/joint run: 12 passed; modern source run: 9 passed; full Bronze suite passed |
| Shared occurrence resolution | Retained-v3 complete measurement dates initially failed effective selection; partial and absent dates stay unknown | `/tmp/opencode/metadata-task5-v3-date-red.log`; final focused run covers all three cases and original CR6/CR9 policies |
| Domain projections | 12 existing numerical/semantic cases failed at the missing catalogue-free APIs; additional relationship regressions exposed altered IDs, opaque-cell endpoint loss and a nullable band-column fallback | `/tmp/opencode/metadata-task5-projection-red.log`, `/tmp/opencode/metadata-task5-relationship-red.log`; final focused **145 passed**, `/tmp/opencode/metadata-task5-focused-green.log` |
| Resolved-input projection boundary | Edited resolved amounts, counts above 2**53 and factors must be consumed rather than recalculated | `/tmp/opencode/metadata-task5-resolved-input-proof.log` |
| Retained transport and persisted reconstruction | Frozen v1/v2/v3 inputs, old v4 defaults, explicit domain bindings/missing tokens and real publication/readback | Parent source-transport run **6 passed**, `/tmp/opencode/metadata-checkpoint-b-source-transport.log`; old-v4 readback `/tmp/opencode/metadata-checkpoint-b-accepted-v4-readback.log` |

The numeric `N/A` repair uses the source-owned `CellBinding.missing_tokens` tuple;
`missing_reason` remains a fallback and does not hide present numbers. The Westpac
default-row qualification regression failed directly at its source owner, then passed
after explicitly binding the qualifier to its numeric cells:
`/tmp/opencode/metadata-task6-westpac-qualifier-red.log` and
`/tmp/opencode/metadata-task6-westpac-qualifier-green.log`. Whole-band evidence
selection preserves an explicitly null source column. No runtime validators, gates,
bank-specific shared interpretation or upstream workaround were added.

Final required verification:

- `uv run pytest -q`: **200 passed**, 7,660 dependency warnings, **481.88 seconds**;
  `/tmp/opencode/metadata-checkpoint-b-full-tests.log`.
- `uv run ruff check src tests examples extractions`: passed;
  `/tmp/opencode/metadata-checkpoint-b-ruff.log`.
- `git diff --check`: passed; `/tmp/opencode/metadata-checkpoint-b-diff-check.log`.
- Changed-document relative file links checked against the checkout.

Pre-review retained examples (superseded for source fidelity by the repairs below):

- Modern root: `/tmp/opencode/cr9-four-bank-7nr50qvc/`.
  PDF → v4 Bronze → staging/master → **36 CR6 / 33 CR9 rows**, eight numeric frame
  identities and **729 source cells** (663 numeric positions, 66 lexical ratings).
  Log: `/tmp/opencode/metadata-checkpoint-b-modern-final.log`.
- Historical root: `/tmp/opencode/historical-mortgages-w9k_ayz1/`.
  All eight historical reports retain **46 datasets, 1,148 body cells and 15 notes**.
  Including the explicit Westpac 2025 view: **48 tables / 1,343 cells**.
  Log: `/tmp/opencode/metadata-checkpoint-b-historical-final.log`.
- Fresh-process saved-only master:
  `/tmp/opencode/cr9-four-bank-7nr50qvc/saved-only/master.duckdb`.
  All four retained v4 bundles reconform with no PDF or authoring directory in the
  retained project root, preserving 36/33 rows, eight frames, 729 cells and all eight
  occurrence kinds. The proof prints a CBA EAD source meaning beside its domain
  amount and mapping provenance; both are **281,508,000,000**.
  Log: `/tmp/opencode/metadata-checkpoint-b-saved-only-final.log`.

Reproduce the saved-only proof:

```bash
uv run python /tmp/opencode/metadata-checkpoint-b-saved-only.py /tmp/opencode/cr9-four-bank-7nr50qvc
```

Final diagnostic comparison with the retained pre-migration run shows identical
CR6/CR9 observations, contexts, relationship IDs and temporal relations. V4 adds
explicit source context/row-qualification provenance; no old mapping/evidence assertion
is lost. Fixed-decimal factors can have additional trailing scale, with unchanged
numeric values. Log: `/tmp/opencode/metadata-checkpoint-b-modern-comparison-final.log`.
The pre-review parity checks passed for the compared numeric fields' payload,
missingness, address and physical evidence; they did not catch the lexical missingness
or source-frame ordering defects found in independent review below. All original
mapping/assertion/evidence entries remain present, ignoring provenance ordinals.
All eight reconstructed numeric
frames preserve labels, order and values. Log:
`/tmp/opencode/metadata-checkpoint-b-final-parity.log`.

Local implementation commits:

- `9e01ccd` — checkpoint A acceptance and ANZ 2024 migration.
- `c96af76` — CBA 2023/2024 migration.
- `0feee2e` — NAB 2023/2024 migration.
- `efb1a55` — shared resolution/projections, retained fixtures and Westpac historical capture.
- `41a440c` — four modern migrations, source test support and public examples.

The implementation handoff identified no unresolved issue; independent review then
found the two in-repo source-fidelity defects recorded below. Checkpoint B acceptance
is pending; Task 7 remains unexecuted.

### Checkpoint B complexity cuts — 2026-10-14

The integrating agent accepted these scope-preserving cuts under the approved plan
before correctness triage. Before editing, Python AST comparison confirmed
all four modern `window` implementations identical and both CBA historical copies
of `region`, `line`, `rows` and `bands` identical. They now share their unchanged
implementations in the existing `extraction/physical.py` owner. The CBA readers have
unambiguous names: `cropped_text_region`, `line_match_groups`, `anchored_prefix_rows`
and `line_band_matches`. Each dated CBA module retains its original operation keys
in `OPERATIONS`; each modern module imports `window` directly.

| Cut | Affected requirement | Retained means of satisfying it |
|---|---|---|
| Four identical modern windows → one shared function | Complete four-bank numeric/lexical capture, headers, missing positions and evidence | Function AST unchanged; source-local grid selection, tolerances, multiline choices, geometry and evidence assembly unchanged; all four existing source goldens pass |
| Two identical CBA historical reader sets → four shared functions | Both historical vintages' full cells, notes, qualifiers, temporal scopes and identities | Function ASTs unchanged except names; dated operation keys and independent declarations unchanged; both existing source goldens pass |

No acceptance scope, test, source definition or qualifier was removed. No framework,
cross-dated import or test seam was added. Production diff: **115 additions / 219
deletions**, net **104 lines removed**. AST checks also verified the existing shared
paragraph reader and every remaining modern source-local function are unchanged.

- AST before: `/tmp/opencode/metadata-checkpoint-b-cuts-ast-before.log`.
- AST after: `/tmp/opencode/metadata-checkpoint-b-cuts-ast-after.log`.
- Affected existing source goldens: **11 passed**, 21.13 seconds;
  `/tmp/opencode/metadata-checkpoint-b-cuts-goldens.log`.
- Modern example: **36 CR6 / 33 CR9 rows**, eight numeric frames;
  `/tmp/opencode/cr9-four-bank-ua5crtx6/`, log
  `/tmp/opencode/metadata-checkpoint-b-cuts-modern.log`.
- Historical example: **48 tables / 1,343 cells / 15 notes**, retaining the complete
  historical 46-dataset / 1,148-body-cell scope plus explicit modern comparison;
  `/tmp/opencode/historical-mortgages-k4hhft37/`, log
  `/tmp/opencode/metadata-checkpoint-b-cuts-historical.log`.
- All **8 modern and 74 historical readback parquet files** match the preceding
  checkpoint outputs in content and dtype, with source-frame row order preserved;
  `/tmp/opencode/metadata-checkpoint-b-cuts-output-parity.log`.
- Ruff and diff checks passed; `/tmp/opencode/metadata-checkpoint-b-cuts-ruff.log`
  and `/tmp/opencode/metadata-checkpoint-b-cuts-diff-check.log`.

Parent's independent pre-cut modern example also passed at
`/tmp/opencode/cr9-four-bank-19fld1e4/`; log
`/tmp/opencode/metadata-checkpoint-b-parent-example.log`. As requested, the full suite
is deferred until correctness findings are addressed. This milestone remains local
and does not advance beyond checkpoint B.

### Checkpoint B correctness repairs — 2026-10-14

Independent review found two in-repo defects, both repaired in `8d7930f`:

- All four modern sources gave rating and numeric columns overlapping positions,
  interleaving their source-shaped CR9 frames. Numeric positions now follow both
  rating columns; source-specific numeric order remains intact, including NAB's
  current-before-previous counts. NAB's separately published rating evidence remains
  sourced from its own page.
- Westpac's fourteen printed lexical `N/A` ratings lost `not_applicable`. The declared
  tag is restored while retaining those tokens and the two distinct default-row
  `blank_unresolved` ratings.

The independent regressions failed first: four ordering cases and one missingness
case. The repaired source goldens and persisted four-bank source-frame cases passed
**17 tests**. Logs: `/tmp/opencode/checkpoint-b-declarations-red-order.log`,
`/tmp/opencode/checkpoint-b-declarations-red-missingness.log` and
`/tmp/opencode/checkpoint-b-declarations-green-final.log`.

Earlier checkpoint-B artifacts are historical evidence only for source-shaped column
ordering and lexical missingness; numeric-domain frames excluded the rating columns
and therefore could not establish those requirements. Independent re-review closed
both findings at `8d7930f`, with **5 focused cases passing**. Fresh captures match
retained v2 source views for values, tokens, missingness, row/field addresses and
column ordering; NAB's PDF46 rating evidence and PDF61 count ordering remain intact.
No upstream defect was identified.

Corrected example roots: `/tmp/opencode/cr9-four-bank-78wd0qol/` and
`/tmp/opencode/historical-mortgages-x5dufviz/`. Both complete paths passed, retaining
36 CR6 / 33 CR9 rows and eight numeric frames, and 48 historical/comparison tables /
1,343 source cells including 15 numeric notes. Logs:
`/tmp/opencode/metadata-checkpoint-b-repaired-modern.log` and
`/tmp/opencode/metadata-checkpoint-b-repaired-historical.log`.

Final post-repair verification: **204 passed**, 8,260 dependency warnings, in
546.36 seconds; `/tmp/opencode/metadata-checkpoint-b-repaired-full-tests.log`.
Ruff and diff checks passed. Fresh-process saved-only reconstruction also passed
from `/tmp/opencode/cr9-four-bank-78wd0qol/`, retaining 36/33 rows, eight numeric
frames and 729 source cells without a PDF or authoring directory in that root.
Log: `/tmp/opencode/metadata-checkpoint-b-repaired-saved-only.log`.

Correctness and complexity reviews are closed with no open findings. Checkpoint B
is ready for researcher acceptance in draft PR #18; Task 7 remains unstarted.

## Task 7 — Whole-path evidence, retirement and delivery

**Files:** Extend existing `tests/integration/test_master_consolidation.py`,
`test_source_table_workflow.py`, `test_historical_vintages.py` and transport cases only
for their distinct new risks. Update `examples/historical_mortgages.py`, `README.md`,
`docs/architecture.md`, source reviews and `AGENTS.md` to implemented evidence.

- [ ] Before the final code changes, extend the existing master test to include new
  occurrence/context tables. Prove shared bundle comments remain reachable after
  staging files are removed, and fewer-input rebuilds remove every dependent output.
  Keep its persisted-value mutation proof; do not replace it with Bronze self-comparison.
- [ ] Run that focused RED, implement missing inventory/readback/reconstruction work,
  then GREEN. New all-kind outputs use the same atomic write/read/master associations.
- [ ] Finish retirement of duplicated metadata/semantic assembly; keep only necessary
  old wire decoders and address adapters. Do not delete retained PDFs, Bronze or
  independently authored expectations. Do not promote the spike.
- [ ] Run the full historical example on fresh roots: 48 source datasets / 1,343
  source cells, including lexical ratings and published missing positions, remain
  the comparison baseline with the explicit Westpac 2025 views. Additional structural
  and comment occurrences are outside that cell baseline.
- [ ] Run the modern example, then the complete suite, Ruff and diff checks. Inspect
  example output roots/run names first. Record commands, retained artifacts and results.
- [ ] Run independent correctness and complexity reviews. Apply complexity cuts first,
  repair in-repo findings, and reproduce/track any required upstream defects without
  an unapproved workaround. An upstream-dependent requirement blocks delivery until
  repaired and verified; do not label it complete with follow-ups.
- [ ] Open/update one implementation PR to `develop`, with code and documentation
  together. Offer local checkout synchronisation after authorised merge.

```bash
uv run python examples/historical_mortgages.py
uv run python examples/four_bank_cr9.py
uv run pytest
uv run ruff check src tests examples extractions
git diff --check
```

## Execution and approval boundary

Independent correctness and complexity reviews completed on 2026-10-13. Complexity
cuts removed mandatory source-review rewrites and rigid module/collection machinery.
Both correctness findings were in-repo plan fixes: the saved-only proof now exercises
retained occurrence-targeted catalogue loading, and the final cell baseline explicitly
includes lexical and missing positions. No upstream-dependent blocker was identified.

Recommended mode is `executing-plans`: Tasks 1–3 form the first batch with early real
persistence, Task 4 is historical migration, Tasks 5–6 deliver modern projections and
source migration, and Task 7 closes the complete scope. Use checkpoints A/B and final
independent review, rather than fresh implementation agents for each small edit.

The researcher approved the production adapters, typed snapshot and all-kind
persistence details on 2026-10-13. If they require changing the accepted separation, stop and review
the design instead of expanding the implementation around a failing shape. Do not
start coding on the basis of the spike approval alone.

## Checkpoint A execution record — 2026-10-13

Checkpoint A was accepted by the researcher on **2026-10-14**, following independent
verification of the exposure-heading repair and the 195-test full suite. Continuation
of Tasks 4–6 is authorised in the existing worktree on
`feature/metadata-driven-extraction`, starting at `881bee2`. Draft PR #18 targets
`develop`. Further commits remain local pending parent review; Task 7 remains behind
checkpoint B acceptance.

Approval: researcher authorised the complete plan, PR #17 merge/synchronisation and
the separate worktree. Execution uses `executing-plans` with TDD/test-audit, seeded
from `develop` `2ef55de` on `feature/metadata-driven-extraction`. No spike code was
read, copied or used as the production base. Tasks 4–7 have not been executed.

### Primary-owner evidence

| Owner | RED evidence | GREEN evidence |
|---|---|---|
| Retained transport | New captured variant absent; later retained semantic-definition contents absent | Focused transport/storage run: 37 passed; typed payload cases extended to v4 while old v3 checkpoint-default case remains |
| Occurrence resolver | Nine cases failed at the missing resolver; role-specific concept initially unresolved; explicitly bound dated mapping initially bypassed missing measurement time | Context conflicts/provisional support, explicit overrides, whole-mapping supersession, selected definition contents and independent conversion exercised at the resolver owner |
| ANZ independent source golden | Existing source returned v3; later published field had no captured header fragment | All 125 independently specified values, structure, qualifications and field timing pass through v4; original golden JSON unchanged |
| Persisted workflow | Existing source returned v3; initial non-cell evidence provenance absent; initial readback included unrelated bundle comments | Shared comments, matrix pre/post headers/NZ blank, reachable metadata, context references and retained comment override survive DuckDB publication |
| Existing compatibility owners | Historical-vintage provenance query failed after cell observation IDs changed | Existing cell observation IDs restored; all-kind owner columns supply new addressing |
| Ordinary fresh-process example | Import-order cycle exposed outside pytest | CapturedBundle moved to the declaration owner, avoiding eager catalogue/source import cycles; actual example and independent saved-only process succeed |

The combined focused command covering catalogue, historical meanings, ANZ goldens,
transport/storage and source workflows passed **110 tests** before final compatibility
and import-order refinements. The first full-suite invocation exceeded its 120-second
command limit; its early failures led to the retained cell-ID repair. Full-suite final
results: **195 passed**, 7,874 existing dependency warnings, in 203.33 seconds.
The final focused rerun after all code changes passed **26 tests** (56.46 seconds):
new resolver/transport cases, old source transport, four-bank vintage publication,
ANZ source golden and source-table workflow. Its log is
`/tmp/opencode/metadata-checkpoint-a-focused-tests.log`.

Final checks: `uv run ruff check src tests examples extractions` passed;
`git diff --check` passed; all relative links in changed Markdown files resolve.
The batch is committed as one checkpoint-A implementation milestone rather than
separate task commits, retaining the recorded red/green evidence above.

### Retained executable artifacts

- Example: `uv run python examples/anz_metadata_capture.py`.
- Initial proof root (superseded by the heading repair below): `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/`.
- v4 snapshot: `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/bronze/au/anz/2023-09-30/aps330/metadata-proof/bundle.json`.
- Retained refinement release: `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/catalogue/releases/anz-checkpoint-refinement.json`.
- Ordinary readback: `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/anz.duckdb`.
- Independent fresh-process readback: `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/fresh-process.duckdb`.
- Logs: `/tmp/opencode/metadata-checkpoint-a-example.log`,
  `/tmp/opencode/metadata-checkpoint-a-saved-only.log`,
  `/tmp/opencode/metadata-checkpoint-a-full-tests.log`.

The copied PDF and source-authoring directory were deleted before reconformance.
The fresh process used the retained proof directory as its project root: **125 cells,
seven shared/context definitions, all eight occurrence kinds, four reconstructed
tables, EAD ratio 1.01000000**, and the retained interpretation
`wholesale review; mortgage applicability unresolved`. The original project PDF and
retained project data were not modified.

Implementation ownership follows the plan, with `CapturedBundle` in
`extraction/definitions.py` to avoid the observed import cycle. The generic storage
inventory already carries the four new source relations, so no duplicated Silver,
manifest or workflow table list was added. Source-table numeric meanings remain a
cell projection of resolved captures. Existing source-table qualifications are
materialised compatibility views of singly captured passages.

No required upstream defect has been reproduced. Existing Mountainash declaration
warnings and Ibis/Polars deprecation warnings remain visible. Independent reviews
are closed following the repair below; checkpoint A awaits researcher acceptance.

### Approved complexity cut

Before correctness triage, removed the redundant `SELECTED_DEFINITIONS` alias and
capture argument. `capture` now consumes `definition.snapshot` directly; declaration
and physical-operation loading remain separate. No alternate mode was introduced.
The ANZ independent golden, saved-only refinement workflow and snapshot transport
tests passed (**3 passed**); focused Ruff and diff checks passed. The parent also
verified the example at `/tmp/opencode/anz-metadata-checkpoint-a-8w4smvvg/` and recorded
the `develop` baseline as **181 passed**. The subsequent correctness finding and
its closure are recorded below.

### Correctness repair: exposure heading selection

The independent review reproduced an in-repo sourcing error on PDF pp.52–54:
the first `Exposure at Default` substring occurs in the table title. The paragraph
reader therefore captured `Exposure at Default subject to Internal Ratings Based
(IRB) approach by risk grade` for the exposure field/block, also publishing that
incorrect block label in `source_axes`. The 125 financial values were unaffected.

The existing independent source test now checks the field and block fragments and
block label against the literal standalone heading on all three panels. RED:
`uv run pytest tests/bronze/au/anz/2023-09-30 -q` failed with the title suffix rather
than `Exposure at Default`; log `/tmp/opencode/metadata-heading-red.log`.
The declaration now passes `after=label` to the existing paragraph reader,
restricting heading selection to content after the panel date. No reader framework
or alternate mode was added. The source golden and saved-only workflow passed
(**2 tests**); log `/tmp/opencode/metadata-heading-green.log`.

All earlier checkpoint artifacts, including the parent's
`/tmp/opencode/anz-metadata-checkpoint-a-8w4smvvg/`, are superseded for source-label
fidelity. They retain the incorrect exposure block labels and remain historical
evidence only. Corrected retained artifacts:

- Root: `/tmp/opencode/anz-metadata-checkpoint-a-4aojvuza/`.
- Snapshot: `/tmp/opencode/anz-metadata-checkpoint-a-4aojvuza/bronze/au/anz/2023-09-30/aps330/metadata-proof/bundle.json`.
- Example database: `/tmp/opencode/anz-metadata-checkpoint-a-4aojvuza/anz.duckdb`.
- Fresh-process saved-only database: `/tmp/opencode/anz-metadata-checkpoint-a-4aojvuza/fresh-process.duckdb`.
- Example log: `/tmp/opencode/metadata-heading-example.log`.
- Saved-only readback log: `/tmp/opencode/metadata-heading-saved-only.log`.
- Full-suite log: `/tmp/opencode/metadata-heading-full-tests.log`.

The fresh process used the retained root after its copied PDF and authoring directory
had been deleted. It asserted that all three persisted exposure blocks and all six
field/block fragments equal exactly `Exposure at Default`, and reconstructed four
tables with 125 financial cells, seven contexts, all eight occurrence kinds and the
retained comment refinement. No upstream finding or further source migration is involved.

Final verification after the heading repair: **195 passed**, 7,874 dependency
warnings, in 204.17 seconds. `uv run ruff check src tests examples extractions`
and `git diff --check` passed. The regression and full-suite evidence preserve the
entire checkpoint scope; the earlier complexity cut removed only duplicate argument
plumbing, with selected definition contents still supplied by the retained snapshot.

Independent correctness re-review confirmed the repair across all three panels,
including the captured field/block fragments and persisted labels. No findings remain
open. Tasks 1–3 are complete for checkpoint A; Tasks 4–7 remain unstarted pending
researcher acceptance of this checkpoint. The implementation PR remains draft for
the complete approved migration, rather than treating this checkpoint as its delivery
boundary.
