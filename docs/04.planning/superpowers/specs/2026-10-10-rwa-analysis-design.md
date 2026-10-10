# RWA analysis: single-user research platform

Date: 2026-10-10

Status: Approved architectural direction; written specification awaiting review.

Governing principles: [Principles and architecture](../../../01.principles/README.md). The collection captures durable decisions; this specification describes their intended implementation.

## 1. Purpose and scope

Build a Python research application to acquire Australian banks' APS 330 / Pillar 3 disclosures, preserve source evidence, extract mortgage risk observations, and calculate reproducible standardised capital metrics.

The governing objective is faithful capture and useful tagging, not perfect accounting. Partial semantic knowledge and unavailable detail are normal. Downstream research can use explicit assumptions, approximations and imperfectly aligned comparisons without discarding accurately captured source observations.

The initial user is a single researcher operating locally. Mountainash is the tabular analytics and data-access interface. A persistent DuckDB database holds structured observations and results. The project-root `raw/` folder holds source PDFs and `raw/index.md` catalogues them. Here `/raw` means this project's raw folder, not the filesystem-root directory.

The first evidence-to-Silver delivery covers Australian mortgage CR6 from CBA June 2025 and Westpac, NAB and ANZ September 2025, following the researcher's expansion of the original two-bank scope during implementation planning. The [CR6 implementation plan](../plans/2026-10-10-cr6-bronze-to-silver.md) owns that delivery; capital analytics and an end-to-end comparison follow separately. Historical coverage targets half-year observations over 2016–2026, limited to published, available disclosures. Broader acquisition follows a validated first slice.

Australian residential mortgages are the first portfolio implementation. The extraction and metadata model must accommodate other retail, non-retail and other portfolios, and other jurisdictions, as subsequent research requires. A single source file may disclose multiple portfolios and jurisdictions. Source documents, extraction datasets and their folder locations do not impose a single portfolio or exposure jurisdiction on their contents.

The platform also extends across data domains. Credit-risk distributions and capital analytics are initial consumers of a broader disclosure extraction capability. Future golden sets may request provisions, market share, lending balances, capital, liquidity or other information actually available in the reports. A data domain is independent of portfolio type and jurisdiction; an observation need not have a credit portfolio, PD band or regulatory approach to be representable.

The research hypothesis and mathematical definitions in `docs/00.ideation/initial_idea.md` remain the domain brief. This design replaces its initial PostgreSQL/SQLAlchemy-centred technology recommendation with a Mountainash-centred, local-first architecture.

## 2. System boundaries

One repository contains versioned agent workflow instructions and an installable package, `rwa_analysis`, with three independently understandable components:

1. **Disclosure processing:** agent-led discovery and retrieval, followed by LLM scrutiny of every PDF and LLM-authored bespoke Python extraction code for that file. Structured outputs and evidence references form the handoff to data processing. A shared extraction library grows from recurring needs across these per-file extractions.
2. **Data preparation:** Mountainash contracts, persistence, normalisation, validation and semantic tagging through a durable, versioned catalogue. Analytical selection is task-specific.
3. **Capital analytics:** pure numerical functions for mortgage capital, PD Differentiation Benefit (PDB) and subsequent sensitivity and decomposition methods.

Capital functions accept numerical arrays and explicit parameter sets. They do not fetch documents or query a database. Application orchestration selects and materialises analytical inputs through Mountainash, invokes numerical calculations, and persists the results and lineage.

The medallion architecture describes data quality and lineage, not a requirement to automate every stage in deterministic code. Agent instructions are first-class workflow assets. Discovery and downloading are agentic. For extraction, the LLM scrutinises each document and constructs a bespoke Python extractor; the saved extractor can then be rerun. Build shared extraction components when the accumulated catalogue demonstrates recurring needs. Reproducibility begins with retained sources, saved extraction code and versioned structured observations; it does not require replaying web searches or reproducing an agent's decisions exactly.

```text
Official archives / targeted web searches
                    |
         Agent-led source discovery
                    |
         Retrieval and classification
                    |
    /raw: source PDFs and index
                    |
    Bronze: per-script outputs by jurisdiction/org/date
                    |
    Silver: conformed observations and interpretation tags
                    |
     Gold: analytical datasets and results
                    |
       Source-traceable charts and exports
```

## 3. Technology choices

| Responsibility | Choice |
|---|---|
| Runtime and dependency management | Python 3.12+, uv and a committed lockfile |
| Tabular selection and transformations | Mountainash relations and expressions |
| Tabular schemas and validation | Mountainash TypeSpec, conformance and data contracts |
| Extraction output models | Python dataclasses representing the target data schema, evolved from real per-file extractions |
| Database access and writes | mountainash-data, backed by persistent DuckDB |
| Structured artifact I/O | mountainash-files |
| Discovery and downloading | Versioned agent instructions using available search/browser/download tools |
| Original document storage and catalogue | Project-root `raw/` with readable PDF filenames and `raw/index.md` maintained by the agent |
| Numerical calculations | NumPy and SciPy |
| Configuration and command inputs | Pydantic |
| PDF extraction | LLM scrutiny of each PDF, followed by a bespoke Python extractor per file using PDF/table tools and shared extraction components where applicable |
| CLI and charts | Typer and Plotly |
| Verification | pytest and Ruff |

