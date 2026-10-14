# Independent Westpac September 2023 expectations

Authored from the source PDF before implementing its extractor; the JSON is not
an extractor snapshot. Reviewed layout text and rendered PDF pages 2, 44, 56–57.
Each of the 216 exposure positions and 18 mortgage backtesting positions is
transcribed, together with three numerical notes (237 cells total): the two
September 2023 RWA amounts and September 2022's 25% floor. No zero floor is
fabricated for 2023.

PDF/printed pages differ by two: 44/42, 56/54, 57/55; page 2 has no visible
printed number. The invisible annual-report text beneath page 2 must not contaminate
entity, currency or rounding evidence. The rendered Pillar 3 text is authoritative.
Definitions were independently read on PDF pages 6, 13, 22, 41 and 110–112.

Source distinctions that the boundary test protects:
- September 2022 default PD is a published `N/A`, not zero or 100%.
- Outstandings on page 44 means drawn balances, without 2024's off-balance-sheet
  extension. The corporate footnote on page 41 must not replace this mortgage note.
- Note 2 states the September 2022 25% floor and January 2023 removal; it does not
  instruct recalculation of band risk weights or table RWA.
- Supplementary RWA is 132,238/209,292 million and is distinct from the body total.
- March/September 2023 use revised asset classes; the September 2022 exposure
  panel retains the pre-2023 default definition. The new mortgage/NZ class
  definitions are not attached retrospectively to September 2022.
- Backtesting histories retain NZ exposures, unknown calendar bounds, annual
  default cohorts and two-year mortgage LGD workout. They are not annual PD points.
- Bands' shared endpoints do not establish inclusivity or disjointness.

The test owns this PDF extraction boundary. Wrong panel selection, dropped metrics,
altered labels/tokens, wrong printed pages, broad note scope, borrowed definitions,
missing temporal roles or collapsed header paths are credible failures not covered
by other vintages' tests. It invokes the ordinary extractor without test-only seams.

The metadata migration extends this same primary boundary to retained v4 bindings:
physical field/panel headers must match the reviewed PDF, including nested repeated
Predicted/Observed labels; the p.57 shared NZ footnote and separate p.56 occurrence
must retain their actual pages and targets. PDF superscripts are plain digit tokens
in captured header fragments, while the reviewed field labels retain superscripts.
The independent JSON values and note transcriptions are unchanged.
