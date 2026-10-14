# Metadata-driven extraction and contextual conformance

Date: 2026-10-13.

Status: **Design direction and disposable spike shape APPROVED by the researcher,
2026-10-13.** The researcher subsequently approved production implementation under the
[implementation plan](../plans/2026-10-13-metadata-driven-extraction.md), including its
production contract details and checkpoint sequence; Tasks 1–3 are implemented and
verified and accepted at checkpoint A on 2026-10-14 (195 passing tests).
Tasks 4–6 are implemented across all twelve selected reports, with 200 tests passing;
checkpoint B acceptance is pending and Task 7 remains unexecuted.
The disposable code remains reference only and is not the implementation base.

## 1. Ask and scope

Define each extraction through singly owned physical-source, semantic and context
metadata, and use those bindings throughout capture, retained Bronze and Silver.
Tables, fields, axes, cells and comments all participate without losing their
different structures or the original evidence.

Governing decisions: [contextual occurrences](../../../01.principles/a.architecture/contextual-source-occurrences.md),
[metadata-driven journey](../../../01.principles/a.architecture/metadata-driven-extraction-and-conformance.md),
[capture and tag](../../../01.principles/a.architecture/capture-and-tag-for-research.md),
[correction-safe identity](../../../01.principles/b.data-semantics/correction-safe-identity.md),
[Mountainash-first](../../../01.principles/d.coding-practices/mountainash-first.md)
and [separate validation](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md).

The target covers the existing four-bank 2023/2024 source tables and 2025 CR6/CR9
captures. A small spike probes that responsibility boundary; it is not permission
to narrow the eventual model to one bank. CR1/CR2, liquidity, new acquisitions,
analytical reconciliation and Gold calculations remain outside this delivery.

## 2. Existing capability and design choice

| Existing owner | Reuse | Actual gap |
|---|---|---|
| `extraction/source_tables.py`, `models.py`, `temporal.py` | Typed payloads, axes, qualifiers, relationships, partial knowledge and timing | Construction and applicability largely live in each extractor; context and evidence addressing are not uniform across occurrence kinds. |
| `catalogue/models.py`, `resolve.py` | Concepts (including roles/populations), measures, decisions, versioned mappings, explicit overrides and conflict composition | `FieldOccurrence`, `MappingScope` and `FieldMeaning` are field-shaped; non-cell occurrences lack the equivalent resolution path. |
| `domains/source_tables/` | Shared source-table conformance, 18 relational outputs and persisted reconstruction | Meanings and temporal bindings use cell keys; table context and evidence assumptions constrain shared comments and row-specific resolution. |
| `storage/`, `workflow.py` | Saved-Bronze handoff, declared write/read inventory, staging/master replacement | References do not automatically retain all metadata/code inputs; new binding metadata needs explicit transport and readback. |

**Recommendation: compose typed metadata declarations in ordinary Python, with
serialisable snapshots and small explicitly supplied physical operations.** The
existing code already uses dataclasses, catalogue revisions and direct stage calls.
A command or one-off script cannot supply shared authoring/resolution responsibilities
across these consumers; extending the existing modules is sufficient. No new package
is needed.

Keeping complete imperative extractors and adding helper constructors would leave
ownership of definitions split across parsing and conformance. Moving all authoring
into JSON/YAML plus a parser language would add a second execution system without
evidence that the source layouts fit it. The recommendation allows reviewed metadata
reuse while retaining Python for difficult physical sourcing.

These are proposed design choices, not further principles: Python authoring, retained
metadata snapshots, explicit target bindings, and extension of the current catalogue
and source-table path. The spike must establish their usefulness and cost.

## 3. Authoritative metadata and captured occurrences

The following are logical responsibilities, not one module or database table each.
Names describe the proposed interface vocabulary.

| Responsibility | Defined once | Consumers |
|---|---|---|
| Physical binding | Revision identity, selected document/page/region or text anchors, operation identity/parameters and named output slots | Physical operation, capture assembly, provenance |
| Semantic definition | Existing concept/measure/role revisions, assertions and researcher decisions | Occurrence resolution, conversions, research queries |
| Context definition | Revisioned, evidence-backed entity/population/regulatory assertions, segment or temporal descriptors and their roles | Table/axis/field/cell/comment bindings and resolution |
| Occurrence binding | Stable local identity and kind, physical slot references, definition/context references, declared relationships and applicability | Capture assembly, Bronze retention, Silver resolution |
| Extraction definition | Revision identity, reviewed selection and composed bindings for one source bundle | Extraction invocation, retained capture manifest |

