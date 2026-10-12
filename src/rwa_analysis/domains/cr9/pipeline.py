"""Dataset-sized CR9 numeric conversion with field-level temporal metadata."""

from decimal import Decimal

import mountainash as ma
import polars as pl

from rwa_analysis.extraction.cr9 import Cr9Dataset

from . import metadata
from .contracts import DECLARATIONS, TABLES, relation
from .models import COUNTS, MEASURES, ConversionFactors, Cr9Output, SilverObservation
from .semantics import resolve_field


class Cr9Pipeline:
    def conform(self, inputs, catalogue) -> Cr9Output:
        tables = {table.member: [] for table in TABLES}
        factors = []
        for loaded in inputs:
            bundle = loaded.bundle
            for ds in bundle.datasets:
                if not isinstance(ds, Cr9Dataset):
                    continue
                metadata.context_rows(tables, loaded, ds)
                metadata.relationship_rows(tables, bundle, ds)
                bands = {
                    b.id: (seg.id, b)
                    for seg in ds.metadata.segmentations
                    for b in seg.bands
                }
                for row in ds.backtesting_rows:
                    oid, cid = metadata.ids(bundle, ds, row), metadata.ids(bundle, ds)
                    meanings = {
                        name: resolve_field(catalogue, ds, row, name)
                        for name in MEASURES
                    }
                    role_values = {
                        (m.attribute("row_role").value, m.attribute("row_role").status)
                        for m in meanings.values()
                    }
                    role, role_status = (
                        next(iter(role_values))
                        if len(role_values) == 1
                        else (None, "conflicting")
                    )
                    seg_id, band = (
                        bands[row.source_segment_memberships[0]]
                        if row.source_segment_memberships
                        else (None, None)
                    )
                    source_ref = (
                        band.source_reference
                        if band
                        else getattr(row, MEASURES[0]).source_reference
                    )
                    tables["observations"].append(
                        SilverObservation(
                            **metadata.location(source_ref),
                            silver_revision_id="",
                            observation_id=oid,
                            context_id=cid,
                            segment_id=f"{cid}/{band.id}" if band else None,
                            source_record_id=row.record_id,
                            source_row_ref=row.source_row_ref,
                            source_row_role=row.source_row_role,
                            canonical_row_role=role,
                            row_role_status=role_status,
                            source_segmentation_id=seg_id,
                            source_band_ref=band.id if band else None,
                            source_label=band.source_label if band else None,
                            category_kind=band.kind if band else None,
                            category=band.category if band else None,
                            lower_fraction=band.lower if band else None,
                            upper_fraction=band.upper if band else None,
                            lower_inclusive=band.lower_inclusive if band else None,
                            upper_inclusive=band.upper_inclusive if band else None,
                            lower_status=band.lower_status if band else None,
                            upper_status=band.upper_status if band else None,
                            **{name: getattr(row, name).value for name in MEASURES},
                        )
                    )
                    factors.append(
                        ConversionFactors(
                            oid,
                            **{name: meanings[name].unit_factor for name in MEASURES},
                        )
                    )
                    for name in MEASURES:
                        metadata.field_rows(
                            tables, loaded, ds, row, name, meanings[name], catalogue
                        )
        output = {
            name: relation(name, rows)
            for name, rows in tables.items()
            if name != "observations"
        }
        if factors:
            values = ma.relation(tables["observations"])
            multipliers = ma.relation(factors).select(
                "observation_id", *(ma.col(n).alias(f"{n}__factor") for n in MEASURES)
            )
            expressions = []
            for name in MEASURES:
                scales = [
                    max(0, -Decimal(v).as_tuple().exponent)
                    for rows in (tables["observations"], factors)
                    for r in rows
                    if (v := getattr(r, name)) is not None
                ]
                working = pl.Decimal(38, max(scales, default=0) * 2)
                dtype = pl.Int64 if name in COUNTS else pl.Decimal(16, 8)
                expressions.append(
                    (
                        ma.col(name).cast(working)
                        * ma.col(f"{name}__factor").cast(working)
                    )
                    .cast(dtype)
                    .alias(name)
                )
            output["observations"] = (
                values.join(multipliers, on="observation_id")
                .with_columns(
                    *expressions,
                    *(
                        (
                            ma.col(n).cast(pl.Decimal(38, 8))
                            * ma.lit(Decimal("0.01")).cast(pl.Decimal(38, 8))
                        ).alias(n)
                        for n in ("lower_fraction", "upper_fraction")
                    ),
                )
                .select(*(f.name for f in DECLARATIONS["observations"].spec.fields))
                .conform(DECLARATIONS["observations"].spec)
            )
        else:
            output["observations"] = relation("observations")
        return Cr9Output(**output)