Pin a compatible set of Mountainash ecosystem revisions. Optional local editable overrides support ecosystem development without making sibling checkout paths a requirement for reproducible runs.

Mountainash capabilities must be checked against the pinned revisions. The first integration milestone verifies decimal round-trips, required relations, contracts, persistence and transaction behavior. Application code uses public interfaces. Any uncovered ecosystem capability needed by the milestone is recorded explicitly before changing the design or adding a workaround.

Polars or Arrow may be used as interchange/materialisation formats. Shared tabular business logic is expressed through Mountainash. SciPy owns the normal CDF/inverse-CDF and other numerical methods at the calculation boundary.

## 4. Discovery and source acquisition

### 4.1 Agent workflow and source index

Maintain `raw/index.md` as the source catalogue. Initial institutions are CBA, Westpac, NAB and ANZ; subsequent expansion includes Macquarie and ING Australia where relevant. Useful archive links and discovery notes can be included in the same index or the agent workflow instructions.

An agent follows a documented workflow to find the requested disclosures, save the PDFs and create or update the index. Bank-specific notes can guide the agent without requiring a discovery adapter, candidate database or search-provider integration.

Search official investor-relations and regulatory-disclosure archives first. Targeted web searches supplement archives for historical documents or changed locations. The acquisition deliverables are the saved PDFs and updated index.

### 4.2 Reporting cadence

Half-yearly is the target research sampling cadence. Acquisition records actual reporting dates and publication dates separately. Banks may have quarterly disclosures, different financial year-ends or relevant supplementary reports.

Do not infer equivalent periods from filenames or labels such as "H1" alone. Analytical selection records the actual dates and reports any mismatch. A downloaded disclosure without mortgage PD-band data can remain useful evidence but is not eligible for the first PDB calculation.

### 4.3 Save and index

Save PDFs in `raw/` under readable filenames such as `cba-2025-06-30-aps330.pdf`, using the actual reporting date. Each index entry includes bank/reporting entity, reporting date, document title, a relative link to the saved file and the source URL. Add links to the document review and bespoke extractor as these become available. Unknown metadata remains explicitly unknown rather than inferred from a filename alone.

Check the existing index before downloading to avoid unnecessary repeat work. If a revised edition is deliberately retained, give it a distinct readable filename and note the relationship in the index. Keep source PDFs as downloaded.

No checksum, content-addressed naming, file-identity proof, acquisition manifest, registration utility or retrieval-attempt database is required. Finding and saving the disclosure and updating `index.md` completes acquisition.

### 4.4 Coverage

Use index notes to record requested periods that were not found or could not be downloaded. A failed search is not proof that a disclosure does not exist. Downstream coverage reports add extraction and analytical availability from processing results; acquisition itself needs no operational tracking subsystem.

### 4.5 Per-document LLM review and bespoke extraction

Every saved PDF is individually scrutinised by an LLM before its extractor is constructed. Similarity to an earlier bank or reporting period can guide the review but does not replace it.

For each document, retain a review in `extractions/<jurisdiction>/<org>/<reporting-date>/<extraction-id>/review.md` identifying:

- Relevant PDF page numbers, and printed page labels where different.
- Table titles, headings and the particular rows/columns to extract.
- Reporting entity, date, portfolio scope, regulatory approach and default status.
- Units, weighting conventions, band definitions, footnotes and cross-page continuations that affect interpretation.
- Expected target fields, disclosed totals useful for reconciliation and unavailable or ambiguous information.
- Organisation/date-specific segmentation metadata: band counts, source labels, ordering, lower and upper bounds, boundary inclusivity, units, default buckets and aggregation roles.

Extraction development has two streams for each document: a human- or LLM-authored golden set drawn directly from the reviewed source tables, and an LLM-authored Python extractor. Golden sets evolve as additional data is required. Create or extend the golden set and its unit tests before iterating on the script. The LLM constructs `extract.py` alongside the review specifically for that file. It may reuse established helpers, but owns the document's page selection, layout interpretation and mapping. Run the tests against the golden set and iterate on the script until the current extraction contract passes. Record unresolved limitations explicitly.

Each extractor emits instances of the shared target-schema dataclasses, retaining source references and original values alongside interpreted fields. Persist these as a structured Bronze dataset organised by jurisdiction, organisation and reporting date. Each extraction script corresponds to exactly one logical Bronze dataset, and every Bronze dataset identifies its producing script. A dataset may contain multiple related tables from that script. Bronze is the input to Mountainash conformance into Silver; extraction does not itself establish cross-bank comparability or publish Silver observations.

