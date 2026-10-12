"""Assemble flat metadata records for native Mountainash ingress.

Source objects retain their composition. No recursive asdict/inference adapter is
needed for these explicit flat declarations; relational calculations live in pipeline.
"""

from dataclasses import fields

from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef
from rwa_analysis.domains.cr6.models import (
    AttributeDecision,
    AttributeEvidence,
    ContextEvidence,
    ContextQualification,
    FieldAttribute,
    FieldMapping,
    FieldQualification,
    RelationshipEvidence,
    SilverField,
)

from .models import (
    SilverContext,
    SilverRelationship,
    SilverTemporalBinding,
    SilverTemporalDescriptor,
    TemporalEvidence,
)

KNOWLEDGE = (
    "reporting_entity",
    "consolidation_scope",
    "regulatory_scope",
    "geography",
    "currency",
)


def location(ref):
    return {f"source_{f.name}": getattr(ref, f.name) for f in fields(ref)}


def ids(bundle, dataset, record=None):
    prefix = f"{bundle.bundle_key}/{dataset.id}"
    return f"{prefix}/{record.record_id if record else dataset.metadata.context.id}"


def descriptor_id(bundle, dataset, ref):
    return f"{bundle.bundle_key}/{dataset.id}/temporal/{ref}"


def context_rows(tables, loaded, ds):
    bundle, ref = loaded.bundle, loaded.ref
    context, cid = ds.metadata.context, ids(bundle, ds)
    knowledge = {
        f"{name}_{part}": getattr(getattr(context, name), part)
        for name in KNOWLEDGE
        for part in ("value", "status")
    }
    tables["contexts"].append(
        SilverContext(
            "",
            cid,
            bundle.bundle_key,
            ref.output_version,
            bundle.document.document_id,
            ds.id,
            context.id,
            bundle.document.organisation_id,
            context.document_date,
            bundle.document.publication_date,
            context.source_template,
            context.source_title,
            context.source_portfolio_label,
            **knowledge,
        )
    )
    for member in ("context", *KNOWLEDGE):
        value = context if member == "context" else getattr(context, member)
        for position, q in enumerate(value.qualification_refs):
            tables["context_qualifications"].append(
                ContextQualification("", cid, member, position, q)
            )
    for position, evidence in enumerate(context.evidence):
        tables["context_evidence"].append(
            ContextEvidence(
                **location(evidence),
                silver_revision_id="",
                context_id=cid,
                position=position,
            )
        )
    for descriptor in ds.metadata.temporal_descriptors:
        did = descriptor_id(bundle, ds, descriptor.id)
        tables["temporal_descriptors"].append(
            SilverTemporalDescriptor(
                "",
                did,
                cid,
                descriptor.id,
                descriptor.source_label,
                descriptor.point,
                descriptor.point_status,
                descriptor.start,
                descriptor.start_status,
                descriptor.end,
                descriptor.end_status,
                descriptor.duration_amount,
                descriptor.duration_unit,
                descriptor.duration_status,
            )
        )
        for position, evidence in enumerate(descriptor.evidence):
            tables["temporal_evidence"].append(
                TemporalEvidence(
                    **location(evidence),
                    silver_revision_id="",
                    descriptor_id=did,
                    position=position,
                )
            )
    rows = {r.record_id: r for r in ds.backtesting_rows}
    for binding in ds.metadata.temporal_bindings:
        tables["temporal_bindings"].append(
            SilverTemporalBinding(
                "",
                ids(bundle, ds, rows[binding.record_id]),
                binding.field_key,
                binding.role,
                descriptor_id(bundle, ds, binding.descriptor_ref),
            )
        )


