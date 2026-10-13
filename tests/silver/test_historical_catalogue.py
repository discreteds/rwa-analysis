"""Source-reviewed CBA semantics, distinct from synthetic composition coverage."""

from dataclasses import replace
from decimal import Decimal

import pytest

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import RevisionRef
from rwa_analysis.domains.source_tables.semantics import resolve_cell


@pytest.fixture
def historical_catalogue(project_root):
    return load_catalogue(
        project_root / "catalogue/releases/historical-mortgages-v1.json"
    )


def test_cba_panels_reuse_lgd_with_local_overlay_evidence(
    historical_catalogue, cba_2024_bundle
):
    meanings = []
    for table in cba_2024_bundle.datasets[:3]:
        cell = next(c for c in table.cells if c.id == "lgd/band-0")
        meaning = resolve_cell(historical_catalogue, cba_2024_bundle, table, cell)
        meanings.append(meaning)
        assert meaning.concept_ref == RevisionRef(
            "concept", "risk.loss-given-default@v1"
        )
        assert meaning.measure_ref == RevisionRef(
            "measure", "measure.cba.historical.exposure-lgd@v1"
        )
        assert meaning.unit_factor == Decimal("0.01")
        assert meaning.attribute("weighting").value == "weighted_average"
        assert meaning.attribute("weight_measure").status == "unresolved"
        overlay = meaning.attribute("overlay_treatment")
        assert overlay.value == "excludes_overlays"
        assert {(e.dataset_id, e.ref_id) for e in overlay.evidence_refs} == {
            (table.id, "overlay")
        }
        assert {e.dataset_id for e in meaning.attribute("measure").evidence_refs} == {
            table.id
        }
    assert len({m.mapping_refs for m in meanings}) == 3


def test_cba_note_is_rwa_overlay_not_a_body_total(
    historical_catalogue, cba_2024_bundle
):
    table = cba_2024_bundle.datasets[0]
    cell = next(c for c in table.cells if c.id == "overlay")
    meaning = resolve_cell(historical_catalogue, cba_2024_bundle, table, cell)
    assert meaning.concept_ref == RevisionRef(
        "concept", "capital.risk-weighted-assets@v1"
    )
    assert meaning.measure_ref == RevisionRef(
        "measure", "measure.cba.historical.rwa-overlay@v1"
    )
    assert meaning.attribute("overlay_treatment").value == "overlay_amount_only"
    assert meaning.unit_factor == Decimal(1000000000)


def test_cba_unknown_average_ead_and_other_occurrences_do_not_inherit_lgd(
    historical_catalogue, cba_2024_bundle
):
    table = cba_2024_bundle.datasets[0]
    average = next(c for c in table.cells if c.id == "average_ead/band-0")
    meaning = resolve_cell(historical_catalogue, cba_2024_bundle, table, average)
    assert meaning.measure_ref is None
    assert meaning.attribute("counted_entity").status == "unresolved"
    assert {
        (e.dataset_id, e.ref_id)
        for e in meaning.attribute("counted_entity").evidence_refs
    } == {(table.id, "average_ead")}
    assert meaning.unit_factor == Decimal(1000000)
    for field in ("exposure", "undrawn", "risk_weight"):
        cell = next(c for c in table.cells if c.field_ref == field)
        meaning = resolve_cell(historical_catalogue, cba_2024_bundle, table, cell)
        assert meaning.measure_ref is None
        assert meaning.attribute("overlay_treatment").status == "unresolved"
    other_table = replace(table, id="unreviewed-panel")
    lgd = next(c for c in table.cells if c.id == "lgd/band-0")
    assert (
        resolve_cell(
            historical_catalogue, cba_2024_bundle, other_table, lgd
        ).measure_ref
        is None
    )
