"""Source-oriented frames from persisted values, with associated queryable metadata."""

from dataclasses import dataclass, fields

import mountainash as ma
import polars as pl

from .models import SourceTableOutput


@dataclass(frozen=True)
class ReconstructedSourceTable:
    frame: pl.DataFrame
    metadata: SourceTableOutput


def reconstruct_source_tables(
    output: SourceTableOutput,
) -> dict[str, ReconstructedSourceTable]:
    result = {}
    for table in output.tables.to_dicts():
        tid = table["table_id"]
        metadata = SourceTableOutput(
            **{
                f.name: getattr(output, f.name).filter(ma.col("table_id") == tid)
                for f in fields(output)
            }
        )
        rows = metadata.axes.filter(ma.col("kind") == "row").sort("position").to_dicts()
        columns = (
            metadata.axes.filter(ma.col("kind") == "column").sort("position").to_dicts()
        )
        body_fields = metadata.fields.filter(
            ma.col("source_form") == "table_body"
        ).select("table_id", "field_id")
        body = metadata.cells.join(body_fields, on=["table_id", "field_id"]).to_dicts()
        by_position = {(c["row_ref"], c["column_ref"]): c for c in body}
        data = {
            "source_row_id": [r["axis_id"] for r in rows],
            "source_row": [r["source_label"] for r in rows],
        }
        for column in columns:
            values = []
            for row in rows:
                c = by_position.get((row["axis_id"], column["axis_id"]))
                values.append(
                    None
                    if c is None
                    else c[
                        {
                            "decimal": "source_number",
                            "integer": "source_count",
                            "text": "source_text",
                        }[c["value_kind"]]
                    ]
                )
            # A source-oriented column can mix lexical, integer and decimal cells.
            # Object is an output boundary in that case; persisted slots stay typed.
            types = {type(v) for v in values if v is not None}
            data[column["axis_id"]] = (
                pl.Series(column["axis_id"], values, dtype=pl.Object)
                if len(types) > 1
                else values
            )
        result[tid] = ReconstructedSourceTable(pl.DataFrame(data), metadata)
    return result
