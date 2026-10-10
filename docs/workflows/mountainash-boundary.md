# Mountainash boundary workflow

Task 1 establishes the install and transport boundary for the
[CR6 plan](../04.planning/superpowers/plans/2026-10-10-cr6-bronze-to-silver.md).
The [README](../../README.md) lists verified revisions and commands.

## Typed frames

Build Polars frames with explicit physical schemas, including all-null columns.
Call `rwa_analysis.contracts.frames.conform_frame(frame, spec)` with a Mountainash
TypeSpec declaring `missingValues: []`. Nonempty field-level missing sentinels
are rejected. Missing data is already represented by nulls at this boundary.

The verified public path is
`ma.relation(frame).conform(spec, apply_value_transforms=False).collect()` followed
by `ma.datacontract(spec).validate_datacontract(result)`. The generated contract
receives its own `Config` with `coerce=False`; the shared dependency base is not
mutated. Failed contracts or changed physical schemas raise `ValueError`.
This boundary does not parse numeric strings or determine semantic units.

The integration test owns the generic precision sentinel, an all-null variant,
and actual database closure/reopening using `IbisBackend`, Arrow and DuckDB.
Source-backed extraction expectations belong to their later extraction tests.

## Nested JSON transport

The pinned signatures are:

```python
write(sink, data, *, params=None) -> None
parse(source, *, params=None, output="arrow") -> list[ParseResult]
```

Use `FileSinkSpec(path=..., format="json")` and the matching `FileSourceSpec`.
`parse(..., output="pydata")` returns a list of parse results; for a single JSON
object its first result's `.data` is a **singleton list containing the object**,
not the bare object. The tested envelope is:

```json
{"records": [{"value": "0.0800", "missing_reason": null}, {"value": null, "missing_reason": "not_disclosed"}]}
```

The complete envelope, decimal text and null metadata survive. Task 4's wrapper
must validate result/cardinality and unwrap this documented shape before strict
schema decoding. No codec or Bronze persistence wrapper is implemented here.
Other envelope shapes still require their owning codec/round-trip checks.

## Clean installation findings

The approved published Mountainash replacement is compatible with the required
conformance call; the spike's unavailable disposable commit is unnecessary.
Polars 1.44.2 replaces 2.0.0 because the published package requires `<2`.
The six packages install from pinned Git sources through uv, with credentials
supplied by the operator's existing external Git configuration.

Ibis 12.0.0 emits `DeprecationWarning: fetch_arrow_table() is deprecated, use
to_arrow_table() instead` during the DuckDB round-trip (four warnings across the
two cases). Tests pass; warnings remain visible and dependencies are unmodified.
