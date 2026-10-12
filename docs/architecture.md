# Current processing architecture

Updated: 2026-10-12. Describes four-bank CR6/CR9 implementation, including the CR9
delivery on PR #9. This is implemented branch scope, not a claim that PR #9 has merged.

The [principles](01.principles/README.md) own durable decisions. The
[strategic specification](04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md)
records the approved design and its history. Code declarations own exact fields and
physical table names; this guide explains how to use and extend that implementation.

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

## Data flow and ownership

```text
Official PDF + raw/index.md
          |
Source review + independent golden expectations
          |
Bespoke extract.py → composed ExtractionBundle
          |
BronzeStore.save → retained bundle.json → BronzeStore.load
                                             |
Versioned catalogue release -----------------+
                                             |
                           Cr6Pipeline / Cr9Pipeline.conform
                                Mountainash relations
                                             |
                                  SilverCandidate
                                             |
                              organisation staging DuckDB

Selected current staging publications → SilverConsolidator → master DuckDB
                                                               |
Saved Bronze structure + persisted Silver numbers → source-shaped dataframes
```

| Owner | Responsibility |
|---|---|
| [`settings.py`](../src/rwa_analysis/settings.py) | Native Mountainash Settings layers; resolve execution paths against an explicit project root |
| [`composition.py`](../src/rwa_analysis/composition.py) | Construct concrete components; construction does not run processing |
| [`workflow.py`](../src/rwa_analysis/workflow.py) | `OrganisationSession` sequences independently callable stages; `RunResult` returns publication, tables and source bundles |
| [`operations.py`](../src/rwa_analysis/operations.py) | Run explicitly selected extractors and load the explicitly selected catalogue for conformance |
| [`extraction/`](../src/rwa_analysis/extraction/) | Source dataclasses, composed metadata, dataset protocol, lossless codec and reusable parsing; each bespoke extractor owns its PDF layout |
| [`catalogue/`](../src/rwa_analysis/catalogue/) | Load and resolve concepts, definitions, scoped mappings, evidence and researcher decisions |
| [`domains/cr6/`](../src/rwa_analysis/domains/cr6/) | CR6 models, schema/table declarations, Mountainash transformations and source-unit reconstruction |
| [`domains/cr9/`](../src/rwa_analysis/domains/cr9/) | CR9 typed rows, field-level temporal metadata, source-scoped semantic selection, conformance and reconstruction |
| [`storage/`](../src/rwa_analysis/storage/) | Bronze transport, paths, manifests, database connections, transactional publication and master consolidation |

Domain transformations receive data and interpretations; they do not open PDFs,
configuration files or database connections. Settings select execution locations;
the catalogue owns financial meaning. Current dispatch explicitly selects CR6 and CR9;
the dataset protocol is not an automatic multi-domain plugin system.

## Source contracts and normalised Silver

`ExtractionBundle` holds datasets satisfying a small `Dataset` protocol. A
`Cr6Dataset` composes `DatasetMetadata` and exposes `exposure_rows`. Its saved
`cr6-v1` representation retains the earlier `records`/flat-metadata wire shape through
the codec. Python composition does not require rewriting retained Bronze or goldens.
New mixed bundles use `disclosure-v2` with explicit domain discriminators.
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

There is no separate persisted band catalogue or universal numeric EAV table.
Band fields live on observations. Repeated metadata becomes related rows; small
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

The shared `compose_field` combines selected meanings. CR6 retains date-aware
selection; the CR9 adapter selects explicit occurrences and leaves date-restricted
definitions/mappings unresolved rather than substituting the document date.
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

The approved temporary `asdict()`/full-record Polars inference boundary is isolated
in `domains/cr6/metadata.py`. Mountainash owns its relational projections. Its
[removal debt](04.planning/a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md)
requires revisiting nested metadata schemas, not generalising the adapter.
CR9 uses flat dataclass lists through native relation ingress; this does not remove
the existing CR6 nested-ingress debt.

## Execution, publication and reconstruction

`run()` calls extract → save Bronze → reload Bronze → conform → publish → reconstruct.
Master consolidation is a separate call. Targeted stages accept explicit inputs and
do not depend on earlier calls on the same session. See the executable examples in
the [README](../README.md).

`SilverCandidate` and `SilverOutput` expose named `cr6` and `cr9` members. The common
inventory in `storage/tables.py` drives all 27 table writes/readbacks; an omitted
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

Follow [Mountainash-first coding practices](01.principles/d.coding-practices/mountainash-first.md).
Select a real source case, review evidence, extend independent goldens and introduce
only the domain records/contracts it needs. Preserve the one-source-bundle boundary.
Add domain operations and update explicit composition/storage associations when a
new domain is approved; do not force stock/flow or liquidity records into CR6.

## Verification evidence

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
