# First CR6 Bronze-to-Silver Implementation Plan

**Status: historical implementation reference.** The researcher declined PR #1 as a merge candidate and retained it as a working demonstration. Review the proposed [simpler CR6 research workflow](../specs/2026-10-10-simple-cr6-research-design.md) before any further implementation; this plan is not the active execution target.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task, according to the execution method chosen by the researcher. Steps use checkbox (`- [ ]`) syntax for tracking. Do not start implementation before plan review. Use `test-audit` when authoring tests and `test-driven-development` when implementing features.

**Goal:** Extract the complete Australian mortgage CR6 blocks from CBA June 2025 and Westpac, NAB and ANZ September 2025 into retained Bronze bundles, then publish a source-traceable, Decimal-preserving Silver revision in local DuckDB from pinned durable inputs.

**Architecture:** Each PDF has a reviewed, bespoke extractor returning source-oriented dataclasses. Retained Bronze and a separate versioned semantic catalogue feed Mountainash conformance into wide typed Silver records with field-level interpretation and lineage. Validate the whole candidate before publishing its tables and revision marker in one `mountainash-data` transaction.

**Tech Stack:** Python 3.12+, uv/lockfile, dataclasses, Pydantic command/configuration models, Mountainash, mountainash-data/DuckDB, mountainash-files, pdfplumber, Polars/Arrow interchange, Typer, pytest, Ruff.

