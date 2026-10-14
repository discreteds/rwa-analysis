"""CR9 is a named view of already interpreted source cells."""

from rwa_analysis.domains.source_tables.projection import project

from .contracts import TABLES
from .models import MEASURES, Cr9Output


def project_cr9(source_output, domain_bindings) -> Cr9Output:
    return Cr9Output(
        **project(
            source_output, domain_bindings, "cr9", {n: n for n in MEASURES}, TABLES
        )
    )
