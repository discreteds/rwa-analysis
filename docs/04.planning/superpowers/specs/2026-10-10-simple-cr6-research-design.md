# A simple four-bank CR6 research workflow

Date: 2026-10-10

Status: **Approved for local execution.** [PR #1](https://github.com/discreteds/rwa-analysis/pull/1) is a working demonstration, not a merge candidate. The [previous plan](../plans/2026-10-10-cr6-bronze-to-silver.md) records how that demonstration was built.

## 1. The ask

Extract four mortgage disclosure tables faithfully, tag their meaning, transform them through Mountainash into a rebuildable DuckDB dataset, and recreate the tables so the researcher can inspect the result.

Selected sources: CBA June 2025 and Westpac, NAB and ANZ September 2025, using the already reviewed Australian mortgage CR6 blocks. The expected selection is 36 source rows and 432 measure positions. ANZ's block is AIRB; this does not mean all ANZ-group mortgages. CBA's date remains distinct from the September cohort.

The durable [project principles](../../../01.principles/README.md) still apply. The simplification is in implementation: a direct research workflow, with small explicit data structures and transformations that can be read end to end.

## 2. Preserve the working shape

```text
PDF → bespoke extractor → saved Bronze
                              │
                  selected semantic mappings
                              │
                 Mountainash dataset relations
                              │
                  validated DuckDB Silver
                              │
                 source-shaped dataframes
```

The [original spike](../../../00.ideation/2026-10-10-layered-model-feasibility-spike.md) established the key transformation shape: prepare one source frame per dataset, apply expressions across its rows, and materialize at the persistence boundary. Keep that shape when implementing the real workflow. A different shape needs a demonstrated reason and researcher agreement.

PR #1 supplies the existing four working extractors, source contracts, complete independently authored goldens, populated metadata/catalogue, saved Bronze and storage integration. Reuse those assets and working interfaces explicitly; simplify the transformation and physical Silver projection without rebuilding the research foundation. The [asset inventory and reuse decisions](../../../00.ideation/2026-10-11-cr6-existing-assets-and-reuse.md) identify the exact paths and preserved artifacts. Its CLI, HTML renderer, heavier orchestration and seven-table physical layout are not requirements for the replacement.

## 3. Four extractors and a small Bronze contract

Each PDF keeps its existing reviewed `extract.py`, source review and golden set. Restore the scripts and their existing source-model/token-parser imports unchanged initially. They already own page selection, table geometry, headers and notes; no new extraction implementation is required absent a demonstrated defect.

The extractor returns a bundle of named typed datasets. For now each contains the selected CR6 block. Its rows have the twelve explicit financial fields already established in the [logical model](2026-10-10-initial-data-model.md#9-typed-domain-records-and-scope-of-implementation). Each value retains original text, Decimal/integer value, precision, missingness and source location. Shared metadata preserves context, both table axes, field bindings, bands, qualifications and aggregate/subset relationships.

Keep these agreed paths:

```text
extractions/<jurisdiction>/<bank>/<document-date>/aps330/
tests/bronze/<jurisdiction>/<bank>/<document-date>/aps330/
data/bronze/<jurisdiction>/<bank>/<document-date>/aps330/<version>/
```

One human-/LLM-authored golden per PDF compares the complete selected payload, including metadata. Expectations come from the PDF, independently of extractor output. Existing demo goldens can be retained after checking their source notes and compatibility with the simpler representation; changing the representation does not require inventing a new expected dataset.

Read and save Bronze through the existing mountainash-files integration and lossless envelope/codec. Reuse the four retained v1 bundles directly, preserving original producer metadata; do not introduce a new bare-payload format or regenerate v1. Source evidence remains distinct from later interpretation, and blank/dash/zero retain their differences.

## 4. Durable semantics, explicit mappings

Keep the existing Git-tracked catalogue files outside Silver: 18 concepts, ten measure definitions, one agreed interpretation and 88 scoped mappings selected by the retained release. Reuse their IDs, evidence and file format. A smaller execution projection can compile these entries into tables without replacing the authoritative knowledge. Revised definitions retain revision IDs and source-effective dates separately from revision history.

Mappings select an explicit document/dataset/field scope, with row exceptions where source evidence requires them. Each mapping records its target concept or partial meaning, unit conversion and supporting evidence/decision. A selected catalogue revision determines the rebuild inputs. Store those entries in readable files; a general inheritance or ontology-execution engine is unnecessary for these four sources.

Important present distinctions:

| Source evidence | Interpretation to preserve |
|---|---|
| CBA PD footnote | Period-end EAD weighting; does not automatically define LGD weighting |
| NAB mortgage agreements | Arrangement counts, distinct from money and other banks' unresolved counted entities |
| NAB CR6 overlay exclusion versus CBA inclusion | Different RWA bases remain visible |
| ANZ entity/AIRB perimeter and maturity note | Correct population and explained missingness |
| ANZ CMS2 overlay context | Cross-table evidence; equal totals alone do not establish CR6 treatment |

Unknown or conflicting meaning is a tagged research limitation. Source-backed percentages can still be converted while their weighting remains unresolved. A researcher decision records its rationale and evidence; it never becomes an invented source statement.

## 5. Mountainash owns tabular transformation

Python handles PDF parsing, dataclass/file encoding and orchestration. After preparing tables, Mountainash owns the tabular work: mapping joins, selection, unit conversion, band conversion, canonical projections, relationship projection and tabular validation. Polars/Arrow are interchange and materialization formats.

The implementation should visibly follow this sequence:

1. Load the selected saved Bronze and catalogue revision.
2. Prepare dataset-sized typed source and mapping tables once.
3. Build Mountainash relations that apply the selected mappings and conversions.
4. Validate the candidate through Mountainash contracts and relevant reference checks.
5. Materialize and publish through mountainash-data.

For CR6, a shared field conversion can be a Mountainash expression over the entire column. Where a mapping varies by row, join the applicable mapping data and use relation expressions. One relation per source record and an additional Python implementation of the same conversions are outside this design.

Use known source scales to produce base monetary units, percentage fractions and integral counts. `Decimal(22,8)` supports the researcher's stated 10-trillion domain; counts remain integers. Verify exact handling of these real units and bounds. Currency uncertainty alone does not invalidate a known scale conversion. An unavailable required conversion leaves the field explicitly `not_conformed` with its source value accessible.

Use supported public Mountainash APIs with a pinned compatible environment. The clean-install demonstration already provides evidence for working APIs; a dependency defect is surfaced upstream rather than hidden behind a new local framework.

Execution clarification: trust framework arithmetic and casts. Keep upfront parameter checks and contracts at layer transitions; do not embed precision guards, repeated numeric verification or a second ETL implementation inside the pipeline.

### A compact Silver shape

Three logical tables are sufficient for this first cut:

| Table | Contents |
|---|---|
| `cr6_observations` | One row per selected source row: stable observation ID, bank/entity/date/portfolio context, band/category/aggregate role, and twelve typed numeric columns |
| `cr6_fields` | One row per represented observation/field: availability, units, interpretation attributes, applied definition/mapping revisions, conversion and source occurrence reference |
| `cr6_relationships` | Source-backed parent/subset/aggregate links with endpoint scope and evidence refs |

Shared source metadata can be resolved from saved Bronze. Context and band attributes needed for analysis can be projected onto the observations. The [earlier E–R models](2026-10-10-layered-data-model.md) describe logical responsibilities, not a requirement to persist a separate table for each entity. Typed numeric values remain in the domain table; the fields table holds metadata.

Observation IDs derive from bundle/dataset/source-row identities, not mutable canonical classifications. A source occurrence additionally identifies field and Bronze version. All Silver tables identify their consumed rebuild revision. Source relationships remain separate from canonical concept relationships; a subset does not imply an exhaustive partition.

## 6. Rebuild is the ordinary operation

A small retained manifest names selected Bronze versions, the catalogue revision, code/environment/configuration versions and any curated corrections used. Keep it outside the disposable database. Use explicit saved versions for reproducible runs; Git supplies implementation and catalogue history.

Every rebuild constructs a fresh candidate from those inputs and publishes the three tables and its revision marker together in one DuckDB transaction through mountainash-data. Repeat execution replaces the selected result without duplicating it. Always rebuild when requested: an existing success marker is not proof that current tables are intact.

Removing an input removes its outputs on rebuild. Interpretation corrections update the selected catalogue revision. Extraction corrections produce new Bronze versions. Defer changed-grain tooling until an actual source correction requires it; that case must retain explicit old/new replacement lineage under the identity principle. Full replacement already prevents obsolete active rows from surviving a changed selection.

Missing inputs, broken references or failed conversions that violate the declared contract receive concrete diagnostics. Incomplete semantic knowledge and unexplained accounting residuals do not cause whole-dataset rejection. No standalone release-management service, cache/no-op policy, generic migration framework or incremental updater is needed for this workflow.

Ordinary experimentation can run in a modified checkout or without a Git repository. Code provenance is optional caller-supplied metadata; extraction, saving Bronze and rebuilding Silver never invoke Git or require a commit identifier. Git remains a development tool, not a runtime prerequisite.

## 7. Recreate the four tables as dataframes

Return a source-shaped Polars dataframe for each selected table, built with Mountainash expressions: source row labels/order, source column labels/order, and numeric values in the published units. Monetary/rate values remain exact Decimal, counts remain integers and missing values remain null. Original blank/dash tokens, displayed precision, qualifications and units remain available in saved Bronze; do not turn numeric columns into formatted strings merely to mimic a PDF.

Read actual persisted Silver numbers and reverse the recorded conversions through Mountainash, retaining exact values before any dataframe viewer rounds its display. Bronze supplies table structure and evidence, not substitute Silver numbers. Reuse the existing whole-unit, sub-display and missing-row test scenarios as dataframe assertions. Previously generated HTML/images remain historical reference only; no HTML generation, page rendering or browser review is required.

Orchestrate through ordinary Python calls to the existing extraction, manifest and rebuild functions and the dataframe reconstruction function. A short example script is sufficient; no CLI or application runner. The dataframes can be inspected directly in Python or a notebook. Retained data/manifests belong in project `data/`; follow the existing retention principle with ordinary file tools. No automatic dataframe export or new reporting artifact is required.

## 8. Prove the useful workflow

Use existing tools: four source goldens, Mountainash contracts, pytest, a real DuckDB transaction and reconstructed dataframes. Preserve the few discovered regressions at their owning boundary. The acceptance evidence is:

- All four complete source payloads match independently authored expectations.
- Saved Bronze preserves values and metadata, including a missing nested-field failure exposed in the demo.
- Dataset-wide Mountainash conformance preserves source-specific meaning and exact numeric conversions.
- Rebuild works from saved Bronze without PDFs, restores altered/empty Silver, and a failed publication preserves the previous result.
- Reconstructed dataframes retain source layout and exact source-unit values from persisted Silver, checked against the independent source expectations.

Write tests around these behaviors. Add another case when it protects a distinct source convention or demonstrated failure; avoid repeating generic decoder/guard checks across layers. Test count and per-task review count are not success criteria.

## 9. Keep, simplify, defer

| Keep | Simplify | Defer until needed |
|---|---|---|
| Four source-specific extractors and independent goldens | Source contract encoding to the few actual data shapes | Additional domains and periods |
| Durable concepts, definitions and evidence-backed mappings | Explicit selected mapping entries and joined tables | General mapping inheritance/rule engine |
| Dataset-wide Mountainash transformations | Three query-oriented Silver tables | Extra normalized projections without a current query consumer |
| Full transactional rebuild and source lineage | One retained input manifest; ordinary repeat execution | Incremental processing, publication caching and workflow services |
| Four reconstructed dataframes for research | Direct Python function calls | CLI, HTML reporting and UI machinery |

The next implementation should make one complete bank flow runnable early, then apply the same shape to the other three. Use the demo to avoid repeating source discovery and known mistakes. Any proposed departure from the validated Mountainash pipeline must explain the present need before adding code.

The researcher requested an [implementation plan](../plans/2026-10-10-simple-cr6-research.md) using this direction. Review that plan before starting the build.
