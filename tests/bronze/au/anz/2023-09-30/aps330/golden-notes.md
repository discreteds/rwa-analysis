# Independent ANZ September 2023 expectations

Authored from PDF pp.52–54 and 56 and reviewed definitions on pp.4–5,
27,29–30,45–48,96, before implementing the extractor. Rendered pp.45,52,54,56
confirm the pre/post reform columns, merged bands and retail/wholesale scope.
All 125 mortgage tokens are explicitly transcribed in `golden.json`.

Credible regressions: selecting mixed NZ retail; confusing repeated mortgage rows;
dropping comparative panels or trailing precision; applying the 2024 dates or a
single shared PD/EAD history window; treating the Sep-2022 comparative as restated;
assigning its old Level-2 parent to current panels or vice versa; losing subset edges.
The complete-source test owns these source-specific contracts. Existing 2024 tests
do not exercise this PDF. No test-only production API is required.

No blank/dash occurs in the selected cells. Bands do not explicitly state lower
inclusivity. Total columns do not imply additive aggregation of percentages or
averages. Undrawn commitments are explicitly included in exposure. The average-EAD
denominator is unresolved; Table 7's half-year average definition does not apply.

Retail PD history is 2018–2022; actual PD cutoff September 2023. Retail EAD history
is independently 2018–2023. LGD history is 2017–2021, with defaults after September
2022 excluded. These are source statements, not corrected or aligned windows.
The wholesale historical-LGD review sentence remains unscoped with unresolved
mortgage applicability. Geographic scope remains unresolved rather than equating
the report jurisdiction with exposure geography.

Independent review correction: the p.45 image
`/tmp/opencode/anz-2023-reform-review.png` establishes complete column reading
order. The two matrix qualifications retain section headings and all four column
headings with their own cell text. In particular, the NZ pre-January rating cell
is blank; “AIRB and Supervisory Slotting” belongs only to the post-January column.
The earlier flattened text interleaved columns and omitted their headings. These
golden strings were corrected from the image first; the existing source test then
failed on `regulatory-basis` before the matrix extraction was repaired.
