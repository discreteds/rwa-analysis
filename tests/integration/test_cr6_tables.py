"""Reconstructed source tables must reflect exact persisted values, not Bronze copies."""

import json
from decimal import Decimal

import pytest
from mountainash_data import IbisBackend


def test_persisted_numeric_mutations_and_absence_are_visible(published_cr6):
    from rwa_analysis.reporting.cr6_tables import reconstruct_cr6

    manifest, root, warehouse = published_cr6
    key = "au/cba/2025-06-30/aps330/cr6-residential-mortgages"
    oid = f"{key}/band-1"
    for amount, expected in (
        ("281509000000", Decimal(281509)),
        ("281508000000.01", Decimal("281508.00000001")),
        (None, None),
    ):
        with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
            raw = db.raw_driver_connection()
            if amount is None:
                raw.execute(
                    "DELETE FROM silver.cr6_observations WHERE observation_id = ?",
                    [oid],
                )
            else:
                raw.execute(
                    "UPDATE silver.cr6_observations SET ead_amount = ? WHERE observation_id = ?",
                    [amount, oid],
                )
        table = reconstruct_cr6(manifest, root, warehouse)[key]
        # Source position: label then on/off balance, CCF, EAD.
        assert table.height == 9
        assert table.row(0)[4] == expected


def test_actual_four_bank_tables_and_revision_guard(published_cr6, project_root):
    from rwa_analysis.reporting.cr6_tables import reconstruct_cr6
    from rwa_analysis.storage.silver import rebuild

    manifest, root, warehouse = published_cr6
    # Reusing a populated warehouse must preserve its schemas and rebuild tables.
    rebuild(manifest, root, warehouse)
    tables = reconstruct_cr6(manifest, root, warehouse)
    assert len(tables) == 4
    for bank, date in (
        ("cba", "2025-06-30"),
        ("westpac", "2025-09-30"),
        ("nab", "2025-09-30"),
        ("anz", "2025-09-30"),
    ):
        key = f"au/{bank}/{date}/aps330"
        golden = json.loads(
            (project_root / f"tests/bronze/{key}/golden.json").read_text()
        )
        ds = golden["datasets"][0]
        table = tables[f"{key}/{ds['id']}"]
        assert table.columns == [
            "source_row",
            *[f["source_label"] for f in ds["published_fields"]],
        ]
        axes = {a["id"]: a for a in ds["axes"]}
        for actual, record in zip(table.rows(), ds["records"], strict=True):
            expected = [axes[record["source_row_ref"]]["source_label"]]
            for field in ds["published_fields"]:
                binding = next(
                    b
                    for b in ds["bindings"]
                    if b["published_field_ref"] == field["id"]
                    and record["source_row_ref"] in b["row_refs"]
                )
                cell = record[binding["typed_field_name"]]
                expected.append(
                    Decimal(str(cell["value"])) if cell["value"] is not None else None
                )
            assert actual == tuple(expected)
        assert table.dtypes[6].is_integer()
    with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
        db.raw_driver_connection().execute(
            "UPDATE ops.silver_publication SET silver_revision_id = 'different'"
        )
    with pytest.raises(ValueError, match="revision"):
        reconstruct_cr6(manifest, root, warehouse)
