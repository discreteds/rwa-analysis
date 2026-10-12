# Reusable disclosure processing architecture

Date: 2026-10-11

Status: **Implemented for the selected four-bank CR6 slice; PR #2 merged into develop.**
The separation of configuration, declarations, operations and workflow, and the
`OrganisationSession.run()` entrypoint, were agreed after the CBA spike. The
researcher approved the migration plan and its CBA checkpoint; staging/master delivery
is complete. See the [current architecture](../../../architecture.md) for actual code
owners, signatures, physical storage, verification evidence and provenance limits.
CR1/CR2 passages remain extension designs. Historical spike/dependency findings below
are dated evidence, not assertions about every current path.

**2026-10-11 correction:** [Validation is a separate process](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md).
Its scope and behaviour are not defined. Earlier boundary-validation and
pre-publication checking instructions are superseded, including native validator
calls; this migration implements processing, not validation.
Working CR6 baseline: `feature/simple-cr6`, commit `3be5e86`; disposable CBA spike:
`feature/cba-cr1-cr2-spike`, commit `e943b3f`. Neither implements these refined boundaries.

## 1. The ask and scope

Organise the working disclosure pipeline into reusable domain models, Mountainash
contracts and transformations, organisation-scoped sessions, layered settings, and
independently rebuildable staging databases feeding master Silver.

The existing four-bank CR6 workflow is the executable baseline. CR1/CR2 supply a
contrasting design case, using the already reviewed sources. This design does not
constitute approval to deliver production CR1/CR2 extraction. The disposable CBA
spike exercised the end-to-end data path; this update clarifies ownership and
interfaces in response to its shape review, before implementation planning.

The [project principles](../../../01.principles/README.md) govern evidence, semantics,
identity and research limitations. The [composed processing principle](../../../01.principles/a.architecture/composed-processing-and-organisation-staging.md)
records the decisions from this discussion. The [simple CR6 design](2026-10-10-simple-cr6-research-design.md)
records the intermediate source-fidelity and direct-Python design. Its earlier three-table
physical layout and ownership are superseded by this specification; validation
instructions are superseded by the separate-validation principle.

## 2. Agreed architecture

```text
Project settings + organisation settings
                       |
             build_session(settings)
             constructs components
                       |
              OrganisationSession.run(...)
                 orders stage calls
                       |
PDF → bespoke extractor → domain datasets → saved Bronze
                                               |
                                  selected catalogue/mappings
                                               |
                                    domain pipelines
                       Bronze conformance → relation transforms → Silver conformance
                                               |
                              organisation staging Silver

CBA staging ─┐
NAB staging ─┤
ANZ staging ─┼→ full consolidation → candidate → master Silver
WBC staging ─┘
```

- Separate domain dataset containers satisfy a shared fundamental protocol.
- Shared metadata is composed into those containers; domain records retain their types.
- Input and output dataclasses anchor each domain's Mountainash contracts.
- Transformations operate on whole relations using declared input/output schemas.
- Validation is a separate, not-yet-defined process; processing does not invoke it.
- Construction assembles concrete operations using resolved settings and domain declarations.
- An organisation session orders stage calls and exposes each stage directly.
- Its thin `run()` entrypoint calls the same stages in order.
- Project and organisation configuration use Mountainash Settings' native layering.
- Organisation staging databases share one Silver schema and rebuild independently.
- Master Silver is a full rebuild from explicitly selected staging publications.

### Ownership boundaries

| Concern | Owns | Current consumers |
|---|---|---|
| Configuration | Typed execution settings: project roots, organisation identity, storage destinations | Component construction and storage operations |
| Declarations | Domain models, augmented input/output schemas, output members and their table identities | Domain pipelines, Silver write/read, master consolidation |
| Operations | Extraction, Bronze encoding and access, domain conformance, publication, readback and reconstruction | Independently callable stages and the organisation workflow |
| Workflow | Explicit input selection, stage ordering and passing results between operations | `OrganisationSession.run()` and targeted reruns |

