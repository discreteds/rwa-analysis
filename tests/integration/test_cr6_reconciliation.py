"""Renderer boundary: real persisted numbers, missingness and publication identity."""

import json
from decimal import Decimal
from html.parser import HTMLParser

import pytest
from mountainash_data import IbisBackend


def table_cell(path, view, observation_id, field_key):
    class Cell(HTMLParser):
        active = False
        found = False
        text = ""

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "td":
                self.active = all(
                    attrs.get(k) == v
                    for k, v in {
                        "data-view": view,
                        "data-observation-id": observation_id,
                        "data-field-key": field_key,
                    }.items()
                )
                self.found |= self.active

        def handle_endtag(self, tag):
            if tag == "td":
                self.active = False

        def handle_data(self, data):
            if self.active:
                self.text += data

    parser = Cell()
    parser.feed(path.read_text())
    assert parser.found, (view, observation_id, field_key)
    return parser.text


def test_persisted_numeric_mutations_and_absence_are_visible(tmp_path, published_cr6):
    from rwa_analysis.reporting.cr6_reconciliation import render_cr6_reconciliation

    manifest, root, warehouse = published_cr6
    oid = "au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1"
    for label, amount, displayed, exact in (
        ("whole", "281509000000", "281,509", "281509"),
        ("subdisplay", "281508000000.01", "281,508", "281508.00000001"),
        ("absent", None, "absent row", None),
    ):
        with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
            raw = db.raw_driver_connection()
            if amount is None:
                raw.execute(
                    "DELETE FROM silver.observations WHERE observation_id = ?", [oid]
                )
            else:
                raw.execute(
                    "UPDATE silver.observations SET ead_amount = ? WHERE observation_id = ?",
                    [amount, oid],
                )
        out = tmp_path / label
        render_cr6_reconciliation(manifest, root, warehouse, out)
        page = out / "cba-2025-06-30-cr6.html"
        assert table_cell(page, "bronze", oid, "ead") == "281,508"
        assert table_cell(page, "silver", oid, "ead") == displayed
        findings = json.loads((out / "differences.json").read_text())
        finding = next(
            f
            for f in findings
            if f.get("observation_id") == oid and f.get("field_key") == "ead"
        )
        assert Decimal(finding["source_value"]) == Decimal(281508)
        if exact is not None:
            assert Decimal(finding["reconstructed_value"]) == Decimal(exact)


def test_actual_four_bank_presentation_and_revision_guard(tmp_path, published_cr6):
    from rwa_analysis.reporting.cr6_reconciliation import render_cr6_reconciliation

    manifest, root, warehouse = published_cr6
    out = tmp_path / "review"
    assert (
        render_cr6_reconciliation(manifest, root, warehouse, out) == out / "index.html"
    )
    assert json.loads((out / "differences.json").read_text()) == []
    for org, date, row, field, token in (
        ("cba", "2025-06-30", "band-1", "average_maturity", ""),
        ("westpac", "2025-09-30", "band-8", "average_ccf", "-"),
        ("nab", "2025-09-30", "band-1", "rwa_density", "6.0%"),
        ("anz", "2025-09-30", "band-1", "average_maturity", "-"),
    ):
        page = out / f"{org}-{date}-cr6.html"
        oid = f"au/{org}/{date}/aps330/cr6-residential-mortgages/{row}"
        for view in ("bronze", "silver"):
            assert table_cell(page, view, oid, field) == token
    with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
        db.raw_driver_connection().execute(
            "UPDATE ops.silver_publication SET silver_revision_id = 'different'"
        )
    with pytest.raises(ValueError, match="revision"):
        render_cr6_reconciliation(manifest, root, warehouse, tmp_path / "wrong")
