"""Dataset-sized native conformance of captured source tables."""

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.occurrences import resolve_capture
from rwa_analysis.extraction.definitions import CapturedBundle
from rwa_analysis.extraction.models import OccurrenceRef

from .contracts import DECLARATIONS, TABLES, relation
from .metadata import capture_rows, source_rows
from .models import SourceTableOutput


class SourceTablePipeline:
    def conform(self, inputs, catalogue) -> SourceTableOutput:
        rows = {t.member: [] for t in TABLES}
        for loaded in inputs:
            resolved = resolve_capture(loaded, catalogue)
            for table in resolved.captured.bundle.datasets:
                meanings = {
                    c.id: resolved.meanings[
                        OccurrenceRef(loaded.bundle.bundle_key, table.id, "cell", c.id)
                    ]
                    for c in table.cells
                }
                source_rows(rows, resolved.captured, table, meanings, catalogue)
            if isinstance(loaded.bundle, CapturedBundle):
                capture_rows(rows, resolved)
        output = {name: relation(name, values) for name, values in rows.items()}
        if rows["cells"]:
            cells = output["cells"].select(
                "table_id", "cell_id", "source_number", "source_count"
            )
            joined = output["meanings"].join(cells, on=["table_id", "cell_id"])
            working = pl.Decimal(38, 16)
            product = ma.col("source_number").cast(working) * ma.col(
                "unit_factor"
            ).cast(working)
            output["meanings"] = (
                joined.with_columns(
                    ma.when(ma.col("result_kind") == "money")
                    .then(product)
                    .otherwise(None)
                    .cast(pl.Decimal(16, 2))
                    .alias("normalised_amount"),
                    ma.when(ma.col("result_kind") == "scalar")
                    .then(product)
                    .otherwise(None)
                    .cast(pl.Decimal(16, 8))
                    .alias("normalised_scalar"),
                    ma.when(ma.col("result_kind") == "count")
                    .then(
                        ma.col("source_count").cast(working)
                        * ma.col("unit_factor").cast(working)
                    )
                    .otherwise(None)
                    .cast(pl.Int64)
                    .alias("normalised_count"),
                )
                .select(*(f.name for f in DECLARATIONS["meanings"].spec.fields))
                .conform(DECLARATIONS["meanings"].spec)
            )
        return SourceTableOutput(**output)
