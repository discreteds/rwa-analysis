"""Native declarations shared by source conformance, storage and readback."""

import mountainash as ma
import polars as pl
from mountainash.core.dtypes import DecimalDtype
from mountainash.typespec.converters import to_polars_schema

from rwa_analysis.domains.cr6.contracts import TableDeclaration, model_spec

from . import models as m

DECIMALS = {
    "source_number": DecimalDtype(16, 8),
    "source_scale": DecimalDtype(16, 6),
    "unit_factor": DecimalDtype(16, 6),
    "lower": DecimalDtype(16, 8),
    "upper": DecimalDtype(16, 8),
    "duration_amount": DecimalDtype(16, 8),
    "normalised_amount": DecimalDtype(16, 2),
    "normalised_scalar": DecimalDtype(16, 8),
}


def table(name, model, *keys):
    return TableDeclaration(
        name,
        "source_" + name,
        model,
        model_spec(
            model, decimals=DECIMALS, keys=("silver_revision_id", "table_id", *keys)
        ),
    )


TABLES = (
    table("occurrences", m.OccurrenceRow, "kind", "local_id"),
    table(
        "occurrence_links", m.OccurrenceLinkRow, "owner_kind", "owner_id", "position"
    ),
    table("contexts", m.ContextRow, "context_revision_id"),
    table(
        "context_bindings", m.ContextBindingRow, "owner_kind", "owner_id", "position"
    ),
    table("tables", m.TableRow),
    table("fields", m.FieldRow, "field_id"),
    table("axes", m.AxisRow, "axis_id"),
    table("cells", m.CellRow, "cell_id"),
    table("references", m.ReferenceRow, "owner_kind", "owner_id", "member", "position"),
    table("source_attributes", m.SourceAttributeRow, "owner_kind", "owner_id", "name"),
    table("evidence", m.EvidenceRow, "owner_kind", "owner_id", "member", "position"),
    table("segmentations", m.SegmentationRow, "segmentation_id"),
    table("bands", m.BandRow, "segmentation_id", "band_id"),
    table("qualifications", m.QualificationRow, "qualification_id"),
    table("relationships", m.RelationshipRow, "relationship_id"),
    table("temporal_descriptors", m.TemporalRow, "descriptor_id"),
    table("temporal_bindings", m.TemporalBindingRow, "position"),
    table("meanings", m.MeaningRow, "cell_id"),
    table("mapping_refs", m.MappingRow, "observation_id", "field_key", "position"),
    table(
        "attributes",
        m.AttributeRow,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
    ),
    table(
        "attribute_evidence",
        m.AttributeEvidenceRow,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
        "position",
    ),
    table(
        "attribute_decisions",
        m.AttributeDecisionRow,
        "observation_id",
        "field_key",
        "name",
        "assertion_index",
        "position",
    ),
)
DECLARATIONS = {t.member: t for t in TABLES}


def relation(name, rows=()):
    spec = DECLARATIONS[name].spec
    return (
        ma.relation(list(rows)).conform(spec)
        if rows
        else ma.relation(pl.DataFrame(schema=to_polars_schema(spec)))
    )


def empty_output():
    return m.SourceTableOutput(**{t.member: relation(t.member) for t in TABLES})