Financial definitions and mapping revisions remain authoritative in the durable
catalogue. They are explicit conformance inputs, not execution settings. Run-specific
document selections, Bronze references, `run_name` and publication revision are call
arguments. Declarations describe record and table contracts; they do not select a run.

Use ordinary functions and a few concrete components. A small `build_session(settings)`
function assembles the extractor operation, Bronze store, domain pipelines and Silver
store, then supplies them to the session. It consumes settings already resolved by
Mountainash Settings. Construction does not extract documents or publish data.

The session delegates execution. Bronze operations own serialization and saved paths;
the Silver store owns connections, transactions, retained manifests and readback.
Domain operations receive datasets, source context and selected interpretations;
they return conformed domain results or reconstructed tables without opening files
or database connections. Each operation receives only the settings or inputs it uses.

These are responsibility boundaries, not four new packages or an execution framework.
Introduce a shared interface only where an existing caller needs it, such as domain
dispatch. Keep declarations beside their domain models and operations.

## 3. Models, containers and protocol

### Shared source models

Reuse the existing document, source-reference, reported-value, axis, binding,
qualification and relationship models. They describe evidence, not processing jobs.
Source metadata stays independent of canonical interpretation.

A shared `DatasetMetadata` groups the source context and descriptors currently
repeated around domain records. It must accommodate snapshot and interval context:
the current CR6 assumption that every dataset has one observation date cannot govern
CR2's opening stock, movements and closing stock.

### Domain containers

Illustrative structure:

```text
ExtractionBundle
  document, source identity, extractor reference
  datasets: collection of Dataset

Dataset protocol
  id
  metadata: DatasetMetadata

Cr6Dataset
  id, metadata
  exposure_rows: collection of BronzeCreditRiskExposureRow

CreditQualityDataset
  id, metadata
  credit_quality_rows: collection of BronzeCreditQualityRow
  allocations: collection of BronzeProvisionAllocation

ExposureMovementDataset
  id, metadata
  movement_records: collection of BronzeExposureMovementRecord
```

The protocol is a Python `Protocol`: common consumers rely on its declared members,
while concrete classes provide domain-specific collections. There is no universal
`.records` requirement hiding CR1's related allocations. These names illustrate the
responsibility split; the spike supplies concrete examples for field-level review.

The container is not a file format. A document's one Bronze bundle can hold all
three kinds of dataset. Adding CR1/CR2 to a CBA document extends that document's
extractor and bundle rather than creating duplicate source documents.

Use composition for metadata. Introduce a base implementation only for shared
behavior actually used by multiple concrete classes. Organisation-specific source
layouts remain in bespoke extractors, not a hierarchy of bank/date session subclasses.

## 4. Dataclasses, conformance and contracts

Each domain has distinct Bronze and Silver record models. A pipeline connects them:

```text
Bronze record collection
  → Mountainash input representation/conformance
  → Mountainash relation transformations with selected mappings
  → Mountainash output conformance
  → Silver dataclass collection or dataframe at the consumer boundary
```

### Declare once where the meaning is shared

| Declaration | Authority |
|---|---|
| Record fields and Python types | Bronze or Silver dataclass |
| Physical storage types | Augmentation of that model's derived Mountainash specification |
| Validation rules and their execution | Not yet defined; separate from this processing migration |
| Applicable source meaning and unit/sign mappings | Durable semantic catalogue |
| Domain transformation | Mountainash expressions in the domain pipeline |

Derive schema information from the dataclass, then add only what annotations cannot
express. Avoid parallel handwritten inventories of the same fields in a dataclass,
Polars schema, TypeSpec and validator. Keep an explicit Bronze-to-Silver mapping when
names or meanings genuinely change. Some duplication between layer-specific models
is appropriate: they describe different contracts.

Domain schemas are explicit declarations beside the models. A shared schema helper
may apply supplied Mountainash declarations, but must not infer validation rules
from field names or turn every intermediate projection into a checked boundary.
Declaring an identity, relationship or type does not authorize a runtime validator.

