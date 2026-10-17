"""Structural views of actual captured content for unchanged independent goldens.

No capture declarations or catalogue interpretation supply expected values here.
The old typed shape is used only as input to the existing complete comparators.
"""

from dataclasses import fields
from datetime import date

from rwa_analysis.extraction.cr6 import BronzeCreditRiskExposureRow, Cr6Dataset
from rwa_analysis.extraction.cr9 import Cr9BacktestingRow, Cr9Context, Cr9Dataset
from rwa_analysis.extraction.datasets import DatasetMetadata, ExtractionBundle
from rwa_analysis.extraction.models import DatasetContext, PublishedField, ValueBinding
from rwa_analysis.extraction.temporal import TemporalBinding


def assert_capture_bindings(bundle, cell_count):
    """Protect physical evidence, lexical positions and original domain addresses."""
    domain_ids = {b.ref.scope for b in bundle.snapshot.domain_bindings}
    domain_tables = tuple(t for t in bundle.datasets if t.id in domain_ids)
    assert sum(len(t.cells) for t in domain_tables) == cell_count
    slots = {(f.binding_ref, f.slot): f for f in bundle.fragments}
    bindings = {b.ref: b for b in bundle.snapshot.occurrences}
    for binding in bindings.values():
        for link in binding.links:
            assert link.target in bindings, (binding.ref, link.target)
    numeric = {
        (t.id, c.id) for t in domain_tables for c in t.cells if c.value_kind != "text"
    }
    assert {
        (b.ref.scope, b.ref.local_id) for b in bundle.snapshot.domain_bindings
    } == numeric
    assert len(bundle.snapshot.domain_bindings) == len(numeric)
    for b in bundle.snapshot.domain_bindings:
        assert b.ref.local_id == b.record_id + "/" + b.field_key
        assert b.ref.scope == b.domain + "-residential-mortgages"
        assert b.binding_ref == "binding-" + b.field_key
    for table in domain_tables:
        local = {
            b.ref.local_id: b
            for b in bindings.values()
            if b.ref.scope == table.id and b.ref.kind == "cell"
        }
        for cell in table.cells:
            binding = local[cell.id]
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            assert fragment.text == cell.value.original_text
            assert fragment.evidence == cell.value.source_reference
            if cell.value_kind == "text":
                axis = next(
                    a
                    for a in table.metadata.axes
                    if a.id == cell.row_ref + "-" + cell.field_ref
                )
                assert cell.value.original_text == axis.source_label
                assert cell.value.value == (axis.source_label or None)
        for field in table.metadata.published_fields:
            binding = next(
                b
                for b in bindings.values()
                if b.ref.scope == table.id
                and b.ref.kind == "field"
                and b.ref.local_id == field.id
            )
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            assert fragment.text == field.source_label
        for note in table.metadata.qualifications:
            binding = next(
                b
                for b in bindings.values()
                if b.ref.kind == "comment" and b.ref.local_id == note.id
            )
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            assert note.source_text == fragment.text
            assert note.evidence == (fragment.evidence,)
            assert binding.links


def golden_view(bundle):
    """Rearrange actual cells/metadata for the old comparators, without interpretation."""
    datasets = []
    domain_ids = {b.ref.scope for b in bundle.snapshot.domain_bindings}
    for table in bundle.datasets:
        if table.id not in domain_ids:
            continue
        cr9 = table.id.startswith("cr9")
        m = table.metadata
        numeric = tuple(f for f in m.published_fields if f.value_kind != "text")
        rows = tuple(a for a in m.axes if a.axis == "row")
        cells = {(c.row_ref, c.field_ref): c for c in table.cells}
        context_type = Cr9Context if cr9 else DatasetContext
        context_values = {
            f.name: getattr(m.context, f.name)
            for f in fields(context_type)
            if f.name != "observation_date"
        }
        if not cr9:
            context_values["observation_date"] = date.fromisoformat(
                next(d.point for d in m.temporal_descriptors if d.id == "measurement")
            )
        bindings = tuple(
            ValueBinding(
                "binding-" + f.id,
                f.id,
                f.id,
                tuple(r.id for r in rows),
                (cells[(rows[0].id, f.id)].column_ref,),
                ("context",),
                f.qualification_refs,
            )
            for f in numeric
        )
        records = tuple(
            (Cr9BacktestingRow if cr9 else BronzeCreditRiskExposureRow)(
                row.id,
                row.id,
                cells[(row.id, numeric[0].id)].source_row_role,
                cells[(row.id, numeric[0].id)].segment_refs,
                cells[(row.id, numeric[0].id)].source_aggregation_scope,
                **{f.id: cells[(row.id, f.id)].value for f in numeric},
            )
            for row in rows
        )
        metadata = DatasetMetadata(
            context_type(**context_values),
            m.axes,
            tuple(
                PublishedField(
                    **{p.name: getattr(f, p.name) for p in fields(PublishedField)}
                )
                for f in numeric
            ),
            bindings,
            m.segmentations,
            m.qualifications,
            m.relationships,
            m.temporal_descriptors if cr9 else (),
            tuple(
                TemporalBinding(
                    b.cell_id.split("/", 1)[0],
                    b.cell_id.split("/", 1)[1],
                    b.role,
                    b.descriptor_ref,
                )
                for b in m.temporal_bindings
            )
            if cr9
            else (),
        )
        datasets.append(
            (Cr9Dataset if cr9 else Cr6Dataset)(table.id, metadata, records)
        )
    return ExtractionBundle(
        bundle.document,
        bundle.bundle_key,
        bundle.extractor_path,
        "disclosure-v2",
        tuple(datasets),
    )
