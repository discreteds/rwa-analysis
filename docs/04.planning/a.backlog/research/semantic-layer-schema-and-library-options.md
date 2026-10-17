# Semantic-layer schemas, generated models and library adoption

**Type:** research / architecture exploration

**Status:** OPEN — umbrella backlog; candidate technologies identified from official
documentation. No migration or dependency adoption approved.

**Owner:** rwa-analysis semantic model and consumer integration; shared library
capabilities remain owned by their respective Mountainash packages.

**Requested:** 2026-10-17. Identify opportunities to replace handwritten semantic
schema and persistence machinery with reusable schemas, generated dataclasses and
libraries. Keep detailed investigations in separate documents linked from this item.

## Objective

Make the semantic layer easier to author, inspect, persist and evolve while
preserving source evidence, contextual meaning, uncertainty and reproducibility.
Prefer existing capabilities and remove replaced machinery rather than adding a
second independently maintained model.

The researcher highlighted generated dataclasses as a particularly promising
opportunity alongside StructureMap's maturing support for persistence and loading.
This establishes an investigation direction, not a decision to use LinkML or change
retained formats. Earlier deferral of StructureMap implementation is not lifted by
recording this backlog.

## Current foundation

The [current architecture](../../../architecture.md) uses source-local capture
definitions, retained Bronze snapshots and a durable semantic catalogue. Shared
occurrence resolution composes definitions, mappings and contexts, retaining evidence
and researcher decisions. Source relations and CR6/CR9 projections are persisted
through Mountainash and local DuckDB.

Existing Python dataclasses express concepts, measures, assertions, references,
contexts, occurrence bindings and temporal descriptors. Handwritten transport and
relational metadata projection supply potential replacement boundaries. Our own
financial interpretation and applicability rules remain domain responsibilities.

Relevant owners:

- [Catalogue models](../../../../src/rwa_analysis/catalogue/models.py)
- [Capture declarations and snapshots](../../../../src/rwa_analysis/extraction/definitions.py)
- [Temporal descriptions](../../../../src/rwa_analysis/extraction/temporal.py)
- [Occurrence resolution](../../../../src/rwa_analysis/catalogue/occurrences.py)
- [Relational metadata projection](../../../../src/rwa_analysis/domains/source_tables/metadata.py)

## Candidate shape

This is a possibility to evaluate, not an approved target architecture:

```text
One authoritative semantic schema
    ├── generated Python dataclasses
    │       ├── StructureMap: structural decomposition and reconstruction
    │       └── Mountainash: declared tabular schemas and processing
    ├── generated documentation and diagrams
    └── standard vocabulary mappings / interchange representations

Mountainash-data: persistence and readback, including the existing DuckDB path
RWA: evidence-backed meaning, applicability, revisions and analytical interpretation
```

Schema authoring, structural persistence and standard vocabulary alignment are
separate adoption decisions. StructureMap can be evaluated with existing dataclasses;
adopting generated models need not require RDF storage or a new analytical engine.

## Possibilities and deep-dive index

Add links when investigations are actually written; the proposed topics below are
not placeholder documents or implementation commitments. Each deep dive should link
back here and update its row with the conclusion and evidence.

| Topic | Candidate / opportunity | Questions for the separate investigation | Deep dive / status |
|---|---|---|---|
| Schema ownership and generated dataclasses | LinkML and `linkml-runtime`; compare against retaining current dataclass-first declarations | What handwritten definitions, loaders or documentation would disappear? Do generated inheritance, constructor semantics, annotations and references work with both StructureMap and Mountainash? | Not started; official documentation reviewed |
| Structural persistence and loading | Mountainash StructureMap | Can the complete existing and candidate generated models be decomposed and reconstructed independently through the consumer's storage path? Which manual projections can be removed while retaining queryable metadata? | Existing upstream qualification item, referenced below; RWA adoption remains open |
| Concepts and terminology | SKOS vocabulary, RDFLib if RDF interchange/querying is useful | How do stable concept IDs, labels, definitions and specialised relationships map? How are scoped interpretations kept distinct from global concept equivalence? | Not started |
| Evidence, decisions and derivations | W3C PROV / PROV-O, Python `prov` or RDFLib | Which provenance structures can use standard terms? How are interpretation attribution, evidence, calculation inputs and revision history preserved without parallel authoritative records? | Not started |
| Observation structure and statistical exchange | SDMX / `sdmx1`; RDF Data Cube as a modelling reference | Which measures, dimensions, attributes and shared contexts map faithfully? How are partial dates, field-level qualifiers and source occurrences retained? Is there a concrete exchange consumer? | Not started |
| Financial-report interchange | XBRL Open Information Model, Arelle | Are native XBRL sources or export consumers available? Which concepts, facts, units and footnote links are reusable, and what PDF evidence/lexical detail needs our own representation? | Not started |
| Analytical semantic interface | dbt MetricFlow as a reference; assess existing Mountainash capabilities first | What would simplify querying comparable measures, dimensions and derived metrics? Which requirements are already served by our relations and projections? | Not started; downstream interface option |

### Existing StructureMap evidence

The upstream consumer requirement is maintained at:

`/home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash-structuremap/a.backlog/plain-dataclass-metadata-roundtrip.md`

Its 2026-10-17 rebaseline records delivered generic tuple, Literal, Decimal and date
capabilities, including installed-package persistence evidence. Complete RWA-model
and consumer DuckDB qualification remains open. Earlier primitive-type failures are
historical findings, not current gap claims. Consult the live upstream item before
opening another requirement or inferring readiness from a small successful example.

