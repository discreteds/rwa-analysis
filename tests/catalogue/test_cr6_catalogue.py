"""Public catalogue boundary: source-backed meaning, isolation and closed releases.

These tests own semantic interpretation, not extraction values. Real extracted
inputs catch cross-field/bank leakage; edited release files exercise revision
closure, ambiguity and declared override behavior without resolver test seams.
"""

import json
import shutil
from copy import deepcopy
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture
def catalogue(project_root):
    from rwa_analysis.catalogue.load import load_catalogue

    return load_catalogue(project_root / "catalogue/releases/cr6-v1.json")


def meaning(cat, bundle, field, row=0):
    from rwa_analysis.catalogue.resolve import resolve_field

    ds = bundle.datasets[0]
    return resolve_field(cat, ds, ds.records[row], field)


def test_cba_pd_evidence_does_not_leak_to_lgd(catalogue, cba_bundle):
    pd = meaning(catalogue, cba_bundle, "average_pd")
    lgd = meaning(catalogue, cba_bundle, "average_lgd")
    assert pd.attribute("weighting").value == "period_end_ead"
    assert pd.attribute("weighting").evidence_refs
    assert pd.attribute("weight_timing").value == "period_end"
    assert (
        pd.attribute("weight_measure").value
        == meaning(catalogue, cba_bundle, "ead").measure_ref
    )
    assert pd.unit_factor == Decimal("0.01")
    assert lgd.attribute("weighting").status == "unresolved"
    assert lgd.unit_factor == Decimal("0.01")
    count = meaning(catalogue, cba_bundle, "reported_borrower_count")
    assert count.attribute("counted_entity").status == "unresolved"
    assert count.attribute("result_unit").value != pd.attribute("result_unit").value
    assert meaning(catalogue, cba_bundle, "regulatory_expected_loss").concept_ref != (
        meaning(catalogue, cba_bundle, "provisions").concept_ref
    )
    assert (
        meaning(catalogue, cba_bundle, "rwa_density")
        .attribute("calculation_precision")
        .value
        == "unrounded_inputs"
    )


def test_source_specific_count_overlay_and_perimeter(
    catalogue, cba_bundle, nab_bundle, anz_bundle
):
    count = meaning(catalogue, nab_bundle, "reported_borrower_count")
    assert count.attribute("counted_entity").value == "arrangement"
    assert count.attribute("counted_entity").evidence_refs
    assert count.attribute("counted_entity").decision_refs
    assert count.attribute("distinctness").status == "unresolved"
    other = meaning(catalogue, anz_bundle, "reported_borrower_count")
    assert other.attribute("counted_entity").status == "unresolved"
    assert other.attribute("counted_entity").evidence_refs
    assert other.attribute("reporting_entity").value == "ANZ BH Pty Ltd"
    assert other.attribute("consolidation_scope").value == "Level 2"
    assert other.attribute("regulatory_scope").value == "AIRB"
    assert other.attribute("geography").status == "provisional"
    for field in ("rwa", "rwa_density"):
        assert (
            meaning(catalogue, nab_bundle, field).attribute("overlay_treatment").value
            == "excludes_overlays"
        )
        anz = meaning(catalogue, anz_bundle, field).attribute("overlay_treatment")
        assert anz.status == "unresolved"
        assert any(e.ref_id == "cms2-overlay-context" for e in anz.evidence_refs)
        assert not anz.decision_refs  # No agreed CR6 inference exists yet.
    assert (
        meaning(catalogue, cba_bundle, "rwa").attribute("overlay_treatment").value
        == "includes_overlays"
    )
    basis = meaning(catalogue, nab_bundle, "on_balance_exposure").attribute(
        "exposure_basis"
    )
    assert basis.value == "ead_pre_crm"
    assert basis.evidence_refs
    maturity = meaning(catalogue, anz_bundle, "average_maturity").attribute(
        "missingness"
    )
    assert maturity.value == "not_used_in_rwa_calculation"
    assert maturity.status == "not_applicable"
    assert {e.ref_id for e in maturity.evidence_refs} == {
        "maturity-definition",
        "maturity-modification",
    }


