"""Seven row contracts and value-independent physical schemas.

Semantic assertions use typed structs, including conflict alternatives. Source
numeric strings in lineage are evidence; analytical values live in the wide row.
"""

from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

import polars as pl

from rwa_analysis.catalogue.models import (
    Assertion,
    EvidenceRef,
    RevisionRef,
    SemanticAttribute,
)
from rwa_analysis.extraction.models import Knowledge, SourceReference


@dataclass(frozen=True)
class SilverCandidate:
    revision_id: str
    tables: dict[str, pl.DataFrame]


@dataclass(frozen=True)
class SilverContext:
    silver_revision_id: str
    context_id: str
    bundle_key: str
    output_version: str
    document_id: str
    dataset_id: str
    source_context_id: str
    organisation_id: str
    document_date: date
    observation_date: date
    source_date_label: str
    source_template: str
    source_title: str
    source_portfolio_label: str
    reporting_entity: Knowledge
    consolidation_scope: Knowledge
    regulatory_scope: Knowledge
    geography: Knowledge
    currency: Knowledge
    qualification_refs: tuple[str, ...]
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class SilverSegment:
    silver_revision_id: str
    segment_id: str
    context_id: str
    source_segmentation_id: str
    source_band_ref: str
    source_label: str
    category_kind: str
    category: str | None
    lower_fraction: Decimal | None
    upper_fraction: Decimal | None
    lower_inclusive: bool | None
    upper_inclusive: bool | None
    lower_status: str
    upper_status: str
    source_reference: SourceReference


@dataclass(frozen=True)
class SilverCreditRiskExposureObservation:
    silver_revision_id: str
    observation_id: str
    context_id: str
    segment_id: str | None
    source_record_id: str
    source_row_ref: str
    source_row_role: str
    canonical_row_role: str | None
    row_role_status: str
    on_balance_amount: Decimal | None
    off_balance_amount: Decimal | None
    mean_ccf_fraction: Decimal | None
    ead_amount: Decimal | None
    mean_pd_fraction: Decimal | None
    reported_entity_count: int | None
    mean_lgd_fraction: Decimal | None
    mean_maturity_years: Decimal | None
    rwa_amount: Decimal | None
    rwa_density_fraction: Decimal | None
    regulatory_expected_loss_amount: Decimal | None
    provision_amount: Decimal | None


@dataclass(frozen=True)
class SilverFieldInterpretation:
    silver_revision_id: str
    observation_id: str
    field_key: str
    catalogue_release_id: str
    concept_revision_ref: str | None
    measure_revision_ref: str | None
    result_unit_revision_ref: str | None
    value_state: Literal["present", "source_missing", "not_conformed"]
    currency_code: str | None
    currency_status: str
    attributes: tuple[SemanticAttribute, ...]


@dataclass(frozen=True)
class AppliedMapping:
    silver_revision_id: str
    observation_id: str
    field_key: str
    catalogue_release_id: str
    mapping_revision_ref: str


@dataclass(frozen=True)
class SourceLineage:
    silver_revision_id: str
    observation_id: str
    field_key: str
    bundle_key: str
    output_version: str
    document_id: str
    dataset_id: str
    source_record_id: str
    source_field_key: str
    binding_ref: str
    published_field_ref: str
    source_value: str | None
    original_text: str
    displayed_precision: int | None
    missing_reason: str | None
    source_unit: str
    source_scale: str | None
    unit_factor: str | None
    selection_role: str
    conversion_reason: str | None
    transformation_description: str
    qualification_refs: tuple[str, ...]
    source_reference: SourceReference


@dataclass(frozen=True)
class SilverObservationRelationship:
    silver_revision_id: str
    relationship_id: str
    context_id: str
    parent_observation_id: str
    child_observation_id: str
    source_relationship_ref: str
    source_label: str
    relationship_kind: str
    exhaustive: bool | None
    mutually_exclusive: bool | None
    evidence: tuple[SourceReference, ...]


DECIMAL = pl.Decimal(38, 8)
STRINGS = pl.List(pl.String)
REFERENCE = pl.Struct(
    {
        "document_id": pl.String,
        "pdf_page": pl.Int64,
        "printed_page": pl.String,
        "location": pl.String,
        "row": pl.String,
        "column": pl.String,
    }
)
KNOWLEDGE = pl.Struct(
    {"value": pl.String, "status": pl.String, "qualification_refs": STRINGS}
)
REVISION_REF = pl.Struct({"kind": pl.String, "revision_id": pl.String})
EVIDENCE_REF = pl.Struct(
    {
        name: pl.String
        for name in ("bundle_key", "document_id", "dataset_id", "kind", "ref_id")
    }
)
ASSERTION_VALUE = pl.Struct(
    {
        "text": pl.String,
        "integer": pl.Int64,
        "boolean": pl.Boolean,
        "revision_ref": REVISION_REF,
        "evidence_ref": EVIDENCE_REF,
    }
)
ASSERTION = {
    "value": ASSERTION_VALUE,
    "status": pl.String,
    "evidence_refs": pl.List(EVIDENCE_REF),
    "decision_refs": pl.List(REVISION_REF),
}
ATTRIBUTES = pl.List(
    pl.Struct(
        ASSERTION | {"name": pl.String, "alternatives": pl.List(pl.Struct(ASSERTION))}
    )
)

