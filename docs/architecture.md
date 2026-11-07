# Current processing architecture

Updated: 2026-10-17. Describes four-bank CR6/CR9 and source-defined historical
capture. The 2024 historical implementation and documentation merged through PRs
#13/#14 into `develop` at `7930a3a`; the CR9 baseline merged through PR #9 at `32e5f6a`.

## Approved direction and current implementation

On 2026-10-13 the researcher approved
[contextual source occurrences](01.principles/a.architecture/contextual-source-occurrences.md)
and the [metadata-driven journey](01.principles/a.architecture/metadata-driven-extraction-and-conformance.md).
These supersede extractor/domain-container ownership as the governing target: physical
sourcing, semantic meaning and context are singly defined metadata consumed across
capture and conformance. The [new design](04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md)
and disposable spike shape are approved. The [implementation plan](04.planning/superpowers/plans/2026-10-13-metadata-driven-extraction.md)
was approved on 2026-10-13. Tasks 1–3 on `feature/metadata-driven-extraction`
implement the first ANZ 2023 v4 path, accepted at checkpoint A on 2026-10-14. The
remaining source migrations and CR6/CR9 projections were accepted at checkpoint B
on 2026-10-14, after 204 tests passed. Task 7 extends master lifecycle evidence;
final independent correctness and complexity reviews passed with no open findings.
Final verification recorded 205 passing tests. PR #18 merged into `develop` on
2026-10-14 at `e1e9245`.

### Checkpoint A: ANZ 2023 metadata-owned capture

`extractions/au/anz/2023-09-30/aps330/definition.py` owns the reviewed selection,
physical parameters, shared contexts and occurrence bindings. Its sibling
`physical.py` exposes only physical readers; the thin `extract.py` invokes
`run_capture`. Execution locations remain in existing session settings.

`CapturedBundle` uses separate `disclosure-v4` transport. Its snapshot retains
selected declarations and reusable definition contents without importing source
authoring files on reload. Physical fragments capture shared comments once;
source-table qualifications are materialised compatibility views of those bindings.
The existing v1/v2/v3 wire paths remain operational.

`catalogue/occurrences.py::resolve_capture` uses the existing composer for table,
axis, field, cell and comment occurrences. Explicit occurrence targets can select
a Bronze output version. Context and mapping revisions retain distinct provenance;
role-specific temporal applicability never substitutes a document date. Cell
numeric projection consumes the already resolved meanings.

The source-table inventory adds `occurrences`, `occurrence_links`, `contexts` and
`context_bindings`; existing assertion/mapping/evidence relations now have
kind-qualified owners. Shared definitions are retained at bundle scope, with
explicit references from occurrences. Reconstruction includes reachable shared
comments and contexts alongside local metadata. The same declared inventory drives
ordinary staging writes, readback and master copying. Task 7's lifecycle test covers
all 49 relations for retained and current captures, including bundle-scoped owners.
It mutates a persisted value and shared comment, deletes staging databases, and
checks reconstructed comment/context reachability and fewer/empty-input replacement.

`examples/anz_metadata_capture.py` runs the full 125-cell source, saves v4, deletes
its disposable copies of the PDF/authoring files and publishes a retained,
occurrence-targeted comment override from saved Bronze. Checkpoint A acceptance
authorises Tasks 4–6; this example does not establish the remaining migration's completion.

### Tasks 4–6: complete selected-source migration

All twelve selected reports now enter through a local `definition.py`, `physical.py`
and thin `extract.py`. Historical source identities, notes and temporal distinctions
remain unchanged. Modern snapshots additionally retain `DomainFieldBinding` records:
explicit cell-to-domain record/field addresses, without a second financial definition.

`SourceTablePipeline` resolves captures once. `project_cr6(source_output, bindings)`
and `project_cr9(source_output, bindings)` consume the resolved relations without a
catalogue, PDF or source module. Native Mountainash joins and expressions project
numbers, factors, qualifiers, timing, relationships and interpretation provenance.
The modern selection retains 36 CR6 rows, 33 CR9 rows and eight numeric frame keys;
its source view contains 729 cells, including 66 lexical rating positions.

