# Emergent analysis and selective persistence

> **Status:** AGREED
> **Scope:** core, Silver, Gold, research

## Principle

Persist durable evidence and curated knowledge; compute exploratory relationships and outcomes as needed. Analytical possibilities do not automatically become core model entities or stored datasets. Retain useful outputs selectively with the information needed to reproduce them.

## Rationale

Reconciliations, residuals and inferred relationships often emerge through analysis rather than being disclosed directly. Modelling and storing every possible combination upfront would burden the core model with speculative structures. A disclosure can also be faithfully extracted even when it lacks the evidence needed to reconcile an analytical relationship.

## Implications

- Preserve source observations, supporting evidence, semantic definitions and versioned mappings as durable inputs.
- Capture curated assumptions and researcher decisions when they become reusable knowledge. Exploratory assumptions can remain with the analysis; a retained result identifies the assumptions actually applied.
- Compute reconciliations, residuals, inferred relationships and cross-document comparisons on demand. No universal reconciliation-definition or assessment table is required by the initial data model.
- Promote a recurring, understood relationship into a reusable analytical definition when research establishes its value and semantics.
- Distinguish source-reported facts, assumption-dependent inference and calculated results. An inferred relationship does not silently become source evidence or an unconditional conformance rule.
- Missing inputs are not zero. An unexplained residual is not automatically an extraction failure, and inability to reconcile does not by itself invalidate a source observation.
- Retained analytical outputs identify input revisions, assumptions and calculation versions. Their storage form and retention follow the research need rather than an obligation to persist every intermediate result.
- Silver conforms the disclosed observations and their meanings. Gold analyses can connect compatible observations across documents and periods, with explicit alignment and assumptions. [Validation is a separate process](../c.extraction-and-validation/validation-is-a-separate-process.md); source evidence does not authorize embedding validation rules in conformance.

## Example

Opening and closing default stocks, twelve months apart, may be compared with a reported default flow. Cures, repayments, write-offs, new arrangements, cohort eligibility and perimeter changes can prevent exact reconciliation. Amount-based stocks may also change through balance movements.

Investigate this relationship using available disclosures and explicit assumptions. Preserve a useful analysis and its provenance when warranted; the possibility of the comparison alone does not justify a new mandatory dataset or a rule that stock changes must equal reported forward defaults.

## References

- [Evidence and interpretation](evidence-and-interpretation.md).
- [Rebuildable analytical layers](rebuildable-analytical-layers.md).
- [Layered metric definitions](../b.data-semantics/layered-metric-definitions.md).
- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md).
