"""Source-defined tables compose metadata without a fixed financial field inventory."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from .models import (
    Knowledge,
    PublishedField,
    Qualification,
    ReportedValue,
    SegmentationDefinition,
    SourceAxisItem,
    SourceReference,
    SourceRelationship,
)
from .temporal import TemporalDescriptor

ValueKind = Literal["decimal", "integer", "text"]
ResultKind = Literal["money", "scalar", "count", "text"]


@dataclass(frozen=True)
class TableContext:
    id: str
    document_date: date
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
class TableField(PublishedField):
    value_kind: ValueKind = "decimal"
    result_kind: ResultKind = "scalar"
    source_form: Literal["table_body", "note"] = "table_body"


@dataclass(frozen=True)
class ReportedText:
    value: str | None
    original_text: str
    missing_reason: str | None
    source_reference: SourceReference


@dataclass(frozen=True)
class SourceCell:
    id: str
    field_ref: str
    row_ref: str | None
    column_ref: str | None
    context_refs: tuple[str, ...]
    segment_refs: tuple[str, ...]
    qualification_refs: tuple[str, ...]
    value_kind: ValueKind
    value: ReportedValue[Decimal] | ReportedValue[int] | ReportedText
    source_row_role: str | None = None
    source_aggregation_scope: tuple[str, ...] = ()


@dataclass(frozen=True)
class CellTemporalBinding:
    cell_id: str
    role: Literal[
        "measurement",
        "cohort_anchor",
        "outcome_window",
        "history_window",
        "rating_assignment",
        "weight_measurement",
    ]
    descriptor_ref: str


@dataclass(frozen=True)
class SourceTableMetadata:
    context: TableContext
    axes: tuple[SourceAxisItem, ...]
    published_fields: tuple[TableField, ...]
    segmentations: tuple[SegmentationDefinition, ...]
    qualifications: tuple[Qualification, ...]
    relationships: tuple[SourceRelationship, ...]
    temporal_descriptors: tuple[TemporalDescriptor, ...]
    temporal_bindings: tuple[CellTemporalBinding, ...]


@dataclass(frozen=True)
class SourceTable:
    id: str
    metadata: SourceTableMetadata
    cells: tuple[SourceCell, ...]
