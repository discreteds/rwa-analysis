"""Exact source occurrences select catalogue meanings without invented dates."""

from functools import cache

from rwa_analysis.catalogue.models import (
    MappingScope,
    SourceMappingRevision,
    revision_references,
)
from rwa_analysis.catalogue.resolve import (
    FieldOccurrence,
    compose_field,
    matches_occurrence,
)


def resolve_cell(catalogue, bundle, table, cell):
    context = table.metadata.context
    field = next(f for f in table.metadata.published_fields if f.id == cell.field_ref)
    occurrence = FieldOccurrence(
        MappingScope(
            document_id=bundle.document.document_id,
            document_date=context.document_date,
            dataset_id=table.id,
            template=context.source_template,
            portfolio=context.source_portfolio_label,
            field_key=field.id,
            published_field_ref=field.id,
            record_id=cell.id,
            reporting_entity=context.reporting_entity.value,
            regulatory_scope=context.regulatory_scope.value,
        ),
        field,
        cell.segment_refs,
    )

    @cache
    def applies(ref):
        member = catalogue.member(ref)
        return (
            member.effective_from is None
            and member.effective_to is None
            and all(
                applies(r) for r in revision_references(member, include_history=False)
            )
        )

    mappings = (
        m
        for m in catalogue.members
        if isinstance(m, SourceMappingRevision)
        and matches_occurrence(m, occurrence)
        and m.scope.observation_from is None
        and m.scope.observation_to is None
        and m.effective_from is None
        and m.effective_to is None
        and all(applies(r) for r in m.decision_refs)
    )
    return compose_field(catalogue, field, mappings, applies)
