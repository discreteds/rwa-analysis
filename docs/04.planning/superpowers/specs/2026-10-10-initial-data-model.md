# Initial disclosure data model

Date: 2026-10-10

Status: Approved conceptual model; written specification awaiting review.

Parent design: [Research platform architecture](2026-10-10-rwa-analysis-design.md).

Governing principles: [Principles and architecture](../../../01.principles/README.md). This specification provides the detailed contracts behind those durable decisions.

Evidence: [CBA/Westpac source review](../../../00.ideation/2025-disclosure-spike.md) and [NAB/ANZ metadata review](../../../00.ideation/2025-nab-anz-metadata-spike.md).

## 1. Design decision

Use shared disclosure metadata and provenance with small typed domain models. The first domain model is a general CR6 `CreditRiskExposureRow`, initially exercised against Australian residential mortgage tables. Mortgage analysis must not determine the structure of all future data domains.

A document identifies the source. An extracted dataset identifies the meaning, scope and grain of its observations. A single extraction bundle can contain multiple datasets, portfolios, jurisdictions and observation dates.

The models below describe the initial logical Python dataclass contracts. Persisted representations preserve decimal values and explicitly convert to corresponding Mountainash tabular contracts. Implement fields required by the first source-backed golden sets, extending these contracts as requirements grow.

## 2. Relationships and identity

```text
SourceDocument
    |
ExtractionBundle — one logical bundle per bespoke extraction script
    |
    +-- ExtractedDataset[CreditRiskExposureRow]
    |       +-- DatasetContext
    |       +-- MetricDefinition references
    |       +-- SegmentationDefinition and BandDefinition records
    |       +-- CreditRiskExposureRow records containing ReportedValue fields
    |
    +-- Other typed domain datasets as required

Contexts, definitions and values reference SourceReference/Qualification records.
```

An extraction bundle's identity is the source-reporting jurisdiction, organisation, document reporting date and extraction ID already used in the folder hierarchy. Output versions belong to the same logical bundle. IDs are readable catalogue identifiers; no content hash or file-identity proof is required.

Dataset IDs distinguish coherent table blocks, including comparative periods and separate portfolio/regulatory scopes. Band IDs are scoped to their segmentation definition; row IDs are scoped to their dataset. Identical labels in unrelated tables do not imply shared identity or equivalent meaning.

## 3. SourceDocument

| Field | Meaning |
|---|---|
| `document_id` | Source catalogue identifier |
| `local_path` | Project-relative path to the saved PDF in `raw/` |
| `organisation_id` | Institution/brand identifier |
| `reporting_entity` | Legal reporting entity as disclosed |
| `title` | Source document title |
| `document_reporting_date` | Date described by the report as a whole |
| `publication_date` | Publication date when known |
| `reporting_jurisdiction` | Jurisdiction of the source disclosure |
| `source_url` | Download/source URL |

`raw/index.md` remains the acquisition catalogue. Structured document context is populated as extraction begins; no registration workflow is introduced. A table can have a different observation date, portfolio jurisdiction or entity scope from its containing document.

## 4. ExtractionBundle and ExtractedDataset

`ExtractionBundle` contains:

- `document`: its `SourceDocument`.
- `extraction_id` and `script_path`: the corresponding bespoke extractor.
- `schema_version`: version of its output contract.
- `output_version`: version of the saved extraction output.
- `datasets`: named typed datasets emitted by that script.

Each `ExtractedDataset[T]` contains its `DatasetContext`, applicable metric definitions, optional segmentation definitions, records of type `T`, and source references/qualifications needed to interpret them.

Dataset collections can be represented as related persisted tables; they need not be flattened into one universal wide table. A future domain introduces a typed record and its conformance contract, rather than filling most of a mortgage record with nulls.

Example: an ANZ September report's single bundle can contain Australian AIRB September CR6, NZ September CR6, March comparative CR6, and subsequently provisions or capital datasets. The bundle remains under `au/anz/`; its contents retain their actual scopes.

## 5. DatasetContext

| Field | Meaning |
|---|---|
| `dataset_id` | Identifier for this coherent source table/block |
| `domain` | Data domain, initially credit-risk exposures |
| `source_template` | Template identifier such as CR6, where present |
| `source_table_title` | Original title |
| `reporting_entity` | Entity represented by this block |
| `consolidation_scope` | Disclosed consolidation/perimeter |
| `observation_date` | Date of a stock or snapshot measure |
| `period_start`, `period_end` | Period covered by a period measure, where applicable |
| `portfolio` | Source portfolio classification and relevant scope, if applicable |
| `geographical_scope` | Country/countries or source-defined aggregate region |
| `regulatory_basis` | Applicable regulator, rules and approach, if applicable |
| `qualifications` | Source-backed explanations and limitations |

