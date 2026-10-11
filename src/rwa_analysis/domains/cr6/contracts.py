"""Dataclass-derived CR6 declarations, augmented with native field contracts."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Literal, get_args, get_origin, get_type_hints

import mountainash as ma
from mountainash.core.dtypes import DecimalDtype
from mountainash.typespec.extraction import extract_from_dataclass
from mountainash.typespec.spec import FieldConstraints
from mountainash.typespec.universal_types import UniversalType

from .models import (
    AttributeDecision,
    AttributeEvidence,
    ContextEvidence,
    ContextQualification,
    FieldAttribute,
    FieldMapping,
    FieldQualification,
    RelationshipEvidence,
    RowIdentity,
    SilverContext,
    SilverField,
    SilverObservation,
    SilverObservationRelationship,
)

MONEY = DecimalDtype(16, 2)
SMALL = DecimalDtype(16, 8)
MEASURES = {
    "on_balance_amount": MONEY,
    "off_balance_amount": MONEY,
    "mean_ccf_fraction": SMALL,
    "ead_amount": MONEY,
    "mean_pd_fraction": SMALL,
    "mean_lgd_fraction": SMALL,
    "mean_maturity_years": SMALL,
    "rwa_amount": MONEY,
    "rwa_density_fraction": SMALL,
    "regulatory_expected_loss_amount": MONEY,
    "provision_amount": MONEY,
    "lower_fraction": SMALL,
    "upper_fraction": SMALL,
}


def model_spec(model, *, decimals=None, keys=()):
    """Augment flat dataclass schemas with declared decimals, literals and keys."""
    spec = extract_from_dataclass(model)
    hints = get_type_hints(model)
    augmented = []
    for field in spec.fields:
        hint = hints[field.name]
        if type(None) in get_args(hint):
            hint = next(t for t in get_args(hint) if t is not type(None))
        if hint is Decimal:
            field = replace(
                field,
                type=UniversalType.NUMBER,
                dtype=decimals[field.name],
                rounding="to_zero",
            )
        elif get_origin(hint) is Literal:
            field = replace(
                field,
                type=UniversalType.STRING,
                constraints=FieldConstraints(enum=list(get_args(hint))),
            )
        if field.name in keys:
            field = replace(
                field,
                constraints=replace(
                    field.constraints or FieldConstraints(), required=True
                ),
            )
        augmented.append(field)
    return replace(
        spec, fields=augmented, primary_key=list(keys) or None, missing_values=[]
    )


IDENTITY_SPEC = model_spec(RowIdentity, keys=("observation_id",))


@dataclass(frozen=True)
class TableDeclaration:
    member: str
    table: str
    model: type
    spec: ma.TypeSpec


def table(member, name, model, keys):
    spec = model_spec(model, decimals=MEASURES, keys=keys)
    return TableDeclaration(member, name, model, spec)


TABLES = (
    table(
        "observations",
        "cr6_observations",
        SilverObservation,
        ("silver_revision_id", "observation_id"),
    ),
    table(
        "fields",
        "cr6_fields",
        SilverField,
        ("silver_revision_id", "observation_id", "field_key"),
    ),
    table(
        "relationships",
        "cr6_relationships",
        SilverObservationRelationship,
        ("silver_revision_id", "relationship_id"),
    ),
    table(
        "contexts", "cr6_contexts", SilverContext, ("silver_revision_id", "context_id")
    ),
    table(
        "context_qualifications",
        "cr6_context_qualifications",
        ContextQualification,
        ("silver_revision_id", "context_id", "member", "position"),
    ),
    table(
        "context_evidence",
        "cr6_context_evidence",
        ContextEvidence,
        ("silver_revision_id", "context_id", "position"),
    ),
    table(
        "field_qualifications",
        "cr6_field_qualifications",
        FieldQualification,
        ("silver_revision_id", "observation_id", "field_key", "position"),
    ),
    table(
        "field_mappings",
        "cr6_field_mappings",
        FieldMapping,
        ("silver_revision_id", "observation_id", "field_key", "position"),
    ),
    table(
        "attributes",
        "cr6_attributes",
        FieldAttribute,
        (
            "silver_revision_id",
            "observation_id",
            "field_key",
            "name",
            "assertion_index",
        ),
    ),
    table(
        "attribute_evidence",
        "cr6_attribute_evidence",
        AttributeEvidence,
        (
            "silver_revision_id",
            "observation_id",
            "field_key",
            "name",
            "assertion_index",
            "position",
        ),
    ),
    table(
        "attribute_decisions",
        "cr6_attribute_decisions",
        AttributeDecision,
        (
            "silver_revision_id",
            "observation_id",
            "field_key",
            "name",
            "assertion_index",
            "position",
        ),
    ),
    table(
        "relationship_evidence",
        "cr6_relationship_evidence",
        RelationshipEvidence,
        ("silver_revision_id", "relationship_id", "position"),
    ),
)