**Spec:** [Initial model](../specs/2026-10-10-initial-data-model.md), [layered contracts/E–R diagrams](../specs/2026-10-10-layered-data-model.md), [platform architecture](../specs/2026-10-10-rwa-analysis-design.md). Evidence: [feasibility spike](../../../00.ideation/2026-10-10-layered-model-feasibility-spike.md), [CBA/Westpac review](../../../00.ideation/2025-disclosure-spike.md), [worked CR6 example](../specs/2026-10-10-data-model-worked-examples.md#1-cr6-mixed-measures-over-a-shared-population).

Scope extension requested by the researcher: include NAB and ANZ September 2025 Australian mortgage CR6. Additional evidence: [NAB/ANZ source and metadata review](../../../00.ideation/2025-nab-anz-metadata-spike.md). The successful feasibility spike covered CBA/Westpac only; the added banks require independent source authoring and integration verification.

## Global Constraints

The following are governing requirements quoted from the specifications:

- “Python 3.12+, uv and a committed lockfile”.
- “Use Python dataclasses and explicit Mountainash tabular conversions.”
- “One PDF's bespoke extractor owns one logical Bronze bundle.”
- “The initial production golden scope covers the full Australian mortgage CR6 blocks from CBA June 2025 and Westpac, NAB and ANZ September 2025.”
- “Keep monetary amounts, percentages and maturity in Decimal and actual integral counts as integers.”
- “Do not use binary floats as the persistence contract.”
- “Golden sets are saved independently of script output and ordinary test execution uses the selected saved version without LLM calls.”
- “Silver reads saved Bronze rather than reopening PDFs or rerunning extraction.”
- “Partial mappings and unresolved semantic attributes remain publishable with tags.”
- “The initial execution model has one writer.”
- “Publish database outputs and successful processing status within one owned transaction.”
- “Optional local editable overrides support ecosystem development without making sibling checkout paths a requirement for reproducible runs.”
- “Git-ignored generated data still requires an explicit retention/backup location; ‘ignored’ does not mean disposable.”

Read [principles guidance](../../../01.principles/README.md), [maintenance rules](../../../01.principles/PRINCIPLES.md) and the applicable actual principle documents before execution. Preserve existing uncommitted work. Do not modify the Mountainash repositories to make a project test pass without a separately agreed dependency change.

## Review Focus

These risks were not established by the successful spike; their owning tasks add verification:

1. **Clean dependency installation:** locally modified Mountainash code must not be an invisible runtime dependency; clean pinned sources must pass the integration boundary (Task 1).
2. **PDF layout and source context:** Westpac's vertically centred heading, CBA's blank columns, NAB's shaded cells/page offset and ANZ's numbered rows/explained dashes must not lose values or meaning; complete independently authored goldens own extraction correctness (Tasks 2–3B).
3. **Source availability versus conversion:** a present source value with an unsupported scale must retain lineage as `not_conformed`; unknown weighting alone must retain its converted value (Task 6).
4. **Ambiguous interpretation and broken references:** overlapping contradictory mappings must remain visibly conflicting; dangling catalogue/source references and cross-revision Silver joins must fail structurally (Tasks 5–6).
5. **Publication and recovery:** a real storage failure must preserve both old data and its revision marker, and an external durable-input backup must rebuild an empty warehouse (Tasks 7–8).

---

## Scope and delivery boundaries

This plan implements the first evidence-to-Silver subproject. It is not the whole platform's A–D delivery: capital/PDB functions, Gold, charts, historical acquisition, CR9, other domain extractors, generic ontology tooling, incremental upserts and comparative/restatement deduplication have separate delivery scopes. No empty packages for them are created here.

The existing repository contains PDFs and documentation, not application code. The scratch spike is evidence about APIs and data shapes; none of its manually populated records becomes a golden fixture by copying its output.

There are eleven reviewable tasks: retain the existing Task 1–8 identifiers, insert NAB Task 3A and ANZ Task 3B after Westpac, and finish with Task 9's table reconstruction and visual reconciliation. The expected full slice is four bundles, four Australian mortgage datasets, 36 rows and 432 field positions, subject to independent PDF verification. Westpac/NAB/ANZ share the September reporting date; CBA remains June. Equal dates or labels do not establish equivalent portfolio or measure definitions. ANZ's selected block is AIRB, not all group mortgage exposures; its separately disclosed NZ block and March comparatives remain future scope within the same document bundle.

### Fixed identifiers for this slice

| Concern | CBA | Westpac |
|---|---|---|
| PDF | `raw/cba-2025-06-30-aps330.pdf` | `raw/westpac-2025-09-30-aps330.pdf` |
| Bundle key | `au/cba/2025-06-30/aps330` | `au/westpac/2025-09-30/aps330` |
| Extractor | `extractions/au/cba/2025-06-30/aps330/extract.py` | `extractions/au/westpac/2025-09-30/aps330/extract.py` |
| Review | Same directory, `review.md` | Same directory, `review.md` |
| Golden directory | `tests/bronze/au/cba/2025-06-30/aps330/` | `tests/bronze/au/westpac/2025-09-30/aps330/` |
| Selected dataset ID | `cr6-residential-mortgages` | `cr6-residential-mortgages` |
| Main PDF/printed page | 55 / 55 | 48 / 48; density qualification on 49 |

| Concern | NAB | ANZ |
|---|---|---|
| PDF | `raw/nab-2025-09-30-aps330.pdf` | `raw/anz-2025-09-30-aps330.pdf` |
| Bundle key | `au/nab/2025-09-30/aps330` | `au/anz/2025-09-30/aps330` |
| Extractor | `extractions/au/nab/2025-09-30/aps330/extract.py` | `extractions/au/anz/2025-09-30/aps330/extract.py` |
| Review | Same directory, `review.md` | Same directory, `review.md` |
| Golden directory | `tests/bronze/au/nab/2025-09-30/aps330/` | `tests/bronze/au/anz/2025-09-30/aps330/` |
| Selected dataset ID | `cr6-residential-mortgages` | `cr6-residential-mortgages` |
| Main PDF/printed page | 49 / 47; definitions on PDF 48 | 57 / 57; source rows 10–18 |
| Initial output version | `v1` | `v1` |
| Initial output version | `v1` | `v1` |

The extraction ID is document-oriented `aps330`, so adding another selected domain later extends the same bundle. Initial record IDs are `band-1` through `band-8` and `portfolio-aggregate`; they identify these reviewed source rows, not a universal eight-band invariant. Source field IDs use the twelve Bronze names in the layered spec.

Proposed stable observation ID: `<bundle-key>/<dataset-id>/<record-id>`. Its field lineage adds `/<field-id>@<output-version>`. Output versions and mutable canonical concepts do not enter observation identity. This covers repeated extraction of unchanged source grain; changed-grain replacements require explicit replacement lineage in a subsequent scoped enhancement. Do not accept a changed-grain correction as a rename of an existing record ID.

### Retained inputs and outputs

```text
catalogue/
    concepts/cr6-v1.json
    measures/cr6-v1.json
    decisions/cr6-v1.json
    mappings/cba-2025-06-30-v1.json
    mappings/westpac-2025-09-30-v1.json
    mappings/nab-2025-09-30-v1.json
    mappings/anz-2025-09-30-v1.json
    releases/cr6-v1.json
config/rebuilds/cr6-2025-v1.json
data/
    bronze/<bundle-key>/v1/bundle.json
    manifests/cr6-2025-v1.json
    warehouse.duckdb
```

Catalogue/configuration files are Git-tracked, append-revised source assets. `data/` remains ignored; Bronze and manifests are retained and backed up, while the warehouse is rebuildable. New versions create new paths and never overwrite a retained file. JSON numbers that represent Decimal quantities are explicitly encoded as strings and explicitly decoded by field type; a permissive `default=str` decoder is not a schema.

One schema version, `cr6-v1`, owns the initial serialization. Strict decoders reject unknown/missing fields and unsupported versions rather than discarding metadata. Extraction envelope run metadata is separate from the source payload, so golden equality excludes only the documented envelope: output version, execution timestamp, implementation revision and environment identifiers.

### File responsibilities

Create only when its owning task needs it; package `__init__.py` files expose no speculative API.

| File/module | Responsibility | Task |
|---|---|---:|
| `pyproject.toml`, `uv.lock`, `README.md` | Install, commands, pinned environment | 1, 8 |
| `src/rwa_analysis/contracts/frames.py` | Typed Mountainash conformance/validation with Decimal preservation | 1 |
| `src/rwa_analysis/extraction/models.py` | Shared source context, references, fields, bands, bindings and relationships | 2 |
| `src/rwa_analysis/extraction/cr6.py` | Explicit twelve-field Bronze row, dataset, bundle | 2 |
| `src/rwa_analysis/extraction/codec.py` | Strict lossless schema encoding/decoding | 2, 4 |
| `src/rwa_analysis/extraction/runner.py` | Load the requested bespoke script and invoke its public extractor | 2 |
| `src/rwa_analysis/extraction/values.py` | Shared token parsing only after demonstrated reuse | 3 |
| `src/rwa_analysis/storage/bronze.py` | Immutable saved-bundle publication/loading | 4 |
| `src/rwa_analysis/catalogue/models.py`, `load.py`, `resolve.py` | Typed revisions, release closure, scoped interpretation | 5 |
| `src/rwa_analysis/normalization/models.py`, `cr6.py`, `validate.py` | Silver records/tables, conversion and cross-table checks | 6 |
| `src/rwa_analysis/storage/manifests.py`, `silver.py` | Durable input selection and transactional publication | 7 |
| `src/rwa_analysis/cli.py` | Typer commands; orchestration, not business logic | 8 |
| `docs/workflows/cr6-extraction.md`, `silver-rebuild.md` | Operator instructions and retention/recovery | 8 |
| `src/rwa_analysis/reporting/cr6_reconciliation.py` | Recreate source-shaped tables from retained Bronze and persisted Silver, alongside PDF page images | 9 |
| `docs/00.ideation/2026-10-10-cr6-visual-reconciliation.md` | Recorded visual findings tied to the reviewed input/output revisions | 9 |

## Task 1: Establish a clean, reproducible Mountainash boundary

**Files:** Create `pyproject.toml`, `uv.lock`, `README.md`, `src/rwa_analysis/__init__.py`, `src/rwa_analysis/contracts/__init__.py`, `src/rwa_analysis/contracts/frames.py`, `tests/integration/test_mountainash_boundary.py`.

**Interfaces:**

```python
def conform_frame(frame: pl.DataFrame, spec: ma.TypeSpec) -> pl.DataFrame:
    """Preserve explicit physical types; fail on contract errors."""
```

**Deliverable:** a locked install from immutable sources that validates and round-trips a Decimal/missing/count frame through the intended libraries. No PDF extraction is needed to establish this boundary.

- [ ] **1. Resolve the environment from clean commits.** Start with the following candidate revisions, observed during planning. Mountainash and mountainash-data working trees were dirty during the spike, so these commits are candidates, not a verified equivalent of that environment. Confirm remote availability and run this task's checks using the locked install. If a required public API is absent at these commits, identify the needed released/committed change and obtain the revised pin; do not silently require a sibling checkout.

| Repository (`https://github.com/mountainash-io/…`) | Candidate revision |
|---|---|
| `mountainash` | `9f43cf818223c02793a6e5f516edaf2924f5339f` |
| `mountainash-data` | `36f4f4a68bc17de51bfc22bbfbd9dd9191db2701` |
| `mountainash-files` | `13721c33fa5876ba8ee1e69917f3e9ce9f781fc2` |
| `mountainash-settings` | `e81750960b3fb078ae239696b848054568af6c72` |
| `mountainash-auth-client` | `1b57247f17deb68c1178635486c05a8bfc6fa83b` |
| `mountainash-transport` | `f79e3a3729f31c88f148f4c8443657ae68c652ce` |

Use `[tool.uv.sources]` Git entries with exact `rev` values for all six. Declare these ecosystem dependencies explicitly to make transitive source overrides unambiguous. Add `mountainash-data[duckdb]`, `pdfplumber`, `polars`, `pyarrow`, `pydantic`, `typer`; dev dependencies `pytest`, `ruff`. Pin `polars==2.0.0`, `duckdb==1.5.6` and `ibis-framework==12.0.0` initially to match the probed backend combination; commit resolved transitive versions in `uv.lock`. Set Python `>=3.12`, Hatchling build backend, and:

```toml
[project.scripts]
rwa = "rwa_analysis.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib"

[tool.ruff]
target-version = "py312"
```

The console entry point becomes usable in Task 8. Run `uv lock` then `uv sync --locked`; record the actual verified pins in README. Install-time repository credentials, if needed, stay outside tracked configuration.

- [ ] **2. Write the boundary test before the adapter.** Its independent contract is exact transport of a precision-sensitive value and a null; the credible failure is Float64 coercion or all-null type inference. It is the only owner of the generic precision sentinel; extraction tests own source values.

```python
def test_decimal_contract_and_persistent_roundtrip(tmp_path):
    import mountainash as ma
    import polars as pl
    from decimal import Decimal
    from mountainash_data import IbisBackend
    from rwa_analysis.contracts.frames import conform_frame

    frame = pl.DataFrame(
        {"id": ["present", "missing"],
         "amount": [Decimal("12345678901234567890.12345678"), None],
         "count": [742470, None]},
        schema={"id": pl.String, "amount": pl.Decimal(38, 8), "count": pl.Int64},
    )
    spec = ma.TypeSpec.from_frictionless({
        "fields": [{"name": "id", "type": "string"},
                   {"name": "amount", "type": "number"},
                   {"name": "count", "type": "integer"}],
        "primaryKey": ["id"], "missingValues": [],
    })
    result = conform_frame(frame, spec)
    path = str(tmp_path / "boundary.duckdb")
    with IbisBackend(dialect="duckdb", database=path) as db:
        db.create_table("sample", result.to_arrow())
    with IbisBackend(dialect="duckdb", database=path) as db:
        restored = pl.from_arrow(db.table("sample").to_pyarrow()).sort("id")
    assert restored.schema == frame.schema
    assert restored.equals(frame.sort("id"))
```

- [ ] **3. Run** `uv run pytest tests/integration/test_mountainash_boundary.py -q`; confirm the intended missing adapter failure. Implement the adapter using the verified public API:

```python
def conform_frame(frame, spec):
    if spec.missing_values != []:
        raise ValueError("Typed frames require explicit missingValues: []")
    result = ma.relation(frame).conform(spec, apply_value_transforms=False).collect()
    contract = ma.datacontract(spec)
    contract.Config = type("Config", (), {"coerce": False})
    report = contract.validate_datacontract(result)
    if not report.passes:
        raise ValueError(str(report.check_summaries))
    if result.schema != frame.schema:
        raise ValueError("Unexpected physical dtype change")
    return result
```

Also reject nonempty field-level missing sentinels in this typed boundary. Do not mutate the dependency's shared base `Config`. This adapter validates already-typed data; it does not parse numeric strings or establish semantic units.

- [ ] **4. Extend the same boundary test module to write/read a small nested JSON record through `mountainash_files.write(FileSinkSpec(...), encoded)` and `parse(FileSourceSpec(...), output="pydata")`.** Use encoded `{"value": "0.0800", "missing_reason": null}` and a second absent-value record; compare against those literal records, including null fields. Inspect the pinned `parse` signature. The library may normalize object shapes through Arrow; ensure the intended envelope survives before selecting its wrapper in Task 4. A failed representation check is a blocker for that encoding, not permission to omit metadata.

- [ ] **5. Run** the boundary module, `uv run ruff check src tests`, and `uv run ruff format --check src tests`. Commit the working environment and adapter as `build: establish pinned Mountainash integration boundary`. Record any difference from the spike APIs in the workflow documentation; do not keep tests requiring a known dependency bug to remain broken.

## Task 2: Source-author CBA goldens and implement its complete Bronze extraction

**Files:** Create the extraction modules listed above except `values.py`; create `extractions/au/cba/2025-06-30/aps330/{review.md,extract.py}`, `tests/bronze/au/cba/2025-06-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`, `tests/support/{__init__.py,golden.py}`. Modify `raw/index.md` to link the review/extractor.

**Interfaces:**

```python
# In the bespoke script:
def extract(pdf_path: Path) -> ExtractionBundle: ...
# In extraction/runner.py:
def run_extractor(script_path: Path, pdf_path: Path) -> ExtractionBundle: ...
# In extraction/codec.py:
def encode_payload(bundle: ExtractionBundle) -> dict: ...
def decode_payload(payload: dict) -> ExtractionBundle: ...
# In tests/support/golden.py:
def assert_golden(actual: dict, expected: dict) -> None: ...
```

Here and below signatures describe interfaces; implementation steps supply behavior. No stubbed successful return is an acceptable completion.

- [ ] **1. Reinspect the PDF before authoring the extractor.** Use the PDF skill at execution time. Inspect p. 55 visually, the report-level definitions and applicable introductions/glossaries; record source evidence for entity, date, scope and currency or explicitly unresolved attributes. The earlier discovery is a navigation aid. Author the complete nine-row/twelve-field golden directly from source, with all axes, bindings, labels, references, scales, precision, bands, qualifications and aggregate relationships. Record the independence of authoring in `golden-notes.md`; never generate expected values by executing the extractor or copying the scratch model.

Known review anchors: first-band EAD `281,508`, PD `0.08`, count `742,470`; aggregate EAD `691,020`, RWA `149,143`, provisions `1,768`. Initial expected blank positions: nine maturities and eight band provisions. Check these against the PDF rather than accepting the notes as proof. Exact complete golden content is the output of this source-authoring step, not manufactured in this plan.

- [ ] **2. Define the smallest typed source contract that represents the authored golden.** Use frozen dataclasses, tuple collections and explicit field types:

| Type | Required content |
|---|---|
| `SourceReference` | document ID; PDF page; printed label; table/row/column or note/span location |
| `ReportedValue[T]` | typed value, original text, displayed precision, missing reason, source reference |
| `DatasetContext` | entity, document/table date, source portfolio, regulatory/geographical scope, source labels and evidence/status per unresolved attribute |
| `SourceAxisItem`, `PublishedField`, `ValueBinding` | IDs, ordered headers, source units/scale and explicit row/column/context/qualification references |
| `BandDefinition`, `SegmentationDefinition` | source bounds/units/inclusivity or category, ordering, source-backed completeness/disjointness status |
| `Qualification`, `SourceRelationship` | evidence, scope, typed row/field/block endpoints; subset does not imply exhaustive children |
| `BronzeCreditRiskExposureRow` | record/source-row/segment/scope refs plus all twelve explicit `ReportedValue` fields from the layered spec |
| `Cr6Dataset` | ID, context, axes, published fields, bindings, segmentation, qualifications, relationships, typed rows |
| `ExtractionBundle` | document, bundle key, extractor path, schema version, tuple of named CR6 datasets |

Use `ReportedValue[Decimal]` for eleven financial fields and `ReportedValue[int]` for `reported_borrower_count`. Validate that present values have no missing reason, absent values have one, IDs are unique within their scope, and all referenced source objects resolve. Do not encode nine rows or eight bands as dataclass invariants. Complete strict encoding/decoding for every declared field; reject floats and nonfinite Decimal values. Scalar JSON Decimal strings preserve their exponent/displayed precision separately from their numerical value.

- [ ] **3. Write the complete PDF-to-payload test, then run it red.** Use project-root discovery from `Path(__file__).resolve().parents` and the ancestor containing `AGENTS.md` and `raw/`, rather than depending on the process working directory.

```python
def test_complete_cba_source_contract():
    import json
    from pathlib import Path
    from rwa_analysis.extraction.runner import run_extractor
    from rwa_analysis.extraction.codec import encode_payload
    from tests.support.golden import assert_golden

    root = next(p for p in Path(__file__).resolve().parents
                if (p / "AGENTS.md").exists() and (p / "raw").is_dir())
    pdf = root / "raw/cba-2025-06-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/cba/2025-06-30/aps330/extract.py", pdf)
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
```

Create `tests/__init__.py` for the support import; do not add Python packages to date-named directories. `assert_golden` recursively compares complete dictionary key sets, ordered collections and scalar values and reports a path such as `datasets[0].records[0].ead.value`; no ignored unknown keys, schema intersection or numeric tolerance. Source collection order is part of the golden where the source has order.

Run: `uv run pytest tests/bronze/au/cba/2025-06-30/aps330 -q`. The first failure must be a missing extractor/contract, not a missing installed PDF dependency.

- [ ] **4. Implement actual extraction with source-specific geometry.** `run_extractor` uses `importlib.util.spec_from_file_location` to load the explicit script and calls `extract(pdf_path)`; missing PDFs raise `FileNotFoundError`, and wrong return types fail. In the CBA script, open `pdfplumber`, select `pages[54]`, determine the mortgage block and twelve column ranges from the inspected header/table coordinates, then assign tokens by x/y positions. Empty coordinate windows produce blank cells without shifting adjacent values. Capture actual header/note strings and check required source labels before constructing records. Keep layout constants and page selections in this script, not a bank-wide parser. Literal numerical data matrices are forbidden in the extractor.

The relevant token conversion is deliberately small:

```python
def parse_decimal_token(token: str) -> Decimal | None:
    text = token.strip()
    if text in {"", "-"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    numeric = text[1:-1] if negative else text
    value = Decimal(numeric.replace(",", "").removesuffix("%"))
    return -value if negative else value
```

The original token and source precision are captured before normalization. Count parsing requires exact integrality; a nonintegral count fails rather than truncating. Metadata from notes is source-backed and remains distinct from catalogue interpretations. If discovery contradicts a prior expectation, update the golden with a recorded source rationale, not to imitate extractor output.

- [ ] **5. Run the CBA golden to green and verify comparison sensitivity.** In a focused comparator test `tests/test_golden_comparison.py`, compare small literal dictionaries with identical values but a changed band upper inclusivity, missing selected field and extra unknown field; each must raise `AssertionError` with the differing key path. This owns the shared comparator's failure behavior rather than duplicating source expectations. Run the CBA test and comparator module, format/lint changed files, commit `feat: capture complete CBA mortgage CR6 evidence`.

## Task 3: Add Westpac's independent golden and bespoke extractor

**Files:** Create `extractions/au/westpac/2025-09-30/aps330/{review.md,extract.py}`, `tests/bronze/au/westpac/2025-09-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`. Create `src/rwa_analysis/extraction/values.py` only for token behavior actually shared with CBA; modify CBA imports if extracted. Modify `raw/index.md`.

**Interfaces:** Uses `ExtractionBundle`, `run_extractor`, `encode_payload`, `assert_golden` from Task 2; produces a second `extract(pdf_path: Path) -> ExtractionBundle` under the same contract.

- [ ] **1. Review Westpac p. 48 visually plus the p. 49 footnote and applicable report definitions.** Independently author all 108 cell positions and metadata. Review anchors: aggregate EAD `569,920`, RWA `116,433`, provisions `1,347`; fourth-band CCF `101%`; default CCF `-`; nine blank maturities and eight blank band provisions. Retain 17 blanks and the dash distinctly unless new source evidence supports a revised missing-value meaning. The vertically centred mortgage heading does not mark the start of the data block.

- [ ] **2. Write and run the full source contract test red.** The test is the following complete entry-point comparison:

```python
def test_complete_westpac_source_contract():
    import json
    from pathlib import Path
    from rwa_analysis.extraction.runner import run_extractor
    from rwa_analysis.extraction.codec import encode_payload
    from tests.support.golden import assert_golden

    root = next(p for p in Path(__file__).resolve().parents
                if (p / "AGENTS.md").exists() and (p / "raw").is_dir())
    pdf = root / "raw/westpac-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/westpac/2025-09-30/aps330/extract.py", pdf)
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
```

Run: `uv run pytest tests/bronze/au/westpac/2025-09-30/aps330 -q`.

- [ ] **3. Implement Westpac's coordinate extraction on `pages[47]` and qualification capture on `pages[48]`.** Identify all mortgage rows from reviewed table geometry, including those above the portfolio label. Retain percent suffixes in original strings and blank maturity windows. Reuse parsing only where both files demonstrate the same behavior; keep row/column coordinates, source-label expectations and page choices bespoke. Do not borrow a CR9 weighting statement to complete CR6 semantics.

- [ ] **4. Run** `uv run pytest tests/bronze/au -q`; both complete goldens must pass. Expected scope is 18 rows and 216 field positions, with independent context/date and default/aggregate assertions embedded in the saved goldens. Run changed-file Ruff checks; commit `feat: capture complete Westpac mortgage CR6 evidence`.

## Task 3A: Add NAB's independent golden and bespoke extractor

**Files:** Create `extractions/au/nab/2025-09-30/aps330/{review.md,extract.py}`, `tests/bronze/au/nab/2025-09-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`. Modify shared extraction dataclasses/codec only for metadata actually required by this source, and modify `raw/index.md` to link the review/extractor.

**Interfaces:** Uses `ExtractionBundle`, `run_extractor`, `encode_payload`, `assert_golden` from Task 2; produces `extract(pdf_path: Path) -> ExtractionBundle` for `au/nab/2025-09-30/aps330`. Its single selected dataset has ID `cr6-residential-mortgages`.

- [ ] **1. Review PDF p. 49 / printed p. 47 visually, plus CR6 definitions on PDF p. 48 and applicable report-level currency/entity statements.** Independently author all nine rows and twelve field positions. Preserve column IDs `a`–`l`, PDF/printed page distinction, original labels and one-decimal RWA-density precision. Inspect shaded cells together with the template legend; only assign `not_applicable` where source evidence establishes that meaning. Do not copy CBA/Westpac's blank-cell counts or missing reasons.

The source review identifies residential mortgage counts as agreements, distinguishes them from corporate counterparties, and states that CR6 RWA/RWA density exclude overlays. Preserve those statements and their applicability in Bronze. Retain the on-balance-sheet **EaD pre-CRM** and off-balance-sheet **EaD pre-CCF and pre-CRM** labels; template field placement alone does not establish equivalence to another bank's gross-exposure definition. Review anchor: CR6 aggregate RWA `112,014` million, distinct from summary/CMS2 `112,064` million. Inspect definitions to determine whether an apparent conflict is a source-qualified measure difference; do not force reconciliation.

- [ ] **2. Write and run the complete PDF-to-payload test red.**

```python
def test_complete_nab_source_contract():
    import json
    from pathlib import Path
    from rwa_analysis.extraction.runner import run_extractor
    from rwa_analysis.extraction.codec import encode_payload
    from tests.support.golden import assert_golden

    root = next(p for p in Path(__file__).resolve().parents
                if (p / "AGENTS.md").exists() and (p / "raw").is_dir())
    pdf = root / "raw/nab-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/nab/2025-09-30/aps330/extract.py", pdf)
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
```

Run: `uv run pytest tests/bronze/au/nab/2025-09-30/aps330 -q`. The complete golden owns the source value, shaded-cell meaning, source labels, column IDs and page-offset assertions; do not duplicate those in helper inventory tests.

- [ ] **3. Implement source-specific coordinate extraction on `pages[48]` and definition capture on `pages[47]`.** Keep page selection, geometry and column identifiers in the NAB extractor. Capture the relevant agreement/count and overlay statements, and bind them only to the appropriate fields/populations. Missing numeric tokens in shaded windows are represented without shifting columns. Parse displayed density as Decimal with the original precision retained. No number matrix, forced RWA adjustment or borrowed count convention belongs in the script.

- [ ] **4. Run** `uv run pytest tests/bronze/au -q`; the three completed source contracts must pass, with an expected combined 27 rows and 324 field positions. If shared metadata models changed, complete strict codec support and rerun the earlier goldens. Run changed-file Ruff checks; commit `feat: capture complete NAB mortgage CR6 evidence`.

## Task 3B: Add ANZ's independent golden and bespoke extractor

**Files:** Create `extractions/au/anz/2025-09-30/aps330/{review.md,extract.py}`, `tests/bronze/au/anz/2025-09-30/aps330/{golden.json,golden-notes.md,test_extraction.py}`. Modify shared dataclasses/codec only for source-required metadata, and modify `raw/index.md`.

**Interfaces:** Uses the shared extraction interfaces from Task 2; produces `extract(pdf_path: Path) -> ExtractionBundle` for `au/anz/2025-09-30/aps330`. The selected `cr6-residential-mortgages` dataset describes the Australian AIRB block, with its actual source portfolio/context retained.

- [ ] **1. Review PDF/printed p. 57 visually, entity/perimeter statements on p. 6, CMS2 overlay context on p. 23 and the applicable template-modification explanation.** Independently author all nine rows and twelve field positions. Preserve source row numbers 10–18 alongside the local record IDs. Identify ANZ BH Pty Ltd's Level 2 reporting perimeter; distinguish the selected AIRB mortgage population from standardised Suncorp/Norfina exposures and the separate NZ distribution on p. 60. Do not pull March comparative rows into this September dataset.

The source explains omitted retail maturity through its non-use in RWA calculation: retain the actual dash and source-supported missingness reason, with a qualification reference. The borrower footnote says definitions vary by portfolio; it does not establish mortgage agreement counts. Do not inherit NAB's arrangement mapping. Review anchor: mortgage CR6 subtotal RWA `94,135` million. Capture p. 23's `3.1` billion PD-model overlay statement as supporting context with its original scope and date; equal CMS2/CR6 totals alone do not prove a CR6 inclusion policy. An inferred applicability decision must be recorded separately and reviewed with the researcher, or remain provisional/unresolved.

- [ ] **2. Write and run the complete source contract test red.**

```python
def test_complete_anz_source_contract():
    import json
    from pathlib import Path
    from rwa_analysis.extraction.runner import run_extractor
    from rwa_analysis.extraction.codec import encode_payload
    from tests.support.golden import assert_golden

    root = next(p for p in Path(__file__).resolve().parents
                if (p / "AGENTS.md").exists() and (p / "raw").is_dir())
    pdf = root / "raw/anz-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/anz/2025-09-30/aps330/extract.py", pdf)
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
```

Run: `uv run pytest tests/bronze/au/anz/2025-09-30/aps330 -q`. The golden must independently fix source-row coverage, September observation date, AIRB population and supported missingness metadata, so another correctly parsed ANZ block cannot accidentally pass.

- [ ] **3. Implement ANZ's source-specific extraction on `pages[56]`, selecting source rows 10–18 by reviewed geometry/identifiers.** Capture and bind applicable footnotes and definitions from their actual pages. Preserve source statement versus researched interpretation, original dash tokens, source row numbers and scope qualifications. Keep NZ and March comparative blocks outside the selected dataset. Extensions later add named datasets inside this bundle rather than copying the PDF or changing its bundle key.

- [ ] **4. Run** `uv run pytest tests/bronze/au -q`; all four complete goldens must pass. Expected full scope is 36 rows and 432 field positions, with per-source missingness counts independently established by the four goldens. Run changed-file Ruff checks; commit `feat: capture complete ANZ mortgage CR6 evidence`.

**Review checkpoint A:** inspect all four reviews and independently authored goldens before persistence/catalogue work. Resolve structural/extraction disagreements against the PDFs. Check NAB agreement counts/overlay exclusion and ANZ entity/perimeter/explained missingness explicitly. Unknown meaning stays explicit; it does not block this checkpoint.

## Task 4: Retain immutable Bronze versions through mountainash-files

**Files:** Create `src/rwa_analysis/storage/{__init__.py,bronze.py}`, `tests/integration/test_bronze_storage.py`; extend `extraction/codec.py` for the versioned envelope.

**Interfaces:**

```python
@dataclass(frozen=True)
class BronzeRef:
    bundle_key: str
    output_version: str

def save_bronze(bundle: ExtractionBundle, output_version: str,
                project_root: Path, implementation_revision: str) -> BronzeRef: ...
def load_bronze(ref: BronzeRef, project_root: Path) -> ExtractionBundle: ...
```

`BronzeRef` is defined in `storage/bronze.py`; identifiers cannot contain traversal components. The saved envelope includes `schema_version`, the reference, code revision, dependency versions, extraction workflow version, execution timestamp and `payload`. The payload is exactly the source contract tested above.

- [ ] **1. Write the storage boundary test using the four actual extractors.** Its independent risk is dropped/numerically changed metadata on serialization or accidental replacement, not extraction correctness:

```python
import pytest


@pytest.mark.parametrize("bundle_fixture", [
    "cba_bundle", "westpac_bundle", "nab_bundle", "anz_bundle",
])
def test_saved_bronze_is_exact_and_immutable(tmp_path, request, bundle_fixture):
    from rwa_analysis.extraction.codec import encode_payload
    from rwa_analysis.storage.bronze import save_bronze, load_bronze

    bundle = request.getfixturevalue(bundle_fixture)
    ref = save_bronze(bundle, "v1", tmp_path, "test-code-revision")
    assert encode_payload(load_bronze(ref, tmp_path)) == encode_payload(bundle)
    with pytest.raises(FileExistsError):
        save_bronze(bundle, "v1", tmp_path, "test-code-revision")
```

Define session fixtures `cba_bundle`, `westpac_bundle`, `nab_bundle` and `anz_bundle` in `tests/conftest.py` by invoking each public extractor against its saved PDF, with explicit prerequisite failures. Fixtures provide inputs, never expected values. Parameterize the shown exact/immutable storage test over the four bundle fixture names using pytest's `request.getfixturevalue`; this covers NAB/ANZ's additional source metadata through the real serialization boundary. The storage test owns strict decoder rejection too: parameterize unknown `schema_version`, one removed required payload field, and one unexpected payload field in a copied envelope; each load must raise `ValueError` identifying the field/version.

- [ ] **2. Run** `uv run pytest tests/integration/test_bronze_storage.py -q` red. Implement the verified `mountainash-files` JSON read/write wrapper with explicit schema encoding and decoding. Write into a same-parent temporary output directory, validate by reading it back, then rename into the new version directory; reject an existing destination, clean failed temporary writes. Single-writer ownership is assumed. Never write to an older version directory or use a mutable `latest` alias as a rebuild input.

```python
encoded = encode_payload(bundle)
write(FileSinkSpec(path=str(staging / "bundle.json")), envelope)
# The reader uses parse(..., output="pydata") and strict envelope/payload decoding.
restored = read_staged_bundle(staging / "bundle.json")
if encode_payload(restored) != encoded:
    raise ValueError("Bronze serialization changed source evidence")
staging.rename(destination)
```

`read_staged_bundle(path: Path) -> ExtractionBundle` is a private helper shared by save/load in `storage/bronze.py`; its parser/result unwrapping follows the representation verified in Task 1. `envelope`, `staging`, and `destination` are built from the declared reference and validated root. This check protects publication; it does not generate a golden.

- [ ] **3. Pass the storage module and all four extraction goldens; commit** `feat: retain versioned lossless Bronze bundles`. Do not publish the real `v1` data until the producing source code has a committed revision available for its envelope.

## Task 5: Implement the smallest durable CR6 catalogue and scoped mappings

**Files:** Create `src/rwa_analysis/catalogue/{__init__.py,models.py,load.py,resolve.py}`, all `catalogue/` files listed above, `tests/catalogue/test_cr6_catalogue.py`.

**Interfaces:**

```python
def load_catalogue(release_path: Path) -> CatalogueRelease: ...
def resolve_field(catalogue: CatalogueRelease, dataset: Cr6Dataset,
                  record: BronzeCreditRiskExposureRow,
                  field_key: str) -> FieldMeaning: ...
```

Define frozen dataclasses in `catalogue/models.py`: `ConceptRevision`, `ConceptRelationshipRevision`, `MeasureRevision`, `InterpretationDecisionRevision`, `SourceMappingRevision`, `CatalogueRelease`, `SemanticAttribute`, `FieldMeaning`. Each revision has stable ID, revision ID, creation date, source-effective interval and supporting source/decision refs as applicable. `CatalogueRelease` holds an explicit immutable member selection and its fully resolved members.

`SemanticAttribute` has `name`, typed scalar/reference `value`, status (`established`, `provisional`, `unresolved`, `conflicting`, `not_applicable`), evidence refs and decision refs. `MeasureRevision` has concept/result-unit refs and typed population, weighting, timing, count and adjustment attributes needed by CR6. `FieldMeaning` has optional concept/measure refs, selected mapping refs, these attributes, and an optional exact Decimal unit factor. This is structured meaning, not an unvalidated free-form dictionary.

- [ ] **1. Seed only source-backed concepts and measures needed for twelve fields and the selected context/band/row-role mappings.** Count result units remain separate from money. CBA's count does not acquire arrangement semantics. CBA PD's weight measure references the applicable EAD measure and period-end timing; mean LGD/CCF weighting remains unresolved unless source review established more. Keep regulatory expected loss distinct from provisions. Preserve CBA overlay and unrounded-density evidence. Source-informed partial measures are allowed; fields lacking an established measure can retain only concept/tags.

The four mapping files scope entries by bundle/document, dataset/template, source field, population/row overrides where evidenced, and observation date. Mapping `v1` IDs are not Python field names alone. `releases/cr6-v1.json` lists exact file/member revisions, not globs. Seed decisions only for already agreed researcher interpretations; source statements are evidence, not invented interviews. Unknown counting/weighting requires no guess to complete the release.

For NAB residential mortgages, map the source agreement definition to the already agreed arrangement-count concept with supporting PDF p. 48 evidence; do not apply the corporate-counterparty definition or transfer this meaning to other banks. Preserve explicit exclusion of overlays on RWA/RWA density. Keep NAB's pre-CRM exposure basis as a source-backed measure attribute rather than declaring equivalence by shared typed field name. For ANZ, preserve ANZ BH Pty Ltd/Level 2 and AIRB perimeter, keep mortgage counted entity unresolved unless additional source review resolves it, and link explained maturity missingness. Any CR6 overlay interpretation using CMS2 must retain the cross-table qualification and separate decision/provisional status; no identity-by-equal-total inference.

- [ ] **2. Write and run failing semantic/reference tests.** Use public resolution against the actual extracted sample:

```python
def test_cba_pd_evidence_does_not_leak_to_lgd(cba_bundle, project_root):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.catalogue.resolve import resolve_field

    cat = load_catalogue(project_root / "catalogue/releases/cr6-v1.json")
    ds = cba_bundle.datasets[0]
    row = ds.records[0]
    pd = resolve_field(cat, ds, row, "average_pd")
    lgd = resolve_field(cat, ds, row, "average_lgd")
    assert pd.attribute("weighting").value == "period_end_ead"
    assert pd.attribute("weighting").evidence_refs
    assert lgd.attribute("weighting").status == "unresolved"
```

`FieldMeaning.attribute(name: str) -> SemanticAttribute` returns the declared attribute or an explicit unresolved attribute; it does not copy another field's meaning. `project_root: Path` is a fixture in `tests/conftest.py` using the root discovery in Task 2.

Add a table-driven case copying release inputs into a temporary catalogue and changing (a) one referenced revision to an absent revision, or (b) a mapping to two equally applicable conflicting weighting assertions with distinct revision IDs. Case (a) must fail loading with the unresolved reference; case (b) must resolve `weighting.status == 'conflicting'`, retain both supports and preserve the known unit factor. Change fixture data directly, not resolver internals. Test wrong document/date scope by applying the CBA entry to Westpac and confirming it does not establish CBA weighting there.

- [ ] **3. Add cross-bank semantic tests, then implement explicit scope matching and release reference-closure checks.** The tests extend the same catalogue module:

```python
def test_nab_agreements_and_overlay_exclusion_are_scoped(
    nab_bundle, anz_bundle, project_root,
):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.catalogue.resolve import resolve_field

    cat = load_catalogue(project_root / "catalogue/releases/cr6-v1.json")
    nab = nab_bundle.datasets[0]
    anz = anz_bundle.datasets[0]
    count = resolve_field(cat, nab, nab.records[0], "reported_borrower_count")
    other_count = resolve_field(cat, anz, anz.records[0], "reported_borrower_count")
    rwa = resolve_field(cat, nab, nab.records[0], "rwa")
    assert count.attribute("counted_entity").value == "arrangement"
    assert count.attribute("counted_entity").evidence_refs
    assert other_count.attribute("counted_entity").status == "unresolved"
    assert rwa.attribute("overlay_treatment").value == "excludes_overlays"
```

The ANZ unresolved assertion reflects current evidence; revise it only with newly reviewed source evidence and the corresponding catalogue decision, not to share NAB's mapping. Extend the test to verify CBA overlay inclusion remains distinct and NAB source exposure-basis evidence is retained. ANZ overlay applicability must not become established merely from equality of two totals; verify the actual selected qualification/decision status against the reviewed interpretation.

Matching is conjunction over specified scope fields, not fuzzy label matching. Compose complementary attributes; resolve conflicting equal-applicability values to `conflicting` with both supports. A narrower override is used only when its mapping declares the supported override relationship. Reject cycles/dangling targets in revision dependencies. Do not choose by file order. Bind evidence references against selected Bronze during candidate validation in Task 6; catalogue loading alone cannot prove an external occurrence exists.

- [ ] **4. Run** `uv run pytest tests/catalogue -q` and all four source goldens after any shared-contract change. Commit `feat: add versioned CR6 semantic catalogue and mappings`.

## Task 6: Conform saved Bronze into validated Silver candidates

**Files:** Create `src/rwa_analysis/normalization/{__init__.py,models.py,cr6.py,validate.py}`, `tests/silver/test_cr6_conformance.py`. Extend `contracts/frames.py` only for demonstrated contract reuse.

**Interfaces:**

```python
@dataclass(frozen=True)
class SilverCandidate:
    revision_id: str
    tables: dict[str, pl.DataFrame]

def conform_cr6(bundles: tuple[ExtractionBundle, ...],
                bronze_refs: tuple[BronzeRef, ...], catalogue: CatalogueRelease,
                revision_id: str) -> SilverCandidate: ...
def validate_candidate(candidate: SilverCandidate,
                       bundles: tuple[ExtractionBundle, ...],
                       bronze_refs: tuple[BronzeRef, ...],
                       catalogue: CatalogueRelease) -> None: ...
```

Define `SilverCreditRiskExposureObservation` with the twelve explicit numeric columns from the layered spec, context/segment/role and revision-qualified identity. `SilverContext`, `SilverSegment`, `SilverFieldInterpretation`, `AppliedMapping`, `SourceLineage`, `SilverObservationRelationship` model the other projections. Dataclasses describe rows; explicit schemas create DataFrames, including zero-row/all-null tables. `tables` uses exactly `contexts`, `segments`, `observations`, `interpretations`, `applied_mappings`, `lineage`, `relationships`.

- [ ] **1. Write the conformance test with independently specified conversion expectations.** Build inputs by saving/loading actual extractor outputs through Task 4, not by loading golden JSON as production Bronze. Define `saved_bundles` and `bronze_refs` fixtures in this test module, using the real save/load APIs.

```python
def test_source_values_and_partial_semantics_survive(saved_bundles, bronze_refs, catalogue):
    from decimal import Decimal
    from rwa_analysis.normalization.cr6 import conform_cr6
    candidate = conform_cr6(saved_bundles, bronze_refs, catalogue, "test-r1")
    rows = {r["observation_id"]: r for r in candidate.tables["observations"].to_dicts()}
    cba = rows["au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1"]
    assert cba["ead_amount"] == Decimal("281508000000")
    assert cba["mean_pd_fraction"] == Decimal("0.0008")
    assert cba["mean_lgd_fraction"] == Decimal("0.14")
    assert cba["reported_entity_count"] == 742470
    assert cba["mean_maturity_years"] is None
    nab = rows["au/nab/2025-09-30/aps330/cr6-residential-mortgages/portfolio-aggregate"]
    anz = rows["au/anz/2025-09-30/aps330/cr6-residential-mortgages/portfolio-aggregate"]
    assert nab["rwa_amount"] == Decimal("112014000000")
    assert anz["rwa_amount"] == Decimal("94135000000")
    assert len(rows) == 36
    assert len(candidate.tables["lineage"]) == 432
```

The `catalogue` fixture calls `load_catalogue` on the tracked release; `saved_bundles` and `bronze_refs` contain all four source bundles. Add assertions in this owner test for the four aggregate rows having no segment, default bands having category kind `default` without synthetic intervals, source dates remaining separate, CBA LGD weighting unresolved, and all source missing fields represented. Verify NAB's Decimal density conversion preserves its one-decimal source precision through lineage, and ANZ's omitted maturity remains `source_missing` with its source-supported reason/qualification rather than `not_conformed` or zero. Expected missing positions come from each independent source contract, not an extrapolation of the spike's 35 missing cells. Do not hard-code unknown currency if source review has since established currency: test that the selected evidence/mapping revision determines it.

- [ ] **2. Add the missing-conversion and structural negative cases before implementation.** Copy a decoded source bundle with `dataclasses.replace`, changing one present monetary `PublishedField.scale` to unresolved and keeping its source value/evidence. Its Silver value must be null with `value_state='not_conformed'`, while lineage retains the source value and reason; other fields remain present. This is synthetic input, not a source fixture correction. Unknown LGD weighting must retain `0.14` with `value_state='present'`.

For numeric representability, use a synthetic value requiring more than eight decimal places and a value exceeding the selected Decimal precision: reject with a field-specific conversion error, never silently round. Structural candidate mutations cover a lineage link to an absent source occurrence, a wrong revision on a segment link, and a deleted interpretation for a represented numeric field. `validate_candidate` must reject each by reference/path. These are different risks from correct-value extraction and the generic transport sentinel.

- [ ] **3. Run** `uv run pytest tests/silver/test_cr6_conformance.py -q` red, then implement unit conversion and table projection. Use exact Decimal `0.01` for percent fractions and established source scales for base amounts, retaining sign. Compute exact Python Decimal bounds/representability with sufficient local decimal context before building explicit `pl.Decimal(38,8)` columns; this must happen before any cast can round. Count fields stay `pl.Int64`; reject overflow explicitly. Unit-scale uncertainty differs from currency-code uncertainty: a known million multiplier can produce a base amount with unresolved currency.

```python
expr = (ma.col(source_field) * ma.lit(factor)).alias(target_field)
converted = ma.relation(source_frame).select(*identity_columns, expr).collect()
validated = conform_frame(converted, spec_with_empty_missing_values)
```

`source_field`, `target_field`, `factor` are resolved per published binding and selected mapping; `identity_columns` is the list of `ma.col(...)` expressions for the declared identity/context fields. Build all twelve target expressions together rather than one table per measure. Missing and unsupported conversions get explicit typed null expressions. Numerical scale changes are transformations with lineage, not rewritten source strings.

- [ ] **4. Implement candidate validation at the publication boundary.** Require unique revision-qualified keys and exact row/field coverage; context and segment refs within the same revision; every lineage occurrence/qualification resolvable in the selected Bronze version; every applied mapping/definition in the selected release; source relationship endpoints and evidence retained; every value state's nullable column consistent. Counts and unit definitions remain field-specific. Use Mountainash contracts for frame constraints and Mountainash relations for cross-table anti-joins where supported; small typed catalogue/source reference sets can be checked in Python. Never accept a failed contract report merely because no exception was raised.

Do not reject partial mappings, a blank maturity, CCF/RWA density above one or rounding residuals. Do not sum portfolio aggregates with their bands. No exact band-to-total reconciliation rule is introduced without source-supported precision/coverage semantics.

- [ ] **5. Run** the conformance module, catalogue tests and the integration boundary after numerical/schema changes; commit `feat: conform CR6 evidence into typed Silver candidates`.

## Task 7: Publish Silver atomically from durable rebuild manifests

**Files:** Create `src/rwa_analysis/storage/{manifests.py,silver.py}`, `config/rebuilds/cr6-2025-v1.json`, `tests/integration/test_silver_rebuild.py`.

**Interfaces:**

```python
class RebuildRequest(BaseModel):
    revision_id: str
    bronze_refs: tuple[BronzeRef, ...]
    catalogue_release_path: str
    conformance_schema_version: Literal["cr6-v1"]

def save_manifest(request: RebuildRequest, project_root: Path,
                  implementation_revision: str) -> Path: ...
def rebuild(manifest_path: Path, project_root: Path, warehouse_path: Path) -> str: ...
def publish_candidate(candidate: SilverCandidate, manifest_path: Path,
                      warehouse_path: Path) -> None: ...
```

`save_manifest` freezes the request plus resolved catalogue member revisions, implementation Git revision, lockfile/environment reference and configuration into `data/manifests/<revision_id>.json`, atomically and without overwrite. It checks that all selected immutable input paths exist before recording them. `rebuild` reloads inputs, conforms and validates; only then calls `publish_candidate`. A manifest records an attempted reproducible run, not successful publication. Successful status and the consumed manifest reference live in the transactionally written `ops.silver_publication` table.

The initial tracked request selects all four `v1` bundles and `catalogue/releases/cr6-v1.json`. Curated semantic corrections are catalogue/mapping revisions; source corrections are Bronze versions. There is no silently ignored generic corrections field. The first CLI rejects unknown request keys, multiple versions of the same bundle in one selection, and unsafe IDs/paths. Inputs from additional comparative documents need an explicit source-selection design before they can be deduplicated.

- [ ] **1. Write the lifecycle test against actual file-backed databases.** Build/save all four Bronze inputs in a temporary project root with a copied tracked catalogue, then save manifest `r1`, rebuild into database A and reopen it. Save `r2` selecting identical inputs and rebuild into empty database B. Read tables through `IbisBackend`; compare sorted typed rows excluding only `silver_revision_id` and publication timestamps/manifest IDs. Both databases must contain 36 observations, 432 field interpretations/lineage, and source relationships. Define local test helper `read_snapshot(path: Path) -> dict[str, pl.DataFrame]` that queries the seven `silver` tables and `ops.silver_publication`; it does not serve production code.

- [ ] **2. Add a real publication-failure test.** Publish `r1`; rename `silver.applied_mappings` to `silver.saved_applied_mappings` in the test database and create a view at its original name selecting the saved table. This preserves the prior query result while obstructing table replacement. Attempt a later candidate through the real `publish_candidate`. Creating/replacing the table where the view exists must produce a real DuckDB/Ibis error after earlier tables have been replaced. Reopen the database and verify unchanged earlier tables, the old publication marker and the old mapping rows through the view; clean up the test obstruction afterward. A planning-time probe on the spike environment confirmed `CatalogException: Existing object applied_mappings is of type View, trying to drop type Table`, retained the old mapping rows and rolled back a preceding table creation. Reverify this behavior with the clean pins from Task 1. Do not add a production `fail_after` switch or a fake database implementation. The generic spike's injected exception is not the production regression test.

- [ ] **3. Implement namespaces and the owned transaction.** Use the public `db.raw_driver_connection().execute("CREATE SCHEMA IF NOT EXISTS silver")` and corresponding `ops` statement before publication; this escape hatch and the `namespace="silver"` table argument were exercised during plan review. Recheck against the clean pins. Publish in the declared order `contexts`, `segments`, `observations`, `interpretations`, `applied_mappings`, `lineage`, `relationships`, followed by the marker; require exactly that table set before entering the transaction. All revision tables and the single-row publication marker are replaced inside the same owned transaction:

```python
with IbisBackend(dialect="duckdb", database=str(warehouse_path)) as db:
    with db.transaction():
        for name, frame in candidate.tables.items():
            db.create_table(name, frame.to_arrow(), namespace="silver", overwrite=True)
        db.create_table("silver_publication", publication_frame.to_arrow(),
                        namespace="ops", overwrite=True)
```

`publication_frame` has `silver_revision_id`, `manifest_path`, `catalogue_release_id`, `schema_version`, `published_at`, `status='published'`; construct it with explicit physical types. Full candidates are materialized/validated before transaction entry. No pre-transaction deletes, per-table commits or in-place Silver correction. Revision-scoped keys are validated at the application boundary even if physical foreign keys are not installed.

- [ ] **4. Verify corrections, removal and repeat execution at this boundary.** A synthetic mapping revision changes one review annotation, retaining observation IDs/values and updating applied mapping refs. A manifest selecting only Westpac/NAB/ANZ removes every CBA observation/context/segment/field/relationship while retaining the September cohort's 27 observations and 324 field-lineage records with distinct source scopes. Repeating the exact successfully published manifest returns its revision without duplicating rows; an empty warehouse rebuilds it even if a manifest exists. Never reuse a revision ID with different frozen inputs. A malformed candidate must fail validation before publication; previous data remains queryable. This tests full selected-scope replacement, not changed-grain economic equivalence or comparative deduplication.

- [ ] **5. Run** `uv run pytest tests/integration/test_silver_rebuild.py -q`, then the conformance and boundary modules if publication required schema changes. Commit `feat: rebuild and atomically publish revisioned Silver`.

**Review checkpoint B:** inspect a real persisted observation, its complete field interpretation/lineage path and the publication marker. Confirm that removing the warehouse and rebuilding needs neither source PDFs nor golden files; saved Bronze and selected catalogue/manifests are authoritative inputs.

## Task 8: Deliver repeatable commands, source-only recovery and operator guidance

**Files:** Create `src/rwa_analysis/cli.py`, `tests/integration/test_cr6_cli.py`, `docs/workflows/{cr6-extraction.md,silver-rebuild.md}`; finish README and update `raw/index.md` links. Update the layered spec with links to implemented contracts and verified physical choices; change principle statuses only where the stated whole scope is actually implemented.

**Interfaces:** Typer `app`, invoking the APIs from prior tasks:

```text
rwa extract --bundle au/cba/2025-06-30/aps330 --output-version v1
rwa extract --bundle au/westpac/2025-09-30/aps330 --output-version v1
rwa extract --bundle au/nab/2025-09-30/aps330 --output-version v1
rwa extract --bundle au/anz/2025-09-30/aps330 --output-version v1
rwa manifest --request config/rebuilds/cr6-2025-v1.json
rwa rebuild --manifest data/manifests/cr6-2025-v1.json
rwa inspect --observation au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1
```

All commands accept `--project-root`; rebuild/inspect additionally accept `--warehouse`, defaulting to `<project-root>/data/warehouse.duckdb`. Bundle selection resolves only the reviewed extraction paths and their declared PDF, rather than guessing an arbitrary file from bank/date. `manifest` records the current committed implementation/lock selection; normal publication requires code and tracked config corresponding to that selection. Exploratory dirty runs must use an explicitly labelled scratch output, not claim reproducibility as a retained production revision.

- [ ] **1. Write the end-to-end CLI test using Typer's `CliRunner`.** Invoke all four extracts against the tracked PDFs into a temporary project root (copy/symlink the four PDFs and copy the necessary extractor/catalogue/config files). Invoke `manifest`, then remove access to the temporary raw PDFs and extractors before invoking `rebuild`. The result must succeed from saved Bronze, with 36 observations and the manifest-selected publication marker. `inspect` returns the selected typed values, field statuses, source occurrence refs, mapping refs and original evidence; inspect at least one record per bank to expose different source dates, count conventions, overlay treatment and missingness. Missing source prerequisites fail only extraction; rebuild must not consult the missing PDFs or goldens.

- [ ] **2. Implement the command orchestration and actionable errors.** Pydantic rejects unknown config fields; Typer prints path/source/field information for missing files, invalid references, duplicate output/revision IDs and failed contracts and exits nonzero. No automatic network acquisition or LLM calls occur. `inspect` reads via Mountainash relations and resolves archived source/catalogue references; it does not infer currency or weighting from neighboring fields.

- [ ] **3. Document concrete retention and recovery commands.** The researcher supplies an existing durable destination through `RWA_BACKUP_ROOT`; do not guess a machine-specific backup mount. Stop the single writer before archiving. Use a fresh revision-labelled archive, preserving exact paths and tracked code/config history:

```bash
: "${RWA_BACKUP_ROOT:?Set an external durable backup directory}"
git bundle create "$RWA_BACKUP_ROOT/rwa-code-cr6-2025-v1.bundle" --all
tar -czf "$RWA_BACKUP_ROOT/rwa-inputs-cr6-2025-v1.tar.gz" \
  raw data/bronze data/manifests catalogue config uv.lock
```

Refuse/relabel an already-existing backup filename rather than overwriting an earlier retained snapshot. Ensure catalogue/config/code changes referenced by the manifest have been committed before bundling; the database is deliberately unnecessary for this recovery procedure. Keep failed run diagnostics separately from the database's successful publication status. Retain PDFs/index, extractors, golden sets and source code in Git; retained data versions need the archive as well.

For recovery: clone the saved Git bundle to a new directory; check out the implementation revision named in the chosen manifest; extract the input archive there; `uv sync --locked`; run `rwa rebuild` with the archived manifest and an empty warehouse path. The archive and Git bundle are distinct but both required. Document installation credentials for private dependencies without storing secrets.

- [ ] **4. Exercise recovery in the CLI integration test.** Archive the test's retained inputs, restore into a different empty directory, and rebuild a new database with the same manifest using installed package code. Compare logical records to the first database, including interpretation/lineage and relationships. This owns path portability and backup content completeness; the earlier transaction test owns rollback. Do not test archive command text with source greps.

- [ ] **5. Run the complete project checks once the final changes are in place:**

```bash
uv sync --locked
uv run pytest -q
uv run ruff check src tests extractions
uv run ruff format --check src tests extractions
git diff --check
```

Check all modified documentation links. Run the four real extraction commands with retained `v1` versions only after finalizing the producing code revision, create the manifest, rebuild and inspect one record per bank. If any `v1` already exists, inspect its provenance and use a new explicit version/request rather than deleting it. Confirm the user-configured external backup by listing/reopening its archive before calling retention complete.

- [ ] **6. Commit** `feat: expose CR6 extraction rebuild and recovery workflow`, with a concise README example and actual verified dependency pins. Do not push without the researcher's instruction. Report the generated Bronze versions, catalogue release, manifest, Silver revision, passing checks and unresolved source semantics.

## Task 9: Recreate each table for final visual reconciliation

**Files:** Create `src/rwa_analysis/reporting/{__init__.py,cr6_reconciliation.py}`, `tests/integration/test_cr6_reconciliation.py`, `docs/00.ideation/2026-10-10-cr6-visual-reconciliation.md`; extend `src/rwa_analysis/cli.py`, README and `docs/workflows/cr6-extraction.md` with the review command. Generated HTML, page images and machine-readable differences live under `data/reconciliation/<silver-revision-id>/` and join the retained-input backup from Task 8 when reviewed.

**Deliverable:** four locally viewable HTML reconciliation pages, one for each selected mortgage CR6 block, plus an index. Each page places the actual source-page image beside source-shaped Bronze and Silver reconstructions. All nine rows and twelve field positions are visible, with applicable headings and notes. This is a final source-to-output review, not an accounting reconciliation or a new bank comparison chart.

**Interfaces:**

```python
def render_cr6_reconciliation(manifest_path: Path, project_root: Path,
                              warehouse_path: Path, output_dir: Path) -> Path:
    """Return index.html for the manifest's persisted, published revision."""
```

The renderer loads the exact Bronze/catalogue versions selected by the durable manifest and reads the published Silver tables through Mountainash/`IbisBackend`. Reject a warehouse whose publication marker does not match the requested revision. It never reruns extraction, reads a golden as source data, or republishes Silver. PDF access here is solely for source images and visual evidence; rebuilding Silver remains PDF-independent.

- [ ] **1. Specify the three aligned views and renderer correctness checks.** Source images cover CBA p. 55, Westpac p. 48, NAB PDF p. 49 / printed p. 47 and ANZ p. 57. Include adjacent/cross-table qualification images or linked local image sections where required, notably Westpac p. 49, NAB p. 48 and ANZ's relevant entity/template/overlay evidence. Preserve enough surrounding headings to identify the selected block; do not crop away units, footnotes or table dates.

The Bronze view renders captured row/column order, nested headings, portfolio/entity/date, source row/column identifiers, bands/default/aggregate roles, source units, original numeric strings, displayed precision, blank/dash distinctions, source relationships and applicable footnotes. Preserve shaded/non-applicable cues where captured and explain them in a legend. Do not invent a missing graphical property merely to imitate the PDF. Use HTML escaping for all captured text.

The Silver view uses persisted numeric columns and field metadata, joined to source positions through validated lineage. Apply the recorded inverse unit conversion to return to source scale (fractions to percent, base currency to source millions), then format with the source's displayed precision. Never populate present Silver cells from Bronze `original_text`; otherwise a broken conformance could look correct. Missing cells may reuse the source blank/dash presentation only when Silver availability/missingness agrees; attach a visible status cue or tooltip. Show `not_conformed`, absent rows/fields and unresolved/conflicting interpretations explicitly, rather than presenting available Bronze numbers as conformed values.

Compare exact Decimal values in source units **before** display rounding so sub-display errors are not hidden. A displayed rounded match with an exact-value mismatch must remain flagged. Do not recompute reported totals, PD averages or densities to make the table reconcile. Compare captured metadata as well as values: date, scope, bounds, units, precision and qualifications matter even when numbers match. Retain full captured strings; line wrapping/font differences alone are not extraction defects.

- [ ] **2. Write the renderer-boundary integration test red.** Reuse actual four-bank saved Bronze and published-Silver setup from the rebuild tests via a shared fixture only where this removes duplicate setup. Define `published_cr6` in `tests/conftest.py` to return `(manifest_path, project_root, warehouse_path)` after the public save/rebuild APIs complete. Define an HTMLParser-based helper `table_cell(path, view, observation_id, field_key) -> str` in this test module; cells carry `data-view`, `data-observation-id` and `data-field-key` attributes so their source position is inspectable in the artifact. These attributes also support review navigation, not a production-only test hook.

```python
def test_silver_reconstruction_reads_persisted_values(tmp_path, published_cr6):
    from mountainash_data import IbisBackend
    from rwa_analysis.reporting.cr6_reconciliation import render_cr6_reconciliation

    manifest, root, warehouse = published_cr6
    oid = "au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1"
    out = tmp_path / "reconciliation"
    render_cr6_reconciliation(manifest, root, warehouse, out)
    page = out / "cba-2025-06-30-cr6.html"
    assert table_cell(page, "bronze", oid, "ead") == "281,508"
    assert table_cell(page, "silver", oid, "ead") == "281,508"

    # Deliberately corrupt only the test warehouse; never a correction workflow.
    with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
        db.raw_driver_connection().execute(
            "UPDATE silver.observations SET ead_amount = ead_amount + 1000000 "
            "WHERE observation_id = ?", [oid],
        )
    changed = tmp_path / "changed"
    render_cr6_reconciliation(manifest, root, warehouse, changed)
    page = changed / "cba-2025-06-30-cr6.html"
    assert table_cell(page, "bronze", oid, "ead") == "281,508"
    assert table_cell(page, "silver", oid, "ead") == "281,509"
```

In the same test module, inspect the emitted `differences.json` and require the changed occurrence/field with exact source and reconstructed values. Add a sub-display mutation (`+0.01` base currency) that still displays `281,508` but remains flagged. Parameterize presentation checks for CBA blank maturity, Westpac default CCF dash, NAB's recorded one-decimal density and ANZ's explained maturity dash against the independently reviewed source expectations. Check a missing Silver field/row and mismatched publication revision produce explicit findings/error rather than silently filling from Bronze. No pixel snapshots or exact whole-HTML comparisons are needed.

Run: `uv run pytest tests/integration/test_cr6_reconciliation.py -q`.

- [ ] **3. Implement the renderer and command.** Use one small HTML/CSS template with an overview, three aligned views, a difference summary and source/interpretation notes. Join by source occurrence/field identity, not by table row position or matching labels. Render page images using `pdfplumber.Page.to_image` from the already-selected PDF toolchain; preserve one-based PDF/printed page labels in captions. Add synchronized source row/field labels and readable horizontal scrolling/print styling for the wide twelve-column table. A self-contained local directory must open without a web service or network resources.

```text
rwa reconcile-tables --manifest data/manifests/cr6-2025-v1.json \
  --output data/reconciliation/cr6-2025-v1
```

The command accepts the same `--project-root` and `--warehouse` options as rebuild/inspect. Output names are `index.html`, `cba-2025-06-30-cr6.html`, `westpac-2025-09-30-cr6.html`, `nab-2025-09-30-cr6.html`, `anz-2025-09-30-cr6.html`, `differences.json`, `review-inputs.json` and an `images/` directory. `review-inputs.json` records manifest, Bronze/catalogue/Silver revisions and renderer code version. Refuse to overwrite a reviewed artifact directory; a rerender after corrections uses a new explicit output directory/revision. Automated differences are findings, not automatic source corrections or proof of visual approval.

- [ ] **4. Generate and visually inspect all four reconstructed tables against the PDFs.** Use the PDF skill when examining the source pages. The reviewing human or LLM checks every selected row/field and source metadata, including NAB shading/precision/page labels, ANZ row numbers/AIRB scope/explained dashes, Westpac's early rows above its portfolio label and CBA's empty columns. Check footnote markers/text/applicability and aggregate/subset structure alongside the numeric body. Record reviewer identity/type, date, exact artifact/input revisions, per-table coverage, discrepancies and disposition in `docs/00.ideation/2026-10-10-cr6-visual-reconciliation.md`. An agent review must not be described as human sign-off.

Classify findings as extraction/structural, conformance, rendering-only, or legitimate unresolved source meaning. Correct extraction defects with source-backed golden/extractor changes and a new Bronze version; correct interpretation/conformance through durable mappings/code and a new Silver revision; correct rendering defects in the renderer. Rerun the affected owner tests and regenerate/review the affected table. Never change a golden merely because a reconstruction looks plausible or alter source values to force arithmetic agreement.

- [ ] **5. Finish with an explicit visual-reconciliation outcome.** All four selected tables must have a recorded review, with no unexplained extraction, conformance or rendering discrepancy. Legitimate unknown semantics may remain, visibly tagged. Run the renderer integration module and the affected owner checks after corrections, then the final project checks from Task 8 if implementation changed. Add the reviewed `data/reconciliation/` directory to the retention archive and verify its recovery. Commit the renderer, tests and actual review findings as `feat: recreate CR6 tables for visual reconciliation`; generated artifacts remain ignored and backed up. Report the four review-page paths and any retained semantic limitations to the researcher.

## Acceptance and coverage map

| Requirement | Owner |
|---|---|
| Clean dependency pins, Decimal numeric boundary | Task 1 |
| Full independent source expectations, four bespoke scripts, both axes and notes | Tasks 2–3B |
| Source-oriented typed models and versioned lossless Bronze | Tasks 2, 4 |
| Durable concepts/partial definitions, contextual mappings and evidence | Task 5 |
| Separate Silver records, known-unit conversions, partial knowledge | Task 6 |
| Source subset/aggregate links and field-level lineage | Tasks 2–3B, 6 |
| NAB agreement counts, exposure bases, overlay exclusion and source precision | Tasks 3A, 5–6 |
| ANZ AIRB/entity perimeter, source-row numbering and explained missingness | Tasks 3B, 5–6 |
| Structural versus semantic validation | Tasks 5–6 |
| Deterministic identity under mapping revisions | Tasks 6–7 |
| Full rebuild, selected-scope removal, atomic publication | Task 7 |
| Offline commands, no PDF dependence in Silver, external recovery | Task 8 |
| Recreate all four tables from saved Bronze/published Silver and visually reconcile against source pages | Task 9 |
| Capital/Gold, richer domain records, changed-grain replacements, comparative deduplication | Explicitly subsequent subprojects; not claimed by this delivery |

## Plan self-review

- Scope follows the approved first CR6 Bronze-to-Silver slice; wider platform goals are explicitly separate.
- Test owners are source extraction, encoding, semantics, numeric conformance, publication, CLI recovery and source-shaped reconstruction boundaries. Renderer mutation checks protect against copying source strings instead of displaying persisted Silver values. No test is added merely to assert a dataclass's field inventory or mirror its implementation.
- Production interfaces share the names/signatures listed above; tests use actual public paths and dependency behavior.
- All five Review Focus risks have owning verification steps.
- Physical file choices and initial identity/publication policy are proposed by this plan for review. They do not change agreed semantic principles or mark the unimplemented design as implemented.
