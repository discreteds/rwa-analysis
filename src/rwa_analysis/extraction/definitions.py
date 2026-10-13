"""Reviewed authoring declarations and their callable-free retained snapshot."""

from dataclasses import dataclass
from typing import Literal

from rwa_analysis.catalogue.models import Member, RevisionRef, SemanticAttribute

from .models import OccurrenceRef, SourceDocument, SourceReference
from .source_tables import SourceTable
from .temporal import TemporalDescriptor


@dataclass(frozen=True)
class PhysicalParameter:
    name: str
    value: str | int | tuple[str, ...]


@dataclass(frozen=True)
class PhysicalBinding:
    revision_id: str
    operation: str
    parameters: tuple[PhysicalParameter, ...] = ()
    source_reference: SourceReference | None = None


@dataclass(frozen=True)
class CapturedFragment:
    binding_ref: str
    slot: str
    text: str
    evidence: SourceReference


@dataclass(frozen=True)
class ContextDefinition:
    revision_id: str
    attributes: tuple[SemanticAttribute, ...] = ()
    temporal: tuple[TemporalDescriptor, ...] = ()
    evidence: tuple[SourceReference, ...] = ()


@dataclass(frozen=True)
class OccurrenceLink:
    role: str
    target: OccurrenceRef


@dataclass(frozen=True)
class FragmentRef:
    binding_ref: str
    slot: str


@dataclass(frozen=True)
class TemporalRole:
    role: str
    context_ref: str
    descriptor_ref: str


@dataclass(frozen=True)
class CellBinding:
    field_ref: str
    row_ref: str | None
    column_ref: str | None
    segment_refs: tuple[str, ...] = ()
    qualification_refs: tuple[str, ...] = ()
    value_kind: Literal["decimal", "integer", "text"] = "decimal"
    missing_reason: str | None = None


@dataclass(frozen=True)
class OccurrenceBinding:
    ref: OccurrenceRef
    physical_refs: tuple[FragmentRef, ...] = ()
    context_refs: tuple[str, ...] = ()
    definition_refs: tuple[RevisionRef, ...] = ()
    links: tuple[OccurrenceLink, ...] = ()
    temporal_roles: tuple[TemporalRole, ...] = ()
    cell: CellBinding | None = None


@dataclass(frozen=True)
class CaptureSnapshot:
    revision_id: str
    physical: tuple[PhysicalBinding, ...]
    contexts: tuple[ContextDefinition, ...]
    occurrences: tuple[OccurrenceBinding, ...]
    semantic_definitions: tuple[Member, ...] = ()


@dataclass(frozen=True)
class CaptureDefinition:
    document: SourceDocument
    bundle_key: str
    extractor_path: str
    tables: tuple[SourceTable, ...]
    snapshot: CaptureSnapshot


@dataclass(frozen=True)
class CapturedBundle:
    document: SourceDocument
    bundle_key: str
    extractor_path: str
    datasets: tuple[SourceTable, ...]
    snapshot: CaptureSnapshot
    fragments: tuple[CapturedFragment, ...] = ()
    schema_version: str = "disclosure-v4"
