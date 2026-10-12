# CR9 capture and shared interfaces implementation plan

> **For agentic workers:** use `executing-plans` in batches with the researcher
> checkpoint after task 3. Use `test-driven-development` and `test-audit` for real
> implementation. Do not reuse the disposable spike as the implementation branch.

**Status:** COMPLETE AND MERGED — all five tasks implemented and verified. PRs #8
and #9 merged into `develop`; implementation merge commit: `32e5f6a`.
The researcher approved the Westpac checkpoint before tasks 4–5. Implementation
[lessons](../../../00.ideation/2026-10-12-cr9-implementation-lessons.md) are retained
for future backlog and design decisions.

**Goal:** Capture the selected four-bank mortgage CR9 disclosures with field-level
meaning/time metadata through retained mixed-domain Bronze, staging and master.

**Architecture:** Keep typed CR6/CR9 source rows and named outputs. Domain adapters
select applicable meanings; a shared composer combines them. Declared tables drive
Mountainash conformance, transactional DuckDB publication and persisted reconstruction.

**Tech stack:** existing pinned Mountainash, mountainash-data/files/settings, Python
dataclasses, Decimal, pdfplumber and DuckDB. No dependency upgrade is planned.

**Spec:** [Approved refined CR9 specification](../specs/2026-10-12-cr9-domain-design.md).
PR #7 merged at `5190388`; design and disposable spike shape are approved. The
implementation plan was subsequently approved and executed, with the task-3
checkpoint approved before tasks 4–5 proceeded.

## Global constraints and execution

Execution status is recorded in the completion table below; the original task
checklists preserve the approved plan wording.

- Use the base checkout for docs; reserve a fresh `develop`-seeded worktree for coding.
  Confirm the coding branch/worktree when execution starts. Never base on spike PR #6.
- Implement field-level capture/tagging; aggregation, vintage selection and inferred
  annual rates remain bespoke analysis. Real restatement discovery is follow-up research.
- Preserve existing `cr6-v1` transport and retained output versions. New mixed bundles
  use `disclosure-v2`; an output version is separate from its wire version.
- Keep one logical source bundle per PDF. Extend existing extractors and golden sets.
- Preserve original tokens, precision, missingness, both axes, notes and external
  ratings as well as numeric values. Unknown meaning is publishable.
- Use native Mountainash relational operations, dataclass-derived declarations and
  explicit working Decimal scales. No new nested-ingress adaptation without approval.
- Validation remains separate and undefined. Do not copy constructor checks or add
  validators, analytical eligibility checks or publication gates.
- Metadata-ingress and constructor-validation refactors remain deferred. Address only
  the optional mapping-date change required by this spec, retaining CR6 behaviour.
- Baseline first: `uv sync --locked`, then the existing relevant suite. Use fresh
  temporary data roots for runs; the coding worktree does not inherit retained Bronze.
- Red → green → refactor each behaviour-sized task; run focused tests while iterating,
  commit the coherent task, and record executable evidence. No test-count target.

## Review focus and owning evidence

| Input/risk | Observable requirement | Primary owner |
|---|---|---|
| Default-row blank versus reported zero | Missingness and original token survive mixed codec | Task 1 codec/golden tests |
| Definition/mapping effective dates with no common observation date | No date restriction bypass; other supported meaning survives | Task 2 catalogue tests |
| Repeated descriptor names in separate reports | Temporal bindings stay with the correct source occurrence | Task 3 persisted metadata test |
| Field subset within a row | New-default count stays linked to default count, not an indistinguishable self-edge | Task 3 persisted metadata test |
| Smaller or empty rebuild selection | Both domains replaced; no stale CR9 rows | Task 5 master test |

These are development assertions, not runtime policies. Existing tests own established
CR6 behaviour; new tests cover new source contracts or distinct persistence risks.
Do not replay complete source goldens or shared-composer cases at each integration
boundary; integration assertions own storage, reconstruction and replacement risks.

## Task 1 — Reviewed Westpac mixed-source capture and transport

**Files:** create `src/rwa_analysis/extraction/cr9.py` and
`src/rwa_analysis/extraction/temporal.py`; modify `extraction/datasets.py`,
`extraction/codec.py`, `storage/bronze.py` and their package exports under
`src/rwa_analysis/`. Extend `extractions/au/westpac/2025-09-30/aps330/extract.py`
and its existing source review. Extend the corresponding `tests/bronze/.../golden.json`,
`golden-notes.md`, `test_extraction.py`, `tests/support/golden.py` and
`tests/integration/test_bronze_storage.py`.

