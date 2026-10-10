# Disclosure model: worked source examples

Date: 2026-10-10

Status: Design review examples. Manually populated from inspected sources; not production data, golden fixtures or implemented contracts.

Model: [Initial disclosure data model](2026-10-10-initial-data-model.md). Source catalogue: [raw/index.md](../../../../raw/index.md).

The examples use readable local IDs and abbreviated logical records. They exercise meaning and references, not a final JSON encoding or a universal row schema. Currency symbols/scale are captured as printed; a canonical currency code needs its own evidence. Unstated conventions remain unresolved.

## 1. CR6: mixed measures over a shared population

Source: [CBA June 2025](../../../../raw/cba-2025-06-30-aps330.pdf), PDF/printed p55, residential mortgage CR6 block. The source has seven non-default interval rows, one default category and a `Sub-total` row. Source context is `Subject to AIRB approach`, observation date 2025-06-30.

### 1.1 Field bindings

All twelve typed measure fields bind independently:

| Typed field | Source label | Result unit/scale | Captured semantics |
|---|---|---|---|
| `on_balance_exposure` | Original on-balance sheet gross exposure | $M | Original gross on-balance amount |
| `off_balance_exposure` | Off-balance sheet exposures pre CCF | $M | Pre-CCF off-balance amount |
| `average_ccf` | Average CCF | % | Averaging convention unresolved |
| `ead` | EAD post CRM and post-CCF | $M | Post-CRM/post-CCF monetary exposure |
| `average_pd` | Average PD | % | Period-end EAD weighting, footnote 1 |
| `reported_borrower_count` | Number of borrowers | Count | Exact counted entity unresolved for this source |
| `average_lgd` | Average LGD | % | Weighting unresolved; PD footnote does not apply automatically |
| `average_maturity` | Average maturity | Years | Cells blank in this block; reason not established by the blank alone |
| `rwa` | RWA | $M | Includes overlays, footnote 2 |
| `rwa_density` | RWA density | % | Calculated using unrounded inputs, footnote 3 |
| `regulatory_expected_loss` | Expected Loss | $M | Regulatory credit-risk context; distinct from provisions |
| `provisions` | Provisions | $M | Disclosed only on the portfolio aggregate; detailed accounting scope unresolved |

Source qualifiers:

```text
q-pd:      "Average PD is calculated using EAD at the end of the period."
q-rwa:     "Includes RWA overlays."
q-density: "RWA density is calculated based on unrounded numbers."
```

The shared measure definition for average PD references its weight measure and timing. The selected population comes from each row, not from an unconditional column-wide default-inclusion flag.

### 1.2 Representative typed rows

Numbers below are source values, still in the units above. `blank` means a visually empty cell, not zero.

| Field | Band `0.00 to <0.15` | `100.00 (Default)` | `Sub-total` |
|---|---:|---:|---:|
| On-balance amount | 227,654 | 6,187 | 613,233 |
| Off-balance amount | 53,855 | 15 | 77,787 |
| Average CCF | 100 | 100 | 100 |
| EAD | 281,508 | 6,202 | 691,020 |
| Average PD | 0.08 | 100.00 | 1.47 |
| Reported borrower count | 742,470 | 16,499 | 1,856,895 |
| Average LGD | 14 | 20 | 16 |
| Average maturity | blank | blank | blank |
| RWA | 18,014 | 13,389 | 149,143 |
| RWA density | 6 | 216 | 22 |
| Expected loss | 31 | 285 | 976 |
| Provisions | blank | blank | 1,768 |

Example resolved binding, abbreviated:

```text
source occurrence: cba-june / mortgage-cr6 / band-1 / average_pd
reported value: Decimal("0.08"), original_text="0.08"
published unit: percent
measure concept: probability of default
aggregation: EAD-weighted mean, period-end weights [q-pd]
row population: mortgage PD interval [0.00, 0.15) percent
weight-measure reference: the applicable EAD definition
source location: p55, residential mortgage, first band, Average PD
```

The arrangement-count concept is not assigned to CBA merely because a NAB definition established agreements for NAB. A count result and a monetary weight remain distinct. The total's canonical role can be `portfolio_aggregate`, while its source role/label remain `subtotal`/`Sub-total`. Its membership comprises all eight bands rather than a fictitious total PD band.

### 1.3 Review outcomes