Numeric policy, revised with researcher approval on 2026-10-11: use `Decimal(16,2)`
for base-unit money, `Decimal(16,8)` for rates and other small-valued measures needing
eight fractional digits, and integers for counts. Scale is fixed per field, not
selected from each value. This preserves the 10-trillion monetary domain without
requiring eight fractional places at that magnitude. Source precision remains in
Bronze. This supersedes the earlier shared `Decimal(22,8)` storage decision.

Use Mountainash's dataclass ingress and `to_dataclasses` egress. Keep data as a
relation through transformation; materialize for the caller or store.
Do not shuttle through Python records between each relational operation.

Bronze's `ReportedValue` includes value and source evidence. Decimal conformance is
needed only at the dataframe/relation boundary, where projected numeric values are
top-level columns. Recursive conversion of source objects is not a requirement.
Keep the source evidence linked to those columns through the existing bindings.

### Normalised CR6 storage — approved after the CBA spike

The researcher approved the disposable one-row CBA normalisation shape and its
production implementation. Preserve composed Bronze objects; project flat Silver
dataclasses and related collections. This is a storage change, not a validation
workflow. Table count follows actual relationships, not a quota.

- `contexts`: one source dataset context, with scalar knowledge value/status pairs.
  `context_qualifications` retains each context/knowledge member's ordered references;
  `context_evidence` retains ordered, flat source locations.
- `observations`: identity, context reference, band details and twelve typed measures.
  A band's single source location is flattened beside its bounds. Band definitions
  remain source-scoped; there is no new cross-document band catalogue.
- `fields`: existing per-field scalar metadata and a flattened source location.
  `field_qualifications` and `field_mappings` hold their ordered reference collections.
- `attributes`: one row per field attribute assertion. `assertion_index=0` identifies
  the resolved assertion; positive indexes preserve alternatives in order. Scalar
  text/integer/boolean columns and flattened revision/evidence-reference columns
  preserve the existing typed value union. Attribute order is retained separately.
  `attribute_evidence` and `attribute_decisions` preserve supporting references per
  assertion. These rows store interpretations already produced by the catalogue;
  they do not implement new interpretation or validation policy.
- `relationships`: existing parent/child rows, with ordered `relationship_evidence`.

Every table carries `silver_revision_id`; child keys include their owning context,
observation/field/assertion or relationship and position. Keep existing stable source
identities. Declare named output members and their physical tables once. Flat row
models use Mountainash conformance. The researcher subsequently authorised a
temporary standard-library `asdict()` metadata ingress boundary, with full-record
inference to handle late non-null values. Mountainash expressions own unnesting,
collection expansion, selection, renaming and joins; Python supplies objects and
resolved catalogue meanings, not a parallel field-by-field metadata ETL.
The [techdebt item](../../a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md)
requires revisiting metadata schemas and removing the adaptation. No custom recursive
serializer or ORM is introduced.
Store/reload the complete output through the existing transaction. Reconstruction
continues to read persisted numbers and saved Bronze source bindings.

Concrete proof: saved CBA first-band EAD → persisted `281508000000.00` → reconstructed
`281508.00000000` in reported millions, with the original evidence and mapping links
retained. Existing conflict examples must retain their alternatives as child rows.
The spike exercised six tables for selected fields; production includes the existing
collections omitted by that probe. No new rejection or runtime gate is introduced.

### Validation ownership

Validation is a separate process, not an operation embedded in these pipelines or
their transitions. Its scope, rules, invocation, outputs and consequences have not
been defined. Do not add validators, validation modes or publication gates under
the headings of contracts, conformance, metadata preservation or source fidelity.

Schema-directed transformations still preserve source meaning and missingness;
ordinary parsing, cast and I/O failures propagate. Independent source goldens and
development tests verify the implementation outside the processing workflow.

Trust framework arithmetic and casts. Wider working types used by an arithmetic
expression are not mandatory source precision declarations or validation checks.
In particular, the observed `Decimal(38,0)` ingress type does not create a project
requirement to coerce source values or null columns to precision 38.

