# Metadata-driven extraction implementation plan

> **For agentic workers:** Use `executing-plans` for batched delivery with the
> checkpoints below and `test-driven-development` for approved production work.
> Use `test-audit` when authoring/changing tests. Tasks are behaviour-sized, not
> micro-steps. Independent correctness and complexity reviews precede delivery.

Status: **APPROVED — Tasks 1–3 complete; checkpoint A awaiting review.** The researcher approved the plan,
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

- [ ] For each source, extend the existing independent golden test to enter the new
  declared path and record RED. Capture all existing cells, structural evidence and
  applicable qualifiers; do not regenerate expected fixtures from new declarations.
- [ ] Re-express metadata as explicit bindings; retain source-local physical algorithms
  where required. Share a reviewed definition by reference, not a previous dated extractor.
  Remove superseded semantic construction from each migrated `extract.py`.
- [ ] Run that source and its adjacent vintage tests to GREEN. Commit per coherent
  bank migration, keeping one implementation PR.
- [ ] Run the joint 2023/2024 publication cases. Preserve the 46 historical datasets,
  1,148 body cells and 15 numeric notes; internal deduplication of shared evidence
  must not deduplicate published financial occurrences.

Run: `uv run pytest tests/bronze tests/integration/test_historical_vintages.py -q`

## Task 5 — Existing CR6/CR9 outputs become projections of resolved captures

**Files:** Create `domains/cr6/projection.py`, `domains/cr9/projection.py`; refactor
`domains/source_tables/legacy.py`, `domains/cr6/{pipeline,metadata,reconstruction}.py`,
`domains/cr9/{pipeline,metadata,reconstruction}.py`, `operations.py` and `workflow.py`.
Extend `tests/silver/test_source_table_legacy.py`, existing CR6/CR9 conformance tests
and `tests/integration/test_cr9_workflow.py` / `test_cr6_tables.py` as their boundaries require.

**Consumes:** Resolved source output plus explicit `DomainFieldBinding` records.
**Produces:** `project_cr6` / `project_cr9` and preserved `.cr6` / `.cr9` outputs.

- [ ] Author projection regressions before refactoring: NAB arrangement counts versus
  amounts; CR9 lexical ratings/blank positions; partial field timing; explicit
  relationships including within-row subset endpoints. Existing bank goldens supply
  independent expectations, not a self-comparison between two new projections.
- [ ] Retain representative old-format inputs before migrating their producers. Keep
  the independently authored v1 fixture and explicit v2/v3 transport fixtures. Existing
  saved files must be readable without source modules or reconstructed fake locators.
- [ ] Adapt old typed captures into source occurrences with original record/field
  addresses. Resolve through the shared owner, retaining old CR6 observation-date and
  CR9 partial-time policies. Missing old capture declarations remain explicitly unknown.
- [ ] Project resolved numeric values, factors, attributes, timing and evidence into
  named CR6/CR9 relations using native expressions. Projection functions receive no
  catalogue and cannot perform another interpretation pass. Preserve source record
  IDs and public frame keys; never union domain views as extra exposure occurrences.
- [ ] Keep ordinary legacy selections' existing numeric views and the explicit legacy
  source-view call. New v4 source captures can expose source structure and their declared
  domain projections; historical captures without domain bindings do not acquire CR6/CR9.
- [ ] Run retained-format, projection and reconstruction cases to GREEN; retire the
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

- [ ] Per bank, pin existing independent CR6/CR9 expectations and record RED for the
  new path. Separate retained-format fixtures from new capture fixtures so old decoder
  evidence is not lost when `extract.py` begins producing v4.
- [ ] Declare actual published source content plus explicit domain field/record bindings.
  Bind each field's units, count basis, qualifiers and temporal roles from its source.
  Preserve lexical ratings and cells missing in the source; do not synthesize numeric
  values to fill optional domain projection slots.
- [ ] Move only physical mechanics to source-local operations; use shared metadata
  types/readers already proven. No bank/year condition enters shared conformance.
- [ ] Run the per-bank source and conformance cases to GREEN. Modern four-bank proof
  must retain 36 CR6 rows, 33 CR9 rows and the existing eight numeric frame identities.
  Update example documentation where fresh bundle internals are now source-shaped;
  retained legacy dataset types remain readable unchanged.
- [ ] Commit each coherent bank migration; present checkpoint B after all four pass.

Run: `uv run pytest tests/bronze tests/silver/test_cr9_banks.py tests/integration/test_cr9_workflow.py -q`

**Checkpoint B:** inspect a modern domain output beside its source occurrences and
mapping provenance. Demonstrate that shared definitions drive both, with no second
bank-specific financial interpretation owner.

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
- Current proof root: `/tmp/opencode/anz-metadata-checkpoint-a-o0_f0yvy/`.
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
warnings and Ibis/Polars deprecation warnings remain visible. Checkpoint A awaits
the parent's independent reviews and researcher acceptance; nothing has been pushed.

### Approved complexity cut

Before correctness triage, removed the redundant `SELECTED_DEFINITIONS` alias and
capture argument. `capture` now consumes `definition.snapshot` directly; declaration
and physical-operation loading remain separate. No alternate mode was introduced.
The ANZ independent golden, saved-only refinement workflow and snapshot transport
tests passed (**3 passed**); focused Ruff and diff checks passed. The parent also
verified the example at `/tmp/opencode/anz-metadata-checkpoint-a-8w4smvvg/` and recorded
the `develop` baseline as **181 passed**. Correctness review remains pending.
