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

## Source-defined capture and composable metadata

Researcher clarification following the disposable shape spike, 2026-10-12:
source-defined tables own capture completeness. Fixed CR6/CR9 rows remain useful
domain projections, but do not define the allowable fields of a captured table.
This revises the fixed-row capture direction for historical extensions; production
still uses the implemented typed contracts until a subsequent design is approved
and delivered. Preserve existing retained formats and behaviour.

Compose tables from source fields, axes, typed values, temporal bindings,
qualifications and relationships. Reuse shared representation types and
evidence-backed semantic definitions across extracts. Each published field and cell
remains an independently identified source occurrence with its own labels, position,
context and evidence; reuse of a definition does not merge occurrences. Applicable
definition revisions and contextual refinements remain explicit and traceable.
Unknown canonical meaning must not prevent retaining or querying a published value.

The physical schema, reusable field-definition sets and complete composition
interfaces remain subjects of the proposed design. The spike established a small
capture-to-persistence path, not a complete metadata model or migration.

## Report structure as research data

Composable metadata supports analysis of how disclosures change over time,
independently of their numeric results. Retain queryable source structure and its
interpretation links so research can compare:

- Fields appearing, disappearing or moving between nested headers.
- Label changes versus evidence-backed changes in meaning or definition revision.
- Original bands, portfolio grain, units and temporal scope.
- Qualifications and parent/subset relationships.

For example, comparing Westpac's selected 2024 and 2025 backtesting disclosures
should expose the portfolio-level versus band-level structure without manufacturing
matching bands or equating their default-rate definitions. A field inventory query
must distinguish an absent field from a published field containing blanks.

Absence is relative to the reviewed selection: a field outside the captured block
is not evidence that the entire report omitted it. Keep report vintage, measured
period and extraction/interpretation revisions distinct so corrections to our
capture are not presented as bank reporting changes. Unresolved equivalence remains
visible rather than being classified automatically as either continuity or change.

These comparisons are analytical queries over retained metadata. Following
[selective persistence](emergent-analysis-and-selective-persistence.md), this use
case does not require a separate change-tracking service or mandatory stored diffs.

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

- [Approved historical source-table design](../../04.planning/superpowers/specs/2026-10-12-historical-source-tables-design.md)
  and [2024 source inventory](../../00.ideation/2026-10-12-historical-source-inventory.md).
- [Capture and tag for research](capture-and-tag-for-research.md).
- [Multi-domain source bundles](multi-domain-source-bundles.md).
- [Source-led extraction and golden sets](../c.extraction-and-validation/source-led-extraction-and-golden-sets.md).
- [Emergent analysis and selective persistence](emergent-analysis-and-selective-persistence.md).
- Official [CBA June 2024 disclosure](https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy24/CBA-FY24-Basel-III-Pillar-3-Disclosure.pdf).
- Official [Westpac September 2024 disclosure](https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-pillar-3-report-september-2024.pdf).
