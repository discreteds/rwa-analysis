# Mortgage distribution evidence and calculation inputs

**Type:** research

**Status:** OPEN — initial official-source leads located; CR9 default-outcome evidence
reviewed in existing PDFs. Further acquisition, extraction and calculation integration
remain outstanding.

**Owner:** rwa-analysis disclosure research / analytical inputs

**Requested:** 2026-10-11. Gather supporting evidence on mortgage composition and
market shares, retain its meaning and provenance, and join it into calculations to
constrain assumed within-band PD distributions.

## Research objective

Narrow the combinations of PD dispersion, LGD dependence, product mix and regulatory
treatment that can explain disclosed CR6 RWA. Start with CBA June 2025 and Westpac,
NAB and ANZ September 2025. Supporting observations should become reusable inputs;
an assumed distribution fitted to them remains an analytical result.

The original [PD Differentiation Benefit definition](../../../00.ideation/initial_idea.md#52-pd-differentiation-benefit)
holds LGD and other parameters constant and initially excludes defaulted exposures.
Reported band RWA also reflects heterogeneous parameters, floors and overlays.
One mean PD and one RWA amount cannot uniquely identify the within-band distribution.

## Evidence sought and its use

| Evidence | Intended use | Applicability question |
|---|---|---|
| Owner-occupied/investor and P&I/interest-only shares, preferably cross-tabulated | Constrain mortgage multiplier categories | Stock or new lending; balances, limits, EAD or counts; same population as CR6? |
| Number of mortgaged investment properties per borrower | Constrain the historical five-or-more-property category | Customers versus properties versus exposures; mortgaged properties versus properties owned; category boundary and exposure weighting? |
| Portfolio facilities, lines of credit, subaccounts and security counts | Interpret average EAD per agreement and product concentration | What is counted; does product terminology establish regulatory treatment? |
| LVR distributions, LMI, LGD methodology and any PD cross-tabs | Constrain LGD assumptions and PD–LGD dependence | Origination versus dynamic LVR; drawn balance versus limit; averages do not establish joint distributions |
| Floors, overlays and model changes | Separate adjustments from distributional residuals | Effective period, CR6 applicability and any disclosed allocation |
| Bank housing balances and corresponding market totals | Calculate consistent market shares and understand CR6 coverage | Domestic ADI versus consolidated group; included subsidiaries; stock versus flow; common denominator |
| Average-PD/LGD weighting and count definitions | Establish the moments used by the inversion | EAD-weighted versus account-weighted; agreements versus distinct borrowers |
| Published historical default rates and annual default-event counts | Compare assigned PD with realised experience; investigate empirical grouped discrimination | Cohort, observation window, denominator, exits, new entrants and initial rating assignment must be established |

## Initial official-source leads

These are discovery leads, not acquired or fully reviewed evidence. Search excerpts
are insufficient for promoting numerical observations or assumptions. Read the actual
tables, axes, charts and footnotes and record PDF/printed page locations on acquisition.

| Source | Lead and next inspection |
|---|---|
| [CBA FY2025 results presentation](https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy25/full-year-profit-presentation.pdf) | June 2025 housing balances, accounts, borrower mix, IO, LMI and dynamic LVR. Multiple portfolio tables appear: establish group/brand coverage before selecting one. |
| [Westpac FY2025 presentation and investor discussion pack](https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-full-year-presentation-and-IDP-2025.pdf) | September 2025 mortgage composition, IO, LMI and LVR; inspect investment-property/customer distribution charts and definitions. |
| [Westpac 1H2025 investor discussion pack](https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-1H25-presentation-IDP-2025.pdf) | Search explicitly surfaced “Investment property portfolio by number of properties per customer”. Locate the September equivalent first; March values require an explicit temporal assumption if used. |
| [NAB FY2025 investor presentation](https://www.nab.com.au/content/dam/nab/documents/reports/corporate/2025-full-year-results-investor-presentation.pdf) | Housing product/borrower mix, IO, offsets and LVR. A scope footnote identifies household lending under ARF 720.1 and excludes some counterparties; inspect its applicability before aligning with CR6. |
| [ANZ FY2025 investor discussion pack](https://www.anz.com/content/dam/anzcom/shareholder/full-year-results-announcement/2025-full-year-results-investor-discussion-pack.pdf) | Candidate source for mortgage mix and LMI. Locate relevant tables and distinguish ANZ, Suncorp and NZ populations; the selected CR6 AIRB block excludes Suncorp. |
| [APRA Monthly ADI Statistics](https://www.apra.gov.au/news-and-publications/monthly-authorised-deposit-taking-institution-statistics) | Individual-bank domestic-market data: retrieve June/September 2025 housing stocks and glossary for owner-occupied/investment market-share denominators. Retain dataset vintage/revisions. |
| [APRA Quarterly ADI Statistics](https://www.apra.gov.au/news-and-publications/quarterly-authorised-deposit-taking-institution-statistics) | Property-exposure series supplies industry aggregates for outstanding and new mortgages. Industry evidence can support scenarios, not directly establish a bank's mix. |
| [Historical APS 113, effective September 2024](https://www.apra.gov.au/standards/aps-113-superseded-1), [legal instrument F2024L01074](https://www.legislation.gov.au/F2024L01074/latest/text) | Regulatory basis for the 2025 observations: mortgage multipliers 1.4/1.7/2.5, minimum RW and overall 1.1 scalar. Retain applicable clauses and dates; the superseding June 2026 standard must not silently replace them. |

Reuse the existing [raw inventory](../../../../raw/index.md) and bank CR6 reviews
before acquiring duplicates. Save acquired PDFs under `raw/` and update its index.
Record native statistical downloads and their release/glossary references alongside
the acquisition record; do not add a registration framework.

## Published actual default evidence — initial source review

On 2026-10-11, inspected extracted text and rendered mortgage CR9 pages in all four
already retained PDFs. This establishes published outcome evidence, not implemented
CR9 extraction or approved conformance mappings. Source files/official acquisition
URLs are in the [raw inventory](../../../../raw/index.md).

| Bank and retained source | Exact location | Published evidence and qualifications |
|---|---|---|
| [CBA June 2025](../../../../raw/cba-2025-06-30-aps330.pdf) | PDF/printed p.60, residential mortgage block and notes | Historical annual default rates use data from 2014, with asset classes under standards applicable at the time. Annual backtesting counts cover 1 April 2024–31 March 2025, not the June CR6 date. Internal grades are mapped to disclosure bands by their midpoints; inspect this before assuming every underlying PD lies inside a printed interval. |
| [Westpac September 2025](../../../../raw/westpac-2025-09-30-aps330.pdf) | PDF/printed p.55 mortgage block; p.56 notes b–d | Historical rates use ten years. Annual counts track July 2024–June 2025; PD and EAD weights are anchored at June 2024. Default counts include both initially performing borrowers and new borrowers who subsequently default; the latter are separately disclosed. |
| [NAB September 2025](../../../../raw/nab-2025-09-30-aps330.pdf) | PDF p.60/printed p.58 definitions; PDF p.61/printed p.59 mortgage block | Historical rates use ten years of initially non-defaulted cohorts, with best-efforts retrospective asset-class alignment. Annual defaults include borrowers non-performing at any month-end during the financial year, including those later cured or exited; new borrowers are separately disclosed. Counting refers back to CR6 (mortgage agreements). Weighted PD is at reporting date, so do not assume it is the opening-cohort prediction. |
| [ANZ September 2025](../../../../raw/anz-2025-09-30-aps330.pdf) | PDF/printed p.66 mortgage block and notes; p.116 modification detail | Mortgage historical rates use five years. The 2.5-year exception is for corporates, not mortgages. Historical-rate numerator excludes technical defaults; denominator excludes exited obligors. Mortgage historical portfolio rate is explicitly 0.62%. Exact annual cohort/rating anchors need further review. |

### Source-reported average historical annual default rates (%)

These are historical outcome rates, not model PDs and not latest-year default rates.
Different history windows and definitions prevent treating them as a matched-period
performance comparison. Values below were checked against the rendered source tables.

| Disclosed PD band | CBA | Westpac | NAB | ANZ |
|---|---:|---:|---:|---:|
| 0–<0.15% | 0.07 | 0.06 | 0.10 | 0.08 |
| 0.15–<0.25% | 0.16 | 0.15 | 0.21 | 0.18 |
| 0.25–<0.50% | 0.29 | 0.27 | 0.38 | 0.34 |
| 0.50–<0.75% | 0.46 | 0.52 | 0.58 | 0.52 |
| 0.75–<2.50% | 1.06 | 0.98 | 0.98 | 1.06 |
| 2.50–<10% | 2.80 | 5.80 | 4.71 | 2.99 |
| 10–<100% | 13.32 | 17.92 | 23.48 | 11.19 |

Capture annual default counts, new-entrant defaults, opening/closing populations and
published historical rates as distinct measures. Derive a one-year opening-cohort rate
only after establishing the matching denominator and band assignment; do not simply
divide all defaults by closing counts. Do not average historical band rates using
current CR6 counts to invent a published historical portfolio rate.

Outcome evidence can inform calibration scenarios and, where matched cohort counts
permit, a grouped realised Gini. Historical averages alone do not establish a current
cohort's ROC/Gini or identify within-band PD dispersion. Keep count-weighted outcomes
separate from EAD-weighted PDB and model-implied Gini. Defaulted stock, arrears, losses
and default-event incidence remain different measures.

## Incorporation into calculations

### CR9 temporal/interface design — researcher direction, 2026-10-12

Use CR9 as the second concrete domain to establish the shared interfaces with CR6.
The design must support recognising revised historical calculations across reports
and extending historical coverage by acquiring earlier and later report vintages.
This direction led to the approved design and spike shape below; it is not an
implemented CR9 pipeline.

Written proposal: [CR9 capture and shared domain interfaces](../../superpowers/specs/2026-10-12-cr9-domain-design.md).
The design and disposable spike shape are approved. The refined production
specification is under review before implementation planning; no production CR9
pipeline is delivered yet.

Keep document reporting/publication dates distinct from field-specific measurement
dates, cohort anchors, outcome intervals and historical calculation windows. Retain
source calculation/methodology changes separately from our extraction and semantic
interpretation revisions. Known window length does not always establish exact bounds.

Preserve each published occurrence. A changed value for the same period and measure
is evidence to investigate, not automatic proof of a bank restatement; a shifted
rolling window, changed cohort or methodology can also explain differences. Preserve
unchanged repeated evidence without adding its population twice.

Historical coverage can grow by collecting annual observations and overlapping
window-level observations at their disclosed grains. A rolling aggregate does not
provide its individual annual components.

**Confirmed scope, 2026-10-12:** capture and tag each published datapoint appropriately.
Preserve annual observations where individually identifiable and rolling-window
observations as published. Temporal meaning must resolve at field/occurrence level:
adjacent columns in one CR9 row need not share a measurement date or window. Shared
descriptors may be referenced without duplicating their contents for every cell.
Keep unknown bounds, source wording, evidence and interpretation status visible.

Aggregation, period alignment, vintage selection, comparisons of possible revisions
and any assumption-based reconstruction are bespoke analytical choices. This design
does not introduce an automatic historical-series builder, rolling-window aggregation,
deduplication policy or rule that newer reports replace older evidence. Explicit bank
restatement statements and approved interpretation links can be retained as metadata;
numeric differences alone do not create those links. Derived results remain distinct
from reported observations.

Metadata ingress and constructor validation refactoring remain on their separate
techdebt items and are not prerequisites for designing these CR9 interfaces.

Use the existing evidence/catalogue/layer separation. Supporting financial values
are observations with metadata, not loose attributes copied onto every CR6 row.
Choose the smallest representation after inspecting the evidence; this item does
not prescribe a new schema, package or general-purpose solver.

- Retain stable observation references, value/unit/precision, source and location,
  observation date, reporting entity, geography, portfolio/subset, regulatory basis,
  stock/flow, denominator/weighting and applicable inclusion rules.
- Keep published statements separate from researcher-approved scope bridges and
  assumptions. Record the rationale, evidence, applicable period and retained revision
  of a reusable interpretation. Unresolved meanings remain explicit.
- Join compatible supporting observations at the analytical layer using their scope
  and dates. Organisation name alone is insufficient. Record any balance-to-EAD,
  group-to-ADI, all-mortgage-to-AIRB or date bridge as an explicit assumption.
- Preserve the source grain: attaching one portfolio constraint to a calculation
  must not duplicate it into additive band facts or multiply EAD through a many-to-many
  join. Band-specific constraints require band-specific evidence or an assumption.
- A retained calculation identifies the Silver publication, supporting observation
  revisions, assumptions and capital-function version. Persist useful results selectively.

## How evidence constrains distributions

For compatible EAD-weighted evidence, let `w_b` be each band's share of the selected
portfolio and `x_b` its unknown investor fraction. A disclosed portfolio investor
share `s` constrains `sum(w_b * x_b) = s`, subject to source rounding or an explicitly
chosen uncertainty interval. It does not establish `x_b = s` in every band.

Use joint OO/investor × P&I/IO observations where available. Marginal shares alone
constrain overlap bounds; they do not establish independence. Likewise, property-count
shares by customer cannot become EAD shares without an explicit exposure-size bridge.
Whole-book evidence needs a bridge before constraining the non-defaulted population.

Market shares constrain the relevant market/bank totals, not PD allocations directly.
Industry averages may inform a labelled scenario range but are not bank observations.
Unknown categories remain unknown; overlapping subsets are not an exhaustive partition.

Keep feasible families/ranges where several distributions fit. If a chosen scenario
cannot reproduce the observations, report that scenario's limitation rather than
altering captured evidence. These are analytical constraints, not processing validators
or publication gates.

## Work and completion evidence

- [ ] Acquire and inspect the four bank packs and dated APRA data; record exact table
  locations, definitions, denominators and unresolved gaps in a compact evidence inventory.
- [ ] Prioritise Westpac's property-count evidence and NAB's housing-scope/counting
  definitions; ask the researcher about material scope bridges and uncertain mappings.
- [ ] Extract the located CR9 mortgage outcome evidence and its cohort/history
  definitions with independent source expectations. Investigate opening-rating
  assignment, exits, new entrants and observation dates before deriving annual rates
  or realised Gini, or joining calibration evidence to CR6 distribution scenarios.
- [ ] Retain source-backed supporting observations and approved interpretations in
  the existing architecture, with any required model changes separately designed.
- [ ] Demonstrate one real bank calculation joining supporting evidence to CR6,
  preserving CR6 row counts/EAD and using each portfolio constraint once. Show the
  feasible distribution range before/after adding evidence; report unchanged or
  incompatible ranges honestly if the evidence does not narrow them.
- [ ] Extend the evidenced joins/scenarios to the remaining banks and calculate
  market shares only for explicitly matched populations and denominators.

Source discovery and the capture-and-tag design scope are recorded. The refined CR9
production specification is under review; acquisition, model implementation and executable
integration remain follow-up work, not completed features.

## Governing principles

- [Evidence and interpretation](../../../01.principles/a.architecture/evidence-and-interpretation.md).
- [Layered, evidence-backed definitions](../../../01.principles/b.data-semantics/layered-metric-definitions.md).
- [Emergent analysis and selective persistence](../../../01.principles/a.architecture/emergent-analysis-and-selective-persistence.md).
