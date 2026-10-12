# Historical mortgage source inventory

Date: 2026-10-12. Status: source-led design evidence, **not approved goldens**.

Reviewed official retained PDFs with layout-preserving text and rendered pages.
Sources and acquisition URLs are in [raw/index.md](../../raw/index.md). PDF page
positions below are one-based. Scope includes mortgage exposure-by-risk-band and
risk-parameter backtesting blocks, all comparative panels and applicable notes;
separate loss-experience tables and non-mortgage portfolios are not selected.

## Exposure tables

| Source | PDF / printed pages | Panels | Mortgage measures | Body cells |
|---|---|---|---|---:|
| CBA Table 9d(ii) | 49–51 / 47–49 | June 2024, December 2023, June 2023 | Total credit risk exposures; undrawn commitments; average EAD; weighted average LGD; weighted average risk weight | 120 |
| Westpac Residential Mortgages portfolio by PD band | 45 / 45 | September 2024, March 2024, September 2023 | Outstandings; committed undrawn; EAD; PD; LGD; regulatory EL; RWA; average risk weight | 216 |
| NAB Table 5.3.B | 50–51 / 48–49 | September 2024, March 2024 | EAD; undrawn commitments; average EAD; exposure-weighted average LGD; exposure-weighted average risk weight | 60 |
| ANZ Table 9(d) | 53–55 / 52–54 | September 2024, March 2024, September 2023 | EAD; undrawn commitments (included in above); average EAD; exposure-weighted average LGD; exposure-weighted average risk weight | 120 |

Amounts are $M/$m; LGD, PD and risk weights are percentages. Average EAD is a
monetary measure, with three displayed decimals at CBA/ANZ and two at NAB.

### Original bands and aggregates

- CBA: `0 < 0.1%`, `0.1% < 0.3%`, `0.3% < 0.5%`, `0.5% < 3%`,
  `3% < 10%`, `10% < 100%`, `Default`, `Total` across columns.
- Westpac: `0.0 to 0.10`, `0.10 to 0.25`, `0.25 to 1.0`, `1.0 to 2.5`,
  `2.5 to 10.0`, `10.0 to 99.99`, `Subtotal`, `Default`, `Total` down rows.
- NAB: `0<0.1%`, `0.1<0.5%`, `0.5<2.0%`, `2.0<5.0%`,
  `5.0<99.9%`, `100%` across columns; no mortgage Total column.
- ANZ two-line headings: `0.00% <0.11%`, `0.11% <0.30%`, `0.30% <0.51%`,
  `0.51% <3.49%`, `3.49% <10.09%`, `10.09% <100.00%`, `Default`, `Total`.

Retain actual label spelling/line structure in extraction evidence. Do not impose
universal inclusivity or silently extend NAB's 99.9 endpoint. ANZ's table-wide Total
and % of Total rows aggregate portfolios; they are not mortgage measures. Mixed NZ
retail aggregates in exposure tables are likewise not mortgage-specific selections.

### Applicable qualifications

- CBA: undrawn commitments are included in total credit risk exposures. The mortgage
  LGD row carries a note excluding a $7.4bn RWA overlay, dated to each panel. Preserve
  that attachment rather than moving it to a seemingly more natural field. Risk-weight
  section notes include a 1.10 scaling factor.
- Westpac: outstandings include certain off-balance-sheet items. Committed undrawn
  concerns undrawn committed exposures at reporting date. Page 42 defines performing
  regulatory EL at facility level using PD × LGD × EAD, and defaulted EL via best
  estimates of loss. Displayed-average products need not equal aggregate EL.
  A p.45 footnote reports September 2024 IRB RWA $131,989m and standardised-equivalent
  RWA $214,081m; the table RWA total is $116,228m. Retain all separately, without
  inventing a reconciliation or replacing the table total.
- NAB: new mortgage PD models changed grade distribution during the six months to
  September 2024. Undrawn is included in total exposure. Average EAD is explicitly
  the simple average by number of arrangements. Prescribed-methodology RWA overlays
  are excluded from exposure-weighted average risk weights.

## Backtesting tables

All selected 2024 backtesting is portfolio-level, without PD bands or count columns.

