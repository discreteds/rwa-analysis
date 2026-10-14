"""Independently callable CR9 view of shared source conformance."""

from rwa_analysis.domains.source_tables.legacy import domain_bindings
from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline

from .projection import project_cr9


class Cr9Pipeline:
    def conform(self, inputs, catalogue):
        return project_cr9(
            SourceTablePipeline().conform(inputs, catalogue),
            tuple(b for loaded in inputs for b in domain_bindings(loaded.bundle)),
        )
