# CR9 capture and shared domain interfaces

Date: 2026-10-12

Status: **PROPOSED — written design for researcher review.** Capture-and-tag scope
and deferred refactoring are agreed; the class shapes below are proposals. No CR9
implementation, extraction fixture or production publication is supplied by this spec.

## 1. Ask and boundary

Use mortgage CR9 as the second concrete domain to establish interfaces that capture
each published datapoint with its meaning, multiple time dimensions and provenance.

Preserve successive report occurrences so bespoke research can investigate changed
historical calculations and extend its historical coverage. Selection, aggregation,
alignment, inferred annual rates and authoritative-vintage selection belong to the
analysis, not conformance. A rolling average remains a rolling average.

Initial source scope: the mortgage CR9 blocks in CBA June 2025 and Westpac, NAB and
ANZ September 2025, including default rows, all displayed columns, ANZ's subtotal,
external-rating labels and applicable notes. NAB's separately labelled BNZ mortgage
block is a useful additional shape probe, not an implicit expansion of production
extraction scope. Additional report vintages follow the same capture shape when selected.

Governing guidance: [capture and tag](../../../01.principles/a.architecture/capture-and-tag-for-research.md),
[field-level semantics](../../../01.principles/b.data-semantics/layered-metric-definitions.md),
[identity](../../../01.principles/b.data-semantics/correction-safe-identity.md),
[composed processing](../../../01.principles/a.architecture/composed-processing-and-organisation-staging.md)
and [Mountainash-first](../../../01.principles/d.coding-practices/mountainash-first.md).
The [current architecture](../../../architecture.md) remains the implemented baseline.

## 2. Existing solutions and choice

The existing `Dataset` protocol, `DatasetMetadata[Context]`, `ReportedValue`, axes,
bindings, qualifications and scoped catalogue already cover most capture needs.
Named `Cr6Output` relations and `TABLES` already separate domain shape from storage.
They fall short specifically at the mandatory single observation date, CR6-only
field resolution, codec dispatch and CR6-only candidate/store associations.

| Approach | Trade-off |
|---|---|
| **Typed domain rows plus shared metadata bindings — recommended** | Retains meaningful CR6/CR9 fields while sharing provenance, temporal descriptors and table operations. Requires explicit two-domain composition. |
| Independent CR9 stack | Small initial change, but duplicates catalogue resolution, transport and staging/master behaviour immediately. |
| Universal observation/value model and plugin engine | Generalises untested domains and weakens typed field contracts; no current consumer justifies this larger change. |

No new package or bank-specific workflow classes. Do not introduce a universal
pipeline protocol merely because two concrete pipelines have similarly named methods.

## 3. Source cases that determine the design

Re-read the retained source pages on 2026-10-12. This is design evidence, not golden
authoring. Source acquisition URLs are in [raw/index.md](../../../../raw/index.md).

| Source | Concrete evidence | Representation consequence |
|---|---|---|
| CBA p.60 | Annual computation 1 April 2024–31 March 2025; historical data “from 2014”; internal-grade midpoints mapped to displayed bands | Annual interval and history window differ. Retain `2014` at year precision; do not invent a January start or history end. Band assignment convention is metadata. |
| Westpac pp.55–56, notes b–d | Weighted PD and EAD at June 2024; annual defaults July 2024–June 2025 include new borrowers; ten-year historical rate | PD measurement and weight dates differ from publication. Preserve the new-borrower subset and history duration; exact history boundaries remain unresolved unless evidenced. |
| NAB PDF pp.60–61, printed pp.58–59 | Weighted PD at reporting date; counts explicitly dated 30 September 2025 and 2024; defaults at any month-end in the financial year include cured/exited borrowers | Field-specific dates and event/exit rules. Do not use the current PD as an opening-cohort prediction. Count definition refers back to CR6. |
| ANZ p.66 | Five-year mortgage history; historical numerator excludes technical defaults and denominator excludes exited obligors; subtotal 0.62% | Preserve aggregate and band observations separately. The corporate 2.5-year exception does not apply to mortgages. Annual cohort/rating anchors remain unresolved where not established. |

Examples of first-band source values: CBA historical rate 0.07%; Westpac annual
default count 385, including 7 new borrowers; NAB counts 198,124 (2025) and 215,531
(2024); ANZ historical rate 0.08%. These are distinct measures, not matched cohorts.

## 4. Source class structure

Keep `Dataset` limited to `id` and `metadata`; parameterise it by context if needed
for static typing, rather than requiring a common numerical row collection.
`ExtractionBundle.datasets` continues to contain typed domain datasets.

