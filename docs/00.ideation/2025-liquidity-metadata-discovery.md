# Liquidity metadata discovery

Date: 2026-10-10

Status: Source findings and model refinements for discussion; no production extraction or golden set.

## Inspected evidence

Sources are the saved PDFs in [raw/index.md](../../raw/index.md). Read layout-preserving text for CBA June pp95–96, NAB September PDF pp85–87 (printed 83–85), ANZ September p109 and Westpac September pp88–89. Visually checked NAB PDF pp86–87 and Westpac p88. Temporary text and renders are in `/tmp/opencode/rwa-2025-spike/`.

## 1. Weighted amount is not weighted average

LIQ2 presents unweighted balances by residual maturity and a weighted monetary value. CBA p96 explains that ASF and RSF apply APRA-prescribed factors to liabilities, assets and off-balance-sheet commitments. NAB PDF p85 similarly explains the regulatory weightings.

For example, NAB's operational deposits in LIQ2 show an unweighted `88,584` ($m) and a weighted `44,292` ($m). The latter is a factor-adjusted amount, not an exposure-weighted mean. Do not map the word `weighted` to the PD-weighting definition merely because the same word appears.

Candidate metadata distinction: weighting role (regulatory factor adjustment versus averaging), method/basis and temporal aggregation. A measure may be adjusted and then averaged over time; those are separate operations.

## 2. Reporting date, averaging window and model horizon differ

NAB PDF p85 defines LCR as a simple average of daily outcomes excluding non-business days, over three months. September uses 66 observations; June uses 61. The same page says NSFR uses spot balances. LCR's stress horizon is 30 days; NSFR's funding horizon is one year.

Thus a September date label can mean a quarter ending in September for LCR or an end-September snapshot for NSFR. The model horizon is distinct from either observation window. Residual maturity buckets add another temporal dimension.

Keep the count's subject too: LCR's 66 counts daily observations, not arrangements. CBA p95 reports 61 business-day observations for June. Westpac p88 reports 62 for June, while ANZ p109 reports 65. Preserve these published counts and available calendar conventions rather than imposing one calendar across organisations.

## 3. Average of ratios is not ratio of averages

NAB PDF p85 and Westpac p88 explicitly define quarterly average LCR using daily LCR outcomes/observations. The displayed average HQLA and average net outflows do not provide the daily series needed to reconstruct that exact average ratio.

Capture the reported ratio and its temporal aggregation definition. A ratio computed from displayed average amounts can remain a useful tagged approximation. Agreement after rounding does not establish identical calculation semantics.

## 4. A merged cell can be a total, not a maturity-band value

NAB LIQ2 PDF p87 has four unweighted maturity columns plus a weighted column. Several rows place one value across a merged unweighted region:

- NSFR derivative liabilities: `5,614` ($m).
- Assets posted as initial margin and default-fund contributions: `4,283` ($m).
- NSFR derivative assets: `6,941` ($m).
- Off-balance-sheet items: `221,248` ($m).

Footnote 1 explicitly states these are disclosed in total and not by maturity bucket. The value's visual placement must not assign it to the nearest maturity label or duplicate it across the covered columns. Capture one unweighted total with maturity breakdown `not_disclosed`, retaining its merged source span and footnote.

The same table's named category `No maturity` is different: it is an explicitly reported category, not missing data, a zero-duration interval or the total of all maturities.

## 5. Similar liquidity labels have different aggregation scopes

NAB LIQ1 PDF p86 shows:

```text
Total HQLA                         207,588
    of which alternative assets     3,633
        of which RBNZ securities    3,633
```

The two equal subset values remain distinct source rows, neither additive to the parent. NAB repeats `207,588` in the total-adjusted-value block. Preserve that source occurrence without treating it as an additional asset holding.

Westpac p88 instead displays HQLA of `182,637`, RBNZ securities of `6,709`, and total adjusted HQLA of `189,346` ($m). The source grouping and arithmetic support different scope from NAB's first HQLA row. A row label or template number alone is insufficient to select a cross-bank total.

Footnotes further qualify scope: NAB excludes NZD liquid assets above an NZD LCR of 100% for transferability reasons and discloses an average excluded amount of $5.8 billion. Capture that qualification and amount if selected, without requiring a complete reconstruction of its adjustment.

## 6. An apparent LVR subset includes additional conditions

NAB LIQ2's mortgage child label describes standard loans to individuals with LVR at or below 80%. Footnote 3 also specifies performing, unencumbered standard residential property loans with residual maturity of one year or more, or no defined maturity, under APS 112.

The short label does not contain the full selection rule. Preserve the richer footnote alongside the subset relationship. Structured condition tags can be added incrementally; faithful capture does not require a generic executable predicate language.

## Proposed refinements

- Distinguish regulatory factor adjustment, weighted averaging and temporal averaging as separate semantic roles.
- Capture snapshot/averaging windows, observation-count subject and model horizons independently, only where disclosed.
- Support merged source spans and explicit total/unsegmented scope without inventing maturity-band values.
- Preserve named categories such as `No maturity` separately from missingness.
- Retain repeated source occurrences and scoped subset relationships; equal values alone establish neither duplication nor conceptual identity.
- Keep conditions supplied by notes even before every condition is canonicalised.

These are tags and evidence relationships for incremental model refinement, not requirements for perfect reconstruction or a new persisted analytical framework.