### 4.6 Evolving the extraction library

The catalogue consists of saved PDFs, per-file reviews, executable extractors and source-checked outputs. As it grows, improve `src/rwa_analysis/extraction/` by drawing reusable components from demonstrated common needs. Prioritise dataclasses representing the target data schema, followed by recurring parsing, provenance and reconciliation helpers. Per-file layout choices remain with the bespoke extractor unless actual reuse warrants moving them.

Start with the minimal dataclasses needed for the first documents, informed by the domain brief: source locations, reporting context, metric definitions and domain-specific records, with portfolio context, segmentation/band definitions and totals where applicable. Mortgage-specific fields and calculations build on these shared concepts; they do not define the shape of every future portfolio or data domain. Refine the models against subsequent disclosures. Distinguish absent values from zero and retain units, weighting and source context. Add domain/portfolio-specific structures as source evidence requires them rather than prebuilding every future domain or a universal bank/layout framework.

Dataclasses are the Python output contract for extraction; Mountainash contracts govern the corresponding persisted/tabular representation. Maintain an explicit conversion between the two. When shared models or helpers change, rerun affected saved extractors against their source-backed expected outputs and update the callers or preserve a documented schema version.

Use a shared context/provenance layer with typed domain-specific records, avoiding both a mortgage-shaped universal record and a single opaque metadata dictionary. Add domain records and their tabular contracts when golden-set requirements establish the fields and grain. For example, provisions may be disclosed by accounting stage and portfolio at a reporting date, while market share requires its market/geography, numerator, denominator, unit and observation date or period. Preserve accounting ECL/provisions separately from regulatory expected loss. Store market share as reported only when disclosed; a ratio computed from other data belongs to an explicitly identified derivation.

### Organisation/date-specific extraction metadata

Metadata describing a disclosure's structure is a first-class extraction output, with the same importance as numerical values. Each Bronze dataset includes typed reporting context and segmentation definitions alongside its observations. The golden set covers both.

Scope a segmentation definition by organisation/reporting entity, observation date, source document/table, portfolio, regulatory approach and breakdown. Organisation and date alone are not sufficient: a single report can contain multiple portfolios, alternative breakdowns and comparative periods with different structures. Preserve the document reporting date separately from each table's observation date.

Represent source reporting jurisdiction separately from portfolio/exposure geographical scope, entity domicile and the jurisdiction of the applicable regulatory rules. A portfolio can cover multiple countries or a disclosed aggregate region; do not force it into one country or duplicate its amounts into each included country. Where a source provides jurisdiction-specific rows, retain their separate contexts and any explicit aggregation relationship. A table's scope can apply to a block of rows, but each observation must resolve unambiguously to the context that governs it.

Extract or explicitly derive:

- Organisation and reporting entity; reporting jurisdiction and disclosed portfolio/geographical scope as distinct concepts.
- Document reporting date, table observation date and any performance-period start/end dates.
- Source table identifier/title, original portfolio label, regulatory approach and segmentation dimension (initially PD).
- Ordered source band labels and stable identifiers within that segmentation.
- Lower and upper bounds, lower/upper inclusivity and the source unit. Preserve an explicitly unbounded endpoint separately from a missing or unresolved bound.
- Band kind, including interval, default category and any other explicitly disclosed category. A default bucket is not forced into a fictitious non-default interval.
- Number of non-default bands, number of default bands and total band rows, excluding totals/subtotals. Keep total/subtotal row counts separately. A count derived from extracted rows is labelled as derived; a count explicitly stated by the source remains separately identifiable.
- Whether the breakdown is mutually exclusive and complete for its stated portfolio, with source support or an explicit unresolved status.
- Metric units, weighting and denominator conventions, relevant footnotes and missing-value meanings where established.
- Metric-specific counting unit (for example agreements versus counterparties), source exposure basis, displayed precision, overlay/floor treatment and whether values are disclosed at band or portfolio grain.
- Source PDF page and printed page label separately, plus original table row numbers and column identifiers where present.

Preserve the source representation in Bronze: for example, `0.15 to <0.25` with unit `percent`, bounds `0.15` and `0.25`, inclusive lower and exclusive upper. Silver may convert those bounds to probability fractions while retaining their source definition. Do not infer a missing bound or inclusivity from another bank's conventions.

For the inspected 2025 mortgage CR6 blocks, the initial expected metadata is seven non-default interval bands, one default category, eight band rows and one total/subtotal row. These are source-backed expectations for those particular tables, not hard-coded defaults for an organisation or all future disclosures. Repeated source structures may share reusable parsing code, but each dataset retains its applicable definition and date.

