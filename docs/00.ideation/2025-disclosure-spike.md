# 2025 disclosure availability spike: CBA and Westpac

Follow-up: [NAB/ANZ metadata discovery](2025-nab-anz-metadata-spike.md) expands the source sample to all four major banks and identifies additional counting, overlay, scope and segmentation differences.

## Outcome

Downloaded eight official Pillar 3 PDFs covering all four 2025 reporting dates for CBA and Westpac. Saved sources and URLs are catalogued in [`raw/index.md`](../../raw/index.md).

Four documents contain the detailed mortgage PD-band tables needed for the initial research:

| Bank | Reporting date | Mortgage CR6 PDF page | Additional useful tables |
|---|---|---|---|
| CBA | 2025-06-30 | 55 | Portfolio summary p. 18; CMS2 p. 20; CR9 p. 60 |
| CBA | 2025-12-31 | 40 | Portfolio summary p. 16; CMS2 p. 19; June comparative CR6 p. 45 |
| Westpac | 2025-03-31 | 25 | CMS2 p. 17 |
| Westpac | 2025-09-30 | 48 | Portfolio summary p. 16; CMS2 p. 19; March comparative CR6 p. 50; CR9 p. 55 |

The other four PDFs provide quarterly summary information but no CR6 table was found. CBA September and Westpac June/December include mortgage EAD and RWA totals, making them useful for reported-RWA coverage even without a PD distribution.

## How the sources were inspected

Used the official bank archive pages to discover the downloads. For this spike, Poppler `pdftotext -layout` provided page-by-page text for inspection. Rendered and visually inspected CBA June p. 55 and Westpac September p. 48 to check the table geometry, headers and blank cells against the text. Inspected the other two detailed mortgage tables in layout-preserving text, together with relevant surrounding definitions and footnotes.

Temporary text and rendered images are in `/tmp/opencode/rwa-2025-spike/`. These are exploratory artifacts, not production extraction outputs. No bespoke extractor, golden set or Bronze dataset has been built.

## 1. The reporting dates do not align

CBA's detailed mortgage disclosures are June and December. Westpac's are March and September. There is therefore no same-reporting-date pair of detailed mortgage CR6 distributions among these eight PDFs.

A cross-bank pilot can use CBA June and Westpac September to exercise both layouts, while explicitly preserving their three-month date difference. They should not be described as a same-date comparison. For within-bank evolution, CBA June/December and Westpac March/September give genuine six-month intervals.

The December 2025 CBA report was published in February 2026 and titled as a 2026 half-year disclosure. Searching only archive sections or filenames labelled “2025” would miss it and could instead select the December 2024 report.

## 2. CR6 provides a useful common starting schema

Both banks disclose the same seven non-default PD ranges, expressed in percent:

```text
0.00 to <0.15
0.15 to <0.25
0.25 to <0.50
0.50 to <0.75
0.75 to <2.50
2.50 to <10.00
10.00 to <100.00
100.00 (Default)
Portfolio total / subtotal
```

Each mortgage block therefore supplies eight band rows plus a total. Four primary documents would give 36 initial mortgage records if this is the chosen scope. Comparative repeats are separate evidence for existing bank-period observations, not additional exposures.

Available columns:

- Original on-balance-sheet gross exposure ($m).
- Off-balance-sheet exposure before CCF ($m).
- Average credit conversion factor (%).
- EAD after CRM and CCF ($m).
- Average PD (%).
- Number of borrowers.
- Average LGD (%).
- Average maturity (years): blank for these mortgage rows.
- RWA ($m).
- RWA density (%).
- Regulatory expected loss ($m).
- Provisions ($m): shown at mortgage-total level, not separately for each band.

CBA explicitly states that average PD uses period-end EAD. Westpac labels its CR6 column “Average PD”; the inspected CR6 text does not separately spell out its weighting convention. Confirm the applicable CR6 definition when establishing the Silver metric contract rather than borrowing the weighting definition from Westpac's different CR9 table.

### Selected published totals

These are transcribed availability notes, not final golden fixtures. Values include the default row.

| Bank/date | EAD ($m) | Average PD (%) | Average LGD (%) | RWA ($m) | Printed RWA density (%) |
|---|---:|---:|---:|---:|---:|
| CBA June 2025 | 691,020 | 1.47 | 16 | 149,143 | 22 |
| CBA December 2025 | 720,249 | 1.40 | 16 | 154,941 | 22 |
| Westpac March 2025 | 558,279 | 1.89 | 15 | 116,954 | 21 |
| Westpac September 2025 | 569,920 | 1.74 | 15 | 116,433 | 20 |

