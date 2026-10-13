"""Source-facing metadata. Unknown meaning is independent of missing values."""

from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

Status = Literal[
    "established", "provisional", "unresolved", "conflicting", "not_applicable"
]


@dataclass(frozen=True)
class OccurrenceRef:
    bundle_key: str
    scope: str | None
    kind: Literal[
        "table", "field", "row", "column", "header", "block", "cell", "comment"
    ]
    local_id: str
    output_version: str | None = None


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    local_path: str
    organisation_id: str
    reporting_entity: str
    title: str
    document_reporting_date: date
    publication_date: date | None
    reporting_jurisdiction: str
    source_url: str


@dataclass(frozen=True)
class SourceReference:
    document_id: str
    pdf_page: int
    printed_page: str
    location: str
    row: str | None = None
    column: str | None = None

    def __post_init__(self):
        if type(self.pdf_page) is not int or self.pdf_page < 1:
            raise ValueError("pdf_page must be a positive one-based integer")


@dataclass(frozen=True)
class ReportedValue[T: (Decimal, int)]:
    value: T | None
    original_text: str
    displayed_precision: int | None
    missing_reason: str | None
    source_reference: SourceReference

    def __post_init__(self):
        if (self.value is None) != (self.missing_reason is not None):
            raise ValueError(
                "Absent values require a missing reason; present values forbid one"
            )
        if self.missing_reason == "":
            raise ValueError("Missing reason cannot be empty")
        if self.value is not None and type(self.value) not in (Decimal, int):
            raise TypeError("Reported values must be Decimal or int")
        if isinstance(self.value, Decimal) and not self.value.is_finite():
            raise ValueError("Nonfinite Decimal value")
        if self.displayed_precision is not None and (
            type(self.displayed_precision) is not int or self.displayed_precision < 0
        ):
            raise ValueError("Invalid displayed precision")


@dataclass(frozen=True)
class Knowledge:
    value: str | None = None
    status: Status = "unresolved"
    qualification_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticAttribute:
    name: str
    value: str | None
    status: Status
    qualification_refs: tuple[str, ...]


@dataclass(frozen=True)
class DatasetContext:
    id: str
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
class SourceAxisItem:
    id: str
    axis: Literal["row", "column", "header", "block"]
    source_label: str
    order: int
    header_path_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    qualification_refs: tuple[str, ...]
    source_reference: SourceReference


@dataclass(frozen=True)
class PublishedField:
    id: str
    source_label: str
    header_path_refs: tuple[str, ...]
    source_unit: str
    source_scale: Decimal | None
    qualification_refs: tuple[str, ...]
    attributes: tuple[SemanticAttribute, ...]
    source_reference: SourceReference


@dataclass(frozen=True)
class ValueBinding:
    id: str
    typed_field_name: str
    published_field_ref: str
    row_refs: tuple[str, ...]
    column_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    qualification_refs: tuple[str, ...]


@dataclass(frozen=True)
class BandDefinition:
    id: str
    source_label: str
    order: int
    kind: Literal["interval", "default", "category"]
    unit: str
    lower: Decimal | None
    upper: Decimal | None
    lower_inclusive: bool | None
    upper_inclusive: bool | None
    lower_status: Literal["established", "unbounded", "unresolved", "not_applicable"]
    upper_status: Literal["established", "unbounded", "unresolved", "not_applicable"]
    category: str | None
    source_reference: SourceReference


@dataclass(frozen=True)
class SegmentationDefinition:
    id: str
    source_dimension: str
    bands: tuple[BandDefinition, ...]
    context_refs: tuple[str, ...]
    completeness: Knowledge
    disjointness: Knowledge
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class SourceEndpoint:
    kind: Literal["row", "field", "block", "dataset", "band", "relationship", "cell"]
    id: str


@dataclass(frozen=True)
class Qualification:
    id: str
    source_text: str
    evidence: tuple[SourceReference, ...]
    scope: tuple[SourceEndpoint, ...]


@dataclass(frozen=True)
class SourceRelationship:
    id: str
    kind: Literal["total", "subset", "comprising"]
    source_label: str
    parent: SourceEndpoint
    children: tuple[SourceEndpoint, ...]
    scope: tuple[SourceEndpoint, ...]
    exhaustive: bool | None
    mutually_exclusive: bool | None
    evidence: tuple[SourceReference, ...]


def source_objects(value):
    """Traverse the typed tree for structural reference validation."""
    if is_dataclass(value):
        yield value
        for field in fields(value):
            yield from source_objects(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from source_objects(item)
    elif isinstance(value, (list, dict, set)):
        raise TypeError("Source collections must be immutable tuples")


def unique_ids(items, attribute="id") -> set[str]:
    ids = [getattr(item, attribute) for item in items]
    if any(not id for id in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"Empty or duplicate {attribute}")
    return set(ids)