Reuse `ConceptRevision`, `MeasureRevision`, `SemanticAttribute`, `TemporalDescriptor`
and source structural types where their meaning fits. Physical/context/extraction
declarations need retained revision identities; they are not new parallel financial
catalogues. Extend the existing revision/reference vocabulary only for those concrete
responsibilities. Financial definitions continue to live under `catalogue/`.
Use the bundle-local snapshot and existing revision conventions first; independent
revision stores or additional lifecycle machinery are deferred unless a real consumer
requires them.

Source declarations live beside the selected source under `extractions/`; reviewed
common declarations can be ordinary imported objects. A new year explicitly composes
its selection and bindings. Importing a common definition does not automatically
carry a previous report's dates, populations, qualifiers or capture selection forward.

### Occurrence shape and identity

An occurrence references its source evidence, semantic assertions and applicable
context; any of these can be plural or partly unresolved. Table/axis/field/comment
occurrences retain labels/text and structure; numeric and lexical cells retain their
typed payloads. A comment's text and its interpretation are separate objects linked
by evidence, not two copies of a statement maintained independently.

Use a kind-qualified address: bundle identity, scope, occurrence kind and local ID.
Scope is the existing dataset ID for table-local content, or bundle scope for content
shared across tables. The kind distinguishes a field from an axis or cell with the
same local spelling. Retain current dataset/local IDs when adapting saved captures;
do not generate IDs from canonical meaning, numeric values or current labels.
Bronze output version and producing Silver revision identify retained versions of
that occurrence; neither replaces its logical source identity.

A shared glossary paragraph is captured once at bundle scope and linked from the
tables/fields it qualifies. If a note is physically repeated, each printed occurrence
retains its own identity even if the text agrees. A numeric observation in a note has
its own cell address linked to that comment; it is not forced into the table body.
Researcher annotations retain decision/author provenance rather than a fictitious
PDF location, using the catalogue's interpretation-decision responsibility.

### Context composition and applicability

Context means semantic applicability, not execution settings. Source selection,
reporting vintage and extraction revision also remain explicit, but cannot supply a
missing population date, exposure geography or historical boundary.

Bindings name the context contributions that apply. Shared table/row/field context is
authorable once through explicitly declared target collections; assembly materialises
the resulting occurrence references. There is no implicit walk up physical parents
and no rule that a nearer header wins. A field can receive its table context plus a
row population and distinct temporal roles without copying their definitions.

Context contributions use the same assertion composition rules as semantic mappings:
equal supported assertions can combine evidence; unresolved information does not
erase a supported assertion; incompatible supported assertions remain conflicting.
Combining provisional support does not promote it to established.
An explicit override identifies the replaced contribution and affected attributes.
Whole-revision supersession remains distinct. This extends the existing composer to
context contributions; it must not create a second precedence algorithm.

Temporal applicability is role-specific. A mapping requiring a measurement date
receives the established measurement binding, not the report date or history-window
end. A missing applicable date leaves the affected time-restricted attributes
unresolved; independently applicable mappings and conversions remain available.
It does not discard the occurrence. Exact source mappings can remain unrestricted in
effective time as they do today. No automatic derivation of yearly history components
or cross-vintage semantic equivalence is proposed.

## 4. Physical sourcing and bespoke interface

Proposed conceptual calls (not existing public APIs):

```text
physical_operation(document, physical_binding) -> captured fragments
capture(document, extraction_definition, supplied_operations)
    -> captured bundle
conform(saved_bundles, selected_interpretations) -> Silver candidate
```

The extraction definition's snapshot supplies the selected physical/context declarations
and any catalogue definitions used by capture. Construction loads those explicit selections;
capture does not resolve references through an implicit current catalogue. Their
serialisable revisions supply the retained snapshot described below.

Each physical operation receives only its document and declared physical parameters.
It returns named fragments: original tokens/text, order and actual source locations.
It may return a matrix or several passages from one operation. Physical outputs do
not select a canonical measure, infer financial applicability or write Silver.
The assembly step binds fragment slots to declared occurrences and context.

For example, ANZ's matrix operation receives page 45 and the reviewed column
boundaries. It returns separate headers/cells with their physical locations. The
metadata binding associates the mortgage row with pre/post-framework evidence and
the NZ row with its separate qualification. Changing column geometry alters the
physical binding; changing which occurrence a qualification applies to alters its
contextual binding, not the matrix algorithm.

