"""Flat source-table rows. Source identity remains independent of interpretation."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from mountainash.relations.core.relation_api.relation import Relation

from rwa_analysis.domains.cr6.models import (
    AttributeDecision,
    AttributeEvidence,
    FieldAttribute,
    FieldMapping,
    SourceLocation,
)


@dataclass(frozen=True)
class TableKey:
    silver_revision_id: str
    table_id: str


@dataclass(frozen=True)
class TableRow(TableKey):
    position: int
    bundle_key: str
    output_version: str
    document_id: str
    organisation_id: str
    dataset_id: str
    context_id: str
    document_date: date
    publication_date: date | None
    source_date_label: str
    source_template: str
    source_title: str
    source_portfolio_label: str


@dataclass(frozen=True)
class FieldRow(TableKey):
    field_id: str
    position: int
    source_label: str
    source_unit: str
    source_scale: Decimal | None
    value_kind: str
    result_kind: str
    source_form: str


@dataclass(frozen=True)
class AxisRow(TableKey):
    axis_id: str
    kind: str
    source_label: str
    position: int


@dataclass(frozen=True)
class CellRow(TableKey):
    cell_id: str
    field_id: str
    position: int
    row_ref: str | None
    column_ref: str | None
    value_kind: str
    source_number: Decimal | None
    source_count: int | None
    source_text: str | None
    original_text: str
    displayed_precision: int | None
    missing_reason: str | None
    source_row_role: str | None = None
    source_value: str | None = None


@dataclass(frozen=True)
class ReferenceRow(TableKey):
    owner_kind: str
    owner_id: str
    member: str
    position: int
    target_kind: str
    target_id: str


@dataclass(frozen=True)
class SourceAttributeRow(TableKey):
    owner_kind: str
    owner_id: str
    name: str
    position: int
    value: str | None
    status: str


@dataclass(frozen=True)
class EvidenceRow(SourceLocation, TableKey):
    owner_kind: str
    owner_id: str
    member: str
    position: int


@dataclass(frozen=True)
class SegmentationRow(TableKey):
    segmentation_id: str
    source_dimension: str
    position: int


@dataclass(frozen=True)
class BandRow(TableKey):
    band_id: str
    segmentation_id: str
    source_label: str
    position: int
    kind: str
    unit: str
    lower: Decimal | None
    upper: Decimal | None
    lower_inclusive: bool | None
    upper_inclusive: bool | None
    lower_status: str
    upper_status: str
    category: str | None


@dataclass(frozen=True)
class QualificationRow(TableKey):
    qualification_id: str
    position: int
    source_text: str


@dataclass(frozen=True)
class RelationshipRow(TableKey):
    relationship_id: str
    position: int
    kind: str
    source_label: str
    exhaustive: bool | None
    mutually_exclusive: bool | None


@dataclass(frozen=True)
class TemporalRow(TableKey):
    descriptor_id: str
    position: int
    source_label: str
    point: str | None
    start: str | None
    end: str | None
    point_status: str
    start_status: str
    end_status: str
    duration_amount: Decimal | None
    duration_unit: str | None
    duration_status: str


@dataclass(frozen=True)
class TemporalBindingRow(TableKey):
    cell_id: str
    role: str
    descriptor_ref: str
    position: int


@dataclass(frozen=True)
class MeaningRow(TableKey):
    cell_id: str
    field_id: str
    catalogue_release_id: str
    concept_revision_ref: str | None
    measure_revision_ref: str | None
    result_kind: str
    unit_factor: Decimal | None
    normalised_amount: Decimal | None
    normalised_scalar: Decimal | None
    normalised_count: int | None
    value_state: str


@dataclass(frozen=True)
class MappingRow(FieldMapping):
    table_id: str
    owner_kind: str
    owner_id: str
    reference_kind: str


@dataclass(frozen=True)
class AttributeRow(FieldAttribute):
    table_id: str
    owner_kind: str
    owner_id: str


@dataclass(frozen=True)
class AttributeEvidenceRow(AttributeEvidence):
    table_id: str
    owner_kind: str
    owner_id: str


@dataclass(frozen=True)
class AttributeDecisionRow(AttributeDecision):
    table_id: str
    owner_kind: str
    owner_id: str


@dataclass(frozen=True)
class OccurrenceRow(TableKey):
    bundle_key: str
    output_version: str
    scope: str | None
    kind: str
    local_id: str
    source_text: str | None
    capture_revision_id: str


@dataclass(frozen=True)
class OccurrenceLinkRow(TableKey):
    owner_kind: str
    owner_id: str
    position: int
    role: str
    target_bundle_key: str
    target_scope: str | None
    target_kind: str
    target_id: str
    target_output_version: str | None


@dataclass(frozen=True)
class ContextRow(TableKey):
    context_revision_id: str


@dataclass(frozen=True)
class ContextBindingRow(TableKey):
    owner_kind: str
    owner_id: str
    context_revision_id: str
    role: str | None
    descriptor_ref: str | None
    position: int


@dataclass(frozen=True)
class SourceTableOutput:
    tables: Relation
    fields: Relation
    axes: Relation
    cells: Relation
    references: Relation
    source_attributes: Relation
    evidence: Relation
    segmentations: Relation
    bands: Relation
    qualifications: Relation
    relationships: Relation
    temporal_descriptors: Relation
    temporal_bindings: Relation
    meanings: Relation
    mapping_refs: Relation
    attributes: Relation
    attribute_evidence: Relation
    attribute_decisions: Relation
    occurrences: Relation
    occurrence_links: Relation
    contexts: Relation
    context_bindings: Relation
