# Westpac September 2025 mortgage CR6 source review

For the subsequently approved non-retail and operational-overlay capture, including
the separately dated October removal, see the
[2026-10-17 adjustment evidence](../../../../../docs/00.ideation/2026-10-17-rwa-adjustment-capture.md).

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

## CR9 extension — reviewed 2026-10-12

Read PDF/printed pp. 55–56, rendered p. 55 at 120 dpi, and re-read the
portfolio, default, program-managed, CR6 and glossary definitions on pp. 33–34,
47–48 and 98. The selected mortgage block has eight rows, with no subtotal.
Its vertically centred label follows three mortgage rows; Corporate precedes
the block and Australian credit cards follows it. Separate geometric windows
retain seven numeric positions and Moody's/S&P equivalents for every row.
The first seven rating pairs are `N/A`; both default-row ratings are blank.
The last three default-row measure cells are blank/shaded. The seventh band's
new-default count is a printed dash, with unresolved meaning, not zero.

The first band reports PDs 0.07%/0.07%, previous/current counts
564,613/571,083, defaults 385 including 7 new borrowers, and history 0.06%.
Notes b–d establish weighted PD and its EAD weights at **June 2024**, defaults
over July 2024–June 2025 including borrowers not funded at the opening point,
and ten years of history. The introductory statement supplies precise annual
boundaries 1 July 2024–30 June 2025. The two end-of-year count headers are
interpreted against that explicitly stated annual period as 30 June 2024 and
30 June 2025; this is header/context interpretation, not a quotation of dates
printed in those headers. No day is added to the June-2024 PD/weight label.
Arithmetic-PD timing and the exact historical endpoints remain unresolved.
There is no implicit document-date fallback or uniform opening-cohort claim.

Note c and the `of which` header establish seven row-scoped field subsets;
the blank default row supplies no default-event count or subset observation.
Note a explicitly concerns non-retail historical proxies and is inapplicable
to this mortgage selection. CR6's report-wide entity, currency, Level 2 and
portfolio evidence is reused with CR9 scope; CR6-specific notes are not.
The PD glossary and program-managed long-run definition qualify both PDs.
The p. 34 default definition qualifies default counts and the default band.
Neither CR6 nor the glossary resolves what exact entity the borrower counts
count, or the history denominator/event/exit conventions; those stay unknown.

The existing PDF extractor now returns CR6 and CR9 in one `disclosure-v2`
bundle. Save under a new output version; retained `cr6-v1` remains unchanged.

## Metadata capture migration — 2026-10-14

The current producer emits `disclosure-v4`, superseding the v2 description above.
`definition.py` declares source structure, interpretation, timing and original
domain addresses; `physical.py` reads grids, regions and column-aware passages;
`extract.py` delegates to shared capture. The snapshot and physical fragments
retain 180 cells: 164 numeric positions and 16 lexical ratings (including printed
`N/A` and blank default ratings). June-2024 PD/weight precision is preserved.
Shared comments are captured once. The default-row qualification is explicitly
declared on numeric cells as well as the row; projection need not infer scope.
The independent goldens remain unchanged, with complete structural comparisons
and direct fragment, rating and default-row applicability regression checks.