- One typed row supports count, money, percentage and duration fields with independent definitions.
- Default state is population membership here, not a forward default event.
- Missingness is independent of unresolved semantic attributes: reported LGD survives unknown weighting, while band provisions remain absent.
- The whole block has 108 metric positions (nine rows by twelve fields); its earlier exploratory transcription had 17 blanks. This is a fixture-scope expectation for that block, not a class invariant.
- Derived `149143 / 691020 * 100` is approximately 21.583%, while published density is 22%. Capture the reported value and precision; exact ratio reconstruction is not required.

## 2. Credit quality and movements: source hierarchy and two-axis binding

This example family draws on separate source occurrences; each retains its own document and dataset identity.

### 2.1 Nested column definition and coarse detail

Source: [CBA June](../../../../raw/cba-2025-06-30-aps330.pdf), p34, CR1 Loans row.

```text
value: Decimal("48"), original_text="48", unit=$M
row: Loans
header path:
    Of which ECL accounting provisions for credit losses on SA exposures
    Allocated in regulatory category of Specific
date: 2025-06-30
tags:
    measure = accounting provision amount
    approach = source SA category
    allocation = source Specific category
```

The broader Loans allowances/impairments value is `5,966`. The `48` is part of its allocation, not an extra amount to add to it. Retain the sibling General allocation `115` and IRB allocation `5,803` when selected. Their hierarchy is source structure, not a canonical concept taxonomy.

Source contrast: [NAB September](../../../../raw/nab-2025-09-30-aps330.pdf), PDF p35 / printed p33, CR1 Total row. The source's `d/e` field reports combined SA provisions `276`, IRB provisions `5,889`, and total provisions `6,165` ($m). Footnote 1 says the finer SA breakdown is omitted on materiality grounds.

A typed credit-quality row can reference related allocation records at the available granularity:

```text
SA allocation: amount=276, category_scope=combined,
               finer_breakdown=not_disclosed, evidence=footnote-1
IRB allocation: amount=5889
total provision: amount=6165
```

There is no generated Specific/General split. CBA and NAB can still be queried using their shared provision concept and source-specific granularity tags.

### 2.2 Signed presentation

Source: [Westpac September](../../../../raw/westpac-2025-09-30-aps330.pdf), p36, CR1 September Loans row, Allowances/impairments.

```text
reported value: Decimal("-4504")
original_text: "(4,504)"
published unit: $m
source interpretation: allowance presented as a deduction
optional canonical transformation: negate, if the selected measure
                                   definition uses positive magnitude
```

Source sign is preserved even if a mapped canonical field uses positive magnitude. That conversion is not applied to every negative value or to the entire report. Before choosing such a canonical convention, the source-signed amount remains useful as captured.

### 2.3 Of-which relationship across columns

Source: [NAB September](../../../../raw/nab-2025-09-30-aps330.pdf), PDF p37 / printed p35, Residential mortgages row.

```text
parent observation: provisions for non-performing exposures = 501 ($m)
child observation: of which individually assessed provision = 71 ($m)
relationship:
    kind = disclosed_subset
    source_label = "Of which"
    parent_ref = mortgage-row / nonperforming_provision
    child_ref = mortgage-row / individually_assessed_provision
    scope = this source block and observation date
    evidence = column headings and footnote 2
    exhaustive_children = not established by this single child
```

Footnote 2 identifies the parent as Stage 3 ECL, individually and collectively assessed. Capture that evidence. The two values are not additive siblings: summing them to 572 double-counts the child. A calculated remainder can be explored downstream without automatically creating a reported observation.

### 2.4 CR2: one column, different measure and time roles

Source: [CBA June](../../../../raw/cba-2025-06-30-aps330.pdf), p34, CR2. The introduction and rows establish loans, debt securities **and off-balance-sheet instruments** despite the shorter title. The source period is the half year ended 30 June 2025.

| Source row | Decimal value ($M) | Typed temporal role | Measure identified by row |
|---|---:|---|---|
| 1 | 10297 | Opening snapshot | Non-performing exposure stock |
| 2 | 4241 | Period flow | Became non-performing |
| 3 | -1922 | Period flow | Returned to performing |
| 4 | -386 | Period flow | Written off |
| 5 | -1251 | Period flow | Other changes |
| 6 | 10979 | Closing snapshot | Non-performing exposure stock |

An `ExposureMovementRecord` holds the source row, temporal role, reporting-period reference and `ReportedValue[Decimal]`. The source role selects opening/closing versus interval context; it is not a hidden override of one dataset snapshot date. The opening date may be resolved from the preceding period with its derivation recorded, without pretending the short column header directly states it.

