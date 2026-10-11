# Strategic architecture migration and retirement plan

> **For agentic workers:** Use `executing-plans`, with a researcher checkpoint at
> the first working CBA path. Use existing source goldens and native Mountainash
> contracts at their owning boundaries. Do not restore the retired defensive suite.

**Status:** Approved for implementation. The researcher accepted the refined design as settled
and authorised planning without another spike. During planning, the researcher
explicitly rejected reintroducing the older checks or bullet-proofing this migration.

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
- Use Mountainash's dataframe conformance, contracts, rules and arithmetic. Keep
  necessary parameter checks at entrypoints. Do not add bespoke numeric verification,
  precision guards, repeated consistency passes or a parallel validation framework.
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
| `normalization/validate.py` | Native domain input/output contracts | Delete; do not port the old checking layer |
| `reporting/cr6_tables.py` | `domains/cr6/reconstruction.py` | Move persisted-value reconstruction into its domain owner |
| `contracts/frames.py::conform_frame` policy wrapper | Native contract boundary used by pipelines | Remove obsolete wrapper/checks and their tests |
| Bronze free save/load functions | `storage/bronze.py::BronzeStore` | Move working I/O into the owner; remove obsolete free entrypoints |
| `storage/silver.py` rebuild/publication orchestration | `SilverStore` plus workflow | Keep transaction/read-write mechanics; remove old orchestration functions |
| Settings and component assembly scattered in examples | `settings.py`, `composition.py` | Add native settings and a small construction function |
| Stage sequencing | `workflow.py::OrganisationSession` | Add stage methods and thin `run()` |
| Master build | `storage/consolidation.py::SilverConsolidator` | Combine selected staging outputs and publish through the store |

Keep the current three CR6 physical tables. Declare their associations with the named
domain output once; storage and consolidation consume that same declaration. Remove
empty legacy packages and compatibility aliases when their last callers move.

## Interfaces

The spec owns the model detail. These are the implementation handoffs:

- Dataset containers compose shared metadata and expose domain-specific collections.
  Existing CR6 wire `records` remains readable; Python callers use the declared domain
  collection. The shared protocol does not impose CR6's snapshot context on other domains.
- Loaded inputs pair each bundle with its `BronzeRef`. Selected catalogue releases
  and supporting Bronze references remain explicit inputs, retained with the result.
- `Cr6Output` exposes `observations`, `fields` and `relationships` as Mountainash
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

**Files:** `extraction/{datasets,cr6,codec,runner}.py`, necessary extractor constructor
and catalogue access changes; new `domains/cr6/{models,contracts,pipeline,reconstruction}.py`.
Retire the normalization/reporting/checking modules listed above as callers switch.

- [ ] Compose source metadata and move shared dataset/bundle ownership. Preserve
  retained wire format through the existing codec and keep golden files unchanged.
- [ ] Declare CR6 input/output models and augment their derived Mountainash contracts
  with field types and domain rules. Keep domain knowledge out of generic helpers.
- [ ] Move the proven dataset-wide transformations and source-binding reconstruction
  into domain operations. Trust Mountainash arithmetic; preserve source values and
  precision until the declared output conversion.
- [ ] Replace table-name dictionaries at domain interfaces with named output members
  and one table association declaration.
- [ ] Update existing source/semantic proof for changed Python access. Remove tests
  whose sole purpose was enforcing the checking layer being retired.

**Useful evidence:** the four independent source goldens still match; a saved CBA
bundle conforms to the new declared monetary/rate/count types with its source tags.
Run the affected existing source/catalogue/conformance tests; do not add a defensive
matrix of synthetic corruptions.

## Task 2 — Make the CBA workflow runnable and cut over its callers

**Files:** `settings.py`, `composition.py`, `workflow.py`, existing
`storage/{bronze,manifests,silver}.py`, project/CBA settings, both existing examples,
README and the affected integration fixtures/tests.

- [ ] Move the existing Bronze I/O and Silver transaction/readback into their stores.
  Retain selected-input provenance; use native declarations at the boundaries.
- [ ] Load project defaults and organisation overrides using Mountainash Settings.
  Resolve paths from the project root and construct operations in `build_session`.
- [ ] Implement independently callable stages and `run()` using those same operations.
- [ ] Execute CBA from retained Bronze through publication and reconstruction. Also
  execute the full entrypoint using the existing CBA extractor.
- [ ] Switch examples and callers, then delete the superseded save/load/rebuild/
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

- [ ] Run each organisation's existing CR6 inputs through the same implementation,
  into its own staging database with the common declared schema.
- [ ] Implement a full master rebuild from explicitly selected staging publications.
  Combine corresponding relations and publish with the existing transaction pattern.
- [ ] Retain producing revisions and references to their durable manifests. Master
  readback uses its saved selection and actual persisted values.
- [ ] Reconstruct the four source tables. Inspect the existing expected values,
  labels, missingness, mappings and relationships using the independent source assets.

```sh
uv run python -i examples/four_bank_research.py
```

**Useful evidence:** four source-shaped dataframes; 36 observations, 432 field positions,
1,296 mapping references and 32 source relationships retained across master. These
describe the selected source case, not new generic runtime completeness checks.

## Task 4 — Finish retirement and hand over

- [ ] Check active imports/examples against the replacement map. Delete unused old
  code and obsolete tests now, rather than schedule a later cleanup project.
- [ ] Update README with `run()`, targeted reruns, layered settings and staging/master
  usage. Keep historical artifacts and label historical instructions appropriately.
- [ ] Run the relevant existing tests, adapting or removing those tied to retired
  checks. Verify the demonstrated workflow and run Ruff plus `git diff --check`.
  Do not restore historical lifecycle/fault-injection suites or invent replacement guards.
- [ ] Review the implementation for correctness and unnecessary complexity against
  this narrowed scope. Open the implementation PR against the confirmed integration
  branch (`develop` currently); offer local synchronisation after handoff.

## Completion

The supported four-bank workflow runs through the new interfaces; source evidence
and interpretations survive; native contracts enforce the declared boundaries; old
implementations are removed. This completes the requested architectural migration.
Additional hardening is not part of this plan.

Execution uses batched `executing-plans` with the CBA checkpoint. Review the plan and
confirm the implementation seed/worktree before coding.
