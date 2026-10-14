"""Interpretation owner: explicit targets, contributions and role-specific time."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from rwa_analysis.catalogue import occurrences as resolve
from rwa_analysis.catalogue.models import (
    CatalogueRelease,
    MemberSelection,
    RevisionRef,
    SemanticAttribute,
    SourceMappingRevision,
    UnitConversion,
)
from rwa_analysis.extraction.definitions import (
    CapturedBundle,
    CaptureSnapshot,
    ContextDefinition,
    OccurrenceBinding,
    OccurrenceRef,
)
from rwa_analysis.storage.bronze import BronzeRef, LoadedBronze


@pytest.mark.parametrize(
    "kind", ["table", "field", "row", "column", "header", "block", "cell", "comment"]
)
def test_occurrence_targets_compose_context_without_collapsing_kind_or_vintage(
    cba_2024_bundle, kind
):
    from rwa_analysis.catalogue.models import OccurrenceScope

    old = cba_2024_bundle
    target = OccurrenceRef(
        old.bundle_key, None if kind == "comment" else old.datasets[0].id, kind, "same"
    )
    other = replace(target, kind="column" if kind != "column" else "field")
    vintage = replace(target, bundle_key="au/cba/2023-06-30/aps330")
    contexts = (
        ContextDefinition(
            "entity@1",
            (
                SemanticAttribute("A", "established", name="reporting_entity"),
                SemanticAttribute("AUD", "established", name="currency"),
            ),
        ),
    )
    snapshot = CaptureSnapshot(
        "capture@1",
        (),
        contexts,
        tuple(
            OccurrenceBinding(r, context_refs=("entity@1",))
            for r in (target, other, vintage)
        ),
    )
    bundle = CapturedBundle(
        old.document, old.bundle_key, old.extractor_path, old.datasets, snapshot
    )
    mapping = SourceMappingRevision(
        id="refinement",
        revision_id="refinement@1",
        created_on=date(2026, 10, 13),
        effective_from=None,
        effective_to=None,
        scope=OccurrenceScope((target,)),
        attributes=(SemanticAttribute("B", "provisional", name="reporting_entity"),),
    )

    def run(m):
        cat = CatalogueRelease(
            "test",
            "cr6-v1",
            date(2026, 10, 13),
            (MemberSelection("test.json", "mapping", m.revision_id),),
            (m,),
        )
        return resolve.resolve_capture(
            LoadedBronze(BronzeRef(old.bundle_key, "proof"), bundle), cat
        ).meanings

    values = run(mapping)
    assert values[target].attribute("reporting_entity").status == "conflicting"
    assert values[other].attribute("reporting_entity").value == "A"
    assert values[vintage].attribute("reporting_entity").value == "A"
    values = run(replace(mapping, overrides_refs=(RevisionRef("context", "entity@1"),)))
    assert values[target].attribute("reporting_entity").value == "B"
    assert values[target].attribute("reporting_entity").status == "provisional"
    assert values[target].attribute("currency").value == "AUD"
    assert RevisionRef("context", "entity@1") in values[target].mapping_refs


def test_missing_measurement_role_does_not_block_independent_conversion(
    cba_2024_bundle,
):
    from rwa_analysis.catalogue.models import OccurrenceScope

    old = cba_2024_bundle
    table = old.datasets[0]
    field = next(f for f in table.metadata.published_fields if f.source_unit == "%")
    cell = next(c for c in table.cells if c.field_ref == field.id)
    target = OccurrenceRef(old.bundle_key, table.id, "cell", cell.id)
    snapshot = CaptureSnapshot(
        "capture@1",
        (),
        (),
        (
            OccurrenceBinding(
                target, definition_refs=(RevisionRef("mapping", "dated@1"),)
            ),
        ),
    )
    bundle = CapturedBundle(
        old.document, old.bundle_key, old.extractor_path, (table,), snapshot
    )
    common = {
        "created_on": date(2026, 10, 13),
        "effective_from": None,
        "effective_to": None,
        "scope": OccurrenceScope((target,)),
    }
    conversion = SourceMappingRevision(
        id="conversion",
        revision_id="conversion@1",
        conversion=UnitConversion("%", Decimal(1), Decimal("0.01")),
        **common,
    )
    dated = replace(
        conversion,
        id="dated",
        revision_id="dated@1",
        conversion=None,
        effective_from=date(2024, 1, 1),
        attributes=(SemanticAttribute("restricted", "established", name="loss_basis"),),
    )
    cat = CatalogueRelease(
        "test",
        "cr6-v1",
        date(2026, 10, 13),
        tuple(
            MemberSelection("test", "mapping", m.revision_id)
            for m in (conversion, dated)
        ),
        (conversion, dated),
    )
    meaning = resolve.resolve_capture(
        LoadedBronze(BronzeRef(old.bundle_key, "proof"), bundle), cat
    ).meanings[target]
    assert meaning.unit_factor == Decimal("0.01")
    assert meaning.attribute("loss_basis").status == "unresolved"


def test_role_specific_definition_selection_and_whole_mapping_supersession(
    cba_2024_bundle,
):
    from rwa_analysis.catalogue.models import ConceptRevision, OccurrenceScope
    from rwa_analysis.extraction.definitions import TemporalRole
    from rwa_analysis.extraction.temporal import TemporalDescriptor

    old = cba_2024_bundle
    target = OccurrenceRef(old.bundle_key, None, "comment", "dated-note")
    concept = ConceptRevision(
        id="role",
        revision_id="role@1",
        created_on=date(2026, 10, 13),
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
        name="Role",
        definition="Synthetic role-specific contract",
        category="role",
    )
    context = ContextDefinition(
        "time@1",
        temporal=(
            TemporalDescriptor(
                "anchor", "2024-06-30", point="2024-06-30", point_status="established"
            ),
        ),
    )
    binding = OccurrenceBinding(
        target, temporal_roles=(TemporalRole("cohort_anchor", "time@1", "anchor"),)
    )
    snapshot = CaptureSnapshot("capture@1", (), (context,), (binding,))
    bundle = CapturedBundle(
        old.document, old.bundle_key, old.extractor_path, (), snapshot
    )
    common = {
        "created_on": date(2026, 10, 13),
        "effective_from": None,
        "effective_to": None,
        "scope": OccurrenceScope((target,), temporal_role="cohort_anchor"),
    }
    base = SourceMappingRevision(
        id="base",
        revision_id="base@1",
        concept_ref=RevisionRef("concept", "role@1"),
        attributes=(SemanticAttribute("discard", "established", name="currency"),),
        **common,
    )
    replacement = SourceMappingRevision(
        id="new",
        revision_id="new@1",
        concept_ref=RevisionRef("concept", "role@1"),
        supersedes_refs=(RevisionRef("mapping", "base@1"),),
        **common,
    )
    members = (concept, base, replacement)
    cat = CatalogueRelease(
        "test",
        "cr6-v1",
        date(2026, 10, 13),
        tuple(
            MemberSelection(
                "test", "concept" if m is concept else "mapping", m.revision_id
            )
            for m in members
        ),
        members,
    )
    loaded = LoadedBronze(BronzeRef(old.bundle_key, "proof"), bundle)
    meaning = resolve.resolve_capture(loaded, cat).meanings[target]
    assert meaning.concept_ref == RevisionRef("concept", "role@1")
    assert meaning.attribute("currency").status == "unresolved"
    assert meaning.mapping_refs == (RevisionRef("mapping", "new@1"),)
    conflict = replace(
        context,
        revision_id="other@1",
        temporal=(replace(context.temporal[0], point="2023-06-30"),),
    )
    binding = replace(
        binding,
        temporal_roles=binding.temporal_roles
        + (TemporalRole("cohort_anchor", "other@1", "anchor"),),
    )
    ambiguous = replace(
        bundle,
        snapshot=replace(
            snapshot, contexts=(context, conflict), occurrences=(binding,)
        ),
    )
    assert (
        resolve.resolve_capture(replace(loaded, bundle=ambiguous), cat)
        .meanings[target]
        .concept_ref
        is None
    )


def test_selected_definition_contents_resolve_without_authoring_catalogue(
    cba_2024_bundle,
):
    from rwa_analysis.catalogue.models import ConceptRevision

    old = cba_2024_bundle
    target = OccurrenceRef(old.bundle_key, None, "header", "population")
    concept = ConceptRevision(
        id="population",
        revision_id="population@1",
        created_on=date(2026, 10, 13),
        effective_from=None,
        effective_to=None,
        name="Population",
        definition="Retained definition",
        category="population",
    )
    snapshot = CaptureSnapshot(
        "capture@1",
        (),
        (),
        (
            OccurrenceBinding(
                target, definition_refs=(RevisionRef("concept", "population@1"),)
            ),
        ),
        semantic_definitions=(concept,),
    )
    bundle = CapturedBundle(
        old.document, old.bundle_key, old.extractor_path, (), snapshot
    )
    cat = CatalogueRelease("empty", "cr6-v1", date(2026, 10, 13), (), ())
    meaning = resolve.resolve_capture(
        LoadedBronze(BronzeRef(old.bundle_key, "proof"), bundle), cat
    ).meanings[target]
    assert meaning.concept_ref == RevisionRef("concept", "population@1")


@pytest.mark.parametrize(
    "point,expected", [("2023-06-30", "selected"), ("2023-06", None), (None, None)]
)
def test_retained_v3_uses_measurement_not_report_date(cba_2024_bundle, point, expected):
    from rwa_analysis.catalogue.models import MappingScope
    from rwa_analysis.extraction.source_tables import CellTemporalBinding
    from rwa_analysis.extraction.temporal import TemporalDescriptor

    table = cba_2024_bundle.datasets[0]
    cell = table.cells[0]
    table = replace(
        table,
        metadata=replace(
            table.metadata,
            temporal_descriptors=(
                TemporalDescriptor(
                    "measurement",
                    "Source period",
                    point=point,
                    point_status="established" if point else "unresolved",
                ),
            ),
            temporal_bindings=(
                CellTemporalBinding(cell.id, "measurement", "measurement"),
            ),
        ),
    )
    bundle = replace(cba_2024_bundle, datasets=(table,))
    mapping = SourceMappingRevision(
        id="dated",
        revision_id="dated@1",
        created_on=date(2026, 10, 14),
        effective_from=date(2023, 6, 30),
        effective_to=date(2023, 6, 30),
        scope=MappingScope(
            document_id=bundle.document.document_id,
            document_date=None,
            template=None,
            portfolio=None,
            dataset_id=table.id,
            record_id=cell.id,
        ),
        attributes=(SemanticAttribute("selected", "established", name="loss_basis"),),
    )
    catalogue = CatalogueRelease(
        "dated",
        "cr6-v1",
        date(2026, 10, 14),
        (MemberSelection("test", "mapping", "dated@1"),),
        (mapping,),
    )
    meaning = resolve.resolve_capture(
        LoadedBronze(BronzeRef(bundle.bundle_key, "retained-v3"), bundle), catalogue
    ).meanings[OccurrenceRef(bundle.bundle_key, table.id, "cell", cell.id)]
    assert meaning.attribute("loss_basis").value == expected
    assert bundle.schema_version == "disclosure-v3"
