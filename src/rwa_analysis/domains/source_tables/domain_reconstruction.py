"""Source-shaped domain frames from persisted domain numbers and retained bindings."""

import mountainash as ma
import polars as pl

from rwa_analysis.extraction.source_tables import SourceTable

from .legacy import adapt_legacy, domain_bindings


def reconstruct_domain(output, bundles, domain, field_map, counts):
    result = {}
    for bundle in bundles:
        bindings = tuple(b for b in domain_bindings(bundle) if b.domain == domain)
        for dataset in bundle.datasets:
            selected = [b for b in bindings if b.ref.scope == dataset.id]
            if not selected:
                continue
            table = (
                dataset if isinstance(dataset, SourceTable) else adapt_legacy(dataset)
            )
            axes = {a.id: a for a in table.metadata.axes}
            cells = {c.id: c for c in table.cells}
            by_record = {b.record_id: cells[b.ref.local_id].row_ref for b in selected}
            key = f"{bundle.bundle_key}/{dataset.id}"
            labels = ma.relation(
                [
                    {
                        "observation_id": f"{key}/{record}",
                        "source_row": axes[row].source_label,
                        "source_order": axes[row].order,
                    }
                    for record, row in by_record.items()
                ]
            )
            relation = labels.join(output.observations, on="observation_id", how="left")
            published = {f.id: f for f in table.metadata.published_fields}
            by_field = {cells[b.ref.local_id].field_ref: b for b in selected}
            fields = [f for f in table.metadata.published_fields if f.id in by_field]
            if domain == "cr9":
                fields.sort(
                    key=lambda f: (
                        axes[cells[by_field[f.id].ref.local_id].column_ref].order
                    )
                )
            expressions = [ma.col("source_row")]
            for field in fields:
                name = by_field[field.id].field_key
                target = field_map[name]
                factor_name = target + "__factor"
                factors = output.fields.filter(ma.col("field_key") == target).select(
                    "observation_id", ma.col("unit_factor").alias(factor_name)
                )
                relation = relation.join(factors, on="observation_id", how="left")
                value = ma.col(target)
                if domain == "cr9" or name not in counts:
                    value = value.cast(pl.Decimal(38, 14)) / ma.col(factor_name).cast(
                        pl.Decimal(38, 8)
                    )
                    if name in counts:
                        value = value.cast(pl.Int64)
                expressions.append(value.alias(published[field.id].source_label))
            result[key] = relation.sort("source_order").select(*expressions).to_polars()
    return result
