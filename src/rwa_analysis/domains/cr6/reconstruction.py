"""Reconstruct CR6 numeric frames for retained and declared domain bindings."""

from rwa_analysis.domains.source_tables.domain_reconstruction import reconstruct_domain

from .models import FIELD_MAP


def reconstruct_cr6(output, bundles):
    return reconstruct_domain(
        output, bundles, "cr6", FIELD_MAP, {"reported_borrower_count"}
    )
