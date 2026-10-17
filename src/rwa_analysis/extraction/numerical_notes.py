"""Compose selected numerical passages using the existing capture contracts.

One physical passage can supply several independently classified numbers. Its
text is retained once; each number keeps its own scale, timing and applicability.
"""

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from rwa_analysis.catalogue.models import (
    EvidenceRef,
    OccurrenceScope,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    UnitConversion,
)

from .definitions import (
    CellBinding,
    ContextDefinition,
    FragmentRef,
    OccurrenceBinding,
    OccurrenceLink,
    TemporalRole,
)
from .models import (
    Knowledge,
    OccurrenceRef,
    Qualification,
    SourceAxisItem,
    SourceEndpoint,
)
from .models import SemanticAttribute as SourceAttribute
from .source_tables import (
    CellTemporalBinding,
    SourceTable,
    SourceTableMetadata,
    TableContext,
    TableField,
)
from .temporal import TemporalDescriptor


@dataclass(frozen=True, kw_only=True)
class NumericalObservation:
    id: str
    slot: str
    label: str
    unit: str
    scale: Decimal
    point: str
    classification: str
    portfolio: str
    concept: str = "capital.risk-weighted-assets@v1"
    result_kind: str = "money"
    source_form: str = "note"
    attributes: tuple[SemanticAttribute, ...] = ()
    links: tuple[OccurrenceLink, ...] = ()
    missing_reason: str = "dash_unresolved"
    missing_tokens: tuple[str, ...] = ()
    temporal: tuple[TemporalDescriptor, ...] = ()