def field_rows(tables, loaded, ds, row, name, meaning, catalogue):
    bundle, ref = loaded.bundle, loaded.ref
    oid, cell = ids(bundle, ds, row), getattr(row, name)
    binding = next(
        b
        for b in ds.metadata.bindings
        if b.typed_field_name == name and row.source_row_ref in b.row_refs
    )
    published = next(
        f for f in ds.metadata.published_fields if f.id == binding.published_field_ref
    )
    factor = meaning.unit_factor
    state = (
        "source_missing"
        if cell.value is None
        else "not_conformed"
        if factor is None
        else "present"
    )
    currency = meaning.attribute("currency")

    def revision(value):
        return value.revision_id if isinstance(value, RevisionRef) else None

    tables["fields"].append(
        SilverField(
            **location(cell.source_reference),
            silver_revision_id="",
            observation_id=oid,
            field_key=name,
            catalogue_release_id=catalogue.id,
            concept_revision_ref=revision(meaning.concept_ref),
            measure_revision_ref=revision(meaning.measure_ref),
            result_unit_revision_ref=revision(meaning.attribute("result_unit").value),
            value_state=state,
            currency_code=currency.value,
            currency_status=currency.status,
            bundle_key=bundle.bundle_key,
            output_version=ref.output_version,
            document_id=bundle.document.document_id,
            dataset_id=ds.id,
            source_record_id=row.record_id,
            source_field_key=name,
            binding_ref=binding.id,
            published_field_ref=published.id,
            source_value=str(cell.value) if cell.value is not None else None,
            original_text=cell.original_text,
            displayed_precision=cell.displayed_precision,
            missing_reason=cell.missing_reason,
            source_unit=published.source_unit,
            source_scale=str(published.source_scale)
            if published.source_scale is not None
            else None,
            unit_factor=str(factor) if factor is not None else None,
            selection_role="selected",
            conversion_reason=None
            if factor is not None
            else "unresolved unit conversion",
            transformation_description="source value multiplied by selected unit factor",
        )
    )
    descriptors = {d.id: d for d in ds.metadata.temporal_descriptors}
    temporal_qualifiers = tuple(
        q
        for b in ds.metadata.temporal_bindings
        if b.record_id == row.record_id and b.field_key == name
        for q in descriptors[b.descriptor_ref].qualification_refs
    )
    for position, q in enumerate(
        dict.fromkeys(
            (
                *ds.metadata.context.qualification_refs,
                *binding.qualification_refs,
                *published.qualification_refs,
                *temporal_qualifiers,
            )
        )
    ):
        tables["field_qualifications"].append(
            FieldQualification("", oid, name, position, q)
        )
    for position, mapping in enumerate(meaning.mapping_refs):
        tables["field_mappings"].append(
            FieldMapping("", oid, name, position, mapping.revision_id)
        )
    for position, attribute in enumerate(meaning.attributes):
        assertions = (attribute, *attribute.alternatives)
        for index, assertion in enumerate(assertions):
            value = assertion.value
            key = {
                "silver_revision_id": "",
                "observation_id": oid,
                "field_key": name,
                "name": attribute.name,
                "assertion_index": index,
            }
            tables["attributes"].append(
                FieldAttribute(
                    **key,
                    position=position,
                    status=assertion.status,
                    value_text=value if type(value) is str else None,
                    value_integer=value if type(value) is int else None,
                    value_boolean=value if type(value) is bool else None,
                    value_revision_kind=value.kind
                    if isinstance(value, RevisionRef)
                    else None,
                    value_revision_id=value.revision_id
                    if isinstance(value, RevisionRef)
                    else None,
                    value_bundle_key=value.bundle_key
                    if isinstance(value, EvidenceRef)
                    else None,
                    value_document_id=value.document_id
                    if isinstance(value, EvidenceRef)
                    else None,
                    value_dataset_id=value.dataset_id
                    if isinstance(value, EvidenceRef)
                    else None,
                    value_ref_kind=value.kind
                    if isinstance(value, EvidenceRef)
                    else None,
                    value_ref_id=value.ref_id
                    if isinstance(value, EvidenceRef)
                    else None,
                )
            )
            for pos, evidence in enumerate(assertion.evidence_refs):
                tables["attribute_evidence"].append(
                    AttributeEvidence(
                        **key,
                        position=pos,
                        bundle_key=evidence.bundle_key,
                        document_id=evidence.document_id,
                        dataset_id=evidence.dataset_id,
                        kind=evidence.kind,
                        ref_id=evidence.ref_id,
                    )
                )
            for pos, decision in enumerate(assertion.decision_refs):
                tables["attribute_decisions"].append(
                    AttributeDecision(
                        **key,
                        position=pos,
                        decision_kind=decision.kind,
                        decision_revision_id=decision.revision_id,
                    )
                )


def relationship_rows(tables, bundle, ds):
    rows = {r.source_row_ref: r for r in ds.backtesting_rows}
    field_names = {
        b.published_field_ref: b.typed_field_name for b in ds.metadata.bindings
    }
    for rel in ds.metadata.relationships:
        for child in rel.children:
            if rel.parent.kind == "row" and child.kind == "row":
                edges = [(rows[rel.parent.id], None, rows[child.id], None)]
            else:
                # A source field relationship applies within its explicitly scoped rows.
                scoped = [s.id for s in rel.scope if s.kind == "row"]
                selected = [rows[r] for r in scoped] if scoped else list(rows.values())
                edges = [
                    (r, field_names[rel.parent.id], r, field_names[child.id])
                    for r in selected
                ]
            for parent_row, parent_field, child_row, child_field in edges:
                rid = f"{ids(bundle, ds)}/{rel.id}/{parent_row.record_id}/{child_row.record_id}/{child.id}"
                tables["relationships"].append(
                    SilverRelationship(
                        "",
                        rid,
                        ids(bundle, ds),
                        ids(bundle, ds, parent_row),
                        parent_field,
                        ids(bundle, ds, child_row),
                        child_field,
                        rel.id,
                        rel.source_label,
                        rel.kind,
                        rel.exhaustive,
                        rel.mutually_exclusive,
                    )
                )
                for position, evidence in enumerate(rel.evidence):
                    tables["relationship_evidence"].append(
                        RelationshipEvidence(
                            **location(evidence),
                            silver_revision_id="",
                            relationship_id=rid,
                            position=position,
                        )
                    )
