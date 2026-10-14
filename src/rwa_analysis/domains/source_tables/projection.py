"""Native domain views of resolved source relations. No catalogue or source I/O."""

from dataclasses import dataclass
from decimal import Decimal

import mountainash as ma
import polars as pl
from mountainash.typespec.converters import to_polars_schema

from .contracts import DECLARATIONS


@dataclass(frozen=True)
class BindingRow:
    table_id: str
    cell_id: str
    observation_id: str
    source_record_id: str
    source_field_key: str
    field_key: str
    binding_ref: str


LOCATION = tuple(
    f"source_{n}"
    for n in ("document_id", "pdf_page", "printed_page", "location", "row", "column")
)
KNOWLEDGE = (
    "reporting_entity",
    "consolidation_scope",
    "regulatory_scope",
    "geography",
    "currency",
)


def project(source, bindings, domain, field_map, declarations):
    """Project the two existing domain contracts through their common source keys."""
    specs = {d.member: d.spec for d in declarations}

    def finish(name, relation=None):
        spec = specs[name]
        if relation is None:
            return ma.relation(pl.DataFrame(schema=to_polars_schema(spec)))
        return relation.select(*spec.field_names).conform(spec)

    selected = [
        BindingRow(
            f"{b.ref.bundle_key}/{b.ref.scope}",
            b.ref.local_id,
            f"{b.ref.bundle_key}/{b.ref.scope}/{b.record_id}",
            b.record_id,
            b.field_key,
            field_map[b.field_key],
            b.binding_ref or b.field_key,
        )
        for b in bindings
        if b.domain == domain
    ]
    if not selected:
        return {name: finish(name) for name in specs}
    addresses = ma.relation(selected)
    tables = (
        source.tables.join(addresses.select("table_id").unique(), on="table_id")
        .rename({"context_id": "source_context_id"})
        .with_columns(
            (ma.col("table_id") + ma.lit("/") + ma.col("source_context_id")).alias(
                "context_id"
            )
        )
    )
    table_keys = tables.select("table_id", "context_id")
    cells = source.cells.join(addresses, on=["table_id", "cell_id"])
    keys = addresses.select("table_id", "cell_id", "observation_id", "field_key")

    def references(kind, member):
        return source.references.filter(
            (ma.col("owner_kind") == kind) & (ma.col("member") == member)
        )

    def evidence(kind):
        return source.evidence.filter(ma.col("owner_kind") == kind)

    output = {}
    for name, original in (
        ("field_mappings", "mapping_refs"),
        ("attributes", "attributes"),
        ("attribute_evidence", "attribute_evidence"),
        ("attribute_decisions", "attribute_decisions"),
    ):
        relation = getattr(source, original).filter(ma.col("owner_kind") == "cell")
        relation = (
            relation.select(
                *(
                    c
                    for c in DECLARATIONS[original].spec.field_names
                    if c not in ("observation_id", "field_key")
                )
            )
            .rename({"owner_id": "cell_id"})
            .join(keys, on=["table_id", "cell_id"])
        )
        output[name] = finish(name, relation)

    contexts = tables
    for name in KNOWLEDGE:
        attrs = source.source_attributes.filter(
            (ma.col("owner_kind") == "context") & (ma.col("name") == name)
        ).select(
            "table_id",
            ma.col("value").alias(name + "_value"),
            ma.col("status").alias(name + "_status"),
        )
        contexts = contexts.join(attrs, on="table_id", how="left")
    temporal = source.temporal_bindings.join(keys, on=["table_id", "cell_id"])
    if domain == "cr6":
        dates = (
            temporal.filter(ma.col("role") == "measurement")
            .join(
                source.temporal_descriptors.select(
                    "table_id",
                    ma.col("descriptor_id").alias("descriptor_ref"),
                    "point",
                    "point_status",
                ),
                on=["table_id", "descriptor_ref"],
            )
            .filter(
                (ma.col("point_status") == "established")
                & (ma.col("point").str.len_chars() == 10)
            )
        )
        dates = dates.group_by("table_id").agg(
            ma.when(ma.col("point").n_unique() == 1)
            .then(ma.col("point").min())
            .otherwise(None)
            .str.to_date("%Y-%m-%d")
            .alias("observation_date")
        )
        contexts = contexts.join(dates, on="table_id", how="left")
    output["contexts"] = finish("contexts", contexts)
    cq = references("context", "qualification_refs").with_columns(
        ma.lit("context").alias("member")
    )
    parts = [
        cq.select("silver_revision_id", "table_id", "member", "position", "target_id")
    ]
    for name in KNOWLEDGE:
        part = (
            references("source_attribute", "qualification_refs")
            .join(
                tables.select(
                    "table_id",
                    (
                        ma.lit("context/")
                        + ma.col("source_context_id")
                        + ma.lit("/" + name)
                    ).alias("owner_id"),
                ),
                on=["table_id", "owner_id"],
            )
            .with_columns(ma.lit(name).alias("member"))
        )
        parts.append(
            part.select(
                "silver_revision_id", "table_id", "member", "position", "target_id"
            )
        )
    output["context_qualifications"] = finish(
        "context_qualifications",
        ma.concat(parts)
        .join(table_keys, on="table_id")
        .rename({"target_id": "qualification_ref"}),
    )
    output["context_evidence"] = finish(
        "context_evidence", evidence("context").join(table_keys, on="table_id")
    )

    fields = (
        cells.join(
            source.meanings.select(
                *(
                    c
                    for c in DECLARATIONS["meanings"].spec.field_names
                    if c not in ("silver_revision_id", "field_id")
                )
            ),
            on=["table_id", "cell_id"],
        )
        .join(
            source.fields.select("table_id", "field_id", "source_unit", "source_scale"),
            on=["table_id", "field_id"],
        )
        .join(
            tables.select(
                "table_id", "bundle_key", "output_version", "document_id", "dataset_id"
            ),
            on="table_id",
        )
    )
    fields = fields.join(
        evidence("cell")
        .filter(ma.col("member") == "source_reference")
        .select("table_id", ma.col("owner_id").alias("cell_id"), *LOCATION),
        on=["table_id", "cell_id"],
        how="left",
    )
    for name, column, target in (
        ("currency", "value_text", "currency_code"),
        ("result_unit", "value_revision_id", "result_unit_revision_ref"),
    ):
        attr = output["attributes"].filter(
            (ma.col("name") == name) & (ma.col("assertion_index") == 0)
        )
        selected_columns = ["observation_id", "field_key", ma.col(column).alias(target)]
        if name == "currency":
            selected_columns.append(ma.col("status").alias("currency_status"))
        fields = fields.join(
            attr.select(*selected_columns),
            on=["observation_id", "field_key"],
            how="left",
        )
    fields = fields.with_columns(
        ma.col("currency_status").fill_null("unresolved"),
        ma.col("field_id").alias("published_field_ref"),
        ma.col("source_scale").cast(pl.String),
        ma.col("unit_factor").cast(pl.String),
        ma.lit("selected_value" if domain == "cr6" else "selected").alias(
            "selection_role"
        ),
        ma.when(ma.col("unit_factor").is_null())
        .then(ma.lit("unresolved unit conversion"))
        .otherwise(None)
        .alias("conversion_reason"),
        ma.when(ma.col("value_state") == "source_missing")
        .then(ma.lit("source missing"))
        .when(ma.col("value_state") == "not_conformed")
        .then(ma.lit("unresolved unit conversion"))
        .otherwise(ma.lit("source value multiplied by selected unit factor"))
        .alias("transformation_description"),
    )
    output["fields"] = finish("fields", fields)

    # Ordered applicability: table, row/cell, field, and explicit temporal notes.
    qualification_parts = []
    for kind, owner_column, priority in (
        ("context", None, 0),
        ("cell", "cell_id", 1),
        ("field", "field_id", 2),
    ):
        refs = references(kind, "qualification_refs").select(
            "table_id",
            ma.col("owner_id").alias(owner_column or "_owner"),
            "position",
            ma.col("target_id").alias("qualification_ref"),
        )
        left = cells.select(
            "table_id",
            "observation_id",
            "field_key",
            "cell_id",
            "field_id",
            "silver_revision_id",
        )
        joined = left.join(
            refs, on=["table_id", owner_column] if owner_column else "table_id"
        )
        qualification_parts.append(
            joined.select(
                "silver_revision_id",
                "observation_id",
                "field_key",
                "qualification_ref",
                (ma.lit(priority * 100000) + ma.col("position")).alias("_order"),
            )
        )
    tq = references("temporal_descriptor", "qualification_refs").select(
        "table_id",
        ma.col("owner_id").alias("descriptor_ref"),
        ma.col("target_id").alias("qualification_ref"),
        ma.col("position").alias("_position"),
    )
    qualification_parts.append(
        temporal.join(tq, on=["table_id", "descriptor_ref"]).select(
            "silver_revision_id",
            "observation_id",
            "field_key",
            "qualification_ref",
            (ma.lit(300000) + ma.col("position") * 100 + ma.col("_position")).alias(
                "_order"
            ),
        )
    )
    qualifications = (
        ma.concat(qualification_parts)
        .sort("_order")
        .unique(
            subset=["observation_id", "field_key", "qualification_ref"], keep="first"
        )
        .with_columns(
            (
                ma.col("_order")
                .rank(method="ordinal")
                .over("observation_id", "field_key")
                - 1
            ).alias("position")
        )
    )
    output["field_qualifications"] = finish("field_qualifications", qualifications)

    row_keys = cells.select(
        "table_id",
        "silver_revision_id",
        "observation_id",
        "source_record_id",
        ma.col("row_ref").alias("source_row_ref"),
        "source_row_role",
    ).unique()
    roles = (
        output["attributes"]
        .filter((ma.col("name") == "row_role") & (ma.col("assertion_index") == 0))
        .group_by("observation_id")
        .agg(
            ma.when(
                (ma.col("value_text").n_unique() == 1)
                & (ma.col("status").n_unique() == 1)
            )
            .then(ma.col("value_text").min())
            .otherwise(None)
            .alias("canonical_row_role"),
            ma.when(
                (ma.col("value_text").n_unique() == 1)
                & (ma.col("status").n_unique() == 1)
            )
            .then(ma.col("status").min())
            .otherwise(ma.lit("conflicting"))
            .alias("row_role_status"),
        )
    )
    observations = (
        row_keys.join(table_keys, on="table_id")
        .join(roles, on="observation_id", how="left")
        .with_columns(ma.col("row_role_status").fill_null("unresolved"))
    )
    segments = (
        references("cell", "segment_refs")
        .filter(ma.col("position") == 0)
        .select(
            "table_id",
            ma.col("owner_id").alias("cell_id"),
            ma.col("target_id").alias("band_id"),
        )
        .join(keys, on=["table_id", "cell_id"])
        .select("table_id", "observation_id", "band_id")
        .unique()
    )
    band_locations = evidence("band").select(
        "table_id", ma.col("owner_id").alias("band_id"), *LOCATION
    )
    bands = source.bands.join(
        band_locations, on=["table_id", "band_id"], how="left"
    ).select(
        "table_id",
        "band_id",
        ma.col("segmentation_id").alias("source_segmentation_id"),
        ma.col("band_id").alias("source_band_ref"),
        "source_label",
        ma.col("kind").alias("category_kind"),
        "category",
        *(
            ma.when(ma.col("unit") == "%")
            .then(ma.col(n).cast(pl.Decimal(38, 8)) * ma.lit(Decimal("0.01")))
            .otherwise(None)
            .alias(n + "_fraction")
            for n in ("lower", "upper")
        ),
        "lower_inclusive",
        "upper_inclusive",
        "lower_status",
        "upper_status",
        *LOCATION,
    )
    observations = (
        observations.join(segments, on=["table_id", "observation_id"], how="left")
        .join(bands, on=["table_id", "band_id"], how="left")
        .with_columns(
            (ma.col("context_id") + ma.lit("/") + ma.col("band_id")).alias("segment_id")
        )
    )
    if domain == "cr9":
        fallback = fields.filter(
            ma.col("source_field_key") == "weighted_average_pd"
        ).select(
            "observation_id", *(ma.col(n).alias(n + "_fallback") for n in LOCATION)
        )
        observations = observations.join(
            fallback, on="observation_id", how="left"
        ).with_columns(
            *(
                ma.when(ma.col("band_id").is_not_null())
                .then(ma.col(n))
                .otherwise(ma.col(n + "_fallback"))
                .alias(n)
                for n in LOCATION
            )
        )
    for target in field_map.values():
        value = fields.filter(ma.col("field_key") == target).select(
            "observation_id",
            ma.coalesce(
                *(
                    ma.col(n)
                    for n in (
                        "normalised_amount",
                        "normalised_scalar",
                        "normalised_count",
                    )
                )
            ).alias(target),
        )
        observations = observations.join(value, on="observation_id", how="left")
    output["observations"] = finish("observations", observations)

    output.update(project_relationships(source, cells, tables, domain, finish))
    if domain == "cr9":
        descriptors = source.temporal_descriptors.join(
            table_keys, on="table_id"
        ).with_columns(
            ma.col("descriptor_id").alias("source_descriptor_ref"),
            (ma.col("table_id") + ma.lit("/temporal/") + ma.col("descriptor_id")).alias(
                "descriptor_id"
            ),
        )
        output["temporal_descriptors"] = finish("temporal_descriptors", descriptors)
        output["temporal_bindings"] = finish(
            "temporal_bindings",
            temporal.with_columns(
                (
                    ma.col("table_id") + ma.lit("/temporal/") + ma.col("descriptor_ref")
                ).alias("descriptor_id")
            ),
        )
        output["temporal_evidence"] = finish(
            "temporal_evidence",
            evidence("temporal_descriptor")
            .join(table_keys, on="table_id")
            .with_columns(
                (ma.col("table_id") + ma.lit("/temporal/") + ma.col("owner_id")).alias(
                    "descriptor_id"
                )
            ),
        )
    return output


