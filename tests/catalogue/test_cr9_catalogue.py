"""CR9 occurrence applicability without synthetic observation-date fallback.

These cases catch restricted meanings leaking through explicit occurrence scope
and supported conversion being lost when financial meaning remains partial.
"""

from dataclasses import fields, is_dataclass, replace
from datetime import date
from decimal import Decimal

import pytest

from rwa_analysis.catalogue.models import (
    CatalogueRelease,
    ConceptRevision,
    EvidenceRef,
    MappingScope,
    MeasureRevision,
    MemberSelection,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    UnitConversion,
)


@pytest.fixture
def source(westpac_bundle):
    return next(
        ds for ds in westpac_bundle.datasets if ds.id == "cr9-residential-mortgages"
    )


def scope(**changes):
    return MappingScope(
        document_id="westpac-2025-09-30-aps330",
        document_date=date(2025, 9, 30),
        dataset_id="cr9-residential-mortgages",
        template="CR9",
        portfolio="Residential\nMortgages",
        **changes,
    )


def catalogue(
    *, mapping_changes=None, definition_changes=None, dependency_changes=None
):
    common = {
        "created_on": date(2026, 10, 12),
        "effective_from": None,
        "effective_to": None,
    }
    concept = ConceptRevision(
        id="pd",
        revision_id="pd@v1",
        name="PD",
        definition="Probability of default",
        category="quantity",
        **common,
    )
    unit = ConceptRevision(
        id="ratio",
        revision_id="ratio@v1",
        name="Ratio",
        definition="Fractional rate",
        category="unit",
        **common,
    )
    measure = MeasureRevision(
        id="pd-measure",
        revision_id="pd-measure@v1",
        concept_ref=RevisionRef("concept", "pd@v1"),
        result_unit_ref=RevisionRef("concept", "ratio@v1"),
        attributes=(
            SemanticAttribute(name="weighting", value="ead", status="established"),
        ),
        **(common | (definition_changes or {})),
    )
    unit = replace(unit, **(dependency_changes or {}))
    mapping = SourceMappingRevision(
        id="mapping",
        revision_id="mapping@v1",
        scope=scope(field_key="weighted_average_pd"),
        concept_ref=RevisionRef("concept", "pd@v1"),
        measure_ref=RevisionRef("measure", "pd-measure@v1"),
        conversion=UnitConversion("%", Decimal(1), Decimal("0.01")),
        **common,
    )
    mapping = replace(mapping, **(mapping_changes or {}))
    members = (concept, unit, measure, mapping)
    return CatalogueRelease(
        "synthetic",
        "cr6-v1",
        date(2026, 10, 12),
        tuple(
            MemberSelection("unused", kind, member.revision_id)
            for kind, member in zip(
                ("concept", "concept", "measure", "mapping"), members
            )
        ),
        members,
    )


@pytest.mark.parametrize(
    "bounds,narrows",
    [
        ({}, False),
        ({"observation_from": date(2024, 1, 1)}, True),
        ({"observation_to": date(2025, 1, 1)}, True),
        (
            {"observation_from": date(2024, 1, 1), "observation_to": date(2025, 1, 1)},
            True,
        ),
    ],
)
def test_optional_bounds_contain_only_narrower_scopes(bounds, narrows):
    broad, narrow = scope(), scope(**bounds)
    assert narrow.narrows(broad) is narrows
    assert not broad.narrows(narrow)


@pytest.mark.parametrize(
    "restriction",
    [None, "effective_from", "effective_to", "observation_from", "observation_to"],
)
def test_mapping_restrictions_do_not_use_document_date(source, restriction):
    from rwa_analysis.domains.cr9.semantics import resolve_field

    changes = {}
    if restriction:
        if restriction.startswith("observation"):
            changes["scope"] = scope(
                field_key="weighted_average_pd", **{restriction: date(2025, 9, 30)}
            )
        else:
            changes[restriction] = date(2025, 9, 30)
    result = resolve_field(
        catalogue(mapping_changes=changes),
        source,
        source.backtesting_rows[0],
        "weighted_average_pd",
    )
    assert result.unit_factor == (None if restriction else Decimal("0.01"))
    assert bool(result.mapping_refs) is (restriction is None)


