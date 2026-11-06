# Semantic-layer structure, standards and library adoption

**Type:** research / architecture exploration

**Status:** OPEN — umbrella backlog. Primary question: which target structure the
semantic layer adopts. Candidate standards identified from official documentation;
no migration or dependency adoption approved.

**Owner:** rwa-analysis semantic model and consumer integration; shared library
capabilities remain owned by their respective Mountainash packages.

**Requested:** 2026-10-17; refocused 2026-11-06. Identify the target structure for
semantic metadata and observations, and opportunities to replace handwritten schema
and persistence machinery. Keep detailed investigations in separate documents linked
from this item.

## Objective

Choose a target structure that maps equivalent source data from diverse formats and
15+ years of disclosure generations to the same target fields, while preserving
source evidence, contextual meaning, uncertainty and reproducibility. Library and
persistence choices are secondary: they store and generate whichever structure is
chosen but do not decide it.

The governing requirements were agreed on 2026-11-06 and are owned by
[format-independent target fields](../../../01.principles/b.data-semantics/format-independent-target-fields.md):
meaning-based target identity, template/format coordinates as source-side mappings,
external data-point models as reference dictionaries, cross-format goldens proving
convergence, and explicit relationships across regulatory regime changes.

The researcher also highlighted generated dataclasses as a promising authoring
opportunity. That is an investigation direction, not a decision to use LinkML or
change retained formats.

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

## Structure candidates

The standards cover different layers of one structure and are mostly complementary:

| Layer | Candidates | Current equivalent |
|---|---|---|
| Observation/fact shape | EBA DPM / XBRL OIM; SDMX / RDF Data Cube | Contexts, occurrences, bindings, temporal descriptors |
| Concepts and terminology | SKOS | Catalogue concepts, measures, variants |
| Evidence, interpretation, derivation | PROV-O | Assertions, evidence, decisions, revisions |
| Schema authoring | LinkML | Handwritten dataclasses |

The observation layer is the primary decision; vocabularies attach to it.

### Findings, 2026-11-06 (official sources)

- **EBA DPM/XBRL.** From reporting framework 4.1 (reference date June 2025) the EBA
  DPM and XBRL taxonomy include the Pillar 3 disclosure templates for the Pillar 3
  data hub. Quantitative data is submitted as XBRL-CSV in currency units with a
  separate `decimals` precision parameter; voluntary rows/columns outside EBA
  templates cannot be included in XBRL-CSV and remain in the PDF only. The framework
  page publishes the DPM database, dictionary, table layouts, taxonomy and samples.
  Not yet verified: the specific EU CR6/CR9 template definitions in DPM 4.1.
- **APRA.** APS 330 disclosures are not XBRL. XBRL International noted in 2022 that
  they would be more useful in structured form. The in-force APS 330 instead
  requires all quantitative information in CSV, Excel or another APRA-approved
  format on the ADI's Regulatory Disclosures page, and keeps fixed-template row and
  column numbering stable when rows/columns are deleted or sub-rows added.
  Attachment A specifies Australian modifications (for example ECL-stage mapping to
  specific/general provisions and non-performing for defaulted).
- **Existing project evidence.** All four banks' archives link quantitative Excel
  files; none has been downloaded or inspected ([raw index](../../../../raw/index.md)).

Working recommendation, pending the deep dive: use DPM's dimensional decomposition
and BCBS template coordinates as reference dictionaries and source-side mapping
evidence, not as target identities or storage format.

## Deep-dive index

Add links when investigations are actually written; each deep dive links back here
and updates its row with conclusion and evidence.

| Topic | Question | Deep dive / status |
|---|---|---|
| Target-field design across disclosure generations | Express mortgage EAD and average PD from a ~2013–2015 disclosure, a 2018–2022 disclosure and 2025 CR6 (PDF and APS 330 workbook) in the current model, informed by EBA DPM dimensions and SKOS-style relationships. Which target fields hold across all generations, and where are explicit cross-regime relationships required? | Next; oldest generation ~2013–2015 selected 2026-11-06 |
| APS 330 quantitative workbooks | What do the published CSV/Excel files contain, and do they support cross-format mapping goldens against our PDF captures? | Not started |
| Schema ownership and generated dataclasses | LinkML and `linkml-runtime` versus current dataclass-first declarations: what handwritten definitions, loaders or documentation would disappear? | Not started; official documentation reviewed |
| Concepts and terminology | SKOS (RDFLib if RDF interchange is useful): how do stable IDs, labels, definitions and scoped interpretations map? | Not started |
| Evidence, decisions and derivations | PROV-O / Python `prov`: which provenance structures can use standard terms without parallel authoritative records? | Not started |
| Statistical exchange | SDMX / `sdmx1`, RDF Data Cube: is there a concrete exchange consumer? | Not started |
| Analytical semantic interface | dbt MetricFlow as a reference; assess existing Mountainash capabilities first | Not started; downstream |

Project-specific deep dives belong under `docs/00.ideation/`.

## Persistence note: StructureMap

Mountainash StructureMap decomposes and reconstructs plain dataclasses through
queryable tables. It could replace the handwritten
[relational metadata projection](../../../../src/rwa_analysis/domains/source_tables/metadata.py)
for whichever structure is chosen, but does not inform the structure decision.
Consumer qualification is tracked upstream at:

`/home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash-structuremap/a.backlog/plain-dataclass-metadata-roundtrip.md`

Reproduced shared-library findings belong with that owner.

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
The next investigation is **target-field design across disclosure generations**
(first deep-dive row). Acquire the required ~2013–2015 disclosure through the normal
[raw index](../../../../raw/index.md) workflow.

Keep the result in a separate deep dive: recommendation, demonstrated behaviour,
remaining gaps and precise replacement boundary. If adoption is recommended, obtain
the design decision before a production implementation plan. Avoid a multi-phase
migration programme until evidence establishes that one is needed.

## Governing principles

- [Format-independent target fields](../../../01.principles/b.data-semantics/format-independent-target-fields.md)
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

Reviewed 2026-11-06 for the structure findings:

- [EBA reporting framework 4.1](https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks/reporting-framework-41) and [Pillar 3 data hub](https://www.eba.europa.eu/risk-and-data-analysis/pillar-3-data-hub)
- [APS 330 Public Disclosure](https://www.apra.gov.au/standards/aps-330)
- [XBRL International on APS 330 (2022)](https://www.xbrl.org/news/apra-publishes-disclosure-standard/)
