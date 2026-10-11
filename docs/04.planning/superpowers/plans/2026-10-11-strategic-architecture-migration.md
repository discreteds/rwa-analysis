# Strategic architecture migration and retirement plan

> **For agentic workers:** Use `executing-plans`, with a researcher checkpoint at
> the first working CBA path. Use existing source goldens and native Mountainash
> schema declarations/conformance. Do not restore the retired defensive suite.

**2026-10-11 decision:** [Validation is a separate process](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md),
and has not yet been defined. This supersedes earlier boundary-validation instructions.
Do not invoke validators or introduce validation gates in this migration.

**Status:** Approved for implementation. The researcher accepted the refined design as settled
and authorised planning without another spike. During planning, the researcher
explicitly rejected reintroducing the older checks or bullet-proofing this migration.

**Current checkpoint:** the researcher approved CBA and authorised the remaining
four-bank work. All four staging databases and master now run successfully; full
suite: **114 passed**. Correctness and complexity reviews found no in-scope defects
or required cuts. PR #2 is open against `develop` (not merged). Earlier blocked-status
entries below are historical execution evidence, not current delivery gates.

Independent alignment and complexity reviews passed on 2026-10-11 with no requested
changes. The researcher approved implementation and confirmed the existing checkout,
`feature/organisation-workflow` seeded at `3be5e86`, with `develop` as the PR target.

**Goal:** Implement the agreed ownership boundaries and `OrganisationSession.run()`,
demonstrate the real four-bank workflow, and remove the implementations it replaces.

**Architecture:** Declarations describe domain models/contracts; operations perform
extraction, conformance and storage; configuration supplies execution settings; the
session sequences calls. Adapt working code and retain research assets.

**Tech stack:** Existing Python/Mountainash/mountainash-data/mountainash-files/
mountainash-settings stack, Polars/Arrow and local DuckDB. The spike used Mountainash
PR #357 merge `ee28822d25310a396865a78cba17f2d7cb779d09` successfully.

**Spec:** [Strategic architecture](../specs/2026-10-11-strategic-architecture-design.md).
The researcher's planning clarification above governs verification scope: this is
implementation of the simpler workflow, not restoration of the older hardening work.

## Scope and constraints

- Keep PDFs, source reviews, independent golden JSON/notes, saved Bronze and catalogue
  files/identities. Read the existing Bronze format; do not regenerate retained v1.
- Production domain scope remains four-bank CR6. CR1/CR2 are disposable design examples.
- Money uses `Decimal(16,2)`; rates, band fractions and maturity years use
  `Decimal(16,8)`; counts remain integers. Preserve source precision before conversion.
- Use Mountainash's schema declarations, dataframe conformance and arithmetic.
  Do not add embedded validation, including native validator calls at boundaries,
  precision guards or repeated consistency passes. Working arithmetic types do not
  impose precision-38 source contracts.
- Do not restore `test_silver_rebuild.py` from history, its defensive scenarios, or
  the old `normalization/validate.py` checks under new names.
- Reuse the existing transaction mechanism and source transport. Record selected
  inputs in retained manifests. Do not expand them into another checking system.
- Keep the ordinary Python interface, independently callable stages and explicit
  inputs. No CLI, runtime Git, workflow engine or automatic plugin discovery.
- The spike is reference material; write production code from the working baseline.

## Starting point

Recommended implementation seed: `feature/simple-cr6` at `3be5e86`, with the approved
documents and tested dependency update carried over selectively. Confirm the branch
and worktree preference before starting; do not use the disposable spike as the
production base. Continue to preserve the existing local `data/` assets.

The existing suite passed 127 tests on the updated dependency. This is baseline
evidence, not a target test count or a reason to keep tests for retired checks.

## Replacement map

Paths are relative to the project root. Delete superseded code when its callers switch.

