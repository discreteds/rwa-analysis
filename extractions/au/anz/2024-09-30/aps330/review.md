# ANZ September 2024 source review

Official tracked source: `raw/anz-2024-09-30-aps330.pdf`.
Reviewed rendered PDF pp.53–55 and 57 (printed pp.52–54 and 56), plus text on
pp.4,25,27–28,46–49,100–101 for scope, definitions and glossary. PDF p.101's
running header says September 2023; it does not change this document's vintage.

## Selection and structure

Four source tables, 125 body cells: three dated exposure panels × five mortgage
measures × eight columns = 120, and one five-measure backtesting row. All values
are numeric, including original comma/percent tokens and displayed precision.
No supplementary financial cells occur within the selected tables' notes.

Table 9(d) has transposed measures and six two-line PD intervals, Default, Total.
The repeated Residential Mortgage rows bind to their measure block. The mortgage
total column is a source total for each measure; averages are not declared sums.
The other portfolios, New Zealand aggregate, table-wide Total rows and % of Total
rows are outside selection. Undrawn commitments are explicitly included in EAD;
eight per-panel subset relationships retain this rather than double-counting it.
Neither exclusivity nor exhaustiveness is inferred.

The source declares AUD millions on p.4 and mortgage AIRB on p.46. Suncorp is
standardised and expressly excluded from IRB-specific tables. Geography remains
unresolved: a source folder and a neighbouring NZ row do not establish it.
The default definition on p.28 and EAD net-of-offsets convention on p.27 apply.
The EAD glossary on p.100 defines facility exposure; it does not establish the
counting denominator of the Table 9(d) average. That attribute remains unresolved.
The unrelated Table 7 half-year average definition is not borrowed.

## Backtesting timing and qualifications

Use the **Retail Portfolios** discussion, not wholesale history:

- Estimated PD: long-run PDs for obligors not in default at September each year;
  2019–2023 history. Actual PD: defaulted obligors up to September 2023 divided by
  obligors measured. No inferred forward annual-cohort equivalence.
- EAD ratio: estimated prior-to-default EAD / realised EAD for defaulted obligors,
  2019–2023 history. Dimensionless, not percent.
- LGD: downturn estimates for accounts defaulted at September each year,
  2018–2022; realised losses for the described observed/defaulted accounts.
  Separately retain the stated exclusion of defaults after September 2023 for
  workout time. Do not repair the apparent timing tension by rewriting either date.
- The historical LGD review sentence is under Wholesale Portfolios and says
  “numbers detailed above”. Retain it unscoped with unresolved mortgage
  applicability, rather than declaring the retail figures restated.

Catalogue additions establish only source-scoped unit conversions; financial
equivalence to other vintages or banks is not established. Eight mappings cover
the exact four dataset/template/portfolio occurrences with unrestricted effective
bounds, not invented measurement-date applicability.

## Verification

Independent goldens were authored before production code from the reviewed PDF.
The initial full-source test failed because the extractor did not exist. After
implementation all 125 numbers and the structural/temporal metadata passed.
An additional source-definition expectation failed for the missing default
definition before p.27–28 qualifications were added.

- `uv run pytest tests/bronze/au/anz/2024-09-30/aps330 -q`: 1 passed.
- Focused `ruff check` and `git diff --check`: passed.
- Real Bronze save/load: exact bundle equality, 125 cells across four datasets.
- Isolated catalogue load and resolution: 72 million-scale money cells, 52 percent
  cells, one dimensionless EAD ratio, all with established conversion factors.
- Retained proof root: `/tmp/opencode/anz2024-proof-fmsll7ym`.

The parent task owns shared catalogue selection and persisted integration proof.

## Metadata migration — 2026-10-14

Task 4 now uses `definition.py` for reviewed selection, physical parameters,
contexts and occurrence bindings; `physical.py` supplies physical readers, and
`extract.py` calls `run_capture`. New output is `disclosure-v4`. The independent
`golden.json` remains unchanged; all 125 financial cells retain their source IDs.

Rechecked the selected tables and definition pages against this PDF, including
rendered pp.53 and 57. Exposure heading selection starts after each panel's date
to avoid the same words in the table title. The p.53 average-EAD heading spans two
lines; its passage ends at the first Residential Mortgage row. Backtesting headers
use reviewed column regions. Shared comments retain explicit qualification targets;
the wholesale LGD review remains unscoped evidence. PD/EAD history 2019–2023, LGD
history 2018–2022 and the September 2023 cutoff are explicit retained declarations.

The extended source-owner test first failed because output was still v3, then
passed with v4, checking captured field/block/column headings and retained timing
in addition to the existing source expectations. Verification:

- `uv run pytest tests/bronze/au/anz/2024-09-30 tests/bronze/au/anz/2023-09-30 -q`: **2 passed**.
- Focused Ruff and `git diff --check`: passed.
- RED/GREEN logs: `/tmp/opencode/anz2024-task4/red.log` and
  `/tmp/opencode/anz2024-task4/green.log`.

No shared-code requirement was identified in this source migration.
