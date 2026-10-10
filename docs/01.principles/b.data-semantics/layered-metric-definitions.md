# Layered, evidence-backed definitions

> **Status:** AGREED
> **Scope:** metadata, Bronze, Silver

## Principle

Metric metadata separates canonical concepts, measurement definitions, reporting definitions and presentation. Published labels map to canonical roles and semantic variants using scoped, versioned evidence. Hierarchical inheritance and overrides are explicit and traceable.

## Rationale

Organisations report similar concepts under different labels, while the same label can hide different counting, weighting or adjustment conventions. Those conventions can evolve independently of the label.

## Implications

- Canonical concepts describe what is measured. Measurement definitions describe population, weighting, denominator, counting unit and adjustment treatment.
- Reporting definitions establish entity, portfolio, regulatory basis and effective period. Presentation preserves labels, units, scale, precision and missing-value conventions.
- Attributes such as geography and currency cut across concept hierarchies and remain reusable rather than generating duplicated branches.
- Mapping applicability includes organisation/entity, domain, table, portfolio, relevant rules and observation dates; document/template restrictions disambiguate comparatives and changed publication conventions.
- Footnotes, introductions, glossaries, methodology sections and appendices can establish variant attributes. Preserve the supporting text, location, scope and whether the interpretation is explicit or inferred from evidence.
- A table-specific qualification can refine a broader definition. Unsupported inheritance or conflicting evidence leaves the affected interpretation unresolved.
- Each conformed observation identifies the effective definition and mapping versions used. A matching canonical concept does not by itself imply analytical comparability.
- Segmentation definitions are similarly scoped. Band boundaries, inclusivity, defaults, omissions and row roles form part of the data contract.

## Examples

| Source evidence | Canonical interpretation |
|---|---|
| CBA mortgage `Sub-total`; Westpac `Total Residential Mortgages` | Portfolio aggregate over the disclosed mortgage PD bands, retaining different source presentation roles |
| NAB mortgage `Number of borrowers` and its CR6 introduction | Borrower-count concept with agreement counting unit |
| CBA CR6 overlay footnote; NAB CR6 exclusion statement | RWA concept with different overlay-treatment variants |

A changed footnote can require a revised mapping even if the published column title stays the same.

## References

- [Initial data model](../../04.planning/superpowers/specs/2026-10-10-initial-data-model.md), sections 11.1–11.2.
- [NAB/ANZ source review](../../00.ideation/2025-nab-anz-metadata-spike.md).
