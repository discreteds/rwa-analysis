# Westpac September 2025 mortgage CR6 source review

Reviewed 2026-10-10 from [saved PDF](../../../../../raw/westpac-2025-09-30-aps330.pdf).
Scope: all twelve columns and nine rows of the p. 48 A-IRB Residential Mortgages
block, plus applicable definitions. PDF and printed page 48 agree.

## Layout and source evidence

- Rendered pp. 48–49 at 150 dpi. The block begins at the first PD interval below
  the preceding RBNZ non-retail total, **above** the vertically centred mortgage
  label. It ends at `Total Residential Mortgages`.
- Nine maturity blanks and eight band-provision blanks are genuine empty/shaded
  windows. Default CCF is a printed dash. These cannot become zeros or shift the
  RWA/EL columns. Percent signs belong to the original cell strings.
- The displayed aggregate EAD is 569,920, RWA 116,433 and provisions 1,347 ($m).
  Fourth-band CCF 101% and seventh-band CCF 104% are valid source observations.
- Page 49 footnote a: density uses unrounded numbers. Footnote b is Corporate-
  specific and does not qualify the mortgage block.
- Page 2 establishes reporting entity, AUD, rounding and APRA implementation of
  Basel III. Page 8 supplies the Level 2 definition and default disclosure basis.
- Page 33 defines the mortgage class, including the standardised treatment of
  non-standard mortgages. Page 48's A-IRB introduction restricts this selection.
- Pages 34/44 define default and provisions respectively. Page 47's model table
  places Residential Mortgages in AIRB Program-Managed; its prose establishes
  long-run PD and downturn LGD. Rendered these definitions and the p. 98 glossary.
- Page 98 defines CCF, EAD, on/off-balance exposure and PD. Page 97 footnote b
  qualifies regulatory expected loss and the separate default/non-default
  comparison with eligible provisions.

## Partial semantics

No applicable CR6 averaging weights or exact borrower-count entity were found.
CR9's weighting statement is not borrowed. The glossary Maturity entry is under
Funding and liquidity, so it is not applied to these empty credit-risk cells.
Exact mortgage geography, maturity missingness and default CCF dash meaning
remain unresolved. The retained source definition of regulatory EL does not
establish a complete formula. These limitations do not block faithful capture.

Seven intervals and the separate default category cover the displayed total.
Keep the total relationship to avoid double-counting; no exact reconciliation or
rate additivity is imposed. Publication date and URL come from the acquisition
index; the cover has no printed page label.

See [independent golden notes](../../../../../tests/bronze/au/westpac/2025-09-30/aps330/golden-notes.md)
for authoring provenance and the complete metadata/value test contract.
