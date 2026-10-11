"""CR6 tabular models; source evidence remains in the extraction bundle."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from mountainash.relations.core.relation_api.relation import Relation

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


@dataclass(frozen=True)
class Cr6Output:
    observations: Relation
    fields: Relation
    relationships: Relation
    contexts: Relation
    context_qualifications: Relation
    context_evidence: Relation
    field_qualifications: Relation
    field_mappings: Relation
    attributes: Relation
    attribute_evidence: Relation
    attribute_decisions: Relation
    relationship_evidence: Relation


@dataclass(frozen=True)
class SourceNumbers:
    """Source-unit numeric projection, also used for selected conversion factors.

    Counts enter the common multiplication as exact Decimal coefficients and
    return to integer counts in Silver. Source values are never rounded here.
    """

    observation_id: str
    on_balance_exposure: Decimal | None
    off_balance_exposure: Decimal | None
    average_ccf: Decimal | None
    ead: Decimal | None
    average_pd: Decimal | None
    reported_borrower_count: Decimal | None
    average_lgd: Decimal | None
    average_maturity: Decimal | None
    rwa: Decimal | None
    rwa_density: Decimal | None
    regulatory_expected_loss: Decimal | None
    provisions: Decimal | None


@dataclass(frozen=True)
class RowIdentity:
    silver_revision_id: str
    observation_id: str
    context_id: str
    segment_id: str | None
    source_record_id: str
    source_row_ref: str
    source_row_role: str
    canonical_row_role: str | None
    row_role_status: str


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
class SourceLocation:
    source_document_id: str | None
    source_pdf_page: int | None
    source_printed_page: str | None
    source_location: str | None
    source_row: str | None
    source_column: str | None


@dataclass(frozen=True)
class ContextQualification:
    silver_revision_id: str
    context_id: str
    member: str
    position: int
    qualification_ref: str


@dataclass(frozen=True)
class ContextEvidence(SourceLocation):
    silver_revision_id: str
    context_id: str
    position: int


@dataclass(frozen=True)
class SilverSegment(SourceLocation):
    silver_revision_id: str
    segment_id: str | None
    context_id: str
    source_segmentation_id: str | None
    source_band_ref: str | None
    source_label: str | None
    category_kind: str | None
    category: str | None
    lower_fraction: Decimal | None
    upper_fraction: Decimal | None
    lower_inclusive: bool | None
    upper_inclusive: bool | None
    lower_status: str | None
    upper_status: str | None


@dataclass(frozen=True)
class SilverObservation(SilverSegment, RowIdentity):
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
class SilverField(SourceLocation):
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


@dataclass(frozen=True)
class FieldKey:
    silver_revision_id: str
    observation_id: str
    field_key: str


@dataclass(frozen=True)
class FieldQualification(FieldKey):
    position: int
    qualification_ref: str


@dataclass(frozen=True)
class FieldMapping(FieldKey):
    position: int
    mapping_revision_ref: str


@dataclass(frozen=True)
class AttributeKey(FieldKey):
    name: str
    assertion_index: int


@dataclass(frozen=True)
class FieldAttribute(AttributeKey):
    position: int
    status: str
    value_text: str | None
    value_integer: int | None
    value_boolean: bool | None
    value_revision_kind: str | None
    value_revision_id: str | None
    value_bundle_key: str | None
    value_document_id: str | None
    value_dataset_id: str | None
    value_ref_kind: str | None
    value_ref_id: str | None


@dataclass(frozen=True)
class AttributeEvidence(AttributeKey):
    position: int
    bundle_key: str
    document_id: str
    dataset_id: str
    kind: str
    ref_id: str


@dataclass(frozen=True)
class AttributeDecision(AttributeKey):
    position: int
    decision_kind: str
    decision_revision_id: str


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


@dataclass(frozen=True)
class RelationshipEvidence(SourceLocation):
    silver_revision_id: str
    relationship_id: str
    position: int
