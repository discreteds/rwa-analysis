# Capture and tag for research

> **Status:** AGREED
> **Scope:** core, extraction, Bronze, Silver, Gold

## Principle

The goal is faithful capture and useful tagging of published disclosures, not perfect accounting or an exhaustive reconstruction of a bank's underlying data. PDFs bound what is observable. Downstream research can use approximations, explicit assumptions and imperfectly comparable measures.

## Rationale

Reports will never expose every metric, dimension, cell or underlying arrangement. They differ in scope, rounding and conventions. Requiring complete semantic knowledge or exact reconciliation before retaining or using their data would defeat the research purpose.

## Implications

- Capture the selected disclosed values and structure faithfully and retain source evidence. Do not invent unavailable cells or require reconstruction of undisclosed data.
- Tag known concepts, scope, units, weighting, timing and qualifications; preserve unresolved or provisional interpretations. Semantic enrichment can improve incrementally without making earlier faithful capture invalid.
- Silver can publish faithfully captured observations with partial mappings and incomplete semantics. Expose interpretation status and limitations alongside the values rather than dropping them or rejecting an entire dataset solely for incomplete knowledge.
- Distinguish extraction and structural errors from research limitations. Wrong values, lost rows, invalid references or contradictory units require correction. Missing disclosures, unknown conventions and unreconciled totals may be legitimate limitations, recorded as such.
- Comparability is task-specific. There is no universal comparable/not-comparable gate on the stored observations. Analyses may deliberately compare related but non-identical populations or measures, keeping their differences visible.
- Approximation and assumptions are normal analytical tools. Identify their use and provenance sufficiently to interpret and reproduce retained results; do not present inferred values as source-reported facts.
- Reconciliation is useful diagnostic evidence where appropriate, not a universal acceptance criterion. Apply exact constraints only when source semantics and precision justify them.
- A particular calculation can require an input or convention that is unavailable. Report that limitation or use a justified explicit assumption; it does not make the source observation generally unusable.

## Example

CBA and NAB mortgage RWA can be compared for research even though their disclosed overlay treatment differs. Preserve and tag that difference and any adjustment or approximation used in the analysis. Neither perfect band-level overlay allocation nor exact accounting reconciliation is a prerequisite for capturing the reported measures.

## References

- [Evidence and interpretation](evidence-and-interpretation.md).
- [Emergent analysis and selective persistence](emergent-analysis-and-selective-persistence.md).
- [Source-led extraction and golden sets](../c.extraction-and-validation/source-led-extraction-and-golden-sets.md).
