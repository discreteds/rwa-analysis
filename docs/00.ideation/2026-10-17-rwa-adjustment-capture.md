# Four-bank 2025 RWA adjustment evidence

Status: capture design approved in conversation on 2026-10-17; implemented and
verified on `feature/rwa-adjustment-capture`, PR #20 targeting `develop`.

## Ask and agreed implementation

Capture, classify and store the identified adjustment amounts and supporting totals
so that mortgage comparisons can explicitly include or exclude them. Extend the
existing source bundles with numerical-note observations and source total rows;
use ordinary Bronze, source-table Silver, staging and master storage. No new storage
schema or adjustment engine is needed. The existing CBA historical numerical-note
capture establishes the implementation pattern.

The researcher approved this bounded design and a worktree seeded from `develop`.
The supplementary dataset name `rwa-adjustments` identifies our selection of source
occurrences; it is not the title of a table published by a bank. Its table-body cells
retain separate rows/columns; note amounts are independently queryable cells linked
to the full source comment. The classification is stored as `qualification_meaning`,
quantity type as the canonical concept, and population as the field's `portfolio`
attribute. Measurement dates, source precision, units and scales remain separate.

## Source evidence and independent expectations

The saved official PDFs were searched in full for overlay/floor references, then
the selected pages and their local notes were inspected. CBA p.18, ANZ p.19 and NAB
PDF p.13 were also rendered to verify row/footnote association. The new per-source
`golden-adjustments.json` files were transcribed from this source evidence, not
generated from the extraction definitions or outputs. Each entry records original
token, scale, PDF page, classification and observation date. Existing CR6/CR9
goldens remain authoritative for the original selected domain content.

| Source | Selected observations | Interpretation |
|---|---|---|
| CBA June 2025 p.18 | $2.4bn floor; all eight cells in the AIRB mortgage overview row, including December comparatives and percentage shares | Self-imposed mortgage RWA floor, included in overview $149,143m and CR6 subtotal. No band allocation. Currency remains unresolved in captured evidence. |
| ANZ September 2025 p.19 | $3.1bn PD overlay; all six cells in AIRB mortgage overview row; $3,499m group floor | Footnote 2 explicitly qualifies the overview mortgage total. Introduced from June 2024; introduction date is distinct from current measurement date. |
| ANZ p.17 note 3 | $12.5bn RWA and $1bn capital at September and June; $9.4bn RWA and $750m capital at March | Operational risk, Level 1 and Level 2; six dated observations, not additive components. Capital and RWA are different concepts. |
| NAB PDF p.13 / printed 11 | $4.8bn credit overlay; $2.3bn RBNZ and $2.1bn AIRB corporate components; all six cells in mortgage overview row; $2,284m group floor | Components are subsets, not an exhaustive partition. The credit overlay is not wholly mortgage-related. CCR dashes remain missing, not manufactured zeroes. |
| Westpac pp.6/15 | $1bn non-retail RWA overlay; $500m operational capital overlay | Neither is a mortgage credit RWA adjustment. No mortgage-overlay zero is fabricated. |
| Westpac p.10 | October removal of $500m capital / $6,250m RWA; approximately 17bp CET1 increase | Subsequent event effective 15 October, separately dated from September stock. The reported CET1 impact is approximate. |

There are **38 selected cells**: CBA 9, ANZ 14, NAB 10 and Westpac 5. Full note
text can contain other contextual numbers outside this explicit numerical selection;
for example CBA's comparative `$nil` remains in the comment. Monetary adjustments
reported to one decimal billion do not become million-precise estimates merely
because conformance stores an exact base-unit decimal representation.

## Researcher decision: ANZ aggregate applicability

The researcher selected **Accept aggregate link**: CR6's September AIRB mortgage
subtotal includes the $3.1bn explicitly qualified overview overlay, based on matching
portfolio, date, EAD $373,535m and RWA $94,135m, with CMS2 corroboration. Record this
as a researcher-approved cross-table interpretation, not a quotation from CR6.

