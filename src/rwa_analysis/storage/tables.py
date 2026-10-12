"""Explicit associations for the two supported domains' declared Silver tables."""

from rwa_analysis.domains.cr6.contracts import TABLES as CR6_TABLES
from rwa_analysis.domains.cr6.models import Cr6Output
from rwa_analysis.domains.cr9.contracts import TABLES as CR9_TABLES
from rwa_analysis.domains.cr9.models import Cr9Output

DOMAINS = (
    ("cr6", Cr6Output, CR6_TABLES),
    ("cr9", Cr9Output, CR9_TABLES),
)
