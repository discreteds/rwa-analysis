# Credit-quality and provisions discovery

Date: 2026-10-10

Status: Source findings and model proposals for discussion; not production extraction or a golden set.

Review outcome: the researcher agreed two-axis semantic bindings and emphasised that hierarchical `of which` relationships, including those conveyed in notes, must be captured to prevent double-counting. These decisions are incorporated in the data-model specification and semantic principles; the remaining proposals are discovery inputs for continued discussion.

## Inspection scope

Used saved official PDFs catalogued in [raw/index.md](../../raw/index.md). Read layout-preserving text for the pages below and visually inspected CBA p34, NAB PDF pp35 and 37, ANZ p39 and Westpac p36. Rendered pages and exploratory text remain under `/tmp/opencode/rwa-2025-spike/`.

| Source | PDF pages | Printed pages | Content |
|---|---|---|---|
| CBA June 2025 | 34 | 34 | CR1 credit quality and CR2 movements |
| NAB September 2025 | 35–37 | 33–35 | CR1, comparative CR1, CR2, ageing and industry provisions |
| ANZ September 2025 | 39–40 | 39–40 | CR1 and CR2 |
| Westpac September 2025 | 36 | 36 | CR1, CR2 and narrative ratios |

The goal is capture and tagging. The relationships below describe source structure or candidate interpretation, not a requirement to achieve perfect reconciliation.

## 1. Source sign and canonical convention are different

CBA's CR1 loan allowances/impairments are shown as `5,966` ($M). Westpac's corresponding source field shows `(4,504)` ($m); ANZ shows `(3,874)` ($M). NAB shows positive loan provisions of `5,578` ($m) and explicitly labels net carrying value `(a+b-c)`.

Preserve source representation and signed numerical value. If a canonical provisions measure uses positive magnitude, applying that convention is an explicit mapping/conversion with lineage, not a blanket absolute-value operation. The dates and populations here differ; these examples establish presentation variation, not an economic comparison.

## 2. Nested headers supply several independent tags

CBA CR1's loan value `48` ($M) sits beneath:

```text
Of which ECL accounting provisions for credit losses on SA exposures
    Allocated in regulatory category of Specific
```

That cell combines a measure (accounting ECL provision), regulatory approach (standardised), source allocation category (Specific), asset row (Loans) and snapshot date. A flattened label such as `Specific` loses most of its meaning. Retain the header path and source qualifications; canonical tags can develop through discovery.

Westpac uses non-performing/performing allocation labels where CBA/ANZ use Specific/General. Do not assume a universal equivalence from matching column positions. Existing glossary evidence can support scoped mappings when examined.

## 3. Different granularity is legitimate source data

NAB combines the standardised provisions allocation into source column `d/e`. Its CR1 total is `276` ($m), compared with total provisions of `6,165` and IRB provisions of `5,889`.

Footnote 1 explicitly says the finer standardised breakdown has not been provided on materiality grounds. Capture the combined amount and reason for unavailable detail. Do not invent Specific/General values or force every bank into the most detailed source layout.

## 4. Row hierarchy and subset relationships matter

NAB CR1 includes `Loans, comprising:` with child rows `Loans and advances` and `Other financial assets`. Its debt-securities row similarly has children. ANZ discloses `Debt Securities` and rows `2a` and `2b` for amortising cost and fair value.

Preserve parent/child and `of which` relationships where established by source layout/text. A total must not add both a parent and its children. `Of which` indicates inclusion, but does not universally establish that all displayed children exhaust the parent or are mutually exclusive. Row numbering alone is insufficient: ANZ's `3a Other financial assets` is not proof that it is a subset of row 3 off-balance-sheet exposure.

These are source presentation/aggregation relationships, distinct from the slowly changing canonical concept hierarchy.

## 5. CR2 has row-defined measures and temporal roles

CBA CR2 reports the following $M figures for the half year ended 30 June 2025:

| Source row | Amount | Temporal role |
|---|---:|---|
| Previous reporting-period end stock | 10,297 | Opening snapshot |
| Became non-performing since the last reporting period | 4,241 | Period movement |
| Returned to performing status | (1,922) | Period movement |
| Amounts written off | (386) | Period movement |
| Other changes | (1,251) | Period movement |
| Reporting-period end stock | 10,979 | Closing snapshot |

The title omits off-balance-sheet instruments, but the introduction and row text explicitly include them. NAB and ANZ also establish off-balance-sheet inclusion outside the short title. Capture these scope qualifications.

The column identifies the period and unit; the row identifies the measure and whether its value is a stock or flow. Thus our initial CR6-oriented assumption that each column alone identifies a measure is too narrow. The dataset can represent a half-year movement schedule with explicit opening/closing snapshot roles and period-flow rows; it need not be fragmented into unrelated datasets to express the timing.

These are monetary exposure movements, not arrangement counts or necessarily defaults from an initially performing fixed cohort. ANZ's `Other changes` includes repayments and foreign exchange impacts; Westpac's includes collections and foreign exchange movements. Retain source wording rather than silently equating every movement definition.

## 6. Same row, nested populations and accounting scope

NAB PDF p37 reports this residential-mortgage row, all in $m:

| Field | Amount |
|---|---:|
| Credit and CCR EAD, post-CCF and post-CRM | 496,085 |
| Of which credit-risk EAD, post-CCF and post-CRM | 496,085 |
| Non-performing exposures | 5,401 |
| Provision for non-performing exposures | 501 |
| Of which individually assessed provision | 71 |

Footnote 2 identifies the non-performing provision as Stage 3 ECL, individually and collectively assessed. The final column is an `of which` subset, not an additional provision to add to 501. Equal EAD values in the first two columns do not erase the different framework definitions.

Below the industry table, the report adds all-industry performing provisions of `3,815` and total provisions of `6,165`. These rows are not residential-mortgage observations or another industry category. Capture their broader scope explicitly. Footnote 5 identifies performing provisions as Stage 1 and Stage 2 ECL assessed collectively.

The disclosure labels its classification as based on ANZSIC Level 1, but includes reported groupings such as Residential mortgages and combined sectors. Preserve the actual labels and claimed classification basis; do not manufacture standard classification codes without a supported mapping.

## 7. Values also occur outside table cells

Westpac p36's narrative reports stressed exposures / total committed exposures of `1.28%` and collectively assessed provisions / credit RWA of `1.25%`. ANZ p39's footnote decomposes allowances into collectively assessed provisions of `$4,379 million` and individually assessed provisions of `$399 million`.

These are source-reported observations, not our derivations. If selected for extraction, source references must support paragraph/footnote locations without fictitious row/column coordinates. Capture the reported ratios without requiring independently disclosed numerator/denominator amounts.

## Proposed model refinements

1. Preserve multi-level source header paths and explicit source row/subset relationships.
2. Resolve meaning from dataset context, row definition, column definition and qualifications. Semantic axes can appear on either side of a table.
3. Keep result unit, source sign convention and canonical conversion separate.
4. Allow explicit row/field temporal roles within a coherent movement dataset; avoid hidden overrides of a single snapshot date.
5. Represent disclosed coarse aggregates without forcing undisclosed finer categories.
6. Support narrative and footnote observations through existing shared provenance, with domain-appropriate records as requirements emerge.

These refinements can extend typed domain models. They do not require a universal cell store, a generic rule language or new persisted reconciliation entities. Agree the representation through researcher review before promoting these proposals into implementation contracts.
