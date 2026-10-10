# 2025 NAB and ANZ disclosures: metadata discovery

## Sources and inspection

Saved all four 2025 quarterly disclosures for each bank, plus ANZ's one-page explanation of the revised disclosure format. Sources and local links are in [`raw/index.md`](../../raw/index.md). Together with CBA/Westpac, the archive now contains sixteen primary disclosures and one supplementary explanation.

Inspected page-by-page layout-preserving text, surrounding definitions and footnotes. Visually checked NAB September's mortgage CR6 and mortgage/BNZ CR9 pages, ANZ September's mortgage CR6 page and ANZ's supplementary explanation. Temporary inspection outputs are in `/tmp/opencode/rwa-2025-spike/`. No production extractor or golden set was created.

| Bank | Reporting date | Mortgage CR6 location | Additional locations |
|---|---|---|---|
| NAB | 2025-03-31 | PDF p. 30 / printed p. 28 | Definitions PDF p. 29; CMS2 PDF p. 12 |
| NAB | 2025-09-30 | PDF p. 49 / printed p. 47 | Definitions PDF p. 48; March comparative PDF p. 52; CR9 definitions PDF p. 60; mortgage/BNZ CR9 PDF p. 61 |
| ANZ | 2025-03-31 | PDF/printed p. 26 | Separate NZ mortgage CR6 p. 29; CMS2 p. 13 |
| ANZ | 2025-09-30 | PDF/printed p. 57 | Separate NZ mortgage CR6 p. 60; March comparatives pp. 61, 64; CMS2 p. 23; mortgage CR9 p. 66; NZ mortgage CR9 p. 69 |

June and December are shorter quarterly reports without mortgage CR6 distributions. NAB's disclosure-requirements index mentions CR6 even when the table is absent, so searching for the template name alone produces false positives.

NAB, ANZ and Westpac now provide a same-reporting-date pilot cohort at both March and September 2025. CBA retains its June/December cycle. Dates can be aligned for the first three, but portfolio and metric definitions still require explicit comparison.

## 1. Band metadata: shared main structure, genuine exceptions

The inspected Australian mortgage CR6 blocks for NAB and ANZ have the same seven non-default ranges as CBA/Westpac, plus a default category and subtotal:

`[0, 0.15)`, `[0.15, 0.25)`, `[0.25, 0.50)`, `[0.50, 0.75)`, `[0.75, 2.50)`, `[2.50, 10)`, `[10, 100)` in percent, followed by `100.00 (Default)`.

However, NAB September **CR9's BNZ residential mortgage block** (PDF p. 61 / printed p. 59) displays only five non-default ranges and one default row:

```text
0.00 to <0.15
0.25 to <0.50
0.50 to <0.75
0.75 to <2.50
2.50 to <10.00
100.00 (Default)
```

There is no displayed `0.15 to <0.25` or `10.00 to <100.00` row in that block. Preserve the five observed non-default bands. Do not create zero-valued missing rows, widen neighbouring intervals or claim the omitted intervals have no exposure without supporting evidence. This is a CR9 observation, not evidence that NAB's Australian CR6 distribution has five bands.

**Metadata needed:** segmentation identity scoped to table/portfolio/entity/date, displayed band count, expected template bands where established, omitted-band status, boundaries/inclusivity, default category, completeness status and row role.

## 2. “Number of borrowers” has different counting units

NAB's CR6 introduction (September PDF p. 48; March PDF p. 29) explicitly defines:

- Corporate, retail SME, sovereign and financial institution counts as **counterparties**.
- Residential mortgage, qualifying revolving retail and other retail counts as **agreements**.
- BNZ counts following the corresponding underlying asset-class convention.

ANZ September p. 57 says the definition of borrower varies by portfolio and that a wholesale borrower can appear in more than one PD band. That footnote does not by itself establish the exact counting unit for ANZ mortgages.

**Metadata needed:** original metric label, count unit (agreement/counterparty/borrower/unspecified), distinctness and cross-band additivity where disclosed, definition text and source reference. A column titled “borrowers” must not automatically become a comparable count of unique people.

## 3. RWA basis changes across tables and banks

NAB CR6 explicitly **excludes RWA overlay adjustments** from RWA and RWA density. CBA CR6 explicitly includes overlays. This changes the meaning of otherwise identically named fields.

For example, NAB September mortgage CR6 reports RWA of **$112,014m**, while its credit-risk summary and CMS2 report **$112,064m**. March CR6 has **$108,967m**, while the summary has **$109,020m**. Retain both as different disclosed measures. The CR6 exclusion policy is relevant context; do not erase the difference by forcing an unconditional reconciliation or assume a band-level allocation.

ANZ September CMS2 p. 23 states its mortgage RWA includes a **$3.1bn PD-model overlay**, introduced in June 2024. Its AIRB mortgage RWA total, **$94,135m**, matches the mortgage CR6 subtotal. Preserve the cross-table source for that overlay context rather than pretending it was stated directly in the CR6 header.

NAB also has a separate group-wide output-floor adjustment ($2,284m at September, PDF p. 12), which is distinct from portfolio overlays and pre-floor CR6 figures.

**Metadata needed:** RWA measure/basis, overlay inclusion status, applicable adjustment amount/date/scope, output-floor treatment and links to supporting disclosures. “Reported RWA” alone is insufficient.

## 4. Organisation is not the reporting entity or portfolio perimeter

