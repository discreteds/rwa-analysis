# 2023 historical mortgage capture

Date: 2026-10-13. Status: complete and verified; independent reviews and repairs
complete. Combined code/documentation PR #15 targets `develop`, pending merge.

## Approved continuation

Extend complete selected mortgage exposure and backtesting capture to CBA June 2023
and Westpac, NAB and ANZ September 2023. The researcher approved using the existing
source-table design and the base checkout seeded from `develop`. Code, independent
goldens, catalogue additions and documentation form one delivery.

The four official PDFs and page inventory are in the
[raw index](../../raw/index.md#prior-annual-reports--2023-discovery). The selected scope
includes all comparative panels and separately identified NAB RBNZ mortgage
backtesting. Separate loss-experience tables and mixed NZ retail aggregates remain
outside this mortgage selection.

## Why publication vintage matters

These reports straddle the January 2023 capital-framework change. A panel's measured
date and a report's publication vintage describe different things. Similar labels
and even identical values do not prove that the surrounding definitions remained
unchanged.

| Source | Concrete distinction requiring explicit metadata |
|---|---|
| CBA | June 2023 exposure notes state 1.10 scaling and a $7.4bn RWA overlay; December/June 2022 state 1.06, without that overlay note. Backtesting expressly uses prudential requirements preceding the revised framework. |
| Westpac | September 2022 has a lexical `N/A` default-PD position and a 25% mortgage risk-weight floor, removed from January 2023. The 2023 outstandings note differs from the 2024 wording. Supplementary RWA remains separate from body totals. |
| NAB | March 2023 undrawn commitments are expressly restated. Main and RBNZ mortgage backtesting rows retain different population and LGD-floor qualifications. The 2024 PD-cohort wording must not be copied backwards without evidence. |
| ANZ | Retail estimated-PD history is 2018–2022, EAD history 2018–2023, estimated-LGD history 2017–2021, with different actual-outcome cutoffs. Exposure comparatives span the reporting-entity and regulatory transition. |

The original 2023 panels and their later 2024 comparatives retain independent bundle,
table and cell identities. New catalogue mapping IDs also include publication vintage:
the older release already contains mappings for 2023 comparative observations. Reusing
those IDs for newly acquired original reports would conflate source occurrences.

## Reuse and bespoke interfaces

The existing `extract(pdf_path) -> ExtractionBundle` entrypoint and source-table
constructors are the extension interfaces. Shared parsing, composed metadata,
catalogue resolution, transport and persistence already serve these new sources.
The [architecture guide](../architecture.md#bespoke-extraction-and-shared-interfaces)
documents the responsibilities and explicit mapping override/correction mechanisms.

A separate read-only assessment compared the four existing 2024 extractors. Repeated
axis/value constructors are mostly argument assembly; a further reported-value helper
would save roughly 10–20 net lines across four consumers while still needing explicit
evidence and missingness. Similar transposed-table loops contain different bands,
qualifications, periods and relationship endpoints. No shared builder was justified
by that inspection. Source review, rather than a bank/year template, determines those
inputs.

Reusable meaning belongs in reviewed measure revisions, with occurrence-specific
evidence and scoped mappings. A common percentage conversion is not a declaration of
equal weighting, population or temporal meaning. Bespoke needs can directly construct
cells, non-body note observations, qualifiers and temporal bindings; they do not need
to subclass a template or override hidden defaults.

## Verification responsibilities

- Per-PDF independent goldens own full numeric, structural and metadata fidelity.
- Joint 2023/2024 publication cases own the distinct integration risk: repeated
  observed periods survive with separate source and mapping identities and correct
  conversions under one selected catalogue release.
- The existing historical example selects both report vintages for each organisation
  and the explicit Westpac 2025 view, retaining saved Bronze, staging, master and
  reconstructed frames. It is the full real-path checkpoint.
- Existing transport/master lifecycle tests continue to own reconstruction from
  persisted values, staging removal and replacement of selected inputs.

## Execution evidence

The joint-vintage regression cases initially fail because the four 2023 extractors
do not exist. Red run: `/tmp/opencode/historical-2023-vintages-red.log`.
All four joint-vintage cases now pass with the combined catalogue release. These
exercise original and comparative occurrences through saved Bronze and persisted
readback, with independent publication and mapping identities.

The first real persisted path passed for ANZ 2023 and 2024 together: 250 cells across
eight reconstructed datasets, through saved Bronze, staging and master. Retained
output: `/tmp/opencode/historical-2023-early-fut84bpo`; log:
`/tmp/opencode/historical-2023-early-persist.log`. This early run used the isolated
catalogue copy retained with the ANZ source proof; the final combined-release example
remains the delivery check.

The complete example subsequently passed using the tracked
`catalogue/releases/historical-mortgages-v2.json`. It selects all 123 earlier release
revisions and 46 new document-scoped conversion mappings. No old release or source
extractor was changed. Unknown canonical financial meanings remain explicit.

| New source | Dated datasets | Body cells | Numerical notes |
|---|---:|---:|---:|
| CBA June 2023 | 5 | 125 | 4 |
| Westpac September 2023 | 6 | 234 | 3 |
| NAB September 2023 | 8 | 90 | 0 |
| ANZ September 2023 | 4 | 125 | 0 |
| **Total new capture** | **23** | **574** | **7** |

Combined 2023/2024 and selected modern Westpac output: **48 datasets, 1,343 cells**
(1,328 body positions, 15 numerical notes), with nine existing CR6 rows and eight CR9
rows retained in their named outputs. All 48 source-oriented frames reconstructed.
Retained full run: `/tmp/opencode/historical-mortgages-_ii6y0tf/`;
log: `/tmp/opencode/historical-2023-full-example.log`.

The new source reviews document geometry and meaning independently:
[CBA](../../extractions/au/cba/2023-06-30/aps330/review.md),
[Westpac](../../extractions/au/westpac/2023-09-30/aps330/review.md),
[NAB](../../extractions/au/nab/2023-09-30/aps330/review.md),
[ANZ](../../extractions/au/anz/2023-09-30/aps330/review.md).

## Final review dispositions

Independent source-correctness and complexity reviews covered all four new sources,
the combined catalogue and example. Complexity cuts were applied before correctness
repairs. The first complete regression run passed **181 tests**; review then found
the following gaps beyond that evidence:

| Bucket | Finding | Disposition |
|---|---|---|
| Complexity cut | CBA context helper accepted an unused dataset ID | Removed the argument and its two call arguments; existing source golden passes. |
| Fix now | ANZ reform matrix evidence interleaved columns and omitted period headers | Repaired against the rendered source, retaining ordered cells and pre/post-January-2023 headers in the existing qualification interface. |
| Fix now | NAB golden intersection could ignore a dropped qualification | Require the expected applicable note IDs per panel before comparing text; independently add the retail LGD/LMI/floor paragraph. In-memory removal of `retail-lgd` now fails. |
| Fix now | Westpac source-document URL pointed at a 404 | Use the acquired official URL and assert it in the existing source golden. The assertion failed before repair and passes afterward. |
| Upstream-dependent | None identified | No dependency change or local workaround. |

Logs for the source-URL red run and missing-note mutation:
`/tmp/opencode/westpac-2023-url-red.log` and
`/tmp/opencode/nab-2023-qualification-mutation.log`.

The correctness reviewer rechecked all three repairs and closed the findings; three
focused source tests passed. ANZ's corrected independent golden failed before the
matrix repair; both its 2023 and 2024 source tests pass afterward.

The full example was rerun after the repairs and again produced 48 datasets and
1,343 cells. Use the corrected retained run:
`/tmp/opencode/historical-mortgages-k2fnepej/`, with log
`/tmp/opencode/historical-2023-final-example.log`. Readback confirms the corrected
pre/post-reform matrix headers in all eight ANZ qualification occurrences. The
earlier run above is pre-review evidence, not the preferred current result.

Final post-repair regression run: **181 passed** in 196.77 seconds, log
`/tmp/opencode/historical-2023-final-suite.log`. Ruff and staged diff checks passed;
135 documentation links/anchors were checked. The suite reports dependency
deprecation/type-normalization warnings; no test failures remain. No runtime
validation process was introduced.

### Specific semantic reuse opportunity

The CBA review identified two existing definitions worth considering for the June
2023 original-report occurrences: `measure.cba.historical.exposure-lgd@v1` and
`measure.cba.historical.rwa-overlay@v1`. Their FY24 comparative mappings already
refer to the same observed June 2023 panel. The FY23 source independently supplies
the weighted-LGD heading, LGD definitions and scoped overlay footnote.

The smallest enrichment would be two FY23-occurrence semantic mappings, each with
FY23 evidence, selected in a subsequent catalogue release; no new measure type or
extractor abstraction is needed. This is a semantic-review opportunity, not a capture
defect or an automatic cross-framework equivalence assertion. The current delivery
retains the source and conversion knowledge; do not extend the overlay treatment to
the 2022 panels, which have no such source note.
