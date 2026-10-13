# Contextual source occurrences

> **Status:** PROPOSED
> **Scope:** extraction definitions, source metadata, Bronze, semantic catalogue, Silver
> **Basis:** Researcher direction and assessment against captured disclosures, 2026-10-13.

## Principle

An extraction is defined by bindings between physical sourcing, semantic meaning and
the context in which content is extracted. Tables, fields, rows, columns, cells and
comments participate as identifiable occurrences in this model. Their structure,
payloads and relationships remain distinct and queryable.

Reusable definitions are singly owned, revisioned metadata. Occurrences reference
those definitions and explicitly record source-specific applicability or refinements.
Reusing meaning or context does not merge published occurrences. Partial or unresolved
meaning is retained rather than preventing capture or conformance.

## Rationale

The same measure can appear on different axes, the same label can change meaning,
and adjacent cells can describe different populations or periods. Definitions and
comments can govern multiple tables, while one value can depend on several passages.
Neither a fixed domain row nor a PDF coordinate alone describes an extraction.

The existing representation already preserves much of this evidence. The proposed
change is to make these bindings the governing model for every occurrence kind,
rather than principally resolving financial fields and attaching other content to them.

## Implications

- Physical sourcing identifies the document and relevant locations, together with
  the operation and parameters needed to obtain content. Recorded evidence identifies
  the locations actually used. Supporting definitions can come from several passages;
  a source reference is not limited to one rectangle or one label.
- Semantic definitions describe financial concepts and also structural roles,
  populations, temporal roles and qualification meanings. A comment retains its
  wording independently from the interpretation of what it qualifies. Researcher
  annotations retain researcher provenance; they are not presented as PDF content.
- Context binds reusable roles to applicable circumstances: entity, portfolio,
  regulatory basis, segmentation, units and temporal roles, where relevant. For
  example, a history-window definition is reusable; its 2018–2022 bounds belong to
  the applicable occurrence. Shared context can be referenced and explicitly refined
  at table, axis, field or cell scope. Conflicts remain visible; narrower scope or
  physical nesting alone does not silently override meaning.
- Extraction selection records which published content was selected. It is distinct
  from the population or period that content describes. A field absent from the
  selected block is not evidence that it is absent from the entire report.
- An occurrence may bind several sources, contextual roles and semantic assertions.
  The three aspects are not a mandatory tuple of three fully resolved identifiers.
  Source missingness and unresolved meaning are independent; preserve zeros, blanks,
  dashes and lexical inapplicability without manufacturing absent occurrences.
- Relationships identify their endpoints, scope and evidence: containment, ordered
  header paths, qualification applicability, totals and subsets. A subset does not
  imply that children are exhaustive or mutually exclusive. Meaning can depend on
  both axes and on linked comments, rather than a simple parent-inheritance chain.
- Published occurrence identity remains independent of mutable interpretation.
  Repeated observations in different report vintages remain distinct; apply
  [correction-safe identity](../b.data-semantics/correction-safe-identity.md).
- Singly defined means one authoritative definition per revision, reused by explicit
  reference. Materialised copies preserve definition identity and revision without
  becoming independently maintained authorities.
- Common participation does not require one universal row shape. Tables still own
  ordered structure, cells carry typed payloads, and comments carry statements and
  qualification links. No particular storage engine or physical schema follows from
  this principle.

## Assessment against captured sources

| Source case | Required behaviour |
|---|---|
| CBA/ANZ transposed exposure tables versus Westpac band rows | Preserve physical axes independently from measure identity. |
| NAB main and RBNZ mortgage backtesting | Bind row-specific populations and qualifications within a shared table. |
| ANZ September 2023 backtesting | Bind estimated-PD history 2018–2022, EAD history 2018–2023 and LGD history/cutoffs separately. |
| CBA June 2023 LGD and $7.4bn overlay footnote | Retain the comment, its applicable LGD relationship and its separately queryable numerical observation; do not apply it to the 2022 panels. |
| Westpac September 2022 default-band PD `N/A` | Retain the occurrence and token without confusing it with an absent field or zero. |
| Original 2023 panels and 2024 comparatives | Reuse established meanings without merging source occurrences or inferring equivalence from equal values. |

Evidence: [2023 source reviews and execution record](../../00.ideation/2026-10-13-historical-2023-capture.md)
and [historical implementation lessons](../../00.ideation/2026-10-13-historical-implementation-lessons.md).
These cases support the conceptual shape; the existing successful pipeline does not
prove a new metadata-driven implementation.

## Proposed replacement and retained decisions

Until accepted, this proposal does not supersede existing AGREED guidance.

- **Broaden** [layered, evidence-backed definitions](../b.data-semantics/layered-metric-definitions.md):
  replace its metric-centred governing scope with definitions and contextual bindings
  for all occurrence kinds. Preserve its financial distinctions, semantic revisioning,
  evidence, explicit overrides, scale requirements and field-specific timing.
- **Refine** [complete historical capture](historical-disclosure-capture.md#source-defined-capture-and-composable-metadata):
  extend its field/cell occurrence model to tables, axes and comments under the same
  binding model. Preserve full selected-source capture, structural research and
  unresolved comparability.
- **Retain** [evidence and interpretation](evidence-and-interpretation.md),
  [correction-safe identity](../b.data-semantics/correction-safe-identity.md) and
  [capture and tag for research](capture-and-tag-for-research.md).

The companion [metadata-driven journey](metadata-driven-extraction-and-conformance.md)
defines the proposed processing responsibility. Physical contracts, composition
interfaces and migration remain subsequent design work.