Proposed CR9 source declarations:

| Declaration | Responsibility / members |
|---|---|
| `Cr9Context` | Existing source title/template/portfolio, entity, regulatory scope, geography, currency, qualifications and evidence; document date remains provenance. No mandatory single observation date. |
| `Cr9Dataset` | `id`, `metadata: DatasetMetadata[Cr9Context]`, `backtesting_rows` |
| `Cr9BacktestingRow` | Source record ID, row reference/role, segment memberships and aggregation scope; seven typed numeric fields below |
| Shared temporal metadata | Descriptors and bindings held by `DatasetMetadata`, empty by default for retained CR6 input |

Seven CR9 measure fields (source names, not canonical equivalence assertions):

- `weighted_average_pd`, `arithmetic_average_pd`, `historical_annual_default_rate`:
  `ReportedValue[Decimal]`.
- `previous_year_borrower_count`, `current_year_borrower_count`,
  `defaulted_borrower_count`, `new_defaulted_borrower_count`: `ReportedValue[int]`.

External-rating equivalents are source labels attached through published fields/axes
and qualifications, not coerced into numerical measures. Preserve their association
with each row/band and agency, including `N/A` and blanks. `new_defaulted_borrower_count`
is a disclosed subset of the default count, not an additional additive population.
Use existing source relationships and field endpoints with row-scoped qualifications.

Retain blank default-row cells with their source missingness; do not invent annual
default counts for default-stock rows. Preserve ANZ's subtotal as a source aggregate;
do not synthesise the same row for other banks. Numeric null and unknown semantics
remain independent. Unknown counting rules do not prevent storing integer counts.

CR6 keeps its row shape and existing context. Do not migrate all source classes to
a new common context superclass: shared metadata composition already provides reuse.

## 5. Field-level temporal metadata

Add two shared source declarations, with no validation methods:

**`TemporalDescriptor`**: `id`, `source_label`, optional `point`, `start`, `end`,
optional `duration`, and qualification/evidence refs. Retain any boundary-inclusion
wording in qualifications; no current case requires separate inclusivity fields.
Each temporal component carries its own existing knowledge status. Date labels use
ISO partial-date text (`2024`, `2024-06`, `2024-06-30`) without padding to a day;
duration uses explicit amount/unit, e.g. 10 years. Null boundaries remain unresolved,
not unbounded. A descriptor can hold a known duration and unknown boundaries.
Source wording and evidence remain available even when no date is normalised.

**`TemporalBinding`**: `record_id`, `field_key`, `role`, `descriptor_ref`.
Initial roles are `measurement`, `cohort_anchor`, `outcome_window`, `history_window`,
`rating_assignment`, and `weight_measurement`. Multiple roles can bind to one field;
multiple fields can reference one descriptor. Binding identifies applicability, not
an inference that all roles in a row share one date. A source-unknown role can bind
to an explicitly unresolved descriptor; irrelevant roles need not be manufactured.

A field's complete metadata is its existing value/published-field binding plus these
temporal bindings, source context, applicable qualifications and catalogue meaning.
There is no implicit dataset-date fallback for CR9. The CR6 adapter can expose its
existing snapshot date as `measurement` with original evidence; it cannot invent
cohort, rating-assignment or outcome dates from that snapshot.

Examples:

```text
Westpac weighted_average_pd:
  measurement -> June 2024
  weight_measurement -> June 2024 (EAD basis from note b)
Westpac defaulted_borrower_count:
  outcome_window -> 2024-07-01 through 2025-06-30 (introductory statement)
Westpac historical_annual_default_rate:
  history_window -> duration 10 years; start/end unresolved
CBA historical_annual_default_rate:
  history_window -> start 2014 (year precision); end unresolved
NAB previous_year_borrower_count:
  measurement -> 2024-09-30 (explicit header)
```

Population eligibility, event definition, exits/cures, denominator and weighting are
semantic definitions/qualifications. They are not encoded as date roles or executable
predicates. Reuse catalogue concepts after checking their meaning against the source;
do not map all annual default columns to the canonical forward-cohort definition.

Bronze descriptors capture source-supported interpretation. Subsequent researcher
corrections use existing versioned catalogue decisions and evidence, not in-place
rewrites of Bronze. Address the affected field through its mapping scope and describe
the temporal role and correction in the decision rationale, supported by existing
qualification references. This slice does not claim machine-resolved corrected dates.
Preserve those decision links alongside source descriptors. A new temporal
correction/resolution engine is deferred; this slice does not derive dates.

## 6. Shared semantic resolution

