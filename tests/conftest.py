"""Retained wire inputs and live extraction helpers; never generated expectations."""

import json
import shutil
from pathlib import Path

import pytest

from rwa_analysis.extraction.runner import run_extractor


@pytest.fixture
def legacy_payload():
    """Independently authored synthetic cr6-v1 wire; never a live extractor."""
    reference = {
        "document_id": "legacy",
        "pdf_page": 1,
        "printed_page": "1",
        "location": "Synthetic transport fixture",
        "row": None,
        "column": None,
    }
    knowledge = {"value": None, "status": "unresolved", "qualification_refs": []}
    names = (
        "on_balance_exposure",
        "off_balance_exposure",
        "average_ccf",
        "ead",
        "average_pd",
        "reported_borrower_count",
        "average_lgd",
        "average_maturity",
        "rwa",
        "rwa_density",
        "regulatory_expected_loss",
        "provisions",
    )
    rows = ["band-1", "band-2"]

    def axis(id, kind):
        return {
            "id": id,
            "axis": kind,
            "source_label": id,
            "order": 0,
            "header_path_refs": [],
            "context_refs": ["context"],
            "qualification_refs": [],
            "source_reference": reference.copy(),
        }

    records = []
    for row in rows:
        record = {
            "record_id": row,
            "source_row_ref": row,
            "source_row_role": "band",
            "source_segment_memberships": [],
            "source_aggregation_scope": ["block"],
        }
        for name in names:
            record[name] = {
                "value": None
                if name == "average_maturity"
                else 10
                if name == "reported_borrower_count"
                else "10",
                "original_text": "" if name == "average_maturity" else "10",
                "displayed_precision": None if name == "average_maturity" else 0,
                "missing_reason": "blank_unresolved"
                if name == "average_maturity"
                else None,
                "source_reference": reference.copy(),
            }
        records.append(record)
    return {
        "document": {
            "document_id": "legacy",
            "local_path": "raw/legacy.pdf",
            "organisation_id": "legacy",
            "reporting_entity": "Synthetic",
            "title": "Synthetic old-wire case",
            "document_reporting_date": "2025-06-30",
            "publication_date": None,
            "reporting_jurisdiction": "au",
            "source_url": "https://example.org/legacy.pdf",
        },
        "bundle_key": "au/legacy/2025-06-30/aps330",
        "extractor_path": "synthetic",
        "schema_version": "cr6-v1",
        "datasets": [
            {
                "id": "cr6",
                "context": dict(
                    id="context",
                    document_date="2025-06-30",
                    observation_date="2025-06-30",
                    source_date_label="30 June 2025",
                    source_template="CR6",
                    source_title="Synthetic",
                    source_portfolio_label="Mortgages",
                    **{
                        k: knowledge.copy()
                        for k in (
                            "reporting_entity",
                            "consolidation_scope",
                            "regulatory_scope",
                            "geography",
                            "currency",
                        )
                    },
                    qualification_refs=[],
                    evidence=[reference.copy()],
                ),
                "axes": [
                    axis("block", "block"),
                    *[axis(row, "row") for row in rows],
                    *[axis(name, "column") for name in names],
                ],
                "published_fields": [
                    {
                        "id": name,
                        "source_label": name,
                        "header_path_refs": [name],
                        "source_unit": "",
                        "source_scale": "1",
                        "qualification_refs": [],
                        "attributes": [],
                        "source_reference": reference.copy(),
                    }
                    for name in names
                ],
                "bindings": [
                    {
                        "id": name,
                        "typed_field_name": name,
                        "published_field_ref": name,
                        "row_refs": rows.copy(),
                        "column_refs": [name],
                        "context_refs": ["context"],
                        "qualification_refs": [],
                    }
                    for name in names
                ],
                "segmentations": [],
                "qualifications": [
                    {
                        "id": "note",
                        "source_text": "Synthetic",
                        "evidence": [reference.copy()],
                        "scope": [{"kind": "dataset", "id": "cr6"}],
                    }
                ],
                "relationships": [
                    {
                        "id": "subset",
                        "kind": "subset",
                        "source_label": "Synthetic",
                        "parent": {"kind": "row", "id": "band-1"},
                        "children": [{"kind": "row", "id": "band-2"}],
                        "scope": [],
                        "exhaustive": None,
                        "mutually_exclusive": None,
                        "evidence": [reference.copy()],
                    }
                ],
                "records": records,
            }
        ],
    }


@pytest.fixture
def legacy_bundle(legacy_payload):
    from rwa_analysis.extraction.codec import decode_payload

    return decode_payload(legacy_payload)


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


def _retained(org, document_date, version="disclosure-v2"):
    """Baseline wire inputs retained before migration; PDF goldens are separate."""
    from rwa_analysis.extraction.codec import decode_payload

    path = (
        Path(__file__).parent
        / "fixtures/retained"
        / f"{org}-{document_date}-{version}.json"
    )
    return decode_payload(json.loads(path.read_text()))


@pytest.fixture(scope="session")
def cba_bundle():
    return _retained("cba", "2025-06-30")


@pytest.fixture(scope="session")
def cba_2024_bundle():
    return _retained("cba", "2024-06-30", "disclosure-v3")


@pytest.fixture(scope="session")
def westpac_bundle():
    return _retained("westpac", "2025-09-30")


@pytest.fixture(scope="session")
def nab_bundle():
    return _retained("nab", "2025-09-30")


@pytest.fixture(scope="session")
def anz_bundle():
    return _retained("anz", "2025-09-30")


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
def published_banks(retained, monkeypatch):
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
                release_path="catalogue/releases/cr6-cr9-v1.json",
                evidence_refs=tuple(r for r in refs if r != ref),
            ),
        )
        publications.append((session, session.publish(candidate, revision="r1")))
    return publications
