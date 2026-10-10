# Reviewed CR6 extraction

Install using the [locked environment](../../README.md#install-and-check).
Run from the project root, with one writer. Commands accept
`--project-root /path/to/project`; paths printed on success identify saved inputs.

```sh
uv run rwa extract --bundle au/cba/2025-06-30/aps330 --output-version v1
uv run rwa extract --bundle au/westpac/2025-09-30/aps330 --output-version v1
uv run rwa extract --bundle au/nab/2025-09-30/aps330 --output-version v1
uv run rwa extract --bundle au/anz/2025-09-30/aps330 --output-version v1
```

The explicit [CLI inventory](../../src/rwa_analysis/cli.py) binds each bundle to
its reviewed extractor and declared PDF in [raw/index.md](../../raw/index.md).
No network acquisition or LLM calls occur. Extractors capture nine rows and
twelve fields per bank, including absent values, qualifiers, nested labels,
source dates, page locations and subtotal relationships. The independently
authored [goldens](../../tests/bronze/) verify extraction; they are not rebuild inputs.

Publication requires executing Python sources, the selected extractor,
`pyproject.toml` and `uv.lock` to match the recorded Git commit. Commit reviewed
changes first. An alternate data root can use the installed checkout's history,
with identical retained input files. The CLI refuses dirty production runs;
exploratory Python runs belong in explicitly labelled scratch directories with
honest scratch provenance, outside retained `data/bronze` and manifests.

Bronze is saved at
`data/bronze/<bundle-key>/<output-version>/bundle.json`. Decimal source values
are strings in the lossless JSON envelope; original tokens and missing reasons
remain separate. The envelope records producing implementation revision,
dependencies, workflow/schema versions and execution time. A version is immutable:
if `v1` already exists, inspect its envelope and choose a new explicit version
such as `v2`. Never delete a retained version to rerun a changed extractor.

Missing PDFs or scripts fail with their paths. Unknown bundles are rejected;
bank/date guessing is unsupported. Source or interpretation corrections require
new Bronze versions or catalogue revisions respectively, followed by a new
[rebuild request and manifest](silver-rebuild.md).

## Scope and limitations

The selection is CBA June and Westpac/NAB/ANZ September 2025 mortgage CR6,
36 rows in total. ANZ's separate NZ block and March comparatives are outside
this selection. Reporting-folder jurisdiction does not establish exposure
geography or currency.

- CBA currency, several geographies, most weights and borrower distinctness
  remain unresolved. Its PD weight uses period-end EAD; RWA includes overlays.
- NAB source agreements map to arrangement counts. RWA and density exclude
  overlays; this does not authorise a band overlay allocation.
- ANZ's CR6 overlay treatment and counted entity remain unresolved. Its CMS2
  overlay statement is retained as cross-table evidence.
- Blank, dash, zero, not applicable and not disclosed at band grain remain
  distinct. Percentages are reported measures, not reconstructed quotients.

Consult each bank's source review linked from the raw index before changing
capture or interpretation. Partial semantics do not prevent faithful retention.

## Final visual reconciliation

After publication, render the saved selection and actual persisted values:

```sh
uv run rwa reconcile-tables --manifest data/manifests/cr6-2025-v1.json \
  --output data/reconciliation/cr6-2025-v1
```

`--project-root` and `--warehouse` have the same path rules as rebuild. Open
`index.html` in the output directory; no server or network is needed. Each bank
has an original source image plus Bronze and Silver tables with all nine rows
and twelve fields. Scroll the paired numeric views horizontally; hover cells
for exact values, precision, status and source identifiers. Expand metadata and
notes to inspect qualifications, unresolved meanings, bands and relationships.
Full source-page images include the surrounding table and footnotes; additional
evidence pages retain their actual PDF and captured printed labels.

Silver display uses persisted numeric columns divided by the recorded unit
factor, never captured numeric strings. `differences.json` compares exact values
before rounding and checks retained metadata, lineage and mappings. Missing rows,
fields and non-conformed values remain explicit. Findings are review evidence,
not automatic corrections or accounting constraints.

The warehouse publication marker and manifest digest must match. Read-only
rendering validates retained input bytes but permits a newer executing renderer;
`review-inputs.json` records the actual publication manifest and renderer commit,
dirty status and source digests separately. Rebuild still requires matching
producing code/environment. Never reuse the old manifest for a changed-code run:
commit a new request with a new revision identity and use a fresh warehouse.

Existing output directories are never overwritten. After review, retain the
review record alongside the artifacts and archive `data/reconciliation` with
the other [retained inputs](silver-rebuild.md#back-up-retained-inputs). Record LLM
review as such; automated zero differences do not establish human approval.
