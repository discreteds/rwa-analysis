# Initial disclosure data model

Date: 2026-10-10

Status: Consolidated design for review. Incorporates agreed principles and discovery; logical record shapes and binding representation below are the proposed first implementation contract, not implemented classes.

Parent: [Platform architecture](2026-10-10-rwa-analysis-design.md). Governance: [Principles and architecture](../../../01.principles/README.md).

Worked review: [CR6, CR1/CR2 and LIQ2 examples](2026-10-10-data-model-worked-examples.md).

**Layer-specific schemas and E–R diagrams:** [Bronze capture, semantic catalogue and Silver conformed model](2026-10-10-layered-data-model.md). This companion supplies explicit entity relationships, proposed layer-specific record names, Silver field conventions and Bronze-to-Silver examples.

Evidence: [CBA/Westpac](../../../00.ideation/2025-disclosure-spike.md), [NAB/ANZ](../../../00.ideation/2025-nab-anz-metadata-spike.md), [credit quality/provisions](../../../00.ideation/2025-credit-quality-provisions-discovery.md), [liquidity](../../../00.ideation/2025-liquidity-metadata-discovery.md).

## 1. Purpose and boundaries

Capture published data faithfully and tag what we understand. PDFs do not disclose every measure, dimension, cell or calculation input. Partial semantics, approximations and comparisons of related but imperfectly aligned measures are normal research conditions, not reasons to discard source observations.

The model has three connected parts:

1. **Source capture:** documents, source structure, typed domain records, values and evidence in versioned Bronze bundles.
2. **Semantic catalogue:** long-lived concepts, composable measure definitions, researcher decisions and contextual mappings, retained independently of Silver.
3. **Conformance:** Mountainash resolves and tags the selected evidence, applies justified conversions, and produces rebuildable Silver observations.

Reconciliations, residuals and inferred relationships emerge through analysis. Persist useful outputs selectively with reproducible inputs and assumptions; no universal reconciliation or inference entity is required.

Australian mortgage CR6 is the first production slice. Credit-quality and liquidity examples exercise shared contracts without committing to production extractors for every explored template. Use Python dataclasses and explicit Mountainash tabular conversions. A typed record for each supported domain shares context and provenance; neither a mortgage-shaped universal record nor an opaque metadata dictionary is the core model.

## 2. Relationships, identity and ownership

