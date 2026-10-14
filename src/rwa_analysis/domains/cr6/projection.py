"""CR6 is a named view of already interpreted source cells."""

from rwa_analysis.domains.source_tables.projection import project

from .contracts import TABLES
from .models import FIELD_MAP, Cr6Output


def project_cr6(source_output, domain_bindings) -> Cr6Output:
    return Cr6Output(
        **project(source_output, domain_bindings, "cr6", FIELD_MAP, TABLES)
    )