@pytest.mark.parametrize("owner", ["definition_changes", "dependency_changes"])
@pytest.mark.parametrize("bound", ["effective_from", "effective_to"])
def test_restricted_definition_leaves_concept_and_conversion_known(
    source, owner, bound
):
    from rwa_analysis.domains.cr9.semantics import resolve_field

    result = resolve_field(
        catalogue(**{owner: {bound: date(2025, 9, 30)}}),
        source,
        source.backtesting_rows[0],
        "weighted_average_pd",
    )
    assert result.measure_ref is None
    assert result.concept_ref == RevisionRef("concept", "pd@v1")
    assert result.attribute("weighting").status == "unresolved"
    assert result.unit_factor == Decimal("0.01")


@pytest.mark.parametrize(
    "changed", ["document_id", "dataset_id", "field_key", "portfolio"]
)
def test_explicit_occurrence_scope_is_conjunctive(source, changed):
    from rwa_analysis.domains.cr9.semantics import resolve_field

    cat = catalogue(
        mapping_changes={
            "scope": replace(
                scope(field_key="weighted_average_pd"), **{changed: "other"}
            )
        }
    )
    result = resolve_field(
        cat, source, source.backtesting_rows[0], "weighted_average_pd"
    )
    assert result.mapping_refs == ()
    assert result.unit_factor is None


def test_westpac_reviewed_meanings_and_cr6_release_preservation(
    project_root, westpac_bundle
):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.domains.cr9.semantics import resolve_field

    old = load_catalogue(project_root / "catalogue/releases/cr6-v1.json")
    cat = load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json")
    for selected, member in zip(old.selection, old.members):
        assert cat.member(RevisionRef(selected.kind, selected.revision_id)) == member
    # Source header/note facts independently read from Westpac pp.55–56.
    keys = (
        "weighted_average_pd",
        "arithmetic_average_pd",
        "historical_annual_default_rate",
        "previous_year_borrower_count",
        "current_year_borrower_count",
        "defaulted_borrower_count",
        "new_defaulted_borrower_count",
    )
    source = next(
        ds for ds in westpac_bundle.datasets if ds.id == "cr9-residential-mortgages"
    )
    row = source.backtesting_rows[0]
    meanings = {key: resolve_field(cat, source, row, key) for key in keys}
    pd = meanings["weighted_average_pd"]
    assert pd.concept_ref == RevisionRef("concept", "risk.default-probability@v1")
    assert pd.attribute("weighting").value == "ead_weighted"
    assert pd.attribute("weight_measure").value is not None
    assert pd.attribute("weight_timing").value == "June 2024"
    assert (
        meanings["arithmetic_average_pd"].attribute("weighting").value
        == "arithmetic_by_borrowers"
    )
    history = meanings["historical_annual_default_rate"]
    assert history.concept_ref != pd.concept_ref
    assert history.attribute("aggregation").value == "historical_average_over_10_years"
    assert history.attribute("denominator").status == "unresolved"
    annual = meanings["defaulted_borrower_count"]
    new = meanings["new_defaulted_borrower_count"]
    assert "new borrowers" in annual.attribute("cohort_eligibility").value
    assert new.measure_ref != annual.measure_ref
    assert "not funded in June 2024" in new.attribute("cohort_eligibility").value
    for key, meaning in meanings.items():
        assert meaning.measure_ref is not None
        assert meaning.unit_factor == (
            Decimal("0.01") if key in keys[:3] else Decimal(1)
        )
        assert meaning.attribute("counted_entity").status == "unresolved"
        assert meaning.attribute("concept").evidence_refs

    # New catalogue support must bind to retained source evidence, including the
    # notes on p.56 rather than merely the numeric cells on p.55.
    def evidence_refs(value):
        if isinstance(value, EvidenceRef):
            yield value
        elif is_dataclass(value):
            for field in fields(value):
                yield from evidence_refs(getattr(value, field.name))
        elif isinstance(value, tuple):
            for item in value:
                yield from evidence_refs(item)

    retained = {
        "field": {f.id for f in source.metadata.published_fields},
        "qualification": {q.id for q in source.metadata.qualifications},
        "context": {source.metadata.context.id},
        "band": {b.id for s in source.metadata.segmentations for b in s.bands},
    }
    for member in cat.members:
        for support in evidence_refs(member):
            if support.dataset_id == source.id:
                assert support.document_id == westpac_bundle.document.document_id
                assert support.ref_id in retained[support.kind]
