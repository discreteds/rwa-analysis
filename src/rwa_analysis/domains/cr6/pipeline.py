"""Source-bound CR6 conformance using dataset-wide Mountainash expressions."""

from dataclasses import fields
from decimal import Decimal

import mountainash as ma
import polars as pl
from mountainash.typespec.converters import to_polars_schema

from rwa_analysis.catalogue.models import CatalogueRelease, RevisionRef
from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.extraction.cr6 import Cr6Dataset
from rwa_analysis.storage.bronze import LoadedBronze

from .contracts import (
    CONTEXT_SPEC,
    IDENTITY_SPEC,
    MEASURES,
    TABLES,
)
from .models import (
    FIELD_MAP,
    Cr6Output,
    RowIdentity,
    SilverContext,
    SilverField,
    SilverObservationRelationship,
    SilverSegment,
    SourceNumbers,
    StoredAttribute,
    stored_assertion,
)


def source_ids(bundle, dataset, record=None):
    prefix = f"{bundle.bundle_key}/{dataset.id}"
    return f"{prefix}/{record.record_id if record else dataset.metadata.context.id}"


def ingress(rows, spec):
    """Native dataclass ingress, with a typed empty collection."""
    relation = ma.relation(
        rows if rows else pl.DataFrame(schema=to_polars_schema(spec))
    )
    return relation.conform(spec)


def source_scale(rows, name):
    """Decimal scale needed by the arithmetic operands, without changing inputs."""
    return max(
        (
            max(0, -value.as_tuple().exponent)
            for row in rows
            if (value := getattr(row, name)) is not None
        ),
        default=0,
    )


def convert_dataset(source, factors, columns):
    """Widen operands before multiplication, then apply declared measure types."""
    values = ma.relation(source)
    multipliers = ma.relation(factors).select(
        "observation_id", *(ma.col(name).alias(f"{name}__factor") for name in columns)
    )
    expressions = []
    for name, target in columns.items():
        scale = source_scale(source, name) + source_scale(factors, name)
        working = pl.Decimal(38, scale)
        dtype = (
            pl.Int64
            if target == "reported_entity_count"
            else pl.Decimal(MEASURES[target].precision, MEASURES[target].scale)
        )
        value = ma.col(name).cast(working) * ma.col(f"{name}__factor").cast(working)
        expressions.append(value.cast(dtype).alias(target))
    return values.join(multipliers, on="observation_id").select(
        "observation_id", *expressions
    )


def field_row(bundle, ref, ds, record, source, target, meaning, catalogue):
    cell = getattr(record, source)
    binding = next(
        b
        for b in ds.metadata.bindings
        if b.typed_field_name == source and record.source_row_ref in b.row_refs
    )
    published = next(
        f for f in ds.metadata.published_fields if f.id == binding.published_field_ref
    )
    state = (
        "source_missing"
        if cell.value is None
        else "not_conformed"
        if meaning.unit_factor is None
        else "present"
    )
    reason = (
        "source unit/scale conversion unresolved or conflicting"
        if state == "not_conformed"
        else None
    )
    currency = meaning.attribute("currency")

    def revision(value):
        return value.revision_id if isinstance(value, RevisionRef) else None

    attributes = []
    for attribute in meaning.attributes:
        stored = stored_assertion(attribute)
        attributes.append(
            StoredAttribute(
                stored.value,
                stored.status,
                stored.evidence_refs,
                stored.decision_refs,
                attribute.name,
                tuple(stored_assertion(a) for a in attribute.alternatives),
            )
        )
    return SilverField(
        silver_revision_id="",
        observation_id=source_ids(bundle, ds, record),
        field_key=target,
        catalogue_release_id=catalogue.id,
        concept_revision_ref=revision(meaning.concept_ref),
        measure_revision_ref=revision(meaning.measure_ref),
        result_unit_revision_ref=revision(meaning.attribute("result_unit").value),
        value_state=state,
        currency_code=currency.value,
        currency_status=currency.status,
        attributes=tuple(attributes),
        bundle_key=bundle.bundle_key,
        output_version=ref.output_version,
        document_id=bundle.document.document_id,
        dataset_id=ds.id,
        source_record_id=record.record_id,
        source_field_key=source,
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
        unit_factor=str(meaning.unit_factor)
        if meaning.unit_factor is not None
        else None,
        selection_role="selected_value",
        conversion_reason=reason,
        transformation_description="source missing"
        if cell.value is None
        else reason or f"multiply source value by {meaning.unit_factor}",
        qualification_refs=tuple(
            dict.fromkeys(
                (
                    *ds.metadata.context.qualification_refs,
                    *binding.qualification_refs,
                    *published.qualification_refs,
                )
            )
        ),
        source_reference=cell.source_reference,
        mapping_revision_refs=tuple(m.revision_id for m in meaning.mapping_refs),
    )


