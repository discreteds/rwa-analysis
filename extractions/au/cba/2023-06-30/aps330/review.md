# CBA June 2023 mortgage source review

Official archive PDF: `raw/cba-2023-06-30-aps330.pdf`. Reviewed the source text,
rendered PDF pages 51–53 and 57, and definitions on PDF pages 4–6 and 45–46 before
constructing the bespoke extractor. PDF page numbers exceed printed labels by two.

## Selection and counts

| Dataset | PDF / printed page | Body cells | Numeric notes | Qualifications |
|---|---|---:|---:|---:|
| `table9d-ii-2023-06-30` | 51 / 49 | 40 | 2 | 13 |
| `table9d-ii-2022-12-31` | 52 / 50 | 40 | 1 | 12 |
| `table9d-ii-2022-06-30` | 53 / 51 | 40 | 1 | 12 |
| `table9f-ii-2023-06-30` | 57 / 55 | 2 | 0 | 7 |
| `table9f-iii-2023-06-30` | 57 / 55 | 3 | 0 | 8 |

Five datasets, 125 body cells and four supplementary note cells: **129 cells**.
Fifty-two qualification occurrences include the scoped source definitions. Five
mortgage exposure metrics run across eight native PD-band/default/total columns.
Separately presented loss-experience and mixed RBNZ retail aggregates are excluded.

## Entity, perimeter and meaning

Page 4 establishes CBA and its subsidiaries (the Group) and Level 2, excluding the
insurance business and certain securitisation entities. Pages 45–46 establish IRB,
one-year PD, long-run PD estimates, retail default, downturn LGD and EAD definitions.
Definitions retain their actual page evidence and field/band scope. The selected
mortgage rows do not establish a complete geographical boundary or named currency;
both remain unresolved. A dollar symbol alone does not establish AUD. Average EAD
has monetary units but its averaging/counting denominator remains unresolved.

June 2023's heading explicitly says Revised Framework, with footnote 1 dating the
change to 1 January 2023. Page 5 describes predominant AIRB credit-risk calculation
from 1 January 2008 until 31 December 2022; that historical context is retained for
the comparative panels, without applying June 2023's revised-framework note to them.
No canonical semantic equivalence across this change is asserted.

June 2023 has the 1.10 scaling factor and a $7.4 billion RWA overlay exclusion.
The overlay's marker 4 is on the mortgage LGD row; preserve that attachment rather
than relocating it to risk weight. Both 2022 panels have 1.06 scaling and no overlay
note. Supplementary quantities retain their original precision and source form.

Undrawn commitments are expressly included in total credit risk exposure: eight
cell-level subset relationships retain this. Five total relationships per panel
record the published total column, not an assertion that average EAD/LGD/risk-weight
totals are additive. Native interval upper bounds are explicitly exclusive;
lower-bound inclusion is not established. No exhaustive/disjoint partition is inferred.

## Backtesting timing and restatement

The page 57 introduction expressly uses prudential requirements **prior to** the
revised framework, with new asset classes to be captured from 1 July 2023. It is
scoped to both selected backtesting datasets. The panel date is not the historical
window. PD averages start in 2016, without an explicitly reported end date; the
source describes beginning-of-financial-year non-defaulted borrowers and annual
default outcomes. Retail LGD covers defaults in financial years 2016–2022, whereas
non-retail's 2016–2021 period must not be applied to mortgages. EAD compares estimates
before default with realised EAD; its historical endpoints remain unknown.

Unlike FY24, FY23's June 2023 restatement for financial periods 2016–2022 explicitly
marks the mortgage row in both tables. Retain a row-scoped qualification applying
to both PD fields and all three LGD/EAD row fields. The source does not justify
limiting the latter restatement to actual LGD. Footnote 2's minimum regulatory floor
is scoped specifically to estimated downturn LGD. No NZ-only restatement is cloned.

## Catalogue and extension seam

`catalogue/mappings/cba-historical-2023-v1.json` adds 13 exact-occurrence unit
conversions only. IDs include `cba-fy23-` so the June 2023 publication remains distinct
from the FY24 report's repeated June 2023 comparative. No new canonical measure,
concept, or implied cross-framework equivalence is introduced. The parent release
must select these 13 revisions alongside its existing members.

Shared SourceTable, axis/field/cell, temporal and qualification constructors already
cover this source. `exposure` owns FY23 page parsing, panel-specific footnote markers
and actual note inventory; `backtesting` owns its row attachments and history windows.
The extractor does not import another dated extractor. A concrete reuse candidate
with FY24 is the exposure-grid assembly (five measure blocks, eight bands, totals
and undrawn subsets), receiving explicit field declarations, panel labels, parsed
tokens, definitions and qualifications. A smaller candidate is reported-decimal and
source-reference construction. Any future helper must accept those source-specific
inputs, especially note inventory, framework and restatement scope, rather than
inherit them by bank/year. No framework change is required for this delivery.

## Independent verification

Goldens were transcribed from the reviewed source before implementation. The new
source-contract test first failed because the dated extractor was absent, then
passed against the implementation. It protects all source numbers, precision,
panels, field/row/column paths, native bands, relationships and scoped timing/notes.
These are development checks, not runtime validation or publication gates.
