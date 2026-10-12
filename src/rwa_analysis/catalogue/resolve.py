"""Conjunctive occurrence matching; attribute-level composition and conflicts."""

from dataclasses import dataclass, fields, replace
from functools import cache

from rwa_analysis.extraction.cr6 import (
    CR6_FIELDS,
    BronzeCreditRiskExposureRow,
    Cr6Dataset,
)
from rwa_analysis.extraction.models import PublishedField
from rwa_analysis.extraction.temporal import TemporalBinding

from .models import (
    Assertion,
    CatalogueRelease,
    FieldMeaning,
    MappingScope,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    revision_references,
)


@dataclass(frozen=True)
class FieldOccurrence:
    """Source occurrence, independent of a domain's numeric row collection."""

    scope: MappingScope
    published_field: PublishedField
    segment_memberships: tuple[str, ...]
    temporal_bindings: tuple[TemporalBinding, ...] = ()


def field_occurrence(dataset, record, field_key):
    context = dataset.metadata.context
    binding = next(
        b
        for b in dataset.metadata.bindings
        if b.typed_field_name == field_key and record.source_row_ref in b.row_refs
    )
    published = next(
        f
        for f in dataset.metadata.published_fields
        if f.id == binding.published_field_ref
    )
    return FieldOccurrence(
        MappingScope(
            document_id=getattr(record, field_key).source_reference.document_id,
            document_date=context.document_date,
            dataset_id=dataset.id,
            template=context.source_template,
            portfolio=context.source_portfolio_label,
            field_key=field_key,
            published_field_ref=binding.published_field_ref,
            record_id=record.record_id,
            row_role=record.source_row_role,
            reporting_entity=context.reporting_entity.value,
            regulatory_scope=context.regulatory_scope.value,
        ),
        published,
        record.source_segment_memberships,
        tuple(
            b
            for b in dataset.metadata.temporal_bindings
            if b.record_id == record.record_id and b.field_key == field_key
        ),
    )


def matches_occurrence(mapping, occurrence):
    """Conjunctive source identity; temporal applicability belongs to the adapter."""
    scope = mapping.scope
    return all(
        getattr(scope, f.name) is None
        or getattr(scope, f.name) == getattr(occurrence.scope, f.name)
        for f in fields(scope)
        if f.name not in ("observation_from", "observation_to", "band_ref")
    ) and (scope.band_ref is None or scope.band_ref in occurrence.segment_memberships)


def _unique(values):
    return tuple(dict.fromkeys(values))


def _combine(name, assertions):
    evidence = _unique(
        e for a in assertions for s in a.assertions() for e in s.evidence_refs
    )
    decisions = _unique(
        d for a in assertions for s in a.assertions() for d in s.decision_refs
    )
    # Unknown information does not contradict a supported assertion, but its
    # evidence remains attached. Provisional support never becomes established.
    known = [a for a in assertions if a.status != "unresolved"]
    values = _unique(a.value for a in known)
    statuses = {a.status for a in known}
    conflict = (
        len(values) > 1
        or "conflicting" in statuses
        or ("not_applicable" in statuses and len(statuses) > 1)
    )
    if conflict:
        alternatives = _unique(
            alternative
            for a in assertions
            for alternative in (
                a.alternatives
                or (Assertion(a.value, a.status, a.evidence_refs, a.decision_refs),)
            )
        )
        return SemanticAttribute(
            name=name,
            value=None,
            status="conflicting",
            evidence_refs=evidence,
            decision_refs=decisions,
            alternatives=alternatives,
        )
    status = (
        "unresolved"
        if not known
        else ("provisional" if "provisional" in statuses else known[0].status)
    )
    return SemanticAttribute(
        name=name,
        value=values[0] if values else None,
        status=status,
        evidence_refs=evidence,
        decision_refs=decisions,
    )