Project-specific deep dives belong under `docs/00.ideation/`, linked from the table
above. Reproduced shared-library findings belong with the existing upstream owner;
this umbrella should retain the consumer consequence and link rather than duplicate
the dependency's implementation backlog.

## Semantic improvements to evaluate alongside library adoption

These are refinements of the existing model and its presentation, not reasons to
introduce another processing layer:

- Make assertions inspectable as **subject + meaning + applicability + evidence or
  decision + revision**. Reuse existing attributes and bindings where sufficient.
- Distinguish concept relationships, disclosed inclusion/subset relationships and
  calculation dependencies. Concept specialisation alone does not establish an
  additive partition or permission to aggregate.
- Expose measurement time, source vintage and interpretation revision separately.
- Distinguish the basis of a statement (source, researcher interpretation or derived
  calculation) from its knowledge status (established, provisional, unresolved or
  conflicting).
- Provide an intelligible resolved-meaning readback: “why does this occurrence have
  this meaning?” First assess a view over existing relations, rather than new storage.

## Evidence needed before choosing a migration

Each deep dive should name the responsibility it would replace, inspect existing
ecosystem capabilities, demonstrate the smallest real example and identify what
code or duplicated maintenance would be removed. A library's advertised generator
or serializer is not proof of compatibility with our complete models.

Initial examples can use ANZ's aggregate overlay interpretation and NAB's derived
bridge. They do not limit acceptance to those cases. Inventory equivalent operations
and shared paths across the capability: tables, axes, cells and comments; all actual
catalogue subtypes and reference/value alternatives; authoring, loading, decomposition,
storage, independent reconstruction and downstream consumption where applicable.

Required preservation includes:

- Exact Decimal values and declared physical precision/scale; original tokens and
  displayed precision remain separate. No floating-point intermediary or sample-based
  schema inference may silently change meaning.
- Native dates, partial temporal bounds and their knowledge states.
- Nested collections, required empty collections, ordering and duplicate memberships;
  distinguish normalisation permitted by an existing contract from a semantic loss.
- Stable application identities and revision-pinned references, including shared
  contexts and distinct occurrences that happen to have equal values.
- Source statements, interpretations, alternatives, evidence and derivations with
  their original scope and provenance.
- Retained-format readability and independently reproducible reconstruction. Record
  generated-model, schema and mapping dependencies needed by a future reader.
- Existing queryable metadata and CR6/CR9/source-shaped outputs through applicable
  Mountainash and DuckDB paths. Package tests for another backend are supporting
  evidence, not proof of this integration.

For generated classes, explicitly inspect constructor coercion/checks, base classes,
immutability, collection representation and type annotations. LinkML's documented
Python generation uses `YAMLRoot` and constructor normalisation; ordinary dataclass
compatibility must be demonstrated. Reconcile these behaviours with the project's
separate-validation principle rather than implicitly adding processing gates.

Do not keep equivalent operations incomplete because an initial example did not
exercise them. Record concrete backend limits and required owner decisions. If a
candidate does not improve the supported contract or maintenance burden, retaining
the existing implementation is a valid outcome.

## Decision boundaries and next step

No schema, wire-format, storage-engine or dependency migration is authorised here.
The next useful investigation is **generated-model compatibility and replacement
value**, paired with the existing StructureMap qualification work. Compare generated
classes with current ordinary dataclasses on real retained models and the actual
Mountainash path before committing to a schema-authoring tool.

Keep the result in a separate deep dive: recommendation, demonstrated behaviour,
remaining gaps and precise replacement boundary. If adoption is recommended, obtain
the design decision before a production implementation plan. Avoid a multi-phase
migration programme until evidence establishes that one is needed.

## Governing principles

- [Contextual source occurrences](../../../01.principles/a.architecture/contextual-source-occurrences.md)
- [Metadata-driven extraction and conformance](../../../01.principles/a.architecture/metadata-driven-extraction-and-conformance.md)
- [Layered, evidence-backed definitions](../../../01.principles/b.data-semantics/layered-metric-definitions.md)
- [Correction-safe identity](../../../01.principles/b.data-semantics/correction-safe-identity.md)
- [Evidence and interpretation](../../../01.principles/a.architecture/evidence-and-interpretation.md)
- [Mountainash-first implementation](../../../01.principles/d.coding-practices/mountainash-first.md)
- [Validation is a separate process](../../../01.principles/c.extraction-and-validation/validation-is-a-separate-process.md)

## Official references

Documentation reviewed during the 2026-10-17 discussion; candidates have not been
qualified against this project's pinned environment merely by that review.

- [LinkML Python generation](https://linkml.io/linkml/generators/python.html)
- [SKOS primer](https://www.w3.org/TR/skos-primer/)
- [RDFLib](https://rdflib.readthedocs.io/en/stable/)
- [PROV-O](https://www.w3.org/TR/prov-o/) and [Python prov](https://prov.readthedocs.io/en/latest/)
- [RDF Data Cube](https://www.w3.org/TR/vocab-data-cube/)
- [sdmx1](https://sdmx1.readthedocs.io/en/latest/)
- [XBRL Open Information Model](https://www.xbrl.org/Specification/oim/REC-2021-10-13/oim-REC-2021-10-13.html)
- [Arelle](https://arelle.readthedocs.io/en/latest/)
- [dbt semantic models / MetricFlow](https://docs.getdbt.com/docs/build/semantic-models)
