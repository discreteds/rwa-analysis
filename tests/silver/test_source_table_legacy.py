"""Adapter owns translation loss; PDF goldens own the source transcription."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import SourceMappingRevision
from rwa_analysis.catalogue.resolve import resolve_field as resolve_cr6
from rwa_analysis.domains.cr9.semantics import resolve_field as resolve_cr9


@pytest.fixture
def catalogue(project_root):
    return load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json")


def adapt(dataset, catalogue):
    from rwa_analysis.domains.source_tables.legacy import adapt_legacy

    return adapt_legacy(dataset, catalogue)


def test_cr9_adapter_preserves_lexical_numeric_and_blank_positions(
    westpac_bundle, catalogue
):
    table, meanings = adapt(westpac_bundle.datasets[1], catalogue)
    assert len(table.cells) == 72
    assert set(meanings) == {c.id for c in table.cells}
    ratings = [c for c in table.cells if c.value_kind == "text"]
    assert len(ratings) == 16
    assert sum(c.value.original_text == "N/A" for c in ratings) == 14
    assert all(c.value.value == "N/A" for c in ratings if c.value.original_text)
    assert all(
        c.value.missing_reason == "not_applicable"
        for c in ratings
        if c.value.original_text
    )
    assert sum(c.value.original_text == "" for c in table.cells) == 5
    count = next(
        c
        for c in table.cells
        if c.row_ref == "band-1" and c.field_ref == "previous_year_borrower_count"
    )
    assert type(count.value.value) is int
    assert count.value.value == 564613
    assert count.value.original_text == "564,613"
    dash = next(
        c
        for c in table.cells
        if c.row_ref == "band-7" and c.field_ref == "new_defaulted_borrower_count"
    )
    assert dash.value.original_text == "-"
    assert dash.value.missing_reason == "dash_unresolved"


def test_adapter_retains_paths_scopes_and_translates_field_endpoints_and_time(
    westpac_bundle, catalogue
):
    original = westpac_bundle.datasets[1]
    table, _ = adapt(original, catalogue)
    meta = table.metadata
    assert meta.axes == original.metadata.axes
    assert meta.qualifications == original.metadata.qualifications
    assert meta.segmentations == original.metadata.segmentations
    assert meta.temporal_descriptors == original.metadata.temporal_descriptors
    cells = {c.id: c for c in table.cells}
    assert len(meta.relationships) == 7
    for relation in meta.relationships:
        assert relation.parent.kind == "cell"
        assert relation.children[0].kind == "cell"
        parent, child = cells[relation.parent.id], cells[relation.children[0].id]
        assert parent.field_ref == "defaulted_borrower_count"
        assert child.field_ref == "new_defaulted_borrower_count"
        assert parent.row_ref == child.row_ref == relation.scope[0].id
        assert relation.exhaustive is False
        assert relation.mutually_exclusive is None
        assert len(relation.evidence) == 2
    assert len(meta.temporal_bindings) == 64
    translated = {
        (cells[b.cell_id].row_ref, cells[b.cell_id].field_ref, b.role, b.descriptor_ref)
        for b in meta.temporal_bindings
    }
    assert translated == {
        (b.record_id, b.field_key, b.role, b.descriptor_ref)
        for b in original.metadata.temporal_bindings
    }
    fields = {f.id: f for f in meta.published_fields}
    assert fields["previous_year_borrower_count"].header_path_refs == (
        "borrower-counts",
        "column-previous_year_borrower_count",
    )
    assert fields["rating-0"].header_path_refs == ("external-ratings", "rating-0")
    weighted = fields["weighted_average_pd"]
    assert weighted.attributes[0].value == "EAD"
    assert weighted.qualification_refs == (
        "pd-definition",
        "pd-long-run",
        "cr9-weighting",
    )
    default = next(
        c
        for c in table.cells
        if c.row_ref == "band-8" and c.field_ref == "weighted_average_pd"
    )
    assert "default-definition" in default.qualification_refs
    assert default.segment_refs == ("pd-band-8",)
    assert default.context_refs == ("context",)


@pytest.mark.parametrize("index,resolver", [(0, resolve_cr6), (1, resolve_cr9)])
def test_adapter_resolves_original_addresses_with_model_specific_date_policy(
    westpac_bundle, catalogue, index, resolver
):
    dataset = westpac_bundle.datasets[index]
    # Give CR6 a comparative snapshot; CR9 must not borrow the report date.
    # Pin mappings to the original record so adapted cell IDs cannot match them.
    if index == 0:
        dataset = replace(
            dataset,
            metadata=replace(
                dataset.metadata,
                context=replace(
                    dataset.metadata.context, observation_date=date(2024, 9, 30)
                ),
            ),
        )
    applicable = date(2024, 9, 30) if index == 0 else date(2025, 9, 30)
    rows = dataset.exposure_rows if index == 0 else dataset.backtesting_rows
    key = "ead" if index == 0 else "weighted_average_pd"
    catalogue = replace(
        catalogue,
        members=tuple(
            replace(
                m,
                effective_from=applicable,
                effective_to=applicable,
                scope=replace(
                    m.scope,
                    record_id=rows[0].record_id,
                    observation_from=applicable,
                    observation_to=applicable,
                ),
            )
            if isinstance(m, SourceMappingRevision) and m.scope.dataset_id == dataset.id
            else m
            for m in catalogue.members
        ),
    )
    expected = resolver(catalogue, dataset, rows[0], key)
    table, meanings = adapt(dataset, catalogue)
    cell = next(
        c
        for c in table.cells
        if c.row_ref == rows[0].source_row_ref and c.field_ref == key
    )
    assert meanings[cell.id] == expected
    if index == 0:
        assert expected.concept_ref.revision_id == "exposure.at-default@v1"
        assert expected.unit_factor == Decimal(1000000)
        assert len(table.cells) == 108
        assert table.metadata.relationships == dataset.metadata.relationships
        assert {b.role for b in table.metadata.temporal_bindings} == {"measurement"}
        assert len(table.metadata.temporal_bindings) == 108
        assert table.metadata.temporal_descriptors[-1].point == "2024-09-30"
        assert table.metadata.context.document_date == date(2025, 9, 30)
        assert (
            next(
                f for f in table.metadata.published_fields if f.id == "ead"
            ).result_kind
            == "money"
        )
    else:
        assert expected.measure_ref is None
        assert expected.mapping_refs == ()


def test_adapter_uses_bindings_not_optional_row_members(westpac_bundle, catalogue):
    original = westpac_bundle.datasets[1]
    selected = replace(
        original,
        metadata=replace(
            original.metadata,
            bindings=tuple(
                b
                for b in original.metadata.bindings
                if b.typed_field_name == "weighted_average_pd"
            ),
        ),
    )
    table, meanings = adapt(selected, catalogue)
    numeric = [c for c in table.cells if c.value_kind != "text"]
    assert len(numeric) == 8
    assert {c.field_ref for c in numeric} == {"weighted_average_pd"}
    assert {f.id for f in table.metadata.published_fields} == {
        "weighted_average_pd",
        "rating-0",
        "rating-1",
    }
    cell = next(c for c in numeric if c.row_ref == "band-1")
    assert meanings[cell.id] == resolve_cr9(
        catalogue, original, original.backtesting_rows[0], "weighted_average_pd"
    )
    assert meanings[cell.id].measure_ref is not None
    assert meanings[cell.id].unit_factor == Decimal("0.01")