See the [Bronze E–R diagram](2026-10-10-layered-data-model.md#2-bronze-er-source-oriented-capture), [catalogue E–R diagram](2026-10-10-layered-data-model.md#3-catalogue-er-durable-semantic-knowledge) and [Silver E–R diagram](2026-10-10-layered-data-model.md#4-silver-er-the-conformed-cr6-domain) for cardinalities and proposed keys. The following is only a layer-dependency overview, not an E–R diagram.

```text
SourceDocument
    -> ExtractionBundle version
        -> ExtractedDataset[T]
            context + source rows/columns/header paths
            published fields + segmentation + source relationships
            typed records containing ReportedValue fields
            evidence + qualifications

Semantic catalogue revision
    concepts + concept relationships
    composable measure definitions
    interpretation decisions + source mappings
                       |
Selected Bronze versions + catalogue/mappings + conformance code/configuration
                       |
                 Silver revision
                       |
               research / Gold
```

One PDF's bespoke extractor owns one logical Bronze bundle. The bundle may include multiple domains, portfolios, jurisdictions and observation periods. Adding selected content extends its golden set and extractor rather than duplicating the PDF into domain-specific bundles.

The logical bundle key is the existing reporting-jurisdiction/org/document-date/extraction-ID path. Output versions belong to that bundle. Dataset, row, field, axis and relationship IDs are readable local identifiers; they do not require content hashes or registration machinery.

A source observation occurrence is addressable by bundle, dataset, record and field IDs, with output version selecting its revision. A row-oriented measure such as CR2 still has a typed value field. Source occurrences in repeated tables or later comparative documents remain separately addressable even when they support the same logical observation.

Use deterministic source keys that do not depend on current canonical labels, monetary values or generated database IDs. If a corrected extraction splits or merges source records, retain explicit replacement lineage rather than pretending the old grain is unchanged. Source IDs are not themselves proof that two published occurrences represent distinct economic amounts.

## 3. Source documents and extraction bundles

### SourceDocument

| Field | Meaning |
|---|---|
| `document_id`, `local_path` | Readable identity and project-relative saved PDF path |
| `organisation_id`, `reporting_entity` | Institution and disclosed legal reporting entity |
| `title`, `source_url` | Original title and acquisition source |
| `document_reporting_date` | Date of the report as a whole |
| `publication_date` | When known; distinct from reporting date |
| `reporting_jurisdiction` | Jurisdiction of the disclosure |

`raw/index.md` remains the acquisition catalogue. Populate structured source context during extraction; no new acquisition registration workflow is introduced. Retain deliberately acquired revised editions as distinct sources with their relationship recorded.

### ExtractionBundle and ExtractedDataset[T]

The bundle contains its document reference, extraction ID/script path, schema version, output version and named datasets. A dataset contains its context, relevant source structure and definitions, typed records and supporting evidence references. Related collections can persist as separate tables or structured files; this is not a requirement for one flattened universal table.

Paths remain:

```text
extractions/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/
data/bronze/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/<output-version>/
```

An `au/anz/` source bundle can contain NZ mortgage observations reported in AUD. Path keys never override dataset context.

## 4. Context, population and time

`DatasetContext` supplies dataset ID, domain, source template/title, reporting entity, consolidation scope, source portfolio label, geography, regulatory basis and applicable temporal context. Distinguish geography, entity domicile, reporting jurisdiction, rule jurisdiction and currency. Preserve aggregates over multiple countries as aggregates rather than copying their value into each country.

Rows and fields contribute explicit context where needed. A coherent CR2 schedule can contain opening stock, movements and closing stock; it does not force every record to inherit one snapshot date. Separate comparative blocks may instead become distinct datasets. Either representation must resolve each selected observation's source period unambiguously where disclosed.

Temporal roles include snapshot, opening snapshot, closing snapshot, reporting interval, averaging window and cohort anchor/outcome window. A stress or model horizon is a separate definition attribute, and residual maturity is a segmentation dimension. Do not collapse these into one generic period.

Actual dates belong to observation context; reusable rules such as “12 months following the anchor” belong to definitions. Preserve source date labels and the basis for any derived dates. An unknown boundary or calendar convention stays unknown.

Population selection combines shared context, row/column segment membership and applicable inclusion rules. CBA's PD definition can apply to seven non-default bands, one default-only band and their combined aggregate without asserting the same default population for every cell.

## 5. Source axes, published fields and relationships

### Source structure and binding

Keep lightweight source descriptors rather than a full PDF rendering model:

- `SourceAxisItem`: local ID, row/column axis, source label/identifier, order, header-path references, applicable context/qualification references and source location. Section headings can be axis descriptors without pretending to contain numeric values.
- `PublishedField`: local ID, source measure label or header path, source units/scale where disclosed, and applicable source qualifications. It describes the published field, not a global canonical metric.
- `ValueBinding`: identifies a typed record field and its published-field/row/column descriptors, relevant context and qualifications. Common CR6 bindings can be shared at dataset-field level; row-defined measures use explicit row bindings.

This replaces the earlier single `MetricDefinition`, which mixed source presentation, canonical concepts and interpreted conventions. Bindings resolve meaning from both axes without making every value a generic key/value record.

`SourceReference` identifies a document, one-based PDF page and printed page label, with optional table, row, column, header, paragraph, footnote and bounding-box locations. It can reference multiple source columns as a span. A narrative value does not require a fabricated table cell.

Merged totals are one observation. A value spanning maturity columns is not duplicated and is not assigned to the nearest visible header. Its semantic scope can be an unsegmented total even when its source location covers only part of the printed grid.

### SegmentationDefinition and BandDefinition

A segmentation contains its local identity, source dimension, ordered bands/categories, applicable context and evidence, plus coverage and mutual-exclusivity information where known. Canonical dimension mappings are separate.

A band has identity, source label/order, interval/category/default kind, unit and applicable bounds/inclusivity. Explicitly unbounded, unresolved and non-applicable endpoints remain distinguishable. A `100.00 (Default)` PD category is not an ordinary interval; `No maturity` is a named category, not a missing value or a zero-duration interval.

Expose derived counts of non-default bands, default categories and aggregate rows separately. Golden sets independently specify expected counts. Source-stated counts, when present, retain their own evidence. Preserve omitted template bands where a template expectation has been established, without filling them with zero exposures.

### SourceRelationship

Capture disclosed `of which`, `comprising`, parent/child and total relationships across either axis. Each relationship has an ID, source label, parent/child references, scope and evidence; known exhaustive coverage or mutual exclusivity is additional information, not an automatic property of a subset link. References can target rows, fields or source blocks. A shared column relationship need not be copied into every cell.

Relationships can form multiple levels and need not describe a strict partition. Keep the source hierarchy separate from canonical `ConceptRelationship` records. Equal values do not establish identity; numbering or indentation alone does not establish parentage where meaning is unclear. Retain uncertain source structure as a qualified interpretation rather than inventing aggregation rules.

These links prevent double-counting a parent and its children. They do not require a universal aggregation engine in the first slice. Analysis selects the relevant level or a supported combination, recording approximations when needed.

## 6. Values, evidence and partial knowledge

### ReportedValue[T]

| Field | Meaning |
|---|---|
| `value` | Decimal, integer, text or absent value |
| `original_text` | Source numeric representation, dash or blank |
| `displayed_precision` | Source decimal places or explicit precision when relevant |
| `missing_reason` | When absent: unresolved, not applicable, not disclosed at this grain, or another source-supported reason |
| `source_reference` | Location of the observation |

Keep monetary amounts, percentages and maturity in Decimal and actual integral counts as integers. Preserve the source scale and sign in Bronze; serialise Decimal losslessly, for example as explicitly decoded decimal strings. Do not use binary floats as the persistence contract. A reported averaged count need not be an integer; its field type follows the source measure.

Source sign and canonical convention are separate. `(4,504)` can parse to `-4504` while retaining its original token; canonical positive-magnitude provisions require an explicit justified conversion. Never apply absolute value globally. A dash becomes numeric zero only when an applicable source convention establishes that meaning. Numeric zero must not be labelled missing.

Keep three things separate: value availability, per-attribute semantic knowledge and structural/extraction validity. A reported LGD with unknown weighting is a usable captured percentage. A blank maturity cell is an absent value; its meaning can remain unresolved. A named `No maturity` segment can contain a present monetary amount.

### Evidence and qualifications

`Qualification` retains source text, evidence references and its applicability to a dataset, row, field, band or relationship. Definitions can occur in introductions, glossaries, footnotes, appendices or related tables. External references need source and version/date context if used.

For interpreted attributes, retain value/status, supporting qualification or researcher decision references, and applicability. A small status vocabulary distinguishes established, provisional, unresolved, conflicting and not applicable. Capture explicit source statements separately from researcher interpretations. These are logical attribute contracts, not a requirement to create an independent database row for every adjective.

Known information can enrich a definition incrementally. Empty unresolved lists never prove exhaustive semantic knowledge. Unmapped labels and conflicts remain visible; preserve the source observation even when canonical fields cannot yet be supplied.

## 7. Durable semantic catalogue

The catalogue lives outside disposable Silver. Its core records are:

| Record | Responsibility |
|---|---|
| `Concept` | Stable identity, name, meaning, revision and lifecycle status |
| `ConceptRelationship` | Versioned, typed relationship between concepts, with rationale |
| `MeasureDefinition` | Concept plus composable meaning-bearing attributes and result unit |
| `InterpretationDecision` | Researcher decision, scope, rationale, evidence, date and supersession history |
| `SourceMapping` | Versioned contextual interpretation of source descriptors into canonical meaning |

Concept IDs are independent of published labels and Python field names. Renames and aliases can preserve identity. Splits, merges and replacements preserve explicit history. Do not reuse an old identity with silently different meaning. Source-effective periods and the dates/revisions of our interpretations are distinct.

### Measure composition

Compose only the attributes needed by actual disclosures and interviews:

- Counted entity or monetary exposure basis; result unit and, when established, currency.
- Aggregation method; averaging weight measure and weight timing.
- Regulatory factor adjustment, overlay/floor treatment and other reported adjustments.
- Numerator/denominator definitions for ratios where established.
- Population rules: inclusion, exclusion and explicit conditional selection.
- Temporal aggregation method/calendar and observation-count subject.
- Cohort eligibility, event definition, relative outcome window and model horizon where relevant.

Reusable components can be referenced as their use recurs. A structured condition may initially retain source text plus known tags; no generic predicate language, taxonomy of every possible combination or universal reasoning engine is required.

Arrangements (#) and monetary exposures ($) are distinct. NAB's mortgage agreement count can map to arrangement count; another portfolio's counterparty count is not automatically equivalent. Result percentages differ from their monetary weights. Ratio denominators differ from averaging weights. Regulatory factor-adjusted amounts differ from weighted means. An average of daily ratios is not generally a ratio of average amounts.

Default state at an anchor and default events over a following interval are different concepts. The researcher-defined forward 12-month default outcome starts with arrangements not in default and identifies qualifying defaults in the following year. Source CR9 measures map to it only when their cohort/window definitions support that interpretation. Exits, cures and repeated defaults remain tagged according to known rules rather than inferred from the word “default”.

### Ongoing discovery and interviews

Inspect evidence, compare with existing concepts, identify uncertainty, interview the researcher where meaning or analytical significance is unclear, and record the agreed decision. New wording does not automatically create a new concept. Researchers and agents maintain the same catalogue through this process during operation as well as initial development.

## 8. Contextual mappings and effective meaning

A `SourceMapping` records ID/revision, applicable source descriptors and context, target concept/measure revision or tags, supporting evidence/decisions and any explicit conversion. Scope can include entity, template, portfolio, approach, observation interval and document restrictions. A later comparative source has both its document context and its actual observation date.

Resolve an effective measurement view from:

```text
reported value + published field + row/column population and time
    + applicable qualifications + selected mapping/catalogue revisions
```

Complementary attributes compose. A documented narrower qualification can refine a broader definition when applicability establishes that relationship. Do not select conflicting interpretations by incidental file order or assume “most specific wins” without a supported scope relationship. Preserve unresolved/conflicting attributes and their evidence.

Every conformed field retains the applied mapping/definition revisions and source context. A transient effective view can assemble those references on demand; it need not duplicate the full semantic object into every cell. Partial mappings produce partial canonical metadata, not fabricated defaults.

A source `Sub-total` and `Total Residential Mortgages` can both map to `portfolio_aggregate` for the appropriate block. Their original labels and roles remain available. A mapping for one occurrence of `Sub-total` does not govern every occurrence in the report.

## 9. Typed domain records and scope of implementation

### First production record: CreditRiskExposureRow

This is the **Bronze** source-capture contract. The layer-explicit proposed name is `BronzeCreditRiskExposureRow`. Its Silver counterpart is `SilverCreditRiskExposureObservation`, with conformed numeric fields and separate interpretation/lineage metadata; the [layered model](2026-10-10-layered-data-model.md#silver-record-contract-and-units) specifies the distinction. The two are not the same class reused at different storage locations.

```text
record_id, source_row_ref, source_row_role
segment_memberships, aggregation_scope
on_balance_exposure, off_balance_exposure, average_ccf, ead
average_pd, reported_borrower_count, average_lgd, average_maturity
rwa, rwa_density, regulatory_expected_loss, provisions
```

Each measure field is a `ReportedValue` with a dataset/row-specific binding. Canonical roles and concepts are outputs of mapping, not prerequisites to accepting Bronze. The source-oriented borrower field does not assert that CBA counts arrangements. CR6's eight bands and one aggregate are pilot fixture expectations, not class invariants.

### Additional example shapes for design review

| Shape | Grain and purpose |
|---|---|
| `CreditQualityRow` | Source asset category with typed gross-performing, gross-non-performing, allowance and net fields; related allocation records carry the source's available SA/IRB/category detail |
| `ExposureMovementRecord` | Source movement line, reporting interval/temporal role and monetary value; retains opening/closing snapshots alongside period flows |
| `FundingRequirementRecord` | Funding item plus source measurement basis and optional maturity membership; a typed monetary amount with binding/evidence |

These shapes are exercises, not a mandate to implement all domains immediately. For LIQ2, maturity-bucket observations and one unsegmented total can be represented without four fabricated cells. “Unsegmented total” is an explicit grain, not an ambiguous null meaning missing, all maturities and no maturity simultaneously. A weighted funding requirement is a different measure, not another unweighted maturity bucket.

Narrative or footnote amounts can use suitable domain records with non-cell source references when selected. A footnote ratio remains reported data even if its numerator and denominator amounts are unavailable.

## 10. Golden sets and contract evolution

Golden sets specify the selected source-facing contract: context, axis/binding metadata, segmentation, source relationships, values, missingness and supporting qualifications. Humans or LLMs author them independently from the extractor and correct them by rereading evidence. Tests run against saved expectations without LLM calls.

Use the agreed mirrored layout:

```text
tests/bronze/<reporting-jurisdiction>/<org>/<document-date>/<extraction-id>/
    golden.json
    golden-notes.md
    test_extraction.py
```

The initial production golden scope covers the full Australian mortgage CR6 blocks from CBA June 2025 and Westpac, NAB and ANZ September 2025. The researcher expanded the original CBA/Westpac scope to NAB/ANZ during implementation-plan review. Each added PDF requires its own independent golden set, source review and bespoke extractor; ANZ's selected block is AIRB, with separate NZ/comparative blocks outside this initial selection. The linked worked examples are specification examples, not completed golden sets or independently verified test fixtures.

Wrong source values, dropped selected fields, incorrect signs, shifted columns or unsupported hierarchy assignments are extraction defects. Faithfully captured unknown semantics and undisclosed categories are legitimate outputs. Golden metadata can explicitly expect unresolved interpretation instead of encoding a guess. Canonical mapping expectations are verified separately against evidence and recorded researcher decisions, so a semantic correction alone need not rewrite an accurate source fixture.

Expand requirements through source review, golden scope/contract changes, focused extractor iteration and a new Bronze output version. Retain existing coverage unless explicitly revised. Shared dataclass/helper changes rerun affected extractors; new fields cannot silently disappear through an older decoder or comparator. Do not manufacture expected values from the extractor under test.

## 11. Silver conformance and rebuild lifecycle

### Conformance result

The [Silver logical schema](2026-10-10-layered-data-model.md#4-silver-er-the-conformed-cr6-domain) defines revision-scoped context, segments, typed domain observations, field interpretations, applied mappings, source lineage and observation relationships. Its CR6 numeric record has explicit fraction, base-currency-amount and count columns. Published labels and raw numeric strings remain Bronze evidence, linked from Silver; long-lived concepts/mappings are authoritative catalogue inputs rather than Silver-owned definitions. Canonical value availability and semantic resolution are distinct statuses.

Silver domain tables retain logical observation identity, canonical context/grain where established, typed values and units, measure/mapping revisions, source lineage and per-attribute interpretation tags. They also retain access to original values and definitions. This is a logical contract, not a requirement for one long-form fact table.

Use Mountainash contracts, relations and persistence integration with local DuckDB through `mountainash-data`; retain the independent NumPy/SciPy analytical library. Verify actual API/backend support for Decimal, contracts and transactions against pinned versions. Physical tables and storage encodings are established with the first working Bronze slice, not a prebuilt universal ontology database.

Validation distinguishes:

- **Structural/extraction errors:** invalid references, lost observations, contradictory value/missingness states or conversions inconsistent with established units.
- **Research limitations:** unknown conventions, coarse disclosures, mismatched populations, unresolved mappings and analytical residuals.

The second group does not block publication. Apply exact reconciliation only where source definitions and precision justify it; otherwise retain a diagnostic or use a tagged approximation in analysis. There is no global analytical eligibility flag. Calculations state their own needed inputs and assumptions.

### Full rebuild inputs and publication

A durable run manifest selects Bronze bundle/output versions, catalogue and mapping revisions, curated corrections, conformance code/contracts/configuration and relevant environment versions. Persist these inputs independently of the Silver tables being replaced. Golden fixtures are not substitute conformance input.

Build from empty candidate tables, validate structural correctness, and publish atomically using a transaction or staging mechanism supported by the selected backend. A failed run leaves the prior published revision available. Semantic incompleteness alone is not a failed rebuild. Gold results identify their consumed Silver revision and become stale when dependencies change.

Stable logical IDs follow explicit source lineage and source-occurrence selection, not mutable canonical names or auto-increment keys. Repeated evidence, restatements and multiple displays of a total require a selection policy; equal numbers alone never deduplicate observations. Splits/merges/removals replace the affected scope and preserve replacement lineage. Detailed deterministic keys are exercised with the first persisted datasets.

Incremental upserts are later optimisations and must yield the same logical result as rebuilding identical selected inputs. Reprocessing must not create duplicate active observations. Existing Silver rows or manually patched values are never necessary inputs to regeneration.

### Corrections and retention

| Change | Durable correction |
|---|---|
| Source extraction error | Correct source expectations/extractor, publish new Bronze version |
| Interpretation error | Revise catalogue/mapping/decision; rebuild selected Bronze |
| Missing source qualification | Expand source fixture/extraction, then revise interpretation as needed |
| Bank restatement | Retain new source occurrence with explicit supersession/selection |
| Analytical assumption change | Revise retained analysis inputs; do not rewrite reported data |

Retain Bronze versions, semantic revisions, run manifests and implementation/configuration needed for reproducibility. Historical Silver snapshots are optional. Git-ignored generated data still requires an explicit retention/backup location; “ignored” does not mean disposable. Catalogue definitions/decisions must not exist only in generated database tables. Concrete file paths and backup commands belong to implementation planning.

## 12. Worked review and next checkpoint

The [worked examples](2026-10-10-data-model-worked-examples.md) exercise:

1. CBA CR6: twelve field definitions, mixed result units, row populations, missingness and qualifications.
2. CR1/CR2: nested allocation headers, coarse disclosures, signed allowances, subset links and row-defined stock/flow measures.
3. NAB LIQ2: hierarchical funding items, categorical/interval maturity, merged totals and factor-adjusted monetary amounts.

They establish that the proposed logical model can express the selected cases without inventing unavailable data. They do not establish full extraction accuracy, backend integration or production readiness.

Review the consolidated contracts and examples before implementation planning. The first implementation checkpoint now covers four agreed full Australian mortgage CR6 golden sets and bespoke extractors, followed by Mountainash conformance/rebuild verification. The [implementation plan](../plans/2026-10-10-cr6-bronze-to-silver.md) details the CBA/Westpac/NAB/ANZ scope. Introduce additional domain classes only as their selected extraction scope becomes concrete.