Numerical observations reference their segmentation and band identifiers. Changes in band count, boundaries, units or reporting scope remain inspectable across periods and become explicit inputs to Silver conformance and analytical comparability. A changed classification must not silently inherit a previous period's definition.

The [NAB/ANZ source review](../../../00.ideation/2025-nab-anz-metadata-spike.md) supplies concrete cases the evolving schema must represent:

- NAB's mortgage borrower count measures agreements; ANZ warns that borrower definitions vary by portfolio.
- NAB CR6 excludes RWA overlays, whereas CBA CR6 includes them. Reconciliation across tables requires compatible measurement bases.
- ANZ's Level 2 reporting entity, AIRB mortgage portfolio, standardised Suncorp exposures and NZ mortgage portfolio are distinct contexts.
- NAB's BNZ mortgage CR9 block displays five non-default bands. Retain observed omissions without inventing zero-exposure rows or extending neighbouring boundaries; distinguish displayed-band coverage from proven portfolio completeness.
- Currency, geographical scope and reporting jurisdiction are independent. NZ portfolios inside an Australian disclosure can be reported in AUD.
- Backtesting lookback and default/cohort conventions are scoped to the relevant metric and portfolio, not inherited indiscriminately across the report.

Definitions and qualifications can come from introductions, footnotes, appendices or related tables. Preserve those source links alongside the values they qualify. Golden-set tests must distinguish a metadata mismatch from a numerical mismatch and allow both to drive schema evolution.

### 4.7 Two-stream extraction and golden-set-driven development

**Stream A — human/LLM golden-set authoring:** a human or LLM creates and updates expected structured records by scrutinising the document's selected pages and tables. The golden set is a living specification of the data required from that document. Authors record source locations, original values, units, missingness and relevant interpretation notes. This stream reads the PDF directly and does not derive expected values from the Python extractor or the helpers being tested. Shared dataclasses represent the output shape and evolve when new golden-set requirements need additional fields or record types; they do not supply the expected values.

Save the resulting golden set under `tests/bronze/<jurisdiction>/<org>/<reporting-date>/<extraction-id>/golden.json`, alongside its source/interpretation notes. It covers all selected rows and fields in the declared extraction scope, including relevant totals and missing values. Decimal quantities are represented losslessly. Unresolved cells are explicitly recorded rather than guessed.

**Stream B — scripted extraction:** execute the bespoke Python extractor against the same PDF and compare its structured output with the saved golden set. Unit tests protect the observable extraction contract: row coverage and identity, values, units, band boundaries, missingness and source references. Assertions should report the affected table, row and field. Use explicit tolerances only where the field's interpretation requires them; directly transcribed decimal values should match exactly. Ignore incidental runtime metadata such as execution timestamps.

Compare the organisation/date/table context and segmentation metadata as well as the values. A numerical match with the wrong observation date, band inclusivity, unit or default classification is a failed extraction. Assert the source-backed expected band counts independently of the extractor's derived counts so a missing row cannot pass merely because both the output rows and its reported count were reduced together. When requirements expand, golden sets can add metadata as well as new numerical fields.

The LLM authors and runs these tests, observes meaningful failures and iterates on the extractor to resolve them. Tests exercise the actual extraction entry point, rather than mocked extraction output or helper internals. Failures such as dropped rows, shifted columns, incorrect percentage conversion or lost footnotes must be detectable. Shared comparison utilities avoid duplicating assertion logic across the catalogue.

Golden sets remain editable throughout the research project. Humans and LLMs may extend them with additional metrics, rows, tables or contextual fields as research needs grow, as well as correct existing entries. They are saved and versioned so each test run has explicit expectations; this does not freeze their scope. Ordinary pytest execution reads the saved version without calling an LLM or regenerating expected values.

The evolution loop is: identify additional data needs → inspect the source → extend the golden set and its scope notes → extend the tests and target-schema dataclasses where needed → observe meaningful failures → update the bespoke extractor and useful shared components → rerun affected tests → publish a new Bronze output version and reconform affected Silver data. Existing expectations remain covered unless the intended scope is explicitly revised. A test must compare the newly requested fields, not silently ignore them because an older dataclass or comparator does not recognise them.

When a mismatch exposes an error in the golden set, a human or LLM re-reads the source and corrects the fixture with a source-backed explanation; expected values are not changed merely to match the script. Schema changes preserve independently established source values while updating their representation. Both human- and LLM-authored expectations can be corrected through this process.

An extractor's tests own its complete source-to-structured-output comparison. Separate shared-helper tests are added only for distinct reusable behavior not already adequately covered. Changes to shared dataclasses or helpers trigger the affected extraction tests; broader changes affecting all extractors trigger the full extraction suite.

## 5. Medallion layers

### 5.1 Raw sources and Bronze extraction datasets

`raw/` contains original PDF files and `raw/index.md`. Bronze contains the structured outputs of the bespoke extraction scripts:

