"""Real extractor inputs shared by downstream boundary tests, never expectations."""

import shutil
from pathlib import Path

import pytest

from rwa_analysis.extraction.runner import run_extractor


@pytest.fixture(scope="session")
def project_root():
    return next(
        path
        for path in Path(__file__).resolve().parents
        if (path / "pyproject.toml").is_file()
    )


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


@pytest.fixture
def retained(
    tmp_path, project_root, cba_bundle, westpac_bundle, nab_bundle, anz_bundle
):
    from rwa_analysis.storage.bronze import BronzeStore

    root = tmp_path / "project"
    root.mkdir()
    shutil.copytree(project_root / "catalogue", root / "catalogue")
    for name in ("uv.lock", "pyproject.toml"):
        shutil.copyfile(project_root / name, root / name)

    store = BronzeStore(root / "data/bronze")
    refs = tuple(
        store.save(b, "v1")
        for b in (cba_bundle, westpac_bundle, nab_bundle, anz_bundle)
    )
    return root, refs


@pytest.fixture
def published_cr6(retained, monkeypatch):
    from rwa_analysis.composition import build_session
    from rwa_analysis.settings import OrganisationSettings
    from rwa_analysis.storage.manifests import CatalogueSelection

    root, refs = retained
    # A research run needs data and the Python environment, not a Git executable.
    monkeypatch.setenv("PATH", "")
    publications = []
    for ref in refs:
        org = ref.bundle_key.split("/")[1]
        session = build_session(
            OrganisationSettings(
                project_root=root,
                organisation_id=org,
                staging_path=f"data/silver/staging/{org}.duckdb",
            )
        )
        candidate = session.conform(
            session.load_bronze((ref,)),
            catalogue=CatalogueSelection(
                release_path="catalogue/releases/cr6-v1.json",
                evidence_refs=tuple(r for r in refs if r != ref),
            ),
        )
        publications.append((session, session.publish(candidate, revision="r1")))
    return publications