| Source | PDF / printed pages | Panels / populations | Fields | Body cells |
|---|---|---|---|---:|
| CBA 9f(ii), 9f(iii) | 56 / 54 | June 2024; mortgage | Estimated/actual PD; estimated downturn/actual LGD; estimated/actual EAD ratio | 5 |
| Westpac regulatory loss estimates and actual losses | 56 methodology; 57–58 panels / same | September 2024, March 2024, September 2023; mortgage | Regulatory EL; predicted/observed default rate; predicted/observed LGD; observed EAD variance to predicted | 18 |
| NAB 5.1.J(ii), 5.1.J(iii) | 40–42 / 38–40 | September 2024, March 2024, September 2023; main mortgage AND separately identified RBNZ-subsidiary mortgage | Estimated/actual PD; estimated/actual EAD ratio; estimated downturn/actual LGD | 30 |
| ANZ 9(f) | 57 / 56 | September 2024; mortgage | Estimated/actual PD; estimated/actual EAD ratio; estimated/actual LGD | 5 |

### CBA

June values: PD 0.71% / 0.56%; LGD 20.0% / 2.8%; EAD ratio 1.0. Estimates use
prudential requirements preceding the revised capital framework. PD averages are
“from 2016”; estimated PD uses opening non-defaulted borrowers, and actual PD uses
annual defaults against opening non-defaulted borrowers. Retail LGD concerns defaults
in financial years 2016–2023 with recent defaults excluded for workout. The EAD
ratio's exact historical window is not independently specified. Mortgage downturn
LGD notes APRA/RBNZ minimum floors. Restatement notes say “all retail portfolios” but
markers attach to RBNZ Retail rows: preserve wording/attachment and unresolved
applicability to the separate mortgage row.

### Westpac

In panel order September 2024 / March 2024 / September 2023:
EL 1338 / 1327 / 1166 ($m); predicted default rate 0.77% throughout; observed
0.61% / 0.60% / 0.60%; predicted LGD 20% and observed 1% throughout; EAD variance
`-` / `-` / `(1%)`. Preserve the last as negative percentage variance, not a ratio.

History starts at AIRB accreditation, 2008 for most portfolios; a mortgage-specific
start date is not established. Annual observed rates follow opening non-defaulted
obligors for a year and are averaged over history. Mortgage LGD allows two years
for workout; economic losses include costs and discounted cash flows. EAD uses
predictions up to one year before default. EL includes defaulted/non-defaulted
exposures. Footnote e includes historical NZ performance in these asset classes;
do not assume the same population as the current exposure-band table.

### NAB

Main mortgage, in panel order: estimated PD 0.87 / 0.89 / 0.87 (%), actual PD
0.92 / 0.91 / 0.91; EAD ratio 1.0 throughout; estimated LGD 20.0% throughout,
actual LGD 1.8 / 1.9 / 2.0 (%). RBNZ mortgage: estimated PD 0.99 / 1.00 / 1.01,
actual 0.69 / 0.68 / 0.68; EAD ratio 1.0; estimated LGD 23.0 / 23.4 / 23.7,
actual LGD 1.7 / 1.9 / 2.1 (%).

PD uses ten years and only exposures with balances at both ends of each annual
period. EAD compares opening exposure for initially non-defaulted customers with
exposure at default. LGD uses ten years to reporting date, excluding the latest
two mortgage years for workout. Main mortgage downturn estimates are subject to
APRA floors; RBNZ estimates follow RBNZ rules. PDF p.38 / printed p.36 retains
old asset-class definitions through 31 March 2023 and adds revised-framework
outcomes from 1 April 2023, without retrospective remapping.

### ANZ

September values: PD 0.91% / 0.70%; EAD ratio 1.01; LGD 18.11% / 1.35%.
Retail estimated PD uses opening September non-defaulted obligors in 2019–2023;
actual PD refers to defaults up to September 2023. EAD ratio uses 2019–2023.
Estimated LGD uses September-defaulted accounts in 2018–2022. Actual LGD describes
realised losses and excludes defaults after September 2023. Preserve both window
wording and exclusion cutoff rather than forcing one common time interval.

## Consequences

The inventory totals **516 exposure + 58 backtesting = 574 body cells**, including
published missing positions. Supplementary numerical footnotes and metadata are
additional. These are review counts, to be independently established by goldens.

NAB establishes arrangement-based average EAD; CBA/ANZ counting conventions remain
unresolved. Neither shared labels nor similar ratios establish shared definitions.
Qualifications and temporal meanings need cell-level applicability. Unexplained
differences and ambiguous footnote scope are research limitations, not grounds to
discard captured evidence. Temporary rendered evidence is under
`/tmp/opencode/historical-review/`; retained official PDFs remain the source authority.
