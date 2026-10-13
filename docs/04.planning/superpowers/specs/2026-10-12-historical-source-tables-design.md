# Historical source tables and composable metadata

Date: 2026-10-12

Status: **APPROVED by the researcher, 2026-10-12**, after independent correctness
and complexity reviews. The complete four-bank 2024 implementation and documentation
merged through PRs #13/#14 into `develop` at `7930a3a` on 2026-10-13, after consuming
upstream PR #377 and completing final reviews. The
[implementation plan](../plans/2026-10-12-historical-source-tables.md) was also
approved on 2026-10-12 and records the CBA checkpoint evidence and review boundary.

**2026-10-13 ownership supersession:** The approved
[contextual-occurrence](../../../01.principles/a.architecture/contextual-source-occurrences.md)
and [metadata-driven processing](../../../01.principles/a.architecture/metadata-driven-extraction-and-conformance.md)
principles replace this specification's bespoke-extractor ownership and field/cell-only
resolution boundary as the future design direction (§§2–5). Its retained formats,
source fidelity and delivered behaviour remain compatibility evidence. The
[replacement design draft](2026-10-13-metadata-driven-extraction-design.md) is not yet
approved or implemented; the execution history below remains historical evidence.

## 1. Ask and scope

Capture complete selected historical mortgage tables, preserving changing fields,
structure and meaning so both financial observations and disclosure evolution can
be researched across reports.

First delivery: CBA June 2024 and Westpac, NAB and ANZ September 2024 mortgage
exposure-by-risk-band and risk-parameter backtesting tables, including their
comparative panels, all mortgage metrics and applicable notes. Mortgage blocks are
the selected scope, not every portfolio in the surrounding tables. Separately
presented loss-experience tables are not implicitly selected; regulatory expected
loss appearing within a selected table is included. Preserve the existing 2025
CR6/CR9 workflows and retained formats. Demonstrate structural comparison with
the existing Westpac 2025 CR6/CR9 selections; broader legacy conversion coverage
can follow actual research selections.

The [source inventory](../../../00.ideation/2026-10-12-historical-source-inventory.md)
identifies 574 selected table-body cells across the four PDFs, plus supplementary
reported figures in notes. It includes Westpac's p.58 comparative continuation and
NAB's separately named RBNZ mortgage backtesting rows on pp.40–42. Mixed NZ retail
aggregates in exposure tables are not relabelled as mortgages. Review counts are
design evidence, not independently approved goldens.

Governing decisions: [historical capture](../../../01.principles/a.architecture/historical-disclosure-capture.md),
[layered definitions](../../../01.principles/b.data-semantics/layered-metric-definitions.md),
[composition](../../../01.principles/a.architecture/composed-processing-and-organisation-staging.md),
[identity](../../../01.principles/b.data-semantics/correction-safe-identity.md),
[Mountainash-first](../../../01.principles/d.coding-practices/mountainash-first.md),
and [separate validation](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md).

## 2. Existing capabilities and smallest adequate change

Existing source models already describe axes, published fields, bands,
qualifications, relationships, typed reported numbers and temporal descriptors.
The catalogue already separates `ConceptRevision`, `MeasureRevision`, scoped
`SourceMappingRevision` and researcher decisions. `compose_field` combines selected
assertions, references, conversions, overrides and conflicts. These remain owners.

The gaps are concrete: fixed numeric row members; bindings addressed by Python
attribute names; lexical values stored indirectly in axes; CR6/CR9-only codec and
storage dispatch; and incomplete persisted source structure for cross-report queries.

Selected approach: add a source-table dataset and shared relational output alongside
existing domain outputs. A small adapter exposes retained typed datasets in this
shape. Bespoke extraction still owns PDF geometry. Shared capture owns source fields,
cells and metadata; domain-specific wide outputs remain projections.

Continually widening CR6/CR9 rows would require code/schema edits for each unfamiliar
measure. A universal ontology, plugin registry or per-year schema would add machinery
without improving the demonstrated capture. Neither is proposed. The cell-oriented
source table has a specific responsibility: faithfully representing selected tables.

## 3. Proposed source objects

Names below describe concrete responsibilities, not a requirement for separate
modules or one database table per Python type.