| Existing responsibility | Target | Action |
|---|---|---|
| Source evidence models, tokens and PDF extraction | `extraction/`, existing bespoke extractors | Keep; make mechanical changes for composed metadata |
| General dataset/bundle ownership inside `extraction/cr6.py` | `extraction/datasets.py` | Move shared protocol/metadata/bundle declarations |
| Strict retained Bronze representation | Existing `extraction/codec.py` | Adapt Python composition while keeping saved wire representation |
| Catalogue knowledge and contextual mapping | Existing `catalogue/` | Keep; update model access only where needed |
| CR6 models and whole-table schemas in `normalization/models.py` | `domains/cr6/models.py`, `contracts.py` | Replace with dataclass-derived, explicitly augmented declarations |
| `normalization/cr6.py` | `domains/cr6/pipeline.py` | Reuse dataset expressions; remove the old entrypoint/file |
| `normalization/validate.py` | No processing replacement | Delete; validation is separate and undefined |
| `reporting/cr6_tables.py` | `domains/cr6/reconstruction.py` | Move persisted-value reconstruction into its domain owner |
| `contracts/frames.py::conform_frame` policy wrapper | Native schema-directed conformance | Remove obsolete wrapper/checks and their tests |
| Bronze free save/load functions | `storage/bronze.py::BronzeStore` | Move working I/O into the owner; remove obsolete free entrypoints |
| `storage/silver.py` rebuild/publication orchestration | `SilverStore` plus workflow | Keep transaction/read-write mechanics; remove old orchestration functions |
| Settings and component assembly scattered in examples | `settings.py`, `composition.py` | Add native settings and a small construction function |
| Stage sequencing | `workflow.py::OrganisationSession` | Add stage methods and thin `run()` |
| Master build | `storage/consolidation.py::SilverConsolidator` | Combine selected staging outputs and publish through the store |

Use flat CR6 rows and normalised child relations, following the approved CBA spike.
The earlier three-table wording was a simplification, not a table-count constraint.
Declare their associations with the named
domain output once; storage and consolidation consume that same declaration. Remove
empty legacy packages and compatibility aliases when their last callers move.

## Interfaces

The spec owns the model detail. These are the implementation handoffs:

- Dataset containers compose shared metadata and expose domain-specific collections.
  Existing CR6 wire `records` remains readable; Python callers use the declared domain
  collection. The shared protocol does not impose CR6's snapshot context on other domains.
- Loaded inputs pair each bundle with its `BronzeRef`. Selected catalogue releases
  and supporting Bronze references remain explicit inputs, retained with the result.
- `Cr6Output` exposes `observations`, `contexts`, `fields`, `relationships` and their
  normalised metadata collections as Mountainash
  relations. Domain operations receive loaded data and return named results; no I/O.
- `SilverCandidate` carries those outputs and the rebuild selection.
- `publish(candidate, revision)` records the producing revision and retained manifest.
  `Publication` identifies the database and manifest; `RunResult` contains the
  publication plus reconstructed tables and metadata.
- Master retains producing revisions and selected staging manifests. Reconstruction
  uses copied master numbers and retained source references, not current staging data.

```python
session = build_session(settings)
inputs = session.load_bronze(selected_refs)
candidate = session.conform(inputs, catalogue=selected_catalogue)
publication = session.publish(candidate, revision="review-1")
tables = session.reconstruct(publication)

result = session.run(
    documents=selected_documents,
    catalogue=selected_catalogue,
    run_name="cba-june-review",
    revision="review-2",
)
```

`run()` calls extract → save Bronze → reload Bronze → conform → publish → reconstruct.
`build_session(settings)` supplies concrete operations. The session does not load
configuration files, construct pipelines, encode JSON or execute database transactions.

## Task 1 — Replace domain declarations and operations

**Approved normalisation amendment:** implement fresh against the shape demonstrated
by `/tmp/opencode/cr6-normalisation-spike.py`; do not promote that disposable script.
Use the existing four-task plan and CBA checkpoint. First adapt domain tests to read
context, attribute, mapping and evidence child relations; retain independent numeric
and source-semantic expectations. Then replace nested Silver models and recursive
schema augmentation with flat declarations and domain-owned projection. Preserve all
currently represented collections, including context knowledge qualifications,
assertion alternatives/typed values, evidence and decisions. Keep band fields on
observations. All tables participate in the existing publication/readback inventory.
Cost: changes are confined to CR6 models/declarations/projection, affected tests and
the Silver format declaration; no new package, ingestion adapter or lifecycle policy.

**Subsequent authorised temporary adaptation:** isolate `asdict()` and full-record
inference in `domains/cr6/metadata.py`; use Mountainash expressions for metadata
projection rather than manually constructing flat records field by field. Track its
removal under [techdebt](../../a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md).
This replaces the preceding no-ingress-adapter assumption, not the normalised storage
shape or the separation of validation.