For non-default PDB, recompute the exposure-weighted mean using only the seven non-default rows. Do not use these default-inclusive total PDs directly as the non-default benchmark.

## 3. Footnotes materially affect interpretation

### CBA mortgage RWA overlays

CBA June p. 55 says CR6 RWA includes overlays. The portfolio summary on p. 18 identifies a $2.4 billion self-imposed residential mortgage risk-weight floor. The September quarterly summary identifies a $5.2 billion floor. December pp. 15–16 identify an $8.0 billion RWA overlay relating to the Australian Residential Mortgage PD model; its CR6 table also says RWA includes overlays.

Preserve the bank's exact descriptions and dates. These are RWA amounts, not percentage-point floors or capital amounts. Do not assume how a portfolio overlay is allocated across bands or mechanically remove it from individual rows.

This is directly relevant to the research: a difference between reported RWA and a standardised PD/LGD calculation cannot automatically be attributed to PD dispersion.

### Regulatory scope

The banks report RBNZ-regulated exposures separately. CBA's June portfolio summary has a separate RBNZ line; Westpac September p. 33 explicitly describes separate New Zealand classification. Keep the mortgage CR6 portfolio distinct from the RBNZ retail block and standardised mortgage exposures. A group-level disclosure is not evidence that every table includes all of the group's mortgages.

### Rounding and blank cells

Both banks state RWA density is calculated from unrounded values. Published amounts and ratios have different precisions. Rounded RWA/EAD need not reproduce printed density exactly, and displayed band amounts can differ slightly from totals when summed.

Empty maturity and band-provision cells are not zeros. Westpac also displays dashes, including the default-row CCF; retain that original representation until its meaning is established. Some non-default CCFs exceed 100%, so a universal CCF <= 100 validation rule would reject disclosed data.

## 4. A natural golden-set expansion is available: CR9

The annual reports disclose mortgage PD backtesting data:

- **CBA June p. 60:** weighted PD, borrower-arithmetic PD, beginning/end borrower counts, non-performing borrower counts, new non-performing borrowers and historical average default rates. Its stated performance window is 1 April 2024–31 March 2025.
- **Westpac September p. 55**, with footnotes on subsequent CR9 pages: corresponding backtesting fields, with a performance window of 1 July 2024–30 June 2025. Footnotes specify June 2024 PD/EAD for the weighted PD observation point.

CR9 can extend the golden sets later to explore calibration questions. It needs separate observation/performance dates and weighting definitions. It cannot be joined to reporting-date CR6 rows as though both describe the same current portfolio cohort.

## 5. Extraction implications

1. **Document-specific selection is justified.** CBA's mortgage page moves from 55 to 40 between June and December; Westpac's moves from 25 to 48 between March and September.
2. **The logical row structure is similar despite different layouts.** CBA places the mortgage label at the start of its block; Westpac uses a vertically centred, split label. A line parser searching for the label would miss early Westpac mortgage rows.
3. **Headers are multi-line.** CBA puts percentage units in headers; Westpac also uses percent signs in cells. Preserve units explicitly.
4. **There are multiple portfolios on the same page.** Extract the intended block, not every numeric line.
5. **Footnotes can be on another page.** Westpac September's CR6 density footnote appears on p. 49, following the mortgage table.
6. **Comparatives appear later in subsequent documents.** CBA December repeats June on p. 45; Westpac September repeats March on p. 50. The table's date must be stored separately from the document reporting date.
7. **Text is available.** These inspected tables are digitally readable; OCR is not needed for the pilot. Layout-preserving text or coordinate-aware PDF tooling are plausible options to evaluate when authoring each bespoke extractor.

## 6. Recommendation for the next brainstorming step

Start golden-set authoring with **CBA June 2025 p. 55 and Westpac September 2025 p. 48**, retaining all CR6 mortgage columns, the eight band rows, total, units and relevant footnotes. Use those two documents to shape minimal dataclasses for source references, reporting context, band definitions, mortgage observations and totals.

Then extend to the other half-year in each bank's cycle and the comparative repeats. This tests both catalogue growth and reuse without assuming a bank-wide layout stays fixed.

The agreed initial scope is the full mortgage CR6 block, including the reporting-context and segmentation metadata. Golden sets must include organisation/reporting entity, document and table dates, portfolio scope, band labels/order, lower and upper bounds, inclusivity, units, default classification and band counts, alongside all selected values and footnotes. The inspected blocks have seven non-default bands, one default bucket and a total/subtotal; that structure is a per-table expectation, not a permanent bank-level assumption. CMS2, capital totals and CR9 are natural subsequent golden-set extensions.

Both bank archives also publish quantitative spreadsheets. They are an available additional source for future cross-checking, but were not inspected during this PDF spike.
