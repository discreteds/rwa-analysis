# Disposable metadata-driven extraction spike

**DISPOSABLE — architecture/shape review only. Do not merge this code into the
production pipeline or use it as the implementation base.** No production files,
retained Bronze versions or goldens are modified. No new test suite was written.

The researcher approved the design direction and requested this spike on 2026-10-13,
emphasising separation of configuration/reusable metadata from operations. This
probe implements a small path from the [design](../../docs/04.planning/superpowers/specs/2026-10-13-metadata-driven-extraction-design.md),
not the complete design or migration.

## Start with the separation

| File | Contains | Does not consume |
|---|---|---|
| `config.py` | Execution roots only | PDF layout, financial definitions |
| `metadata.py` | Data declarations; reusable roles and percent/ratio definitions | Files, PDF readers, database connections |
| `anz_2023.py` | Source coordinates/anchors; reviewed context definitions; occurrence and applicability bindings | Extraction/conformance/storage operations |
| `physical.py` | Five small physical readers, including a ruled-matrix reader | ANZ declarations, financial interpretations, storage |
| `capture.py` | Invoke supplied readers; assemble source occurrences; retain the metadata snapshot | Bank-specific meaning rules |
| `conformance.py` | Saved bindings -> existing semantic composer -> Mountainash relations -> DuckDB | PDF library, source configuration, physical readers |
| `run.py` | Explicit composition, retained outputs and independent demonstration comparisons | Hidden workflow state |

Source configuration is ordinary data construction. For example, the same
`anz.pd-history@1` definition is bound to predicted/actual PD occurrences; the EAD
ratio references `anz.ead-history@1` instead. Percent conversion is one reusable
definition shared by four financial fields. Readers never select those meanings.

```text
run config                         source declarations + reusable definitions
    |                                              |
    +-------- run.py supplies physical ops ---------+
                       |
                capture -> saved snapshot + evidence + payloads
                       |
       saved JSON + explicit interpretation selection
                       |
             shared conformance -> DuckDB -> readback
```

## Run and inspect

From the repository root:

```bash
uv run python spikes/metadata-driven-extraction/run.py
```

Every run retains a fresh labelled directory under `/tmp/opencode/`. Read
`summary.json`, `bronze-spike.json`, `baseline-attributes.json` and
`refined-attributes.json`. The two DuckDB files and JSON readbacks are retained;
`disposable-code/` preserves the code used for that run. The JSON snapshot records
physical parameters and selected definitions independently from live authoring files.

## Executed result

Latest full run: `/tmp/opencode/metadata-extraction-spike-zcze07kq/`.
Log: `/tmp/opencode/metadata-driven-spike-final.log`.

- **42 occurrences**, covering tables, headers, rows, columns, fields, cells and comments.
- Five financial values match the independent ANZ 2023 golden exactly, including
  lexical precision. Five selected paragraphs and the two matrix evidence summaries
  also agree with independently reviewed expectations.
- Matrix pre/post-framework headers survive; NZ's pre-framework cell remains a blank.
- Native percent conversion produces `0.0093`, `0.0077`, `0.1869`, `0.0140`;
  the EAD ratio remains `1.01`. Original tokens remain available beside those values.
- PD history **2018–2022**, EAD history **2018–2023**, LGD history **2017–2021** and
  separate outcome cutoffs survive persisted attribute readback.
- A deliberately partial actual-LGD `loss_basis` interpretation is enriched from
  unresolved to source-supported **average realised losses**, with explicit override
  of its earlier revision and retained comment evidence. All five persisted numbers
  remain identical. This is an illustrative interpretation, not a production mapping
  or a newly approved canonical LGD definition.

A separate fresh Python process loaded only saved Bronze and the saved interpretation
selection and regenerated `saved-only.duckdb`. It opened **zero PDFs** and imported
neither `pdfplumber`, `anz_2023` nor `physical`. The 42 occurrences and revised meaning
survived. Evidence: `/tmp/opencode/metadata-driven-spike-saved-only.log`.

The first execution exposed a consumer declaration mistake: Decimal casts require an
explicit rounding option in the pinned API. Supplying `rounding="to_zero"` fixed it.
No dependency workaround was added. Existing native type-normalisation diagnostics
are emitted before the successful run.

## What this establishes, and what remains unproven

The physical/configuration boundary works for both a regular row and a troublesome
matrix. Shared operations consume declared applicability rather than importing bank
rules. Saved metadata is sufficient for this reconformance path without either the
PDF or source-authoring code. Role and contextual assertions resolve for nonnumeric
occurrences through the same composition machinery.

This is intentionally a partial source selection, not the full ANZ Bronze contract.
The production codec, complete four-bank migration, master publication and domain
projections are not exercised. Addresses are local to this one labelled bundle;
cross-bundle revision/identity handling is not proven. It uses source-supported
percent/ratio conversion, not a complete unit or missing-token catalogue.

The existing `compose_field` is reused through a lightweight structural input view.
This demonstrates shared composition, but does not implement a production all-kind
catalogue codec or its reference vocabulary. Temporal assertions use simple named
attributes here; the final typed temporal bindings remain a design obligation.
Original text is retained, while physical matrix text assembly preserves reading
order rather than byte-for-byte PDF whitespace.

**Binding inspection beyond ANZ:** CBA's overlay would bind one comment both to the
applicable LGD occurrences and a separate numeric note cell; its 2022 panels would
omit those bindings. NAB's main/RBNZ rows would bind their own population/floor
definitions to the relevant fields/cells. Neither calls for another conformance
operation. These two are interface inspections, not executed capture proofs.

Review the ownership and call shape before any implementation plan. If accepted,
production work should be written afresh against the approved design and independent
source expectations, not by extending or wrapping tests around this spike.
