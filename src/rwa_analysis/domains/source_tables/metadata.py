"""Assemble flat source/interpretation inputs, retaining scoped ordered references."""

from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef

from .contracts import DECLARATIONS


def capture_rows(rows, resolved):
    """Persist shared definitions once and occurrence-qualified results and links."""
    loaded = resolved.captured
    bundle = loaded.bundle
    slots = {(f.binding_ref, f.slot): f for f in bundle.fragments}

    def emitter(tid):
        def emit(relation_name, **values):
            rows[relation_name].append(
                DECLARATIONS[relation_name].model(
                    silver_revision_id="", table_id=tid, **values
                )
            )

        return emit

    def evidence(emit, kind, key, member, sources):
        for i, r in enumerate(sources):
            emit(
                "evidence",
                owner_kind=kind,
                owner_id=key,
                member=member,
                position=i,
                source_document_id=r.document_id,
                source_pdf_page=r.pdf_page,
                source_printed_page=r.printed_page,
                source_location=r.location,
                source_row=r.row,
                source_column=r.column,
            )

    emit = emitter(bundle.bundle_key)
    for context in bundle.snapshot.contexts:
        emit("contexts", context_revision_id=context.revision_id)
        evidence(
            emit,
            "context_definition",
            context.revision_id,
            "evidence",
            context.evidence,
        )
        from rwa_analysis.catalogue.models import FieldMeaning

        interpretation_rows(
            emit,
            bundle.bundle_key,
            "context_definition",
            context.revision_id,
            "",
            FieldMeaning(None, None, (), context.attributes, None),
        )
        for i, d in enumerate(context.temporal):
            key = context.revision_id + "/" + d.id
            emit(
                "references",
                owner_kind="context_definition",
                owner_id=context.revision_id,
                member="temporal_descriptors",
                position=i,
                target_kind="temporal_descriptor",
                target_id=key,
            )
            emit(
                "temporal_descriptors",
                descriptor_id=key,
                position=i,
                **{
                    name: getattr(d, name)
                    for name in (
                        "source_label",
                        "point",
                        "start",
                        "end",
                        "point_status",
                        "start_status",
                        "end_status",
                        "duration_amount",
                        "duration_unit",
                        "duration_status",
                    )
                },
            )
            evidence(emit, "temporal_descriptor", key, "evidence", d.evidence)
            for j, q in enumerate(d.qualification_refs):
                emit(
                    "references",
                    owner_kind="temporal_descriptor",
                    owner_id=key,
                    member="qualification_refs",
                    position=j,
                    target_kind="comment",
                    target_id=q,
                )
    for binding in bundle.snapshot.occurrences:
        ref = binding.ref
        tid = ref.bundle_key + ("/" + ref.scope if ref.scope else "")
        emit = emitter(tid)
        fragments = [slots[(r.binding_ref, r.slot)] for r in binding.physical_refs]
        emit(
            "occurrences",
            bundle_key=ref.bundle_key,
            output_version=loaded.ref.output_version,
            scope=ref.scope,
            kind=ref.kind,
            local_id=ref.local_id,
            source_text="\n".join(f.text for f in fragments) if fragments else None,
            capture_revision_id=bundle.snapshot.revision_id,
        )
        evidence(
            emit,
            ref.kind,
            ref.local_id,
            "physical_capture",
            (f.evidence for f in fragments),
        )
        for i, link in enumerate(binding.links):
            target = link.target
            emit(
                "occurrence_links",
                owner_kind=ref.kind,
                owner_id=ref.local_id,
                position=i,
                role=link.role,
                target_bundle_key=target.bundle_key,
                target_scope=target.scope,
                target_kind=target.kind,
                target_id=target.local_id,
                target_output_version=target.output_version,
            )
        links = [(key, None, None) for key in binding.context_refs] + [
            (r.context_ref, r.role, r.context_ref + "/" + r.descriptor_ref)
            for r in binding.temporal_roles
        ]
        for i, (key, role, descriptor) in enumerate(links):
            emit(
                "context_bindings",
                owner_kind=ref.kind,
                owner_id=ref.local_id,
                context_revision_id=key,
                role=role,
                descriptor_ref=descriptor,
                position=i,
            )
        if ref.kind != "cell":
            interpretation_rows(
                emit, tid, ref.kind, ref.local_id, "", resolved.meanings[ref]
            )