The durable decision is
`catalogue/decisions/anz-2025-aggregate-overlay-v1.json`. It applies to aggregate
RWA and aggregate density only. Band-level allocation/treatment remains unresolved.
This refines the earlier ANZ source review's wholly unresolved CR6 treatment.

## Derived NAB bridge

NAB CR6 explicitly excludes overlays (PDF p.48 / printed 46) and reports $112,014m
(PDF p.49 / printed 47). The overview and CMS2 report $112,064m for AIRB mortgages.
Store both published values, then retain the $50m difference as
`derived_reconciliation_difference`, with input identities, Bronze output versions,
producing Silver revision, master manifest and calculation version. It is not an
explicitly published mortgage-overlay allocation. The full $4.8bn credit overlay
and group output floor are not subtracted from the mortgage CR6 subtotal.

`examples/rwa_adjustments.py` executes the existing four-bank workflow, exports the
persisted adjustment inventory and retains this bridge separately as JSON. All
tabular calculation uses Mountainash. This does not overwrite reported RWA or
allocate aggregate adjustments across bands.

## Verification

Independent source expectations initially failed for all four banks because the
adjustment observations were absent. A first real CBA saved-Bronze/staging run
exposed absent unit conversion: source amounts survived but normalised amounts were
null. An explicit retained unit mapping fixed that issue. The persisted integration
test checks base-unit amounts, distinct capital/RWA, original CR6/CR9 row counts,
ANZ aggregate-only interpretation and decision provenance, and the separately
retained NAB bridge after deleting staging databases.

The focused suite passed all fourteen tests. A complete four-bank run retained
38 supplementary observations alongside 36 CR6 and 33 CR9 rows. Direct master
readback confirmed 29 monetary values, five scalars and four source-missing CCR
positions. ANZ's model-introduction date and source-specific currency knowledge
also survive persistence.

Durable generated output (outside the coding worktree):

`/home/ubuntu/git/discreteds/rwa-analysis/data/research/rwa-adjustments-corrected-6yyy9pb6/`

- `bronze/`: four new `adjustments-corrected` captures with retained snapshots.
- `silver/master.duckdb`: consolidated values and complete source metadata.
- `manifests/`: staging/master selections and producing revisions.
- `research/adjustment-observations.parquet`: convenience readback inventory.
- `research/nab-mortgage-rwa-bridge.json`: $50,000,000 derived difference and inputs.

Execution log: `/tmp/opencode/rwa-adjustments-corrected-run.log`.
Earlier runs (including `rwa-adjustments-2026-10-17-a2n3ljoy`) are superseded:
review found that inference truncated Westpac's 0.0001 basis-point unit factor,
producing a zero scalar. The ingestion boundary now uses Mountainash's supported
`PydataIngress.convert(source_spec=spec, inline_conform=False)` before conformance.
The persisted regression failed before this repair and passed afterwards; the
corrected durable run explicitly verifies the 17bp result as `0.00170000`.

The full suite completed with 209 passes and one outdated Westpac source-cell-count
expectation (180 versus 185 after its five new observations). The rerun also exposed
the same test's outdated reconstructed-table inventory. Both expectations now include
the new selection. The affected suites passed twelve other tests, and the corrected
Westpac test passed independently. The persisted adjustment test passed after the
decimal repair. Together these runs cover all 210 tests; the full suite was not
repeated after the final expectation-only correction. Ruff, whitespace and 85
documentation-path checks passed.
Independent complexity review passed: the existing-contract composer, four
source-local declarations, catalogue additions and separate derived result were
all grounded in approved requirements. No scope-preserving cuts or blockers were
identified. Further genericisation and historical-helper migration were rejected
as unnecessary for this delivery. Independent correctness re-review approved the
native source-schema repair and closed its sole P1 finding, reproducing preservation
of the late-row `0.000100` factor. No open review defects or verification failures
remain.
