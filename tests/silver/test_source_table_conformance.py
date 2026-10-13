"""Composition stays occurrence-scoped while reusing durable definitions."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

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
)


def synthetic_catalogue(bundle):
    """Independently specified composition exercise, not a financial interpretation."""
    revision = {
        "created_on": date(2026, 10, 12),
        "effective_from": None,
        "effective_to": None,
    }
    quantity = ConceptRevision(
        id="test-quantity",
        revision_id="test-quantity@1",
        name="Synthetic quantity",
        definition="Synthetic only",
        category="quantity",
        **revision,
    )
    unit = ConceptRevision(
        id="test-unit",
        revision_id="test-unit@1",
        name="Synthetic unit",
        definition="Synthetic only",
        category="unit",
        **revision,
    )
    measure = MeasureRevision(
        id="test-measure",
        revision_id="test-measure@1",
        concept_ref=RevisionRef("concept", quantity.revision_id),
        result_unit_ref=RevisionRef("concept", unit.revision_id),
        attributes=(
            SemanticAttribute(
                name="weighting", value="synthetic base", status="established"
            ),
        ),
        **revision,
    )
    mappings = []
    for table in bundle.datasets[:2]:
        scope = MappingScope(
            bundle.document.document_id,
            bundle.document.document_reporting_date,
            table.id,
            table.metadata.context.source_template,
            "Residential mortgage",
            field_key="average_ead",
        )
        evidence = EvidenceRef(
            bundle.bundle_key,
            bundle.document.document_id,
            table.id,
            "field",
            "average_ead",
        )
        mappings.append(
            SourceMappingRevision(
                id=table.id,
                revision_id=table.id + "@1",
                scope=scope,
                measure_ref=RevisionRef("measure", measure.revision_id),
                evidence_refs=(evidence,),
                **revision,
            )
        )
    members = (quantity, unit, measure, *mappings)
    kinds = ("concept", "concept", "measure", "mapping", "mapping")
    return CatalogueRelease(
        "synthetic",
        "cr6-v1",
        date(2026, 10, 12),
        tuple(
            MemberSelection("synthetic", k, m.revision_id)
            for k, m in zip(kinds, members, strict=True)
        ),
        members,
    )


def test_shared_definition_and_narrow_override_preserve_occurrences(cba_2024_bundle):
    from rwa_analysis.domains.source_tables.semantics import resolve_cell

    bundle = cba_2024_bundle
    cat = synthetic_catalogue(bundle)
    tables = bundle.datasets[:2]
    cells = [next(c for c in t.cells if c.id == "average_ead/band-0") for t in tables]
    meanings = [
        resolve_cell(cat, bundle, t, c) for t, c in zip(tables, cells, strict=True)
    ]
    assert all(
        m.measure_ref == RevisionRef("measure", "test-measure@1") for m in meanings
    )
    assert meanings[0].mapping_refs != meanings[1].mapping_refs
    assert meanings[0].attribute("measure").evidence_refs[0].dataset_id == tables[0].id
    base = cat.members[3]
    override = replace(
        base,
        id="override",
        revision_id="override@1",
        measure_ref=None,
        scope=replace(base.scope, record_id=cells[0].id),
        overrides_refs=(RevisionRef("mapping", base.revision_id),),
        attributes=(
            SemanticAttribute(
                name="weighting", value="synthetic local", status="established"
            ),
        ),
    )
    cat = replace(
        cat,
        selection=(
            *cat.selection,
            MemberSelection("synthetic", "mapping", override.revision_id),
        ),
        members=(*cat.members, override),
    )
    assert (
        resolve_cell(cat, bundle, tables[0], cells[0]).attribute("weighting").value
        == "synthetic local"
    )
    assert (
        resolve_cell(cat, bundle, tables[1], cells[1]).attribute("weighting").value
        == "synthetic base"
    )


def test_conflict_and_restricted_time_do_not_remove_source(cba_2024_bundle):
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
    from rwa_analysis.storage.bronze import BronzeRef, LoadedBronze

    bundle = cba_2024_bundle
    cat = synthetic_catalogue(bundle)
    base = cat.members[3]
    conflicting = replace(
        base,
        id="conflicting",
        revision_id="conflicting@1",
        measure_ref=None,
        attributes=(
            SemanticAttribute(
                name="weighting", value="other weighting", status="established"
            ),
        ),
    )
    restricted = replace(
        base,
        id="restricted",
        revision_id="restricted@1",
        effective_from=date(2020, 1, 1),
        scope=replace(
            base.scope,
            dataset_id=bundle.datasets[3].id,
            template=bundle.datasets[3].metadata.context.source_template,
            field_key="actual_pd",
        ),
    )
    cat = replace(
        cat,
        members=(*cat.members, conflicting, restricted),
        selection=(
            *cat.selection,
            *(
                MemberSelection("synthetic", "mapping", m.revision_id)
                for m in (conflicting, restricted)
            ),
        ),
    )
    loaded = LoadedBronze(BronzeRef(bundle.bundle_key, "synthetic"), bundle)
    result = SourceTablePipeline().conform((loaded,), cat)
    import mountainash as ma

    attrs = result.attributes.filter(
        (ma.col("name") == "weighting") & (ma.col("status") == "conflicting")
    )
    assert attrs.count_rows() == 8
    assert result.cells.count_rows() == 131
    pd = result.meanings.filter(ma.col("field_id") == "actual_pd").to_dicts()[0]
    assert pd["measure_revision_ref"] is None
    assert result.cells.filter(ma.col("field_id") == "actual_pd").item(
        "source_number"
    ) == Decimal("0.56")
