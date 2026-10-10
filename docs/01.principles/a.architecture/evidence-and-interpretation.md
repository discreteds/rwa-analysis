# Evidence and interpretation

> **Status:** AGREED
> **Scope:** core, raw, Bronze, Silver, Gold

## Principle

The platform preserves what the source reports alongside the evidence needed to interpret it. Canonical interpretations and calculated results remain distinguishable from published observations. Uncertainty is explicit.

## Rationale

Identical labels can describe different measures. Correct numerical extraction does not establish comparability, and plausible assumptions can be wrong during development or operation.

## Implications

- Raw PDFs and `raw/index.md` provide the acquisition record. Acquisition does not require a separate registration or file-identity proof mechanism.
- Bronze preserves source labels, numerical representation, units, row structure, definitions, qualifications and source locations. Structured interpretation of the source retains its evidence and unresolved attributes.
- Silver reads saved Bronze and applies explicit, versioned conformance rules. It does not reread PDFs to fill undocumented gaps.
- Gold calculations identify their inputs and assumptions. A derived value is not presented as a published value.
- Blank, dash, zero, not applicable and not disclosed at the selected grain are distinguishable. No absent band is silently assigned zero exposure.
- PDF page positions, printed page labels and relevant table/row/column locations remain available. Evidence may lie outside the immediate table.

## Example

CBA June mortgage CR6 reports aggregate RWA density of 22%. Dividing displayed RWA by displayed EAD gives approximately 21.583%. The reported percentage and the calculation have different provenance; neither replaces the other. The footnote explaining unrounded density calculations is part of the interpretation.

## References

- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md), sections 7–11.
- [CBA/Westpac source review](../../00.ideation/2025-disclosure-spike.md).
