# Metadata-driven extraction and conformance

> **Status:** AGREED
> **Scope:** extraction, Bronze, Silver, declarations, processing ownership
> **Basis:** Researcher direction and assessment against captured disclosures, 2026-10-13.
> **Accepted:** 2026-10-13. Governing design constraint; not a claim of implementation.

## Principle

The [source–meaning–context bindings](contextual-source-occurrences.md) define an
extraction and govern its journey through Bronze to Silver. Physical sourcing,
semantic interpretation and contextual applicability are singly defined metadata
consumed by the relevant stages, rather than independently restated in extractors,
domain transformations and storage mappings.

Executable operations implement the declared behaviour. Source-specific code supplies
physical extraction where necessary; shared processing applies selected definitions,
conversions and projections. Metadata drives these operations without requiring every
PDF parsing algorithm to be expressed as declarative data.

## Rationale

Current extractors combine PDF navigation, table assembly, contextual assertions and
qualifications. The catalogue resolves field meaning separately, while declarations
already drive much of conformance and persistence. This partial separation leaves
several places to maintain the shape and applicability of one extraction.

The ANZ reform-matrix repair demonstrates that physical sourcing can need specialised
code. Its headers and semantic applicability nevertheless belong in explicit bindings.
The cross-vintage captures demonstrate that common processing can preserve independent
occurrences without a separate financial pipeline for each report year.

## Implications

- Reviewed metadata selects captured content, physical bindings, applicable definition
  revisions and contextual relationships. Operations receive these declarations;
  financial meaning and qualification applicability are not hidden in parser branches.
- A physical operation can use coordinates, header recognition, table extraction or
  document-specific text-layer handling. Its declared inputs and captured outputs
  connect to the occurrence model. Bespoke sourcing remains available without owning
  a parallel semantic model or a separate Bronze-to-Silver pathway.
- Bronze retains original payloads, tokens, source structure, evidence and the bindings
  used to capture them. Retained definitions or pinned references make those bindings
  reproducible. Merely referencing a mutable current file does not establish that.
- Silver consumes saved Bronze and explicitly selected interpretation revisions. It
  resolves contextual meaning, applies declared conversions and materialises useful
  relations. It does not reread PDFs or independently infer definitions from labels,
  neighbouring columns or the report date. Revised interpretations remain traceable
  alongside the captured bindings rather than silently replacing their history.
- Structural conformance can proceed with unresolved financial meaning. Preserve
  source values and known conversions without claiming established comparability.
  Metadata is not an analytical eligibility gate.
- Declarations for conformance, storage and reconstruction consume the same authoritative
  definitions and bindings. Derived schema information or explicit technical storage
  associations may be required; they must not duplicate financial definitions or
  create a competing inventory of what source content is allowed to exist.
- Domain-shaped CR6/CR9 outputs remain useful projections. Their fixed field inventories
  do not govern capture completeness.
- Apply [correction-safe identity](../b.data-semantics/correction-safe-identity.md):
  distinguish extraction corrections, interpretation revisions and bank restatements.
- Independent source review and goldens remain external evidence for implementation
  correctness. Expected results generated from the extraction definitions themselves
  cannot establish that those definitions faithfully represent the PDF.
- Use existing Mountainash declarations, conformance, relations and storage capabilities.
  Definition placement and sourcing interfaces remain design decisions; metadata-driven
  processing alone does not justify a new language, registry or orchestration framework.

## Journey against an existing case

For ANZ September 2023 backtesting, physical sourcing obtains the five mortgage
values and the applicable explanatory paragraphs. Contextual bindings associate each
field with its own disclosed history or outcome window. Bronze retains the tokens,
paragraphs and bindings. Silver applies selected unit conversions and interpretations,
preserving the distinct windows and unresolved meanings. Source-shaped reconstruction
and research queries consume those same retained relationships.

A correction to the interpretation of a retained paragraph can reconform Bronze;
discovering that the paragraph itself was mis-extracted requires corrected capture.
Neither correction requires copying the temporal definitions into a bank-specific
Silver algorithm.

## Clause supersessions and retained decisions

Accepted 2026-10-13. The following ownership clauses are superseded; continuing
constraints in the affected principles remain AGREED. This decision does not migrate
the existing implementation or retire its retained capture formats.

| Superseded principle clause | Agreed replacement | Retained responsibility |
|---|---|---|
| [Source-led extraction](../c.extraction-and-validation/source-led-extraction-and-golden-sets.md), Principle and local-layout implication: each PDF receives a bespoke Python extractor owning layout handling | Each PDF receives reviewed extraction metadata; bespoke physical operations are supplied where required. | Source scrutiny, independent goldens and full selected content. |
| [Multi-domain bundles](multi-domain-source-bundles.md), Principle and extension implication: a PDF owns an extractor and bundle | A PDF owns a logical source bundle whose selected capture is described by bindings; adding selected content extends those bindings and expectations. | One source bundle, distinct contextual populations and retained output versions. |
| [Historical capture](historical-disclosure-capture.md), local layout handling and composed capture clauses | Physical layout choices belong to source bindings and their selected operations; contextual semantics have separate authoritative definitions. | Source-specific layout support, demonstrated reuse and no silent semantic inheritance. |
| [Composed processing](composed-processing-and-organisation-staging.md), opening paragraphs and domain-declaration ownership | Metadata-defined capture and contextual conformance govern the pathway; domain records are projections and technical declarations consume those definitions. | Independently callable stages, ordinary Python, Mountainash, settings/operations/storage separation, organisation staging and atomic master publication. |

Retain [rebuildable layers](rebuildable-analytical-layers.md),
[selective analytical persistence](emergent-analysis-and-selective-persistence.md),
[Mountainash-first implementation](../d.coding-practices/mountainash-first.md) and
[separate validation](../c.extraction-and-validation/validation-is-a-separate-process.md).
The agreed journey does not define validation or add runtime gates.

## Decision boundary

Affected clauses and indexes record this acceptance under the
[principle maintenance rules](../PRINCIPLES.md), preserving continuing decisions and
replacement links. The [metadata-driven extraction design](../../04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md)
develops these constraints. Implementation still requires design approval and a
real-source spike under the project workflow; principle acceptance alone does not
approve a physical schema or migration. Existing capture remains supported.