### Verified framework entry points and remaining proof

The following records API inspection and spike findings from implementation design.
For the delivered path, use the current guide and completed migration evidence.
References to native rule/validator APIs establish availability only; no invocation
is authorised by this specification.

Inspection of the installed dependencies confirmed:

- `mountainash.typespec.extraction.extract_from_dataclass` derives a TypeSpec.
- `ma.datacontract(spec)` compiles a contract from that specification.
- `BaseDataContract`, `Field`, `Rule`, `RuleRegistry` and `Validator` supply native
  contract augmentation and expression-rule facilities.
- `ma.relation(...)` is the relation entry point; `Relation.to_dataclasses(cls, ...)`
  supports a supplied specification or automatic derivation.
- `MountainAshBaseSettings` and `SettingsParameters` support native configuration
  loading and reusable settings parameters.

API inspection established these entrypoints; the spike subsequently exercised the
selected CBA round trips and numeric declarations. The installed `TypeSpec` does not
expose the `TypeSpec.from_dataclass` convenience method shown in some website
documentation; use the actual extraction entry point. Evidence is scoped to the
executed paths, not every possible nested object or backend. Report observed dependency
limitations rather than prebuild adapters for hypothetical gaps.

Review probes on the pinned Mountainash commit
`3c25bbffe0a3998ef56a9092e54898b3219ce9a2` identified two distinct upstream findings,
tracked here pending upstream resolution:

- **MA-INFERENCE-1 — required fields (open, upstream-dependent).** Deriving a
  dataclass with `label: str` and no default produces `constraints=None`.
  `typespec/extraction.py:185–190` contains a self-inequality condition that is
  always false. Automatic required-field inference is blocked until the upstream
  fix is available and the required/optional cases pass on the pinned dependency.
- **MA-INFERENCE-2 — bare Decimal inference (observed limitation).** Deriving
  `amount: Decimal` logs an unrecognised Python type and produces `ANY`.
  PRs #355 and #357 support explicit decimal declarations and dataframe conformance.
  Explicit measure-specific decimal augmentation is the agreed path, since a bare
  annotation supplies neither precision nor scale. Automatic inference of that
  declaration is not required for this spike.

The first disposable spike probe on PR #357's merge
`ee28822d25310a396865a78cba17f2d7cb779d09` established a narrower, concrete blocker:
**MA-DECIMAL-22 (closed for this consumer by revised requirement)**. CBA amounts enter as `Decimal(38,0)`;
native conformance to `Decimal(16,8)` succeeds, but `Decimal(22,8)` fails because
conversion targets remain capped at precision 16. The researcher then approved
`Decimal(16,2)` for money and `Decimal(16,8)` for small-valued measures. The upstream
cap still exists; this consumer no longer requires a higher-precision cast.
The revised native-conformance path works through saved Bronze, DuckDB and domain
reconstruction in the disposable spike (retained on `feature/cba-cr1-cr2-spike`;
read its guide with `git show e943b3f:spikes/cba_cr1_cr2/README.md`).
Automatic required-field inference remains a separate upstream limitation; the spike
uses the already-agreed explicit key constraints rather than depending on it.
The spike demonstrates shape, not production readiness.

## 5. Domain pipelines and the CR1/CR2 design exercise

Each concrete pipeline associates its input models/contracts, transformation and
output models/contracts. For CR1, the same pipeline processes the credit-quality rows
and their related allocation collection. A small shared pipeline interface enables
session dispatch; a shared base implementation is warranted only where the execution
sequence really is identical. Mountainash supplies the data-processing machinery.

Domain-owned reconstruction functions assemble loaded Silver output and source
metadata; the session obtains both through storage operations and dispatches to the
domain function. CR1 reconstruction joins its rows and allocations through their
source bindings, while CR2 preserves each row's temporal role.

### Explicit domain results