@pytest.mark.parametrize("change", ["document", "date", "portfolio", "template"])
def test_scope_is_conjunctive(catalogue, cba_bundle, westpac_bundle, change):
    from rwa_analysis.catalogue.resolve import resolve_field

    ds = cba_bundle.datasets[0]
    if change == "document":
        assert (
            meaning(catalogue, westpac_bundle, "average_pd")
            .attribute("weighting")
            .status
            == "unresolved"
        )
        # Change only the occurrence document so another scope guard cannot
        # mask a broken document predicate.
        row = ds.records[0]
        pd = replace(
            row.average_pd,
            source_reference=replace(
                row.average_pd.source_reference,
                document_id=westpac_bundle.document.document_id,
            ),
        )
        ds = replace(ds, records=(replace(row, average_pd=pd), *ds.records[1:]))
    else:
        updates = {
            "date": {"observation_date": date(2025, 9, 30)},
            "portfolio": {"source_portfolio_label": "Corporate"},
            "template": {"source_template": "CR9"},
        }[change]
        ds = replace(ds, context=replace(ds.context, **updates))
    result = resolve_field(catalogue, ds, ds.records[0], "average_pd")
    assert result.attribute("weighting").status == "unresolved"


def test_row_population_and_aggregate_are_distinct(catalogue, cba_bundle):
    default = meaning(catalogue, cba_bundle, "average_pd", 7)
    total = meaning(catalogue, cba_bundle, "average_pd", 8)
    assert default.attribute("default_state").value == "default"
    assert default.attribute("pd_band").value.ref_id == "pd-band-8"
    assert total.attribute("row_role").value == "portfolio_aggregate"
    assert total.attribute("pd_band").status == "unresolved"


@pytest.fixture
def editable_catalogue(tmp_path, project_root):
    root = tmp_path / "catalogue"
    shutil.copytree(project_root / "catalogue", root)
    return root


def edit_members(root, relative, edit):
    path = root / relative
    payload = json.loads(path.read_text())
    edit(payload["members"])
    path.write_text(json.dumps(payload))


@pytest.mark.parametrize("change", ["absent", "conflict", "cycle", "wrong_kind"])
def test_release_edits_resolve_or_fail_structurally(
    editable_catalogue, cba_bundle, change
):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.catalogue.resolve import resolve_field

    root = editable_catalogue
    mapping_path = "mappings/cba-2025-06-30-v1.json"
    new_id = "cba.cr6.pd-alternative@v1"

    def edit(members):
        pd = next(m for m in members if m["id"] == "cba.cr6.average_pd")
        if change in ("absent", "wrong_kind"):
            pd["measure_ref"]["revision_id"] = (
                "missing@v9" if change == "absent" else "unit.ratio@v1"
            )
        else:
            other = deepcopy(pd)
            other.update(id="cba.cr6.pd-alternative", revision_id=new_id)
            other["measure_ref"] = None
            other["attributes"] = [
                {
                    "name": "weighting",
                    "value": "account_weighted",
                    "status": "established",
                    "evidence_refs": [
                        {
                            "bundle_key": "au/cba/2025-06-30/aps330",
                            "document_id": "cba-2025-06-30-aps330",
                            "dataset_id": "cr6-residential-mortgages",
                            "kind": "qualification",
                            "ref_id": "synthetic-competing-note",
                        }
                    ],
                }
            ]
            if change == "cycle":
                pd["supersedes_refs"] = [{"kind": "mapping", "revision_id": new_id}]
                other["supersedes_refs"] = [
                    {"kind": "mapping", "revision_id": pd["revision_id"]}
                ]
            members.append(other)

    edit_members(root, mapping_path, edit)
    release = root / "releases/cr6-v1.json"
    if change in ("conflict", "cycle"):
        payload = json.loads(release.read_text())
        payload["selection"].append(
            {"path": mapping_path, "kind": "mapping", "revision_id": new_id}
        )
        release.write_text(json.dumps(payload))
    if change != "conflict":
        with pytest.raises(
            ValueError,
            match={
                "absent": "missing@v9",
                "cycle": "[Cc]ycle",
                "wrong_kind": "unit.ratio@v1",
            }[change],
        ):
            load_catalogue(release)
        return
    cat = load_catalogue(release)
    ds = cba_bundle.datasets[0]
    result = resolve_field(cat, ds, ds.records[0], "average_pd")
    weighting = result.attribute("weighting")
    assert weighting.status == "conflicting"
    assert {e.ref_id for e in weighting.evidence_refs} == {
        "pd-weighting",
        "synthetic-competing-note",
    }
    assert {a.value for a in weighting.alternatives} == {
        "period_end_ead",
        "account_weighted",
    }
    assert result.unit_factor == Decimal("0.01")
    # Reordering the pinned selection and member file must not choose a winner.
    payload = json.loads(release.read_text())
    payload["selection"].reverse()
    release.write_text(json.dumps(payload))
    edit_members(root, mapping_path, lambda members: members.reverse())
    assert (
        resolve_field(load_catalogue(release), ds, ds.records[0], "average_pd")
        == result
    )