- References to source PDFs in `raw/` and their index entries.
- Raw extracted tables and cell text.
- Page, table, row and column references; coordinates where available.
- Associated headings and relevant footnotes.
- Organisation/date/table-specific reporting context, segmentation definitions, band counts, bounds, inclusivity, units and row roles, linked to the extracted observations.
- Per-file review and extractor references, extraction schema version, tool/code versions where available, workflow instruction version, run identifier and diagnostics. Record the authoring model identifier where available and relevant task instructions.

Extraction runs are separate from document retrievals. A PDF can be re-extracted without re-downloading it. Original values and previous extraction attempts are retained.

Bronze datasets are organised as `data/bronze/<jurisdiction>/<org>/<reporting-date>/<extraction-id>/`. The matching script lives at `extractions/<jurisdiction>/<org>/<reporting-date>/<extraction-id>/extract.py`, alongside its review. Here the path's jurisdiction is the source disclosure's reporting jurisdiction, and the date is the document's reporting date, not the download or execution date. The organisation key identifies the reporting organisation. Portfolio jurisdiction, regulatory-rule jurisdiction, specific entity and table observation date remain explicit in the records and may differ from the path keys.

The shared path keys establish a one-to-one relationship between an extraction script and its logical Bronze dataset. An extraction ID distinguishes multiple documents or extractions for the same organisation and reporting date. Reruns or code revisions are versions of that same dataset, with output versions retained beneath it; they do not create unrelated catalogue entries. Where several tables are extracted, they form one dataset bundle rather than independent datasets with ambiguous script ownership.

A single file's extractor may emit several portfolio/jurisdiction blocks into its one Bronze dataset. For example, an ANZ APRA disclosure stored under `au/anz/` may emit both Australian AIRB mortgage observations and RBNZ-regulated NZ mortgage observations, with AUD as the reporting currency for both. Retain their separate portfolio contexts in the same bundle rather than duplicating the source dataset under a second jurisdiction folder. The human/LLM golden set and mirrored test directory cover all selected blocks from that extractor. Silver can subsequently select, conform and combine records by their actual portfolio/jurisdiction metadata while preserving their shared source lineage.

The same bundle may also contain multiple data domains, represented as named typed record collections or related tables. Adding provisions, market share or another selected disclosure expands the file's golden set and extractor; it does not require a new source download or a duplicate domain-specific source bundle. Golden expectations and diagnostics identify domain/table/record/field, and conformance operates through the applicable domain's Mountainash contract. No universal PD-band or portfolio requirement applies to the bundle as a whole.

The LLM interprets each layout and writes its bespoke extractor. Running that Python code produces the structured extraction artifacts. The handoff contract requires source locations and original values. Schema and source-backed golden checks validate faithful capture; reconciliation is diagnostic unless established semantics and precision justify an exact constraint. A revised extractor produces a new extraction version rather than overwriting prior observations.

### 5.2 Silver: conformed and semantically tagged observations

Silver is produced by conforming versioned Bronze extraction datasets through Mountainash using selected semantic catalogue and mapping revisions, interpreting evidence without replacing it. Silver reads saved Bronze rather than reopening PDFs or rerunning extraction. Full regeneration from empty candidate tables is the primary workflow. Partial mappings and unresolved semantic attributes remain publishable with tags. Silver may combine multiple Bronze datasets while retaining their individual lineage and scope differences:

- Canonical concepts, measure-definition revisions, units, currencies and denominator conventions where established; source metadata remains available when canonical interpretation is partial.
- Reporting entity, date, regulatory approach and portfolio scope.
- Original and canonical portfolio labels, connected by versioned mappings.
- Explicit PD-band boundaries, units, inclusivity and open-ended ranges.
- Source row/column roles and canonical roles where mapped, including explicit subset/aggregate relationships and multi-level header paths.
- Defaulted/non-defaulted classification.
- Missing-value reasons, validation outcomes and source references.

Each segmentation belongs to a disclosed breakdown. Exact portfolio aggregation requires supported coverage and disjointness; parent rows and their subsets are not additive siblings. PD, LVR and borrower-type breakdowns are not combined as if they were disjoint exposures. Analyses can use incomplete breakdowns or approximate alignment with explicit selection and assumptions, without relabelling inferred results as published totals.

Corrections belong to durable inputs: extraction fixes produce new Bronze versions, semantic fixes revise catalogue/mapping decisions, and source restatements retain new published evidence. Record reasons and supersession relationships. A manual Silver-only edit is not a durable correction. Mapping and observation versions remain addressable after correction.

Observed/derived/estimated status, verification status and extraction confidence are separate concepts. Statistical uncertainty belongs to estimated analytical results, not to extraction confidence.

Validation includes unit and percentage interpretation, reference and band validity, and source-appropriate checks on EAD/RWA, density and weighted PD. Reconciliation tolerances reflect disclosed rounding and scope. A check that cannot be performed is distinguished from one that passed; analytical residuals and absent definitions are not automatically extraction errors.

