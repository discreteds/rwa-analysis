# Independent Westpac expectations

Authored 2026-10-10 directly from the saved September 2025 PDF, before the
Westpac extractor. Visually inspected rendered pp. 48–49 at 150 dpi and the
portfolio/program-managed/glossary definitions on pp. 33, 47 and 98. Read report
conventions p. 2, Level 2 p. 8, default p. 34, provisioning p. 44 and regulatory
EL p. 97 directly. The ignored `author-westpac-golden.py` aid expands independently
transcribed tokens and prose into JSON using only stdlib; it reads no PDF,
production module, scratch records, existing golden or extractor output.

All 108 positions are retained: 90 present, 17 blank and one dash. The nine
maturity windows are blank and shaded, including the total; absent meaning stays
unresolved. Eight band provisions are blank/shaded; provisions are disclosed only
at total grain. Default CCF is `-`, retained as `dash_unresolved`, not zero. All
present rate tokens retain `%`; PD precision is two, other present values zero.
The fourth-band `101%` and seventh-band `104%` CCFs are source values.

The centred two-line `Residential / Mortgages` heading spans the full block:
three rows sit above its first line. The first row has EAD `201,511`, PD `0.08%`
and count `578,226`. Total EAD/RWA/provisions are `569,920`/`116,433`/`1,347`.
The eight bands comprise seven non-overlapping printed intervals and a separate
default category; the ninth row is `Total Residential Mortgages`. The source
total relationship covers the displayed block, not additive percentage semantics.

Context preserves September 30 independently from CBA's June 30. The cover states
September 2025, the table supplies the day. Publication date `2025-11-03` and URL
are acquisition metadata from `raw/index.md`, not claims printed on the cover.
Cover `printed_page` is the empty string because no page label is printed;
PDF position remains 1. Other inspected PDF/printed page numbers agree.

Report conventions explicitly establish AUD and APRA Basel III; p. 8 establishes
Level 2. The block is A-IRB, with RBNZ exposures separately labelled elsewhere.
Exact exposure geography remains unresolved. Source headers retain line breaks
and the density footnote marker `a`; monetary units inherit `$m`, while rates,
maturity and count have their field-specific units. No currency is inferred from
the folder. Prose line wraps become spaces, but source wording is retained.

All four average-field weighting conventions and the counted entity remain
unresolved. The CR9 June-2024 PD/EAD weighting note does not establish CR6
weighting. The p. 98 funding/liquidity Maturity definition is also inapplicable.
Program-managed PD/LGD definitions apply to mortgages per p. 47's model table.
Regulatory EL is kept distinct from provisioning/ECL; p. 97 supplies its IRB
scope and default/non-default comparison qualification, not a complete formula.

Test-audit gate: the complete real runner/codec/golden boundary protects lost
rows, shifted columns, changed dates/units, lost tokens and unsupported semantics.
CBA's test cannot detect Westpac geometry or qualifications. No production test
seam or duplicate anchor-only test is introduced. Expected metadata receives the
same complete comparison as financial cells.

## CR9 independent expectations — 2026-10-12

`golden-cr9.json` is the independently transcribed companion to the unchanged
CR6 `golden.json`. Authored from pp. 55–56 and a rendered p. 55 before adding
the CR9 extractor. It contains all 56 measure tokens, all 16 rating positions,
the seven full headers, eight bands and applicable table notes. The separate
test-support expansion specifies all source dataclass members: context, axes,
fields, bindings, segmentation, source qualifications, field-level subsets,
temporal descriptors and all 64 temporal bindings. It does not read the PDF,
extractor constants, extracted values or the disposable spike. Existing
independent CR6 expectations supply only unchanged common source quotations
and provenance; their scopes are explicitly restated for CR9.

There are 52 present values, three blanks, and one dash. Count values are
integers, rates retain two displayed decimal places and percent tokens. Blank
default-event/history cells remain distinct from the seventh band's dash.
The two ratings retain their agency and row even when blank. There is no
synthetic total. The source's `of which` relationship is retained for each
non-default row, scoped to that row and addressed by measure field endpoints.

June-2024 PD/weight timing keeps month precision. Annual dates come from the
introduction; end-of-year count dates are interpreted in that stated year.
History has a known ten-year duration and unknown endpoints; arithmetic-PD
measurement remains explicitly unknown. The synthetic transport test separately
checks a year-only start and fractional duration, and does not claim those
values were disclosed by Westpac.
