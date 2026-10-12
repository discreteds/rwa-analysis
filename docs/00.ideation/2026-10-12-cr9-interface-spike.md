# Disposable CR9 interface spike

Status: **RUN — awaiting researcher shape review. Not production implementation.**

The [approved spec](../04.planning/superpowers/specs/2026-10-12-cr9-domain-design.md)
uses CR9 to find the shared interfaces without introducing analytical aggregation.
This spike is disposable, including its edits in `src/`. Do not merge it as the
implementation or use this branch as the base for real work.

## Inspect and run

- Code: `spikes/cr9-interface/run.py`.
- Hand-transcribed source input: `spikes/cr9-interface/source.json`.
- Shared resolution seam: `src/rwa_analysis/catalogue/resolve.py::compose_field`.
- Optional mapping-date experiment: `src/rwa_analysis/catalogue/models.py::MappingScope`.

```bash
uv sync --locked
uv run python spikes/cr9-interface/run.py /tmp/opencode/cr9-shape-review
```

The output directory contains an actual saved/reloaded Westpac CR6 bundle, the
separate saved CR9 shape input, `shape.duckdb` and `result.json`. Repeated runs replace
the disposable database. Nothing is written under the project's production data root.

## Shape demonstrated

```text
Real Westpac extractor -> saved CR6 -> existing Cr6Pipeline ---+
                                                              |
Saved, manually reviewed CR9 row -> concrete CR9 conformance ---+-> Candidate(cr6, cr9)
                              |                                      |
                  FieldOccurrence / explicit mapping                 |
                              |                         declared table inventory
                   shared compose_field                              |
                                                         DuckDB transaction
                                                               -> readback
```

CR6 still selects its mappings using its snapshot context. CR9 supplies a field
occurrence and an explicit source-unit mapping, without inventing an observation
date. Both use the same extracted assertion/conversion composer. CR9 canonical
measure semantics remain unresolved; conversion success does not imply equivalence.

The prototype's `TemporalDescriptor` stores partial date strings, duration and
component knowledge status. `TemporalBinding` links a field occurrence and temporal
role to a descriptor. IDs are dataset-scoped. Typed scalar rows enter Mountainash
directly; no new nested-metadata ingress adapter was needed for these flat examples.
Source quotations and spike interpretation notes are separate columns.

Named domain outputs and a combined declaration inventory drive one transaction.
CR9 has six prototype relations: observations, descriptors, bindings, field tags,
field-addressable relationships and document context. The context retains reporting
date independently of the datapoint's timing; publication date remains unknown.

## Executed evidence — 2026-10-12

Run artifacts: `/tmp/opencode/cr9-shape-0rjgzlux/`.

- **18 relations** written/read back: 12 CR6, six CR9.
- All 12 CR6 relations equal the baseline captured from the unmodified code before
  extracting the shared composer, including values and interpretation metadata.
- Westpac p.55 first-band source values reconstruct from DuckDB as 0.07% weighted
  PD, 0.07% arithmetic PD, counts 564613/571083, defaults 385, new defaults 7 and
  historical rate 0.06%.
- Eight temporal bindings survive storage. Weighted PD and EAD timing retain June
  2024; annual events retain 1 July 2024–30 June 2025; history retains ten years with
  unresolved endpoints. Other timing remains explicitly unresolved in this probe.
- The 7 new defaults remain a field-level subset of 385 within the same row.
- Additional in-memory shapes retain CBA's `2014` history start without a day or end,
  and ANZ's five-year descriptor and published aggregate 0.62% (fraction 0.0062).
- Ruff and whitespace checks pass. No tests added or suite run: this is a shape spike.

The first prototype arithmetic rounded small rates. Explicit working-scale casts
on both operands, matching the existing CR6 conversion pattern, corrected the
source-shaped readback. Likewise native ingress accepts the supplied flat dataclass
lists; passing a tuple directly did not work. Both were consumer-side corrections,
not evidence of a new upstream defect. Schema derivation still logs the existing
Decimal/Literal warnings before explicit augmentation supplies their declarations.

## Deliberate limits and review decision

This probes shared resolution and persisted data shape, not the entire approved
delivery scope. The CR9 input is neither production Bronze nor a golden fixture;
there is no mixed-domain codec or PDF extractor. It supplies one reviewed row, no
missing-cell cases, and explicit local conversion mappings rather than an approved
CR9 catalogue. Full source objects, evidence collections and domain dispatch remain
implementation work. Additional CBA/ANZ shapes are not persisted publications.

The existing CR6 metadata adapter and constructor checks remain in place. Optional
scope bounds are a local experiment only; the spike does not establish every mapping
containment or correction case. No aggregation, historical-series selection or new
runtime validation was introduced.

**Recommendation:** retain the small field-occurrence/composer seam, temporal
descriptor/binding pair and named outputs with a shared table inventory. No new
pipeline protocol or plugin engine was needed for this path. Review these interfaces
and data flow; if approved, plan the production work fresh from `develop`, with
independent source goldens and complete domain metadata. Do not polish this spike
into production or wrap tests around it as the implementation.
