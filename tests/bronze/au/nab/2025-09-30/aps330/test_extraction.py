"""Independent PDF-to-payload contract for the selected NAB mortgage block."""

import json
from dataclasses import replace
from decimal import Decimal
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
    assert bundle.schema_version == "disclosure-v2"
    assert len(bundle.datasets) == 2
    assert_golden(
        encode_payload(
            replace(bundle, schema_version="cr6-v1", datasets=bundle.datasets[:1])
        ),
        expected,
    )
    golden = json.loads(Path(__file__).with_name("golden-cr9.json").read_text())
    dataset = bundle.datasets[1]
    metadata = dataset.metadata
    assert dataset.id == "cr9-residential-mortgages"
    assert metadata.context.source_portfolio_label == "Residential mortgage"
    assert metadata.context.source_template == "CR9"
    assert metadata.context.geography.status == "unresolved"
    assert len(dataset.backtesting_rows) == 8
    assert [f.id for f in metadata.published_fields] == golden["fields"]
    assert [f.source_label for f in metadata.published_fields] == golden["headers"]
    axes = {a.id: a for a in metadata.axes}
    for j, agency in enumerate(golden["rating_agencies"]):
        assert axes[f"rating-{j}"].source_label == agency
    for i, (row, want) in enumerate(zip(dataset.backtesting_rows, golden["rows"]), 1):
        rid = f"band-{i}"
        assert row.record_id == row.source_row_ref == rid
        assert row.source_row_role == "band"
        assert row.source_segment_memberships == (f"pd-band-{i}",)
        assert axes[rid].source_label == want[0]
        band = metadata.segmentations[0].bands[i - 1]
        assert band.source_label == want[0]
        assert band.kind == ("default" if i == 8 else "interval")
        if i < 8:
            lower, upper = want[0].split(" to <")
            assert (band.lower, band.upper) == (Decimal(lower), Decimal(upper))
            assert (band.lower_inclusive, band.upper_inclusive) == (True, False)
        else:
            assert band.lower is band.upper is None
            assert band.category == "100.00 (Default)"
        for j, rating in enumerate(golden["ratings"][i - 1]):
            axis = axes[f"{rid}-rating-{j}"]
            assert axis.source_label == rating
            assert axis.header_path_refs == (rid, f"rating-{j}")
            assert axis.source_reference.pdf_page == 46
        for name, token in zip(golden["fields"], want[1:]):
            cell = getattr(row, name)
            assert cell.original_text == token
            value = (
                None
                if token in ("", "-")
                else Decimal(token.replace(",", "").rstrip("%"))
            )
            assert cell.value == value
            assert cell.displayed_precision == (
                None if value is None else 0 if name.endswith("count") else 2
            )
            assert cell.missing_reason == (
                "blank_unresolved"
                if token == ""
                else "dash_unresolved"
                if token == "-"
                else None
            )
            assert cell.source_reference.pdf_page == 61
            assert cell.source_reference.printed_page == "59"
        assert {
            (b.field_key, b.role, b.descriptor_ref)
            for b in metadata.temporal_bindings
            if b.record_id == rid
        } == {tuple(r) for r in golden["temporal_roles"]}
    times = {t.id: t for t in metadata.temporal_descriptors}
    assert times["current-year"].point == "2025-09-30"
    assert times["previous-year"].point == "2024-09-30"
    assert times["annual"].start == "2024-10-01"
    assert times["annual"].end == "2025-09-30"
    assert times["history"].duration_amount == 10
    assert times["history"].duration_unit == "years"
    assert times["history"].start is times["history"].end is None
    assert times["history"].start_status == times["history"].end_status == "unresolved"
    assert times["unspecified"].point is None
    notes = {q.id: q for q in metadata.qualifications}
    for name, text in golden["notes"].items():
        assert notes[name].source_text == text
    assert "number of agreements" in notes["borrower-definition"].source_text
    assert notes["borrower-definition"].evidence[0].pdf_page == 48
    for field in metadata.published_fields:
        attrs = {a.name: a for a in field.attributes}
        if field.id.endswith("count"):
            assert attrs["counted_entity"].value == "agreement"
            assert attrs["distinctness"].status == "unresolved"
        assert field.source_unit == ("" if field.id.endswith("count") else "%")
        binding = next(b for b in metadata.bindings if b.typed_field_name == field.id)
        assert binding.published_field_ref == field.id
        assert binding.row_refs == tuple(f"band-{i}" for i in range(1, 9))
        assert binding.column_refs == ("column-" + field.id,)
        assert binding.qualification_refs == field.qualification_refs
        assert all(q in notes for q in field.qualification_refs)
    count_field = next(
        f for f in metadata.published_fields if f.id == "current_year_borrower_count"
    )
    assert "borrower-definition" in count_field.qualification_refs
    assert "cr9-weighting" not in count_field.qualification_refs
    assert times["current-year"].qualification_refs == ()
    assert len(metadata.relationships) == 7
    for i, relation in enumerate(metadata.relationships, 1):
        assert relation.kind == "subset"
        assert relation.parent.id == "defaulted_borrower_count"
        assert relation.children[0].id == "new_defaulted_borrower_count"
        assert relation.scope[0].id == f"band-{i}"