**Interfaces produced:** `Cr9Dataset(id, metadata, backtesting_rows)`,
`Cr9BacktestingRow`, `Cr9Context`, `TemporalDescriptor`, `TemporalBinding` as specified;
existing `ExtractionBundle` and `BronzeStore.save/load` support both wire versions.

- [ ] Re-read Westpac pp.55–56 and relevant glossary/CR6 definitions. Independently
  author the complete selected mortgage block expectations: eight displayed bands,
  seven measure positions per row, rating labels, missing default-row cells, notes
  and field timing. Keep unsupported exact dates unresolved. Extend the existing
  source review rather than using the spike transcription as a golden.
- [ ] Add failing source and codec cases for that complete block, mixed CR6/CR9
  dispatch, partial-date/history metadata, missing cells and retained `cr6-v1` loading.
  Keep an independently authored small old-wire case so updating the extractor cannot
  silently turn every transport test into `disclosure-v2` coverage.
- [ ] Bind existing old-wire transport cases to that retained legacy fixture now,
  including tests that address `records` directly. They must not depend on a live
  CBA extractor that task 4 will change to `disclosure-v2`. Update the shared fixture
  ownership in `tests/conftest.py` as part of this transport change.
- [ ] Implement source classes and metadata composition without validation methods.
  Add explicit `disclosure-v2` codec dispatch and domain discriminators. Old decoding
  supplies empty temporal collections; explicit old encoding preserves the old wire.
  Extend the one Westpac extractor to return both datasets in the same logical bundle.
- [ ] Extend golden comparison to include new dataclass fields/collections and lexical
  ratings. Preserve CR6 expectations; do not regenerate expected data from the extractor.

Focused command:
```bash
uv run pytest tests/bronze/au/westpac/2025-09-30/aps330 tests/integration/test_bronze_storage.py tests/test_golden_comparison.py
```

Key transport assertion using an independently authored mixed input and expected
metadata (extend the existing test setup rather than a production test hook):
```python
ref = store.save(mixed_bundle, "cr9-review")
loaded = store.load(ref).bundle
assert loaded.schema_version == "disclosure-v2"
# Compare the decoded domain objects and metadata against the independent fixture.
```

- [ ] Commit: `feat: capture Westpac CR9 in versioned mixed-domain Bronze`.

## Task 2 — Shared interpretation and CR9 conformance

**Files:** modify `src/rwa_analysis/catalogue/models.py`, `resolve.py`, `load.py` only
where new declarations/release selection require it; add concrete CR9 adapter in
`src/rwa_analysis/domains/cr9/semantics.py`. Create that domain's `models.py`,
`contracts.py`, `pipeline.py`, `metadata.py`, `reconstruction.py`, `__init__.py`.
Add reviewed catalogue assets under existing `catalogue/` conventions and a new
`catalogue/releases/cr6-cr9-v1.json`. Extend `tests/catalogue/test_cr6_catalogue.py`;
create `tests/catalogue/test_cr9_catalogue.py` and `tests/silver/test_cr9_conformance.py`.

**Interfaces:** preserve CR6 `resolve_field(...)`; extract
`compose_field(catalogue, published_field, applicable_mappings, definition_applies)`
returning `FieldMeaning`. CR9's adapter builds `FieldOccurrence` and selects explicit
source-scoped mappings. `Cr9Pipeline.conform(inputs, catalogue) -> Cr9Output` uses
the spec's fifteen named relations. `reconstruct_cr9(output, bundles)` returns
bundle/dataset-keyed source-shaped numeric dataframes.

- [ ] Add failing catalogue cases for optional scope bounds/containment, independent
  mapping and definition effective-date restrictions, partial/conflicting attributes,
  and known conversion with unknown measure. Reuse existing CR6 override/supersession
  evidence rather than duplicating it for every CR9 field.
- [ ] Separate source occurrence selection from shared composition. Bounds absent
  on a mapping scope mean unrestricted on that side; CR9 mappings for this slice use
  unrestricted effective dates. A restricted mapping/definition cannot acquire
  applicability from report date by default. Preserve all existing CR6 results.
- [ ] Review source terms against existing catalogue concepts. Record source statements
  and researcher decisions separately; unresolved financial meaning stays unresolved.
  Use real release assets, not spike-local mappings. Do not invent a denominator or
  equate all borrower counts with arrangements.