Use an explicit Python mapping from declared operation names to callables at assembly,
not automatic plugin discovery. The retained definition stores the operation identity
and parameters; executable callables are not JSON-serialised. A common paragraph or
grid reader is reused only where its physical behaviour is genuinely common. Font
filtering, unusual pagination or merged-cell traversal can use a source-local function
under this same input/output seam.

The binding supplies declared value kinds and source-supported missing-token meanings.
Shared parsing turns comma/percent/accounting tokens into Decimal/integer/text using
the existing primitive conventions. It preserves the original token and displayed
precision. Thus Westpac's `N/A` can remain an explicitly inapplicable decimal-field
occurrence without teaching a geometry operation financial semantics.

Source structure is metadata too: the reviewed field/axis selection declares ordering,
roles, native bands and relationships. Grid assembly can expand an explicit ordered
set of field/band bindings; this does not require one handwritten definition per cell.
Captured header tokens remain evidence rather than being replaced with expected
labels. A changed or additional source field requires source review and an updated
selection, not automatic matching to an old semantic definition.

Malformed PDF tokens, unavailable operation names and I/O/cast failures propagate
from their owning operations. No new completeness, precision or publication validator
is added. Independent source expectations detect incorrect definitions and omissions
outside the execution path.

## 5. Bronze retention and Silver resolution

```text
PDF + selected extraction definition + physical operations
          -> fragments -> bound source occurrences
          -> saved Bronze (payloads, evidence, definition snapshot)
          -> reload + selected interpretation revisions
          -> resolve occurrence meanings/context -> Mountainash conformance
          -> existing staging publication -> master -> reconstruction/research
```

### Bronze

Retain original values/text, structure and applicability bindings, together with a
serialisable snapshot of the metadata revisions actually used. This includes capture
selection, physical operation identifiers/parameters, context declarations and any
referenced semantics used during capture. Repeated definitions in a bundle snapshot
are stored once and referenced; a materialised snapshot preserves the same revision
identity and is not another editable authority.

The PDF remains in `raw/`. Record the caller-supplied implementation identifier and
dependency information through the existing provenance machinery; re-extraction also
requires retaining the corresponding operation code. Neither a snapshot nor a Git
label alone promises archival reproducibility. Git remains unnecessary at runtime.

The richer bundle requires a new explicit wire version rather than modifying
`cr6-v1`, `disclosure-v2` or `disclosure-v3` in place. Final wire fields follow the
spike-reviewed model. The source codec and `mountainash-files` remain the transport
owners; ordinary saved output versions retain earlier captures.

### Resolution and conformance

Generalise the occurrence-selection/composition seam from `FieldOccurrence` to the
kind-qualified occurrence address. Existing financial mapping addresses retain their
meaning through an adapter; new mappings can target a table, row/column/header,
field, cell or comment. No artificial numeric field is created to resolve a comment.

Broaden the existing mapping/evidence references and output meaning keys accordingly.
Reuse concept/measure/decision revisions and the composer for semantic assertions.
Conversion applies only to a value-bearing occurrence with a declared source unit
and result kind. Definition/context resolution does not depend on having a number.
Mapping provenance records which occurrence and contribution established the result.

Resolve source-backed context and selected interpretation refinements alongside each
other, retaining evidence/decision distinctions and conflicts. Explicit revised
interpretations may change the resolved meaning without mutating Bronze's captured
bindings. This supports a researcher correcting applicability from retained evidence
without rerunning physical extraction. If the evidence was missing or mis-extracted,
a new Bronze capture is needed instead.
Selected interpretation revisions remain durable rebuild inputs outside disposable
Silver; the capture snapshot does not contain later corrections.

Collect dataset/bundle-sized records before constructing Mountainash relations.
Use the current dataclass-to-TypeSpec declarations, existing declared decimal slots
and native relation expressions for joins, selection and conversions. Preserve money
`Decimal(16,2)`, scalar `Decimal(16,8)`, integer counts and original source precision;
this proposal does not revise numeric policy or infer types from magnitudes.

Known unit conversion can yield a normalised value when canonical meaning is unknown.
Unresolved conversion leaves the source value available. Conflicting meanings and
partial temporal bounds remain queryable; conformance does not adjudicate research
comparability or reconcile financial totals.

### Persistence and readback