Structural defects require correction; partial semantics and ambiguous mappings remain inspectable and tagged. Analytical suitability is task-specific, with assumptions and limitations visible. There is no universal comparable/not-comparable gate on source observations.

Keep Bronze versions, semantic definitions, mappings, curated corrections and rebuild manifests outside disposable Silver. Each manifest identifies input versions and conformance code/contracts/configuration. Validate a candidate revision and publish atomically through supported transaction/staging mechanisms. A failed rebuild leaves the prior revision available. Incremental upserts are later optimisations and must yield the same logical result as a full rebuild. Gold outputs identify their Silver revision and become stale when their dependencies change.

### 5.3 Gold: versioned research products

Initial products:

1. Disclosure and metric coverage by bank and reporting date.
2. Selected mortgage portfolio observations with comparability tags and explicit analytical assumptions.
3. Native-band exposure-weighted PD distributions.
4. Standardised mortgage risk weights, PDB and absolute differentiation benefit.
5. A two-bank comparison chart and reproducible data export.

Gold input manifests reference exact Silver versions. Each calculation records function version, parameters, code revision, dependency/environment identifier and relevant eligibility/mapping versions. Re-running identical inputs must reproduce numerical results within a declared numerical tolerance; operational timestamps and run IDs may differ.

Distribution reconstruction, common-band estimates, statistical inferences and modelled capital allocations belong here. They are labelled separately from observed disclosures. Published bank RWA and theoretical standardised RWA remain distinct measures.

## 6. Logical data model

The consolidated model is detailed in [Initial disclosure data model](2026-10-10-initial-data-model.md), with [worked CR6, CR1/CR2 and LIQ2 examples](2026-10-10-data-model-worked-examples.md). It separates source capture, the durable semantic catalogue and rebuildable conformance. A general CR6 `CreditRiskExposureRow` remains the first production domain record; the consolidated logical contracts await written review.

The [layered E–R models](2026-10-10-layered-data-model.md) make that boundary explicit: `BronzeCreditRiskExposureRow` retains source-form values and bindings; `SilverCreditRiskExposureObservation` has conformed typed columns with revision-scoped context, per-field interpretation and source lineage. Canonical definitions and mappings are durable catalogue inputs, not owned by disposable Silver. These proposed layer-specific contracts await review.

The initial model comprises the following groups. Physical schemas are versioned by application-owned migrations executed through the storage boundary.

| Group | Principal records |
|---|---|
| Operations | Processing runs and stage outcomes; acquisition is catalogued in `index.md` |
| Semantic catalogue | Stable concepts and relationships, measure definitions, researcher decisions, framework/parameter versions |
| Evidence | Source file, extraction run, published field, axes/header paths, qualifications and source relationships |
| Observations | Typed domain records/values, breakdown, segment membership, band definition and source lineage |
| Interpretation | Contextual mapping revisions, corrections, interpretation tags and validation outcomes |
| Retained analysis | Selected input manifests, calculations, outputs and assumptions when useful; not a mandatory record of every exploratory result |

Source values are addressable through their dataset, typed record and field, including non-cell locations for narrative observations. Effective meaning combines dataset context, row definition, column definition and qualifications. A source row can contain multiple measure types or identify a particular stock/flow measure. Preserve merged spans and subset relationships rather than forcing every source into one rectangular grain. Important quantities and dimensions use typed fields; JSON may hold source metadata or complete run configuration.

Store source quantities as decimal/fixed-point values with explicit units. Convert to floating point deliberately when preparing numerical inputs. Identifiers remain stable; revisions and run identifiers distinguish history. Referential and uniqueness requirements are enforced through database facilities where supported and application contracts where necessary.

## 7. Initial analytical contract

For a selected non-defaulted portfolio, require:

- EAD for every included band, with positive total EAD.
- EAD-weighted mean PD for each included band.
- Sufficient evidence that the bands cover the selected portfolio without double counting.
- Explicit common LGD and capital-function parameters.

Reported RWA, risk-weight density and LGD are retained when available for reconciliation and comparison. They are not substituted for missing mean PDs.

Calculate weights from EAD and compute:

```text
mean_pd = sum(weight_i * pd_i)
rw_uniform = f(mean_pd)
rw_grouped = sum(weight_i * f(pd_i))
delta_rw = rw_uniform - rw_grouped
pdb = 1 - rw_grouped / rw_uniform
```

A zero uniform benchmark yields an explicitly undefined PDB, not a fabricated zero. Defaulted exposures are analysed separately. Capital functions declare their valid inputs and boundary treatment.

Common PD bands are not required to compute each bank's grouped PDB. Preserve native bands initially. Differences in granularity affect interpretation and must accompany comparisons. A grouped result is described as a lower bound only under the applicable concavity and accurate-band-mean assumptions. Floors and regulatory overlays must not inherit an unfloored function's concavity claim automatically.

