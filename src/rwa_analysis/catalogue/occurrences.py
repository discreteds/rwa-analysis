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
    from rwa_analysis.domains.source_tables.legacy import adapt_legacy, domain_bindings
    from rwa_analysis.extraction.definitions import CapturedBundle
    from rwa_analysis.extraction.source_tables import SourceTable

    bundle = loaded_bronze.bundle
    if not isinstance(bundle, CapturedBundle):
        tables = tuple(
            ds if isinstance(ds, SourceTable) else adapt_legacy(ds)
            for ds in bundle.datasets
        )
        domains = {b.ref: b for b in domain_bindings(bundle)}
        originals = {ds.id: ds for ds in bundle.datasets}
        meanings = {}
        for table in tables:
            for cell in table.cells:
                ref = OccurrenceRef(bundle.bundle_key, table.id, "cell", cell.id)
                domain = domains.get(ref)
                original = originals[table.id]
                point = (
                    original.metadata.context.observation_date
                    if domain and domain.domain == "cr6"
                    else None
                )
                old = source_occurrence(bundle, table, cell, domain)
                meanings[ref] = resolve_occurrence(
                    catalogue,
                    old,
                    ref=ref,
                    output_version=loaded_bronze.ref.output_version,
                    point_for=(
                        (lambda role, point=point: point)
                        if domain
                        else (
                            lambda role, table=table, cell=cell: source_date(
                                table, cell, role
                            )
                        )
                    ),
                )
        return ResolvedCapture(
            replace(loaded_bronze, bundle=replace(bundle, datasets=tables)), meanings
        )
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
    domains = {b.ref: b for b in bundle.snapshot.domain_bindings}
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
        old = source_occurrence(bundle, table, cell, domains.get(ref)) if cell else None
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
        meanings[ref] = resolve_occurrence(
            catalogue,
            old,
            field=field,
            ref=ref,
            output_version=loaded_bronze.ref.output_version,
            point_for=lambda role, binding=binding: _date_for(binding, contexts, role),
            definition_refs=binding.definition_refs,
            contributions=contributions,
        )
    return ResolvedCapture(loaded_bronze, meanings)


def source_occurrence(bundle, table, cell, domain=None):
    context = table.metadata.context
    field = next(f for f in table.metadata.published_fields if f.id == cell.field_ref)
    return FieldOccurrence(
        MappingScope(
            document_id=bundle.document.document_id,
            document_date=context.document_date,
            dataset_id=table.id,
            template=context.source_template,
            portfolio=context.source_portfolio_label,
            field_key=domain.field_key if domain else field.id,
            published_field_ref=field.id,
            record_id=domain.record_id if domain else cell.id,
            row_role=cell.source_row_role,
            reporting_entity=context.reporting_entity.value,
            regulatory_scope=context.regulatory_scope.value,
        ),
        field,
        cell.segment_refs,
    )


def source_date(table, cell, role="measurement"):
    """Only complete established points in the explicitly bound temporal role."""
    descriptors = {d.id: d for d in table.metadata.temporal_descriptors}
    selected = [
        descriptors[b.descriptor_ref]
        for b in table.metadata.temporal_bindings
        if b.cell_id == cell.id and b.role == role
    ]
    if not selected or any(
        d.point_status != "established" or not d.point or len(d.point) != 10
        for d in selected
    ):
        return None
    points = {date.fromisoformat(d.point) for d in selected}
    return next(iter(points)) if len(points) == 1 else None


def resolve_occurrence(
    catalogue,
    occurrence,
    *,
    field=None,
    ref=None,
    output_version=None,
    point_for=lambda role: None,
    definition_refs=(),
    contributions=(),
):
    """Shared applicability and composition for native and retained addresses."""
    field = occurrence.published_field if occurrence else field

    def selected(mapping):
        if RevisionRef("mapping", mapping.revision_id) in definition_refs:
            return True
        if isinstance(mapping.scope, OccurrenceScope):
            return ref is not None and any(
                replace(t, output_version=None) == replace(ref, output_version=None)
                and (t.output_version is None or t.output_version == output_version)
                for t in mapping.scope.targets
            )
        return occurrence is not None and matches_occurrence(mapping, occurrence)

    def interval(start, end, point):
        return (start is None and end is None) or (
            point is not None
            and (start is None or start <= point)
            and (end is None or point <= end)
        )

    def applicability(mapping):
        point = point_for(
            getattr(getattr(mapping, "scope", None), "temporal_role", "measurement")
        )

        @cache
        def applies(reference):
            member = catalogue.member(reference)
            return interval(member.effective_from, member.effective_to, point) and all(
                applies(r) for r in revision_references(member, include_history=False)
            )

        return applies

    mappings = []
    for mapping in catalogue.members:
        if not isinstance(mapping, SourceMappingRevision) or not selected(mapping):
            continue
        point = point_for(getattr(mapping.scope, "temporal_role", "measurement"))
        if (
            interval(mapping.effective_from, mapping.effective_to, point)
            and interval(
                getattr(mapping.scope, "observation_from", None),
                getattr(mapping.scope, "observation_to", None),
                point,
            )
            and all(applicability(mapping)(r) for r in mapping.decision_refs)
        ):
            mappings.append(mapping)
    return compose_field(
        catalogue,
        field,
        [*contributions, *mappings],
        applicability(None),
        mapping_applicability=applicability,
    )
