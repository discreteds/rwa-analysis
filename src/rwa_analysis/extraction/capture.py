"""Invoke explicit physical readers and bind fragments to reviewed source structure."""

from dataclasses import replace

import pdfplumber

from .definitions import CapturedBundle
from .models import ReportedValue
from .source_tables import ReportedText, SourceCell
from .values import parse_decimal_token


def capture(pdf_path, definition, selected_definitions, operations):
    snapshot = replace(definition.snapshot, contexts=tuple(selected_definitions))
    with pdfplumber.open(pdf_path) as document:
        fragments = tuple(
            fragment
            for binding in snapshot.physical
            for fragment in operations[binding.operation](document, binding)
        )
    slots = {(f.binding_ref, f.slot): f for f in fragments}
    bindings = snapshot.occurrences
    comments = {
        (b.ref.scope, b.ref.local_id): b
        for b in bindings
        if b.ref.kind == "comment" and b.physical_refs
    }
    tables = []
    for table in definition.tables:
        cells = []
        local = [b for b in bindings if b.ref.scope == table.id]
        for binding in local:
            if binding.cell is None:
                continue
            spec = binding.cell
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            token = fragment.text
            if spec.value_kind == "text":
                value = ReportedText(
                    token or None, token, spec.missing_reason, fragment.evidence
                )
            else:
                number = parse_decimal_token(token.rstrip("%"))
                if spec.value_kind == "integer" and number is not None:
                    number = int(number)
                precision = (
                    (
                        max(0, -number.as_tuple().exponent)
                        if spec.value_kind == "decimal"
                        else 0
                    )
                    if number is not None
                    else None
                )
                value = ReportedValue(
                    number,
                    token,
                    precision,
                    spec.missing_reason if number is None else None,
                    fragment.evidence,
                )
            cells.append(
                SourceCell(
                    binding.ref.local_id,
                    spec.field_ref,
                    spec.row_ref,
                    spec.column_ref,
                    (table.metadata.context.id,),
                    spec.segment_refs,
                    spec.qualification_refs,
                    spec.value_kind,
                    value,
                )
            )

        def qualification(q, table=table):
            binding = comments.get((table.id, q.id)) or comments[(None, q.id)]
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            return replace(q, source_text=fragment.text, evidence=(fragment.evidence,))

        def axis(a, local=local):
            binding = next(
                (
                    b
                    for b in local
                    if b.ref.kind == a.axis
                    and b.ref.local_id == a.id
                    and b.physical_refs
                ),
                None,
            )
            if binding is None:
                return a
            fragment = slots[
                (binding.physical_refs[0].binding_ref, binding.physical_refs[0].slot)
            ]
            return replace(
                a, source_label=fragment.text, source_reference=fragment.evidence
            )

        tables.append(
            replace(
                table,
                cells=tuple(cells),
                metadata=replace(
                    table.metadata,
                    qualifications=tuple(
                        qualification(q) for q in table.metadata.qualifications
                    ),
                    axes=tuple(axis(a) for a in table.metadata.axes),
                ),
            )
        )
    return CapturedBundle(
        definition.document,
        definition.bundle_key,
        definition.extractor_path,
        tuple(tables),
        snapshot,
        fragments,
    )
