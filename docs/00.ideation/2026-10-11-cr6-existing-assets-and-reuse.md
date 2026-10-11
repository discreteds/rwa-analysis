# CR6 existing assets: preservation and explicit reuse

Date: 2026-10-11. Baseline: `feat/cr6-bronze-to-silver`, commit `0fc5221` (PR #1).

## Finding

This is a simplification of a completed working demonstration, not a greenfield build. The previous replacement plan unnecessarily proposed new extraction/serialization modules, a new catalogue file format, new goldens plumbing, a new CLI framework and a new renderer. Those are not prerequisites to dataset-wide Mountainash transformations or three-table Silver.

The reviewed baseline contains four working bespoke extractors (2,231 lines of source-specific geometry and evidence capture), four full independent goldens, source metadata, a populated catalogue, retained Bronze, published Silver and reviewed HTML. The source-specific work is the research asset to preserve, not implementation scaffolding to discard. Subsequent researcher simplification: use direct Python orchestration and reconstruct tables as dataframes; the CLI and HTML presentation are not part of the replacement.

## Verified inventory

| Asset | Observed state |
|---|---|
| Raw disclosures | All 17 PDF files already in the original checkout are byte-identical to `0fc5221`: 16 primary disclosures and ANZ's supplementary explanation. No reacquisition required. |
| Four golden sets | `tests/bronze/au/{bank}/{date}/aps330/{golden.json,golden-notes.md}` in the baseline. CBA date is `2025-06-30`; Westpac/NAB/ANZ are `2025-09-30`. |
| Saved Bronze | Four `v1/bundle.json` envelopes; every decoded `payload` exactly equals its corresponding independent golden. Each contains one selected dataset with nine rows. Producer revision remains `198ea6ada83e1b9cae2c59e752487644584c9e18`. |
| Source metadata | Goldens/Bronze retain context, axes, bindings, source labels/units/precision, bands, qualifications, evidence and source relationships. These are already populated, not tasks to re-author. |
| Catalogue | 18 concepts, 10 measure definitions, one agreed interpretation decision and 88 scoped mappings, selected by `catalogue/releases/cr6-v1.json`. Existing revision IDs and evidence/decision references are durable inputs. |
| Reconciliation | Three retained runs: `cr6-2025-v1`, `cr6-2025-task9-v2`, `cr6-2025-final-v3`; each `differences.json` is empty. This checks the saved finding files, not a new visual sign-off. |
| Final warehouse | `data/warehouse-cr6-2025-final-v3.duckdb`, seven-table demonstration output; useful as a comparison baseline, not the new physical schema. |
| Working code/history | Baseline commit remains reachable locally and on the pushed branch. Directory relocation did not lose it. |

The final review note at baseline `docs/00.ideation/2026-10-10-cr6-visual-reconciliation.md` records 36 observations, 432 field positions, 32 source relationships, 152 passing tests and the original LLM visual review. These are historical results, not claims about the replacement implementation.

## Preserved in the original checkout

Copied and byte-compared **338 files / 264,605,747 bytes** from the temporary locations. Existing conflicting destinations would have stopped the copy; none were found. Original copies remain untouched.

| Destination under `/home/ubuntu/git/discreteds/rwa-analysis/` | Contents |
|---|---|
| `data/bronze/` | Four original versioned envelopes, unchanged |
| `data/manifests/` | Three historical retained manifests, unchanged |
| `data/warehouse*.duckdb` | All three historical warehouses |
| `data/reconciliation/` | All three HTML/image/review/provenance artifact sets |
| `data/diagnostics/` | Existing diagnostic artifacts |
| `data/reference/rwa-layered-spike/` | Whole-dataset Mountainash spike code, inputs, results, manifests and databases |
| `data/reference/rwa-model-spike/` | Earlier model/field-binding exploration and populated examples |
| `data/reference/rwa-2025-spike/` | Discovery text and source-page images |
| `data/reference/rwa-task9-draft/`, `data/reference/rwa-task9-draft-screenshots/` | Historical draft rendering and screenshots, clearly separated from reviewed runs |
| `data/reference/rwa-task9-visual.cjs` | Existing browser screenshot helper |
| `data/reference/cr6-demo-execution-evidence/` | Prior ignored execution/review evidence |
| `data/reference/recovery/` | Task 8, task 9 and final-v3 archive files, Git bundles and retained recovery screenshot |

Virtual environments, caches and `node_modules` were not copied. Restore the environment from the existing `pyproject.toml`/`uv.lock`; do not relocate an old virtual environment. Tracked code and PDFs remain available through Git rather than another full working copy. Historical provenance may contain original absolute paths; preserving those records is not permission to continue development there.

`data/` remains Git-ignored. This is local persistent preservation, not external backup configuration.

## Explicit reuse decisions

Paths below are at `0fc5221` unless already present in this checkout.

| Disposition | Exact assets | Implementation action |
|---|---|---|
| **Reuse unchanged** | `raw/*.pdf` | Use the existing files. Restore the demo's updated `raw/index.md` annotations when importing source assets. |
| **Reuse unchanged** | All four `extractions/au/.../extract.py` and `review.md` | Restore the actual scripts, not just their geometry. Keep source review, passages and helper calls. Change only for a demonstrated source/extraction defect. |
| **Reuse unchanged** | All four `tests/bronze/au/.../{golden.json,golden-notes.md,test_extraction.py}`; `tests/support/golden.py` | Keep independent expectations and the existing recursive mismatch diagnostics. Do not replace them with new expected payloads or a second comparator. |
| **Reuse unchanged initially** | `src/rwa_analysis/extraction/{models,cr6,codec,runner,values}.py` | Keep existing import paths, dataclasses, token parsing and source wire format. They already support the goldens and retained Bronze. Rewriting the codec would add migration work without helping the transformation requirement. |
| **Reuse unchanged initially** | `src/rwa_analysis/storage/bronze.py` | Read the existing envelope, not a newly invented bare-payload `bundle.json`. Preserve original producer/version metadata and write-once behavior. |
| **Reuse unchanged** | `catalogue/concepts/`, `measures/`, `decisions/`, `mappings/`, `releases/` | Keep the files and IDs. A smaller execution projection may compile these into tables; it does not replace the authoritative catalogue with `catalogue/cr6-v1.json`. |
| **Reuse dependency pins; remove CLI declaration** | `pyproject.toml`, `uv.lock` | Retain the proven data dependencies. Remove the `rwa` console entry point and direct Typer dependency, then refresh the lock; no replacement CLI framework. |
| **Reuse** | `src/rwa_analysis/contracts/frames.py` | Keep the 21-line proven Decimal-preserving Mountainash contract boundary. |
| **Adapt narrowly** | `src/rwa_analysis/catalogue/{load,models,resolve}.py` | Keep loading/versioned knowledge. Execute selected mappings as dataset-sized tables/relations; simplify resolution only where required by that path. Do not erase recorded decisions or broaden interpretation scope. |
| **Replace transformation internals** | `src/rwa_analysis/normalization/cr6.py` | Replace `_convert_row` and duplicated Python numeric conversion with whole-dataset Mountainash expressions, using the preserved spike's shape. Preserve numeric field names and source-based IDs. |
| **Adapt physical projection** | `src/rwa_analysis/normalization/{models,validate}.py` | Project context/bands onto observations and interpretation/mapping/lineage onto field metadata. Three tables instead of seven; Mountainash owns joins, checks and conversions. |
| **Adapt narrowly** | `src/rwa_analysis/storage/{manifests,silver}.py` | Retain saved-input selection, working transaction API and same-marker repair fix. Call these functions directly from ordinary Python. |
| **Do not import** | `src/rwa_analysis/cli.py`, `tests/integration/test_cr6_cli.py` | CLI orchestration is removed from scope. Existing core/lifecycle tests cover the callable functions. |
| **Reuse numeric reconstruction knowledge only** | `src/rwa_analysis/reporting/cr6_reconciliation.py` | Reuse source ordering/bindings and inverse-conversion behavior to produce dataframes with Mountainash. Do not import HTML/CSS, page-image generation or browser presentation. Preserve existing output artifacts as historical evidence. |
| **Reuse as historical comparison** | Final-v3 warehouse, manifests, rendered pages and review note | Compare overlapping values/semantics while adapting the physical schema. Do not claim seven-table outputs prove the new projection correct or overwrite old runs. |

### Tests already owning the important behaviors

Retain or adapt these existing tests, rather than adding parallel replacements:

- `tests/integration/test_bronze_storage.py`: lossless immutable storage and missing-member decoding regressions.
- `tests/integration/test_mountainash_boundary.py::test_domain_decimal_contract_and_persistent_roundtrip`: the 10-trillion boundary, exact fractional Decimal and all-null columns.
- `tests/catalogue/test_cr6_catalogue.py::test_cba_pd_evidence_does_not_leak_to_lgd` and `::test_source_specific_count_overlay_and_perimeter`: existing interpretation knowledge/isolation.
- `tests/silver/test_cr6_conformance.py::test_source_values_and_partial_semantics_survive` and `::test_missing_scale_blocks_only_its_conversion`: source-backed numbers, missingness and partial conformance.
- `tests/integration/test_silver_rebuild.py::test_fresh_rebuild_identity_and_exact_manifest_repeat`: fresh rebuild, missing PDFs and same-marker repair.
- `tests/integration/test_silver_rebuild.py::test_real_view_obstruction_rolls_back_all_tables_and_marker`: real transaction rollback; retarget the obstruction to a retained table rather than inventing another fault-injection mechanism.
- `tests/integration/test_silver_rebuild.py::test_mapping_revision_and_selected_scope_replacement`: changed interpretation and scope removal.
- Scenarios from `tests/integration/test_cr6_reconciliation.py`: four-bank source ordering, persisted numeric corruption (including below display precision), absent rows and revision identity. Adapt these to dataframe values; omit HTML parsing, the `table_cell` helper, image checks and browser presentation.

Update tabular test queries to Mountainash and physical expectations to the new projection. Raw SQL can remain for deliberate corruption/DDL obstruction. Tests asserting removed policy machinery need individual triage against the simple spec, not indiscriminate restoration or wholesale deletion. No new test suite or test-count target is needed.

## What the replacement actually needs to build

1. Restore the selected existing assets/code at their established paths and run the existing source/storage checks.
2. Replace the per-row Silver implementation with dataset-wide Mountainash while keeping the source contract and durable knowledge.
3. Adapt publication and numeric table reconstruction to the three-table projection; demonstrate a CBA dataframe using the already saved Bronze and direct Python calls.
4. Run the same path over the other three already extracted bundles and adapt existing lifecycle/numeric-reconstruction regressions.

See the revised [implementation plan](../04.planning/superpowers/plans/2026-10-10-simple-cr6-research.md). Importing active implementation code awaits plan approval; preservation above is complete.