## 8. Execution, idempotency and failures

Stages have explicit handoffs: discover, acquire, scrutinise, construct/run the per-file extractor, normalise/validate, analyse and report. Discovery and acquisition are agent workflows producing PDFs in `raw/` and `raw/index.md`. LLM review and extractor authoring produce saved review notes and Python code. Code exposes extraction execution, structured-data import, validation, transformation and analytical entry points. A convenience command regenerates the comparison from a pinned structured extraction/observation snapshot and its saved source references; it does not need to repeat discovery or LLM review. Saved bespoke extractors can also be rerun independently.

Code-driven processing records input observation/extraction versions, implementation version and configuration. Repeating a successful deterministic stage with identical inputs reuses its published output unless an explicit new attempt is requested. Agent extraction attempts retain distinct outputs and workflow metadata; their outputs are not assumed identical merely because instructions match. Failed processing attempts can be retried without duplicating published observations. These processing conventions do not impose identity checks or run tracking on source downloads.

Publish database outputs and successful processing status within one owned transaction. An unsuccessful processing stage cannot expose a partial dataset as a completed Silver or Gold version. Source PDFs are simply saved and linked from the index.

The initial execution model has one writer. Agent instructions coordinate exploratory work; CLI commands coordinate repeatable data processing. Saved PDFs, the index and structured extraction outputs connect them. Processing logs retain failures and actionable diagnostics.

## 9. Repository and physical layout

```text
pyproject.toml
uv.lock
src/rwa_analysis/
    contracts/
    extraction/      # Shared target-schema dataclasses and proven reusable helpers
    normalization/
    storage/
    regulatory/
    analytics/
    reporting/
    cli.py
config/
    institutions/
    frameworks/
    mappings/
tests/
    conftest.py
    bronze/
        <jurisdiction>/<org>/<reporting-date>/<extraction-id>/
            golden.json
            golden-notes.md
            test_extraction.py
    fixtures/        # Shared fixtures only where useful
notebooks/
raw/
    index.md
    <bank>-<reporting-date>-aps330.pdf
extractions/
    <jurisdiction>/<org>/<reporting-date>/<extraction-id>/
        review.md
        extract.py
docs/
    00.ideation/
    01.principles/
    04.planning/superpowers/
    workflows/       # Agent instructions for discovery, acquisition and extraction
data/
    bronze/
        <jurisdiction>/<org>/<reporting-date>/<extraction-id>/
            <output-version>/...
    warehouse.duckdb
    gold/
        snapshots/
        reports/
```

DuckDB namespaces are `ops`, `bronze`, `silver` and `gold`. The `raw/` folder holds source documents; the jurisdiction/org/date-organised Bronze files hold the extraction outputs used for Silver conformance. Database Bronze representations, where useful, refer to those saved datasets and their producing scripts. Source PDFs and `raw/index.md` are currently tracked in Git, along with documentation; future review notes, extractors, dataclasses, golden sets and tests are versioned. The live warehouse, secrets and generated data are ignored. Durable generated Bronze versions and rebuild manifests still require retention/backup independently of disposable Silver. Keep catalogue definitions and decisions in versioned source files outside generated tables; physical catalogue paths are selected during implementation planning. Notebooks consume the package rather than owning reusable processing logic.

The hierarchy below `tests/bronze/` mirrors the logical dataset hierarchy below `data/bronze/`, through extraction ID. It does not duplicate output-version directories. This permits targeted pytest execution by jurisdiction, organisation, reporting date or individual extraction. Use pytest's importlib import mode so repeated `test_extraction.py` filenames can coexist without turning date-named folders into Python packages. Source PDFs must be available locally for these tests; missing PDFs produce a clear prerequisite failure rather than triggering network retrieval or silently skipping validation.

Example test commands (with illustrative dataset identifiers):

```bash
uv run pytest tests/bronze/au/
uv run pytest tests/bronze/au/cba/
uv run pytest tests/bronze/au/cba/2025-06-30/
uv run pytest tests/bronze/au/cba/2025-06-30/aps330/
```

Back up source files/index, retained Bronze versions, semantic catalogue/mappings, run manifests and implementation/configuration versions. A consistent closed/checkpointed warehouse is a useful snapshot but not a required input to reconstruct Silver. Retained Gold outputs can be regenerated from pinned inputs and code.

## 10. Delivery sequence and acceptance criteria

### A. Project foundation and Mountainash integration

Establish package tooling, configuration, contracts and storage connectivity.

Acceptance: a small disclosure-shaped dataset preserves decimal values, missingness and identifiers through storage and Mountainash querying; required validation works; a failed write transaction leaves no partially published dataset. Record the tested ecosystem revisions.

### B. Numerical core

Implement the baseline mortgage capital function and grouped PDB independently of acquisition.