def with_numerical_notes(definition, passages, *, semantic_definitions=()):
    """Append explicitly selected observations; do not infer scope from the PDF."""
    tid = "rwa-adjustments"
    bundle = definition.bundle_key
    document = definition.document
    snapshot = definition.snapshot

    def address(kind, key):
        return OccurrenceRef(bundle, tid, kind, key)

    physicals, contexts, occurrences, mappings = [], [], [], []
    # Reuse only report-wide facts. AIRB/mortgage context does not apply to a
    # group output floor or an operational-risk capital charge.
    first_table = definition.tables[0].id
    table_binding = next(
        b
        for b in snapshot.occurrences
        if b.ref.scope == first_table and b.ref.kind == "table"
    )
    shared_attributes = tuple(
        a
        for c in snapshot.contexts
        if c.revision_id in table_binding.context_refs
        for a in c.attributes
        if a.name in ("reporting_entity", "currency")
    )
    report_context = tid + "/report@1"
    contexts.append(ContextDefinition(report_context, shared_attributes))
    fields, notes, descriptors, temporal, axes = [], [], [], [], []
    occurrences.append(OccurrenceBinding(address("table", tid)))
    for binding, numbers in passages:
        physicals.append(binding)
        note_id = binding.revision_id
        source = binding.source_reference
        note_ref = address("comment", note_id)
        evidence = (EvidenceRef(bundle, document.document_id, tid, "comment", note_id),)
        targets = tuple(address("cell", n.id) for n in numbers)
        occurrences.append(
            OccurrenceBinding(
                note_ref,
                (FragmentRef(note_id, "text"),),
                links=tuple(OccurrenceLink("qualifies", target) for target in targets),
            )
        )
        notes.append(
            Qualification(
                note_id,
                "",
                (source,),
                tuple(SourceEndpoint("cell", n.id) for n in numbers),
            )
        )
        row_id = "row/" + note_id
        if any(n.source_form == "table_body" for n in numbers):
            axes.append(
                SourceAxisItem(
                    row_id,
                    "row",
                    source.row or source.location,
                    len(axes),
                    (),
                    ("context",),
                    (note_id,),
                    source,
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address("row", row_id),
                    links=(OccurrenceLink("evidence", note_ref),),
                )
            )
        for number in numbers:
            context_id = tid + "/" + number.id + "@1"
            descriptor = TemporalDescriptor(
                "measurement",
                number.point,
                point=number.point,
                point_status="established",
                evidence=(source,),
            )
            attrs = (
                SemanticAttribute(
                    number.classification,
                    "established",
                    evidence_refs=evidence,
                    name="qualification_meaning",
                ),
                SemanticAttribute(
                    "reported",
                    "established",
                    evidence_refs=evidence,
                    name="structural_role",
                ),
                *(
                    replace(a, evidence_refs=a.evidence_refs or evidence)
                    for a in number.attributes
                ),
            )
            contexts.append(
                ContextDefinition(
                    context_id, attrs, (descriptor, *number.temporal), (source,)
                )
            )
            column_id = (
                "column/" + number.id if number.source_form == "table_body" else None
            )
            if column_id:
                axes.append(
                    SourceAxisItem(
                        column_id,
                        "column",
                        number.label,
                        len(axes),
                        (),
                        ("context",),
                        (note_id,),
                        source,
                    )
                )
                occurrences.append(
                    OccurrenceBinding(
                        address("column", column_id),
                        context_refs=(context_id,),
                        links=(OccurrenceLink("evidence", note_ref),),
                    )
                )
            fields.append(
                TableField(
                    number.id,
                    number.label,
                    (column_id,) if column_id else (),
                    number.unit,
                    number.scale,
                    (note_id,),
                    (
                        SourceAttribute(
                            "portfolio", number.portfolio, "established", (note_id,)
                        ),
                    ),
                    source,
                    "decimal",
                    number.result_kind,
                    number.source_form,
                )
            )
            definition_refs = (RevisionRef("concept", number.concept),)
            mapping_id = bundle + "/" + tid + "/" + number.id + "/units@1"
            mappings.append(
                SourceMappingRevision(
                    id=mapping_id.removesuffix("@1"),
                    revision_id=mapping_id,
                    created_on=date(2026, 10, 17),
                    effective_from=None,
                    effective_to=None,
                    evidence_refs=evidence,
                    scope=OccurrenceScope((address("cell", number.id),)),
                    conversion=UnitConversion(number.unit, number.scale, number.scale),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address("field", number.id),
                    context_refs=(context_id, report_context),
                    definition_refs=definition_refs,
                    links=(OccurrenceLink("evidence", note_ref),),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address("cell", number.id),
                    (FragmentRef(note_id, number.slot),),
                    (context_id, report_context),
                    (*definition_refs, RevisionRef("mapping", mapping_id)),
                    links=(OccurrenceLink("evidence", note_ref), *number.links),
                    temporal_roles=(
                        TemporalRole("measurement", context_id, "measurement"),
                        *(
                            TemporalRole(t.id, context_id, t.id)
                            for t in number.temporal
                        ),
                    ),
                    cell=CellBinding(
                        number.id,
                        row_id if column_id else None,
                        column_id,
                        qualification_refs=(note_id,),
                        missing_reason=number.missing_reason,
                        missing_tokens=number.missing_tokens,
                    ),
                )
            )
            descriptors.append(replace(descriptor, id=number.id + "/measurement"))
            temporal.append(
                CellTemporalBinding(number.id, "measurement", descriptors[-1].id)
            )
    table = SourceTable(
        tid,
        SourceTableMetadata(
            TableContext(
                "context",
                document.document_reporting_date,
                "",
                "Selected numerical evidence",
                "Selected adjustment notes and supporting totals",
                "Mixed; field-specific",
                Knowledge(document.reporting_entity, "established"),
                Knowledge(),
                Knowledge(),
                Knowledge(),
                Knowledge(),
                (),
                tuple(p.source_reference for p in physicals),
            ),
            tuple(axes),
            tuple(fields),
            (),
            tuple(notes),
            (),
            tuple(descriptors),
            tuple(temporal),
        ),
        (),
    )
    return replace(
        definition,
        tables=(*definition.tables, table),
        snapshot=replace(
            snapshot,
            revision_id=snapshot.revision_id + "/adjustments-1",
            physical=(*snapshot.physical, *physicals),
            contexts=(*snapshot.contexts, *contexts),
            occurrences=(*snapshot.occurrences, *occurrences),
            semantic_definitions=(
                *snapshot.semantic_definitions,
                *semantic_definitions,
                *mappings,
            ),
        ),
    )
