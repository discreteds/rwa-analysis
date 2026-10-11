"""Independent PDF-to-payload contract for the selected NAB mortgage block."""

import json
from pathlib import Path

from rwa_analysis.extraction.codec import encode_payload
from rwa_analysis.extraction.runner import run_extractor
from tests.support.golden import assert_golden


def test_complete_nab_source_contract():
    root = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "AGENTS.md").exists() and (p / "raw").is_dir()
    )
    pdf = root / "raw/nab-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/nab/2025-09-30/aps330/extract.py", pdf
    )
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert_golden(encode_payload(bundle), expected)