- [ ] Add failing conformance cases from the task-1 source: exact rate conversion,
  nullable numeric columns, temporal roles/unknowns and row-scoped field relationships.
  Declare the full output inventory, including evidence/qualification associations.
  Domain transformations consume data and catalogue only; storage remains external.
- [ ] Implement native relation conversions/projections with explicit working scales
  on both operands. Keep source units/tokens and interpretation references in field
  metadata; counts remain integers and rates become `Decimal(16,8)` fractions.

One source-backed acceptance assertion:
```python
output = Cr9Pipeline().conform(saved_westpac_inputs, selected_catalogue)
row = output.observations.to_polars().filter(
    pl.col("source_record_id") == "band-1"
).row(0, named=True)
assert row["historical_annual_default_rate"] == Decimal("0.00060000")
assert row["defaulted_borrower_count"] == 385
```
Use the actual independently authored record identity from task 1; keep its name
consistent in the extractor, fixture and conformance output, not inferred from values.

Focused command:
```bash
uv run pytest tests/catalogue tests/silver
```
- [ ] Commit: `feat: conform CR9 with shared field interpretation and temporal metadata`.

## Task 3 — First real mixed-domain staging path and researcher checkpoint

**Files:** modify `src/rwa_analysis/operations.py`, `composition.py`, `workflow.py`,
`storage/silver.py`, `storage/manifests.py`, `storage/consolidation.py`; add shared declaration association in
`src/rwa_analysis/storage/tables.py` only for the combined inventory. Update callers
in existing organisation-workflow tests; add
`tests/integration/test_cr9_workflow.py` and `examples/westpac_cr9.py`.

**Interfaces:** `SilverCandidate` has named CR6/CR9 outputs. A concrete
`SilverOutput(cr6, cr9)` is the combined `SilverStore.read()` result. Domain pipelines
and reconstruction retain domain-specific inputs; `OrganisationSession` retains its
explicit independent stages and `run()` sequence. Absent domains produce typed empties.

- [ ] Write the failing real Westpac PDF → mixed saved Bronze → reload → conform →
  publish → read → reconstruct case. Update CR6 callers to use `read(...).cr6` without
  weakening their expected values. Add persisted metadata cases for two synthetic
  document occurrences sharing a local `history` ID, explicitly labelled synthetic,
  and the within-row new-default subset. No real restatement claim.
- [ ] Dispatch supported datasets into their domains; replace all 27 declared tables
  and publication marker in one transaction. Retain source selection and producing
  revision IDs, full temporal/evidence linkage and catalogue release selection.
  Update manifests to identify the new mixed Silver schema while retaining current
  provenance limitations. No snapshot or freshness-guard project.
- [ ] Implement combined readback before closing backend connections. Reconstruct
  from persisted values and retained source bindings, not an in-memory candidate.
  Exercise fewer-domain staging replacement so omitted CR9 is cleared.
- [ ] Migrate the existing master caller to combined read/write/reconstruction
  interfaces in this task so the checkpoint leaves ordinary CR6 master use working.
  Update its existing caller tests now; task 5 owns expanded CR9 master behaviour
  and four-bank acceptance, not repair of a temporarily broken public caller.
- [ ] Run `examples/westpac_cr9.py` using an explicitly supplied temporary data root
  and new run name. Retain the new mixed bundle and readback artifacts. Show eight
  mortgage rows, preserved CR6 output, multiple temporal roles, unknown history bounds
  and the 7-of-385 field relationship. Record actual results and any limitations.

Focused command:
```bash
uv run pytest tests/integration/test_organisation_workflow.py tests/integration/test_cr9_workflow.py tests/integration/test_cr6_tables.py tests/integration/test_master_consolidation.py
```
- [ ] Commit: `feat: publish and reconstruct mixed CR6 CR9 organisation outputs`.
- [ ] **STOP for researcher review of the real Westpac end-to-end path.** Do not
  postpone this checkpoint to finish four-bank extraction or speculative abstractions.

## Task 4 — Complete CBA, NAB and ANZ source/catalogue coverage

**Files:** the existing `extract.py` and source reviews under
`extractions/au/{cba,nab,anz}/<document-date>/aps330/`, matching
`tests/bronze/.../{golden.json,golden-notes.md,test_extraction.py}`, catalogue assets
and release selection, plus table-driven cases in the task-2 conformance owner.
Dates: CBA `2025-06-30`; NAB/ANZ `2025-09-30`.

