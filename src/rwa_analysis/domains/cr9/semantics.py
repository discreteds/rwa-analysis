"""Retained CR9 address adapter: no inferred date from partial field descriptors."""

from rwa_analysis.catalogue.occurrences import resolve_occurrence
from rwa_analysis.catalogue.resolve import field_occurrence


def resolve_field(catalogue, dataset, row, field_key):
    return resolve_occurrence(catalogue, field_occurrence(dataset, row, field_key))
