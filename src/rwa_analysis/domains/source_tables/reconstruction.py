"""Source-oriented frames from persisted values, with associated queryable metadata."""

from dataclasses import dataclass, fields

import mountainash as ma
import polars as pl

from .models import SourceTableOutput


@dataclass(frozen=True)
class ReconstructedSourceTable:
    frame: pl.DataFrame
    metadata: SourceTableOutput


def _owners(pairs, kind_column="owner_kind", id_column="owner_id"):
    predicate = ma.lit(False)
    for kind, key in sorted(pairs):
        predicate = predicate | (
            (ma.col(kind_column) == kind) & (ma.col(id_column) == key)
        )
    return predicate


def _table_metadata(output, table):
    tid, bundle = table["table_id"], table["bundle_key"]
    links = output.occurrence_links.filter(
        (ma.col("table_id") == tid) | (ma.col("table_id") == bundle)
    ).to_dicts()
    reachable = set()
    for link in links:
        if (
            link["table_id"] == bundle
            and link["target_bundle_key"] == bundle
            and link["target_scope"] == table["dataset_id"]
        ):
            reachable.add((link["owner_kind"], link["owner_id"]))
        if (
            link["table_id"] == tid
            and link["target_bundle_key"] == bundle
            and link["target_scope"] is None
        ):
            reachable.add((link["target_kind"], link["target_id"]))
    while True:
        added = {
            (link["target_kind"], link["target_id"])
            for link in links
            if link["table_id"] == bundle
            and (link["owner_kind"], link["owner_id"]) in reachable
            and link["target_bundle_key"] == bundle
            and link["target_scope"] is None
        }
        if added <= reachable:
            break
        reachable |= added
    bindings = output.context_bindings.filter(
        (ma.col("table_id") == tid)
        | ((ma.col("table_id") == bundle) & _owners(reachable))
    )
    context_ids = {row["context_revision_id"] for row in bindings.to_dicts()}
    reachable |= {("context_definition", key) for key in context_ids}
    references = output.references.filter(
        (ma.col("table_id") == bundle) & _owners(reachable)
    ).to_dicts()
    descriptor_ids = {
        r["target_id"] for r in references if r["target_kind"] == "temporal_descriptor"
    }
    reachable |= {("temporal_descriptor", key) for key in descriptor_ids}
    members = {}
    for f in fields(output):
        shared = ma.lit(False)
        if f.name == "occurrences":
            shared = _owners(reachable, "kind", "local_id")
        elif f.name == "contexts":
            shared = ma.col("context_revision_id").is_in(sorted(context_ids))
        elif f.name == "temporal_descriptors":
            shared = ma.col("descriptor_id").is_in(sorted(descriptor_ids))
        elif f.name in (
            "occurrence_links",
            "context_bindings",
            "references",
            "evidence",
            "source_attributes",
            "mapping_refs",
            "attributes",
            "attribute_evidence",
            "attribute_decisions",
        ):
            shared = _owners(reachable)
        members[f.name] = getattr(output, f.name).filter(
            (ma.col("table_id") == tid) | ((ma.col("table_id") == bundle) & shared)
        )
    return SourceTableOutput(**members)


def reconstruct_source_tables(
    output: SourceTableOutput,
) -> dict[str, ReconstructedSourceTable]:
    result = {}
    for table in output.tables.to_dicts():
        tid = table["table_id"]
        metadata = _table_metadata(output, table)
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