class Cr6Pipeline:
    def conform(
        self, inputs: tuple[LoadedBronze, ...], catalogue: CatalogueRelease
    ) -> Cr6Output:
        (
            contexts,
            segments,
            relationships,
            identities,
            source_rows,
            factor_rows,
            field_rows,
        ) = ([] for _ in range(7))
        for loaded in inputs:
            bundle, ref = loaded.bundle, loaded.ref
            for ds in bundle.datasets:
                if not isinstance(ds, Cr6Dataset):
                    continue
                ctx = ds.metadata.context
                cid = source_ids(bundle, ds)
                contexts.append(
                    SilverContext(
                        "",
                        cid,
                        bundle.bundle_key,
                        ref.output_version,
                        bundle.document.document_id,
                        ds.id,
                        ctx.id,
                        bundle.document.organisation_id,
                        **{
                            f.name: getattr(ctx, f.name)
                            for f in fields(ctx)
                            if f.name != "id"
                        },
                    )
                )
                for segmentation in ds.metadata.segmentations:
                    for band in segmentation.bands:
                        segments.append(
                            SilverSegment(
                                "",
                                f"{cid}/{band.id}",
                                cid,
                                segmentation.id,
                                band.id,
                                band.source_label,
                                band.kind,
                                band.category,
                                band.lower if band.unit == "%" else None,
                                band.upper if band.unit == "%" else None,
                                band.lower_inclusive,
                                band.upper_inclusive,
                                band.lower_status,
                                band.upper_status,
                                band.source_reference,
                            )
                        )
                row_ids = {
                    r.source_row_ref: source_ids(bundle, ds, r)
                    for r in ds.exposure_rows
                }
                for relationship in ds.metadata.relationships:
                    for child in relationship.children:
                        relationships.append(
                            SilverObservationRelationship(
                                "",
                                f"{cid}/{relationship.id}/{child.id}",
                                cid,
                                row_ids[relationship.parent.id],
                                row_ids[child.id],
                                relationship.id,
                                relationship.source_label,
                                relationship.kind,
                                relationship.exhaustive,
                                relationship.mutually_exclusive,
                                relationship.evidence,
                            )
                        )
                for record in ds.exposure_rows:
                    oid = source_ids(bundle, ds, record)
                    meanings = {
                        name: resolve_field(catalogue, ds, record, name)
                        for name in FIELD_MAP
                    }
                    roles = {
                        (m.attribute("row_role").value, m.attribute("row_role").status)
                        for m in meanings.values()
                    }
                    role, status = (
                        next(iter(roles)) if len(roles) == 1 else (None, "conflicting")
                    )
                    identities.append(
                        RowIdentity(
                            "",
                            oid,
                            cid,
                            f"{cid}/{record.source_segment_memberships[0]}"
                            if record.source_segment_memberships
                            else None,
                            record.record_id,
                            record.source_row_ref,
                            record.source_row_role,
                            role,
                            status,
                        )
                    )
                    source_rows.append(
                        SourceNumbers(
                            oid,
                            **{
                                name: Decimal(value)
                                if (value := getattr(record, name).value) is not None
                                else None
                                for name in FIELD_MAP
                            },
                        )
                    )
                    factor_rows.append(
                        SourceNumbers(
                            oid,
                            **{name: meanings[name].unit_factor for name in FIELD_MAP},
                        )
                    )
                    field_rows.extend(
                        field_row(
                            bundle,
                            ref,
                            ds,
                            record,
                            name,
                            target,
                            meanings[name],
                            catalogue,
                        )
                        for name, target in FIELD_MAP.items()
                    )

        if not source_rows:
            return Cr6Output(**{table.member: ingress([], table.spec) for table in TABLES})

        values = convert_dataset(source_rows, factor_rows, FIELD_MAP)
        # Bounds retain their source coefficients until the relation conversion.
        bounds = ma.relation(segments).with_columns(
            *(
                (
                    ma.col(name).cast(pl.Decimal(38, source_scale(segments, name) + 2))
                    * ma.lit(Decimal("0.01")).cast(
                        pl.Decimal(38, source_scale(segments, name) + 2)
                    )
                )
                .cast(pl.Decimal(16, 8))
                .alias(name)
                for name in ("lower_fraction", "upper_fraction")
            )
        )
        observations = (
            ingress(identities, IDENTITY_SPEC)
            .join(values, on="observation_id")
            .join(
                ingress(contexts, CONTEXT_SPEC),
                on=["silver_revision_id", "context_id"],
            )
            .join(
                bounds.drop("context_id"),
                on=["silver_revision_id", "segment_id"],
                how="left",
            )
            .select(*TABLES[0].spec.field_names)
        )
        return Cr6Output(
            observations.conform(TABLES[0].spec),
            ingress(field_rows, TABLES[1].spec),
            ingress(relationships, TABLES[2].spec),
        )