- [ ] Independently review CBA p.60, NAB PDF pp.60–61 and referenced CR6 count definition,
  ANZ p.66 and applicable definitions. Author full mortgage-block expectations before
  extractor changes. Capture eight CBA/NAB rows, nine ANZ rows including its subtotal;
  preserve each source's column ordering, ratings, blank cells and notes.
- [ ] Extend each PDF's existing bundle/extractor; do not create CR9-only source copies.
  Explicitly tag CBA's April–March interval/year-precision history, NAB's two dated
  count columns/current weighted PD and agreement-count evidence, and ANZ's five-year
  history/exclusions/subtotal. Unknown anchors remain unknown; ask the researcher
  about uncertain canonical equivalences rather than inventing mappings.
- [ ] Extend durable mappings/release and parameterised conformance/reconstruction
  evidence. ANZ aggregate history 0.62% must become 0.0062 without averaging bands;
  NAB first-band counts must remain 198124/215531 with their own dates. Preserve all
  existing four-bank CR6 goldens and numerical results.

Focused command:
```bash
uv run pytest tests/bronze tests/catalogue tests/silver tests/integration/test_cr9_workflow.py
```
- [ ] Commit source-backed bank increments; finish with all selected blocks passing.

## Task 5 — Master replacement, complete verification and delivery

**Files:** modify `src/rwa_analysis/storage/consolidation.py`, its manifest handling,
`tests/integration/test_master_consolidation.py`, `tests/conftest.py`, existing examples
and add `examples/four_bank_cr9.py`; update `README.md`, `docs/architecture.md`,
`docs/README.md`, spec/plan status and research backlog after actual delivery evidence.

- [ ] Extend the existing master boundary tests to both named domains. Confirm that
  changed persisted staging CR9 values/temporal metadata are copied, not reconformed;
  producing revisions survive; master reconstruction works without live staging
  databases while retained source bundles/manifests remain available.
- [ ] Implement inventory-driven concat/full replacement for both domains. Prove
  smaller selections and zero selections clear prior results and retain typed tables.
  Do not deduplicate repeated report occurrences or choose authoritative vintages.
- [ ] Use mixed-source fixtures with the new release. Confirm the task-1 retained
  old-wire fixture still owns legacy compatibility; newly generated mixed bundles
  are not proof that old saved formats work.
- [ ] Run real four-bank staging/master example in a temporary root, selecting each
  source output explicitly. Record source row counts, reconstruction, temporal/evidence
  availability and exact source-unit values. Do not infer historical annual rates.
- [ ] Run full required checks once the focused paths pass:
```bash
uv run pytest
uv run ruff check src tests examples extractions
git diff --check
```
- [ ] Update current architecture to delivered scope and exact remaining provenance
  limits; link dated run evidence. Correct contradictions in owned code/docs now.
  Reproduce dependency findings before tracking upstream; do not silently add an
  adaptation. A required unsupported path blocks delivery until resolved.
- [ ] Independent correctness and complexity reviews of the production diff; apply
  complexity cuts before correctness triage. Re-run checks affected by repairs.
- [ ] Commit, push and open PR against `develop`. Offer to clean the coding worktree
  and sync the base checkout after merge. Keep disposable spike code out of the PR.

## Plan coverage and completion rule

Source capture/transport: task 1 and task 4. Semantics and all fifteen CR9 relations:
task 2. Independent stages, combined readback and transactional publication: task 3.
Master replacement, provenance, reconstruction and user guidance: task 5. Identity,
unknown dates and no implicit analytical aggregation apply throughout.

The only intermediate researcher checkpoint is task 3; final delivery is reviewed
through the implementation PR. Mark progress with actual runs, not the presence of
classes or table declarations. This plan does not authorise the deferred refactors.

## Task-3 execution evidence — 2026-10-12

