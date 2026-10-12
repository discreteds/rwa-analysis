"""Pure projection of selected typed datasets, using their original resolvers."""

from dataclasses import fields, replace

from rwa_analysis.catalogue.models import CatalogueRelease, FieldMeaning
from rwa_analysis.catalogue.resolve import resolve_field as resolve_cr6
from rwa_analysis.domains.cr9.models import COUNTS
from rwa_analysis.domains.cr9.semantics import resolve_field as resolve_cr9
from rwa_analysis.extraction.cr6 import Cr6Dataset
from rwa_analysis.extraction.cr9 import Cr9Dataset
from rwa_analysis.extraction.models import PublishedField, SourceEndpoint
from rwa_analysis.extraction.source_tables import (
    CellTemporalBinding,
    ReportedText,
    SourceCell,
    SourceTable,
    SourceTableMetadata,
    TableContext,
    TableField,
)
from rwa_analysis.extraction.temporal import TemporalDescriptor

CR6_MONEY = {
    "on_balance_exposure",
    "off_balance_exposure",
    "ead",
    "rwa",
    "regulatory_expected_loss",
    "provisions",
}


def adapt_legacy(
    dataset: Cr6Dataset | Cr9Dataset, catalogue: CatalogueRelease
) -> tuple[SourceTable, dict[str, FieldMeaning]]:
    """Adapt published bindings and lexical axes without PDF or storage access.

    Numeric cell IDs are ``record_id/published_field_id``; lexical cells retain
    their source axis IDs. Meanings are selected before changing those addresses.
    """
    meta = dataset.metadata
    cr6 = isinstance(dataset, Cr6Dataset)
    records = dataset.exposure_rows if cr6 else dataset.backtesting_rows
    resolver = resolve_cr6 if cr6 else resolve_cr9
    counts = {"reported_borrower_count"} if cr6 else set(COUNTS)
    axes = {a.id: a for a in meta.axes}
    records_by_row = {r.source_row_ref: r for r in records}
    published = {f.id: f for f in meta.published_fields}
    table_fields, cells, meanings, addresses = {}, [], {}, {}
    row_fields = {}
    for binding in meta.bindings:
        key = binding.typed_field_name
        field = published[binding.published_field_ref]
        count = key in counts
        value_kind = "integer" if count else "decimal"
        table_fields[field.id] = TableField(
            **{f.name: getattr(field, f.name) for f in fields(PublishedField)},
            value_kind=value_kind,
            result_kind="count"
            if count
            else "money"
            if cr6 and key in CR6_MONEY
            else "scalar",
        )
        for row_ref in binding.row_refs:
            record = records_by_row[row_ref]
            meaning = resolver(catalogue, dataset, record, key)
            cell_id = f"{record.record_id}/{field.id}"
            addresses[record.record_id, key] = cell_id
            row_fields[row_ref, field.id] = cell_id
            cells.append(
                SourceCell(
                    cell_id,
                    field.id,
                    row_ref,
                    binding.column_refs[0] if binding.column_refs else None,
                    binding.context_refs,
                    record.source_segment_memberships,
                    tuple(
                        dict.fromkeys(
                            binding.qualification_refs
                            + axes[row_ref].qualification_refs
                        )
                    ),
                    value_kind,
                    getattr(record, key),
                )
            )
            meanings[cell_id] = meaning

    # Legacy CR9 lexical values are header occurrences whose paths identify both
    # a body row and a column. Other headers are structure, never extra cells.
    if not cr6:
        for axis in meta.axes:
            rows = [r for r in axis.header_path_refs if r in records_by_row]
            columns = [r for r in axis.header_path_refs if axes[r].axis == "column"]
            if axis.axis != "header" or not rows or not columns:
                continue
            row_ref, column_ref = rows[0], columns[0]
            column = axes[column_ref]
            table_fields.setdefault(
                column_ref,
                TableField(
                    column.id,
                    column.source_label,
                    column.header_path_refs + (column.id,),
                    "",
                    None,
                    column.qualification_refs,
                    (),
                    column.source_reference,
                    value_kind="text",
                    result_kind="text",
                ),
            )
            token = axis.source_label
            cells.append(
                SourceCell(
                    axis.id,
                    column_ref,
                    row_ref,
                    column_ref,
                    axis.context_refs,
                    records_by_row[row_ref].source_segment_memberships,
                    tuple(
                        dict.fromkeys(
                            axis.qualification_refs + axes[row_ref].qualification_refs
                        )
                    ),
                    "text",
                    ReportedText(
                        token or None,
                        token,
                        "blank_unresolved"
                        if not token
                        else "not_applicable"
                        if token == "N/A"
                        else None,
                        axis.source_reference,
                    ),
                )
            )
            meanings[axis.id] = FieldMeaning(None, None, (), (), None)

    temporal = [
        CellTemporalBinding(
            addresses[b.record_id, b.field_key], b.role, b.descriptor_ref
        )
        for b in meta.temporal_bindings
        if (b.record_id, b.field_key) in addresses
    ]
    descriptors = meta.temporal_descriptors
    if cr6:
        descriptor = TemporalDescriptor(
            f"{meta.context.id}/observation-date",
            meta.context.source_date_label,
            point=meta.context.observation_date.isoformat(),
            point_status="established",
            evidence=meta.context.evidence,
        )
        descriptors += (descriptor,)
        temporal.extend(
            CellTemporalBinding(c.id, "measurement", descriptor.id) for c in cells
        )

    relationships = []
    for relationship in meta.relationships:
        scoped_rows = [s.id for s in relationship.scope if s.kind == "row"]

        def endpoint(value, scoped_rows=scoped_rows):
            if value.kind == "field" and len(scoped_rows) == 1:
                cell_id = row_fields.get((scoped_rows[0], value.id))
                if cell_id is not None:
                    return SourceEndpoint("cell", cell_id)
            return value

        relationships.append(
            replace(
                relationship,
                parent=endpoint(relationship.parent),
                children=tuple(endpoint(c) for c in relationship.children),
            )
        )
    context = TableContext(
        **{
            f.name: getattr(meta.context, f.name)
            for f in fields(TableContext)
            if f.name != "source_date_label"
        },
        source_date_label=meta.context.source_date_label if cr6 else "",
    )
    return SourceTable(
        dataset.id,
        SourceTableMetadata(
            context,
            meta.axes,
            tuple(table_fields.values()),
            meta.segmentations,
            meta.qualifications,
            tuple(relationships),
            descriptors,
            tuple(temporal),
        ),
        tuple(cells),
    ), meanings
