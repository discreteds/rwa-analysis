# Westpac September 2024 mortgage source review

## Selected evidence and capture

Reviewed the tracked official PDF, including rendered pages 42, 45, 56, 57 and 58.
PDF and printed page numbers are identical. Context comes from pp.2, 7 and 14;
applicable credit-risk and RWA glossary entries come from pp.113–114. Appendix V
p.107 identifies the historical disclosures as APS 330 Table 9(d) and 9(f).

One `disclosure-v3` bundle contains six source tables:

| Dataset IDs | Source | Body cells | Supplementary |
|---|---|---:|---:|
| `table9d-2024-09-30` | p.45 first panel | 72 | 2 |
| `table9d-2024-03-31` | p.45 second panel | 72 | 0 |
| `table9d-2023-09-30` | p.45 third panel | 72 | 0 |
| `table9f-2024-09-30` | p.57 first panel | 6 | 0 |
| `table9f-2024-03-31` | p.57 second panel | 6 | 0 |
| `table9f-2023-09-30` | p.58 continuation | 6 | 0 |

The 234 body positions and two supplementary positions retain exact source tokens,
Decimal quantities and displayed precision. Body cell addresses are
`band-<0..8>/<field>` and `mortgage/<field>`. Exposure fields are `outstandings`,
`undrawn`, `ead`, `pd`, `lgd`, `expected_loss`, `rwa`, `risk_weight`.
Backtesting fields are `expected_loss`, `predicted_pd`, `observed_pd`,
`predicted_lgd`, `observed_lgd`, `ead_variance`. Supplementary fields/cells are
`irb_rwa` and `standardised_rwa`, without invented row/column positions.

Exposure Subtotal relates to the six non-default bands; Total relates to Subtotal
and Default. Roles retain source labels with the shared `total` relationship kind.
Default is its own band kind. Boundary inclusivity, completeness and mutual
exclusivity remain unresolved. Nested Default rate and Loss Given Default headers
distinguish the repeated Predicted/Observed labels in backtesting.

## Interpretation boundaries

- The source says Level 2, Advanced IRB, AUD and Westpac Banking Corporation and
  controlled entities. The selected portfolio is not asserted to be Australia-only.
- Page 42 explicitly describes average PD and facility-level regulatory expected
  loss, with different default/non-default calculations. The aggregate expected
  loss is not reconstructed from the displayed averages.
- Page 45 notes distinguish drawn outstandings and committed undrawn balances.
  The EAD glossary includes outstandings plus expected drawn committed undrawn.
  Glossary PD is through-the-cycle one-year probability; LGD is downturn severity.
  Default refers to the NPE definition from January 2023; this is attached to the
  exposure default band, not imposed on historical backtesting years.
- The supplementary September 2024 IRB $131,989m and standardised-equivalent
  $214,081m figures remain separate from body RWA $116,228m. Their reconciliation
  is unresolved, and neither replaces the other.
- Page 56 establishes historical annual non-defaulted opening cohorts, annual
  default outcomes, long-run predictions, downturn LGD/regulatory minima, and
  historical Basel II-to-III mapping. It gives 2008 for *most* portfolios, not an
  established mortgage-history start. Exact history endpoints remain unknown.
- Residential mortgage LGD excludes recent defaults with a two-year workout;
  this is retained in the qualification and LGD history descriptor. No exact
  two-year-shifted endpoint is invented.
- Page 57 defines EAD comparison using predictions **up to** one year before
  default and observed EAD for defaulting obligors. This is not a fixed annual
  date or an EAD ratio field. `(1%)` in September 2023 is numeric `-1`; both 2024
  dashes remain unresolved missing values.
- Footnote e on pp.57–58 places historical NZ default/LGD/EAD results within
  asset classes above. It qualifies the five historical fields, not snapshot
  regulatory expected loss. Exact NZ contribution and weighting are unresolved.
- Backtesting regulatory expected loss alone receives the panel measurement
  date. Historical rates receive history roles; default cohorts, rating assignment
  and annual outcomes retain distinct descriptors without panel-date fallback.

The separate loss-experience table on p.56 and other portfolios are outside this
approved selection. No modern CR6/CR9 fields or bands are manufactured.

## Verification and integration

Independent goldens were written before the extractor. The focused source test
first failed because the historical extractor did not exist, then passed against
the real PDF. A later qualifier-scope assertion caught missing band scope and was
repaired before delivery. Saved tests require no LLM calls.

This extractor uses shared SourceTable models and primitive decimal parsing only;
it does not import another bank's extractor or read golden files. No runtime
validation is added. Catalogue mappings, legacy adaptation and workflow integration
are owned by the parent task; the identifiers above are the integration interface.