Acceptance: independently sourced reference calculations agree within declared tolerances; uniform-PD portfolios have zero PDB; equal-mean portfolios with different distributions behave consistently with the function's applicable concavity; invalid inputs and undefined ratios have explicit outcomes.

### C. Discovery and trusted evidence

Write and follow an agent workflow to find suitable disclosures, save the PDFs in `raw/` and create/update `raw/index.md`. The initial selected sources are the already saved CBA June 2025 and Westpac/NAB/ANZ September 2025 disclosures. Individually scrutinise each PDF with an LLM and save its page/table review. Create and save independent golden sets, authored by a human or LLM, with source locations for the selected tables and the current data requirements.

Acceptance: all four PDFs are saved and linked in the index with their banks, reporting dates, titles and source URLs. The source-to-Silver slice retains all selected CR6 fields and partial interpretations. For a subsequent analytical comparison, establish sufficient non-defaulted EAD and mean-PD semantics for each selected input or record explicit assumptions; publication of faithful Silver does not require complete analytical suitability.

### D. Complete the medallion slice

Have the LLM construct unit tests from the saved golden sets, then develop a bespoke Python extractor for each document through the test-driven iteration loop. Establish the minimal shared target-schema dataclasses and refine them against both extractions. Implement extraction-output persistence, canonical mapping, reconciliation, analysis and reporting; draw additional shared helpers from actual common needs.

Acceptance:

- Scripted extraction outputs match the independently human- or LLM-authored golden sets across the currently declared rows and fields; discrepancies are resolved against the PDF evidence.
- Each extraction has a mirrored test directory and can be tested alone or as part of a jurisdiction, organisation or reporting-date subtree.
- Golden sets can be extended by humans or LLMs as new data is required; the added expectations drive test, dataclass and extractor evolution.
- Golden sets are saved independently of script output and ordinary test execution uses the selected saved version without LLM calls.
- Each PDF has an LLM-authored page/table review and a saved, executable per-file Python extractor emitting the shared target-schema dataclasses.
- Every extraction script has exactly one logical Bronze dataset, organised by jurisdiction, organisation and reporting date, with an unambiguous link back to that script.
- Bronze and the golden sets include reporting-context and segmentation metadata as well as values; tests detect wrong dates, band counts, bounds, inclusivity, units and default/total classifications even when the numerical values match.
- The shared extraction model supports multiple portfolios and jurisdictions in one script's Bronze bundle. The folder jurisdiction does not override record-level portfolio or regulatory-rule context; a golden-set expansion to another jurisdiction remains within the same extractor/dataset relationship.
- A source bundle can expand to other data domains without forcing those records into the mortgage schema. Each added domain has typed records, source-backed golden expectations and a corresponding Silver conformance contract; previously selected domains remain covered by tests.
- Silver conformance runs from saved Bronze datasets independently of PDF access or extractor execution and preserves Bronze dataset/version lineage.
- Source-appropriate reconciliation diagnostics retain tolerances and limitations; incomplete disclosures or unexplained analytical residuals alone do not prevent publication of faithful capture.
- Every analytical input is traceable to its source cell or explicit derivation.
- One command produces the two-bank comparison and coverage summary from pinned structured inputs, archived source references and assumptions, without rerunning agent discovery or interpretation.
- Repeating the run does not duplicate published data.
- A correction creates new Silver/Gold versions while prior results retain their original lineage.
- Full Silver rebuilds from pinned durable inputs preserve logical results independently of existing Silver rows; partial semantic mappings remain available with tags.
- Missing or rejected inputs produce visible coverage/eligibility outcomes rather than plausible-looking invented results.

### E. Historical expansion

Add banks and reporting periods incrementally, scrutinising each PDF and constructing its bespoke extractor. Evolve the extraction library, especially its dataclasses, from this growing catalogue and verify affected existing extractions when shared components change. Introduce common-band aggregation, distribution reconstruction, additional regulatory regimes and longitudinal analysis as separately scoped increments after the first slice is validated.

## 11. Verification strategy

Use independent numerical reference values and mathematical properties for the capital engine, the two-stream human/LLM golden-set and scripted-extraction workflow for extraction correctness and evolving data requirements, and focused integration tests against persistent DuckDB for data contracts, precision, idempotency and correction lineage. Routine tests are offline. Acquisition is complete when the requested PDFs are saved and the index is updated, with any missing periods noted. Identical search paths or agent outputs are not a test requirement.

The first slice validates only the selected backend and actual required operations. Broader backend portability is a later requirement. Each bespoke extractor is checked against its reviewed source tables. Shared dataclass/helper changes are checked against affected existing extractions; correctness is assessed at the structured-data handoff.

## 12. Next review boundary

Review this written specification before producing detailed implementation tasks. The implementation plan should begin with milestones A–D and leave broad historical scraping until the first full pipeline is working.
