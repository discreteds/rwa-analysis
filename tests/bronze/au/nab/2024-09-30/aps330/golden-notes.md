# NAB September 2024 independent golden authoring

Authored before production extraction from the official PDF, rendered PDF pages
38, 40–42 and 50–51 (printed 36, 38–40, 48–49). Text review also covered
introduction p.4, internal ratings definitions pp.45–47 and glossary pp.76–77.
Numbers above are manual source transcriptions, not extractor output.

The selection is 60 exposure cells (five measures × six bands × two panels)
and 30 backtesting cells (two separately labelled mortgage populations × three
panels × five measures). No mortgage total column is printed. Mixed RBNZ retail
exposure rows are outside this mortgage selection. Main and RBNZ backtesting rows
are distinct populations; no additive or subset relation between them is inferred.

Source tests own all 90 values, tokens, precision, axes, scopes and field timing.
They catch omitted comparative panels, loss of percent tokens, main/RBNZ swaps,
invented totals and leakage of APRA LGD floors to RBNZ. Existing CBA tests cannot
exercise NAB's different layout, arrangement average or continuing-balance cohort.
The test uses the real public extractor boundary without a production test hook.

PD history has ten-year duration but no exact start/end dates supplied in its own
paragraph; do not substitute the panel date. The EAD comparison establishes relative
beginning/default timing but no ten-year averaging window. Actual LGD has ten-year
history to reporting date and excludes the latest two years for mortgages; retain
that exclusion without calculating an invented exact effective window. Estimated
LGD is at beginning of year, with the exact date unresolved. The APRA floor note
does not state its numerical level; do not overwrite it using the current RWA
floor discussed elsewhere. The PD model-change note applies to the September
exposure and undrawn rows bearing its marker, not automatically to the comparative.
