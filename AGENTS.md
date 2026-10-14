# Agent guidance

## Project purpose

This is a single-user Python disclosure research project using Mountainash for tabular analytics, conformance, configuration and storage integration. Australian mortgage regulatory capital is the first slice. Validation is separate and undefined.

The primary goal is [faithful capture and useful tagging](docs/01.principles/a.architecture/capture-and-tag-for-research.md), not perfect accounting. PDFs provide incomplete evidence by nature. Preserve and tag partial semantics; support explicit assumptions, approximations and imperfect comparisons downstream. Do not demand exhaustive definitions, exact reconciliation or global analytical eligibility before retaining faithfully captured observations. Distinguish actual extraction/structural errors from legitimate research limitations.

The implemented slice includes four-bank mortgage CR6/CR9 and selected 2023/2024 historical
source tables: metadata-defined PDF capture with bespoke physical readers, retained Bronze, a durable semantic catalogue,
normalised organisation staging Silver, master consolidation and source-shaped
numeric/lexical dataframe reconstruction. CR1/CR2,
liquidity and capital analytics remain research/design work rather than production
pipelines. Check actual code and assets before asserting additional capability.

Start with the [documentation guide](docs/README.md), [current architecture](docs/architecture.md)
and [executable README](README.md). Historical specs and plans retain superseded
proposals; their presence is not authority to restore retired functionality.

The approved [contextual-occurrence](docs/01.principles/a.architecture/contextual-source-occurrences.md)
and [metadata-driven processing](docs/01.principles/a.architecture/metadata-driven-extraction-and-conformance.md)
principles govern the target architecture. Their [design specification](docs/04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md)
and disposable spike shape are approved; the implementation plan was approved on
2026-10-13. Checkpoint A was accepted on 2026-10-14. Tasks 4–6 migrate all twelve
selected sources and implement catalogue-free CR6/CR9 projections on
`feature/metadata-driven-extraction`; checkpoint B review is pending. Do not execute
Task 7 before checkpoint B acceptance. Preserve retained formats and source identities.

## Design principles — mandatory

Before architectural decisions or changes to extraction contracts, metadata, mappings, conformance, persistence, identity or validation:

1. Read [the principles guide](docs/01.principles/README.md) and [maintenance rules](docs/01.principles/PRINCIPLES.md).
2. Follow the relevant category index and read the actual applicable principle documents. Summaries, conversation memory and this file are not substitutes.
3. Read the relevant detailed specification and source evidence before implementing its requirements.

| Concern | Required starting point |
|---|---|
| Layer boundaries, source bundles, Silver rebuilds, Gold dependencies | [Architecture](docs/01.principles/a.architecture/INDEX.md) |
| Metric definitions, label mappings, variants, temporal scope, corrections and identity | [Data semantics](docs/01.principles/b.data-semantics/INDEX.md) |
| PDF review, bespoke extractors, golden sets and extraction tests | [Extraction and validation](docs/01.principles/c.extraction-and-validation/INDEX.md) |
| Library selection, tabular expressions, settings, adapters and coding style | [Coding practices](docs/01.principles/d.coding-practices/INDEX.md) |

Principle documents own their decisions, statuses and scopes; category indexes own the navigation inventory. `AGREED` means an accepted design constraint, not implemented functionality. If new evidence conflicts with an agreed principle, surface the conflict and obtain a revised decision rather than silently overriding it. Update the principle, category index and affected specifications together when a decision changes.

Follow [validation is a separate process](docs/01.principles/c.extraction-and-validation/validation-is-a-separate-process.md). Validation is not defined yet: do not embed validators, precision/consistency checks or validation gates in processing, including at input/output or publication boundaries. Model/schema declarations and conformance do not authorize runtime validation. Earlier boundary-validation instructions are superseded by this principle.

## Documentation and planning locations

Work on documentation in the synced base checkout, on a documentation branch with a
PR when it is standalone work. Keep documentation associated with an implementation
on that implementation branch and in the same PR. Reserve worktrees for coding;
do not create a worktree for each spec or plan.

