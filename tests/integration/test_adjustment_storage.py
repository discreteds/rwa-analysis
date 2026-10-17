"""Adjustment conformance and readback use saved evidence and declared money scales."""

import json
from decimal import Decimal
from pathlib import Path
from runpy import run_path

from rwa_analysis.composition import build_consolidator, build_session
from rwa_analysis.operations import DocumentSelection
from rwa_analysis.settings import OrganisationSettings, ProjectSettings
from rwa_analysis.storage.manifests import CatalogueSelection


def test_adjustments_survive_staging_and_master(tmp_path):
    root = Path(__file__).resolve().parents[2]
    settings = {
        "project_root": root,
        "bronze_root": tmp_path / "bronze",
        "manifest_root": tmp_path / "manifests",
    }
    publications = []
    for bank, day in (
        ("cba", "2025-06-30"),
        ("anz", "2025-09-30"),
        ("nab", "2025-09-30"),
        ("westpac", "2025-09-30"),
    ):
        session = build_session(
            OrganisationSettings(
                **settings,
                organisation_id=bank,
                staging_path=tmp_path / f"{bank}.duckdb",
            )
        )
        result = session.run(
            documents=(
                DocumentSelection(
                    f"extractions/au/{bank}/{day}/aps330/extract.py",
                    f"raw/{bank}-{day}-aps330.pdf",
                ),
            ),
            catalogue=CatalogueSelection(
                release_path="catalogue/releases/cr6-cr9-v1.json"
            ),
            run_name="adjustments-test",
            revision=f"{bank}-adjustments-test",
        )
        publications.append(result.publication)
    master = build_consolidator(
        ProjectSettings(**settings, master_path=tmp_path / "master.duckdb")
    )
    publication = master.consolidate(tuple(publications), revision="adjustments-test")
    for staging in publications:
        staging.database.unlink()
    output = master.store.read(publication)
    amounts = {
        (r["table_id"].split("/")[1], r["cell_id"]): r["normalised_amount"]
        for r in output.source_tables.meanings.to_dicts()
        if r["table_id"].endswith("/rwa-adjustments")
    }
    assert amounts[("cba", "mortgage-floor")] == Decimal("2400000000.00")
    assert amounts[("anz", "mortgage-pd-overlay")] == Decimal("3100000000.00")
    assert amounts[("nab", "mortgage-overview-rwa")] == Decimal("112064000000.00")
    assert amounts[("westpac", "operational-capital-overlay")] == Decimal(
        "500000000.00"
    )
    assert amounts[("westpac", "operational-rwa-removal")] == Decimal("6250000000.00")
    cet1 = next(
        r
        for r in output.source_tables.meanings.to_dicts()
        if r["cell_id"] == "cet1-ratio-increase"
    )
    assert cet1["unit_factor"] == Decimal("0.0001")
    assert cet1["normalised_scalar"] == Decimal("0.00170000")
    assert output.cr6.observations.count_rows() == 36
    assert output.cr9.observations.count_rows() == 33
    anz = "au/anz/2025-09-30/aps330/cr6-residential-mortgages"
    treatment = {
        r["owner_id"]: (r["value_text"], r["status"])
        for r in output.source_tables.attributes.to_dicts()
        if r["table_id"] == anz
        and r["owner_kind"] == "cell"
        and r["name"] == "overlay_treatment"
    }
    assert treatment["portfolio-aggregate/rwa"] == ("included", "established")
    assert treatment["band-1/rwa"] == (None, "unresolved")
    assert any(
        r["table_id"] == anz
        and r["owner_id"] == "portfolio-aggregate/rwa"
        and r["decision_revision_id"] == "agreed.anz-2025-aggregate-overlay@v1"
        for r in output.source_tables.attribute_decisions.to_dicts()
    )
    retain_results = run_path(str(root / "examples/rwa_adjustments.py"))[
        "retain_results"
    ]
    retain_results(output, publication, tmp_path / "research")
    bridge = json.loads(
        (tmp_path / "research/nab-mortgage-rwa-bridge.json").read_text()
    )
    assert Decimal(bridge["result"]["difference_amount"]) == Decimal("50000000.00")
    assert bridge["classification"] == "derived_reconciliation_difference"
    assert bridge["master_revision"] == "adjustments-test"
    assert len(bridge["inputs"]) == 2