The displayed signed bridge sums to 10,979. This is a diagnostic for this disclosed schedule. Row 2 is a monetary movement over a half year, not an arrangement count or automatically a forward 12-month fixed-cohort default outcome.

### 2.5 Review outcomes

- Header paths preserve multiple tags; differing allocation detail does not prevent capture.
- Source relationships retain overlapping populations and prevent naive double-counting.
- Source signs and canonical conventions are separately addressable.
- Row-defined measures and temporal roles fit a coherent schedule without losing snapshot/flow distinctions.

## 3. LIQ2: segmentation, factor adjustment and merged totals

Source: [NAB September](../../../../raw/nab-2025-09-30-aps330.pdf), PDF p87 / printed p85, as at 30 September 2025. Regulatory-factor definitions are on PDF p85 / printed p83.

### 3.1 Source axes and subset

The unweighted header is segmented into `No maturity`, `<6 months`, `6 months to <1 year` and `≥1 year`. A separate column reports weighted value.

| Source item | No maturity | <6 months | 6 months to <1 year | ≥1 year | Weighted value |
|---|---:|---:|---:|---:|---:|
| Performing residential mortgages | 8,049 | 5,132 | 5,461 | 406,449 | 301,921 |
| Of which standard loans to individuals with LVR ≤80% | 5,539 | - | - | 272,036 | 180,424 |

All monetary values are in source $m. Dashes retain their original tokens and unresolved meaning unless an applicable source convention establishes more.

Example `FundingRequirementRecord` instances:

```text
item: performing-residential-mortgages
basis: unweighted_balance
maturity: named category "No maturity"
amount: Decimal("8049")

item: performing-residential-mortgages
basis: regulatory_weighted_funding_requirement
maturity_scope: aggregate_for_item
amount: Decimal("301921")
```

The weighted value is not a fifth unweighted bucket or an exposure-weighted mean. Capture the factor-adjusted monetary measure; do not infer exact factors by dividing rounded totals.

The child mortgage row references its parent and footnote 3, which adds performing, unencumbered, standard residential property loans and residual maturity of at least one year or no defined maturity under APS 112. Preserve this condition text before requiring a complete canonical predicate.

### 3.2 Merged source total

For Off-balance-sheet items, source row 32:

```text
unweighted amount: Decimal("221248")
source location: p87 / printed p85 / row 32 /
                 merged region across dated maturity columns
semantic maturity scope: unsegmented total
breakdown availability: not disclosed, footnote 1

weighted amount: Decimal("10770")
source location: same row / Weighted value column
measure basis: regulatory factor-adjusted amount
```

The merged source span is a location, not a maturity classification. Footnote 1 states “Disclosed in total and not by maturity bucket”. Emit one unweighted total, not three or four copies and not a value assigned to `6 months to <1 year` because of its horizontal position.

For contrast, `No maturity` in section 3.1 is a populated named category. It does not mean unsegmented total, unknown maturity or an absent value.

### 3.3 Time and count companions

NAB's LIQ1 is a three-month average of daily LCR outcomes excluding non-business days, with 66 observations in September. LIQ2 uses spot balances. The 30-day liquidity stress horizon and one-year stable funding horizon belong to definitions; they are not alternative dates for the underlying measurements.

An optional observation-count field has result unit count and counted subject `daily observations`, not arrangement. These companion disclosures demonstrate why result unit `count` alone cannot determine the entity being counted.

### 3.4 Review outcomes

- Source span, semantic segmentation and measure basis are independently represented.
- Unweighted maturity observations and weighted item amounts share context without sharing measure definitions.
- Footnote-backed subset conditions can remain partly textual while useful tags are captured.
- Source snapshot, averaging window, model horizon and count subject do not collapse into one period or unit field.

## 4. Review conclusion and remaining implementation questions

The three example families fit the consolidated model using typed domain records, shared evidence, two-axis bindings and source relationships. None requires a universal cell database, complete semantic knowledge or a stored reconciliation framework.

Implementation still needs to establish actual dataclass ergonomics, serialisation/Decimal round-trips, Mountainash table contracts and backend-supported atomic publication. The first persisted slice will exercise deterministic source identities and repeated-evidence selection. These are implementation checks, not missing financial data to invent.

The examples do not expand the initial golden-set commitment beyond CBA/Westpac CR6. Their role is to keep that first implementation extensible enough for the source diversity already observed.
