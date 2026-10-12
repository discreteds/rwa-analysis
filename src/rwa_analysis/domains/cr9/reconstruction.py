"""Source-unit numeric reconstruction from persisted CR9 values and factors."""

import mountainash as ma
import polars as pl

from rwa_analysis.extraction.cr9 import Cr9Dataset

from .metadata import ids
from .models import COUNTS, MEASURES


def reconstruct_cr9(output, bundles):
    tables = {}
    for bundle in bundles:
        for ds in bundle.datasets:
            if not isinstance(ds, Cr9Dataset):
                continue
            axes = {a.id: a for a in ds.metadata.axes}
            column_order = {
                name: min(
                    axes[ref].order
                    for binding in ds.metadata.bindings
                    if binding.typed_field_name == name
                    for ref in binding.column_refs
                )
                for name in MEASURES
            }
            source_fields = sorted(MEASURES, key=column_order.__getitem__)
            labels = ma.relation(
                [
                    {
                        "observation_id": ids(bundle, ds, row),
                        "source_row": axes[row.source_row_ref].source_label,
                        "source_order": axes[row.source_row_ref].order,
                    }
                    for row in ds.backtesting_rows
                ]
            )
            result = labels.join(
                output.observations.select("observation_id", *MEASURES),
                on="observation_id",
            )
            for name in MEASURES:
                factors = output.fields.filter(ma.col("field_key") == name).select(
                    "observation_id",
                    ma.col("unit_factor").cast(pl.Decimal(38, 12)).alias("factor"),
                )
                result = (
                    result.join(factors, on="observation_id")
                    .with_columns(
                        (ma.col(name).cast(pl.Decimal(38, 12)) / ma.col("factor"))
                        .cast(pl.Int64 if name in COUNTS else pl.Decimal(38, 12))
                        .alias(name)
                    )
                    .select("observation_id", "source_row", "source_order", *MEASURES)
                )
            tables[f"{bundle.bundle_key}/{ds.id}"] = (
                result.sort("source_order").select("source_row", *source_fields).to_polars()
            )
    return tables
