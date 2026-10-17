"""Retain four-bank adjustments and a separately identified NAB analytical bridge.

Run: uv run python -i examples/rwa_adjustments.py
Uses a fresh retained directory, the existing four-bank workflow and master readback.
"""

import json
from pathlib import Path
from runpy import run_path

import mountainash as ma


def retain_results(output, publication, directory):
    directory.mkdir(parents=True, exist_ok=True)
    source = output.source_tables
    table_ids = source.tables.filter(ma.col("dataset_id") == "rwa-adjustments").select(
        "table_id"
    )
    keys = ["silver_revision_id", "table_id", "cell_id"]
    amounts = source.meanings.join(table_ids, on="table_id")
    classifications = source.attributes.filter(
        (ma.col("owner_kind") == "cell") & (ma.col("name") == "qualification_meaning")
    ).select(
        "silver_revision_id",
        "table_id",
        ma.col("owner_id").alias("cell_id"),
        ma.col("value_text").alias("classification"),
    )
    inventory = amounts.join(classifications, on=keys).join(
        source.cells.select(
            *keys, "original_text", "displayed_precision", "missing_reason"
        ),
        on=keys,
    )
    inventory.to_polars().write_parquet(directory / "adjustment-observations.parquet")

    # One explicit research calculation, not a new source observation or Silver rule.
    bundle = "au/nab/2025-09-30/aps330"
    left_id, right_id = (
        bundle + "/rwa-adjustments",
        bundle + "/cr6-residential-mortgages",
    )
    inclusive = source.meanings.filter(
        (ma.col("table_id") == left_id) & (ma.col("cell_id") == "mortgage-overview-rwa")
    ).select("silver_revision_id", ma.col("normalised_amount").alias("inclusive_rwa"))
    exclusive = source.meanings.filter(
        (ma.col("table_id") == right_id)
        & (ma.col("cell_id") == "portfolio-aggregate/rwa")
    ).select("silver_revision_id", ma.col("normalised_amount").alias("cr6_rwa"))
    result = (
        inclusive.join(exclusive, on="silver_revision_id")
        .with_columns(
            (ma.col("inclusive_rwa") - ma.col("cr6_rwa")).alias("difference_amount")
        )
        .to_dicts()[0]
    )
    versions = {r["table_id"]: r["output_version"] for r in source.tables.to_dicts()}
    record = {
        "calculation": "nab-overview-minus-cr6-v1",
        "classification": "derived_reconciliation_difference",
        "currency": "AUD",
        "unit": "base currency units",
        "observation_date": "2025-09-30",
        "interpretation": "Difference between the reported AIRB mortgage overview RWA and CR6 RWA, which explicitly excludes overlays. Not an explicitly disclosed mortgage overlay allocation.",
        "master_revision": publication.revision,
        "master_manifest": str(publication.manifest_path),
        "inputs": [
            {
                "table_id": left_id,
                "cell_id": "mortgage-overview-rwa",
                "output_version": versions[left_id],
            },
            {
                "table_id": right_id,
                "cell_id": "portfolio-aggregate/rwa",
                "output_version": versions[right_id],
            },
        ],
        "result": result,
    }
    (directory / "nab-mortgage-rwa-bridge.json").write_text(
        json.dumps(record, default=str, indent=2) + "\n"
    )
    print(f"Retained adjustment observations and derived NAB bridge: {directory}")
    return inventory


if __name__ == "__main__":
    run = run_path(str(Path(__file__).with_name("four_bank_cr9.py")))
    output, publication = run["output"], run["master_publication"]
    inventory = retain_results(output, publication, run["data_root"] / "research")
    print(inventory.to_polars())
