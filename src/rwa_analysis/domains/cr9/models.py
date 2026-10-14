"""Flat CR9 tables; repeated source evidence remains independently addressable."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from mountainash.relations.core.relation_api.relation import Relation

from rwa_analysis.domains.cr6.models import RowIdentity, SilverSegment, SourceLocation

RATES = (
    "weighted_average_pd",
    "arithmetic_average_pd",
    "historical_annual_default_rate",
)
COUNTS = (
    "previous_year_borrower_count",
    "current_year_borrower_count",
    "defaulted_borrower_count",
    "new_defaulted_borrower_count",
)
MEASURES = (*RATES, *COUNTS)


@dataclass(frozen=True)
class Cr9Output:
    observations: Relation
    contexts: Relation
    context_qualifications: Relation
    context_evidence: Relation
    fields: Relation
    field_qualifications: Relation
    field_mappings: Relation
    attributes: Relation
    attribute_evidence: Relation
    attribute_decisions: Relation
    relationships: Relation
    relationship_evidence: Relation
    temporal_descriptors: Relation
    temporal_bindings: Relation
    temporal_evidence: Relation


@dataclass(frozen=True)
class SilverObservation(SilverSegment, RowIdentity):
    weighted_average_pd: Decimal | None
    arithmetic_average_pd: Decimal | None
    historical_annual_default_rate: Decimal | None
    previous_year_borrower_count: int | None
    current_year_borrower_count: int | None
    defaulted_borrower_count: int | None
    new_defaulted_borrower_count: int | None


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
    publication_date: date | None
    source_template: str
    source_title: str
    source_portfolio_label: str
    reporting_entity_value: str | None
    reporting_entity_status: str
    consolidation_scope_value: str | None
    consolidation_scope_status: str
    regulatory_scope_value: str | None
    regulatory_scope_status: str
    geography_value: str | None
    geography_status: str
    currency_value: str | None
    currency_status: str


@dataclass(frozen=True)
class SilverRelationship:
    silver_revision_id: str
    relationship_id: str
    context_id: str
    parent_observation_id: str
    parent_field_key: str | None
    child_observation_id: str
    child_field_key: str | None
    source_relationship_ref: str
    source_label: str
    relationship_kind: str
    exhaustive: bool | None
    mutually_exclusive: bool | None


@dataclass(frozen=True)
class SilverTemporalDescriptor:
    silver_revision_id: str
    descriptor_id: str
    context_id: str
    source_descriptor_ref: str
    source_label: str
    point: str | None
    point_status: str
    start: str | None
    start_status: str
    end: str | None
    end_status: str
    duration_amount: Decimal | None
    duration_unit: str | None
    duration_status: str


@dataclass(frozen=True)
class SilverTemporalBinding:
    silver_revision_id: str
    observation_id: str
    field_key: str
    role: str
    descriptor_id: str


@dataclass(frozen=True)
class TemporalEvidence(SourceLocation):
    silver_revision_id: str
    descriptor_id: str
    position: int