| Object | Responsibility |
|---|---|
| `SourceTable` | Dataset ID, composed metadata and cells; satisfies the existing `id`/`metadata` dataset protocol |
| Table context | Document date, source title/identifier, portfolio and existing knowledge-valued entity, perimeter, geography and currency; no mandatory common observation date |
| Published field occurrence | Local ID, original label/header path, unit/scale, qualifications and evidence; identifies a published measure or lexical field, regardless of orientation |
| Source axes | Existing ordered row/column/header/block items with full ordered header paths and evidence |
| Source cell | Local ID, published-field reference, leaf row/column references, context and segmentation references, typed reported payload, applicable qualification references |
| Composed metadata | Context, fields, axes, segmentations, qualifications, relationships and temporal descriptors/bindings |

Use the existing source structures where their meaning matches. A new table-metadata
container omits the legacy `ValueBinding.typed_field_name`; the cell itself supplies
its field and axis binding. Keep legacy `DatasetMetadata` and numeric rows intact.
Reuse the context members already demonstrated by CR9 without making CR9 the owner
of all source tables.

Each separately headed dated panel becomes a table dataset; one PDF still owns one
logical Bronze bundle. A table spanning continuation pages can remain one dataset.
Selection notes identify the exact mortgage blocks, panels and page locations so
an absent field is interpreted only within the captured scope.

### Values, axes and presence

Numeric payloads reuse `ReportedValue[Decimal | int]` conceptually (the concrete
generic instances remain Decimal or int). Add a lexical payload with original text,
optional interpreted text, missingness and source reference. Use explicit payload
discriminators in transport, not trial coercion between text, integers and decimals.

An absent published field has no occurrence. A published blank/dash has a cell and
original token, with source-specific missingness. Zero remains numeric zero. `N/A`
remains its original lexical token with source-supported inapplicability; it is not
silently reduced to an ordinary blank. Unknown semantics is independent of presence.

Headers and repeated labels are retained once as axis occurrences with ordered
paths. Leaf row/column references locate cells; field references express meaning.
A CBA measure can therefore lie on the row axis while its bands lie on columns.
Merged headers are represented by shared header paths, not duplicated value cells.
Lexical rating cells are values, not header text masquerading as measures.

Numerical notes also carry reported observations: retain Westpac's two supplementary
RWA figures and CBA's panel-specific overlay amount/scaling factor as supplementary
cells linked to the original qualification/evidence. A field records its source form
(`table_body` or `note`); note cells can omit leaf row/column positions and reference
their qualification instead. They are queryable with their own units and scope, but
are not inserted into the reconstructed table body or used to replace its totals.
Narrative years/window lengths remain temporal metadata rather than financial cells.

Keep native band boundaries and their knowledge statuses. Do not infer exclusivity
or exhaustiveness from adjacent intervals. Source relationships retain kind,
endpoints, scope, evidence and explicit exhaustive/disjoint status. Add cell endpoints
for within-row subsets; existing row/field/block/band endpoints retain their meaning.

### Identity

Logical source identity is `(bundle_key, dataset_id, local_occurrence_id)`. Field,
axis and cell IDs are explicitly assigned by the bespoke extractor, not generated
from canonical classifications or numeric values. IDs should survive corrections
to labels/values in that source where the occurrence is unchanged.

A retained reference additionally identifies the selected Bronze output version.
Silver rows identify their producing publication revision. A different document
repeating the same historical period remains a different occurrence. Rebuilds select
the intended extraction version; they do not add all corrections together.

## 4. Reuse and metadata composition

Three levels stay distinct:

1. Shared representation types describe cells, fields, axes and bindings.
2. Durable catalogue definitions describe reusable concepts, units and measurement
   conventions, with retained revisions and evidence.
3. Published field/cell occurrences identify what this source actually contains.

Use existing `MeasureRevision` plus composed semantic attributes as the reusable
field definition. Do not introduce a duplicate `FieldDefinition` catalogue hierarchy.
Two extracts may reference the same measure revision while retaining different
labels, locations, bands, periods and qualifiers. Genuine semantic changes select
different revisions/variants through explicit contextual mappings. Identical labels
alone never select a shared definition.