def source_rows(rows, loaded, table, meanings, catalogue):
    bundle, meta = loaded.bundle, table.metadata
    tid = f"{bundle.bundle_key}/{table.id}"
    base = {"silver_revision_id": "", "table_id": tid}

    def emit(relation_name, **values):
        rows[relation_name].append(DECLARATIONS[relation_name].model(**base, **values))

    def references(kind, id, member, values, target_kind=None):
        for i, value in enumerate(values):
            emit(
                "references",
                owner_kind=kind,
                owner_id=id,
                member=member,
                position=i,
                target_kind=target_kind if target_kind else value.kind,
                target_id=value if target_kind else value.id,
            )

    def evidence(kind, id, member, values):
        for i, r in enumerate(values):
            emit(
                "evidence",
                owner_kind=kind,
                owner_id=id,
                member=member,
                position=i,
                source_document_id=r.document_id,
                source_pdf_page=r.pdf_page,
                source_printed_page=r.printed_page,
                source_location=r.location,
                source_row=r.row,
                source_column=r.column,
            )

    def attributes(kind, id, values):
        for i, (name, a) in enumerate(values):
            emit(
                "source_attributes",
                owner_kind=kind,
                owner_id=id,
                name=name,
                position=i,
                value=a.value,
                status=a.status,
            )
            references(
                "source_attribute",
                f"{kind}/{id}/{name}",
                "qualification_refs",
                a.qualification_refs,
                "qualification",
            )

    ctx = meta.context
    emit(
        "tables",
        position=next(i for i, ds in enumerate(bundle.datasets) if ds.id == table.id),
        bundle_key=bundle.bundle_key,
        output_version=loaded.ref.output_version,
        document_id=bundle.document.document_id,
        organisation_id=bundle.document.organisation_id,
        dataset_id=table.id,
        context_id=ctx.id,
        document_date=ctx.document_date,
        publication_date=bundle.document.publication_date,
        source_date_label=ctx.source_date_label,
        source_template=ctx.source_template,
        source_title=ctx.source_title,
        source_portfolio_label=ctx.source_portfolio_label,
    )
    attributes(
        "context",
        ctx.id,
        (
            (name, getattr(ctx, name))
            for name in (
                "reporting_entity",
                "consolidation_scope",
                "regulatory_scope",
                "geography",
                "currency",
            )
        ),
    )
    references(
        "context", ctx.id, "qualification_refs", ctx.qualification_refs, "qualification"
    )
    evidence("context", ctx.id, "evidence", ctx.evidence)
    for i, f in enumerate(meta.published_fields):
        emit(
            "fields",
            field_id=f.id,
            position=i,
            source_label=f.source_label,
            source_unit=f.source_unit,
            source_scale=f.source_scale,
            value_kind=f.value_kind,
            result_kind=f.result_kind,
            source_form=f.source_form,
        )
        references("field", f.id, "header_path_refs", f.header_path_refs, "axis")
        references(
            "field", f.id, "qualification_refs", f.qualification_refs, "qualification"
        )
        attributes("field", f.id, ((a.name, a) for a in f.attributes))
        evidence("field", f.id, "source_reference", (f.source_reference,))
    for a in meta.axes:
        emit(
            "axes",
            axis_id=a.id,
            kind=a.axis,
            source_label=a.source_label,
            position=a.order,
        )
        references("axis", a.id, "header_path_refs", a.header_path_refs, "axis")
        references("axis", a.id, "context_refs", a.context_refs, "context")
        references(
            "axis", a.id, "qualification_refs", a.qualification_refs, "qualification"
        )
        evidence("axis", a.id, "source_reference", (a.source_reference,))
    for i, s in enumerate(meta.segmentations):
        emit(
            "segmentations",
            segmentation_id=s.id,
            source_dimension=s.source_dimension,
            position=i,
        )
        attributes(
            "segmentation",
            s.id,
            (("completeness", s.completeness), ("disjointness", s.disjointness)),
        )
        references("segmentation", s.id, "context_refs", s.context_refs, "context")
        evidence("segmentation", s.id, "evidence", s.evidence)
        for b in s.bands:
            emit(
                "bands",
                band_id=b.id,
                segmentation_id=s.id,
                source_label=b.source_label,
                position=b.order,
                kind=b.kind,
                unit=b.unit,
                lower=b.lower,
                upper=b.upper,
                lower_inclusive=b.lower_inclusive,
                upper_inclusive=b.upper_inclusive,
                lower_status=b.lower_status,
                upper_status=b.upper_status,
                category=b.category,
            )
            evidence("band", b.id, "source_reference", (b.source_reference,))
    for i, q in enumerate(meta.qualifications):
        emit(
            "qualifications",
            qualification_id=q.id,
            position=i,
            source_text=q.source_text,
        )
        references("qualification", q.id, "scope", q.scope)
        evidence("qualification", q.id, "evidence", q.evidence)
    for i, r in enumerate(meta.relationships):
        emit(
            "relationships",
            relationship_id=r.id,
            position=i,
            kind=r.kind,
            source_label=r.source_label,
            exhaustive=r.exhaustive,
            mutually_exclusive=r.mutually_exclusive,
        )
        references("relationship", r.id, "parent", (r.parent,))
        references("relationship", r.id, "children", r.children)
        references("relationship", r.id, "scope", r.scope)
        evidence("relationship", r.id, "evidence", r.evidence)
    for i, d in enumerate(meta.temporal_descriptors):
        emit(
            "temporal_descriptors",
            descriptor_id=d.id,
            position=i,
            source_label=d.source_label,
            **{
                name: getattr(d, name)
                for name in (
                    "point",
                    "start",
                    "end",
                    "point_status",
                    "start_status",
                    "end_status",
                    "duration_amount",
                    "duration_unit",
                    "duration_status",
                )
            },
        )
        references(
            "temporal_descriptor",
            d.id,
            "qualification_refs",
            d.qualification_refs,
            "qualification",
        )
        evidence("temporal_descriptor", d.id, "evidence", d.evidence)
    for i, b in enumerate(meta.temporal_bindings):
        emit(
            "temporal_bindings",
            cell_id=b.cell_id,
            role=b.role,
            descriptor_ref=b.descriptor_ref,
            position=i,
        )
    fields = {f.id: f for f in meta.published_fields}
    for i, c in enumerate(table.cells):
        value, f, meaning = c.value, fields[c.field_ref], meanings[c.id]
        emit(
            "cells",
            cell_id=c.id,
            field_id=c.field_ref,
            position=i,
            row_ref=c.row_ref,
            column_ref=c.column_ref,
            value_kind=c.value_kind,
            source_number=value.value if c.value_kind == "decimal" else None,
            source_count=value.value if c.value_kind == "integer" else None,
            source_text=value.value if c.value_kind == "text" else None,
            original_text=value.original_text,
            displayed_precision=getattr(value, "displayed_precision", None),
            missing_reason=value.missing_reason,
            source_row_role=c.source_row_role,
        )
        references("cell", c.id, "context_refs", c.context_refs, "context")
        references("cell", c.id, "segment_refs", c.segment_refs, "band")
        references(
            "cell",
            c.id,
            "source_aggregation_scope",
            c.source_aggregation_scope,
            "block",
        )
        references(
            "cell", c.id, "qualification_refs", c.qualification_refs, "qualification"
        )
        evidence("cell", c.id, "source_reference", (value.source_reference,))
        emit(
            "meanings",
            cell_id=c.id,
            field_id=c.field_ref,
            catalogue_release_id=catalogue.id,
            concept_revision_ref=meaning.concept_ref.revision_id
            if meaning.concept_ref
            else None,
            measure_revision_ref=meaning.measure_ref.revision_id
            if meaning.measure_ref
            else None,
            result_kind=f.result_kind,
            unit_factor=meaning.unit_factor,
            normalised_amount=None,
            normalised_scalar=None,
            normalised_count=None,
            value_state="source_missing"
            if value.value is None
            else "not_conformed"
            if meaning.unit_factor is None and c.value_kind != "text"
            else "present",
        )
        interpretation_rows(emit, tid, "cell", c.id, c.field_ref, meaning)


