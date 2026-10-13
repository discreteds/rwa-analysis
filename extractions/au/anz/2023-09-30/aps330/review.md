# ANZ September 2023 mortgage source review

## Selection and evidence

Source: `raw/anz-2023-09-30-aps330.pdf`, official ANZ September disclosure.
Reviewed all selected Tables 9(d), PDF pp.52–54 (printed 51–53), and 9(f),
PDF p.56 (printed 55). Reviewed applicable report context, definitions and glossary
on PDF pp.4–5,25,27–31,45–48,96; rendered pp.45,52,54,56 to check nested headers,
the reform matrix and the placement of the wholesale/retail paragraphs.

Four datasets retain 125 table-body cells: three dates × five mortgage measures ×
eight risk grades (120), plus five mortgage backtesting metrics. There are no
supplementary financial observations in the selected table notes. Table 9(e) loss
experience and mixed New Zealand retail aggregates are outside the selection.
The capital-reform discussion is contextual evidence, not a selected financial
table. The p.25 2024 correction concerns Level-1 capital/RWA, not these mortgage
cells; the downloaded document remains the September-2023 reporting vintage.

Preserved labels, merged date headers, metric blocks, row/column bindings, money
scale, comma/percent tokens and precision. All selected values are numeric.
Six two-line PD intervals precede Default and Total. Lower inclusivity is unstated;
upper bounds are explicitly exclusive. Each metric has a source total edge, without
asserting that averages/rates are additive. Eight per-panel undrawn/EAD subset
edges preserve “included in above”; disjointness and exhaustiveness remain unknown.

## Perimeter and changing basis

PDF p.4 establishes the new ANZ Bank HoldCo Level-2 parent after the 3 January 2023
restructure, naming Australia and New Zealand Banking Group Limited for prior
years. The Sep-2022 comparative therefore retains that former reporting entity;
both 2023 panels and the backtesting table use the current report entity. The
document itself is still issued for ANZ Bank HoldCo. The complete restructuring
paragraph is retained on each dataset.

The same page states that pre-March-2023 comparatives retain pre-1-January-2023
prudential standards and have **not been restated**. The reform paragraph retains
the mortgage LGD model, IRB scalar and NZ-rule changes. The p.45 two-column matrix
establishes mortgage AIRB before and after January 2023; its new NZ asset class
includes all NZ banking-subsidiary exposures formerly reported within the old
classes. This is retained as scoped evidence, not an assumption of stable mortgage
population. Geography remains unresolved: a folder, adjacent NZ row, or reform
description does not establish every exposure's geographic location.

Currency is AUD millions (p.5), default is the p.30 definition, and EAD is net of
credit-risk-mitigation offsets (p.29). PD/LGD definitions (p.46), EAD modelling
(p.48), regulatory adjustments (p.47) and facility EAD glossary (p.96) are retained.
Regulatory adjustment prose describes this report's methodology; the explicit
comparative-basis qualification prevents interpreting it as a restatement of 2022.
The average-EAD denominator remains unknown. Table 7's separately defined half-year
average is not applied to the small per-band Table 9(d) averages.

## Retail backtesting: document-specific timing

The selected mortgage row is governed by **Retail Portfolios**, not wholesale:

- Estimated PD: long-run PD for non-defaulted obligors at September each year,
  history **2018–2022**. Actual PD: defaulted obligors up to **September 2023**,
  divided by obligors measured. No forward-annual-cohort equivalence is imposed.
- EAD ratio: internally estimated prior-default EAD / realised EAD for defaulted
  obligors, independently **2018–2023**; dimensionless, not percent.
- Estimated LGD: downturn LGD for accounts defaulted at September each year,
  **2017–2021**. Actual LGD: realised losses for the described observed/defaulted
  accounts. Retain the exclusion of defaults after **September 2022** separately.
- The historical-LGD-review sentence appears above Retail Portfolios, under
  wholesale, with “numbers detailed above”. Retain it unscoped and mark mortgage
  applicability unresolved, rather than asserting restatement.

These distinct histories/cutoffs are separate descriptors bound to applicable
cells. Copying 2024's combined PD/EAD history or its cutoff would be incorrect.

## Catalogue and reuse

Eight source-scoped conversion mappings reuse existing million/percent/ratio
conventions. All IDs include `anz-fy23-`, so the Sep-2023 occurrence does not collide
with the same observation date in the 2024 document. No new canonical financial
equivalence is asserted: ANZ's definitions do not establish the CBA-specific
historical LGD revision's full semantics. Parent owns the combined release.

Existing SourceTable, temporal, axis, qualification and relationship contracts
fully express this source; no shared protocol or runtime validation change is
needed. A concrete future reuse opportunity is a reviewed transposed-grid assembly
helper taking fields, bands, tokens and per-cell source locations: 2023/2024 ANZ
share this assembly. Keep pages, paragraph boundaries, entity selection, reform
notes and all temporal bindings bespoke. A generic year decrement or import of a
dated extractor would conceal precisely the differences this capture exposes.

## Verification

Independent source goldens were written before production implementation. The
complete-source test first failed because 2023 capture was absent, then passed
against the PDF: four datasets, all 125 values and structural/context/timing
expectations. Parent owns combined release and persisted four-bank integration.

- Focused 2023 and existing 2024 source tests: **2 passed**.
- Focused Ruff checks: passed.
- Real Bronze save/load: exact bundle equality.
- Isolated combined-v1-plus-2023 catalogue load: all eight new revisions resolve
  without collisions; 72 million-scale cells, 52 percent cells, one ratio.
- Native SourceTablePipeline conformance: four tables and 125 cells.
- Retained proof root: `/tmp/opencode/anz2023-proof-x4_b7fzj`.

The conformance run emitted existing model-declaration type-normalization warnings
before succeeding; no new precision or validation guards were introduced.

### Independent-review correction: p.45 matrix

Reviewed `/tmp/opencode/anz-2023-reform-review.png`. The original paragraph-style
extraction interleaved matrix cells and omitted the pre/post column headings. The
earlier golden repeated that corruption; it was corrected independently from the
render before modifying production extraction. The existing 2023 test then failed
on `regulatory-basis` (RED). Bespoke explicit vertical edges now retain the outside
columns, with section headings read separately because they span columns.

Render-verified qualification text (colons/newlines delimit the source cells):

```text
Remains post-January 2023
IRB Asset Class: Residential Mortgages
Borrower Type: Exposures secured by residential property
Rating Approach Pre-Jan 2023: AIRB
Rating Approach Post-Jan 2023: AIRB
```

```text
New from January 2023
IRB Asset Class: Exposures of New Zealand banking subsidiaries
Borrower Type: Includes all exposures in all asset classes for New Zealand banking subsidiaries Reported within all pre-January 2023 asset classes as per APS 113.
Rating Approach Pre-Jan 2023:
Rating Approach Post-Jan 2023: AIRB and Supervisory Slotting
```

The NZ pre-January cell remains empty, not an inferred rating or an invented `N/A`.
After repair, the existing 2023 and 2024 source tests both pass (GREEN: 2 passed).
No additional test, schema, framework or runtime validation was introduced. The
earlier retained proof root predates this metadata correction.
