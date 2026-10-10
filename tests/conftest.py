"""Real extractor inputs shared by downstream boundary tests, never expectations."""

from pathlib import Path

import pytest

from rwa_analysis.extraction.runner import run_extractor


def _extract(org, document_date):
    root = Path(__file__).resolve().parents[1]
    pdf = root / f"raw/{org}-{document_date}-aps330.pdf"
    script = root / f"extractions/au/{org}/{document_date}/aps330/extract.py"
    for path in (pdf, script):
        if not path.is_file():
            pytest.fail(f"Required extraction prerequisite missing: {path}")
    return run_extractor(script, pdf)


@pytest.fixture(scope="session")
def cba_bundle():
    return _extract("cba", "2025-06-30")


@pytest.fixture(scope="session")
def westpac_bundle():
    return _extract("westpac", "2025-09-30")


@pytest.fixture(scope="session")
def nab_bundle():
    return _extract("nab", "2025-09-30")


@pytest.fixture(scope="session")
def anz_bundle():
    return _extract("anz", "2025-09-30")