Portfolio geography, entity domicile, reporting jurisdiction, regulatory-rule jurisdiction and currency are distinct concepts. Do not infer one from another.

A multi-country aggregate remains one observation unless the source discloses a breakdown. Do not copy its amount into each included country. Source labels remain available even when Silver later supplies canonical classifications.

Context applies to a coherent block of records. Split different periods or scopes into distinct datasets instead of introducing hidden row overrides. Domains such as CR9 may subsequently add explicit observation/cohort timing fields to their typed record model where the table contains measures with different temporal meanings.

## 6. SegmentationDefinition and BandDefinition

`SegmentationDefinition` contains:

- `segmentation_id`.
- `dimension`: PD initially; other numeric or categorical dimensions as required.
- Ordered `bands`.
- `coverage_status` and `mutual_exclusivity_status`, supported by qualifications or explicitly unresolved.
- Applicable source/template expectations when established.
- Qualifications and source references.

`BandDefinition` contains:

| Field | Meaning |
|---|---|
| `band_id` | Identifier within the segmentation |
| `source_label` | Verbatim band/category label |
| `position` | Source order |
| `kind` | Interval, category or default category |
| `lower_bound`, `upper_bound` | Decimal numeric bounds for an interval |
| `lower_inclusive`, `upper_inclusive` | Endpoint membership where established |
| `unit` | Source unit of the segmentation dimension |

Categorical and default buckets do not require interval fields. Distinguish an explicitly unbounded endpoint from a missing or unresolved endpoint; a null alone must not ambiguously mean all of these. Preserve the source label and a qualification when endpoint meaning is unresolved.

Expose the displayed non-default band count, default category count and total band-row count. Keep subtotal/total counts separately. Counts derived from the extracted structure are derived metadata; source-stated counts, if any, are separately attributable observations. The golden set independently specifies expected counts and bands.

Example: `0.15 to <0.25` in percent means a lower bound of Decimal `0.15`, inclusive, and upper bound of Decimal `0.25`, exclusive. Silver can convert those bounds to probability fractions. `100.00 (Default)` is a default category, not an ordinary interval.

NAB's BNZ mortgage CR9 block demonstrates that displayed intervals can omit parts of the standard template. Preserve omitted-band status when an expected template has been established. Do not manufacture zero values, extend neighbouring bounds or assert complete coverage without evidence.

## 7. MetricDefinition

Metric definitions describe fields in a dataset; definitions can be reused when the source establishes equivalent meaning.

| Field | Meaning |
|---|---|
| `metric_id` | Identifier of the applicable metric definition |
| `source_label` | Original column/metric label |
| `unit`, `scale` | Currency/count/percent/etc. and source magnitude |
| `weighting_basis` | EAD, borrower arithmetic or other disclosed convention |
| `denominator_basis` | Definition of a ratio's denominator |
| `counting_unit` | Agreements, counterparties, borrowers or unspecified |
| `exposure_basis` | Gross/net and pre/post CRM/CCF where relevant |
| `adjustment_treatment` | Overlay/floor inclusion or exclusion, where established |
| `qualifications` | Relevant source-backed explanations |

Retain displayed precision alongside the original value representation, rather than treating the rounded number as exact at arbitrary precision. Some definitions apply at portfolio grain only, such as total provisions. Missing-value semantics can also be qualified by the applicable source definition.

Unknown convention is distinct from not applicable. For example, preserve an original “Average PD” label without assigning EAD weighting until its definition has been established. Do not infer unique borrowers merely from a column title.

Accounting provisions/ECL and regulatory expected loss are different metrics. Market share, when added, requires the relevant market, numerator/denominator definitions and date or period; a calculated share is a derivation rather than a source-reported observation.

## 8. ReportedValue, SourceReference and Qualification

`ReportedValue[T]` contains:

- `value`: a typed value such as Decimal, integer or text; absent when unavailable.
- `original_text`: the source representation, including a dash or blank.
- `missing_reason`: when applicable, the established explanation or unresolved status.
- `source_reference`: location of the evidence for that field.

Metric semantics are supplied by the dataset's field-to-definition mapping. Do not repeat complete definition objects in every cell.

`SourceReference` identifies the document, one-based PDF page, printed page label where present, table, source row and source column. Coordinates are optional. Preserve original row numbers/column letters alongside semantic identifiers when provided.

`Qualification` carries the source-backed explanation, its reference and its applicability to a dataset, definition, band or field. Context may come from another table, introduction or appendix. For example, ANZ's mortgage overlay is explained in CMS2 and must retain that location when it qualifies CR6 interpretation.