Retained v1/v2 typed data is adapted to original source addresses; missing historical
capture declarations are not invented. The shared resolution owner preserves CR6's
observation-date policy, CR9's partial-time policy and v3's explicit field measurement
dates. Ordinary legacy selections retain their named domain views; explicit source
views remain available. Historical captures have no domain bindings and stay source-only.
Checkpoint B is accepted. Fresh Task 7 historical and modern runs preserve these
outputs; final independent delivery reviews remain pending.

The [principles](01.principles/README.md) own durable decisions. The
[strategic specification](04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md)
records the approved design and its history. Code declarations own exact fields and
physical table names; this guide explains how to use and extend that implementation.

### Supplementary adjustment evidence

The four 2025 definitions now compose source-local `adjustments.py` declarations
with the existing numerical-note contracts. `extraction/numerical_notes.py` expands
explicit physical passages and typed observation declarations into the existing
snapshot types; physical readers remain separately selected. The `rwa-adjustments`
selection groups 38 source observations (9 CBA, 14 ANZ, 10 NAB, 5 Westpac), including
supporting total rows and separately dated comparatives/events. It is not a new
published bank table or a new storage domain.

Classification is a resolved `qualification_meaning` attribute; quantity concepts
distinguish RWA, required capital, reported shares and CET1-ratio changes. Portfolio
labels are source field attributes. Explicit unit mappings, note text, source axes,
dates and occurrence links are retained in the existing source relations. Common
report entity/currency evidence is reused without inheriting mortgage/AIRB scope
onto group or operational-risk amounts.

The researcher-approved ANZ decision qualifies aggregate CR6 RWA/density, leaving
band allocation unresolved. `examples/rwa_adjustments.py` reads master and retains
NAB's $50m difference separately with calculation/input provenance. The existing
mutable-publication limits below still apply. See the
[source evidence and decision record](00.ideation/2026-10-17-rwa-adjustment-capture.md).

## Supported scope

Production extraction covers the selected mortgage CR6 blocks from CBA June 2025
and Westpac, NAB and ANZ September 2025: nine source rows and twelve measure fields
per bank. These counts describe the selected sources, not universal schema constraints.
Source dates, legal entities, geography, currency and regulatory perimeters remain
distinct. ANZ's selected AIRB block does not represent every ANZ-group mortgage.

The same source bundles now include selected CR9 blocks: eight rows each for CBA,
Westpac and NAB, and nine for ANZ including its subtotal; seven measure positions
per row. CR9 timing attaches to individual fields rather than a common observation date.
CR1/CR2 and liquidity remain research/design cases, not implemented domain pipelines.
Gold persistence and a reusable NumPy/SciPy capital engine are not implemented.
The application is ordinary Python, with examples and numeric dataframes for research.

Historical capture selects the 2023 and 2024 mortgage exposure/backtesting panels
from CBA, Westpac, NAB and ANZ: 46 dated datasets, 1,148 body cells and 15 numerical
notes. The 2023 extension merged through PR #15 into `develop` at `bd6926b`, after
independent reviews and verification. Each report vintage owns separate source occurrences,
including repeated comparative periods.
NAB main and separately named RBNZ mortgage backtesting populations remain distinct.
Selected Westpac 2025 CR6/CR9 can be explicitly projected as two source datasets for
structural comparison; that is a second view, not additional exposure to aggregate.

## Data flow and ownership

```text
Official PDF + raw/index.md
          |
Source review + independent golden expectations
          |
definition.py + physical.py → thin extract.py → CapturedBundle (v4)
          |
BronzeStore.save → retained bundle.json → BronzeStore.load
                                             |
Versioned catalogue release -----------------+
                                             |
                  shared occurrence resolution / SourceTablePipeline
                       source relations → CR6/CR9 projections
                                Mountainash relations
                                             |
                                  SilverCandidate
                                             |
                              organisation staging DuckDB

Selected current staging publications → SilverConsolidator → master DuckDB
                                                               |
Saved Bronze structure + persisted Silver numbers → source-shaped dataframes
Persisted source-table structure + cells → source-oriented numeric/lexical frames
```