Split the current CR6 `resolve_field()` responsibility at the existing seam:

1. Domain adapters locate a typed field, its source binding and occurrence context.
2. Shared resolution composes explicitly applicable catalogue mappings, definitions,
   overrides, supersessions and unresolved/conflicting attributes into `FieldMeaning`.

The shared input is a concrete `FieldOccurrence` carrying source identity, published
field/binding, scoped source attributes and temporal bindings. It has no `Cr6Dataset`
dependency and does not demand that every domain expose `exposure_rows`.

Mapping applicability must not substitute report date for every effective date.
For this first CR9 slice, use explicit document/dataset/field-scoped mappings to pin
the applicable definition revisions after source review. Unknown/partial temporal
metadata is preserved and is not proof of applicability to a narrower date range.
Keep unsupported meaning unresolved while retaining supported attributes and numerical
conversions. Keep existing CR6 date-scoped behaviour intact. A general role-sensitive
effective-period matcher is deferred; explicit mappings supply this slice's selection.

Minimal catalogue declaration change: allow `MappingScope.observation_from` and
`observation_to` to be absent for explicit CR9 occurrence-scoped mappings. Existing CR6
mappings retain their date bounds and matching behaviour. The CR9 adapter selects by
document/dataset/record-or-field scope; it does not pass a fabricated observation date
into the CR6 matcher. Initially use definition revisions without date restrictions
where their source applicability is established by those mappings. A date-restricted
definition lacking established applicable timing remains unresolved; selecting its ID
alone does not bypass its restriction. Shared assertion composition receives the
applicable mappings/definitions selected by the domain adapter. No temporal evidence
reference kind or temporal assertion vocabulary is required for the source-only tags.

Do not build a calendar-expression or interval-inference engine. Exact-document
mappings and evidence-backed decisions are sufficient for these selected reports.
The spike must demonstrate one CR6 and one CR9 field using the shared composition
without changing existing CR6 interpretation results.

## 7. Conformance, outputs and storage interfaces

Keep concrete `Cr6Pipeline` and add `Cr9Pipeline`. Both receive saved Bronze and the
selected catalogue; neither performs I/O. Composition explicitly supplies both to
`ConformanceOperation`. Dispatch recognised dataset types once into their respective
domains; mixed CR6/CR9 bundles must not lose their CR9 datasets through CR6 filtering.

Extend `SilverCandidate` with named `cr6` and `cr9` outputs. Each output owns its
domain's named relations and table declarations. Shared storage iterates the combined
declared inventory; avoid a plugin registry or a dictionary of arbitrary tables.
Absent domains yield declared typed empty relations. Full replacement covers both
domains in one transaction, so omitting CR9 on a later complete rebuild removes its
previous rows rather than leaving stale tables.

`Cr9Output` includes typed observations (three Decimal(16,8) rate fields and four
integer counts), source context/field/meaning relations following the CR6 pattern,
and temporal descriptor/binding relations. Shared metadata row models can be reused
where their fields genuinely match; CR9 contexts must not inherit CR6's required
snapshot date. Temporal rows flatten components/statuses; evidence is related rows.
No universal numeric EAV storage and no JSON column hiding the temporal bindings.

CR9 relationship rows must retain parent and child endpoints as
`(observation_id, field_key | None)`, plus source scope, kind and evidence. A null
field key denotes a whole-row endpoint. Thus a row's `new_defaulted_borrower_count`
can be a subset of that same row's `defaulted_borrower_count` without becoming an
indistinguishable self-edge. ANZ aggregate relationships can still address whole
rows. Existing CR6 row-only relationship declarations remain unchanged; do not reuse
them for CR9 field endpoints. Master copies these endpoint columns and evidence.

Mountainash expressions own numeric conversions, metadata projections and joins.
Derive declarations from row dataclasses and use native conformance. Storage remains
`mountainash-data`/DuckDB; Settings layering and file transport retain their owners.
The disposable spike will establish exact relation membership and physical declarations
against pinned APIs before an implementation plan treats them as settled contracts.

Master concatenates corresponding persisted domain relations with producing revision
IDs, preserving occurrences. Reconstruction dispatches by domain to source-shaped
numeric tables using persisted numbers and retained source bindings. Temporal metadata
is accessible through named output relations; reconstruction does not attach one
misleading observation date to the dataframe or silently aggregate rows.

## 8. Identity, vintages and transport

Use existing bundle/dataset/source-record/field identity, independent of mutable
semantic classifications. A complete retained occurrence reference includes the
selected Bronze output version. Distinguish:

- **Document vintage:** document ID, reporting date and known publication date.
- **Measured time:** field-bound descriptors above.
- **Extraction revision:** selected Bronze output version for that source document.
- **Interpretation revision:** selected catalogue definitions/mappings/decisions.
- **Publication revision:** staging/master materialisation identity.

A second report repeating a historical value is a second published occurrence, even
when the measured period and value agree. A corrected extraction of the first report
is a new Bronze version of that occurrence, not a new bank vintage. Full rebuilds
select the intended version per logical bundle; historical versions remain retained
inputs, not additional additive observations in that selection.

An explicit bank restatement is captured with its qualification and source reference.
Reuse existing catalogue evidence references to identify a predecessor when established;
new predecessor-link machinery waits for a concrete source case. Unresolved predecessor
identity stays unresolved. Do not generate supersession edges by comparing numbers or
suppress the prior published occurrence. Source statements and researcher decisions
remain distinguishable.

Retain the `cr6-v1` reader/writer unchanged for existing saved outputs. Add one explicit
new mixed-domain wire version, with CR6/CR9 dataset discriminators and temporal metadata.
New extended extraction outputs use new output versions; never rewrite retained `v1`
bundles. Both codecs reconstruct the same supported Python CR6 domain objects. There
is no compatibility layer for hypothetical domains or unreleased alternate formats.

Existing mutable-publication and manifest limitations still apply; this spec does not
introduce historical database snapshots or automatic code/environment pinning.

## 9. Observable acceptance examples

These are design requirements for independent development evidence, not runtime gates.

| Call / scenario | Expected result |
|---|---|
| Conform a mixed CBA CR6/CR9 saved bundle | Both named outputs; CR6 results preserved; CR9 annual and history timing remain distinct |
| Resolve Westpac first-band default count | Integer 385, with new-default count 7 linked as subset, annual interval retained; no annual default rate manufactured |
| Resolve NAB current/previous counts | 198124 and 215531 with respective 2025-09-30 / 2024-09-30 measurement bindings regardless of column order |
| Resolve Westpac ten-year historical rate with unknown bounds | Value retained and converted to fraction; duration established, endpoints unresolved; publication succeeds |
| Capture ANZ mortgage subtotal | Published 0.62% becomes 0.0062, with five-year history and exclusions; no band average substituted |
| Select two reports repeating the same measured period | Two source occurrences retained, queryable by period and vintage; no automatic winner or total |
| Select a corrected Bronze version or catalogue revision | Rebuilt interpretation/value reflects explicit selection; previous retained inputs remain reproducible within current provenance limits |
| Reconstruct persisted CR9 then rebuild master | Source-shaped values and metadata remain linked; master copies saved staging results rather than reinterpreting them |
| Read existing `cr6-v1` | Existing CR6 objects and conformance results preserved |

Revision-comparison examples using invented later values must be labelled synthetic.
The selected reports establish temporal variety but do not themselves prove a
same-bank cross-vintage restatement. Acquire and inspect another real vintage before
claiming demonstrated historical-revision discovery.

Ordinary parsing, arithmetic and I/O errors propagate from their existing owners.
No new validation stage, unknown-semantics refusal or analytical-eligibility error
is introduced. Independent source goldens cover values, axes, temporal bindings,
missingness and notes; meaningful integration proof covers persisted reconstruction.

## 10. Cost, deferred work and next checkpoint

After spike approval, expected production reach is shared extraction metadata and codec, a CR9 source/domain
module, the catalogue resolution seam, explicit composition and shared storage inventory,
plus four bespoke extractors/goldens. This is several hundred lines of processing/model
code plus source fixtures, not a small metadata-only change. This is an estimate, not
measured implementation evidence. Four-bank extractor expansion follows spike approval.
Exact cost depends on the
spike; stop for rescoping if it demands a generic framework or broad CR6 rewrite.

[Metadata ingress](../../a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md)
and [constructor validation](../../a.backlog/techdebt/constructor-validation-separation.md)
remain deferred. Do not expand their existing adaptations/checks into new frameworks.
New declarations do not copy constructor validation; any required new ingress adaptation
must be surfaced rather than silently broadening the approved CR6 exception.

After researcher review, the next deliverable is a **disposable shape spike**: one
source-backed Westpac CR9 row with multi-time metadata alongside CR6, through shared
resolution, conformance and persisted readback. Include CBA's partial-year history
descriptor and ANZ's aggregate as small shape examples. Minimum scaffolding, no test
suite or production extractor expansion. The researcher reviews interfaces/data flow;
only an approved spike leads to a fresh implementation plan and real implementation.