Blank, dash, zero, not applicable, not disclosed at this grain and unresolved are not interchangeable. Store the original representation even when a missing reason has been established. Dataclass validation should reject contradictory states such as a zero value labelled missing.

## 9. First domain record: CreditRiskExposureRow

This general CR6 record initially supports the selected mortgage blocks:

```text
CreditRiskExposureRow
    row_id
    row_role                        detail / subtotal / total
    band_id                         for band rows
    on_balance_exposure
    off_balance_exposure
    average_ccf
    ead
    average_pd
    reported_borrower_count
    average_lgd
    average_maturity
    rwa
    rwa_density
    regulatory_expected_loss
    provisions
```

Every metric field uses `ReportedValue` with the applicable dataset metric definition. Monetary amounts, percentages and maturity use Decimal; reported counts use integer. Preserve percentages and monetary scale as disclosed in Bronze. Numerical conversion for analytical calculations happens after explicit conformance.

The initial mortgage blocks have eight band rows and one total/subtotal, but that row count is a golden-set expectation for those datasets, not a class invariant. Mortgage maturity and band-level provisions can be unavailable for different reasons. Totals have no PD-band identifier and are excluded from summing the detail rows.

Other retail/non-retail CR6 blocks can reuse this model if its semantics fit. New domains such as provisions by accounting stage or market share receive distinct record types with shared context and provenance.

## 10. Golden sets and evolution

Golden sets use the same logical structure as extraction outputs: dataset context, metric definitions, segmentation, source-backed qualifications and expected records. Humans or LLMs author them independently from the source. Expected values must not be produced by the extractor under test.

Tests compare metadata and values, excluding execution-specific fields such as output timestamps. A wrong date, counting unit, band bound, missingness reason or overlay basis is a failure even when amounts match.

When additional data is required, extend the golden set and its scope, update the relevant dataclasses and tests, then iterate on the extractor. Newly requested fields must not disappear silently through an older decoder or comparator. Regenerate Bronze and reconform affected Silver datasets after the tests pass. Previously selected data remains covered unless scope is explicitly revised.

Test directories retain the agreed mirrored layout:

```text
tests/bronze/<reporting-jurisdiction>/<org>/<document-reporting-date>/<extraction-id>/
    golden.json
    golden-notes.md
    test_extraction.py
```

All datasets emitted by the corresponding script can be covered within that directory. A new jurisdiction or domain inside the same file does not require duplicating the source bundle.

## 11. Silver handoff

Silver reads saved Bronze outputs, not PDFs. Its domain-specific Mountainash contracts:

- Map source classifications to canonical classifications through versioned mappings.
- Convert percentages, currencies/scales where appropriate and other units explicitly.
- Apply schema conformance, value checks and compatible-basis reconciliation.
- Preserve original definitions, source references and Bronze dataset/output-version lineage.
- Record analytical comparability and eligibility separately from successful extraction.

Final physical Silver tables are designed from the first working, golden-tested Bronze datasets. This specification does not require implementing every possible dimension table before extracting the initial documents.

### 11.1 Published labels to canonical roles and variants

Maintain explicit, versioned semantic mappings from published labels and their source context to canonical concepts, roles and variants. Organisations can use different labels for equivalent concepts, and both labels and underlying definitions can change over time. Label equality alone does not establish equivalence.

Each mapping records:

- Mapping ID and revision, together with the canonical vocabulary version.
- Source label and mapping target kind (for example row role, metric or portfolio classification).
- Applicable organisation/reporting entity, domain, table/template, portfolio, regulatory basis and other context needed to disambiguate the label.
- Applicable observation-date range, with an explicit document/template restriction when needed for comparatives or changed publication conventions.
- Canonical concept/role and its relevant semantic variant attributes.
- Supporting source references and the rationale for the interpretation.

For the inspected mortgage blocks, CBA's `Sub-total` and Westpac's `Total Residential Mortgages` both map to the canonical row role `portfolio_aggregate`, with scope `all_disclosed_pd_bands_in_portfolio`. Preserve the original labels and source presentation roles (`subtotal` versus `total`) separately. A different occurrence of `Sub-total` does not inherit this mapping without matching context.

Likewise, NAB's `Number of borrowers` can map to a borrower-count concept with counting-unit variant `agreement` for its mortgage CR6 block. Other banks' counting units remain unresolved until established. CBA and NAB RWA can share a canonical RWA concept while retaining distinct overlay-treatment variants. Variants describe semantic differences, not merely spelling differences, and may comprise several attributes rather than one combined enum.

