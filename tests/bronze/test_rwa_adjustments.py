"""Independent PDF expectations for the selected 2025 adjustment evidence.

Protects amount/scale, risk scope and timing: notably capital versus RWA,
post-report removal versus reporting-date stock, and reported versus derived.
The older domain goldens cannot cover these newly selected source occurrences.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from rwa_analysis.extraction.runner import run_extractor

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "bank,day",
    [
        ("cba", "2025-06-30"),
        ("anz", "2025-09-30"),
        ("nab", "2025-09-30"),
        ("westpac", "2025-09-30"),
    ],
)
def test_source_adjustment_amounts_and_classification(bank, day):
    expected = json.loads(
        (
            ROOT / f"tests/bronze/au/{bank}/{day}/aps330/golden-adjustments.json"
        ).read_text()
    )
    bundle = run_extractor(
        ROOT / f"extractions/au/{bank}/{day}/aps330/extract.py",
        ROOT / f"raw/{bank}-{day}-aps330.pdf",
    )
    selected = [t for t in bundle.datasets if t.id == "rwa-adjustments"]
    assert len(selected) == 1, (
        "Adjustment observations must be captured, not prose only"
    )
    table = selected[0]
    cells = {c.id: c for c in table.cells}
    assert cells.keys() == expected.keys()
    fields = {f.id: f for f in table.metadata.published_fields}
    contexts = {c.revision_id: c for c in bundle.snapshot.contexts}
    bindings = {
        b.ref.local_id: b
        for b in bundle.snapshot.occurrences
        if b.ref.scope == table.id and b.ref.kind == "cell"
    }
    for key, (token, scale, page, classification, point) in expected.items():
        cell = cells[key]
        assert cell.value.original_text == token
        assert cell.value.value == (
            None if token == "-" else Decimal(token.replace(",", ""))
        )
        assert cell.value.missing_reason == (
            "dash_unresolved" if token == "-" else None
        )
        assert cell.value.source_reference.pdf_page == page
        assert fields[cell.field_ref].source_scale == Decimal(scale)
        context = contexts[bindings[key].context_refs[0]]
        attributes = {a.name: a.value for a in context.attributes}
        assert attributes["qualification_meaning"] == classification
        assert next(t.point for t in context.temporal if t.id == "measurement") == point
        assert cell.value.displayed_precision == (
            None
            if token == "-"
            else max(0, -Decimal(token.replace(",", "")).as_tuple().exponent)
        )
        if "capital" in classification:
            assert any(
                r.revision_id == "capital.requirement@v1"
                for r in bindings[key].definition_refs
            )
    if bank == "nab":
        assert (
            "mortgage-overlay" not in cells
        )  # $50m is a derived bridge, not a PDF amount.
    if bank == "westpac":
        assert (
            "mortgage-overlay" not in cells
        )  # Not finding an amount is not reported zero.
