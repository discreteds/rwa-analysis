"""DISPOSABLE: apply supplied physical bindings, retain declarations and payloads."""

from dataclasses import asdict

import pdfplumber

from rwa_analysis.extraction.values import parse_decimal_token


def capture(pdf_path, definition, operations):
    fragments = {}
    with pdfplumber.open(pdf_path) as document:
        for binding in definition.physical:
            fragments[binding.id] = operations[binding.operation](
                document.pages[binding.page - 1], binding.parameters)
    physical = {binding.id: binding for binding in definition.physical}
    occurrences = []
    for position, occurrence in enumerate(definition.occurrences):
        text = fragments[occurrence.physical][occurrence.slot]
        number = parse_decimal_token(text) if occurrence.value_kind == "decimal" else None
        binding = physical[occurrence.physical]
        occurrences.append({
            "id": occurrence.id, "kind": occurrence.kind, "position": position,
            "original_text": text, "source_number": str(number) if number is not None else None,
            "value_kind": occurrence.value_kind, "unit": occurrence.unit,
            "precision": max(0, -number.as_tuple().exponent) if number is not None else None,
            "missing_reason": "source_blank" if not text else None,
            "physical_binding": binding.id, "slot": occurrence.slot,
            "pdf_page": binding.page, "printed_page": binding.printed_page,
        })
    return {"status": "DISPOSABLE SPIKE — NOT PRODUCTION BRONZE",
            "definition_snapshot": asdict(definition), "occurrences": occurrences}