Variant evidence may appear in footnotes, table introductions, methodology notes, glossaries, appendices or explicitly referenced definitions outside the immediate table. Each PDF review must look for applicable definitions in those locations and connect them to the affected fields. Preserve the supporting text and source locations in Bronze, together with the scope that establishes applicability (such as portfolio, table, metric or period). A glossary definition must not automatically override a more specific table qualification; conflicting or insufficient evidence leaves the affected interpretation unresolved. External definitions, when needed, require their own source reference and applicable version/date rather than being silently assumed.

The semantic mapping can therefore depend on both a published label and multiple evidence-backed qualifications. Record which evidence supports each variant attribute, distinguishing explicit source statements from supported interpretations. Golden expectations cover these qualifications and their applicability as well as cell values; changes to notes or glossaries can require a new mapping even when the column label is unchanged.

Bronze preserves published labels, definitions and evidence. Silver applies these mappings through Mountainash conformance and retains the applied mapping ID/revision alongside the canonical result. Distinguish source-effective dates from mapping revisions: correcting our interpretation of an old disclosure creates a new mapping revision without pretending the bank changed its definition on that date. Repeated comparative observations retain their own observation dates and document context.

Mapping outcomes explicitly distinguish resolved, unresolved and ambiguous cases. Conflicting applicable rules must not be selected by incidental order; unknown labels or unsupported variants remain inspectable and ineligible for analyses requiring resolved semantics. Published-label mappings do not themselves convert units or make differently defined measures analytically interchangeable. Save the mapping revision used for each conformance run so a later correction can produce a new, reproducible Silver result.

### 11.2 Layered metric definitions and revisable conformance

Metric metadata separates the canonical concept, measurement definition, reporting definition and presentation. Measurement definitions describe population, weighting, denominator, counting unit and adjustment treatment; reporting definitions scope these to the entity, portfolio, regulatory basis and effective period; presentation retains source labels, units, scale, precision and missing-value conventions. Reusable attributes such as geography and currency cut across the concept hierarchy. Inheritance and overrides must be explicit and evidence-backed, with unknown or conflicting attributes remaining unresolved. Each conformed observation identifies the effective definition version used.

Corrections are expected during development and operation. An extraction error requires corrected source-backed expectations, extractor changes and a new Bronze output version. An interpretation error requires revised metadata/mappings and reconformance of affected saved Bronze. A bank restatement supplies new source evidence with an explicit supersession relationship. These are distinct changes and must remain distinguishable in lineage.

### 11.3 Silver is rebuildable from scratch

Full Silver regeneration is a normal, first-class workflow throughout the repository's lifetime. Silver is a derived, replaceable interpretation of retained Bronze outputs and versioned conformance inputs. Its existing rows, generated IDs or manually patched values must never be required to reconstruct it.

The authoritative rebuild inputs are:

- Explicitly selected saved Bronze bundle/output versions, including the policy selecting repeated comparative evidence and restatements without double-counting observations.
- Versioned canonical definitions, source mappings and any curated corrections or overrides, with their evidence and scope.
- Conformance code, contracts and configuration versions.

Keep these inputs outside the disposable Silver layer. Golden sets verify extraction; they are not a substitute input for rebuilding Silver. Corrections discovered while using Silver must be captured in the appropriate durable input and replayed, rather than existing only as edits to current Silver rows.

For each rebuild, record the selected input versions and conformance versions in a durable run manifest. Build a candidate Silver revision from empty target tables, validate it with Mountainash contracts and reconciliation checks, and publish it atomically through a supported transactional or staging mechanism. A failed rebuild leaves the last published revision available. Publishing a new revision also makes dependent Gold outputs stale until regenerated against that revision.

Stable source identities and deterministic logical observation identities must survive a rebuild. A mutable canonical interpretation is not the sole observation/upsert key, and database-generated surrogate IDs are not cross-rebuild identities. When a correction changes record grain through splitting, merging or removal, replace the affected dataset scope and preserve its source lineage rather than leaving obsolete rows active.

Incremental updates/upserts are a subsequent efficiency mechanism: given the same selected inputs and definition versions, they must produce the same logical current result as a full rebuild. Reprocessing identical inputs must not duplicate observations. Design and verify the initial conformance path around full regeneration before optimising incremental updates.

Reproducibility requires retaining the relevant Bronze versions, definition/mapping revisions, conformance implementation/configuration and run manifests. Physical historical Silver snapshots may be retained for convenience, but rebuilding the current layer must not depend on them. Gold results identify the Silver revision they consumed so results from different interpretations cannot silently mix.

## 12. First implementation checkpoint

Demonstrate the contracts using the agreed CBA June and Westpac September mortgage CR6 blocks, informed by the NAB/ANZ scope, count and overlay differences. Before implementation planning, review the written model and ensure those distinctions can be expressed without bank-specific changes to shared metadata classes.

This document defines the approved model structure, not completed Python classes, golden fixtures or extraction scripts.
