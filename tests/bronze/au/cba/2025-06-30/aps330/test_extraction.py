"""Owns complete CBA PDF-to-source-contract correctness, including blank columns."""

import runpy
from decimal import Decimal
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("(4,504)", Decimal(-4504)),
        ("0.0800%", Decimal("0.0800")),
        ("-", None),
        ("", None),
        ("0", Decimal(0)),
    ],
)
def test_source_token_conventions(token, expected):
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").exists()
    )
    script = runpy.run_path(
        str(root / "extractions/au/cba/2025-06-30/aps330/extract.py")
    )
    assert script["parse_decimal_token"](token) == expected


def test_count_parser_rejects_fractional_count():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").exists()
    )
    script = runpy.run_path(
        str(root / "extractions/au/cba/2025-06-30/aps330/extract.py")
    )
    with pytest.raises(ValueError, match="integral"):
        script["parse_count_token"]("1.5")


def test_complete_cba_source_contract():
    import json
    from pathlib import Path

    from rwa_analysis.extraction.codec import encode_payload
    from rwa_analysis.extraction.runner import run_extractor
    from tests.support.golden import assert_golden

    root = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "AGENTS.md").exists() and (p / "raw").is_dir()
    )
    pdf = root / "raw/cba-2025-06-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/cba/2025-06-30/aps330/extract.py", pdf
    )
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