def project_relationships(source, cells, tables, domain, finish):
    """Translate explicit row/field/cell endpoints without inventing aggregation."""
    refs = source.references.filter(ma.col("owner_kind") == "relationship")
    endpoints = []
    for kind, id_column, field in (
        ("row", "row_ref", False),
        ("field", "field_id", True),
        ("cell", "cell_id", True),
    ):
        endpoints.append(
            cells.select(
                "table_id",
                ma.lit(kind).alias("target_kind"),
                ma.col(id_column).alias("target_id"),
                "observation_id",
                "source_record_id",
                "row_ref",
                ma.col("field_id" if field else "row_ref").alias("source_endpoint_id"),
                (ma.col("field_key") if field else ma.lit(None).cast(pl.String)).alias(
                    "endpoint_field"
                ),
            ).unique()
        )
    endpoints = ma.concat(endpoints)

    def side(member):
        return (
            refs.filter(ma.col("member") == member)
            .join(endpoints, on=["table_id", "target_kind", "target_id"])
            .select(
                "table_id",
                ma.col("owner_id").alias("source_relationship_ref"),
                *(
                    ma.col(n).alias(member + "_" + n)
                    for n in (
                        "observation_id",
                        "source_record_id",
                        "row_ref",
                        "endpoint_field",
                        "target_id",
                        "target_kind",
                        "source_endpoint_id",
                    )
                ),
            )
        )

    edges = (
        side("parent")
        .join(side("children"), on=["table_id", "source_relationship_ref"])
        .filter(
            (
                (ma.col("parent_target_kind") != "field")
                & (ma.col("children_target_kind") != "field")
            )
            | (ma.col("parent_row_ref") == ma.col("children_row_ref"))
        )
    )
    scopes = refs.filter(
        (ma.col("member") == "scope") & (ma.col("target_kind") == "row")
    ).select(
        "table_id",
        ma.col("owner_id").alias("source_relationship_ref"),
        ma.col("target_id").alias("scoped_row"),
    )
    edges = (
        edges.join(scopes, on=["table_id", "source_relationship_ref"], how="left")
        .filter(
            ma.col("scoped_row").is_null()
            | (ma.col("scoped_row") == ma.col("parent_row_ref"))
        )
        .join(
            source.relationships.rename(
                {
                    "relationship_id": "source_relationship_ref",
                    "kind": "relationship_kind",
                }
            ),
            on=["table_id", "source_relationship_ref"],
        )
        .join(tables.select("table_id", "context_id"), on="table_id")
    )
    rid = (
        ma.col("context_id")
        + ma.lit("/")
        + ma.col("source_relationship_ref")
        + ma.lit("/")
    )
    if domain == "cr9":
        rid = (
            rid
            + ma.col("parent_source_record_id")
            + ma.lit("/")
            + ma.col("children_source_record_id")
            + ma.lit("/")
        )
    edges = edges.with_columns(
        (rid + ma.col("children_source_endpoint_id")).alias("relationship_id")
    ).rename(
        {
            "parent_endpoint_field": "parent_field_key",
            "children_endpoint_field": "child_field_key",
            "children_observation_id": "child_observation_id",
        }
    )
    evidence = (
        source.evidence.filter(ma.col("owner_kind") == "relationship")
        .rename({"owner_id": "source_relationship_ref"})
        .join(
            edges.select("table_id", "source_relationship_ref", "relationship_id"),
            on=["table_id", "source_relationship_ref"],
        )
    )
    return {
        "relationships": finish("relationships", edges),
        "relationship_evidence": finish("relationship_evidence", evidence),
    }