Run `uv run pytest tests/silver tests/integration -q`, then the full suite and the
real saved-Bronze/PDF CBA examples. Verify related metadata after DuckDB readback,
not just in-memory projections. Completion is the existing CBA researcher checkpoint.

**Files:** `extraction/{datasets,cr6,codec,runner}.py`, necessary extractor constructor
and catalogue access changes; new `domains/cr6/{models,contracts,pipeline,reconstruction}.py`.
Retire the normalization/reporting/checking modules listed above as callers switch.

- [x] Compose source metadata and move shared dataset/bundle ownership. Preserve
  retained wire format through the existing codec and keep golden files unchanged.
- [x] Declare CR6 input/output models and augment their derived Mountainash schemas
  with field types. Keep domain knowledge out of generic helpers; do not add validators.
- [x] Move the proven dataset-wide transformations and source-binding reconstruction
  into domain operations. Trust Mountainash arithmetic; preserve source values and
  precision until the declared output conversion.
- [x] Replace table-name dictionaries at domain interfaces with named output members
  and one table association declaration.
- [x] Update existing source/semantic proof for changed Python access. Remove tests
  whose sole purpose was enforcing the checking layer being retired.

**Useful evidence:** the four independent source goldens still match; a saved CBA
bundle conforms to the new declared monetary/rate/count types with its source tags.
Run the affected existing source/catalogue/conformance tests; do not add a defensive
matrix of synthetic corruptions.

## Task 2 — Make the CBA workflow runnable and cut over its callers

**Files:** `settings.py`, `composition.py`, `workflow.py`, existing
`storage/{bronze,manifests,silver}.py`, project/CBA settings, both existing examples,
README and the affected integration fixtures/tests.

- [x] Move the existing Bronze I/O and Silver transaction/readback into their stores.
  Retain selected-input provenance; use native declarations at the boundaries.
- [x] Load project defaults and organisation overrides using Mountainash Settings.
  Resolve paths from the project root and construct operations in `build_session`.
- [x] Implement independently callable stages and `run()` using those same operations.
- [x] Execute CBA from retained Bronze through publication and reconstruction. Also
  execute the full entrypoint using the existing CBA extractor.
- [x] Switch examples and callers, then delete the superseded save/load/rebuild/
  reconstruction entrypoints. Do not leave a second supported route or alias layer.

```sh
uv run python -i examples/cba_extraction.py
uv run python -i examples/cr6_research.py
```

**Researcher checkpoint:** show the real CBA dataframe, the session entrypoint,
component construction, one domain declaration and the deletion diff. This executable
checkpoint comes before extending the same pattern to the remaining banks.

## Task 3 — Extend the same path to four staging databases and master

**Files:** organisation settings for Westpac/NAB/ANZ,
`storage/consolidation.py`, composition and `examples/four_bank_research.py`.

- [x] Run each organisation's existing CR6 inputs through the same implementation,
  into its own staging database with the common declared schema.
- [x] Implement a full master rebuild from explicitly selected staging publications.
  Combine corresponding relations and publish with the existing transaction pattern.
- [x] Retain producing revisions and references to their durable manifests. Master
  readback uses its saved selection and actual persisted values.
- [x] Reconstruct the four source tables. Inspect the existing expected values,
  labels, missingness, mappings and relationships using the independent source assets.

```sh
uv run python -i examples/four_bank_research.py
```

**Useful evidence:** four source-shaped dataframes; 36 observations, 432 field positions,
1,296 mapping references and 32 source relationships retained across master. These
describe the selected source case, not new generic runtime completeness checks.

## Task 4 — Finish retirement and hand over

- [x] Check active imports/examples against the replacement map. Delete unused old
  code and obsolete tests now, rather than schedule a later cleanup project.
- [x] Update README with `run()`, targeted reruns, layered settings and staging/master
  usage. Keep historical artifacts and label historical instructions appropriately.
- [x] Run the relevant existing tests, adapting or removing those tied to retired
  checks. Verify the demonstrated workflow and run Ruff plus `git diff --check`.
  Do not restore historical lifecycle/fault-injection suites or invent replacement guards.
- [x] Review the implementation for correctness and unnecessary complexity against
  this narrowed scope. Open the implementation PR against the confirmed integration
  branch (`develop` currently); offer local synchronisation after handoff.

## Completion

