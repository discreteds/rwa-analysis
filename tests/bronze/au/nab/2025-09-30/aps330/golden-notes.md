# Independent NAB golden

## Adjustment extension — 2026-10-17

`golden-adjustments.json` independently transcribes PDF p.13 / printed p.11:
three overlay amounts, all six mortgage overview cells and the group output floor.
The page was rendered to inspect the table and footnote. CCR dashes remain missing;
$2.3bn and $2.1bn are non-exhaustive components of the $4.8bn credit overlay.
The $50m mortgage bridge is deliberately absent from this source golden: it is a
calculated difference between two stored disclosures. See the
[source review](../../../../../../extractions/au/nab/2025-09-30/aps330/review.md).

Authored 2026-10-10 before the NAB extractor existed. Direct rendered PDF 49 / printed 47 supplied all nine rows and twelve column positions. PDF 48 / printed 46 supplied CR6 definitions and the A-IRB heading; PDF 4 / printed 2 supplied entity, currency, rounding, regulation and consolidation context. The cover and acquisition index supplied document metadata. See the [source review](../../../../../../extractions/au/nab/2025-09-30/aps330/review.md).

The author manually transcribed the complete 9×12 token matrix and source prose into an isolated, one-off JSON authoring script. That script imported neither the extractor nor the codec/models/parser, read no other bank's fixture and consumed no extractor output. It only expanded these reviewed literals into the existing wire schema. `golden.json` was saved before the first test run and before any source-specific production code. Ordinary tests read only this saved JSON.

All columns a–l are retained. Nine maturity cells are `not_applicable` in this CR6 calculation/disclosure context, based on the explicit maturity definition; eight provision cells are `not_disclosed_at_this_grain` based on the provision definition. Shading is retained separately and does not itself prove either meaning. There are 91 numbers and 17 blanks, no dashes. The default row's CCF is 85%; density retains one decimal in every row. The count definition means agreements in this selected portfolio; the full definition distinguishes counterparties in other portfolios. Both RWA and density exclude overlays. EaD pre-CRM wording is preserved without a cross-bank equivalence claim.

The complete contract test is the primary test owner at the real saved-PDF → runner → strict encoded-payload boundary. It catches omitted or shifted columns, selecting Retail SME instead of mortgages, lost source labels/column letters, incorrect two-page offsets, changed missingness, lost precision, inapplicable counterparty conventions, and dropped or mis-scoped overlay qualifications. Existing CBA/Westpac tests exercise different PDFs and cannot catch these source-specific failures. This test needs no mocks or production-only test seam; inventory assertions duplicating the full fixture are deliberately unnecessary.

Red run: `uv run pytest tests/bronze/au/nab/2025-09-30/aps330 -q` failed at `run_extractor` with `FileNotFoundError` for the not-yet-created NAB `extract.py`; the saved source PDF was present. The independent full fixture was already on disk. The extractor was implemented only after observing this failure.
# CR9 addition, 2026-10-12

`golden-cr9.json` is independently transcribed from retained PDF61/printed59's
first Residential mortgage block, PDF60/printed58 notes, PDF46/printed44 ratings,
and PDF48/printed46 agreement-count definition. Rendered PDF61 and PDF46 confirm
geometry and labels. No expected value was generated from the extractor.

This fixture owns all 56 measure positions (51 numbers, two dashes, three blanks),
eight PD bands, sixteen external-rating equivalents, source column order, dated
count columns, field timing, month-end default/cure/exit rules and ten-year history
with unresolved exact bounds. The same PDF's separately labelled BNZ mortgage
block is excluded. The unchanged original golden continues to own all CR6 data.

Test-audit gate: the real PDF-to-bundle boundary catches wrong block selection,
swapped count dates, dropped missing positions or rating labels, and transplanted
bank-specific semantics. Existing CR6 tests cannot cover these CR9 regressions;
the test requires no new production seam. RED: existing extractor returned
`cr6-v1`, failing the mixed-bundle expectation. GREEN: the NAB source contract
passes after implementing the CR9 extension.
