"""Owns complete CBA PDF-to-source-contract correctness, including blank columns."""

from dataclasses import replace
from decimal import Decimal

import pytest

from rwa_analysis.extraction.values import parse_count_token, parse_decimal_token
from tests.support.captured_golden import assert_capture_bindings, golden_view


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("(4,504)", Decimal(-4504)),
        ("0.0800%", Decimal("0.0800")),
        ("0", Decimal(0)),
    ],
)
def test_source_token_conventions(token, expected):
    assert parse_decimal_token(token) == expected


def test_count_parser_rejects_fractional_count():
    with pytest.raises(ValueError, match="integral"):
        parse_count_token("1.5")


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
    assert bundle.schema_version == "disclosure-v4"
    assert_capture_bindings(bundle, 180)
    bundle = golden_view(bundle)
    assert len(bundle.datasets) == 2
    assert_golden(
        encode_payload(
            replace(bundle, schema_version="cr6-v1", datasets=bundle.datasets[:1])
        ),
        expected,
    )
    cr9 = bundle.datasets[1]
    golden = json.loads(Path(__file__).with_name("golden-cr9.json").read_text())
    assert_cr9_source(cr9, golden)


def assert_cr9_source(cr9, golden):
    metadata = cr9.metadata
    assert cr9.id == "cr9-residential-mortgages"
    assert metadata.context.source_title == golden["title"]
    assert metadata.context.source_portfolio_label == golden["portfolio"]
    assert metadata.context.regulatory_scope.value == golden["approach"]
    assert metadata.context.geography.status == "unresolved"
    assert metadata.context.currency.status == "unresolved"
    assert (
        metadata.context.reporting_entity.value
        == "CBA and its subsidiaries (the Group)"
    )
    assert metadata.context.consolidation_scope.value == "Level 2"
    assert [
        [f.id, f.source_label, f.source_unit] for f in metadata.published_fields
    ] == golden["fields"]
    axes = {a.id: a for a in metadata.axes}
    assert axes["rating-0"].source_label == "S&P"
    assert axes["rating-1"].source_label == "Moodys"
    assert axes["pd-heading"].source_label == "PD Range ¹"
    assert axes["borrower-counts"].source_label == "Number of borrowers"
    assert len(metadata.bindings) == 7
    for field, binding in zip(metadata.published_fields, metadata.bindings):
        assert binding.typed_field_name == binding.published_field_ref == field.id
        assert binding.row_refs == tuple(f"band-{i}" for i in range(1, 9))
        assert binding.column_refs == ("column-" + field.id,)
        assert list(field.qualification_refs) == golden["field_notes"][field.id]
        assert binding.qualification_refs == field.qualification_refs
        assert field.source_scale == Decimal(1)
        attrs = {a.name: (a.value, a.status) for a in field.attributes}
        if field.id == "weighted_average_pd":
            assert attrs == {"weighting": (None, "unresolved")}
        elif field.id == "arithmetic_average_pd":
            assert attrs == {
                "weighting": ("borrowers", "established"),
                "counted_entity": (None, "unresolved"),
            }
        elif field.id.endswith("count"):
            assert attrs == {"counted_entity": (None, "unresolved")}
    assert len(cr9.backtesting_rows) == 8
    for i, (row, cells, band) in enumerate(
        zip(cr9.backtesting_rows, golden["rows"], metadata.segmentations[0].bands)
    ):
        rid = f"band-{i + 1}"
        assert row.record_id == row.source_row_ref == rid
        assert row.source_segment_memberships == (f"pd-band-{i + 1}",)
        assert row.source_row_role == "band"
        assert axes[rid].source_label == band.source_label == cells[0]
        assert [axes[f"{rid}-rating-{j}"].source_label for j in range(2)] == cells[1:3]
        for j in range(2):
            assert axes[f"{rid}-rating-{j}"].header_path_refs == (rid, f"rating-{j}")
        assert [
            str(x) if x is not None else None for x in (band.lower, band.upper)
        ] == golden["bands"][i]
        assert band.kind == ("default" if i == 7 else "interval")
        assert (band.lower_inclusive, band.upper_inclusive) == (
            (None, None) if i == 7 else (True, False)
        )
        for (field, header, unit), token in zip(golden["fields"], cells[3:]):
            value = getattr(row, field)
            assert value.original_text == token
            missing = token in ("", "–")
            assert value.value == (None if missing else Decimal(token.replace(",", "")))
            assert value.displayed_precision == (
                None if missing else 0 if unit == "#" else 2
            )
            assert value.missing_reason == (
                "blank_unresolved"
                if token == ""
                else "dash_unresolved"
                if token == "–"
                else None
            )
            assert value.source_reference.pdf_page == 60
            assert value.source_reference.row == cells[0]
            assert value.source_reference.column == header
    notes = {q.id: q for q in metadata.qualifications}
    for key, text in golden["notes"].items():
        assert notes[key].source_text == text
        assert notes[key].evidence[0].pdf_page == (
            {"non-performing-definition": 116, "retail-non-performing": 51}.get(key, 60)
        )
    assert "pd-weighting" not in notes
    assert [(s.kind, s.id) for s in notes["cr9-history"].scope] == [
        ("field", "historical_annual_default_rate")
    ]
    assert [(s.kind, s.id) for s in notes["cr9-bands"].scope] == [("dataset", cr9.id)]
    assert [
        [
            d.id,
            d.source_label,
            d.point,
            d.start,
            d.end,
            str(d.duration_amount) if d.duration_amount else None,
            d.duration_unit,
        ]
        for d in metadata.temporal_descriptors
    ] == golden["timing"]
    for d in metadata.temporal_descriptors:
        for component in ("point", "start", "end"):
            assert getattr(d, component + "_status") == (
                "established" if getattr(d, component) else "unresolved"
            )
    assert [
        (b.record_id, b.field_key, b.role, b.descriptor_ref)
        for b in metadata.temporal_bindings
    ] == [(f"band-{i}", *role) for i in range(1, 9) for role in golden["roles"]]
    assert len(metadata.relationships) == 7
    for i, relationship in enumerate(metadata.relationships, 1):
        assert relationship.kind == "subset"
        assert relationship.parent.kind == "field"
        assert relationship.parent.id == "defaulted_borrower_count"
        assert [(c.kind, c.id) for c in relationship.children] == [
            ("field", "new_defaulted_borrower_count")
        ]
        assert [(s.kind, s.id) for s in relationship.scope] == [("row", f"band-{i}")]
        assert relationship.exhaustive is False
        assert relationship.mutually_exclusive is None
        assert relationship.evidence[0].pdf_page == 60
        assert relationship.evidence[0].row == golden["rows"][i - 1][0]