Return a named domain result rather than making callers coordinate a dictionary of
physical table names. For example, `CreditQualityOutput` exposes `rows` and
`allocations`; `ExposureMovementOutput` exposes `movements`. These members hold
conformed Mountainash relations, with materialization at storage or caller boundaries.
They do not require parallel copies as both dataframe and dataclass collections.

Each domain declares the association between its result members, record contracts
and persisted table identities once. The store uses that association for publication
and readback; consolidation uses the same table inventory. The workflow does not
repeat a list of CR1/CR2 table names. The association can be a small explicit mapping;
it does not require automatic discovery or a plugin registry.

A Silver candidate groups these domain results and their explicit rebuild selection.
Readback restores the domain result shape, so the same reconstruction operation can
consume it independently of the database connection. Keep the input/output contracts
visible at the pipeline boundary and retain Bronze references through this handoff.

The [source discovery](../../../00.ideation/2025-credit-quality-provisions-discovery.md)
and [worked examples](2026-10-10-data-model-worked-examples.md#2-credit-quality-and-movements-source-hierarchy-and-two-axis-binding)
provide these concrete architecture checks:

| Source case | Required behavior |
|---|---|
| CBA CR1 Loans allowance `5,966`, with Specific SA allocation `48` | Preserve the allocation's nested header meaning and subset relationship; do not add it to the parent allowance |
| NAB combined SA allocation `276` in column `d/e` | Retain the combined detail and footnote; no invented Specific/General split |
| Westpac allowance `(4,504)` | Bronze retains `-4504` and its token; any canonical sign change is an explicit mapping |
| CBA CR2 opening `10,297`, flows `4,241`, `-1,922`, `-386`, `-1,251`, closing `10,979` | Distinguish snapshot and interval roles within one movement schedule |
| CR2 title versus scope in introduction/row text | Retain off-balance-sheet inclusion established by the evidence |

The CBA movement bridge is a useful diagnostic example. It is not a universal rule
that every disclosed movement schedule must reconcile exactly. These reviewed values
are design evidence, not a newly approved production golden set.

CR6 keeps its current fields, independent goldens and conformance results. Common
behavior is extracted from both examples; CR1/CR2 are not forced into the CR6 shape.

## 6. Organisation session and stage methods

`OrganisationSession` receives the components assembled for an organisation. It owns
workflow sequencing and delegates each stage to its operation. Component construction,
configuration-file loading, source parsing, JSON codecs, domain expressions and
database transactions belong to their respective owners above.

The organisation identifies the source owner and staging destination. It does not
force every dataset to share a legal entity, exposure country or reporting date.

Implemented CR6 session method responsibilities:

| Session method | Delegated owner | Input → output |
|---|---|---|
| `extract(documents)` | Extraction operation / selected bespoke extractors | Explicit source selections → domain bundles |
| `save_bronze(bundles, run_name)` | Bronze store | Bundles → saved Bronze references |
| `load_bronze(refs)` | Bronze store | Explicit saved references → bundles paired with their Bronze references |
| `conform(inputs, catalogue)` | Domain pipelines | Referenced bundles and interpretations → conformed domain results in a Silver candidate carrying its rebuild selection |
| `publish(candidate, revision)` | Silver store | Complete candidate → organisation staging publication, with retained manifest |
| `reconstruct(publication)` | Silver/Bronze read operations, then domain reconstruction | Loaded Silver and linked source metadata → source-shaped numeric dataframes |
| `run(documents=..., catalogue=..., run_name=..., revision=...)` | Workflow: the stage methods above | Explicit run inputs → publication reference and reconstructed tables |

The full workflow deliberately reloads saved Bronze before conformance, preserving
the established handoff. A targeted rerun calls only the relevant methods. A complete
stage selection replaces the organisation's staging contents; it is not an implicit
append. For example, rebuilding only the June document leaves only the June selection
in that staging database. To retain several dates, include their saved inputs.

`reconstruct()` returns `dict[str, pl.DataFrame]`, not the full source metadata.
Source bundles are available separately through `RunResult.bundles` or the store's
`read_sources(publication)` method.

`run()` replaces the provisional `all()` name. It is the entrypoint for the organisation
workflow: extract, save Bronze, reload Bronze, conform, publish, reconstruct. It uses
ordinary sequential calls and does not invoke master consolidation. Targeted reruns
use the stage methods directly. Each stage accepts explicit inputs; it does not require
earlier methods to have run on that same session object.

As demonstrated by the spike's `RunResult`, return the publication reference alongside
reconstructed tables and their metadata. This makes later inspection and reruns
possible without an implicit session `last_result`. Exceptions propagate from the
owning operation; publication's transaction preserves the prior database on failure.

Loaded inputs retain their `BronzeRef`, including the saved output namespace.
Conformance carries those references and the selected catalogue into the candidate's
rebuild selection. Publication retains the existing rebuild manifest outside disposable
Silver. This explicit data flow, rather than session history, supports later readback.

Targeted use with the implemented application methods:

```python
cba = build_session(cba_settings)
inputs = cba.load_bronze(selected_refs)
candidate = cba.conform(inputs, catalogue=selected_catalogue)
publication = cba.publish(candidate, revision="cba-june-review")
tables = cba.reconstruct(publication)
```

Illustrative full entrypoint using those same operations:

```python
result = cba.run(
    documents=selected_documents,
    catalogue=selected_catalogue,
    run_name="cba-june-review",
    revision="review-1",
)
tables = result.tables
publication = result.publication
```

An extraction `run_name` is a user-chosen saved-output namespace, not a code/schema
version. Keep the current saved-run behavior and existing files. Git is never a
runtime prerequisite.

## 7. Settings and configuration

Use Mountainash Settings directly, with two file layers:

```text
config/project.yaml                 shared project defaults
config/organisations/cba.yaml        CBA identity and overrides
config/organisations/nab.yaml        NAB identity and overrides
```

`ProjectSettings` declares common paths and storage defaults; an
`OrganisationSettings` model can extend it with organisation identity and staging
location. Load project configuration followed by the organisation file through the
native `config_files` mechanism. Use the library's supported precedence, typed path
handling and explicit call overrides rather than writing a merger or settings registry.
Resolve settings before calling `build_session(settings)`. That construction function
passes paths, connection settings and organisation context to the components that use
them. Domain declarations and transformation functions do not read configuration files
or environment variables. Direct construction with explicit components remains ordinary
Python use; a dependency-injection container is unnecessary.

| Settings | Explicit call inputs | Durable domain knowledge |
|---|---|---|
| Project/raw/Bronze roots, staging and master locations, organisation identity | Documents, extractor paths, selected Bronze runs, `run_name`, publication revision, selected catalogue | Concepts, definitions, source mappings, interpretation decisions and evidence |

Paths are resolved consistently from the configured project root, so a notebook's
working directory does not alter their meaning. Connection construction uses
mountainash-data; native Mountainash Settings connection profiles can supply its
configuration where useful. The initial backend remains local DuckDB.

Environmental settings do not redefine financial semantics. A researcher selects a
catalogue revision explicitly; a source interpretation does not silently change
because an environment variable was set.

## 8. Staging and master Silver

### Organisation staging

Illustrative destinations:

```text
data/silver/staging/cba.duckdb
data/silver/staging/nab.duckdb
data/silver/staging/anz.duckdb
data/silver/staging/westpac.duckdb
data/silver/master.duckdb
```

Settings own the actual paths. Every staging database implements the same published
Silver schema. Tables for domains not selected by an organisation are empty and typed.
The schema expands in concert when another domain is implemented; an empty CR2 table
does not claim CR2 extraction exists for that organisation.

Use the normalised CR6 relations above. CR1/CR2 table definitions follow their typed collections
and contracts; the spike supplies a candidate physical shape. Shared schema does not
mean one universal observation table or an identical number of tables per domain.

Each staging rebuild consumes a complete explicit input selection and replaces
the staging tables in one supported transaction. A failed
publication leaves the previous publication available. The database can also be
deliberately deleted and regenerated from saved Bronze and catalogue inputs.

### Master consolidation

`SilverConsolidator` accepts explicit organisation staging publications and the
master destination. It reads each selected publication, combines corresponding
tables with Mountainash under their declared schemas, and replaces master Silver
atomically through mountainash-data. It does not introduce validation checks.

The operation reads already conformed values; it does not rerun extraction, reinterpret
catalogue mappings or repeat domain transformations. It does not add together reported
totals or deduplicate independent source occurrences merely because values agree.

Publication details, reconciled with the delivered CR6 path:

- Select current completed staging publications, normally one per organisation.
  Schema compatibility follows the declared tables and native operations; there is
  no separate upfront schema-validation pass or publication freshness check.
- Preserve source identities and producing-publication lineage. Master retains its
  selected staging publications and their durable rebuild manifests, so reconstruction
  remains possible after staging is replaced. Producing `silver_revision_id` values
  remain on copied rows; `MasterManifest` retains staging manifest paths and the
  `ops.silver_publication` marker identifies the master publication. Database paths
  are mutable, not historical snapshots; see the current architecture's limits.
- Removing an organisation from the selection removes its rows on the next full
  master rebuild. A failed master rebuild leaves the prior master publication intact.
- The initial workflow remains single-writer and sequential. Finish staging rebuilds
  before consolidating them; no concurrent staging publication during consolidation.

This extends the existing transactional replacement pattern. There is no incremental
merge/upsert path in this design.

## 9. Reuse and evidence for the next step

Reuse the existing PDFs, four bespoke extractors, source metadata, independent goldens,
saved Bronze, semantic catalogue, Mountainash transformations, storage integration and
numeric dataframe reconstruction. The [asset inventory](../../../00.ideation/2026-10-11-cr6-existing-assets-and-reuse.md)
records their origin. Reorganising classes is not a reason to rediscover their content.

The disposable CBA spike saved/reloaded its manually transcribed bundle, conformed
the domain collections, persisted three Silver tables and reconstructed all 34 selected
cells with missingness and temporal roles. It exercised layered settings, native rules,
typed empty inputs and dataclass readback. Its source transcription remains separate
from production Bronze and approved goldens; production CR1/CR2 extraction is a later
decision. Its guide remains available with
`git show e943b3f:spikes/cba_cr1_cr2/README.md`; the production branch does not include
the disposable implementation.

The shape review identified three ownership changes captured here: move construction
and storage mechanics out of the session; replace domain-name checks in `schema()`
with explicit declarations; replace table-name dictionaries at domain interfaces with
named results and one declared storage association. Rename the entrypoint to `run()`.
The retained spike still uses the earlier interfaces and remains disposable.

For this migration, retain the relevant development tests for source goldens, Bronze
transport, domain transformations and persisted reconstruction. These tests do not
authorize runtime validation. Production CR1/CR2 and a defensive lifecycle suite are
outside this migration; do not repeat framework arithmetic tests throughout it.

## 10. Completed review and implementation checkpoint

The researcher accepted the refined design as settled and authorised the
[migration-and-retirement plan](../plans/2026-10-11-strategic-architecture-migration.md)
without another disposable spike. Production implementation proceeds from the working
CR6 baseline, with a CBA checkpoint, rather than promoting spike code.

Planning clarification: implement the simpler interfaces and remove their predecessors.
Keep declarative input/output schemas and existing source goldens. Validation is
separate and remains undefined. Do not restore the retired application checks, historical
defensive lifecycle suite or introduce a hardening programme as part of this migration.
The plan's verification is sized to the real workflow and the declared boundaries.

The migration completed with 114 tests passing and a real four-bank staging/master
demonstration on 2026-10-11; PR #2 merged into `develop`. The
[migration completion record](../plans/2026-10-11-strategic-architecture-migration.md#four-bank-completion--2026-10-11)
retains that evidence. This is not approval to implement the additional domain examples.
