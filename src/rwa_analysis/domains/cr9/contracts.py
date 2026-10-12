"""CR9 declarations reuse identical metadata rows, not CR6 numeric semantics."""

import mountainash as ma

from rwa_analysis.domains.cr6.contracts import SMALL, TableDeclaration, model_spec
from rwa_analysis.domains.cr6.models import (
    AttributeDecision,
    AttributeEvidence,
    ContextEvidence,
    ContextQualification,
    FieldAttribute,
    FieldMapping,
    FieldQualification,
    RelationshipEvidence,
    SilverField,
)

from .models import (
    RATES,
    SilverContext,
    SilverObservation,
    SilverRelationship,
    SilverTemporalBinding,
    SilverTemporalDescriptor,
    TemporalEvidence,
)

DECIMALS = dict.fromkeys(
    (*RATES, "lower_fraction", "upper_fraction", "duration_amount"), SMALL
)


def table(member, model, *keys):
    spec = model_spec(model, decimals=DECIMALS, keys=("silver_revision_id", *keys))
    return TableDeclaration(member, f"cr9_{member}", model, spec)


TABLES = (
    table("observations", SilverObservation, "observation_id"),
    table("contexts", SilverContext, "context_id"),
    table(
        "context_qualifications",
        ContextQualification,
        "context_id",
        "member",
        "position",
    ),
    table("context_evidence", ContextEvidence, "context_id", "position"),
    table("fields", SilverField, "observation_id", "field_key"),
    table(
        "field_qualifications",
        FieldQualification,
        "observation_id",
        "field_key",
        "position",
    ),
    table("field_mappings", FieldMapping, "observation_id", "field_key", "position"),
    table(
        "attributes",
        FieldAttribute,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
    ),
    table(
        "attribute_evidence",
        AttributeEvidence,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
        "position",
    ),
    table(
        "attribute_decisions",
        AttributeDecision,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
        "position",
    ),
    table("relationships", SilverRelationship, "relationship_id"),
    table("relationship_evidence", RelationshipEvidence, "relationship_id", "position"),
    table("temporal_descriptors", SilverTemporalDescriptor, "descriptor_id"),
    table(
        "temporal_bindings",
        SilverTemporalBinding,
        "observation_id",
        "field_key",
        "role",
        "descriptor_id",
    ),
    table("temporal_evidence", TemporalEvidence, "descriptor_id", "position"),
)

DECLARATIONS = {t.member: t for t in TABLES}


def relation(member, rows=()):
    """Flat object ingress, with typed empty output for an unselected domain."""
    if rows:
        return ma.relation(list(rows)).conform(DECLARATIONS[member].spec)
    import polars as pl
    from mountainash.typespec.converters import to_polars_schema

    return ma.relation(pl.DataFrame(schema=to_polars_schema(DECLARATIONS[member].spec)))
