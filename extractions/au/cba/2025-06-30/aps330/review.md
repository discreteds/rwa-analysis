# CBA 30 June 2025 — mortgage CR6/CR9 source review

Reviewed 2026-10-10 with the PDF skill, directly against the
[saved disclosure](../../../../../raw/cba-2025-06-30-aps330.pdf).

## Selected source and geometry

PDF page 55 (printed 55), `CR6: IRB – Credit risk exposures by portfolio and PD
range`, `Subject to AIRB approach`, `Residential mortgage`, `30 June 2025`.
The page was rendered at 140 dpi and visually scrutinised before authoring the
golden or implementing the extractor. It is landscape, 841.92 × 595.32 PDF points.

The selected block starts at y≈172 and ends with its subtotal at y≈269; the next
portfolio starts at y≈280. PD labels start at x≈168. Twelve independent financial
windows use the inspected header gutters at x=232, 280, 325, 370, 416, 458, 506,
550, 595, 638, 682, 724, 770. Headers occupy y=110–154, units y=157–167, and notes
y=507–533. The extractor reads each window independently, deriving row positions
from PD-label tokens. These constants are local to this disclosure.

Seven non-default intervals, one default category, and one `Sub-total` contain
108 selected field positions. All nine maturity cells are visibly blank; band
provisions are blank in eight rows, with provisions disclosed only on the
subtotal. The maturity meaning is unresolved. Provisions are not disclosed at
band grain. Neither is interpreted as zero. The default category is categorical,
not an interval with invented bounds.

The subtotal is a source total over the disjoint displayed PD partition. This
relationship supports selecting the appropriate level without double-counting;
it does not prescribe summing means or require exact reconciliation of rounded
amounts. No data outside the mortgage block is included as an observation.

## Context and definitions inspected

- Cover p. 1: title, Commonwealth Bank of Australia, 30 June 2025. Release p. 2:
  13 August 2025 publication date.
- Introduction p. 6 and framework p. 8: CBA and subsidiaries, APRA APS 330,
  regulatory methodologies. Scope p. 9 describes Level 1/2/3 and ASB/RBNZ.
- Glossary p. 115 explicitly says the report is produced on the Level 2 basis:
  consolidated banking group excluding insurance and certain securitisation
  entities. This evidence is captured as `level-2`.
- Overview p. 18 separately displays AIRB and RBNZ-regulated exposures. It notes
  a self-imposed mortgage risk-weight floor. Its numerical similarity does not
  independently prove a CR6 cell's scope or justify allocating that floor across
  CR6 bands. CR6's own overlay footnote is the captured field qualification.
- IRB introduction p. 49 and PD methodology pp. 50–51: one-year PD horizon,
  long-run estimates, retail pools and regulatory floors. Risk-rated/non-retail
  masterscale descriptions are not assigned to this mortgage PD segmentation.
- Page 52: LGD loss/cost basis and downturn treatment; EAD for performing versus
  defaulted facilities; outstanding plus undrawn × CCF; regulatory EL's different
  rules for non-defaulted and defaulted exposures. The relevant passages are
  retained as source qualifications, including the conditional BEEL statement.
- Page 53 describes other internal uses. Page 54 introduces CR6 as capital
  parameters broken down by asset class and PD range.
- Glossary pp. 114–117 was reviewed, including AIRB, EAD, Group, Level 2, LGD,
  PD, Residential Mortgage and RWA. The mortgage definition is captured; the
  glossary does not establish an exact borrower counting convention.
- Page 55 notes: (1) average PD uses period-end EAD, (2) RWA includes overlays,
  (3) RWA density uses unrounded numbers. Each is retained and bound to its field.

## Retained limitations

Currency code and the precise geographical perimeter of this selected block
remain unresolved. `$M` establishes the million-dollar display scale, not AUD by
itself. Reporting jurisdiction `au` is not exposure geography. CBA's exact counted
entity/distinctness convention remains unresolved; `Number of borrowers` is
preserved without equating it to agreements. The average CCF, LGD and maturity
weighting conventions are unresolved. A known PD weighting convention does not
propagate to adjacent measures. These are usable partial semantics.

## Contract and verification

[Golden notes](../../../../../tests/bronze/au/cba/2025-06-30/aps330/golden-notes.md)
record independent authoring. The golden was completed before production code,
from the rendered page and reviewed prose. It covers all values and metadata,
not merely numerical anchors. No scratch JSON or extractor output authored it.

