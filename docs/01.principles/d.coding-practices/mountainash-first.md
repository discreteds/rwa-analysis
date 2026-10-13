# Mountainash-first implementation

> **Status:** AGREED
> **Scope:** implementation, configuration, conformance, storage, analytics
> **Basis:** approved strategic architecture and researcher request to consolidate
> Mountainash-first coding practices, 2026-10-11–12.

## Principle

Use Mountainash and its ecosystem wherever they provide the required capability.
Check existing project code and the pinned library APIs before writing another
implementation. Prefer direct supported calls and a small domain operation over
local frameworks, parallel dataframe pipelines or generic compatibility layers.

## Responsibility boundaries

| Work | Preferred implementation |
|---|---|
| Selection, filtering, joins, grouping, aggregates, arithmetic, casts, sorting and concatenation | Mountainash relations and expressions |
| Metadata projection, unnesting and collection expansion | Mountainash expressions over source/interpretation inputs |
| Tabular schemas and conformance | Dataclass-derived TypeSpecs with explicit domain augmentation; native conformance |
| Database reads/writes and transactions | `mountainash-data`; local DuckDB is the supported store |
| Structured file transport | `mountainash-files`, with the retained source codec where needed |
| Typed settings and file layering | `mountainash-settings`; no local YAML merge or second precedence system |
| PDF parsing, source objects, semantic interpretation and orchestration | Ordinary Python and existing focused libraries |
| Numerical capital/statistical kernels | NumPy/SciPy when implemented, receiving explicit numeric inputs independently of persistence |

Polars and Arrow are boundary/interchange formats, including typed empty relations,
supported dtype declarations and caller-facing dataframes. Their presence as imports
is not itself a defect. Express reusable tabular business logic through Mountainash
rather than processing in Polars and wrapping the finished result in `ma.relation`.

## Concrete coding practices

- Prepare dataset-sized source and mapping inputs, then transform relations. Do not
  create one relation per cell or reimplement the same conversions in Python loops.
  Python iteration for PDF interpretation, object assembly or semantic resolution
  has a different responsibility from columnar calculation.
- Keep relations through successive transformations. Materialise when the caller,
  file writer or connection lifetime needs it, not between every projection/join.
- Derive shared schema facts once. Domain declarations add the precision, scale,
  literal values and keys that the model/library cannot infer. Storage and master
  consume the same declared table inventory rather than repeating field lists.
- Use named domain outputs and explicit inputs. Separate settings, construction,
  domain operations and workflow sequencing. Under the approved
  [metadata-driven journey](../a.architecture/metadata-driven-extraction-and-conformance.md),
  source/layout bindings select physical operations, including bespoke code where
  needed; financial interpretation remains in the durable catalogue. This refines
  the earlier instruction that layout rules must live in complete bespoke extractors.
- Prefer composition and concrete functions/components. Add a protocol, base class,
  registry or package only for an actual shared responsibility and caller.
- Keep full replacement as the normal rebuild. Native transactions own atomic
  database publication; do not add a local transaction/workflow engine.
- Inspect supported APIs at the pinned revisions in `pyproject.toml`/`uv.lock`.
  Website examples and sibling checkouts may describe a different version.
- Check adjacent ecosystem packages before implementing a new I/O or configuration
  facility. A dependency being installed does not mean it needs to be exercised:
  no authentication or transport subsystem is required by the local workflow.
- Retire superseded entrypoints when callers move. Preserve source assets, saved
  formats and genuine compatibility requirements; avoid aliases for retired designs.

## Gaps and justified exceptions

Reproduce a required missing capability on the pinned dependency and distinguish
a dependency defect from a consumer declaration error. Record upstream findings in
Mountainash Central under its existing owner; do not open GitHub issues without
researcher approval. A local adaptation requires an explicit reason and researcher
agreement. Keep it at the affected boundary and track removal under project techdebt.

The existing approved exception is the nested metadata ingress adaptation in
[`metadata.py`](../../../src/rwa_analysis/domains/cr6/metadata.py): standard-library
`asdict()` plus full-record Polars inference. It does not move relational work out
of Mountainash. Its [debt item](../../04.planning/a.backlog/techdebt/metadata-ingress-and-nested-dataclasses.md)
requires revisiting source metadata schemas and removing that boundary.

## Numbers, validation and tests

Retain Decimal source quantities and explicit field-level units/scales. Use declared
money/rate/count types from the [semantic principle](../b.data-semantics/layered-metric-definitions.md).
Convert deliberately to floating point at a numerical-analysis boundary when needed,
including before division where fixed-point arithmetic would prematurely round
analytical weights. Do not silently replace stored observations with float results.

Trust framework arithmetic, casts and ordinary error propagation.
[Validation is separate and undefined](../c.extraction-and-validation/validation-is-a-separate-process.md):
Mountainash-first does not authorise invoking its validators, adding validation modes
or reinstating discarded precision/lifecycle guards.

Verify observable behaviour at its owning boundary: independent PDF goldens,
source-semantic conformance, persisted-value reconstruction and actual staging/master
round trips. Add tests for distinct regressions or contracts, not source-code spelling,
duplicated framework arithmetic or implementation inventories. Documentation changes
need link, status and example checks; they do not require new tests mirroring prose.

## References

- [Current architecture and code evidence](../../architecture.md).
- [Composed processing](../a.architecture/composed-processing-and-organisation-staging.md).
- [Strategic design](../../04.planning/superpowers/specs/2026-10-11-strategic-architecture-design.md).
