# NAB September 2023 mortgage source review

## Reviewed evidence and selection

Official source: `raw/nab-2023-09-30-aps330.pdf`, Full Year Pillar 3 Report 2023.
Reviewed extracted text and rendered PDF pp.40–42, 50–51 (printed pages two lower).
Definitions/perimeter review covered introduction p.4, default p.23, historical
framework p.38, internal ratings pp.45–47 and glossary pp.76–77.

One PDF yields one `disclosure-v4` captured bundle with eight separately dated datasets:

| Source | Dates | Selected body cells |
|---|---|---:|
| Table 5.3.B, pp.50–51 | September 2023, March 2023 | 60 |
| Table 5.1.J (ii), pp.40–41 | September 2023, March 2023, September 2022 | 18 |
| Table 5.1.J (iii), pp.41–42 | Same three dates | 12 |

Exposure selection is all five main residential-mortgage metrics across six native
PD bands. Main and explicitly labelled RBNZ residential mortgages are both selected
in backtesting, with separate row/header paths. Mixed RBNZ retail exposure totals,
other asset classes and separate loss-experience Table 5.1.J (i) are outside selection.
No portfolio total or additional numeric note is manufactured.

## Context and semantics

The report is NAB and controlled entities, Level 2, AUD unless otherwise stated;
this does not establish Australian exposure geography. Backtesting's p.38 perimeter
and historical-framework paragraphs are retained verbatim. They describe pre-revised
capital-framework asset classes and separately disclosed RBNZ significant classes.
No aggregate/subset relationship between main and RBNZ mortgage rows is inferred.

Exposure blocks use advanced IRB. Native PD intervals retain unresolved lower-end
inclusivity; 100% is the default category, supported by the p.23 default definition.
EAD includes principal, fees and interest, model stresses, retail scaling/CCF context,
and the glossary's net-of-eligible-financial-collateral convention. Average EAD is
money per arrangement, explicitly a simple average, not an arrangement count.
LGD retains downturn modelling, cure/recovery and LMI treatment and the p.47 10%
RWA supervisory floor. Exposure-weighted risk weights exclude regulatory methodology
overlays. Undrawn is a subset of exposure within each band, not an additive metric.

## Differences from FY24 that require bespoke handling

- March 2023 undrawn commitments explicitly restated (p.51 note 3); only that field
  and its cells receive this qualification. p.51 note 1 restates mixed RBNZ retail
  presentation, outside the selected mortgage exposure rows.
- Exposure footnote numbering is 1/2/3 in September versus 2+3/4/5 in March.
  There is no FY24 PD-model-change note in this source.
- September backtesting headings say **IRB approach**; March and prior September
  say **advanced IRB approach**. These source labels survive unchanged.
- FY23 PD prose specifies a non-default opening cohort and ten-year averaging,
  without the FY24 paragraph's 12-month outcome wording. No outcome binding is
  inferred from the general PD model horizon. Exact history boundaries are unknown.
- EAD compares opening non-default customers with EAD at default; no historical
  averaging duration is stated. Actual LGD uses net write-offs over ten years to
  reporting date, excluding the latest two years for mortgages. Estimated LGD is
  at beginning of year, exact date unresolved. APRA floors and RBNZ prescription
  are cell-scoped to their own estimated-LGD rows.
- Default evidence is p.23, not a copied FY24 glossary definition. Framework
  transition and RBNZ materiality evidence is p.38, not FY24 wording.

## Metadata-owned capture

`definition.py` declares this vintage's selection, physical parameters, source-table
templates, contexts and occurrence bindings. `physical.py` reads rows, bands,
column headers and cropped definition passages, alongside the shared paragraph
reader. The thin `extract.py` invokes `run_capture`; shared capture owns numeric
parsing and comment materialisation. No dated extractor supplies definitions.

The snapshot preserves all table, axis, field, cell and comment addresses. Shared
methodology paragraphs have one physical occurrence with explicit qualification
links; separately printed floor notes retain their individual panel occurrences.
Exposure headers are selected after their panel date. Backtesting headers use
reviewed column boundaries between the panel date and exposure-type line, avoiding
interleaved text. The glossary's EaD definition and the mortgage definition use
cropped columns rather than copied prose.

Thirteen conversion mappings use exact document/panel/template/portfolio scopes,
with `nab-fy23-` identities to distinguish FY24's repeated September 2023 panels.
They reuse the established million/percent/ratio conversion convention. Source
attributes retain arrangement and overlay evidence; no new canonical measure
equivalence is asserted from similar labels alone.

## Verification

Independent source transcription preceded implementation. The focused golden test
first failed because the FY23 extractor was absent, then passed against the real
PDF: eight datasets, 90 body cells, exact tokens/precision, field units, native axes,
restatement scope, APRA/RBNZ qualifiers and per-cell timing.

Task 4 migration, 2026-10-14: source tests first failed on the old v3 return format,
then passed through v4 with the independent golden JSON unchanged. The tests also
check captured headers, explicit comment targets, full source identity, retained
temporal roles and distinct repeated floor comments. The NAB joint-vintage
publication test owns catalogue/address separation after saved-Bronze conformance.