def interpretation_rows(emit, tid, kind, owner_id, field_key, meaning):
    oid = tid + "/" + ("" if kind == "cell" else kind + "/") + owner_id
    for pos, mapping in enumerate(meaning.mapping_refs):
        emit(
            "mapping_refs",
            observation_id=oid,
            field_key=field_key,
            owner_kind=kind,
            owner_id=owner_id,
            reference_kind=mapping.kind,
            position=pos,
            mapping_revision_ref=mapping.revision_id,
        )
    for pos, attribute in enumerate(meaning.attributes):
        for idx, assertion in enumerate((attribute, *attribute.alternatives)):
            key = {
                "observation_id": oid,
                "field_key": field_key,
                "owner_kind": kind,
                "owner_id": owner_id,
                "name": attribute.name,
                "assertion_index": idx,
            }
            v = assertion.value
            emit(
                "attributes",
                **key,
                position=pos,
                status=assertion.status,
                value_text=v if type(v) is str else None,
                value_integer=v if type(v) is int else None,
                value_boolean=v if type(v) is bool else None,
                value_revision_kind=v.kind if isinstance(v, RevisionRef) else None,
                value_revision_id=v.revision_id if isinstance(v, RevisionRef) else None,
                value_bundle_key=v.bundle_key if isinstance(v, EvidenceRef) else None,
                value_document_id=v.document_id if isinstance(v, EvidenceRef) else None,
                value_dataset_id=v.dataset_id if isinstance(v, EvidenceRef) else None,
                value_ref_kind=v.kind if isinstance(v, EvidenceRef) else None,
                value_ref_id=v.ref_id if isinstance(v, EvidenceRef) else None,
            )
            for j, e in enumerate(assertion.evidence_refs):
                emit(
                    "attribute_evidence",
                    **key,
                    position=j,
                    bundle_key=e.bundle_key,
                    document_id=e.document_id,
                    dataset_id=e.dataset_id,
                    kind=e.kind,
                    ref_id=e.ref_id,
                )
            for j, d in enumerate(assertion.decision_refs):
                emit(
                    "attribute_decisions",
                    **key,
                    position=j,
                    decision_kind=d.kind,
                    decision_revision_id=d.revision_id,
                )
