"""Reconstruct CR9 numeric frames for retained and declared domain bindings."""

from rwa_analysis.domains.source_tables.domain_reconstruction import reconstruct_domain

from .models import COUNTS, MEASURES


def reconstruct_cr9(output, bundles):
    return reconstruct_domain(output, bundles, "cr9", {n: n for n in MEASURES}, COUNTS)
