# ANZ September 2025 mortgage CR6 source review

## Inspection and selection

Directly inspected rendered PDF / printed **p. 57**, **p. 6**, **p. 23** and
**p. 116** on 2026-10-10. Read source text on pp. 1, 7, 36, 54–57, 60, 115–116
and 119–120. Renderings were produced from the saved PDF with pdfplumber at
130 dpi, retained as temporary inspection artifacts under
`/tmp/opencode/anz-task3b/`. The [independent golden notes](../../../../../tests/bronze/au/anz/2025-09-30/aps330/golden-notes.md)
record authorship and coverage.

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
