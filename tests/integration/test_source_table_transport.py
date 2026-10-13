"""Saved transport owns typed payload and evidence retention, not PDF correctness."""

from dataclasses import replace
from decimal import Decimal

import pytest

from rwa_analysis.extraction.models import ReportedValue
from rwa_analysis.storage.bronze import BronzeStore


def test_saved_source_tables_preserve_all_metadata(cba_2024_bundle, tmp_path):
    bundle = cba_2024_bundle
    store = BronzeStore(tmp_path)
    ref = store.save(bundle, "transport-proof")
    restored = store.load(ref).bundle
    assert restored == bundle
    assert restored.schema_version == "disclosure-v3"


def test_retained_checkpoint_v3_cells_decode_without_later_legacy_row_metadata(
    cba_2024_bundle,
):
    from rwa_analysis.extraction.codec import decode_payload, encode_payload

    payload = encode_payload(cba_2024_bundle)
    # Checkpoint A retained v3 predates the explicit legacy row-property projection.
    for dataset in payload["datasets"]:
        for cell in dataset["cells"]:
            cell.pop("source_row_role")
            cell.pop("source_aggregation_scope")
    restored = decode_payload(payload)
    assert restored == cba_2024_bundle
    assert restored.datasets[0].cells[0].value.original_text == "175,918"


@pytest.mark.parametrize("version", ["disclosure-v3", "disclosure-v4"])
def test_explicit_payload_kinds_preserve_integer_text_and_missingness(
    cba_2024_bundle, tmp_path, version
):
    from rwa_analysis.extraction.source_tables import ReportedText

    bundle = cba_2024_bundle
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
    selected = replace(bundle, datasets=(synthetic,))
    if version == "disclosure-v4":
        from rwa_analysis.extraction.definitions import CapturedBundle, CaptureSnapshot

        selected = CapturedBundle(
            bundle.document,
            bundle.bundle_key,
            bundle.extractor_path,
            (synthetic,),
            CaptureSnapshot("typed@1", (), (), ()),
        )
    saved = store.save(selected, "synthetic")
    restored = store.load(saved).bundle.datasets[0]
    assert restored == synthetic
    assert type(restored.cells[0].value.value) is int
    assert restored.cells[0].value.value == 9007199254740993
    assert restored.cells[1].value.value == Decimal("0.00000001")
    assert [c.value.original_text for c in restored.cells[2:]] == ["N/A", "-", "", "0"]
