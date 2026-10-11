"""CR6 tabular models; source evidence remains in the extraction bundle."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from mountainash.relations.core.relation_api.relation import Relation

from rwa_analysis.catalogue.models import Assertion, EvidenceRef, RevisionRef
from rwa_analysis.extraction.models import Knowledge, SourceReference

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
    source_reference: SourceReference | None


@dataclass(frozen=True)
class SilverObservation(SilverSegment, SilverContext, RowIdentity):
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
class AssertionValue:
    """Typed storage representation of the catalogue's heterogeneous value."""

    text: str | None
    integer: int | None
    boolean: bool | None
    revision_ref: RevisionRef | None
    evidence_ref: EvidenceRef | None


@dataclass(frozen=True)
class StoredAssertion:
    value: AssertionValue
    status: str
    evidence_refs: tuple[EvidenceRef, ...]
    decision_refs: tuple[RevisionRef, ...]


@dataclass(frozen=True)
class StoredAttribute(StoredAssertion):
    name: str
    alternatives: tuple[StoredAssertion, ...]


def stored_assertion(assertion: Assertion) -> StoredAssertion:
    value = assertion.value
    return StoredAssertion(
        AssertionValue(
            value if type(value) is str else None,
            value if type(value) is int else None,
            value if type(value) is bool else None,
            value if isinstance(value, RevisionRef) else None,
            value if isinstance(value, EvidenceRef) else None,
        ),
        assertion.status,
        assertion.evidence_refs,
        assertion.decision_refs,
    )


@dataclass(frozen=True)
class SilverField:
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
    attributes: tuple[StoredAttribute, ...]
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
    mapping_revision_refs: tuple[str, ...]


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