@pytest.mark.parametrize("declared", [False, True])
def test_narrow_mapping_needs_explicit_supported_override(
    editable_catalogue, cba_bundle, declared
):
    from rwa_analysis.catalogue.load import load_catalogue

    root = editable_catalogue
    relative = "mappings/cba-2025-06-30-v1.json"
    new_id = "cba.cr6.pd-default@v1"

    def edit(members):
        pd = next(m for m in members if m["id"] == "cba.cr6.average_pd")
        other = deepcopy(pd)
        other.update(id="cba.cr6.pd-default", revision_id=new_id, measure_ref=None)
        other["scope"]["record_id"] = "band-8"
        other["attributes"] = [
            {
                "name": "weighting",
                "value": "default_specific",
                "status": "provisional",
                "evidence_refs": pd["evidence_refs"],
            }
        ]
        if declared:
            other["overrides_refs"] = [
                {"kind": "mapping", "revision_id": pd["revision_id"]}
            ]
        members.append(other)

    edit_members(root, relative, edit)
    release = root / "releases/cr6-v1.json"
    payload = json.loads(release.read_text())
    payload["selection"].append(
        {"path": relative, "kind": "mapping", "revision_id": new_id}
    )
    release.write_text(json.dumps(payload))
    cat = load_catalogue(release)
    result = meaning(cat, cba_bundle, "average_pd", 7)
    assert result.attribute("weighting").status == (
        "provisional" if declared else "conflicting"
    )
    assert result.unit_factor == Decimal("0.01")
    assert (
        meaning(cat, cba_bundle, "average_pd").attribute("weighting").value
        == "period_end_ead"
    )


def test_unknown_scale_keeps_semantics_without_inventing_conversion(
    catalogue, cba_bundle
):
    from rwa_analysis.catalogue.resolve import resolve_field

    ds = cba_bundle.datasets[0]
    ds = replace(
        ds,
        published_fields=tuple(
            replace(f, source_scale=None) if f.id == "average_pd" else f
            for f in ds.published_fields
        ),
    )
    result = resolve_field(catalogue, ds, ds.records[0], "average_pd")
    assert result.unit_factor is None
    assert result.attribute("weighting").value == "period_end_ead"


@pytest.mark.parametrize(
    "change",
    [
        "unknown_field",
        "bad_status",
        "float_factor",
        "not_unit",
        "bad_population",
        "unsupported_override",
        "alternative_population",
        "alternative_decision",
        "alternative_unit",
        "alternative_known_null",
        "alternative_unknown_value",
    ],
)
def test_strict_typed_release_rejects_malformed_meaning(editable_catalogue, change):
    from rwa_analysis.catalogue.load import load_catalogue

    root = editable_catalogue
    relative = "mappings/cba-2025-06-30-v1.json"

    def edit(members):
        pd = next(m for m in members if m["id"] == "cba.cr6.average_pd")
        if change == "unknown_field":
            pd["silent_typo"] = "must not disappear"
        elif change == "bad_status":
            pd["attributes"] = [
                {"name": "weighting", "value": "x", "status": "certain"}
            ]
        elif change == "float_factor":
            pd["conversion"]["unit_factor"] = 0.01
        elif change == "not_unit":
            pd["attributes"] = [
                {
                    "name": "result_unit",
                    "value": {
                        "kind": "concept",
                        "revision_id": "risk.default-probability@v1",
                    },
                    "status": "established",
                }
            ]
        elif change == "bad_population":
            pd["attributes"] = [
                {"name": "population", "value": True, "status": "established"}
            ]
        elif change.startswith("alternative_"):
            assertion = {
                "value": {
                    "kind": "concept",
                    "revision_id": "population.residential-mortgages@v1",
                },
                "status": "established",
            }
            name = "population"
            if change == "alternative_population":
                assertion["value"] = True
            elif change == "alternative_decision":
                assertion["decision_refs"] = [
                    {"kind": "concept", "revision_id": "unit.money@v1"}
                ]
            elif change == "alternative_unit":
                name = "result_unit"
            elif change == "alternative_known_null":
                assertion["value"] = None
            else:
                assertion["status"] = "unresolved"
            pd["attributes"] = [
                {
                    "name": name,
                    "value": None,
                    "status": "conflicting",
                    "alternatives": [assertion],
                }
            ]
        else:
            pd["overrides_refs"] = [
                {"kind": "mapping", "revision_id": "cba.cr6.average_lgd@v1"}
            ]

    edit_members(root, relative, edit)
    with pytest.raises(ValueError):
        load_catalogue(root / "releases/cr6-v1.json")


