"""Reconstructed source tables must reflect exact persisted values, not Bronze copies."""

import json
from decimal import Decimal

from mountainash_data import IbisBackend


def test_persisted_numeric_mutations_and_absence_are_visible(published_cr6):
    session, publication = published_cr6[0]
    warehouse = publication.database
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
        table = session.reconstruct(publication)[key]
        # Source position: label then on/off balance, CCF, EAD.
        assert table.height == 9
        assert table.row(0)[4] == expected


def test_actual_four_bank_tables(published_cr6, project_root):
    from rwa_analysis.domains.cr6.reconstruction import reconstruct_cr6

    tables = {}
    for session, publication in published_cr6:
        # Reusing a populated warehouse must preserve its schemas and rebuild tables.
        manifest = session.silver.read_manifest(publication)
        candidate = session.conform(
            session.load_bronze(manifest.selection.bronze_refs),
            catalogue=manifest.selection.catalogue,
        )
        session.publish(candidate, revision=publication.revision)
        tables.update(
            reconstruct_cr6(
                session.silver.read(publication).cr6,
                session.silver.read_sources(publication),
            )
        )
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
