"""Conform twelve source-bound measures together through Mountainash relations."""

from dataclasses import fields
from decimal import Decimal

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.models import CatalogueRelease, RevisionRef
from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.extraction.cr6 import ExtractionBundle
from rwa_analysis.storage.bronze import BronzeRef

from .models import (
    DECIMAL,
    FIELD_MAP,
    PROJECTION_SCHEMAS,
    SCHEMAS,
    SilverCandidate,
    SilverContext,
    SilverFieldInterpretation,
    SilverObservationRelationship,
    SilverSegment,
    SourceLineage,
    frame,
    tabular,
)


def decimal_type(values, path):
    """Choose a lossless Arrow working scale from source coefficients, not results."""
    present = [Decimal(v) for v in values if v is not None]
    if any(not v.is_finite() for v in present):
        raise ValueError(f"{path}: nonfinite source value")
    scale = max((max(0, -v.as_tuple().exponent) for v in present), default=0)
    integers = max((max(0, v.adjusted() + 1) for v in present), default=0)
    if scale + integers > 38:
        raise ValueError(f"{path}: source exceeds Decimal working precision")
    return pl.Decimal(38, scale)


def convert_dataset(source, factors, identity, columns):
    """Join selected factors once and convert all rows with column expressions."""
    relation = ma.relation(source).join(factors, on=identity)
    expressions = []
    for name, target in columns.items():
        dtype = pl.Int64 if target == "reported_entity_count" else DECIMAL
        scale = source.schema[name].scale + factors.schema[f"{name}__factor"].scale
        if scale > 38:
            raise ValueError(f"{name}: conversion exceeds Decimal working scale")
        working = pl.Decimal(38, scale)
        # Polars multiplication retains the operands' common scale; widen it
        # before multiplying so percent fractions are not rounded to source scale.
        value = ma.col(name).cast(working) * ma.col(f"{name}__factor").cast(working)
        try:
            check = relation.select(
                *identity, value.alias("value"), value.cast(dtype).alias("converted")
            )
            lost = check.filter(ma.col("value") != ma.col("converted")).to_dicts()
            if lost:
                raise ValueError(f"conversion loses precision: {lost}")
        except Exception as error:
            raise ValueError(f"{name}: {error}") from error
        expressions.append(value.cast(dtype).alias(target))
    return relation.select(*identity, *expressions).to_polars()


def source_binding(dataset, record, source):
    binding = next(
        b
        for b in dataset.bindings
        if b.typed_field_name == source and record.source_row_ref in b.row_refs
    )
    published = next(
        f for f in dataset.published_fields if f.id == binding.published_field_ref
    )
    return binding, published


def source_ids(bundle, dataset, record=None):
    prefix = f"{bundle.bundle_key}/{dataset.id}"
    return (
        f"{prefix}/{record.record_id}" if record else f"{prefix}/{dataset.context.id}"
    )


def value_state(cell, meaning):
    return (
        "source_missing"
        if cell.value is None
        else "not_conformed"
        if meaning.unit_factor is None
        else "present"
    )


def interpretation(revision, oid, target, cell, meaning, catalogue):
    def ref(value):
        return value.revision_id if isinstance(value, RevisionRef) else None

    currency = meaning.attribute("currency")
    return SilverFieldInterpretation(
        revision,
        oid,
        target,
        catalogue.id,
        ref(meaning.concept_ref),
        ref(meaning.measure_ref),
        ref(meaning.attribute("result_unit").value),
        value_state(cell, meaning),
        currency.value,
        currency.status,
        meaning.attributes,
    )


def lineage(revision, oid, target, bundle, ref, dataset, record, source, meaning):
    cell = getattr(record, source)
    binding, published = source_binding(dataset, record, source)
    factor = meaning.unit_factor
    reason = (
        "source unit/scale conversion unresolved or conflicting"
        if value_state(cell, meaning) == "not_conformed"
        else None
    )
    return SourceLineage(
        revision,
        oid,
        target,
        bundle.bundle_key,
        ref.output_version,
        bundle.document.document_id,
        dataset.id,
        record.record_id,
        source,
        binding.id,
        published.id,
        str(cell.value) if cell.value is not None else None,
        cell.original_text,
        cell.displayed_precision,
        cell.missing_reason,
        published.source_unit,
        str(published.source_scale) if published.source_scale is not None else None,
        str(factor) if factor is not None else None,
        "selected_value",
        reason,
        "source missing"
        if cell.value is None
        else reason or f"multiply source value by {factor}",
        tuple(
            dict.fromkeys(
                (
                    *dataset.context.qualification_refs,
                    *binding.qualification_refs,
                    *published.qualification_refs,
                )
            )
        ),
        cell.source_reference,
    )