Shared temporal descriptors, qualifiers and bands are referenced by all applicable
cells within their source scope. Across documents, actual dates and evidence remain
occurrences; reusable measurement definitions can express relative temporal meaning.
Ordinary Python constructors can reuse a reviewed field-set declaration when useful;
no persistent template registry or automatic template inheritance is required.

For each cell, assemble its published field, context, segmentation, qualifications
and timing; construct an occurrence for the existing catalogue selection/composition
seam. Use the cell ID as the new adapter's source-record address and the local field
ID as its field key. Legacy adapters retain their original addresses and mappings.

Mappings reference exact source scope and definition revisions. Reuse existing
attribute-level override/supersession handling; no last-writer-wins or blanket
"nearest header wins" inheritance. Retain source statements separately from
researcher decisions. Unsupported meaning stays unresolved; conflicting assertions
and their alternatives remain queryable.

Temporal roles attach to cells through the existing descriptors. Preserve partial
dates, duration-only windows and unknown bounds. A table's date does not supply an
unstated measurement/cohort/history date. Historical mappings use explicit
occurrence scope; use unrestricted effective bounds where source-specific revisions
establish applicability. Restricted definitions lacking established applicable timing
remain unresolved, following the existing CR9 rule. This does not add a temporal
inference engine.

## 5. Conformance and persistence

```text
bespoke PDF extractor -> SourceTable in one source bundle -> saved Bronze
                                                               |
retained CR6/CR9 -> explicit source-table adapter ----------------+
                                                               |
                         catalogue + SourceTablePipeline.conform
                                                               |
                    named source-table relations in staging Silver
                                                               |
                     existing full-replacement master consolidation
                                                               |
                  source-shaped frames and structural research queries
```

Add one concrete `SourceTablePipeline`, a named source-table output on
`SilverCandidate`/`SilverOutput`, and explicit table declarations in the current
storage inventory. Preserve named `.cr6`/`.cr9` outputs and current call signatures.
Legacy inputs continue through their existing pipelines; new source tables feed
the source-table pipeline. The structural research example explicitly invokes the
independently callable source-table stage with its selected historical and legacy
bundles, then publishes that complete source-table output with the candidate. Do
not automatically duplicate every legacy input into structural output. This uses
ordinary stage calls and candidate composition, not a new workflow mode or policy.
Historical fields are not coerced into
modern CR6/CR9 outputs. Those outputs are alternative views, not additional exposure
occurrences to union with source cells.

The source-table output exposes these relational responsibilities:

- Tables/contexts, fields, axes and ordered axis-path references.
- Cells with field/axis/context bindings and source values/tokens/missingness.
- Segmentations, bands and cell membership; qualifications and scoped bindings.
- Relationships, endpoints and supporting evidence.
- Temporal descriptors, bindings and evidence.
- Resolved cell meanings, conversion factors, definition/mapping revision references,
  semantic assertions/alternatives and their evidence/decision links.

Reuse existing flat metadata row declarations where semantics and keys agree.
Source locations can be flattened as today; repeated references use related rows.
Fields, axes, bindings and interpretation links needed by structural queries remain
relational. Reuse native `extract_from_dataclass` and existing declaration augmentation;
the same declarations drive staging/readback/master. No schema-generation facility
is added. Preserve other evidence detail through the existing metadata conventions.

### Numbers

Bronze keeps exact Decimal values, original tokens and displayed precision. For the
selected sources, propose source numeric slots `Decimal(16,8)` and integer, with a
separate lexical slot. Conformed monetary results use `Decimal(16,2)` and rates or
dimensionless ratios use `Decimal(16,8)`, following existing policy. A field's declared
result kind selects its numeric slot; selection is never based on value magnitude.
Original tokens remain accessible alongside numeric projections.

Unit conversion can be established even when the measure definition is unresolved:
CBA average EAD `0.359` million remains a source number and can yield `359000` base
currency units. If conversion is unresolved, retain the queryable source value;
leave only the normalised result unresolved. Percent and ratio conventions come
from the source and mappings, not neighbouring columns.

