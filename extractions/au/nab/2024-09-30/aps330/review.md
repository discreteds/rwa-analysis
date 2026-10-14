# NAB September 2024 mortgage source review

Reviewed official `raw/nab-2024-09-30-aps330.pdf` before implementation. Rendered
PDF pp.38, 40–42, 50–51, checked introduction p.4, definitions pp.45–47 and glossary
pp.76–77. Printed page numbering is PDF page minus two.

## Selected scope and interfaces

`extract(pdf_path) -> CapturedBundle` returns `disclosure-v4`, eight `SourceTable`
datasets and 90 body cells:

- `table5-3-b-2024-09-30`, `table5-3-b-2024-03-31`: 30 cells each, five measures
  across six native PD bands. No total column. Mixed RBNZ retail rows are not
  relabelled as mortgages and are not included.
- `table5-1-j-ii-{date}` for September 2024, March 2024 and September 2023: six cells
  each (estimated PD, actual PD, EAD ratio, each for `main` and `rbnz`).
- `table5-1-j-iii-{date}` for those same dates: four cells each (estimated and actual
  LGD for the two separately headed mortgage populations).

Exposure cell IDs are `{field}/band-{0..5}`; backtesting IDs are
`{main|rbnz}/{field}`. Rows retain the full panel/measure/approach or panel/population
header path. Field labels and row labels retain source footnote markers. Six
within-band undrawn subset relationships per exposure panel use cell endpoints;
neither exhaustiveness nor disjointness is inferred. No relation between the two
backtesting populations is manufactured.

## Evidence and qualifications

- PDF p.4 establishes AUD, NAB and its controlled entities and Level 2 reporting.
  The dataset geography stays unresolved; a regulator or subsidiary's name does
  not establish the geography of every mortgage exposure. Backtesting regulatory
  context stays unresolved at table level because both populations are present;
  population block paths and scoped qualifications distinguish them.
- PDF pp.50–51 define average EAD as a simple average by number of arrangements,
  undrawn as included in total exposure, and risk weights as excluding regulatory
  methodology RWA overlays. September's marked exposure/undrawn rows carry the
  six-month PD-model change; no silent inheritance into March.
- PDF pp.45–47 establish twelve-month PD, through-cycle regulatory PD, downturn
  EAD/LGD and retail modelling conventions. The p.76 glossary establishes EAD net
  of eligible financial collateral unless indicated and the default definition.
- PDF p.38 records mixed historical capital frameworks without retrospective
  restatement. Preserve the complete paragraph, including its financial-institution
  example, as contextual evidence rather than recasting it as mortgage weighting.
- PDF p.40 PD methodology requires a non-defaulted opening cohort **and a balance
  at both ends** of the twelve-month period. This is not assumed equivalent to an
  unrestricted forward default cohort. Ten-year PD history has unresolved exact
  bounds. EAD ratio compares beginning-period EAD with EAD at default; its history
  duration and exact dates remain unresolved.
- PDF p.41 LGD estimates refer to beginning of year without a precise date. Actual
  LGD uses net write-offs over ten years to reporting date, excluding the latest two
  years for mortgages. Retain the exclusion in the attached qualification; do not
  fabricate adjusted window bounds or treat ten years as eight years.
- APRA floors qualify only main estimated LGD; RBNZ prescribed LGDs qualify only
  RBNZ estimated LGD. Current retail RWA floor text on p.47 is not substituted for
  the historical LGD floor note. RBNZ materiality notes remain row-scoped.

## Catalogue handoff and verification

`definition.py` owns reviewed source-table templates, contexts, physical parameters
and occurrence bindings. `physical.py` returns only source fragments; `extract.py`
is a thin call to shared `run_capture`. Headers and comments are captured from
the PDF, including cropped multi-column glossary definitions. Backtesting field
headers use reviewed column geometry. Exposure headers are selected after the
panel date, and the population heading excludes the adjacent percent-unit columns.
Shared methodology text is captured once; repeated floor/materiality notes retain
their separate printed panel occurrences and explicit targets.

`catalogue/mappings/nab-historical-2024-v1.json` contains only source-scoped unit
conversions: million AUD to base units, percentages to fractions and dimensionless
EAD ratios unchanged. Canonical financial equivalence and uncertain conventions
are not invented. Parent integration owns release inclusion and persisted proof.

Independent source-authored goldens cover all 90 cells and the distinguishing
metadata. The complete source test was observed failing before implementation,
then green. No runtime validation or shared-file changes were introduced.

Task 4 migration, 2026-10-14: source tests first failed on the old v3 return format,
then passed through v4 with the independent golden JSON unchanged. Extended
assertions cover actual header fragments, required note presence, qualification
targets, complete source identities and the unresolved dates of the retained
12-month PD outcome window. The NAB joint-vintage publication test owns
catalogue/address separation after saved-Bronze conformance.