@pytest.mark.parametrize("effective_from", ["2025-06-30", "2025-07-01"])
def test_correction_retains_history_without_executing_superseded_mapping(
    editable_catalogue, cba_bundle, effective_from
):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.catalogue.models import RevisionRef

    root = editable_catalogue
    relative = "mappings/cba-2025-06-30-v1.json"
    old_release = root / "releases/cr6-v1.json"
    old = load_catalogue(old_release)
    old_ref = RevisionRef("mapping", "cba.cr6.on_balance_exposure@v1")
    new_ref = RevisionRef("mapping", "cba.cr6.on_balance_exposure@v2")

    def edit(members):
        prior = next(m for m in members if m["revision_id"] == old_ref.revision_id)
        correction = deepcopy(prior)
        correction.update(
            revision_id=new_ref.revision_id,
            effective_from=effective_from,
            effective_to="2025-07-31",
        )
        correction["scope"]["observation_to"] = "2025-07-31"
        correction["supersedes_refs"] = [
            {"kind": "mapping", "revision_id": old_ref.revision_id}
        ]
        next(a for a in correction["attributes"] if a["name"] == "exposure_basis")[
            "value"
        ] = "synthetic_corrected_basis"
        members.append(correction)

    edit_members(root, relative, edit)
    new_release = root / "releases/correction.json"
    payload = json.loads(old_release.read_text())
    payload["id"] = "synthetic-correction"
    payload["selection"].append(
        {"path": relative, "kind": "mapping", "revision_id": new_ref.revision_id}
    )
    new_release.write_text(json.dumps(payload))
    corrected = load_catalogue(new_release)
    # Closure and old release reproducibility survive retention of the predecessor.
    assert corrected.member(old_ref) == old.member(old_ref)
    assert meaning(
        load_catalogue(old_release), cba_bundle, "on_balance_exposure"
    ) == meaning(old, cba_bundle, "on_balance_exposure")
    result = meaning(corrected, cba_bundle, "on_balance_exposure")
    applies = effective_from == "2025-06-30"
    assert result.attribute("exposure_basis").value == (
        "synthetic_corrected_basis" if applies else "original_gross_exposure"
    )
    assert result.attribute("exposure_basis").status == "established"
    assert (old_ref in result.mapping_refs) is not applies
    assert (new_ref in result.mapping_refs) is applies
    assert result.unit_factor == Decimal(1000000)


@pytest.mark.parametrize(
    "definition", ["measure.cba.cr6.average_pd", "measure.cba.cr6.ead"]
)
@pytest.mark.parametrize(
    "interval",
    [
        ("2025-01-01", "2025-06-29", False),
        ("2025-07-01", "2025-12-31", False),
        ("2025-06-30", "2025-06-30", True),
    ],
)
def test_definition_and_weight_dependency_effective_boundaries(
    editable_catalogue, cba_bundle, definition, interval
):
    from rwa_analysis.catalogue.load import load_catalogue

    start, end, applies = interval

    def edit(members):
        measure = next(m for m in members if m["id"] == definition)
        measure.update(effective_from=start, effective_to=end)

    edit_members(editable_catalogue, "measures/cr6-v1.json", edit)
    cat = load_catalogue(editable_catalogue / "releases/cr6-v1.json")
    result = meaning(cat, cba_bundle, "average_pd")
    assert result.attribute("weighting").status == (
        "established" if applies else "unresolved"
    )
    assert (result.measure_ref is not None) is applies
    assert result.concept_ref is not None
    assert result.unit_factor == Decimal("0.01")


def test_valid_nested_conflict_retains_alternative_support(
    editable_catalogue, cba_bundle
):
    from rwa_analysis.catalogue.load import load_catalogue

    def edit(members):
        pd = next(m for m in members if m["id"] == "cba.cr6.average_pd")
        support = pd["evidence_refs"]
        pd["measure_ref"] = None
        pd["attributes"] = [
            {
                "name": "weighting",
                "value": None,
                "status": "conflicting",
                "alternatives": [
                    {"value": value, "status": "provisional", "evidence_refs": support}
                    for value in ("synthetic_a", "synthetic_b")
                ],
            }
        ]

    edit_members(editable_catalogue, "mappings/cba-2025-06-30-v1.json", edit)
    cat = load_catalogue(editable_catalogue / "releases/cr6-v1.json")
    weighting = meaning(cat, cba_bundle, "average_pd").attribute("weighting")
    assert weighting.status == "conflicting"
    assert {a.value for a in weighting.alternatives} == {"synthetic_a", "synthetic_b"}
    assert all(a.evidence_refs for a in weighting.alternatives)
    assert weighting.evidence_refs  # Summary retains nested support too.
