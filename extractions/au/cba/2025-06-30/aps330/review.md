# CBA 30 June 2025 — mortgage CR6 source review

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
