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
    # p.55 places both external-rating columns before the numeric PD columns.
    columns = sorted(
        (a for a in meta.axes if a.axis == "column"), key=lambda a: a.order
    )
    assert [a.id for a in columns] == [
        "rating-0",
        "rating-1",
        "column-weighted_average_pd",
        "column-arithmetic_average_pd",
        "column-previous_year_borrower_count",
        "column-current_year_borrower_count",
        "column-defaulted_borrower_count",
        "column-new_defaulted_borrower_count",
        "column-historical_annual_default_rate",
    ]
    assert [a.order for a in columns] == list(range(9))
    original_axes = {a.id: a for a in original.metadata.axes}
    assert tuple(replace(a, order=original_axes[a.id].order) for a in meta.axes) == (
        original.metadata.axes
    )
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


@pytest.mark.parametrize("index", [0, 1])
def test_legacy_row_metadata_reaches_flat_cells_and_ordered_scope_references(
    westpac_bundle, catalogue, index
):
    from rwa_analysis.domains.source_tables.contracts import DECLARATIONS
    from rwa_analysis.domains.source_tables.metadata import source_rows
    from rwa_analysis.storage.bronze import BronzeRef, LoadedBronze

    dataset = westpac_bundle.datasets[index]
    table, meanings = adapt(dataset, catalogue)
    records = dataset.exposure_rows if index == 0 else dataset.backtesting_rows
    by_row = {r.source_row_ref: r for r in records}
    for cell in table.cells:
        assert cell.source_row_role == by_row[cell.row_ref].source_row_role
        assert cell.source_aggregation_scope == ("mortgage-block",)
    rows = {name: [] for name in DECLARATIONS}
    loaded = LoadedBronze(BronzeRef(westpac_bundle.bundle_key, "test"), westpac_bundle)
    source_rows(rows, loaded, table, meanings, catalogue)
    for cell in rows["cells"]:
        assert cell.source_row_role == by_row[cell.row_ref].source_row_role
    scopes = [
        r
        for r in rows["references"]
        if r.owner_kind == "cell" and r.member == "source_aggregation_scope"
    ]
    assert {(r.owner_id, r.position, r.target_kind, r.target_id) for r in scopes} == {
        (cell.id, 0, "block", "mortgage-block") for cell in table.cells
    }
    if index == 0:
        assert {c.source_row_role for c in rows["cells"]} == {
            "band",
            "Total Residential Mortgages",
        }


def test_native_source_constructors_and_metadata_keep_optional_legacy_defaults(
    cba_2024_bundle, catalogue
):
    from rwa_analysis.domains.source_tables.contracts import DECLARATIONS
    from rwa_analysis.domains.source_tables.metadata import source_rows
    from rwa_analysis.domains.source_tables.semantics import resolve_cell
    from rwa_analysis.storage.bronze import BronzeRef, LoadedBronze

    table = cba_2024_bundle.datasets[0]
    assert table.cells
    assert all(
        c.source_row_role is None and c.source_aggregation_scope == ()
        for c in table.cells
    )
    meanings = {
        c.id: resolve_cell(catalogue, cba_2024_bundle, table, c) for c in table.cells
    }
    rows = {name: [] for name in DECLARATIONS}
    loaded = LoadedBronze(
        BronzeRef(cba_2024_bundle.bundle_key, "test"), cba_2024_bundle
    )
    source_rows(rows, loaded, table, meanings, catalogue)
    assert all(c.source_row_role is None for c in rows["cells"])
    assert not any(r.member == "source_aggregation_scope" for r in rows["references"])