def metadata_rows(bundles, bronze_refs, revision):
    """Lossless source-context, band and relationship projections (no mappings)."""
    result = {name: [] for name in ("contexts", "segments", "relationships")}
    for bundle, ref in zip(bundles, bronze_refs, strict=True):
        for ds in bundle.datasets:
            ctx = ds.context
            cid = source_ids(bundle, ds)
            context = {
                f.name: getattr(ctx, f.name) for f in fields(ctx) if f.name != "id"
            }
            result["contexts"].append(
                SilverContext(
                    revision,
                    cid,
                    bundle.bundle_key,
                    ref.output_version,
                    bundle.document.document_id,
                    ds.id,
                    ctx.id,
                    bundle.document.organisation_id,
                    **context,
                )
            )
            for segmentation in ds.segmentations:
                for band in segmentation.bands:
                    factor = Decimal("0.01") if band.unit == "%" else None
                    result["segments"].append(
                        SilverSegment(
                            revision,
                            f"{cid}/{band.id}",
                            cid,
                            segmentation.id,
                            band.id,
                            band.source_label,
                            band.kind,
                            band.category,
                            band.lower if factor is not None else None,
                            band.upper if factor is not None else None,
                            band.lower_inclusive,
                            band.upper_inclusive,
                            band.lower_status,
                            band.upper_status,
                            band.source_reference,
                        )
                    )
            row_ids = {r.source_row_ref: source_ids(bundle, ds, r) for r in ds.records}
            for relationship in ds.relationships:
                # This domain projects source row-to-row totals/subsets. Never
                # silently discard an unsupported endpoint or invent an edge.
                if relationship.parent.kind != "row" or any(
                    c.kind != "row" for c in relationship.children
                ):
                    raise ValueError(
                        f"relationships/{relationship.id}: unsupported CR6 endpoint kind"
                    )
                for child in relationship.children:
                    if relationship.parent.id not in row_ids or child.id not in row_ids:
                        raise ValueError(
                            f"relationships/{relationship.id}: endpoint absent from selected observations"
                        )
                    result["relationships"].append(
                        SilverObservationRelationship(
                            revision,
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
    return result


def check_inputs(bundles, bronze_refs):
    if len(bundles) != len(bronze_refs):
        raise ValueError("bronze_refs: selection length differs from bundles")
    keys = [b.bundle_key for b in bundles]
    if len(set(keys)) != len(keys):
        raise ValueError("bronze_refs: duplicate bundle selection")
    for bundle, ref in zip(bundles, bronze_refs, strict=True):
        if bundle.bundle_key != ref.bundle_key:
            raise ValueError(f"bronze_refs: bundle association mismatch: {ref}")


def conform_cr6(
    bundles: tuple[ExtractionBundle, ...],
    bronze_refs: tuple[BronzeRef, ...],
    catalogue: CatalogueRelease,
    revision_id: str,
    *,
    evidence_bundles: tuple[ExtractionBundle, ...] = (),
) -> SilverCandidate:
    check_inputs(bundles, bronze_refs)
    metadata = metadata_rows(bundles, bronze_refs, revision_id)
    observation_frames, field_rows = [], []
    for bundle, ref in zip(bundles, bronze_refs, strict=True):
        for ds in bundle.datasets:
            cid = source_ids(bundle, ds)
            source_rows, mapping_rows = [], []
            for record in ds.records:
                oid = source_ids(bundle, ds, record)
                meanings = {
                    source: resolve_field(catalogue, ds, record, source)
                    for source in FIELD_MAP
                }
                roles = {m.attribute("row_role") for m in meanings.values()}
                role_values = {(r.value, r.status) for r in roles}
                role, status = (
                    next(iter(role_values))
                    if len(role_values) == 1
                    else (None, "conflicting")
                )
                if len(record.source_segment_memberships) > 1:
                    raise ValueError(f"{oid}: CR6 requires at most one PD segment")
                identity = {
                    "silver_revision_id": revision_id,
                    "observation_id": oid,
                    "context_id": cid,
                    "segment_id": f"{cid}/{record.source_segment_memberships[0]}"
                    if record.source_segment_memberships
                    else None,
                    "source_record_id": record.record_id,
                    "source_row_ref": record.source_row_ref,
                    "source_row_role": record.source_row_role,
                    "canonical_row_role": role,
                    "row_role_status": status,
                }
                source_rows.append(identity | {
                    source: getattr(record, source).value for source in FIELD_MAP
                })
                mapping_rows.append({"observation_id": oid} | {
                    f"{source}__factor": meanings[source].unit_factor
                    for source in FIELD_MAP
                })
                for source, target in FIELD_MAP.items():
                    meaning = meanings[source]
                    field_rows.append(
                        tabular(interpretation(
                            revision_id,
                            oid,
                            target,
                            getattr(record, source),
                            meaning,
                            catalogue,
                        )) | tabular(lineage(
                            revision_id,
                            oid,
                            target,
                            bundle,
                            ref,
                            ds,
                            record,
                            source,
                            meaning,
                        )) | {"mapping_revision_refs": [m.revision_id for m in meaning.mapping_refs]}
                    )
            identity_schema = {
                k: v for k, v in PROJECTION_SCHEMAS["observations"].items()
                if k not in FIELD_MAP.values()
            }
            source_schema = identity_schema | {
                name: decimal_type([r[name] for r in source_rows], name)
                for name in FIELD_MAP
            }
            factor_schema = {"observation_id": pl.String} | {
                f"{name}__factor": decimal_type(
                    [r[f"{name}__factor"] for r in mapping_rows], name
                ) for name in FIELD_MAP
            }
            # Counts start as exact Decimal too, so the checked final Int64 cast
            # diagnoses out-of-range/fractional inputs without truncating them.
            for row in source_rows:
                for name in FIELD_MAP:
                    if row[name] is not None:
                        row[name] = Decimal(row[name])
            source_frame = pl.DataFrame(source_rows, schema=source_schema)
            converted = convert_dataset(
                source_frame, pl.DataFrame(mapping_rows, schema=factor_schema),
                ["observation_id"], FIELD_MAP,
            )
            observation_frames.append(
                ma.relation(source_frame).select(*identity_schema)
                .join(converted, on="observation_id").to_polars()
            )
    observations = pl.concat(observation_frames) if observation_frames else frame("observations", [])
    contexts = frame("contexts", metadata["contexts"])
    # Bounds use the same relation conversion path, not Python Decimal math.
    segment_rows = [tabular(r) for r in metadata["segments"]]
    segment_schema = PROJECTION_SCHEMAS["segments"] | {
        k: decimal_type([r[k] for r in segment_rows], k)
        for k in ("lower_fraction", "upper_fraction")
    }
    segments = pl.DataFrame(segment_rows, schema=segment_schema)
    bounds = ("lower_fraction", "upper_fraction")
    bound_factors = pl.DataFrame([
        {"segment_id": r["segment_id"], **{f"{k}__factor": Decimal("0.01") for k in bounds}}
        for r in segment_rows
    ], schema={"segment_id": pl.String} | {f"{k}__factor": pl.Decimal(38, 2) for k in bounds})
    converted_bounds = convert_dataset(segments, bound_factors, ["segment_id"], dict(zip(bounds, bounds)))
    segments = ma.relation(segments).drop(*bounds).join(converted_bounds, on="segment_id")
    observations = (
        ma.relation(observations).join(contexts, on=["silver_revision_id", "context_id"])
        .join(segments.drop("context_id"), on=["silver_revision_id", "segment_id"], how="left")
        .select(*SCHEMAS["cr6_observations"]).to_polars()
    )
    candidate = SilverCandidate(
        revision_id, {
            "cr6_observations": observations,
            "cr6_fields": frame("cr6_fields", field_rows),
            "cr6_relationships": frame("cr6_relationships", metadata["relationships"]),
        }
    )
    from .validate import validate_candidate

    validate_candidate(
        candidate, bundles, bronze_refs, catalogue, evidence_bundles=evidence_bundles
    )
    return candidate