| Owner | Responsibility |
|---|---|
| [`settings.py`](../src/rwa_analysis/settings.py) | Native Mountainash Settings layers; resolve execution paths against an explicit project root |
| [`composition.py`](../src/rwa_analysis/composition.py) | Construct concrete components; construction does not run processing |
| [`workflow.py`](../src/rwa_analysis/workflow.py) | `OrganisationSession` sequences independently callable stages; `RunResult` returns publication, tables and source bundles |
| [`operations.py`](../src/rwa_analysis/operations.py) | Run explicitly selected extractors and load the explicitly selected catalogue for conformance |
| [`extraction/`](../src/rwa_analysis/extraction/) | Typed declarations/snapshots, explicit physical invocation, captured fragments, source dataclasses and retained codecs |
| [`catalogue/`](../src/rwa_analysis/catalogue/) | Load and resolve concepts, definitions, scoped mappings, evidence and researcher decisions |
| [`domains/cr6/`](../src/rwa_analysis/domains/cr6/) | CR6 models, declarations, catalogue-free projection and source-unit reconstruction |
| [`domains/cr9/`](../src/rwa_analysis/domains/cr9/) | CR9 models, declarations, catalogue-free projection, field-level timing and reconstruction |
| [`domains/source_tables/`](../src/rwa_analysis/domains/source_tables/) | Source-defined cells/metadata conformance, explicit legacy adaptation and persisted structural reconstruction |
| [`storage/`](../src/rwa_analysis/storage/) | Bronze transport, paths, manifests, database connections, transactional publication and master consolidation |

Domain transformations receive data and interpretations; they do not open PDFs,
configuration files or database connections. Settings select execution locations;
the catalogue owns financial meaning. Dispatch explicitly selects CR6, CR9 and source tables;
the dataset protocol is not an automatic multi-domain plugin system.

## Source contracts and normalised Silver

`ExtractionBundle` holds datasets satisfying a small `Dataset` protocol. A
`Cr6Dataset` composes `DatasetMetadata` and exposes `exposure_rows`. Its saved
`cr6-v1` representation retains the earlier `records`/flat-metadata wire shape through
the codec. Python composition does not require rewriting retained Bronze or goldens.
Retained mixed bundles use `disclosure-v2` with explicit domain discriminators;
current declared captures use `disclosure-v4`.
`Cr9Dataset` composes metadata with `backtesting_rows`; its context deliberately has
no table-wide observation date. Existing `cr6-v1` output remains readable and retains
its old wire format. Extraction output names are independent of these wire versions.

[`contracts.py::TABLES`](../src/rwa_analysis/domains/cr6/contracts.py) associates
the 12 named `Cr6Output` relation members with their row models, derived/augmented
TypeSpecs and physical `silver.cr6_*` tables:

| Members | Stored meaning |
|---|---|
| `observations` | Scalar financial measures, source-derived identity, band bounds/category and context reference |
| `contexts`, `context_qualifications`, `context_evidence` | Shared source context once, with ordered qualification/evidence references |
| `fields`, `field_qualifications`, `field_mappings` | Per-measure source/conversion metadata and ordered interpretation references |
| `attributes`, `attribute_evidence`, `attribute_decisions` | Resolved assertions and alternatives, typed values and supporting references |
| `relationships`, `relationship_evidence` | Source parent/child relationships and evidence |

Within CR6, band fields live on observations. Repeated metadata becomes related rows; small
owned source locations are flattened. Catalogue definitions remain durable files
under [`catalogue/`](../catalogue/), outside disposable Silver.

CR9 declares the analogous twelve metadata/measure relations plus
`temporal_descriptors`, `temporal_bindings` and `temporal_evidence` in
[`contracts.py`](../src/rwa_analysis/domains/cr9/contracts.py). Its relationships
include optional field endpoints so a new-default subset is distinct from a row
self-edge. Bindings join a source record/field and temporal role to an occurrence-
scoped descriptor; partial dates, duration and unresolved bounds remain explicit.
Temporal qualifications are projected to affected fields. Source row qualifications
also follow those fields into Silver.

