"""Saved payload boundary owns strict types, schema closure and source references."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def payload():
    return json.loads(
        (
            Path(__file__).parent / "bronze/au/cba/2025-06-30/aps330/golden.json"
        ).read_text()
    )


def test_saved_payload_restores_types_and_decimal_exponent(payload):
    from decimal import Decimal

    from rwa_analysis.extraction.codec import decode_payload, encode_payload

    payload["datasets"][0]["records"][0]["average_pd"]["value"] = "0.0800"
    bundle = decode_payload(payload)
    row = bundle.datasets[0].records[0]
    assert isinstance(row.average_pd.value, Decimal)
    assert row.average_pd.value.as_tuple().exponent == -4
    assert type(row.reported_borrower_count.value) is int
    assert row.average_maturity.value is None
    assert encode_payload(bundle) == payload


def test_bundle_rejects_mutable_source_collections(payload):
    from dataclasses import replace

    from rwa_analysis.extraction.codec import decode_payload

    bundle = decode_payload(payload)
    with pytest.raises(TypeError, match="tuple"):
        replace(bundle, datasets=list(bundle.datasets))


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("schema_version",), "future"),
        (("datasets", 0, "context", "currency", "status"), "guessed"),
        (("datasets", 0, "records", 0, "ead", "value"), 281508.0),
        (("datasets", 0, "records", 0, "ead", "value"), "NaN"),
        (("datasets", 0, "records", 0, "ead", "value"), "Infinity"),
        (("datasets", 0, "records", 0, "reported_borrower_count", "value"), "742470"),
        (("datasets", 0, "records", 0, "reported_borrower_count", "value"), True),
        (("datasets", 0, "records", 0, "ead", "missing_reason"), "blank_unresolved"),
        (("datasets", 0, "records", 0, "average_maturity", "missing_reason"), None),
        (("datasets", 0, "records", 0, "source_row_ref"), "missing-row"),
        (("datasets", 0, "records", 0, "source_segment_memberships"), ["missing-band"]),
        (("datasets", 0, "records", 0, "source_aggregation_scope"), ["missing-block"]),
        (("datasets", 0, "records", 1, "record_id"), "band-1"),
        (("datasets", 0, "bindings", 0, "published_field_ref"), "missing-field"),
        (("datasets", 0, "bindings", 0, "typed_field_name"), "unknown"),
        (("datasets", 0, "axes", 0, "header_path_refs"), ["missing-header"]),
        (
            ("datasets", 0, "published_fields", 0, "qualification_refs"),
            ["missing-note"],
        ),
        (("datasets", 0, "relationships", 0, "parent", "id"), "missing-parent"),
        (("datasets", 0, "qualifications", 0, "scope", 0, "id"), "missing-dataset"),
        (("datasets", 0, "context", "evidence", 0, "document_id"), "other-document"),
        (("datasets", 0, "context", "evidence", 0, "pdf_page"), 0),
    ],
)
def test_rejects_invalid_saved_contract(payload, path, replacement):
    from rwa_analysis.extraction.codec import decode_payload

    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises((ValueError, TypeError)):
        decode_payload(payload)


def test_decoder_rejects_unknown_nested_field(payload):
    from rwa_analysis.extraction.codec import decode_payload

    cell = payload["datasets"][0]["records"][0]["ead"]
    cell["unknown"] = "lost metadata"
    with pytest.raises(ValueError, match="unknown"):
        decode_payload(payload)


def test_runner_rejects_missing_pdf_and_wrong_result(tmp_path):
    from rwa_analysis.extraction.runner import run_extractor

    script = tmp_path / "extract.py"
    script.write_text("def extract(pdf_path):\n    return {}\n")
    pdf = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError):
        run_extractor(script, pdf)
    pdf.touch()
    with pytest.raises(TypeError, match="ExtractionBundle"):
        run_extractor(script, pdf)
