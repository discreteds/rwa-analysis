"""Conform twelve source-bound measures together through Mountainash relations."""

from dataclasses import fields
from decimal import (
    ROUND_DOWN,
    Decimal,
    DecimalException,
    Inexact,
    Rounded,
    localcontext,
)

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.models import CatalogueRelease, FieldMeaning, RevisionRef
from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.extraction.cr6 import ExtractionBundle
from rwa_analysis.storage.bronze import BronzeRef

from .models import (
    DECIMAL,
    FIELD_MAP,
    SCHEMAS,
    AppliedMapping,
    SilverCandidate,
    SilverContext,
    SilverCreditRiskExposureObservation,
    SilverFieldInterpretation,
    SilverObservationRelationship,
    SilverSegment,
    SourceLineage,
    frame,
)


def exact_conversion(value, factor, path, *, count=False):
    """Preflight *before* Arrow/casts; never use the ambient Decimal precision.

    Multiplication needs at most the sum of coefficient lengths. Quantization
    additionally needs room for the integer part and the eight fractional places.
    No normalize(), abs() or arithmetic outside this local context may round.
    """
    if value is None or factor is None:
        return None
    source = Decimal(value)
    if not source.is_finite() or not factor.is_finite():
        raise ValueError(f"{path}: nonfinite conversion")
    with localcontext() as ctx:
        ctx.prec = max(
            80, len(source.as_tuple().digits) + len(factor.as_tuple().digits) + 10
        )
        ctx.traps[Inexact] = True
        ctx.traps[Rounded] = False
        try:
            result = source * factor
        except DecimalException as error:
            raise ValueError(
                f"{path}: conversion exceeds exact Decimal representation"
            ) from error
        if count:
            if (
                result != result.to_integral_value()
                or not -(2**63) <= result <= 2**63 - 1
            ):
                raise ValueError(f"{path}: conversion is not representable as Int64")
            return int(result)
        if abs(result) >= Decimal("1e30"):
            raise ValueError(f"{path}: conversion exceeds Decimal(38,8) precision")
        try:
            rounded = result.quantize(Decimal("0.00000001"))
        except DecimalException as error:
            raise ValueError(
                f"{path}: conversion needs more than eight decimal places"
            ) from error
        return rounded


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
                            exact_conversion(
                                band.lower, factor, f"{cid}/{band.id}.lower"
                            ),
                            exact_conversion(
                                band.upper, factor, f"{cid}/{band.id}.upper"
                            ),
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


def _convert_row(identity, record, meanings):
    """One wide relation projection, with preflight and exact backend checks."""
    source_values, source_schema, expressions, expected = dict(identity), {}, [], {}
    for source, target in FIELD_MAP.items():
        cell, meaning = getattr(record, source), meanings[source]
        count = target == "reported_entity_count"
        dtype = pl.Int64 if count else DECIMAL
        converted = exact_conversion(
            cell.value,
            meaning.unit_factor,
            f"{identity['observation_id']}.{source}",
            count=count,
        )
        expected[target] = converted
        if converted is None:
            expressions.append(ma.lit(None).cast(dtype).alias(target))
            continue
        # Preserve the source coefficient until relation multiplication. A source
        # can require more than eight places even when its base amount does not.
        scale = max(8, -Decimal(cell.value).as_tuple().exponent)
        integer_digits = max(0, Decimal(cell.value).adjusted() + 1)
        if not count and (scale > 8 or integer_digits + scale > 38):
            # Polars multiplication retains the common operand scale. A valid
            # base amount can overflow that intermediate (e.g. 30 integer + 9
            # fractional places). Split only the representation, not the unit
            # conversion: both source parts are multiplied inside the relation.
            with localcontext() as ctx:
                ctx.prec = max(80, len(cell.value.as_tuple().digits) + 10)
                whole = cell.value.to_integral_value(rounding=ROUND_DOWN)
                fraction = cell.value - whole
            fraction_name = f"{source}_fraction"
            source_values[source], source_values[fraction_name] = whole, fraction
            source_schema[source] = pl.Decimal(38, 0)
            source_schema[fraction_name] = pl.Decimal(38, scale)
            expr = (ma.col(source) * ma.lit(meaning.unit_factor)).cast(dtype) + (
                ma.col(fraction_name) * ma.lit(meaning.unit_factor)
            ).cast(dtype)
        else:
            source_values[source] = cell.value
            source_schema[source] = pl.Int64 if count else pl.Decimal(38, scale)
            expr = (ma.col(source) * ma.lit(meaning.unit_factor)).cast(dtype)
        expressions.append(expr.alias(target))
    source_frame = pl.DataFrame(
        [source_values],
        schema={name: SCHEMAS["observations"][name] for name in identity}
        | source_schema,
    )
    converted = (
        ma.relation(source_frame)
        .select(*[ma.col(name) for name in identity], *expressions)
        .collect()
    )
    actual = converted.row(0, named=True)
    for target, value in expected.items():
        if actual[target] != value:
            raise ValueError(
                f"{identity['observation_id']}.{target}: backend conversion lost precision"
            )
    return SilverCreditRiskExposureObservation(**actual)


def conform_cr6(
    bundles: tuple[ExtractionBundle, ...],
    bronze_refs: tuple[BronzeRef, ...],
    catalogue: CatalogueRelease,
    revision_id: str,
) -> SilverCandidate:
    check_inputs(bundles, bronze_refs)
    rows = {name: [] for name in SCHEMAS} | metadata_rows(
        bundles, bronze_refs, revision_id
    )
    for bundle, ref in zip(bundles, bronze_refs, strict=True):
        for ds in bundle.datasets:
            cid = source_ids(bundle, ds)
            for record in ds.records:
                oid = source_ids(bundle, ds, record)
                meanings: dict[str, FieldMeaning] = {
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
                rows["observations"].append(_convert_row(identity, record, meanings))
                for source, target in FIELD_MAP.items():
                    meaning = meanings[source]
                    rows["interpretations"].append(
                        interpretation(
                            revision_id,
                            oid,
                            target,
                            getattr(record, source),
                            meaning,
                            catalogue,
                        )
                    )
                    rows["lineage"].append(
                        lineage(
                            revision_id,
                            oid,
                            target,
                            bundle,
                            ref,
                            ds,
                            record,
                            source,
                            meaning,
                        )
                    )
                    rows["applied_mappings"].extend(
                        AppliedMapping(
                            revision_id, oid, target, catalogue.id, m.revision_id
                        )
                        for m in meaning.mapping_refs
                    )
    candidate = SilverCandidate(
        revision_id, {name: frame(name, data) for name, data in rows.items()}
    )
    from .validate import validate_candidate

    validate_candidate(candidate, bundles, bronze_refs, catalogue)
    return candidate
