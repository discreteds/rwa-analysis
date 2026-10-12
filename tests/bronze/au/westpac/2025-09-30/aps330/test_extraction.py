import json
from dataclasses import replace
from pathlib import Path

from rwa_analysis.extraction.codec import encode_payload
from rwa_analysis.extraction.runner import run_extractor
from tests.support.golden import assert_golden


def test_complete_westpac_source_contract():
    root = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "AGENTS.md").exists() and (p / "raw").is_dir()
    )
    pdf = root / "raw/westpac-2025-09-30-aps330.pdf"
    assert pdf.is_file(), f"Required saved disclosure missing: {pdf}"
    bundle = run_extractor(
        root / "extractions/au/westpac/2025-09-30/aps330/extract.py", pdf
    )
    expected = json.loads(Path(__file__).with_name("golden.json").read_text())
    assert bundle.schema_version == "disclosure-v2"
    assert len(bundle.datasets) == 2
    assert_golden(
        encode_payload(
            replace(bundle, schema_version="cr6-v1", datasets=bundle.datasets[:1])
        ),
        expected,
    )
    cr9 = json.loads(Path(__file__).with_name("golden-cr9.json").read_text())
    from tests.support.golden import assert_westpac_cr9

    assert_westpac_cr9(bundle.datasets[1], cr9, expected["datasets"][0])
