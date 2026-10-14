"""Retained source-cell adapter to the shared interpretation owner."""

from rwa_analysis.catalogue.occurrences import (
    resolve_occurrence,
    source_date,
    source_occurrence,
)


def resolve_cell(catalogue, bundle, table, cell):
    return resolve_occurrence(
        catalogue,
        source_occurrence(bundle, table, cell),
        point_for=lambda role: source_date(table, cell, role),
    )
