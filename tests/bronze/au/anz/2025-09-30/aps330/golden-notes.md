# ANZ September 2025 independent source contract

## Adjustment extension — 2026-10-17

`golden-adjustments.json` independently transcribes p.19's mortgage overlay, full
six-position overview row and group output floor, plus all six dated RWA/capital
amounts in p.17 footnote 3. Rendered p.19 confirms footnote 2 belongs to the AIRB
mortgage row. CCR dashes remain missing. The approved aggregate CR6 applicability
is a researcher decision, separately tested through persisted metadata; it does
not change the original source golden or establish a band allocation. See the
[source review](../../../../../../extractions/au/anz/2025-09-30/aps330/review.md).

Authored before the bespoke extractor, from direct rendered inspection of PDF /
printed pp. 57, 6, 23 and 116, supported by source text on pp. 1, 7, 36, 54 and 60.
All nine rows and twelve field positions were manually transcribed; no extractor
output, another bank's golden, shared numeric parser or production codec generated
the expectations. A temporary, production-independent authoring script expanded
the reviewed literals into the complete JSON wire schema.

The test owns the real PDF-to-bundle contract. Credible regressions include
selecting March or NZ rows, losing source row numbers, shifting the blank
provisions column, treating maturity dashes as unexplained or zero, substituting
the parent reporting entity, or asserting mortgage agreement counts / CR6 overlay
inclusion without evidence. Existing three-bank tests cannot detect those ANZ
errors. No test-only production interface is needed.

## Coverage

- PDF p. 57: source rows **10–18**, AIRB Residential Mortgages, **Sep 25**.
- Seven intervals, the `100.00 (Default)` category, and
  `Sub-Total AIRB Residential Mortgages`. Local IDs retain source numbers through
  every row / cell reference. Column IDs are local positions, not printed letters.
- **108 positions: 91 present, 9 maturity dashes, 8 blank band provisions**.
  Maturity is `not_applicable` to the reported retail RWA calculation (footnote 2);
  provisions are `not_disclosed_at_this_grain`, based on the visually blank band
  cells and sole subtotal disclosure. No broader provisioning policy is inferred.
- Amounts: AUD millions (p. 7), integral displayed precision; count: integer;
  average PD: two decimals; other reported percentages: whole percent.
- Self-review rendered the cover separately: PDF p. 1 has no printed page label.
  Corrected that evidence reference to an empty printed label from the image,
  then reran the contract red before fixing the extractor reference helper.
- Subtotal: on-balance **339,108**, off-balance **34,373**, EAD **373,535**,
  borrowers **921,055**, RWA **94,135**, EL **801**, provisions **841**.
  Default row: EAD **4,316**, PD **100.00%**, RWA **12,184**, density **282%**.

## Metadata decisions

ANZ BH Pty Ltd heads the Level 2 reporting group. ANZBGL is its ADI subsidiary;
ANZ Group Holdings Limited is the ultimate parent. Suncorp/Norfina is standardised
and expressly excluded from IRB-specific tables (p. 54). NZ is a separate
RBNZ-regulated CR6 block (p. 60, rows 84–92). The selected Australian AIRB label
does not establish exhaustive collateral geography: `Australia` is provisional.

Borrower counted entity and distinctness remain unresolved. Footnote 3 is not
NAB's mortgage agreement definition. Average weighting remains unresolved.

CMS2 Sep 25 footnote 2 on p. 23 states a **$3.1 billion PD-model overlay introduced
from the 30 June 2024 reporting period**. Preserve its cross-table scope and date.
CMS2 modelled mortgage RWA matches 94,135, but equality does not prove CR6's overlay
policy. Both RWA and density retain unresolved overlay treatment; no researcher
decision has been made. Appendix 1 p. 116 expressly removes retail average
maturity (BCBS column h), with an industry-practice / usefulness rationale;
CR6 footnote 2 separately supplies the non-use-in-RWA reason.

Structural subtotal membership follows the printed block, complete non-overlapping
PD intervals and distinct default category. It does not establish count additivity
or weighted-average formulas. No exact arithmetic reconciliation is required.

## CR9 independent extension — 2026-10-12

`golden-cr9.json` was manually authored from p. 66 text and its rendered page,
before implementing the CR9 extractor. The test first failed on the existing
CR6-only bundle version. It preserves the original CR6 golden verbatim by testing
the CR6 dataset through the retained `cr6-v1` representation.

CR9 scope is **63 measure positions** across source rows **11–18 and 20**:
**59 present, one dash, three blanks**, plus both agencies' nine rating positions.
All tokens, decimal precision, integer count types, row/column evidence, bands,
subtotal membership, `of which` relationships and field timing are checked. Default
ratings are the literal `Default`; subtotal rating cells are blank. The history
note's line-wrap `5- year` is retained as flattened source text, not rewritten.

The independent note expectations cover p. 66 footnotes 1–4. The review reads
p. 116's Corporates-only 2.5-year modification in context; mortgage duration stays
five years, with no invented endpoints. Annual count/PD anchors are unknown.
The subtotal's **0.62%** and first-band **0.08%** history are independent published
observations. The catalogue test loads the owned ANZ assets through a temporary
release and resolves actual extracted fields: it catches imported Westpac weights
or cohort rules, incorrect corporate history, dropped historical exclusions,
and lost band/aggregate semantic tags. It first failed on missing ANZ assets and
then on absent band mappings. Parent tests own persisted rate conversion.

These tests exercise the public extractor and semantic resolver with the real
PDF and independently authored expectations. No new production test seam or
runtime validation process is introduced.