The shared occurrence owner uses `compose_field` to combine selected meanings.
Retained CR6 uses its observation date; retained CR9 leaves date-restricted
definitions/mappings unresolved rather than substituting the document date. V4
resolves explicit occurrence temporal roles. Domain projections never select mappings.
`cr6-cr9-v1` retains the old release's members and adds source-specific CR9 definitions.
Counts are not assumed to share one counting convention: NAB establishes agreements,
while unsupported counting/weighting conventions remain unresolved.

Dataclass schemas are derived with `extract_from_dataclass`, then augmented with
explicit literals, keys and measure-specific decimals. Money uses `Decimal(16,2)`;
rates, band fractions and maturity use `Decimal(16,8)`; counts are integers.
Bronze retains source units, tokens and displayed precision. Arithmetic working
types can be wider than persisted types; they are not new source constraints.

`present`, `source_missing` and `not_conformed` distinguish numeric availability.
Semantic attributes can remain unresolved or conflicting independently. An unknown
currency does not negate a known million-to-base-unit conversion. A source amount
without an established conversion remains accessible in source metadata.

Task 5 removed the earlier recursive `asdict()`/full-record inference bridge in
`domains/cr6/metadata.py`. Source metadata enters as flat declared records, and
domain projections consume native relations. The
[removal record](04.planning/a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md)
retains the original rationale and checkpoint review boundary.

## Execution, publication and reconstruction

`run()` calls extract → save Bronze → reload Bronze → conform → publish → reconstruct.
Master consolidation is a separate call. Targeted stages accept explicit inputs and
do not depend on earlier calls on the same session. See the executable examples in
the [README](../README.md).

`SilverCandidate` and `SilverOutput` expose named `cr6`, `cr9` and `source_tables`
members. The common inventory in `storage/tables.py` drives all 49 table writes/readbacks; an omitted
domain is represented by typed empty relations and is cleared on replacement.

- Bronze output names select retained versions beneath a bundle path. Use a new
  `run_name` to save another extraction; it is not a schema or code version.
- Staging publication replaces every declared table for the complete selected input
  set, plus `ops.silver_publication`, in one mountainash-data DuckDB transaction.
  Selecting fewer inputs removes their former rows. Manifests are retained separately
   before the database write; file retention and the database are not one transaction.
- Master reads persisted staging values, concatenates corresponding relations with
  `ma.concat`, and replaces its own tables. It does not reconform Bronze or deduplicate
  source occurrences. Empty selections produce typed empty tables.
- Master rows retain their producing staging `silver_revision_id`; its marker and
  `MasterManifest` identify the master revision and selected staging manifest paths.
- Reconstruction uses persisted values and conversion factors, with saved Bronze
  supplying labels, ordering and source metadata. Master reconstruction needs those
  retained files, but not live staging databases.

### Source-defined historical tables

`SourceTable` composes a table context, published fields, ordered axes and typed
cells with qualifications, segmentations, relationships and cell-level timing.
Fields carry units, scale and source form (`table_body` or `note`). Cells carry
Decimal/integer/lexical payloads and explicit source missingness; absent fields have
no occurrence. `disclosure-v3` transports these datasets without extending the fixed
CR6/CR9 row inventories. Earlier v3 checkpoint cells decode with defaults for the
later legacy row-role and aggregation-scope metadata.

`SourceTableOutput` declares 22 relations: tables, fields, axes, cells, references,
source attributes, evidence, segmentations, bands, qualifications, relationships,
temporal descriptors/bindings, meanings, mapping references and interpretation
attributes/evidence/decisions, plus occurrences, occurrence links, contexts and context
bindings. Ordered reference rows preserve header paths and
qualified endpoints; the same declarations drive storage and master copying.

