# Complete capture across evolving disclosures

> **Status:** AGREED
> **Scope:** extraction, Bronze, metadata, Silver, downstream analysis
> **Decision context:** Researcher direction during earlier-period scoping, 2026-10-12.

## Principle

Capture each selected table's complete published content and meaning in its source
context. Historical disclosures are not incomplete instances of today's template.
Columns, metrics, bands, definitions and observation grain can change within one
organisation over time. Preserve those differences rather than forcing continuity.

## Rationale

The research will eventually span more than fifteen years. A fixed set of current
CR6/CR9 fields cannot define what earlier reports are allowed to contain. Faithful
capture creates a sparse, heterogeneous evidence base; interpreting that sparsity
and constructing comparable histories are downstream research tasks.

## Implications

- Full capture is relative to the explicitly selected table or portfolio block, not
  every table in a report. Within that selection, retain all published metrics,
  rows, columns, bands, subtotals, totals, nested headers, units, scale, precision,
  missing-value tokens and applicable notes, definitions and relationships.
- Preserve source table names and identifiers. A predecessor table may serve a
  similar research purpose without being the same disclosure or having the same
  grain as modern CR6 or CR9.
- Distinguish an absent column or metric from a published blank, dash, explicit
  zero or stated inapplicability. Preserve the source token; do not assume a dash
  means zero. The physical representation is a design decision, not an instruction
  to manufacture empty current-template cells in every older table.
- Retain original band boundaries, inclusivity and aggregation relationships.
  Transposition or different ordering must not lose meaning. Do not reband, allocate
  values, interpolate or derive missing metrics during faithful source capture.
- A repeated label, column position, table number or organisation does not establish
  stable metric identity. Changes to population, weighting, denominator, timing,
  regulatory basis or footnotes can change meaning without changing the label.
  Conversely, changed wording does not alone establish a new concept. Apply
  [scoped, evidence-backed definitions](../b.data-semantics/layered-metric-definitions.md)
  and retain unresolved equivalence explicitly.
- Shared capture and conformance contracts must accommodate the demonstrated source
  requirements. A published measure must not be dropped, stored as an unrelated
  measure or confined to prose because a current typed row has no suitable field.
  Extend the representation when needed; this principle does not prescribe EAV,
  a universal observation model or a separate schema for every reporting year.
- Keep PDF layout handling local to the bespoke source extractor: page coordinates,
  header traversal, transposed sections and document-specific token handling.
  Semantic differences remain explicit in source metadata and scoped catalogue
  mappings; they must not disappear inside parser branches.
- Generalise helpers or domain contracts from demonstrated source needs. Share a
  capability when its meaning and behaviour are genuinely common, not merely because
  two reports belong to the same bank or have similarly shaped code. Record the
  source cases motivating a shared change and preserve existing extraction evidence.
- Period alignment, rebanding, imputation, inferred metrics, vintage selection and
  reconciliation of changing definitions belong to downstream analysis with explicit
  assumptions. Preserve reported observations separately from those derived results.

## Source-led examples from 2024 discovery

- CBA June 2024, Table 9d(ii), PDF p.49: bands run across columns; repeated sections
  include mortgage average EAD. Neither the transposed layout nor a missing current
  field justifies omitting that measure.
- Westpac September 2024, pp.56–57: portfolio-level historical predicted/observed
  default rates have a different grain from its 2025 CR9 band-level observations.
  Do not manufacture band observations from the portfolio rates.

These are scoping observations from the official PDFs, not claims that historical
extractors or extended contracts are implemented. The earlier-period specification
must establish the complete selected source requirements before implementation.

## References

- [Capture and tag for research](capture-and-tag-for-research.md).
- [Multi-domain source bundles](multi-domain-source-bundles.md).
- [Source-led extraction and golden sets](../c.extraction-and-validation/source-led-extraction-and-golden-sets.md).
- [Emergent analysis and selective persistence](emergent-analysis-and-selective-persistence.md).
- Official [CBA June 2024 disclosure](https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy24/CBA-FY24-Basel-III-Pillar-3-Disclosure.pdf).
- Official [Westpac September 2024 disclosure](https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-pillar-3-report-september-2024.pdf).
