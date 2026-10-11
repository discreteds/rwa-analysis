"""Conjunctive occurrence matching; attribute-level composition and conflicts."""

from dataclasses import replace
from functools import cache

from rwa_analysis.extraction.cr6 import (
    CR6_FIELDS,
    BronzeCreditRiskExposureRow,
    Cr6Dataset,
)

from .models import (
    Assertion,
    CatalogueRelease,
    FieldMeaning,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    revision_references,
)


def _matches(mapping, dataset, record, field_key, binding):
    scope, context = mapping.scope, dataset.context
    observed = {
        "document_id": getattr(record, field_key).source_reference.document_id,
        "document_date": context.document_date,
        "dataset_id": dataset.id,
        "template": context.source_template,
        "portfolio": context.source_portfolio_label,
        "field_key": field_key,
        "published_field_ref": binding.published_field_ref,
        "record_id": record.record_id,
        "row_role": record.source_row_role,
        "reporting_entity": context.reporting_entity.value,
        "regulatory_scope": context.regulatory_scope.value,
    }
    return (
        all(
            getattr(scope, key) is None or getattr(scope, key) == value
            for key, value in observed.items()
        )
        and (
            scope.band_ref is None
            or scope.band_ref in record.source_segment_memberships
        )
        and scope.observation_from <= context.observation_date <= scope.observation_to
        and (
            mapping.effective_from is None
            or mapping.effective_from <= context.observation_date
        )
        and (
            mapping.effective_to is None
            or mapping.effective_to >= context.observation_date
        )
    )


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
    if record not in dataset.records:
        raise ValueError("Record does not belong to dataset")
    binding = next(
        b
        for b in dataset.bindings
        if b.typed_field_name == field_key and record.source_row_ref in b.row_refs
    )
    published = next(
        f for f in dataset.published_fields if f.id == binding.published_field_ref
    )
    observation_date = dataset.context.observation_date

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

    mappings = sorted(
        (
            m
            for m in catalogue.members
            if isinstance(m, SourceMappingRevision)
            and _matches(m, dataset, record, field_key, binding)
            and all(definition_applies(ref) for ref in m.decision_refs)
        ),
        key=lambda m: m.revision_id,
    )
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
            and published.source_unit == rule.source_unit
            and published.source_scale == rule.source_scale
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