The spike's 38-digit conformance target was unsupported by the pinned API. This
design uses the existing supported declarations, not a bypass. Source review and
development fixtures must establish that the selected source values are represented
exactly; a future requirement outside these declarations needs an explicit design
decision. This is not a runtime precision gate or a universal fifteen-year precision
claim. Working arithmetic follows the existing wider-cast path.

Mountainash owns relational projections, joins, conversions and concatenation;
`mountainash-data` owns DuckDB I/O and transactions. Flat dataclass-list ingress is
demonstrated by the spike. Keep Python assembly at the source/semantic boundary and
Arrow/Polars at interchange or dataframe output boundaries. Existing nested-ingress
debt is not expanded or refactored as part of this change.

All source-table relations participate in the same full-replacement publication
transaction as the existing outputs. Empty selections clear their prior contents.
Master copies persisted relations with producing revisions; it does not reinterpret
Bronze or silently choose a vintage. Existing mutable-path and manifest limits remain
as documented in [current architecture](../../../architecture.md#current-publication-and-provenance-limits).

## 6. Reconstruction and structural queries

Reconstruct source-oriented numeric/lexical dataframes using persisted cells and
ordered axes. IDs provide collision-free dataframe keys; associated metadata supplies
visible labels and full paths. Return table metadata alongside frames so repeated
`Predicted` headers are distinguishable by their parent paths. Numeric reconstruction
uses persisted source values, with normalised values available as a separate relation;
it must not substitute the input PDF or recompute from extractor output.

Provide one ordinary interactive example that selects retained 2024/2025 mortgage
tables and builds a field/structure inventory with Mountainash relations. Its output
includes document vintage, measured-time references, selected scope, table/field IDs,
source labels/axis paths, units, bands, definition/mapping revisions and knowledge
status. Unmapped fields stay in the inventory.

Researchers can compare this inventory to answer which fields appeared/disappeared,
which labels or header positions changed, and which definitions, bands or time scopes
differ. Source presence is determined from field/cell occurrences, not non-null
numeric results. Report changes and extraction/interpretation corrections remain
separate via their distinct revision axes.

Matching two fields across reports is an analytical choice supported by definitions
and explicit source selection. Unresolved equivalence is an output, not an automatic
rename or semantic-change verdict. Start with queries and a dataframe example;
do not introduce a structural-diff service, automatic similarity matcher, stored
change-event schema or mandatory historical snapshots.

## 7. Transport and compatibility

Propose `disclosure-v3` for bundles containing source-table datasets, with an explicit
`source_table` discriminator and typed cell payloads. Continue reading/writing existing
`cr6-v1` and `disclosure-v2` representations unchanged. New source-table bytes never
leak into an old wire version. Retain one logical bundle per source PDF and use new
output versions for new captures; do not rewrite retained outputs.

The legacy adapter is pure, consumes saved objects and does not reread PDFs. It emits
only actually published fields/cells from bindings, not every optional slot of a
modern row. Convert lexical ratings carried in legacy axes to lexical cells while
retaining original evidence and paths. Preserve all existing temporal roles, source
qualifications, band definitions and relationship endpoints; the abbreviated spike
adapter is not sufficient implementation.

Adapters are per existing model, not per bank or year. The first demonstrated
selection is Westpac's 2025 CR6 and CR9, giving real cross-vintage exposure and
backtesting comparisons. Exhaustive conversion of the other retained selections
is deferred; it is not necessary to preserve their existing processing. The adapter
does not migrate old numeric pipelines or physical schemas. Move shared declaration
helpers out of CR6 ownership only
where the new shared responsibility requires it; avoid unrelated refactoring.

Keep existing parser/transport checks on their retained paths. New declarations and
conformance do not add constructor validators, precision checks or publication gates.
Reuse primitive transport conversion as appropriate without copying the old automatic
roundtrip validation into the new path. Ordinary parse/cast/I/O errors retain their
existing owners. Constructor-validation separation remains deferred.

## 8. Observable acceptance

These are independent development expectations, not runtime validation.

| Scenario | Required observable result |
|---|---|
| Capture CBA 2024 mortgage average EAD | Published numbers and original bands retained; `0.359` million remains queryable even without a measure definition |
| Compare CBA exposure field inventories across vintages | No fabricated modern average-PD field in the older selection; added/absent fields distinguishable from blank cells |
| Capture Westpac 2024 portfolio-level backtesting | Every selected metric/panel retained at portfolio grain; no band observations manufactured |
| Query modern Westpac ratings and default-row blanks | Lexical `N/A`, blank and numeric zero remain distinct, with original order and paths |
| Two extracts reuse a reviewed measure definition | Same pinned definition reference, separate source field/cell IDs and evidence |
| A contextual qualification changes meaning | Applicable revised mapping/attributes and evidence visible; other source occurrences do not silently change |
| Unknown history bounds or conflicting meaning | Source cell and partial metadata retained and published; no document-date fallback |
| Retain within-row subset and source total | Query identifies scoped endpoints; it does not infer disjoint/exhaustive coverage |
| Persist/reload the source-table output | All captured cells, full header paths, scope, qualifications, timing and interpretation references survive |
| Reconstruct after changing a persisted source value in a development fixture | Frame reflects persisted value, not original Bronze number |
| Consolidate master and remove staging files | Source-table queries/reconstruction use persisted master; producing revisions remain traceable |
| Rebuild with fewer selected inputs | Removed source tables disappear from every related output; other retained inputs remain intact |
| Read retained CR6/mixed Bronze and run current examples | Existing `.cr6`/`.cr9` results and wire representations remain compatible |
| Compare structure across real Westpac 2024/2025 inputs | Portfolio versus band grain and changed fields exposed, while unresolved semantic equivalence remains explicit |

Author per-PDF goldens independently, covering all selected metrics, panels and
metadata. Existing goldens remain regression evidence. Plan the first real saved
Bronze → conformance → DuckDB → reconstruction path early, then broaden to full
four-bank historical capture and the selected Westpac legacy projections. Never
use the spike output as a golden.

## 9. Spike evidence, reach and review boundary

Disposable script:
`/home/ubuntu/git/discreteds/rwa-analysis-historical-spike/spikes/historical-table-shape/run.py`.
Successful artifacts: `/tmp/opencode/historical-table-shape-r2vrst48/`.
It retained 40 CBA 2024 cells, 12 Westpac 2024 cells and 72 modern Westpac cells;
eight relations matched on persistence/readback. It exercised the existing composer,
native flat-dataclass ingress and DuckDB reconstruction, including unmapped values.

It did not prove complete evidence/qualification handling, reusable definition sets,
all header paths, complete historical timing, full four-bank capture, a new codec,
master consolidation or a production migration. The researcher agreed the composable
source-defined direction; this proposal adds the details for review. The spike is
disposable and must not become the implementation base.

Expected reach: shared source declarations/codec, one source-table pipeline and
legacy adapter, storage dispatch/inventory, four bespoke historical extractors,
catalogue mappings, independent source fixtures and one research example. This is
a multi-module change likely on the order of one to two thousand production lines
plus source-specific fixtures, not four small parser edits. Planning should refine
that estimate against the approved contracts, not treat it as a quota.

Researcher approval permits implementation planning, not promotion of the spike.
New source evidence may refine unresolved financial definitions without blocking faithful
capture. Any required unsupported dependency path is reproduced and tracked with
its upstream owner; do not hide it with an unapproved local workaround.

## 10. Design review dispositions

Independent correctness and complexity reviews completed on 2026-10-12. Complexity
findings were applied before correctness triage:

| Finding | Disposition |
|---|---|
| All-eight legacy structural conversion exceeded the demonstrated comparison | Defer exhaustive legacy coverage; use explicitly selected Westpac 2025 CR6/CR9 for the first comparison, with adapters owned by source model rather than bank |
| A blanket JSON prohibition over-prescribed storage | Cut the blanket rule; retain relational structure/query links and existing evidence conventions |
| Declaration derivation could imply a new generator | Keep native derivation only: the inspected `extract_from_dataclass`/`model_spec` path already exists; add no generation mechanism |
| Correctness review | No material design defects identified; legacy mapping addresses/date selection, composed-definition reuse and complete persisted metadata remain implementation proof obligations |

No upstream blocker was established by these reviews. The unsupported 38-digit
conformance attempt is not required by this selected design; it is not treated as
an upstream defect or permission for a workaround. Review completion does not
constitute researcher approval or production acceptance.
