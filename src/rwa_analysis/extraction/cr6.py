"""Typed CR6 observations and closed, locally referenced source bundles."""

from dataclasses import dataclass, fields
from decimal import Decimal

from .models import (
    DatasetContext,
    PublishedField,
    Qualification,
    ReportedValue,
    SegmentationDefinition,
    SourceAxisItem,
    SourceDocument,
    SourceEndpoint,
    SourceReference,
    SourceRelationship,
    ValueBinding,
    source_objects,
    unique_ids,
)


@dataclass(frozen=True)
class BronzeCreditRiskExposureRow:
    record_id: str
    source_row_ref: str
    source_row_role: str
    source_segment_memberships: tuple[str, ...]
    source_aggregation_scope: tuple[str, ...]
    on_balance_exposure: ReportedValue[Decimal]
    off_balance_exposure: ReportedValue[Decimal]
    average_ccf: ReportedValue[Decimal]
    ead: ReportedValue[Decimal]
    average_pd: ReportedValue[Decimal]
    reported_borrower_count: ReportedValue[int]
    average_lgd: ReportedValue[Decimal]
    average_maturity: ReportedValue[Decimal]
    rwa: ReportedValue[Decimal]
    rwa_density: ReportedValue[Decimal]
    regulatory_expected_loss: ReportedValue[Decimal]
    provisions: ReportedValue[Decimal]

    def __post_init__(self):
        for name in CR6_FIELDS:
            cell = getattr(self, name)
            expected = int if name == "reported_borrower_count" else Decimal
            if not isinstance(cell, ReportedValue) or (
                cell.value is not None and type(cell.value) is not expected
            ):
                raise TypeError(f"{name} requires ReportedValue[{expected.__name__}]")


CR6_FIELDS = tuple(f.name for f in fields(BronzeCreditRiskExposureRow)[5:])


@dataclass(frozen=True)
class Cr6Dataset:
    id: str
    context: DatasetContext
    axes: tuple[SourceAxisItem, ...]
    published_fields: tuple[PublishedField, ...]
    bindings: tuple[ValueBinding, ...]
    segmentations: tuple[SegmentationDefinition, ...]
    qualifications: tuple[Qualification, ...]
    relationships: tuple[SourceRelationship, ...]
    records: tuple[BronzeCreditRiskExposureRow, ...]

    def __post_init__(self):
        axes = unique_ids(self.axes)
        published = unique_ids(self.published_fields)
        notes = unique_ids(self.qualifications)
        relationships = unique_ids(self.relationships)
        unique_ids(self.bindings)
        unique_ids(self.segmentations)
        unique_ids(self.records, "record_id")
        bands = unique_ids(tuple(b for s in self.segmentations for b in s.bands))
        rows = {a.id for a in self.axes if a.axis == "row"}
        columns = {a.id for a in self.axes if a.axis == "column"}
        blocks = {a.id for a in self.axes if a.axis == "block"}
        endpoints = {
            "row": rows,
            "field": published,
            "block": blocks,
            "dataset": {self.id},
            "band": bands,
            "relationship": relationships,
        }

        def resolve(refs, allowed, name):
            for ref in refs:
                if ref not in allowed:
                    raise ValueError(f"Unresolved {name}: {ref}")

        for obj in source_objects(self):
            for attr, allowed in (
                ("qualification_refs", notes),
                ("header_path_refs", axes),
                ("context_refs", {self.context.id}),
            ):
                resolve(getattr(obj, attr, ()), allowed, attr)
            if isinstance(obj, SourceEndpoint):
                resolve((obj.id,), endpoints.get(obj.kind, set()), obj.kind)
        for field in self.published_fields:
            unique_ids(field.attributes, "name")
        coverage = set()
        for binding in self.bindings:
            resolve((binding.typed_field_name,), CR6_FIELDS, "typed_field_name")
            resolve((binding.published_field_ref,), published, "published_field_ref")
            resolve(binding.row_refs, rows, "row_refs")
            resolve(binding.column_refs, columns, "column_refs")
            for row in binding.row_refs:
                pair = (row, binding.typed_field_name)
                if pair in coverage:
                    raise ValueError(f"Ambiguous binding for {pair}")
                coverage.add(pair)
        for record in self.records:
            resolve((record.source_row_ref,), rows, "source_row_ref")
            resolve(
                record.source_segment_memberships, bands, "source_segment_memberships"
            )
            resolve(record.source_aggregation_scope, blocks, "source_aggregation_scope")
            for name in CR6_FIELDS:
                if (record.source_row_ref, name) not in coverage:
                    raise ValueError(f"Missing binding for {record.record_id}.{name}")


@dataclass(frozen=True)
class ExtractionBundle:
    document: SourceDocument
    bundle_key: str
    extractor_path: str
    schema_version: str
    datasets: tuple[Cr6Dataset, ...]

    def __post_init__(self):
        if self.schema_version != "cr6-v1":
            raise ValueError(f"Unsupported schema version: {self.schema_version}")
        unique_ids(self.datasets)
        for obj in source_objects(self):
            if (
                isinstance(obj, SourceReference)
                and obj.document_id != self.document.document_id
            ):
                raise ValueError(f"Unresolved document: {obj.document_id}")
