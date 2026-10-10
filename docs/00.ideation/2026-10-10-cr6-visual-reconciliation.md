# CR6 visual reconciliation — 10 October 2026

Reviewer: **OpenAI GPT-6 Astra, LLM agent**. This is not human sign-off.

## Outcome

**All four selected tables reviewed; no unexplained extraction, conformance or
rendering discrepancy identified.** All retained artifact sets have zero exact-value
and metadata findings. Legitimate unresolved meanings listed below remain tagged.

The primary review reads the actual published `cr6-2025-v1` warehouse. Its
manifest and four Bronze `v1` bundles record producer
`198ea6ada83e1b9cae2c59e752487644584c9e18`. Renderer commit
`e200a62d95fd6398231ddb580c6c53e590bad350` is recorded separately, with clean
source status. Reading historical publication evidence does not claim that the
renderer is the original producing implementation.

A fresh run after the code additions uses manifest `cr6-2025-task9-v2`, producer
`e200a62d95fd6398231ddb580c6c53e590bad350`, and separate warehouse
`data/warehouse-cr6-2025-task9-v2.duckdb`. It selects the original four Bronze
`v1` bundles and catalogue release `cr6-v1`. All seven Silver tables are logically
identical to v1 after excluding the new revision ID. Neither original Bronze,
original manifest nor `data/warehouse.duckdb` was overwritten. The original five
retained input files are byte-identical to the Task 8 archive, and its recovered
seven-table snapshot equals the original v1 warehouse.

Manifest SHA-256 (retained run provenance, not PDF acquisition identity):

- `cr6-2025-v1`: `deb1d59064d7516ac9e10bb673a1a00a05cfc86ad9ed7b3a69f19567480178e4`
- `cr6-2025-task9-v2`: `f08a1c9b363cc74d29723e362f5336929af30c35afce4c9859351d4a48e7e151`

## Final replay fix and current publication

Current runnable publication: `cr6-2025-final-v3`, produced and rendered from clean
commit `b58eb8d3e34469f2aa0121e7681ccda6fabe205e`. The fix removes the identical-marker
early return: every validated replay atomically replaces Silver. The existing
recovery test was observed failing with 0 observations before the fix and passing
with all 36 restored afterward. Different-input reuse remains rejected.

- Manifest: `data/manifests/cr6-2025-final-v3.json`; SHA-256
  `298490a26550eb5d9f9433153b934c7783955072b41ad0d591234996303c49f9`.
- Warehouse: `data/warehouse-cr6-2025-final-v3.duckdb`.
- Reviewed index: `data/reconciliation/cr6-2025-final-v3/index.html`;
  adjacent `review.md`, `review-inputs.json` and empty `differences.json` retain
  review and implementation provenance.
- Same four immutable Bronze v1 bundles and catalogue cr6-v1. All seven tables
  equal task9-v2 after excluding revision identity: 4/32/36/432/1,296/432/32 rows
  for contexts/segments/observations/interpretations/mappings/lineage/relationships.
- All eight reconstructed HTML tables equal the previously reviewed tables after
  replacing only revision ID; all 32 source images are byte-identical. All five
  pages' local links resolve. Prior 432-position visual findings remain applicable
  by this comparison; no new browser screenshot review is claimed.
- Focused rebuild suite: **16 passed**. Full suite: **152 passed**, 184.72 seconds;
  existing Ibis deprecation warnings. Ruff lint/format and diff checks passed.

The historical runs and direct visual findings below remain the review evidence.
Use the [current rebuild commands](../workflows/silver-rebuild.md) with final-v3;
historical manifests require matching historical implementation code.

## Coverage and findings

The agent opened the actual source-page images rendered with
`pdfplumber.Page.to_image` and browser screenshots of all four Bronze and Silver
reconstructions. Each selected block contains eight bands and one aggregate,
with all twelve source field positions. Numeric bodies, original precision,
blank/dash distinctions, headers and row order matched the source pages. This
covers **432 source positions in each view** (864 reconstructed cells), not just
sample totals. Review included date/entity/portfolio/approach, both axes, notes,
default/aggregate roles and the eight band-to-total links per bank. Relationships
retain their captured exhaustive/disjoint status; no sums, averages, density
quotients or overlay allocations were used to repair reported values.

- **CBA PDF/printed 55:** empty maturity and band provisions, subtotal, PD/RWA/
  density footnote markers 1–3. The reported 22% density remains reported;
  it was not replaced by a quotient of rounded numbers.
- **Westpac PDF/printed 48:** early mortgage rows above the vertically centred
  portfolio label are included; default CCF is a dash, maturity is blank.
  Direct review of p. 49 confirms density footnote a; corporate-only footnote b
  is not applied to mortgages.
- **NAB PDF 49 / printed 47:** columns a–l, one-decimal density (including 6.0%),
  shaded maturity and band provisions, unshaded aggregate provision. Direct
  review of PDF 48 / printed 46 confirms agreement counts, disclosure at asset
  class rather than band level, and exclusion of overlays from RWA/density.
