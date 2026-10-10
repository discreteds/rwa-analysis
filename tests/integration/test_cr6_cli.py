"""CLI transport, committed provenance, and portable source-only recovery.

Owns failures that API lifecycle tests cannot catch: wrong bundle dispatch,
root-relative paths, lost inspection evidence, and incomplete recovery archives.
"""

import json
import shutil
import tarfile

import pytest
from typer.testing import CliRunner

from tests.integration.test_silver_rebuild import compare, git, read_snapshot


@pytest.fixture
def cli_root(tmp_path, project_root):
    root = tmp_path / "source"
    root.mkdir()
    for directory in ("src", "extractions", "catalogue", "config", "raw"):
        shutil.copytree(
            project_root / directory,
            root / directory,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(project_root / name, root / name)
    git(root, "init", "-q")
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-qm",
        "Retained inputs",
    )
    return root


def invoke(root, *args, ok=True):
    from rwa_analysis.cli import app

    result = CliRunner().invoke(app, [*args, "--project-root", str(root)])
    assert (result.exit_code == 0) is ok, result.output or repr(result.exception)
    return result.output


def test_cli_offline_inspection_and_archive_recovery(cli_root, tmp_path):
    root = cli_root
    request = json.loads((root / "config/rebuilds/cr6-2025-v1.json").read_text())
    for ref in request["bronze_refs"]:
        invoke(root, "extract", "--bundle", ref["bundle_key"], "--output-version", "v1")
    duplicate = invoke(
        root,
        "extract",
        "--bundle",
        request["bronze_refs"][0]["bundle_key"],
        "--output-version",
        "v1",
        ok=False,
    )
    assert "v1" in duplicate and "exists" in duplicate.lower()
    invoke(root, "manifest", "--request", "config/rebuilds/cr6-2025-v1.json")
    assert (
        "exists"
        in invoke(
            root, "manifest", "--request", "config/rebuilds/cr6-2025-v1.json", ok=False
        ).lower()
    )

    # Actual Git bundle plus input archive, without any database.
    git(root, "bundle", "create", str(tmp_path / "code.bundle"), "--all")
    archive = tmp_path / "inputs.tar.gz"
    with tarfile.open(archive, "x:gz") as tar:
        for name in (
            "raw",
            "data/bronze",
            "data/manifests",
            "catalogue",
            "config",
            "uv.lock",
        ):
            tar.add(root / name, arcname=name)
    shutil.rmtree(root / "raw")
    shutil.rmtree(root / "extractions")
    missing = invoke(
        root,
        "extract",
        "--bundle",
        request["bronze_refs"][0]["bundle_key"],
        "--output-version",
        "v2",
        ok=False,
    )
    assert "raw/cba-2025-06-30-aps330.pdf" in missing
    manifest = "data/manifests/cr6-2025-v1.json"
    invoke(root, "rebuild", "--manifest", manifest)
    first = read_snapshot(root / "data/warehouse.duckdb")
    assert len(first["observations"]) == 36
    assert first["publication"]["silver_revision_id"].to_list() == ["cr6-2025-v1"]
    reports = {}
    for ref in request["bronze_refs"]:
        key = ref["bundle_key"]
        reports[key.split("/")[1]] = json.loads(
            invoke(
                root,
                "inspect",
                "--observation",
                f"{key}/cr6-residential-mortgages/band-1",
            )
        )
    cba = reports["cba"]
    assert cba["observation"]["ead_amount"] == "281508000000.00000000"
    assert cba["observation"]["reported_entity_count"] == 742470
    ead = next(r for r in cba["lineage"] if r["field_key"] == "ead_amount")
    assert ead["original_text"] == "281,508"
    assert ead["source_reference"]["pdf_page"] == 55
    assert ead["output_version"] == "v1"
    assert cba["context"]["observation_date"] == "2025-06-30"
    for org, report in reports.items():
        assert len(report["interpretations"]) == len(report["lineage"]) == 12
        assert (
            report["applied_mappings"]
            and report["catalogue"]
            and report["source_evidence"]
        )
        if org != "cba":
            assert report["context"]["observation_date"] == "2025-09-30"

    def attribute(org, field, name):
        row = next(
            r for r in reports[org]["interpretations"] if r["field_key"] == field
        )
        return next(a for a in row["attributes"] if a["name"] == name)

    assert (
        attribute("nab", "reported_entity_count", "counted_entity")["value"]["text"]
        == "arrangement"
    )
    assert (
        attribute("anz", "reported_entity_count", "counted_entity")["status"]
        == "unresolved"
    )
    assert (
        attribute("nab", "rwa_amount", "overlay_treatment")["value"]["text"]
        == "excludes_overlays"
    )
    assert (
        attribute("cba", "rwa_amount", "overlay_treatment")["value"]["text"]
        == "includes_overlays"
    )
    assert (
        next(
            r
            for r in reports["anz"]["lineage"]
            if r["field_key"] == "mean_maturity_years"
        )["missing_reason"]
        == "not_applicable"
    )
    assert (
        "not found"
        in invoke(root, "inspect", "--observation", "absent", ok=False).lower()
    )

    restored = tmp_path / "restored"
    git(tmp_path, "clone", "-q", str(tmp_path / "code.bundle"), str(restored))
    with tarfile.open(archive) as tar:
        tar.extractall(restored, filter="data")
    selection = json.loads((restored / manifest).read_text())
    git(restored, "checkout", "--detach", selection["implementation_revision"])
    shutil.rmtree(restored / "raw")
    shutil.rmtree(restored / "extractions")
    warehouse = restored / "recovered.duckdb"
    invoke(restored, "rebuild", "--manifest", manifest, "--warehouse", str(warehouse))
    compare(first, read_snapshot(warehouse), logical=True)
    assert (
        json.loads(
            invoke(
                restored,
                "inspect",
                "--warehouse",
                str(warehouse),
                "--observation",
                cba["observation"]["observation_id"],
            )
        )
        == cba
    )


def test_cli_actionable_config_and_dirty_provenance_errors(cli_root):
    root = cli_root
    assert "reviewed" in invoke(
        root,
        "extract",
        "--bundle",
        "au/unknown/date/pdf",
        "--output-version",
        "v1",
        ok=False,
    )
    request = root / "config/rebuilds/cr6-2025-v1.json"
    raw = json.loads(request.read_text())
    request.write_text(json.dumps(raw | {"unknown_field": True}))
    error = invoke(root, "manifest", "--request", str(request), ok=False)
    assert "unknown_field" in error and str(request) in error
    request.write_text(json.dumps(raw))
    error = invoke(root, "manifest", "--request", str(request), ok=False)
    assert "commit" in error and "config/rebuilds/cr6-2025-v1.json" in error
    script = root / "extractions/au/cba/2025-06-30/aps330/extract.py"
    script.write_text(script.read_text() + "\n# uncommitted change\n")
    error = invoke(
        root,
        "extract",
        "--bundle",
        "au/cba/2025-06-30/aps330",
        "--output-version",
        "v1",
        ok=False,
    )
    assert "extract.py" in error and "commit" in error
    assert not (root / "data").exists()
