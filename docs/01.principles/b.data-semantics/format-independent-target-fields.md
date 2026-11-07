# Format-independent target fields

> **Status:** AGREED
> **Scope:** metadata, mappings, Silver, extraction tests

## Principle

Target fields are defined by meaning, not by any source format or template
generation. Template, row, column, sheet and cell coordinates are source addresses,
mapped to target fields with evidence. The same source data reaches the same target
field regardless of whether it was captured from a PDF table, a structured
spreadsheet or a different historical template. Where regulatory regimes change the
underlying meaning, old and new fields are related explicitly rather than silently
equated or left unrelated.

## Rationale

The research spans 15+ years of disclosures. Machine-readable files (APS 330 now
requires quantitative CSV/Excel publication) and modern BCBS template codes exist
only for recent periods; older disclosures use different tables, layouts and
regulatory rules. Identity derived from any one format or template generation would
force fabricated equivalents onto every other period and could not guarantee that
equivalent source data converges on one field.

Agreed with the researcher on 2026-11-06.

## Implications

- A target field is identified by its concept, measurement basis, unit, weighting and
  applicable dimensions (for example portfolio, approach, PD band, entity level,
  regulatory basis and temporal role), under
  [layered, evidence-backed definitions](layered-metric-definitions.md). Its identity
  does not contain a template code, row/column number or file-format location.
- BCBS/APS 330 template coordinates, EBA DPM codes, legacy table numbers and
  spreadsheet cells are source-side addresses. Each source generation has its own
  scoped mappings to the shared target fields. Stable template numbering remains
  valuable source metadata and mapping evidence.
- External data-point models such as the EBA DPM are reference dictionaries for
  decomposing target definitions into dimensions; adopting their codes as our
  identities would bind fields to one template generation.
- Mapping convergence is verified, not assumed. Where the same period is available in
  more than one format or publication (for example a PDF table and its APS 330
  workbook, or a comparative column restated in a later report), independent goldens
  assert that both resolve to the same target observations. These are saved tests of
  the mappings, not runtime validation; see
  [validation is a separate process](../c.extraction-and-validation/validation-is-a-separate-process.md).
- Regulatory change can change meaning without changing labels: scaling factors,
  risk-weight floors, default definitions and approach changes. A pre-reform measure
  that is not equivalent to a modern field maps to its own field with an explicit
  relationship (for example refinement, variant or approximate correspondence), with
  evidence. It is neither forced into the modern field nor left unrelated.
- A field available only in some generations or formats is legitimate partial
  coverage under [capture and tag for research](../a.architecture/capture-and-tag-for-research.md),
  not a mapping failure.

## Examples

| Source address | Target |
|---|---|
| 2025 CR6 PDF, mortgage block, column EAD post-CRM/CCF | Mortgage IRB EAD (post-CRM, post-CCF) by PD band, period end |
| Same period, APS 330 workbook, CR6 sheet cell | The same target field and observation |
| CBA 2022 panel under 1.06 scaling | RWA variant related explicitly to the June 2023 field under 1.10 scaling and its RWA-overlay note, per the [2023 historical capture](../../00.ideation/2026-10-13-historical-2023-capture.md) |

## References

- [Correction-safe identity](correction-safe-identity.md)
- [Complete capture across evolving disclosures](../a.architecture/historical-disclosure-capture.md)
- [Contextual source occurrences](../a.architecture/contextual-source-occurrences.md)
- [Semantic-layer structure backlog](../../04.planning/a.backlog/research/semantic-layer-schema-and-library-options.md)
- [APS 330 Public Disclosure](https://www.apra.gov.au/standards/aps-330), presentation of disclosures
- [EBA reporting framework 4.1](https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks/reporting-framework-41) (Pillar 3 templates in DPM/XBRL)
