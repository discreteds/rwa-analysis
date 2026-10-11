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
    from rwa_analysis.storage.bronze import save_bronze

    root = tmp_path / "project"
    root.mkdir()
    shutil.copytree(project_root / "catalogue", root / "catalogue")
    for name in ("uv.lock", "pyproject.toml"):
        shutil.copyfile(project_root / name, root / name)

    refs = tuple(
        save_bronze(b, "v1", root)
        for b in (cba_bundle, westpac_bundle, nab_bundle, anz_bundle)
    )
    return root, refs


@pytest.fixture
def published_cr6(retained, project_root, monkeypatch):
    from rwa_analysis.storage.manifests import RebuildRequest, save_manifest
    from rwa_analysis.storage.silver import rebuild

    root, refs = retained
    # A research run needs data and the Python environment, not a Git executable.
    monkeypatch.setenv("PATH", "")
    (root / "raw").symlink_to(project_root / "raw", target_is_directory=True)
    path = save_manifest(
        RebuildRequest(
            revision_id="r1",
            bronze_refs=refs,
            catalogue_release_path="catalogue/releases/cr6-v1.json",
            conformance_schema_version="cr6-simple-v1",
        ),
        root,
    )
    warehouse = root / "warehouse.duckdb"
    rebuild(path, root, warehouse)
    return path, root, warehouse