Extend the existing source-table output responsibilities rather than adding a second
parallel database pipeline. Table, field, axis, cell, comment, segmentation and
relationship data retain their typed collections. Shared references, evidence,
context contributions and resolved meanings gain occurrence-qualified owners and
bundle scope where required. Context definitions and their occurrence references
must be persisted, not reconstructed from Python defaults at readback.

The current 18-table layout is the starting point, not a required table count.
In particular, cell-only meaning/temporal keys and table-only evidence keys cannot
serve the new responsibility unchanged. The spike must demonstrate a minimal flat
projection and preserved joins before final DDL is set. This is not a universal
payload/EAV table; common reference addressing does not erase typed content.

One declared inventory continues to drive write/read/master copying, including typed
empty outputs and removal under full replacement. Metadata consumers and technical
storage declarations reference the authoritative definitions; an added source measure
must not demand another bank/year-specific Silver transformation.

Reconstruction uses persisted cells, ordering, labels and bindings. Researchers can
query physical evidence, applicable context and resolved meaning for a comment or
axis as well as a number. Master copies persisted results and producing revisions;
it neither reconforms nor selects a preferred reporting vintage. The existing
[mutable-path publication limits](../../../architecture.md#current-publication-and-provenance-limits)
remain; this design does not introduce a snapshot database service.

### Existing Mountainash capability

The repository pins Mountainash `c98f35ace19562dac0612fdd9f6c580a59bdc5f8`.
Installed API inspection on 2026-10-13 confirms `ma.relation(data)` and
`extract_from_dataclass(dataclass_type, preserve_optional=True, **metadata)`.
Existing `domains/source_tables/contracts.py`, `pipeline.py` and `storage/` exercise
flat dataclass ingress, declared conformance and `mountainash-data` DuckDB persistence.
This supports reuse of those paths, not a claim that the new reference shape has been
executed. Prove it in the spike; reproduce and track any required upstream defect
under the existing policy rather than adding an unapproved local workaround.

## 6. Worked cases and observable acceptance

These are development expectations, not processing-time gates. Existing independent
goldens remain the source authority; metadata declarations must not generate their
own expected results.

| Call / case | Required observable result |
|---|---|
| Capture ANZ 2023 retail backtesting from reviewed declarations | Five values (`0.93`, `0.77`, `1.01`, `18.69`, `1.40`) survive; estimated-PD history 2018–2022, EAD 2018–2023, LGD 2017–2021 and actual-outcome cutoffs remain separately bound. |
| Capture ANZ reform matrix with bespoke geometry | Separate pre/post headers and NZ blank cell survive; bindings retain their distinct scopes without interleaved text. |
| Capture CBA June 2023 LGD and its comment | LGD field/cells, overlay comment and `$7.4bn` note observation remain linked but separately addressable; 2022 panels do not acquire the overlay. |
| Reuse one reviewed context or measure in two source bindings | Same definition revision is referenced; physical evidence and occurrence identities remain distinct. |
| Resolve NAB main and RBNZ rows | Different population/floor qualifications survive in the same table; no aggregate/subset relationship is invented. |
| Read Westpac 2022 default PD and compare with an absent field | `N/A` occurrence has its original token and inapplicability; absent field has no fabricated occurrence. |
| Resolve differing supported context assertions without an override | Both assertions/evidence remain with conflicting status; neither row order nor narrower scope silently wins. |
| Apply an explicit interpretation correction to saved Bronze | New Silver meaning/mapping revision, unchanged captured value/source address; unrelated occurrences retain their meanings. |
| Query a time-restricted definition without its required temporal role | Meaning remains unresolved; no document-date substitution and no loss of the source occurrence. |
| Publish both original and comparative 2023 observations | Different source-vintage occurrences survive even where their financial values agree. |
| Read back all occurrence kinds after master publication | Payloads, ordered paths, comment links, context and semantic revisions are available from persistence; no re-extraction. |
| Select fewer source bundles for a full rebuild | Removed occurrences and their dependent published relationships disappear from the output; retained Bronze remains intact. |

Evidence for these cases: source reviews for
[ANZ](../../../../extractions/au/anz/2023-09-30/aps330/review.md),
[CBA](../../../../extractions/au/cba/2023-06-30/aps330/review.md),
[NAB](../../../../extractions/au/nab/2023-09-30/aps330/review.md) and
[Westpac](../../../../extractions/au/westpac/2023-09-30/aps330/review.md).

## 7. Compatibility and bounded migration responsibility

Retained files and current public `.cr6`, `.cr9` and source-shaped research outputs
remain usable. Read existing formats through their existing decoders. Adapting old
capture material must not fabricate physical extraction declarations that were never
recorded: preserve its original evidence and extractor provenance, marking the absent
declaration knowledge explicitly. Legacy acceptance does not require re-extraction.

The new model is the target owner for capture and contextual resolution. Existing
domain-specific paths continue to serve retained inputs until equivalent projections
are demonstrated. Migration moves a supported source path once and retires its
superseded semantic assembly; it does not maintain two separately authored sets of
definitions. Modern domain outputs remain named projections of actual compatible
source content, not a requirement to invent modern fields in historical sources.

The subsequent implementation plan must cover existing four-bank capture behaviour
and saved-format compatibility, including all source qualifications and temporal
roles. It may sequence that proof by source/model. The small spike below establishes
shape only and cannot claim completion of that migration.

## 8. Disposable spike and review boundary

After researcher review of this draft, propose a throwaway script with ordinary
Python declarations for **ANZ September 2023's five-cell mortgage backtesting row**
and its governing comments/context, plus the reviewed reform-matrix evidence. This
tests all occurrence kinds, field-specific temporal roles and genuinely bespoke
physical sourcing with the same interface. Preserve the existing production files.

Run PDF -> declared physical operations -> saved/reloaded metadata and values ->
contextual resolution -> Mountainash/DuckDB -> readback, early in the probe. Then
demonstrate a revised interpretation over the saved capture, without another PDF
read. Use independent existing source expectations for comparison; no new test suite
or production transport implementation is needed for the disposable probe.

Also inspect the proposed bindings for the CBA note and NAB population cases against
this draft. If they demand another model or special conformance path, revise the
design rather than adding exceptions around the ANZ example.

Cost estimate to be tested, not a quota: a few hundred lines for the disposable
probe; the production change is multi-module work in extraction contracts/assembly,
catalogue resolution, codec, relational metadata projection and retained-source
adapters. Source declaration migration is additional. The first persisted example is
the progress checkpoint; no implementation task breakdown is approved.

Questions for spike-shape review: does the explicit Python declaration/operation split
make the three responsibilities independently maintainable; do explicit scoped
bindings describe applicability clearly enough; and does a retained metadata snapshot
meet the required reproducibility boundary? The design direction is approved for the
probe; its executable shape remains for researcher review. Final physical fields and migration sequencing
depend on the spike; the principles and source acceptance behaviours do not.

## 9. Draft review dispositions

Independent correctness and complexity reviews completed on 2026-10-13. Complexity
cuts were applied first: defer revision-store/lifecycle machinery beyond the current
revision conventions and retained bundle snapshot; remove an arbitrary code-volume
threshold while keeping the early persisted-path checkpoint.

Correctness review found no required defect. Clarifications retain provisional status,
independently applicable conversions when temporal meaning is unresolved, and later
interpretations as durable rebuild inputs. No upstream-dependent finding was identified;
the new runtime shape remains unproven until the spike. Review completion does not
constitute approval of an implementation plan; researcher approval for the spike is
recorded separately above.

## 10. Disposable spike evidence

The approved probe ran on `spike/metadata-driven-extraction`, seeded from the
specification branch in the base checkout. Code remains disposable under
`spikes/metadata-driven-extraction/`; it must not become the production implementation
base. Execution config, metadata/source declarations, physical operations, capture and
saved-data conformance are separately inspectable.

ANZ's selected row and reform matrix produced 42 occurrences spanning all seven kinds
and five financial cells. The selected numbers, five paragraphs and two matrix
evidence summaries agree with the independent source goldens. A separately retained,
source-supported loss-basis refinement changed the actual-LGD interpretation while
preserving all five persisted numbers. A fresh-process saved-only reconstruction
opened no PDFs and imported neither the source configuration nor the physical readers.

Retained run: `/tmp/opencode/metadata-extraction-spike-zcze07kq/`.
Logs: `/tmp/opencode/metadata-driven-spike-final.log` and
`/tmp/opencode/metadata-driven-spike-saved-only.log`.

The researcher accepted this shape on 2026-10-13 ("looks good!"). This proves the
selected separation and persisted path, not production transport,
all-kind catalogue decoding, cross-bundle identity, master consolidation or migration.
The spike's lightweight composer adapter and simplified temporal attributes are not
final physical contracts. No new tests were authored for the spike. The implementation
plan is drafted independently, with fresh production code and TDD required after
plan approval.
