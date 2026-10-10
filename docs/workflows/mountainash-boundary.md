# Mountainash boundary workflow

The implemented install and transport boundaries support the
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

[`test_mountainash_boundary.py`](../../tests/integration/test_mountainash_boundary.py)
owns exact domain Decimal/Int64 transport, its all-null variant, missing-sentinel
rejection, and database closure/reopening using `IbisBackend`, Arrow and DuckDB.
The four source golden tests under `tests/bronze/` own PDF extraction expectations,
including blank/dash values and their source-specific metadata.

## Nested JSON transport

[`storage/bronze.py`](../../src/rwa_analysis/storage/bronze.py) writes with
`write(FileSinkSpec(path=..., format="json"), envelope)` and reads the saved bytes
with `parse_bytes(raw, "json", output="pydata")`. The reader validates the original
JSON before Arrow normalization, then checks that the result's `.data` is a
singleton list containing the unchanged envelope.

[`test_bronze_storage.py`](../../tests/integration/test_bronze_storage.py) owns
complete nested JSON transport through all four exact, immutable saved-bundle
roundtrips. Its missing-cell-precision load regression and missing-field staging
regression protect against Arrow restoring omitted keys as nulls; staging also
owns failed-publication cleanup.
[`test_extraction_contract.py`](../../tests/test_extraction_contract.py) retains
the explicit `0.0800` Decimal exponent assertion and unknown nested-field rejection.

## Clean installation findings

The approved published Mountainash replacement is compatible with the required
conformance call; the spike's unavailable disposable commit is unnecessary.
Polars 1.44.2 replaces 2.0.0 because the published package requires `<2`.
The six packages install from pinned Git sources through uv, with credentials
supplied by the operator's existing external Git configuration.

Ibis 12.0.0 emits `DeprecationWarning: fetch_arrow_table() is deprecated, use
to_arrow_table() instead` during the DuckDB round-trip (four warnings across the
two cases). Tests pass; warnings remain visible and dependencies are unmodified.
