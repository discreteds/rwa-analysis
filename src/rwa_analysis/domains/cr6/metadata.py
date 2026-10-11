"""Normalise metadata with Mountainash expressions.

Temporary object ingress: see docs/04.planning/a.backlog/techdebt/
metadata-ingress-and-nested-dataclasses.md. Revisit the nested source schemas
and remove this asdict/full-inference boundary rather than generalising it.
"""

from dataclasses import asdict, fields

import mountainash as ma
import polars as pl
from mountainash.typespec.converters import to_polars_schema

from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef

from .contracts import TABLES

DECLARATIONS = {table.member: table for table in TABLES}
FIELD_KEY = ("observation_id", "field_key")
ATTRIBUTE_KEY = (*FIELD_KEY, "name", "assertion_index")
KNOWLEDGE = (
    "reporting_entity",
    "consolidation_scope",
    "regulatory_scope",
    "geography",
    "currency",
)


def record(value):
    return asdict(value)


def source(records):
    # Full inference also preserves columns whose first non-null is after row 100.
    return ma.relation(pl.DataFrame(records, infer_schema_length=None))


def finish(member, relation=None):
    spec = DECLARATIONS[member].spec
    if relation is None:
        return ma.relation(pl.DataFrame(schema=to_polars_schema(spec)))
    return (
        relation.with_columns(ma.lit("").alias("silver_revision_id"))
        .select(*spec.field_names)
        .conform(spec)
    )


def ordered(values):
    return [{"position": i, "item": value} for i, value in enumerate(values)]


def children(member, records, keys, column, *, prefix="", renames=None):
    """Expand an ordered source collection, retaining its owning row's keys."""
    parents = [
        {**{key: row[key] for key in keys}, column: ordered(row[column])}
        for row in records
        if row[column]
    ]
    if not parents:
        return finish(member)
    relation = source(parents).explode(column).unnest(column, separator="")
    if prefix:
        name = prefix.removesuffix("_")
        relation = relation.rename({"item": name}).unnest(name, separator="_")
    else:
        relation = relation.unnest("item", separator="")
    if renames:
        relation = relation.rename(renames)
    return finish(member, relation)


def context_tables(records):
    if not records:
        return {
            name: finish(name)
            for name in ("contexts", "context_evidence", "context_qualifications")
        }
    contexts = (
        source(records)
        .unnest("context", separator="")
        .unnest(*KNOWLEDGE, separator="_")
    )
    qualifications = []
    evidence = []
    for row in records:
        ctx = row["context"]
        evidence.append({"context_id": row["context_id"], "evidence": ctx["evidence"]})
        for member in ("context", *KNOWLEDGE):
            refs = (ctx if member == "context" else ctx[member])["qualification_refs"]
            qualifications.append(
                {
                    "context_id": row["context_id"],
                    "member": member,
                    "refs": [{"qualification_ref": ref} for ref in refs],
                }
            )
    return {
        "contexts": finish("contexts", contexts.rename({"id": "source_context_id"})),
        "context_evidence": children(
            "context_evidence", evidence, ("context_id",), "evidence", prefix="source_"
        ),
        "context_qualifications": children(
            "context_qualifications", qualifications, ("context_id", "member"), "refs"
        ),
    }


def reference_value(value, model):
    # The catalogue's heterogeneous value union needs an explicit storage tag.
    return (
        record(value)
        if isinstance(value, model)
        else dict.fromkeys(f.name for f in fields(model))
    )


def assertion_inputs(oid, target, meaning):
    """Expose typed union branches; relational projection owns their columns."""
    for position, attribute in enumerate(meaning.attributes):
        for index, assertion in enumerate((attribute, *attribute.alternatives)):
            value = assertion.value
            yield {
                "observation_id": oid,
                "field_key": target,
                "name": attribute.name,
                "assertion_index": index,
                "position": position,
                "status": assertion.status,
                "value_text": value if type(value) is str else None,
                "value_integer": value if type(value) is int else None,
                "value_boolean": value if type(value) is bool else None,
                "revision": reference_value(value, RevisionRef),
                "reference": reference_value(value, EvidenceRef),
                "evidence": [record(e) for e in assertion.evidence_refs],
                "decisions": [record(d) for d in assertion.decision_refs],
            }


def attribute_tables(records):
    if not records:
        return {
            name: finish(name)
            for name in ("attributes", "attribute_evidence", "attribute_decisions")
        }
    relation = (
        source(records)
        .rename({"revision": "value"})
        .unnest("value", separator="_")
        .rename({"value_kind": "value_revision_kind"})
        .rename({"reference": "value"})
        .unnest("value", separator="_")
        .rename({"value_kind": "value_ref_kind"})
    )
    return {
        "attributes": finish("attributes", relation),
        "attribute_evidence": children(
            "attribute_evidence", records, ATTRIBUTE_KEY, "evidence"
        ),
        "attribute_decisions": children(
            "attribute_decisions",
            records,
            ATTRIBUTE_KEY,
            "decisions",
            renames={"kind": "decision_kind", "revision_id": "decision_revision_id"},
        ),
    }


def field_tables(records):
    if not records:
        return {
            name: finish(name)
            for name in ("fields", "field_qualifications", "field_mappings")
        }
    relation = (
        source(records)
        .unnest("cell", separator="")
        .rename({"source_reference": "source"})
        .unnest("source", separator="_")
        .unnest("binding", separator="_")
        .unnest("published", separator="_")
        .rename(
            {
                "value": "source_value",
                "binding_id": "binding_ref",
                "published_id": "published_field_ref",
                "published_source_unit": "source_unit",
                "published_source_scale": "source_scale",
            }
        )
    )
    state = (
        ma.when(ma.col("source_value").is_null())
        .then(ma.lit("source_missing"))
        .when(ma.col("unit_factor").is_null())
        .then(ma.lit("not_conformed"))
        .otherwise(ma.lit("present"))
    )
    relation = (
        relation.with_columns(state.alias("value_state"))
        .with_columns(
            ma.when(ma.col("value_state") == "not_conformed")
            .then(ma.lit("source unit/scale conversion unresolved or conflicting"))
            .otherwise(ma.lit(None))
            .alias("conversion_reason"),
            ma.lit("selected_value").alias("selection_role"),
        )
        .with_columns(
            ma.when(ma.col("value_state") == "source_missing")
            .then(ma.lit("source missing"))
            .when(ma.col("value_state") == "not_conformed")
            .then(ma.col("conversion_reason"))
            .otherwise(ma.lit("multiply source value by ") + ma.col("unit_factor"))
            .alias("transformation_description")
        )
    )
    return {
        "fields": finish("fields", relation),
        "field_qualifications": children(
            "field_qualifications", records, FIELD_KEY, "qualifications"
        ),
        "field_mappings": children(
            "field_mappings",
            records,
            FIELD_KEY,
            "mappings",
            renames={"revision_id": "mapping_revision_ref"},
        ),
    }


def relationship_tables(records):
    return {
        "relationships": finish(
            "relationships",
            source(records).rename(
                {"id": "source_relationship_ref", "kind": "relationship_kind"}
            )
            if records
            else None,
        ),
        "relationship_evidence": children(
            "relationship_evidence",
            records,
            ("relationship_id",),
            "evidence",
            prefix="source_",
        ),
    }
