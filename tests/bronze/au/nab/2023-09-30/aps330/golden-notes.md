# NAB September 2023 independent expectations

Manually transcribed before implementation from PDF pp.40–42 and 50–51 (printed
38–40 and 48–49), with all five pages rendered and inspected. Reviewed introduction
p.4, framework/perimeter p.38, default definition p.23, internal ratings pp.45–47
and glossary pp.76–77. No extractor output supplies expected values.

The public extractor test owns 90 body cells in eight dated panels: 60 exposure
cells and 30 backtesting cells. Credible regressions are lost comparative panels,
main/RBNZ swaps, inherited 2024 definitions, incorrect note scope and a fabricated
PD outcome window. Existing 2024 tests cannot detect these source-specific errors.
The test uses the real extractor entrypoint without a test-only production seam.

March undrawn commitments bear both inclusion and restatement markers; the separate
RBNZ retail restatement does not apply to the selected main mortgage rows. No 2024
PD-model-change note applies. September backtesting headings say IRB, comparative
headings advanced IRB; exposure headings all say advanced IRB. Mixed RBNZ retail
exposure aggregates are excluded; explicit RBNZ mortgage backtesting is retained.

PD history is ten years, with exact bounds unspecified. Unlike 2024, the PD paragraph
does not state a 12-month outcome window; the general model's horizon is not an
outcome-window definition. EAD has relative beginning/default timing, not a stated
ten-year window. Actual LGD uses a ten-year history to reporting date and excludes
the latest two years for mortgages, without inventing adjusted exact boundaries.
Estimated LGD is at beginning of year, exact date unresolved. APRA floors attach
only to main estimated LGD, RBNZ prescription only to RBNZ estimated LGD. The p.47
10% RWA floor does not replace the backtesting note's unspecified floor level.

Final review added the full retail LGD/LMI/floor paragraph independently from p.47
and required applicable golden note IDs per panel. A mutation removing `retail-lgd`
now fails the existing source test; an intersection-only comparison had missed it.