`resolve_capture` uses the existing scoped catalogue composer; the retained
`resolve_cell` address adapter delegates to the same owner. Definitions can be
shared while source occurrences and evidence remain separate. Exact unit conversion
does not imply an established canonical measure. Source Decimal slots use
`Decimal(16,8)`, conversion factors `Decimal(16,6)`, normalised money `Decimal(16,2)`
and other numeric scalars `Decimal(16,8)`; counts remain integers. Wider arithmetic
precedes conformance. The native model-declared ingress fix in Mountainash PR #377
is pinned; no source-row reordering or inference-window workaround is used.

Ordinary `ConformanceOperation` resolves all selected inputs once and publishes
native source datasets plus their declared domain projections. An explicit
`SourceTablePipeline().conform(inputs, catalogue)` also exposes selected legacy
CR6/CR9 datasets as source tables. The legacy adapter preserves original addresses,
published bindings, lexical rating cells and scoped relationships for the shared
resolution owner. Candidate selections retain their actual saved input references.

`reconstruct_source_tables(output.source_tables)` returns source-shaped frames and
filtered metadata from persisted relations. It does not reread source numbers from
Bronze. Numeric notes remain separately queryable cells outside body frames.
Session/master frame dictionaries preserve existing numeric CR6/CR9 keys when an
explicit source projection shares their source identity. The historical example
exposes source views separately and constructs field/path/time/band inventories
with Mountainash, including fields with unresolved definitions or missing values.

### Current publication and provenance limits

`Publication` names a **mutable database path**, a retained manifest and a revision
label. Reading an old handle does not retrieve an old snapshot or check that the
database still matches its revision. Finish staging work first and select its current
publications before consolidating; execution is single-writer and sequential.

Retain the selected Bronze, catalogue files/revisions, manifests and the relevant
implementation/environment when preserving an analysis. Manifests retain references,
not copies of catalogue files or staging data. `RebuildManifest.implementation_revision`
currently defaults to `unrecorded`; session publication does not automatically capture
a code commit or complete configuration/environment snapshot. Bronze envelopes record
dependency versions and permit an implementation identifier, but the ordinary session
does not obtain one from Git. Reproducibility remains dependent on retaining the
referenced assets; a revision label alone is insufficient.

### Validation boundary

[Validation remains separate and undefined](01.principles/c.extraction-and-validation/validation-is-a-separate-process.md).
Conformance, declarations and development tests do not authorise validators or
publication gates. The migration retained the existing strict Bronze codec/transport,
catalogue constructors and manifest parsing; those paths still contain checks and
ordinary parsing errors. This is not a claim that the whole package contains no
checks, nor a new exemption authorising their expansion. Any change to that retained
behaviour must be reconciled explicitly with the separate-validation decision.

## Extending the implementation

### Bespoke extraction and shared interfaces

The extension seam is an explicitly selected script with
`extract(pdf_path: Path) -> CapturedBundle` for current declarations; retained bespoke
callers can return `ExtractionBundle`. `run_extractor(script_path, pdf_path)`
loads that function; `DocumentSelection` supplies the two paths. One source PDF owns
one bundle. The structural `Dataset` protocol exposes `id` and `metadata`; supported
concrete dataset types have explicit codec and conformance dispatch. Implementing the
protocol alone does not register a new persistence format.

| Responsibility | Shared interface | Source-specific decisions |
|---|---|---|
| Primitive numbers | `parse_decimal_token`, `ReportedValue` | Missing-reason interpretation, original token, displayed precision and exact evidence |
| Table construction | `SourceTable`, `TableField`, `SourceCell`, `SourceTableMetadata` | Selected panels, local IDs, orientation, original labels/order and source form |
| Metadata | `SourceAxisItem`, qualifications, bands, relationships, temporal descriptors/bindings | Header paths, scope/endpoints, applicable definitions, period bounds and uncertainty |
| Interpretation | Scoped `SourceMappingRevision`, reusable `MeasureRevision`, `compose_field` | Evidence-backed applicability and explicit overrides/corrections |
| Transport and storage | `disclosure-v4` plus retained v1/v2/v3 codecs, `SourceTablePipeline`, existing staging/master | Explicit bundle/catalogue selections and fresh saved output versions |

