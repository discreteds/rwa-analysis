# ANZ September 2025 mortgage CR6 and CR9 source review

## Inspection and selection

Directly inspected rendered PDF / printed **p. 57**, **p. 6**, **p. 23** and
**p. 116** on 2026-10-10. Read source text on pp. 1, 7, 36, 54–57, 60, 115–116
and 119–120. Renderings were produced from the saved PDF with pdfplumber at
130 dpi, retained as temporary inspection artifacts under
`/tmp/opencode/anz-task3b/`. The [independent golden notes](../../../../../tests/bronze/au/anz/2025-09-30/aps330/golden-notes.md)
record authorship and coverage.
Self-review also rendered the cover at 80 dpi: PDF p. 1 has no printed page label.

Selected **Sep 25 AIRB Residential Mortgages, source rows 10–18**, on p. 57
(`pages[56]`). Seven non-default intervals, one default category and a named
subtotal supply 108 positions. The subtotal RWA anchor is **94,135 AUD million**.
Retain nested date / AIRB / portfolio / PD-scale structure and original numeric
tokens, including percent signs, trailing decimals, nine dashes and eight blanks.
The provisions column is blank for bands, populated at subtotal only.

## Entity and population

P. 6 names **ANZ BH Pty Ltd (ANZ Bank HoldCo)** as reporting entity and Level 2
group head. ANZBGL is the ADI subsidiary; ANZ Group Holdings Limited is the ultimate
parent. Suncorp is the trading name of **Norfina Limited**, formerly
Suncorp-Metway Limited. The acquisition occurred on 31 July 2024. It is a
standardised ADI under APS 112, not part of the selected AIRB mortgage block.
P. 54 explicitly excludes Suncorp from IRB-specific disclosure tables; p. 23
places it in standardised portfolios, predominantly corporates and mortgages.

P. 60 separately reports RBNZ-regulated NZ mortgages (source rows 84–92).
March comparatives on pp. 61 / 64 are outside the September selection. Future
selections extend this same source bundle with named datasets. `Australia` is a
provisional geography interpretation of the selected AIRB versus NZ blocks,
not a claim about every collateral location or all ANZ-group mortgages.

## Definitions, missingness and modifications

- P. 7 establishes AUD millions and rounding.
- P. 36 CRA defines PD's 12-month horizon, EAD including expected additional
  drawings under committed limits, and economic LGD as a percentage of EAD.
  These definitions do not establish the weighting of CR6 averages.
- P. 57 footnote 1 excludes Specialised Lending subject to supervisory slotting.
- Footnote 2: retail maturity is excluded because it is **not used in RWA
  calculation**. Retain `-` with `not_applicable` and field/binding references to
  the footnote. This does not mean the loans lack contractual maturity.
- Footnote 3 says borrower definitions differ across portfolios and wholesale
  borrowers may appear in multiple bands. Mortgage counted entity and
  distinctness remain **unresolved**; no NAB agreement mapping is inherited.
- The actual applicable modification is **Appendix 1 p. 116, CR6, BCBS column h:
  Retail – Average maturity, Removed**. Its rationale says exclusion is consistent
  with industry practice and does not add relevant information for users. This
  is distinct from the p. 57 RWA-use explanation; both are captured. The separate
  March format-update leaflet is not the source of this September modification.

## Cross-table overlay evidence

P. 23 **CMS2 Sep 25 footnote 2** states that Retail Residential Mortgages RWA
include a **$3.1 billion overlay for the PD model introduced from 30 June 2024**.
It accompanies modelled mortgage RWA 94,135, standardised RWA 22,407 and total
actual RWA 116,542 (AUD million). Only the first matches the CR6 subtotal.
The bundle retains the original statement with its CMS2 location, scope and date
as supporting context for RWA and density. **CR6 overlay treatment remains
unresolved**: equality of totals is not an inclusion rule or band allocation.
Researcher review is needed before promoting a CR6 applicability interpretation.

The subtotal relationship prevents summing bands alongside their total. It does
not establish borrower distinctness, averaging formulas or exact reconciliation
of rounded values. Shared dataclasses already express these source requirements.

## CR9 extension — reviewed 2026-10-12

Read PDF/printed p. 66 and Appendix 1 p. 116 directly; rendered p. 66 at
100 dpi (`/tmp/opencode/anz66.png`) to inspect the two rating columns, multiline
subtotal and blank cells. Read pp. 67–69 to establish the separate AIRB, FIRB
and RBNZ blocks. The selected **AIRB Residential Mortgages** block on p. 66
contains source rows **11–18 and 20**: seven intervals, a default category and
`Sub-Total AIRB Residential Mortgage` (singular, split over two lines).

All seven numeric columns are retained in published order, alongside S&P and
Moody’s rating equivalents. The default row reports 100.00% in both PD columns
and counts 8,879 / 10,121, with three genuinely blank default-event/history cells.
Band 7's new-default count is a dash, retained as unresolved missingness rather
than zero. Subtotal history is the published **0.62%**, not an average of bands.
Subtotal membership and the eight populated `of which` field relationships
(seven performing bands plus subtotal) preserve the source hierarchy.

### Applicable notes and unresolved meaning

- Footnote 1 maps external ratings to bands using the midpoint of each PD range.
  This establishes rating equivalents, not the date of borrower rating assignment.
- Footnote 2 describes **five-year** default history. Its **2.5-year** exception
  applies to **corporate exposures only**, following March 2023 capital reforms.
  Appendix 1 p. 116 explicitly repeats the Corporates-only modification and
  rationale. Retain it as context clarifying the exception, without applying its
  period to mortgage history. The known mortgage duration has unknown endpoints.
- Footnote 3 excludes specialised lending subject to supervisory slotting.
- Footnote 4 says the historical average excludes **technical defaults from the
  numerator** and **exited obligors from the denominator**, aligned with APS 113.
  These exclusions belong to the historical rate; they are not silently applied
  to the two annual default-count columns. The complete denominator/averaging
  formula is not established by this text.
- `Sep 25` is the disclosure label. `End of previous year`, `End of the year`
  and `in the year` do not independently establish exact annual cohort, PD,
  weight-measurement or outcome dates. All such anchors remain unresolved;
  no September-to-September or Westpac July-to-June interval is assigned.
- The arithmetic heading explicitly says `by Borrowers`. Weighted PD does not
  identify its weight measure. Counted entity/distinctness remain unresolved;
  no agreement/arrangement definition or forward-cohort equivalence is imported.
- P. 69 independently labels the RBNZ block and NZ mortgage subtotal. The p. 66
  geography is provisionally Australian, with that evidence and p. 54's Suncorp
  exclusion. Shared entity/Level 2/currency and general PD definition retain their
  existing source evidence, re-scoped to CR9.

The existing logical bundle now includes CR6 and CR9 using `disclosure-v2`.
Retained CR6 goldens and old saved versions are unchanged. ANZ-specific catalogue
assets map supported concepts, units, bands, aggregate role and history exclusions;
they do not define an inferred annual rate. Parent integration owns release
selection and persisted conformance/reconstruction evidence.