ANZ September p. 6 identifies **ANZ BH Pty Ltd** as the Level 2 reporting-group head, **Australia and New Zealand Banking Group Limited** as an ADI subsidiary and **ANZ Group Holdings Limited** as the ultimate parent.

The same page explains that Suncorp Bank was acquired on 31 July 2024. Suncorp is the trading name of **Norfina Limited**, formerly Suncorp-Metway Limited, and uses the **standardised** credit approach. CMS2 p. 23 places it within standardised portfolios, predominantly corporate and residential mortgages. Do not treat all ANZ-group mortgage exposure as the population represented by the AIRB PD bands.

ANZ also discloses a separate RBNZ mortgage distribution (September p. 60) rather than only a combined NZ retail block. NAB separately describes BNZ and provides BNZ mortgage backtesting. NAB's introduction states BNZ RWA/EL uses RBNZ requirements with APRA scaling factors and any APRA-imposed overlays.

**Metadata needed:** institution/brand, legal reporting entity, consolidation level, portfolio entity/geography, included/excluded subsidiaries, approach, regulator/rule basis and effective-date changes. An APRA report filed under `au/anz/` can legitimately contain NZ portfolio observations denominated in AUD.

## 5. Exposure labels and precision must survive extraction

NAB labels the first columns **on-balance-sheet EaD pre-CRM** and **off-balance-sheet EaD pre-CCF and pre-CRM**. Other reports use “original on-balance-sheet gross exposure” and related labels. Preserve these source definitions before deciding canonical equivalence.

NAB reports RWA density to one decimal place (for example, 26.1%); the inspected CBA, Westpac and ANZ mortgage blocks show whole-percent densities. Amounts are generally AUD millions, but this comes from the report's currency statement, not merely `$m` in a table header. Keep displayed precision and source units so reconciliation tolerances are justified.

NAB greys out non-applicable cells. ANZ uses dashes for retail maturity and explains that it is omitted because it is not used in the RWA calculation. Provisions appear only at portfolio level. Preserve the reason for missingness where known: not applicable, not disclosed at this grain, omitted row and unresolved are different situations.

## 6. Backtesting needs richer time and methodology metadata

NAB September CR9 definitions (PDF p. 60) describe PD weighted by EAD **at the reporting date**, a **ten-year** historical-default observation period, and defaults captured at **any month-end** in the financial year, including borrowers subsequently cured or exited. It reuses the agreement/counterparty count conventions from CR6.

ANZ CR9 p. 66 describes a **five-year** historical-default history, with corporate classes restricted to **2.5 years** from March 2023 because of capital-reform classification changes. It excludes technical defaults from the historical-rate numerator and exited obligors from the denominator. Appendix p. 116 explains the corporate exception. Do not apply this corporate 2.5-year exception to mortgage rows.

These differ from the windows and observation points already found for CBA/Westpac. Useful metadata includes PD observation date, performance window, historical lookback, cohort eligibility, default-event definition, numerator/denominator exclusions and retrospective classification policy.

## 7. Source-location and template metadata

- NAB has a two-page offset between PDF positions and printed labels on the inspected main tables.
- ANZ CR6 has numbered source rows; Australian mortgage rows are 10–18 and NZ mortgage rows 84–92. Keep these identifiers alongside semantic band IDs.
- NAB uses source column letters `a`–`l`; keep column identifiers where available.
- ANZ appends a table explaining modifications to BCBS templates. Missing retail maturity is an intentional modification, not a failed extraction.
- The supplementary ANZ format explanation is readable visually but mostly absent from `pdftotext` output. Tool output alone is not adequate evidence that a page has no relevant information.

## Recommended metadata contract, informed by all four banks

Organise the first dataclasses around these responsibilities rather than one unstructured metadata dictionary:

1. **Reporting context:** organisation, legal entity, consolidation, document date and table/observation dates.
2. **Portfolio context:** original classification, scope, regulatory approach, entity/geography and rule basis.
3. **Segmentation definition:** dimension, ordered bands, counts, bounds, inclusivity, default status and observed omissions.
4. **Metric definition:** source label, units/scale/precision, count unit, weighting, exposure basis, overlay treatment, grain and missingness semantics.
5. **Source references and qualifications:** PDF/printed page, template, row/column, footnotes and cross-table context.
6. **Performance context when CR9 is added:** cohort, observation/performance periods, lookback and default definitions.

Persist these with Bronze and include expected metadata in the human/LLM golden sets. Silver should explicitly decide comparability from them. Reuse a definition only when the sources establish equivalence; a matching column title or band label is not enough.

Agreed scope direction: Australian residential mortgages are the first implementation of an extensible model for retail, non-retail and other portfolios across jurisdictions. One source PDF and its bespoke extractor can produce multiple portfolio/jurisdiction blocks in a single Bronze bundle. The `au/anz/` or `au/nab/` source folder describes the disclosure's reporting jurisdiction, not a restriction that every extracted exposure is Australian. Shared context, segmentation and metric dataclasses should remain reusable as new portfolio types are added; portfolio-specific fields evolve from their golden sets.

For the next extraction pilot, retain the agreed CBA/Westpac mortgage blocks and add NAB/ANZ September as schema examples. That exposes the most useful differences without requiring a full historical build. The five-band BNZ CR9 block is a compact future extension for testing that segmentation metadata is genuinely flexible.
