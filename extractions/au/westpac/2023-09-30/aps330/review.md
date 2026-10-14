# Westpac September 2023 mortgage source review

## Selection and evidence

Reviewed the official PDF's layout text and rendered PDF pages 2, 44, 56–57.
Context/definitions were read on PDF pages 6, 13, 22, 41, 110–112. Appendix VI,
PDF p.107/printed p.105, cross-references these disclosures to APS330 Table 9(d)
and Table 9(f). PDF page numbers are two greater than printed numbers; the
contents/context page 2 has no visible printed number.

| Dataset | PDF / printed page | Body cells | Numerical notes |
|---|---|---:|---:|
| `table9d-2023-09-30` | 44 / 42 | 72 | 2 |
| `table9d-2023-03-31` | 44 / 42 | 72 | 0 |
| `table9d-2022-09-30` | 44 / 42 | 72 | 1 |
| `table9f-2023-09-30` | 56 / 54 | 6 | 0 |
| `table9f-2023-03-31` | 57 / 55 | 6 | 0 |
| `table9f-2022-09-30` | 57 / 55 | 6 | 0 |

The selected bundle contains 237 cells: 234 body positions and three
numerical notes. The selected portfolio's source spelling is `Residential
mortgages`. Separate actual-loss tables and mixed New Zealand aggregate rows are
outside the selection. No modern CR6 or CR9 rows are manufactured.

## Source semantics and vintage distinctions

- Report context establishes Westpac Banking Corporation and controlled entities,
  Level 2, Advanced IRB and AUD. Geography remains unresolved; Australian filing
  jurisdiction does not establish Australian-only exposure geography.
- Page 22 defines the new residential mortgage asset class (individuals,
  non-business, residential-property security; non-standard loans receive 100%
  standardised weight) and separate RBNZ-regulated New Zealand class. Page 41
  explicitly applies the new classes from 31 March 2023. These qualifications
  attach to the two 2023 exposure panels, not retrospectively to September 2022.
  The 100% non-standard rule describes exposures outside the selected AIRB block;
  it is retained as definition text, not an observation within that block.
- Page 44 note 3 defines outstandings as drawn balances at reporting date. It
  **does not** contain 2024's additional off-balance-sheet wording,
  nor the corporate table's page 41 off-balance-sheet extension. This local note
  owns the mortgage definition. Undrawn and EAD remain separately described.
- Page 41 defines average PD within PD bands and facility-level regulatory
  expected loss, with different default/non-default computations. PD glossary
  supplies through-the-cycle one-year probability; LGD supplies downturn loss
  severity. Weighting conventions are not invented from adjacent columns.
- The default definition changes on 1 January 2023. September 2022's default band
  receives the pre-2023 definition; 2023 default bands receive the NPE reference
  and APS220 definition. These stock definitions are not imposed retrospectively
  on historical backtesting cohorts.
- September 2022 default PD is `N/A`: a decimal-field cell with null numeric
  payload, original token, no displayed precision and `not_applicable` missingness.
  The v4 declaration supplies `not_applicable` on this cell's `CellBinding`.
  Numeric materialisation belongs to shared capture, not the physical reader.
- Page 44 note 2 states a 25% residential mortgage risk-weight floor at September
  2022, removed under the APRA framework commencing 1 January 2023. It qualifies
  RWA and risk-weight fields across the panels, retaining the complete transition
  wording. September 2022 additionally has a `risk_weight_floor` percent note
  cell, measured at that panel date. There is no inferred zero-floor cell in 2023
  and no recalculation of any body value from this floor.
- Note 1 supplies September 2023 IRB RWA 132,238 million and standardised equivalent
  209,292 million. The `irb_rwa`/`standardised_rwa` note cells do not replace the
  table's RWA total of 112,948 million; reconciliation remains a research question.
- Exposure subtotal relates to six non-default intervals; total relates to
  subtotal and default. Boundary inclusivity, exhaustiveness and mutual
  exclusivity are not inferred. Decimal bounds preserve `0.0` versus `0.10`.
- Backtesting uses portfolio-level historical averages since IRB accreditation,
  with 2008 stated for most portfolios rather than an exact mortgage start. It
  retains annual non-defaulted opening cohorts, annual default outcomes, long-run
  predictions and downturn LGD/regulatory minima. Exact historical endpoints
  remain unresolved; panel dates apply to expected loss, not to annual PD points.
- Mortgage LGD excludes recent defaults with a two-year workout. EAD variance
  compares observed EAD with predictions up to one year before default. All three
  selected EAD variances are `(1%)`, numeric -1 percent.
- Page 56 explains best-endeavour realignment to revised asset classes and future
  inclusion from March 2024 when new-class histories become available. Its actual
  wording is retained; the displayed mortgage metrics are not discarded because
  surrounding new-class rows show N/A.
- Footnote 5 retains historical NZ default/LGD/EAD outcomes within the old asset
  classes. It qualifies only the five historical fields, not snapshot expected
  loss. Predicted/Observed paths retain their Default rate versus LGD headers.

## Bespoke interfaces and reusable responsibilities

The external interface is the thin `extract(pdf_path)` entrypoint, calling
`run_capture` with sibling `definition.py` and `physical.py`. The metadata-only
definition owns SourceTable templates, contexts, temporal roles, qualifications,
physical parameters and cell bindings. Physical operations return fragments;
shared capture materialises v4. `ref` owns this PDF's printed-page offset.
No other dated extractor or golden is imported.

Page 2 contains an obscured annual-report text layer. Its visible Pillar 3 body
uses the `WFANIQ+Gotham-Light` font subset. The page-specific font selection was
checked against the render; it avoids corrupting entity, currency and rounding
evidence with hidden annual-report prose. This is a bespoke layout decision,
not a shared PDF-library rule.

The metadata binds separately repeated physical column headers on all three p.44
panels. The repeated Predicted/Observed labels are cropped under their actual
Default rate and Loss Given Default parents on pp.56–57. Common paragraphs are
captured once. The p.57 footnotes serve two comparative panels, while the separately
printed p.56 copies retain their own occurrences. Numerical note cells link to
their comment and retain distinct addresses from body RWA.

## Catalogue and verification

The owned mapping file supplies 12 exact-document/panel/template/portfolio unit
mappings. IDs include `westpac-fy23-` to avoid collisions with September 2023
comparatives already owned by the 2024 mapping file. Percent conversion includes
the floor note; money conversion includes both supplementary RWA amounts.

Existing historical measure definitions are CBA-specific LGD/overlay variants;
modern CR6/CR9 definitions carry distinct dates, weighting or cohort semantics.
None establishes a reviewed reusable Westpac historical definition here. Unit
conversion is therefore mapped while canonical measure equivalence remains
unresolved. A future shared definition requires a reviewed convention and scoped
mapping, using existing attribute-level overrides only with supporting evidence;
matching labels or dates are insufficient. Release selection is parent-owned.

Independent numeric/metadata goldens preceded implementation. The focused test
failed on the absent extractor (RED), then passed against the real PDF (GREEN).
No processing-time validation or reconciliation gate is added.

The real session pipeline was also run with an isolated temporary catalogue
containing the existing v1 selections plus these 12 mappings. PDF → saved/reloaded
Bronze → conformance → DuckDB publication/readback → reconstruction produced six
tables and 237 cells. Readback retained `N/A` as `source_missing`, the floor as
25 percent / normalised 0.25, and supplementary RWA as 132,238,000,000 and
209,292,000,000 AUD. Proof artifacts are retained at
`/tmp/opencode/westpac-2023-proof-uafrj382`. The session emitted the existing native
schema type-normalisation diagnostics and completed successfully. Both the 2023
and 2024 Westpac source tests pass; scoped Ruff checks pass.

## Metadata migration — 2026-10-14

Task 4 source tests were extended before code and failed at the expected v3/v4
boundary (`/tmp/opencode/westpac-metadata-red.log`). The retained independent JSON
golden is unchanged. Physical-only diagnostics match all 237 tokens, all comments,
all body-field headers and panel headings against independent expectations.
The full 2023 capture currently stops in shared `capture.py` on `N/A`:
`parse_decimal_token` raises `decimal.InvalidOperation` despite the declared
`not_applicable` binding. This is a parent-owned shared requirement; no local
workaround or runtime gate is added. The migration is not yet GREEN.
