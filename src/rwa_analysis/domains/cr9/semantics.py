"""Explicit CR9 source-occurrence selection without an invented snapshot date."""

from functools import cache

from rwa_analysis.catalogue.models import (
    CatalogueRelease,
    FieldMeaning,
    SourceMappingRevision,
    revision_references,
)
from rwa_analysis.catalogue.resolve import (
    compose_field,
    field_occurrence,
    matches_occurrence,
)
from rwa_analysis.extraction.cr9 import Cr9BacktestingRow, Cr9Dataset


def resolve_field(
    catalogue: CatalogueRelease,
    dataset: Cr9Dataset,
    row: Cr9BacktestingRow,
    field_key: str,
) -> FieldMeaning:
    """Resolve supported meaning; date-restricted claims remain unresolved.

    CR9 fields have multiple temporal roles. This slice deliberately does not
    infer a definition's applicable date from report dates or partial descriptors.
    """
    occurrence = field_occurrence(dataset, row, field_key)

    @cache
    def definition_applies(ref):
        member = catalogue.member(ref)
        return (
            member.effective_from is None
            and member.effective_to is None
            and all(
                definition_applies(dependency)
                for dependency in revision_references(member, include_history=False)
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
        and all(definition_applies(ref) for ref in m.decision_refs)
    )
    return compose_field(
        catalogue, occurrence.published_field, mappings, definition_applies
    )
