# Independent CBA expectations

Authored 2026-10-10 directly from `raw/cba-2025-06-30-aps330.pdf`, before the
contract, codec or extractor existed. Page 55 was rendered at 140 dpi and visually
read, including all twelve columns, nine rows and three notes. The financial
tokens were manually transcribed; neither extractor output nor scratch JSON was
used. An ignored authoring aid expanded this independent transcription into the
complete JSON contract; it imports no production code.

All 108 field positions are selected: 91 present and 17 blank. Nine maturity
cells are blank (meaning unresolved); eight provisions cells are blank while the
subtotal discloses provisions (not disclosed at band grain). These are not dashes
or zeroes. PD has two decimal places, every other present number has zero.
The count is integral, with the exact counted entity unresolved.

Seven non-default intervals have inclusive lower/exclusive upper bounds, followed
by the distinct `100.00 (Default)` category. The final `Sub-total` aggregates the
displayed mortgage block. The printed ranges establish a disjoint, covering
partition, but this does not assert additivity of percentages or maturity. Bounds
of the default category are not applicable, rather than zero or unbounded.

Reviewed context: cover and release p. 1–2, introduction p. 6, capital framework
p. 8, scope p. 9, AIRB/other approach overview p. 18, IRB definitions pp. 49–53,
CR6 introduction p. 54, and glossary pp. 114–117. The glossary p. 115 explicitly
establishes the report's Level 2 basis. The table says AIRB and Residential
mortgage. The evidence reviewed does not explicitly establish a currency code or
precise geographic perimeter for this block: both remain unresolved. `$M` still
establishes the displayed million-dollar scale. Do not infer AUD from `au/`.

Definitions and qualifications preserve source wording. Multiline column headers
retain line breaks and superscript note markers; prose line wrapping is collapsed
to spaces and a word broken across a line is rejoined. Footnote numbers live in
their location references. PD weighting is established separately from unknown
CCF/LGD/maturity averaging conventions. EL qualifications retain their conditional
non-default/default applicability in the source text; default-row scope is also
recorded for BEEL. No assumption equates CBA borrowers to NAB agreements.

The complete JSON includes context, every axis/field/binding, all bands,
qualifications, aggregate relationships and per-cell references. No keys are
ignored by the comparator. Future corrections require rereading source evidence
and recording the rationale here.