Direct dataclass construction is the bespoke interface, including non-rectangular
notes, different row/column roles and per-cell timing. Local constructors can shorten
repeated assembly, but are not mandatory hooks or a hierarchy of template subclasses.
PDF geometry and printed-page offsets stay with the document. Extractors do not import
other dated extractors or obtain semantics through silent template inheritance.

For semantic reuse, source occurrences reference a reviewed measure revision while
retaining their own evidence. A narrower mapping does **not** implicitly win: explicit
`overrides_refs` replace the affected attributes/conversions, while `supersedes_refs`
record replacement of a whole mapping. Conflicting assertions otherwise remain
conflicting. Source-table mappings select document and dataset occurrences; the
document date does not substitute for an unknown field measurement date.

Mapping identities must distinguish publication vintage as well as observed period.
A June/September 2023 panel in a 2023 report and its 2024 comparative are separate
occurrences, even when their values agree. A new release can select both without
changing the previously retained release. Neither publication nor master consolidation
chooses between them on the researcher's behalf.

Review shared-helper opportunities against real consumers. The four 2024 extractors
already share numeric parsing, composed representation, catalogue resolution and
persistence. Their similar construction loops also encode differing source meaning;
moving those loops into a configurable template would not by itself establish reuse.
Extract a further common operation only when its inputs make evidence, missingness
and source-specific alternatives explicit and it removes meaningful duplication.

The agreed [historical-capture direction](01.principles/a.architecture/historical-disclosure-capture.md#source-defined-capture-and-composable-metadata)
is implemented for the selected 2023/2024 reports and explicit Westpac 2025 comparison.
Extend bespoke extraction and independent goldens for additional sources; do not
assume this selection establishes fifteen-year coverage or cross-vintage equivalence.
The disposable shape spike remains separate from production implementation.

Follow [Mountainash-first coding practices](01.principles/d.coding-practices/mountainash-first.md).
Select a real source case, review evidence, extend independent goldens and introduce
only the domain records/contracts it needs. Preserve the one-source-bundle boundary.
Add domain operations and update explicit composition/storage associations when a
new domain is approved; do not force stock/flow or liquidity records into CR6.

## Verification evidence

Task 7 verification on 2026-10-14 passed **205 tests**. Fresh historical and modern
examples and saved-only reconstruction passed; all 74 historical and eight modern
readback files match accepted checkpoint B in content/dtype and source-frame order.
Exact commands, retained roots and logs are in the
[execution record](04.planning/superpowers/plans/2026-10-13-metadata-driven-extraction.md#task-7-execution-evidence--2026-10-14).
Final independent delivery reviews remain pending.

The [completed migration record](04.planning/superpowers/plans/2026-10-11-strategic-architecture-migration.md)
records 114 passing tests and the real CBA/four-bank demonstrations on 2026-10-11.
This is dated evidence, not a fresh test-run claim or a target test count.

The [CR9 execution record](04.planning/superpowers/plans/2026-10-12-cr9-implementation.md)
records 148 passing tests and the real four-bank PDF → retained Bronze → staging →
master run: 36 CR6 rows, 33 CR9 rows and eight reconstructed numeric tables. Existing
CR6 goldens are unchanged. Master tests mutate stored CR9 rates/history duration,
then verify copying and reconstruction after deleting the staging databases.

- [Organisation workflow tests](../tests/integration/test_organisation_workflow.py):
  real CBA PDF → saved Bronze → persisted tables, independent reruns and rooted settings.
- [Master tests](../tests/integration/test_master_consolidation.py): copied staging
  values/metadata, reconstruction after staging deletion, fewer/empty selections.
- [Reconstruction tests](../tests/integration/test_cr6_tables.py): source-shaped
  numeric output using actual persisted values.
- [Conformance tests](../tests/silver/test_cr6_conformance.py) and
  [source goldens](../tests/bronze/): numerical conversions and preserved source semantics.