### Execution status — 2026-10-11: incomplete; blocker classification under reassessment

The evidence below predates the separate-validation decision. Runtime validation
was added outside the intended scope. Item 290 remains a dependency finding, but
is not a processing delivery gate. Neither an invented source precision declaration
nor a failing validator establishes a blocker for the approved workflow. Code has
not yet been corrected or rerun following this documentation decision.

The implementation branch is `feature/organisation-workflow`, seeded from
`3be5e86`. Approved documentation and dependency pin were carried over in `1fef532`;
the disposable spike was not imported.

- Source composition and retained wire compatibility are verified: 70 source/
  catalogue tests and 31 Bronze transport tests passed, including all four unchanged
  source goldens. Six retained Bronze payloads round-tripped unchanged.
- Domain declarations, named results, stores, settings, construction, stages and
  `run()` are written, with superseded modules removed in this work-in-progress
  branch. This is not a completed cutover: Tasks 1/2 remain blocked until the real
  CBA path passes. The prior working implementation remains at the seed commit.
- The latest full run before removing provisional ingress adaptations reported
  **102 passed, 7 failed, 2 setup errors**. The failures/errors reached native array
  contracts. Subsequent focused execution without those adaptations fails earlier
  on the all-null source Decimal declaration: **1 passed, 7 failed** in the domain/
  organisation tests. The real `examples/cr6_research.py` run confirms #363 before
  publication (the known cap; consumer declaration necessity remains unresolved).
  Tests remain failing, not skipped. Ruff and `git diff --check` pass.
- A focused storage/workflow review found component construction inside session
  reconstruction; source loading was moved into the storage operation.
- Review of the domain handoff identified blanket decimal pre-casts and manual
  nested-metadata transport introduced after native ingress failures. Both were
  removed rather than retain consumer workarounds. Native field rounding is now
  explicit; ordinary arithmetic widening and source-unit reconstruction remain.

**Tracking correction:** the four GitHub reports were filed in the wrong location
and have been closed as transferred, not fixed. Mountainash Central owns the
records below (commit `6f2ff8f4`). These are two reproduced defects, one capability
investigation, and an observation under an existing constraint—not four established
upstream bugs. No new execution priority or upstream implementation is authorized.

Canonical backlog directory:
`/home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash/a.backlog/active/`