Source prose line wrapping is collapsed and broken words rejoined. Header line
breaks and superscript note markers are preserved. Source references use one-based
PDF/printed pages and table, row, column or passage locations. Structured
qualification scopes name applicable fields and, where specified, a row; a
field+row scope restricts that field to that row, with source conditional wording
retained. Subtotal EL retains both conditional definitions.

Run `uv run pytest tests/bronze/au/cba/2025-06-30/aps330 -q` from the project.
Tests discover the project root by ancestors, so collection does not depend on
the process working directory. [Extractor](extract.py) returns the typed source
bundle; it does not read the golden or create persisted Bronze output versions.

## CR9 extension — reviewed 2026-10-12

Reviewed PDF/printed p.60, its introduction and both footnotes against a rendered
page before authoring `golden-cr9.json`. Re-read PD methodology pp.49–52 and the
glossary pp.114–117. This extends the same logical bundle with a CR9 dataset using
`disclosure-v2`; the CR6 golden and existing retained Bronze versions are preserved.

The selected `Residential mortgage` block is under `Subject to AIRB approach`.
Eight rows have seven numeric positions, plus S&P and `Moodys` rating equivalents.
The first row reports PDs 0.07/0.07%, counts 718,884/730,204, non-performing 1,045,
new non-performing 28, historical rate 0.07%. The default row retains PDs 100.00%,
counts 14,145/16,296, S&P `D` and Moodys `Ca to C`, with three visibly blank cells.
The 10–100% band's new-non-performing cell is an en dash, not zero or a blank.
No mortgage subtotal is published here.

Page-60 PDF gutters are x=400/450/506/560/617/673/730/777 for numeric columns;
rating columns occupy x=275–340 and 340–400. Headers occupy y=132–173, unit labels
y=176–185. Mortgage PD-label starts are x≈199.8, y≈365.6–433.9. Existing CBA
`window` and `source_passage` helpers serve this layout without new shared helpers.

### Meaning and time

- The introduction specifies a 12-month computation from **1 April 2024 to
  31 March 2025**, excluding RWA overlays and risk floors. This is distinct from
  the June document date and August publication. `End of previous year` and
  `End of the year` are interpreted with that explicit annual context as
  31 March 2024 and 31 March 2025; both header and introduction remain evidence.
- Footnote 1 maps internal PD grade **midpoints** to the fixed disclosure ranges.
  It is captured as a dataset/band qualification, not a rating-assignment date.
- Footnote 2 uses data **from 2014**, with asset class determined by regulatory
  standards applicable at the time. History starts at year precision `2014`;
  its end and duration remain unresolved. No January date or March history end
  is inferred from the annual window.
- CR9 does not establish the weighted-PD weight measure or its measurement date.
  The CR6 period-end-EAD weighting note does not apply here. Arithmetic PD is
  explicitly by borrowers, but the exact counted entity and distinctness remain
  unresolved. PD measurement and weight timing have unresolved descriptors;
  cohort and rating anchors are not manufactured.
- Glossary p.116 defines non-performing as an exposure in default. Retail
  methodology p.51 gives 90 days or more past due or unlikeliness to pay. Both
  passages qualify the non-performing count fields. They do not establish CR9
  repeated-event, cure/exit, opening-cohort or exact counting rules.
- `of which: new non-performing borrowers in the year` establishes a subset of
  the adjacent non-performing count in each non-default row. Seven row-scoped
  field relationships preserve it, including the dash cell. “New” does not
  establish Westpac's new-funding convention. No relationship is manufactured
  between the three blank default-row cells.
- Level 2/reporting entity and mortgage-definition evidence remains applicable;
  geography and currency stay unresolved. The external-rating labels preserve
  the table's exact spelling and association, without assigning non-retail
  masterscale rules to mortgage pools.

### Catalogue handoff

Bank-specific members are in `catalogue/measures/cba-cr9-2025-06-30-v1.json`
and `catalogue/mappings/cba-cr9-2025-06-30-v1.json`. Seven measure definitions reuse
the existing PD, reported-borrower-count and historical-annual-default-rate
concepts. Seven exact-document field mappings establish percent/count conversions;
one context mapping supplies the mortgage population, source band role and overlay
treatment. No date-restricted definition or canonical forward-cohort equivalence
is asserted. Shared release selection is owned by the integrating session.