def resolve_field(
    catalogue: CatalogueRelease,
    dataset: Cr6Dataset,
    record: BronzeCreditRiskExposureRow,
    field_key: str,
) -> FieldMeaning:
    if field_key not in CR6_FIELDS:
        raise ValueError(f"Unknown CR6 field: {field_key}")
    if record not in dataset.exposure_rows:
        raise ValueError("Record does not belong to dataset")
    occurrence = field_occurrence(dataset, record, field_key)
    observation_date = dataset.metadata.context.observation_date

    @cache
    def definition_applies(ref):
        member = catalogue.member(ref)
        return (
            (member.effective_from is None or member.effective_from <= observation_date)
            and (member.effective_to is None or observation_date <= member.effective_to)
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
        and (
            m.scope.observation_from is None
            or m.scope.observation_from <= observation_date
        )
        and (
            m.scope.observation_to is None or observation_date <= m.scope.observation_to
        )
        and (m.effective_from is None or m.effective_from <= observation_date)
        and (m.effective_to is None or observation_date <= m.effective_to)
        and all(definition_applies(ref) for ref in m.decision_refs)
    )
    return compose_field(
        catalogue, occurrence.published_field, mappings, definition_applies
    )


def compose_field(catalogue, published_field, applicable_mappings, definition_applies):
    """Compose domain-selected meaning, retaining conflicts and partial knowledge."""
    mappings = sorted(applicable_mappings, key=lambda m: m.revision_id)
    # A correction replaces a whole predecessor mapping for this occurrence.
    # Keep every historical member available through catalogue.member(), but
    # never execute superseded ancestors alongside an applicable correction.
    superseded = set()

    def retain_history(mapping):
        for ref in mapping.supersedes_refs:
            if ref.kind == "mapping" and ref.revision_id not in superseded:
                superseded.add(ref.revision_id)
                retain_history(catalogue.member(ref))

    for mapping in mappings:
        retain_history(mapping)
    mappings = [m for m in mappings if m.revision_id not in superseded]
    candidates = {}
    conversions = []
    for mapping in mappings:
        attrs = list(mapping.attributes)
        if mapping.measure_ref and definition_applies(mapping.measure_ref):
            measure = catalogue.member(mapping.measure_ref)
            attrs.extend(measure.attributes)
            attrs.extend(
                [
                    SemanticAttribute(
                        name="measure", value=mapping.measure_ref, status="established"
                    ),
                    SemanticAttribute(
                        name="concept", value=measure.concept_ref, status="established"
                    ),
                    SemanticAttribute(
                        name="result_unit",
                        value=measure.result_unit_ref,
                        status="established",
                    ),
                ]
            )
        if mapping.concept_ref and definition_applies(mapping.concept_ref):
            attrs.append(
                SemanticAttribute(
                    name="concept", value=mapping.concept_ref, status="established"
                )
            )
        for attr in attrs:
            if not all(definition_applies(ref) for ref in revision_references(attr)):
                continue
            # Only the mapping's own source support is added; unrelated field
            # qualifiers are not propagated from neighboring measures.
            if attr.name in ("concept", "measure", "result_unit"):
                attr = replace(
                    attr,
                    evidence_refs=_unique(attr.evidence_refs + mapping.evidence_refs),
                    decision_refs=_unique(attr.decision_refs + mapping.decision_refs),
                )
            candidates.setdefault(attr.name, []).append((mapping, attr))
        rule = mapping.conversion
        if (
            rule
            and published_field.source_unit == rule.source_unit
            and published_field.source_scale == rule.source_scale
        ):
            conversions.append((mapping, rule.unit_factor))

    def surviving(items):
        overridden = {
            ref.revision_id for mapping, _ in items for ref in mapping.overrides_refs
        }
        return [
            value for mapping, value in items if mapping.revision_id not in overridden
        ]

    attributes = tuple(
        _combine(name, surviving(items)) for name, items in sorted(candidates.items())
    )
    factors = _unique(surviving(conversions))
    view = FieldMeaning(
        None,
        None,
        tuple(RevisionRef("mapping", m.revision_id) for m in mappings),
        attributes,
        factors[0] if len(factors) == 1 else None,
    )
    return replace(
        view,
        concept_ref=view.attribute("concept").value,
        measure_ref=view.attribute("measure").value,
    )
