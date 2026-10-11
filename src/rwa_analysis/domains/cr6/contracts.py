"""Dataclass-derived CR6 declarations, augmented with native field contracts."""

from dataclasses import dataclass, is_dataclass, replace
from decimal import Decimal
from typing import Literal, get_args, get_origin, get_type_hints

import mountainash as ma
from mountainash.core.dtypes import DecimalDtype
from mountainash.typespec.extraction import extract_from_dataclass
from mountainash.typespec.spec import FieldConstraints
from mountainash.typespec.universal_types import UniversalType

from .models import (
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
    """Augment native derivation with nested shapes, literals and supplied decimals.

    No domain rules are inferred from field names. Callers declare keys and
    numeric types; nested dataclasses remain the sole field inventory.
    """
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
        elif is_dataclass(hint):
            field = replace(
                field, type=UniversalType.OBJECT, object_fields=model_spec(hint).fields
            )
        elif get_origin(hint) is tuple:
            inner = get_args(hint)[0]
            field = replace(
                field,
                type=UniversalType.ARRAY,
                item_object_fields=model_spec(inner).fields
                if is_dataclass(inner)
                else None,
                backend_type=None if is_dataclass(inner) else "List(String)",
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
CONTEXT_SPEC = model_spec(SilverContext, keys=("context_id",))


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
)
