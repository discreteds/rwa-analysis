"""One composition owner for captured source, context and interpretations."""

from dataclasses import dataclass, replace
from datetime import date
from functools import cache

from rwa_analysis.extraction.models import OccurrenceRef
from rwa_analysis.storage.bronze import LoadedBronze

from .load import TYPES
from .models import (
    EvidenceRef,
    FieldMeaning,
    MappingScope,
    MemberSelection,
    OccurrenceScope,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    UnitConversion,
    revision_references,
)
from .resolve import FieldOccurrence, compose_field, matches_occurrence


@dataclass(frozen=True)
class ContextContribution:
    revision_id: str
    attributes: tuple[SemanticAttribute, ...]
    reference_kind: str = "context"
    supersedes_refs: tuple[RevisionRef, ...] = ()
    overrides_refs: tuple[RevisionRef, ...] = ()
    concept_ref: RevisionRef | None = None
    measure_ref: RevisionRef | None = None
    conversion: UnitConversion | None = None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    decision_refs: tuple[RevisionRef, ...] = ()


@dataclass(frozen=True)
class ResolvedCapture:
    captured: LoadedBronze
    meanings: dict[OccurrenceRef, FieldMeaning]


def _date_for(binding, contexts, role):
    points = []
    for link in binding.temporal_roles:
        if link.role != role:
            continue
        descriptor = next(
            t
            for t in contexts[link.context_ref].temporal
            if t.id == link.descriptor_ref
        )
        if (
            descriptor.point_status != "established"
            or not descriptor.point
            or len(descriptor.point) != 10
        ):
            return None
        points.append(date.fromisoformat(descriptor.point))
    return points[0] if points and len(set(points)) == 1 else None


def resolve_capture(loaded_bronze, catalogue):
    bundle = loaded_bronze.bundle
    retained = tuple(
        member
        for member in bundle.snapshot.semantic_definitions
        if member.revision_id not in {s.revision_id for s in catalogue.selection}
    )
    kinds = {cls: kind for kind, cls in TYPES.items()}
    catalogue = replace(
        catalogue,
        members=catalogue.members + retained,
        selection=catalogue.selection
        + tuple(
            MemberSelection("capture-snapshot", kinds[type(m)], m.revision_id)
            for m in retained
        ),
    )
    contexts = {c.revision_id: c for c in bundle.snapshot.contexts}
    tables = {t.id: t for t in bundle.datasets}
    meanings = {}
    for binding in bundle.snapshot.occurrences:
        ref = binding.ref
        table = tables.get(ref.scope)
        cell = (
            next((c for c in table.cells if c.id == ref.local_id), None)
            if table and ref.kind == "cell"
            else None
        )
        field_id = (
            cell.field_ref if cell else ref.local_id if ref.kind == "field" else None
        )
        field = (
            next((f for f in table.metadata.published_fields if f.id == field_id), None)
            if table
            else None
        )
        old = None
        if cell:
            context = table.metadata.context
            old = FieldOccurrence(
                MappingScope(
                    bundle.document.document_id,
                    context.document_date,
                    table.id,
                    context.source_template,
                    context.source_portfolio_label,
                    field_key=field.id,
                    published_field_ref=field.id,
                    record_id=cell.id,
                    reporting_entity=context.reporting_entity.value,
                    regulatory_scope=context.regulatory_scope.value,
                ),
                field,
                cell.segment_refs,
            )

        def selected(mapping, ref=ref, old=old, binding=binding):
            if RevisionRef("mapping", mapping.revision_id) in binding.definition_refs:
                return True
            scope = mapping.scope
            if isinstance(scope, OccurrenceScope):
                return any(
                    replace(t, output_version=None) == replace(ref, output_version=None)
                    and (
                        t.output_version is None
                        or t.output_version == loaded_bronze.ref.output_version
                    )
                    for t in scope.targets
                )
            return old is not None and matches_occurrence(mapping, old)

        mappings = []
        for mapping in catalogue.members:
            if not isinstance(mapping, SourceMappingRevision) or not selected(mapping):
                continue
            role = getattr(mapping.scope, "temporal_role", "measurement")
            point = _date_for(binding, contexts, role)

            def interval(start, end, point=point):
                return (start is None and end is None) or (
                    point is not None
                    and (start is None or start <= point)
                    and (end is None or point <= end)
                )

            if interval(mapping.effective_from, mapping.effective_to) and interval(
                getattr(mapping.scope, "observation_from", None),
                getattr(mapping.scope, "observation_to", None),
            ):
                mappings.append(mapping)

        def applicability(mapping, binding=binding):
            point = _date_for(
                binding,
                contexts,
                getattr(
                    getattr(mapping, "scope", None), "temporal_role", "measurement"
                ),
            )

            @cache
            def applies(reference):
                member = catalogue.member(reference)
                return (
                    (member.effective_from is None and member.effective_to is None)
                    or (
                        point is not None
                        and (
                            member.effective_from is None
                            or member.effective_from <= point
                        )
                        and (
                            member.effective_to is None or point <= member.effective_to
                        )
                    )
                ) and all(
                    applies(r)
                    for r in revision_references(member, include_history=False)
                )

            return applies

        mappings = [
            m for m in mappings if all(applicability(m)(r) for r in m.decision_refs)
        ]
        contributions = [
            ContextContribution(key, contexts[key].attributes)
            for key in binding.context_refs
        ]
        for definition in binding.definition_refs:
            if definition.kind != "mapping":
                contributions.append(
                    ContextContribution(
                        definition.revision_id,
                        (),
                        reference_kind=definition.kind,
                        concept_ref=definition
                        if definition.kind == "concept"
                        else None,
                        measure_ref=definition
                        if definition.kind == "measure"
                        else None,
                    )
                )
        meanings[ref] = compose_field(
            catalogue,
            field,
            [*contributions, *mappings],
            applicability(None),
            mapping_applicability=applicability,
        )
    return ResolvedCapture(loaded_bronze, meanings)