Coding branch: `feature/cr9-capture`, seeded from the approved plan branch rather
than the disposable spike. Documentation remains in the base checkout.
Checkpoint code is retained in [draft PR #9](https://github.com/discreteds/rwa-analysis/pull/9).

- Baseline: 114 tests passed before changes.
- Tasks 1–3 integrated and review fixes applied: 143 tests passed, including original CR6 behaviour, old-wire
  fixtures, Westpac mixed capture, field semantics and persisted metadata/reconstruction.
- Real PDF run produced nine CR6 and eight CR9 mortgage rows, all 27 declared tables,
  four temporal roles and seven within-row default/new-default subset relationships.
- Annual interval remains July 2024–June 2025; weighted PD/EAD timing remains June
  2024; ten-year history has unresolved endpoints. No annual default rate was inferred.
- Reconstruction uses stored values and restores published column labels/order.
- The scope of the default-count subset excludes the blank default-stock row.

Run from the coding worktree:
```bash
uv run python examples/westpac_cr9.py --data-root /tmp/opencode/cr9-task3-final --run-name westpac-cr9-checkpoint-reviewed
```

Retained local evidence: `/tmp/opencode/cr9-task3-final/` (Bronze, manifest, DuckDB,
readback Parquet files); log: `/tmp/opencode/cr9-task3-final-reviewed.log`.

Complexity review retained the typed models, fifteen-relation CR9 inventory and
boundary-specific tests. It removed an unused temporal-binding copy on semantic
`FieldOccurrence`; source metadata still owns those bindings and Silver persists them.
The 52 catalogue tests passed after that cut. No metadata-ingress or constructor-
validation refactoring was included. Four-bank CR9 expansion and full CR9 master
acceptance remain task-4/5 work, not claimed complete by this checkpoint.

Correctness review found a missing row-axis qualification in Silver field metadata.
A failing source-backed regression reproduced it; the repaired projection now attaches
the default definition to default-stock counts without leaking it to performing rows.
The full suite and the real example passed after repair; Ruff and diff checks pass.
No upstream-dependent blocker was identified for this checkpoint.

## Four-bank completion evidence — 2026-10-12

| Task | Status | Executable evidence |
|---|---|---|
| 1 — Westpac source/transport | COMPLETE | Independent source golden and retained legacy-wire fixture; mixed transport roundtrip. |
| 2 — Shared semantics/CR9 conformance | COMPLETE | Occurrence/date applicability tests; precise rates, missingness, temporal roles and qualifications. |
| 3 — Mixed staging | COMPLETE, researcher approved | Real Westpac checkpoint above, followed by explicit permission to continue. |
| 4 — CBA/NAB/ANZ | COMPLETE | Eight/eight/nine rows; independent goldens; bank-specific conformance and actual selected catalogue evidence references. |
| 5 — Master/delivery | COMPLETE AND MERGED | Persisted mutations copied; reconstruction without staging databases; smaller/empty selections replace both domains. |

Actual command: `uv run python examples/four_bank_cr9.py`.

Artifacts: `/tmp/opencode/cr9-four-bank-8yj05s49/`.
Log: `/tmp/opencode/cr9-four-bank-final.log`.

The example retained four mixed bundles, four organisation publications and a master
publication containing 36 CR6 rows and 33 CR9 rows, then reconstructed eight tables
from master values. Readback Parquet files are under the artifact root's `readback/`.
The new example exposes research objects for `python -i` and prints its fresh retained
temporary output root. Existing Westpac interactive-example debt remains tracked.

Full suite: **148 passed**. Independent final correctness review: no repair findings;
its focused extraction/catalogue/conformance/master run passed 32 tests. Complexity
review retained the source-specific extraction/code evidence and cut ANZ's temporary
test release auto-completion so it now exercises the actual integrated release.
After that test-only cut, the two focused ANZ tests passed. Ruff and diff checks
passed; 91 local documentation targets resolved against the documentation and
implementation checkouts.

Source decisions remain faithful and scoped: CBA history starts at year precision
`2014`; NAB count columns keep their explicit dates and agreement-count evidence;
ANZ's five-year history excludes technical defaults/exited obligors as disclosed and
its 0.62% subtotal is retained directly. Unknown annual anchors/denominators stay
unknown. No automatic aggregation or authoritative-vintage selection was added.

The pinned APIs emit schema-inference and deprecation messages; the separately
recorded inference-log investigation is not a confirmed upstream correctness defect.
No upstream-dependent blocker was established for the completed capture scope.

## Next work — earlier reporting period

Researcher direction: repeat CR6 and CR9 capture across an earlier reporting period
for the four banks, using the established source-review, extraction, catalogue and
publication workflow. The reporting period and source documents remain to be selected.
Preserve the existing captures and retain each earlier report as a distinct source
occurrence. This is the next piece of work, not an outstanding task in this completed
plan; detailed scope will follow source selection.
