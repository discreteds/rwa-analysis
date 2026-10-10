from decimal import Decimal

import mountainash as ma
import polars as pl
import pytest
from mountainash_data import IbisBackend
from mountainash_files import FileSinkSpec, FileSourceSpec, parse, write


@pytest.mark.parametrize("all_missing", [False, True])
def test_decimal_contract_and_persistent_roundtrip(tmp_path, all_missing):
    from rwa_analysis.contracts.frames import conform_frame

    frame = pl.DataFrame(
        {
            "id": ["present", "missing"],
            "amount": [Decimal("12345678901234567890.12345678"), None],
            "count": [742470, None],
        },
        schema={"id": pl.String, "amount": pl.Decimal(38, 8), "count": pl.Int64},
    )
    if all_missing:
        frame = frame.with_columns(
            pl.lit(None, dtype=pl.Decimal(38, 8)).alias("amount"),
            pl.lit(None, dtype=pl.Int64).alias("count"),
        )
    spec = ma.TypeSpec.from_frictionless(
        {
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "amount", "type": "number"},
                {"name": "count", "type": "integer"},
            ],
            "primaryKey": ["id"],
            "missingValues": [],
        }
    )
    result = conform_frame(frame, spec)
    path = str(tmp_path / "boundary.duckdb")
    with IbisBackend(dialect="duckdb", database=path) as db:
        db.create_table("sample", result.to_arrow())
    with IbisBackend(dialect="duckdb", database=path) as db:
        restored = pl.from_arrow(db.table("sample").to_pyarrow()).sort("id")
    assert restored.schema == frame.schema
    assert restored.equals(frame.sort("id"))


@pytest.mark.parametrize(
    "missing_declaration",
    [
        {},
        {"missingValues": ["NA"]},
        {"missingValues": [], "field_missing": ["NA"]},
    ],
)
def test_typed_boundary_rejects_missing_sentinels(missing_declaration):
    from rwa_analysis.contracts.frames import conform_frame

    field = {"name": "id", "type": "string"}
    if "field_missing" in missing_declaration:
        field["missingValues"] = missing_declaration["field_missing"]
    descriptor = {"fields": [field]}
    if "missingValues" in missing_declaration:
        descriptor["missingValues"] = missing_declaration["missingValues"]
    spec = ma.TypeSpec.from_frictionless(descriptor)
    with pytest.raises(ValueError, match="missingValues"):
        conform_frame(pl.DataFrame({"id": ["NA"]}), spec)


@pytest.mark.parametrize(
    "data",
    [
        {"id": ["same", "same"], "count": [1, 2]},
        {"id": ["first", "second"], "count": ["1", "2"]},
    ],
)
def test_typed_boundary_rejects_invalid_contract(data):
    from rwa_analysis.contracts.frames import conform_frame

    spec = ma.TypeSpec.from_frictionless(
        {
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "count", "type": "integer"},
            ],
            "primaryKey": ["id"],
            "missingValues": [],
        }
    )
    with pytest.raises(ValueError):
        conform_frame(pl.DataFrame(data), spec)


def test_nested_json_preserves_decimal_text_and_null_metadata(tmp_path):
    encoded = {
        "records": [
            {"value": "0.0800", "missing_reason": None},
            {"value": None, "missing_reason": "not_disclosed"},
        ]
    }
    path = str(tmp_path / "boundary.json")
    write(FileSinkSpec(path=path, format="json"), encoded)
    restored = parse(FileSourceSpec(path=path, format="json"), output="pydata")
    assert len(restored) == 1
    assert restored[0].data == [
        {
            "records": [
                {"value": "0.0800", "missing_reason": None},
                {"value": None, "missing_reason": "not_disclosed"},
            ]
        }
    ]