All project documentation belongs in this repository:

- Project backlog: `docs/04.planning/a.backlog/INDEX.md`. Temporary implementation
  adaptations belong in its `techdebt/` subtype with an explicit removal objective.

- Discovery and source reviews: `docs/00.ideation/`.
- Durable principles and architecture: `docs/01.principles/`.
- Superpowers specifications: `docs/04.planning/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
- Superpowers implementation plans: `docs/04.planning/superpowers/plans/YYYY-MM-DD-<topic>.md`.

Use these planning paths even when a skill defaults to `docs/superpowers/`. Preserve the user's directory convention and update relative links after moves. Mountainash's external repository is a reference, not the destination for this project's documents.

The [documentation guide](docs/README.md) identifies current specifications, completed
plans and logical-model examples. Follow its status distinctions before using a design.

## Source and extraction workflow

- Save acquired PDFs in project-root `raw/` and maintain [raw/index.md](raw/index.md). Keep acquisition simple; do not introduce checksums, registration machinery or file-identity proofs.
- Scrutinise each PDF with an LLM before defining its capture bindings and physical sourcing. Inspect tables, notes, glossaries and applicable definitions; use rendered pages when extracted text loses meaning. Current entrypoints compose source-local `definition.py` and `physical.py` through a thin `extract.py`.
- One source PDF owns one logical Bronze bundle, potentially containing multiple domains, portfolios, jurisdictions and observation dates. Reviewed metadata binds capture selection and applicability; source-specific operations supply physical mechanics where needed.
- Implemented paths are `extractions/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/` and `data/bronze/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/<output-version>/bundle.json`. Generated Bronze is retained separately and is not automatically present in a fresh checkout/worktree.
- `run_name` supplies the saved output version, not a code/schema version. Current captures use `disclosure-v4` with `datasets`, a retained definition `snapshot` and physical `fragments`; source datasets expose `cells` and `metadata`. Explicit snapshot domain bindings provide named CR6/CR9 projections. Preserve retained `cr6-v1`/`disclosure-v2`/`disclosure-v3` formats: legacy CR6 datasets still expose `metadata` and `exposure_rows`, and CR9 exposes `metadata` and `backtesting_rows`. See the [source extension interfaces](docs/architecture.md#bespoke-extraction-and-shared-interfaces).
- Folder jurisdiction/date describe the source disclosure. Dataset context determines exposure geography, regulatory basis and observation date.
- Preserve labels, values, units, precision, missingness, segmentation and evidence. Unresolved meanings remain explicit; notes and glossaries may establish metric variants.
- Inspect both table axes and nested headers for meaning. Capture `of which`, parent/child and total relationships, including those established by notes, so downstream aggregation does not double-count parents and subsets. Do not assume displayed children exhaust a parent or are mutually exclusive without evidence.
- Author golden expectations independently from the extractor's output. Humans or LLMs may extend or correct them using source evidence. Saved tests run without LLM calls.
- Mirror the extraction hierarchy under `tests/bronze/`, with `golden.json`, `golden-notes.md` and `test_extraction.py`. Metadata mismatches are failures even when values match.

## Conformance and persistence

### Mountainash-first coding — mandatory

Follow [Mountainash-first implementation](docs/01.principles/d.coding-practices/mountainash-first.md).
Use native ecosystem capabilities for tabular work, contracts, settings and storage;
inspect pinned APIs before writing local equivalents. Polars/Arrow are explicit
boundaries, not a parallel business-logic pipeline. The principle owns adaptation
policy and the approved temporary metadata-ingress exception.

Follow the [current architecture](docs/architecture.md) for processing ownership and
entrypoints. Keep ordinary Python use, explicit inputs and independently callable stages.

### Semantic discovery and maintenance

- Treat canonical concepts and their relationships as durable, slowly changing, first-class research assets with stable identities and retained revisions.
- Develop the semantic hierarchy through source discovery and researcher interviews. Compare unfamiliar terminology with existing concepts before proposing a new concept or variant; differing labels alone do not establish differing semantics.
- Ask the researcher to resolve uncertain meaning or analytical significance. Record the agreed interpretation, rationale and decision context separately from explicit source statements, with links to supporting evidence.
- Preserve source terms and map them in context. Arrangements are counted entities (#), while exposures are monetary amounts ($); do not merge these concepts. One table can contain counts, amounts and exposure-weighted rates (%), each with its own field-level definition and units. Establish counting, weighting and aggregation conventions from evidence and researcher decisions rather than adjacent columns or vocabulary alone.
- Keep catalogue revisions and mapping decisions outside disposable Silver, and make them reproducible rebuild inputs. Renames can preserve identity; semantic splits, merges and replacements require explicit relationships and revised mappings.

### Execution and storage

- Use Mountainash relations/contracts and storage integration; the selected persistent store is local DuckDB through `mountainash-data`. Keep NumPy/SciPy capital calculations independent of persistence.
- Consult the actual installed/local Mountainash APIs and backend capabilities before implementing an integration. The dependency's documentation does not prove every conformance or transaction path is supported.
- Record Mountainash dependency findings in `/home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash/a.backlog/`, following its conventions and checking existing owners first. Do not open GitHub issues without explicit researcher approval. Distinguish reproduced defects, capability questions and consumer declaration mistakes.
- Silver reads saved Bronze. Full regeneration is the implemented workflow; incremental upserts are deferred and would need to yield the same logical result.
- Keep definitions, mappings, curated corrections and rebuild manifests outside disposable Silver. A manual Silver edit alone is not a durable correction.
- Version interpretations and preserve source-effective dates separately from revision history. Mutable canonical classifications and database-generated IDs are not sufficient durable observation identities.
- Publish candidate revisions atomically. Handle removal, splitting and merging as well as updates; preserve source lineage and avoid double-counting comparative evidence. Validation is separate and does not supply an implicit publication gate.
- Before publication/consolidation, consult the [current publication limits](docs/architecture.md#current-publication-and-provenance-limits):
  paths are mutable, selections replace contents, and manifests do not automatically
  pin all reproducibility inputs. Preserve retained assets and use current publications.
- Gold identifies the Silver revision it consumed and must be regenerated when its dependencies change.
- Apply [emergent analysis and selective persistence](docs/01.principles/a.architecture/emergent-analysis-and-selective-persistence.md): do not create core entities or mandatory storage for every possible reconciliation or inference. Compute exploratory relationships as needed, retain useful outputs with reproducible inputs and assumptions, and promote reusable definitions when research warrants them. Missing evidence or unexplained analytical residuals do not automatically indicate extraction errors.

## Verification and maintenance

Use verification appropriate to the actual change: check links, statuses, indexes and
code/example accuracy for documentation; independent goldens for extraction; actual
conformance and persisted reconstruction for Silver. Current project commands:

```bash
uv sync --locked
uv run pytest
uv run ruff check src tests examples extractions
git diff --check
```

Use focused existing tests while iterating. New tests must protect observable behaviour
or a distinct regression, not duplicate framework arithmetic or implementation details.
Do not restore the retired defensive lifecycle suite or turn tests into runtime gates.
The retained codec/transport and model parsers still perform checks; their existence
does not authorise a new validation process. See the current architecture's distinction.

Example scripts write generated data; inspect their selected roots/run names before
running them. `examples/cba_extraction.py` starts from the tracked PDF; saved-Bronze
examples require retained `v1` bundles, which a fresh worktree does not inherit.
`examples/four_bank_cr9.py` starts from all four PDFs, retains a fresh temporary output
root and exposes interactive results. Store readback has named `.cr6` and `.cr9` outputs.

Preserve unrelated user work. Keep exploratory artifacts clearly labelled and distinguish them from production Bronze, approved golden fixtures and implemented contracts. When changing this guidance, retain links to authoritative principles instead of duplicating their status inventories here.
