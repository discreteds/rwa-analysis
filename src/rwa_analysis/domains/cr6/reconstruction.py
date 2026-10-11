"""Reconstruct source-unit tables from supplied Silver values and source bindings."""

import mountainash as ma
import polars as pl

from rwa_analysis.extraction.cr6 import Cr6Dataset
from rwa_analysis.extraction.datasets import ExtractionBundle

from .models import FIELD_MAP, Cr6Output
from .pipeline import source_ids


def reconstruct_cr6(
    output: Cr6Output, bundles: tuple[ExtractionBundle, ...]
) -> dict[str, pl.DataFrame]:
    tables = {}
    for bundle in bundles:
        for ds in bundle.datasets:
            if not isinstance(ds, Cr6Dataset):
                continue
            axes = {axis.id: axis for axis in ds.metadata.axes}
            source = pl.DataFrame(
                [
                    {
                        "observation_id": source_ids(bundle, ds, record),
                        "source_row": axes[record.source_row_ref].source_label,
                        "source_order": axes[record.source_row_ref].order,
                    }
                    for record in ds.exposure_rows
                ],
                schema={
                    "observation_id": pl.String,
                    "source_row": pl.String,
                    "source_order": pl.Int64,
                },
            )
            relation = ma.relation(source).join(
                output.observations, on="observation_id", how="left"
            )
            expressions = [ma.col("source_row")]
            for published in ds.metadata.published_fields:
                binding = next(
                    b
                    for b in ds.metadata.bindings
                    if b.published_field_ref == published.id
                )
                target = FIELD_MAP[binding.typed_field_name]
                factor_name = f"{target}__factor"
                factors = output.fields.filter(ma.col("field_key") == target).select(
                    "observation_id", ma.col("unit_factor").alias(factor_name)
                )
                relation = relation.join(factors, on="observation_id", how="left")
                value = ma.col(target)
                if target != "reported_entity_count":
                    # Keep division wider than storage: one cent / one million
                    # remains 0.00000001 in the reconstructed source-unit table.
                    value = value.cast(pl.Decimal(38, 14)) / ma.col(factor_name).cast(
                        pl.Decimal(38, 8)
                    )
                expressions.append(value.alias(published.source_label))
            tables[f"{bundle.bundle_key}/{ds.id}"] = (
                relation.sort("source_order").select(*expressions).to_polars()
            )
    return tables