| Central record | Observed failure / disposition | Affected step |
|---|---|---|
| 289 — `dataclass-source-schema-structured-join.md` (former GitHub #360) | Reproduced schema loss during structured join lineage | Task 1 relation composition |
| 290 — `native-array-datacontract-validation.md` (former GitHub #361) | Reproduced validator defect; validation is outside processing | Not a migration gate |
| 291 — `nested-dataclass-ingress-support.md` (former GitHub #362) | Establish supported native ingress API or capability gap; not a confirmed regression | Task 1 metadata ingress |
| 285 — `polars-decimal-round-panic-upstream.md`, consumer observation (former GitHub #363) | Known owner-approved precision cap; first investigate whether our precision-38 source declaration is necessary | Task 1 source-number conformance |

The measure-specific persisted numeric decision remains unchanged. #363 concerns
source working columns, not a return to universal precision-22 persisted measures.

**Next evidence:** correct the implementation to the agreed processing scope, then
run the actual path to establish which ingress/schema findings still affect it.
Resolve genuinely required dependency capabilities through their central owners.
Run the relevant domain and organisation/persisted-reconstruction tests, adapting
tests tied to retired checks. Then run the full suite and the real saved-Bronze
and PDF CBA examples before requesting the researcher checkpoint. Full implementation
correctness/complexity review and PR remain pending; Tasks 3/4 are not started.

### Processing correction — 2026-10-11 (CBA still blocked)

- Removed `checked()`, generated runtime datacontracts and repeated conformance.
  Removed source/factor/band precision-38 schema declarations. Wide Decimal
  arithmetic operands remain expressions, not source validation contracts.
- Removed the new organisation-content and publication-revision checking passes.
  Corrected publication to the installed native `Relation.to_pyarrow()` API.
- Fixed project-root resolution for default settings paths (a failing/passing
  regression now covers it). Removed the accidental test manifest referencing
  `/tmp/pytest-of-ubuntu/pytest-259/`; retained research artifacts were preserved.
  Retired the revision-guard assertion while keeping four-bank reconstruction proof.
- Executed numeric conversion on the nine retained CBA rows: first-band EAD is
  `281508000000.00`, PD is `0.00080000`, and maturity remains null. Output types
  are money `Decimal(16,2)`, small measures `Decimal(16,8)`, and integer counts.
- The full CBA session still fails materializing nested dataclass metadata with
  `ComputeError: not yet implemented: Nested object types`. Explicit-schema native
  `PydataIngress.convert` fails too; item 291 now includes this re-entry evidence.
  No consumer workaround was added. This is the current observed blocker; the
  previously reported join finding has not yet been reached on this path.
- CBA publication/reconstruction and the researcher checkpoint remain incomplete.
  Full pytest: **103 passed, 7 failed, 2 setup errors**. Eight failures/errors reach
  nested-object construction; the remaining conflict case fails native construction
  with an `AUD` value/type inference error. No failures are skipped. The empty-selection
  and default-path regressions pass. Source goldens and transport tests remain passing.

### Normalised CBA checkpoint — 2026-10-11

- Production CR6 uses flat persisted row models with shared contexts and ordered
  child metadata relations. All existing field value union branches, source locations,
  context knowledge qualifications, alternatives and decision/evidence references
  remain represented. The selected schema marker is `cr6-normalised-v1`.
- Mountainash expressions own metadata expansion, unnesting, projection, renaming
  and value-state derivation. `metadata.py` isolates the approved temporary recursive
  `asdict()` and full-record inference; its removal objective is in the project's
  new `a.backlog/techdebt/` subtype. No runtime validators were added.
- `uv run pytest -q`: **112 passed**. Tests include four-bank numeric reconstruction,
  a one-cent persisted mutation, source goldens, all CBA normalised tables through
  DuckDB readback, assertion alternatives/decision links, and typed integer/Boolean
  metadata. Dependency deprecation warnings remain, not new processing gates.
- Both `examples/cr6_research.py` (saved v1 Bronze) and `examples/cba_extraction.py`
  (PDF through `run()`) ran successfully. First CBA band reconstructs EAD `281508`
  million, PD `0.08` percent and count `742470`; all nine source rows are present.
  Review publications are `cba-normalised-retained-review` and `cba-normalised-review`.
- Independent complexity review: keep the normalised relations and local helper;
  restore readable formatting, defer metadata-schema redesign and master configuration.
  Applied formatting cut. Independent correctness review found a test fixture using
  an out-of-period decision; replaced it with an explicitly synthetic applicable
  decision. No in-scope production defects were reported. Full tests then passed.
- Tasks 3/4 and the final migration PR remain after researcher checkpoint review.
  The dependency findings are not gates on this now-executed CBA path; this does not
  claim the upstream nested-dataclass capability is fixed.

### Four-bank completion — 2026-10-11

- Added Westpac/NAB/ANZ settings and executed `examples/four_bank_research.py` using
  retained `v1` Bronze. Master contains 36 observations, 432 fields, 1,296 mappings
  and 32 relationships; all four reconstructed tables contain nine rows.
- `SilverConsolidator` concatenates selected staging relations through Mountainash
  and reuses the store's atomic replacement operation. Producing row revisions are
  retained; `MasterManifest` records the selected durable staging manifests.
- Tests demonstrate preservation of every table, copied persisted numeric changes,
  reconstruction after staging databases are removed, and full replacement when
  selecting fewer banks or an empty selection.
- Full suite: **114 passed**; Ruff passes. Independent correctness review found no
  concrete defects and confirmed no active imports of retired normalization,
  reporting or conformance-wrapper modules. Independent complexity review found
  no required cuts. No additional cleanup layer or runtime guards were introduced.
- README documents staging/master usage and the mutable publication database paths.
  The approved temporary metadata ingress adaptation remains tracked for removal.
- Migration PR: https://github.com/discreteds/rwa-analysis/pull/2, targeting `develop`.
  Local synchronisation is offered at handoff; the checkout remains on the feature
  branch until the researcher chooses it.

### Delivery criterion

The supported four-bank workflow runs through the new interfaces; source evidence
and interpretations survive; native conformance produces the declared schemas; old
implementations are removed. This completes the requested architectural migration.
Additional hardening is not part of this plan.

Execution uses batched `executing-plans` with the CBA checkpoint. Review the plan and
confirm the implementation seed/worktree before coding.
