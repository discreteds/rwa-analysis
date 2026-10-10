# Agent guidance

## Project purpose

This is a single-user Python disclosure research project using Mountainash for tabular analytics, conformance, validation and storage integration. Australian mortgage regulatory capital is the first slice; the architecture supports other portfolios, jurisdictions and data domains.

The primary goal is [faithful capture and useful tagging](docs/01.principles/a.architecture/capture-and-tag-for-research.md), not perfect accounting. PDFs provide incomplete evidence by nature. Preserve and tag partial semantics; support explicit assumptions, approximations and imperfect comparisons downstream. Do not demand exhaustive definitions, exact reconciliation or global analytical eligibility before retaining faithfully captured observations. Distinguish actual extraction/structural errors from legitimate research limitations.

The repository currently contains source PDFs, discovery notes, principles and design specifications. Check the actual files before assuming a package, extractor, database or test command has been implemented.

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

Principle documents own their decisions, statuses and scopes; category indexes own the navigation inventory. `AGREED` means an accepted design constraint, not implemented functionality. If new evidence conflicts with an agreed principle, surface the conflict and obtain a revised decision rather than silently overriding it. Update the principle, category index and affected specifications together when a decision changes.

## Documentation and planning locations

All project documentation belongs in this repository:

- Discovery and source reviews: `docs/00.ideation/`.
- Durable principles and architecture: `docs/01.principles/`.
- Superpowers specifications: `docs/04.planning/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
- Superpowers implementation plans: `docs/04.planning/superpowers/plans/YYYY-MM-DD-<topic>.md`.

Use these planning paths even when a skill defaults to `docs/superpowers/`. Preserve the user's directory convention and update relative links after moves. Mountainash's external repository is a reference, not the destination for this project's documents.

Current detailed specifications:

- [Platform architecture](docs/04.planning/superpowers/specs/2026-10-10-rwa-analysis-design.md).
- [Initial data model](docs/04.planning/superpowers/specs/2026-10-10-initial-data-model.md).
- [Layered schemas and E–R diagrams](docs/04.planning/superpowers/specs/2026-10-10-layered-data-model.md): distinct Bronze capture and Silver conformed contracts, with the durable semantic catalogue between them.
- [Worked model examples](docs/04.planning/superpowers/specs/2026-10-10-data-model-worked-examples.md): design exercises, not production fixtures.

## Source and extraction workflow

- Save acquired PDFs in project-root `raw/` and maintain [raw/index.md](raw/index.md). Keep acquisition simple; do not introduce checksums, registration machinery or file-identity proofs.
- Scrutinise each PDF with an LLM before constructing its bespoke Python extractor. Inspect tables, notes, glossaries and applicable definitions; use rendered pages when extracted text loses meaning.
- One source PDF's extractor owns one logical Bronze bundle, potentially containing multiple domains, portfolios, jurisdictions and observation dates.
- Agreed paths are `extractions/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/` and `data/bronze/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/<output-version>/`. These are intended layouts, not claims that they already exist.
- Folder jurisdiction/date describe the source disclosure. Dataset context determines exposure geography, regulatory basis and observation date.
- Preserve labels, values, units, precision, missingness, segmentation and evidence. Unresolved meanings remain explicit; notes and glossaries may establish metric variants.
- Inspect both table axes and nested headers for meaning. Capture `of which`, parent/child and total relationships, including those established by notes, so downstream aggregation does not double-count parents and subsets. Do not assume displayed children exhaust a parent or are mutually exclusive without evidence.
- Author golden expectations independently from the extractor's output. Humans or LLMs may extend or correct them using source evidence. Saved tests run without LLM calls.
- Mirror the extraction hierarchy under `tests/bronze/`, with `golden.json`, `golden-notes.md` and `test_extraction.py`. Metadata mismatches are failures even when values match.

## Conformance and persistence

### Semantic discovery and maintenance

- Treat canonical concepts and their relationships as durable, slowly changing, first-class research assets with stable identities and retained revisions.
- Develop the semantic hierarchy through source discovery and researcher interviews. Compare unfamiliar terminology with existing concepts before proposing a new concept or variant; differing labels alone do not establish differing semantics.
- Ask the researcher to resolve uncertain meaning or analytical significance. Record the agreed interpretation, rationale and decision context separately from explicit source statements, with links to supporting evidence.
- Preserve source terms and map them in context. Arrangements are counted entities (#), while exposures are monetary amounts ($); do not merge these concepts. One table can contain counts, amounts and exposure-weighted rates (%), each with its own field-level definition and units. Establish counting, weighting and aggregation conventions from evidence and researcher decisions rather than adjacent columns or vocabulary alone.
- Keep catalogue revisions and mapping decisions outside disposable Silver, and make them reproducible rebuild inputs. Renames can preserve identity; semantic splits, merges and replacements require explicit relationships and revised mappings.

### Execution and storage

- Use Mountainash relations/contracts and storage integration; the selected persistent store is local DuckDB through `mountainash-data`. Keep NumPy/SciPy capital calculations independent of persistence.
- Consult the actual installed/local Mountainash APIs and backend capabilities before implementing an integration. The dependency's documentation does not prove every conformance or transaction path is supported.
- Silver reads saved Bronze. Full regeneration is the primary workflow; incremental upserts must yield the same logical result.
- Keep definitions, mappings, curated corrections and rebuild manifests outside disposable Silver. A manual Silver edit alone is not a durable correction.
- Version interpretations and preserve source-effective dates separately from revision history. Mutable canonical classifications and database-generated IDs are not sufficient durable observation identities.
- Validate candidate revisions before atomic publication. Handle removal, splitting and merging as well as updates; preserve source lineage and avoid double-counting comparative evidence.
- Gold identifies the Silver revision it consumed and must be regenerated when its dependencies change.
- Apply [emergent analysis and selective persistence](docs/01.principles/a.architecture/emergent-analysis-and-selective-persistence.md): do not create core entities or mandatory storage for every possible reconciliation or inference. Compute exploratory relationships as needed, retain useful outputs with reproducible inputs and assumptions, and promote reusable definitions when research warrants them. Missing evidence or unexplained analytical residuals do not automatically indicate extraction errors.

## Verification and maintenance

Use verification appropriate to the actual change: check links and indexes for documentation; source-backed golden comparisons for extraction; conformance and rebuild behaviour for Silver. Discover commands from the project's configuration when it exists rather than copying Mountainash's development commands.

Preserve unrelated user work. Keep exploratory artifacts clearly labelled and distinguish them from production Bronze, approved golden fixtures and implemented contracts. When changing this guidance, retain links to authoritative principles instead of duplicating their status inventories here.