FIELD_MAP = {
    "on_balance_exposure": "on_balance_amount",
    "off_balance_exposure": "off_balance_amount",
    "average_ccf": "mean_ccf_fraction",
    "ead": "ead_amount",
    "average_pd": "mean_pd_fraction",
    "reported_borrower_count": "reported_entity_count",
    "average_lgd": "mean_lgd_fraction",
    "average_maturity": "mean_maturity_years",
    "rwa": "rwa_amount",
    "rwa_density": "rwa_density_fraction",
    "regulatory_expected_loss": "regulatory_expected_loss_amount",
    "provisions": "provision_amount",
}


def strings(*names):
    return dict.fromkeys(names, pl.String)


FIELD_KEY = ["silver_revision_id", "observation_id", "field_key"]
SCHEMAS = {
    "contexts": strings(
        "silver_revision_id",
        "context_id",
        "bundle_key",
        "output_version",
        "document_id",
        "dataset_id",
        "source_context_id",
        "organisation_id",
    )
    | {"document_date": pl.Date, "observation_date": pl.Date}
    | strings(
        "source_date_label", "source_template", "source_title", "source_portfolio_label"
    )
    | dict.fromkeys(
        (
            "reporting_entity",
            "consolidation_scope",
            "regulatory_scope",
            "geography",
            "currency",
        ),
        KNOWLEDGE,
    )
    | {"qualification_refs": STRINGS, "evidence": pl.List(REFERENCE)},
    "segments": strings(
        "silver_revision_id",
        "segment_id",
        "context_id",
        "source_segmentation_id",
        "source_band_ref",
        "source_label",
        "category_kind",
        "category",
    )
    | {
        "lower_fraction": DECIMAL,
        "upper_fraction": DECIMAL,
        "lower_inclusive": pl.Boolean,
        "upper_inclusive": pl.Boolean,
    }
    | strings("lower_status", "upper_status")
    | {"source_reference": REFERENCE},
    "observations": strings(
        "silver_revision_id",
        "observation_id",
        "context_id",
        "segment_id",
        "source_record_id",
        "source_row_ref",
        "source_row_role",
        "canonical_row_role",
        "row_role_status",
    )
    | {
        target: pl.Int64 if target == "reported_entity_count" else DECIMAL
        for target in FIELD_MAP.values()
    },
    "interpretations": strings(
        *FIELD_KEY,
        "catalogue_release_id",
        "concept_revision_ref",
        "measure_revision_ref",
        "result_unit_revision_ref",
        "value_state",
        "currency_code",
        "currency_status",
    )
    | {"attributes": ATTRIBUTES},
    "applied_mappings": strings(
        *FIELD_KEY, "catalogue_release_id", "mapping_revision_ref"
    ),
    "lineage": strings(
        *FIELD_KEY,
        "bundle_key",
        "output_version",
        "document_id",
        "dataset_id",
        "source_record_id",
        "source_field_key",
        "binding_ref",
        "published_field_ref",
        "source_value",
        "original_text",
    )
    | {"displayed_precision": pl.Int64}
    | strings(
        "missing_reason",
        "source_unit",
        "source_scale",
        "unit_factor",
        "selection_role",
        "conversion_reason",
        "transformation_description",
    )
    | {"qualification_refs": STRINGS, "source_reference": REFERENCE},
    "relationships": strings(
        "silver_revision_id",
        "relationship_id",
        "context_id",
        "parent_observation_id",
        "child_observation_id",
        "source_relationship_ref",
        "source_label",
        "relationship_kind",
    )
    | {
        "exhaustive": pl.Boolean,
        "mutually_exclusive": pl.Boolean,
        "evidence": pl.List(REFERENCE),
    },
}
KEYS = {
    "contexts": ["silver_revision_id", "context_id"],
    "segments": ["silver_revision_id", "segment_id"],
    "observations": ["silver_revision_id", "observation_id"],
    "interpretations": FIELD_KEY,
    "applied_mappings": [*FIELD_KEY, "mapping_revision_ref"],
    "lineage": [
        *FIELD_KEY,
        "bundle_key",
        "output_version",
        "dataset_id",
        "source_record_id",
        "source_field_key",
    ],
    "relationships": ["silver_revision_id", "relationship_id"],
}


def tabular(value):
    """Encode immutable metadata into declared Arrow-compatible nested structs."""
    if isinstance(value, Assertion):
        v = value.value
        encoded = {
            "text": v if type(v) is str else None,
            "integer": v if type(v) is int else None,
            "boolean": v if type(v) is bool else None,
            "revision_ref": tabular(v) if isinstance(v, RevisionRef) else None,
            "evidence_ref": tabular(v) if isinstance(v, EvidenceRef) else None,
        }
        return {
            f.name: encoded if f.name == "value" else tabular(getattr(value, f.name))
            for f in fields(value)
        }
    if is_dataclass(value):
        return {f.name: tabular(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple):
        return [tabular(v) for v in value]
    return value


def frame(name, rows):
    return pl.DataFrame([tabular(row) for row in rows], schema=SCHEMAS[name])
