"""Saved transport owns typed payload and evidence retention, not PDF correctness."""

from dataclasses import replace
from decimal import Decimal

from rwa_analysis.extraction.models import ReportedValue
from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.storage.bronze import BronzeStore


def capture(project_root):
    return run_extractor(
        project_root / "extractions/au/cba/2024-06-30/aps330/extract.py",
        project_root / "raw/cba-2024-06-30-aps330.pdf",
    )


def test_saved_source_tables_preserve_all_metadata(project_root, tmp_path):
    bundle = capture(project_root)
    store = BronzeStore(tmp_path)
    ref = store.save(bundle, "transport-proof")
    restored = store.load(ref).bundle
    assert restored == bundle
    assert restored.schema_version == "disclosure-v3"


def test_explicit_payload_kinds_preserve_integer_text_and_missingness(
    project_root, tmp_path
):
    from rwa_analysis.extraction.source_tables import ReportedText

    bundle = capture(project_root)
    table = bundle.datasets[0]
    original = table.cells[0]
    evidence = original.value.source_reference
    fields, cells = [], []
    cases = (
        ("integer", 9007199254740993, "9,007,199,254,740,993", 0, None),
        ("decimal", Decimal("0.00000001"), "0.00000001", 8, None),
        ("text", "N/A", "N/A", None, "not_applicable"),
        ("decimal", None, "-", None, "dash_unresolved"),
        ("decimal", None, "", None, "blank_unresolved"),
        ("decimal", Decimal(0), "0", 0, None),
    )
    for i, (kind, value, token, precision, missing) in enumerate(cases):
        key = f"synthetic-{i}"
        fields.append(
            replace(table.metadata.published_fields[0], id=key, value_kind=kind)
        )
        payload = (
            ReportedText(value, token, missing, evidence)
            if kind == "text"
            else ReportedValue(value, token, precision, missing, evidence)
        )
        cells.append(
            replace(original, id=key, field_ref=key, value_kind=kind, value=payload)
        )
    synthetic = replace(
        table,
        id="synthetic-transport",
        cells=tuple(cells),
        metadata=replace(table.metadata, published_fields=tuple(fields)),
    )
    store = BronzeStore(tmp_path)
    saved = store.save(replace(bundle, datasets=(synthetic,)), "synthetic")
    restored = store.load(saved).bundle.datasets[0]
    assert restored == synthetic
    assert type(restored.cells[0].value.value) is int
    assert restored.cells[0].value.value == 9007199254740993
    assert restored.cells[1].value.value == Decimal("0.00000001")
    assert [c.value.original_text for c in restored.cells[2:]] == ["N/A", "-", "", "0"]
