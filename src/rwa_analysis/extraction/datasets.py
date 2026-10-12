"""Shared source metadata and bundles, independent of domain record collections."""

from dataclasses import dataclass
from typing import Protocol

from .models import (
    PublishedField,
    Qualification,
    SegmentationDefinition,
    SourceAxisItem,
    SourceDocument,
    SourceReference,
    SourceRelationship,
    ValueBinding,
    source_objects,
    unique_ids,
)
from .temporal import TemporalBinding, TemporalDescriptor


@dataclass(frozen=True)
class DatasetMetadata[Context]:
    context: Context
    axes: tuple[SourceAxisItem, ...]
    published_fields: tuple[PublishedField, ...]
    bindings: tuple[ValueBinding, ...]
    segmentations: tuple[SegmentationDefinition, ...]
    qualifications: tuple[Qualification, ...]
    relationships: tuple[SourceRelationship, ...]
    temporal_descriptors: tuple[TemporalDescriptor, ...] = ()
    temporal_bindings: tuple[TemporalBinding, ...] = ()


class Dataset(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def metadata(self) -> DatasetMetadata[object]: ...


@dataclass(frozen=True)
class ExtractionBundle:
    document: SourceDocument
    bundle_key: str
    extractor_path: str
    schema_version: str
    datasets: tuple[Dataset, ...]

    def __post_init__(self):
        unique_ids(self.datasets)
        for obj in source_objects(self):
            if (
                isinstance(obj, SourceReference)
                and obj.document_id != self.document.document_id
            ):
                raise ValueError(f"Unresolved document: {obj.document_id}")
