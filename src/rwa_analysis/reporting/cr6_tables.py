"""Reconstruct source-unit tables from actual persisted Silver values."""

from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.normalization.cr6 import source_ids
from rwa_analysis.normalization.models import FIELD_MAP
from rwa_analysis.storage.manifests import load_manifest


def reconstruct_cr6(
    manifest_path: Path, project_root: Path, warehouse_path: Path
) -> dict[str, pl.DataFrame]:
    manifest, bundles, _, _ = load_manifest(
        manifest_path, project_root, verify_runtime=False
    )
    revision = manifest.request.revision_id
    with IbisBackend(
        dialect="duckdb", database=str(warehouse_path), read_only=True
    ) as db:
        marker = ma.relation(db.table("silver_publication", namespace="ops"))
        if marker.count_rows() != 1 or marker.item("silver_revision_id") != revision:
            raise ValueError(
                "Warehouse publication revision differs from selected manifest"
            )
        # Exact Decimal transport to the same Mountainash/Polars expression
        # backend used for conformance; no SQL or binary-float division.
        observations = (
            ma.relation(db.table("cr6_observations", namespace="silver"))
            .filter(ma.col("silver_revision_id") == revision)
            .to_polars()
        )
        fields = (
            ma.relation(db.table("cr6_fields", namespace="silver"))
            .filter(ma.col("silver_revision_id") == revision)
            .to_polars()
        )

    tables = {}
    for bundle in bundles:
        for ds in bundle.datasets:
            axes = {axis.id: axis for axis in ds.axes}
            source = pl.DataFrame(
                [
                    {
                        "observation_id": source_ids(bundle, ds, record),
                        "source_row": axes[record.source_row_ref].source_label,
                        "source_order": axes[record.source_row_ref].order,
                    }
                    for record in ds.records
                ],
                schema={
                    "observation_id": pl.String,
                    "source_row": pl.String,
                    "source_order": pl.Int64,
                },
            )
            relation = ma.relation(source).join(
                observations, on="observation_id", how="left"
            )
            expressions = [ma.col("source_row")]
            for published in ds.published_fields:
                binding = next(
                    b for b in ds.bindings if b.published_field_ref == published.id
                )
                target = FIELD_MAP[binding.typed_field_name]
                factor_name = f"{target}__factor"
                factors = (
                    ma.relation(fields)
                    .filter(ma.col("field_key") == target)
                    .select("observation_id", ma.col("unit_factor").alias(factor_name))
                )
                relation = relation.join(factors, on="observation_id", how="left")
                value = ma.col(target)
                if target != "reported_entity_count":
                    # Eight base-unit decimal places / a million needs fourteen
                    # source-unit places. Rates use this same exact working type.
                    value = value.cast(pl.Decimal(38, 14)) / ma.col(factor_name).cast(
                        pl.Decimal(38, 8)
                    )
                expressions.append(value.alias(published.source_label))
            tables[f"{bundle.bundle_key}/{ds.id}"] = (
                relation.sort("source_order").select(*expressions).to_polars()
            )
    return tables