- **ANZ PDF/printed 57:** source rows 10–18, AIRB scope, dashes for maturity,
  blank band provisions, subtotal and footnotes 1–3. Direct images of pp. 6–7,
  23, 54 and 116 confirm entity/Level 2 scope, AUD millions, the separate CMS2 overlay
  evidence, Suncorp's exclusion from IRB-specific tables and the retail maturity
  template modification.

Classification/disposition:

- **Extraction/structural:** none identified; no Bronze/golden changes required.
- **Conformance:** none identified; no mapping or numeric correction required.
- **Rendering-only:** native source colours and shading not captured as metadata
  are deliberately not inferred. In particular, Westpac's source shading remains
  visible in the PDF image while its captured blank states remain blank with a
  missingness tooltip. NAB's explicitly captured shading is reproduced. Different
  wrapping, table grid and review-status cues are explained presentation choices.
- **Legitimate unresolved source meaning:** retained below, with no approval of
  cross-bank comparability implied by this visual review.

The final v1 Bronze and Silver browser screenshots were opened directly by the
LLM after generation. Final v2 source images and all eight table screenshots were
verified byte-identical to these reviewed images; the v2 NAB overview was also
opened directly. Browser screenshots expand tables to 1800 px to inspect every
column, and retain separate 1920 px overview screenshots of the normal three-view
layout. These are review aids, not pixel-snapshot tests. The renderer's provenance
correctly states that rendering itself does not perform visual approval; this
record and each artifact directory's `review.md` record the subsequent LLM review.

## Artifacts

Open `data/reconciliation/cr6-2025-v1/index.html`. Its four review pages are:

- `data/reconciliation/cr6-2025-v1/cba-2025-06-30-cr6.html`
- `data/reconciliation/cr6-2025-v1/westpac-2025-09-30-cr6.html`
- `data/reconciliation/cr6-2025-v1/nab-2025-09-30-cr6.html`
- `data/reconciliation/cr6-2025-v1/anz-2025-09-30-cr6.html`

The fresh run has the same page names under
`data/reconciliation/cr6-2025-task9-v2/`. Both directories include
`differences.json`, `review-inputs.json`, full-page source images and
`review-screenshots/`. All page images and resources are local. Main source
captions distinguish PDF position from printed label, notably NAB 49 / 47 and
its explanatory page 48 / 46. Supplemental images cover every captured evidence
page, including Westpac 49 and ANZ entity/template/overlay evidence.

## Verification

- Renderer boundary tests were observed red before implementation, then green:
  `uv run pytest tests/integration/test_cr6_reconciliation.py -q` (2 passed).
  They protect persisted numeric reads, the source-million `+1` mutation,
  sub-display `+0.01` base-currency error, explicit absent row, actual four-bank
  presentation and publication-revision mismatch. There is no defensive matrix
  or renderer-specific production test seam.
- Final `uv run pytest -q`: **152 passed** in 176.79 seconds. The first full run
  was stopped by a 120-second command timeout; the complete run used a larger
  limit. Existing Ibis `fetch_arrow_table()` deprecation warnings remain.
- Ruff check, Ruff format check and `git diff --check` passed. Local links in
  changed documentation and workflows were checked.
- Real CLI rendering succeeded for the older published manifest with a newer
  renderer; fresh manifest/rebuild/render succeeded under a distinct revision.
- Self-review checked that present Silver digits come only from persisted numeric
  columns, inverse conversion precedes display rounding, metadata/lineage are
  compared, all captured HTML text is escaped, and rebuild retains its strict
  executing-version check by default.

## Retention

Both reviewed artifact sets join the retained-input archive at
`/tmp/opencode/rwa-task9-local-recovery-e200a62/rwa-inputs-reviewed.tar.gz`.
It includes raw sources, original Bronze, both manifests, catalogue/configuration,
lock/project configuration and both review directories. Restoration to
`/tmp/opencode/rwa-task9-local-recovery-e200a62/restored-inputs/` verified all
**104 artifact files byte-for-byte**, all local links across ten HTML pages,
and opening the restored v1 index in Chromium. Retain the adjacent
`rwa-code-reviewed.bundle` with this archive for implementation and review history.

`RWA_BACKUP_ROOT` was unset: **external durable backup remains pending**. This
local rehearsal is not a claim of external retention.

## Retained semantic limitations

CBA currency and several geographies, most weighting conventions and borrower
distinctness remain unresolved. NAB counts agreements (mapped to arrangements),
not an asserted count of distinct people. ANZ CR6 overlay treatment remains
unresolved: the CMS2 statement is cross-table evidence, not automatic CR6
inheritance. These are legitimate research limitations, visible in the source
notes and field interpretations, not extraction errors or reasons to drop values.

See [extraction and review commands](../workflows/cr6-extraction.md) and
[retention/recovery](../workflows/silver-rebuild.md).
