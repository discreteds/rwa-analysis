"""Source-bound CR6 conformance using dataset-wide Mountainash expressions."""

from decimal import Decimal

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.models import CatalogueRelease, RevisionRef
from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.extraction.cr6 import Cr6Dataset
from rwa_analysis.storage.bronze import LoadedBronze

from . import metadata
from .contracts import IDENTITY_SPEC, MEASURES
from .models import FIELD_MAP, Cr6Output, RowIdentity, SourceNumbers


def source_ids(bundle, dataset, record=None):
    prefix = f"{bundle.bundle_key}/{dataset.id}"
    return f"{prefix}/{record.record_id if record else dataset.metadata.context.id}"


def source_scale(rows, name):
    """Decimal scale needed by arithmetic operands, without changing inputs."""
    return max(
        (
            max(0, -value.as_tuple().exponent)
            for row in rows
            if (value := getattr(row, name)) is not None
        ),
        default=0,
    )


def convert_dataset(source, factors, columns):
    values = ma.relation(source)
    multipliers = ma.relation(factors).select(
        "observation_id", *(ma.col(name).alias(f"{name}__factor") for name in columns)
    )
    expressions = []
    for name, target in columns.items():
        working = pl.Decimal(
            38, source_scale(source, name) + source_scale(factors, name)
        )
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


def field_input(bundle, ref, ds, row, name, meaning, catalogue):
    """Bind a source cell and its resolved meaning; expressions project the metadata."""
    binding = next(
        b
        for b in ds.metadata.bindings
        if b.typed_field_name == name and row.source_row_ref in b.row_refs
    )
    published = next(
        f for f in ds.metadata.published_fields if f.id == binding.published_field_ref
    )
    cell = getattr(row, name)
    currency = meaning.attribute("currency")

    def revision(value):
        return value.revision_id if isinstance(value, RevisionRef) else None

    return {
        "observation_id": source_ids(bundle, ds, row),
        "field_key": FIELD_MAP[name],
        "catalogue_release_id": catalogue.id,
        "concept_revision_ref": revision(meaning.concept_ref),
        "measure_revision_ref": revision(meaning.measure_ref),
        "result_unit_revision_ref": revision(meaning.attribute("result_unit").value),
        "currency_code": currency.value,
        "currency_status": currency.status,
        "bundle_key": bundle.bundle_key,
        "output_version": ref.output_version,
        "document_id": bundle.document.document_id,
        "dataset_id": ds.id,
        "source_record_id": row.record_id,
        "source_field_key": name,
        "unit_factor": str(meaning.unit_factor)
        if meaning.unit_factor is not None
        else None,
        "cell": {
            **metadata.record(cell),
            "value": str(cell.value) if cell.value is not None else None,
        },
        "binding": metadata.record(binding),
        "published": {
            **metadata.record(published),
            "source_scale": str(published.source_scale)
            if published.source_scale is not None
            else None,
        },
        "qualifications": [
            {"qualification_ref": q}
            for q in dict.fromkeys(
                (
                    *ds.metadata.context.qualification_refs,
                    *binding.qualification_refs,
                    *published.qualification_refs,
                )
            )
        ],
        "mappings": [metadata.record(m) for m in meaning.mapping_refs],
    }


class Cr6Pipeline:
    def conform(
        self, inputs: tuple[LoadedBronze, ...], catalogue: CatalogueRelease
    ) -> Cr6Output:
        contexts, segments, relationships, field_rows, attributes = (
            [] for _ in range(5)
        )
        identities, source_rows, factor_rows = ([] for _ in range(3))
        for loaded in inputs:
            bundle, ref = loaded.bundle, loaded.ref
            for ds in bundle.datasets:
                if not isinstance(ds, Cr6Dataset):
                    continue
                cid = source_ids(bundle, ds)
                contexts.append(
                    {
                        "context_id": cid,
                        "bundle_key": bundle.bundle_key,
                        "output_version": ref.output_version,
                        "document_id": bundle.document.document_id,
                        "dataset_id": ds.id,
                        "organisation_id": bundle.document.organisation_id,
                        "context": metadata.record(ds.metadata.context),
                    }
                )
                for segmentation in ds.metadata.segmentations:
                    for band in segmentation.bands:
                        segments.append(
                            {
                                "context_id": cid,
                                "segment_id": f"{cid}/{band.id}",
                                "source_segmentation_id": segmentation.id,
                                "band": metadata.record(band),
                            }
                        )
                row_ids = {
                    r.source_row_ref: source_ids(bundle, ds, r)
                    for r in ds.exposure_rows
                }
                for relationship in ds.metadata.relationships:
                    for child in relationship.children:
                        relationships.append(
                            {
                                **metadata.record(relationship),
                                "context_id": cid,
                                "relationship_id": f"{cid}/{relationship.id}/{child.id}",
                                "parent_observation_id": row_ids[
                                    relationship.parent.id
                                ],
                                "child_observation_id": row_ids[child.id],
                            }
                        )
                for row in ds.exposure_rows:
                    oid = source_ids(bundle, ds, row)
                    meanings = {
                        name: resolve_field(catalogue, ds, row, name)
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
                            f"{cid}/{row.source_segment_memberships[0]}"
                            if row.source_segment_memberships
                            else None,
                            row.record_id,
                            row.source_row_ref,
                            row.source_row_role,
                            role,
                            status,
                        )
                    )
                    source_rows.append(
                        SourceNumbers(
                            oid,
                            **{
                                name: Decimal(value)
                                if (value := getattr(row, name).value) is not None
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
                    for name, target in FIELD_MAP.items():
                        field_rows.append(
                            field_input(
                                bundle, ref, ds, row, name, meanings[name], catalogue
                            )
                        )
                        attributes.extend(
                            metadata.assertion_inputs(oid, target, meanings[name])
                        )

        relations = {
            **metadata.context_tables(contexts),
            **metadata.field_tables(field_rows),
            **metadata.attribute_tables(attributes),
            **metadata.relationship_tables(relationships),
        }
        if source_rows:
            values = convert_dataset(source_rows, factor_rows, FIELD_MAP)
            bounds = (
                metadata.source(segments)
                .unnest("band", separator="")
                .rename({"source_reference": "source"})
                .unnest("source", separator="_")
                .rename({"id": "source_band_ref", "kind": "category_kind"})
            )
            bounds = bounds.with_columns(
                *(
                    ma.when(ma.col("unit") == "%")
                    .then(
                        (
                            ma.col(name).cast(pl.Decimal(38, 8))
                            * ma.lit(Decimal("0.01"))
                        ).cast(pl.Decimal(16, 8))
                    )
                    .otherwise(ma.lit(None).cast(pl.Decimal(16, 8)))
                    .alias(f"{name}_fraction")
                    for name in ("lower", "upper")
                )
            ).select(
                "segment_id",
                "source_segmentation_id",
                "source_band_ref",
                "source_label",
                "category_kind",
                "category",
                "lower_fraction",
                "upper_fraction",
                "lower_inclusive",
                "upper_inclusive",
                "lower_status",
                "upper_status",
                *(
                    f"source_{name}"
                    for name in (
                        "document_id",
                        "pdf_page",
                        "printed_page",
                        "location",
                        "row",
                        "column",
                    )
                ),
            )
            observations = (
                ma.relation(identities)
                .conform(IDENTITY_SPEC)
                .join(values, on="observation_id")
                .join(bounds, on="segment_id", how="left")
            )
            relations["observations"] = metadata.finish("observations", observations)
        else:
            relations["observations"] = metadata.finish("observations")
        return Cr6Output(**relations)
