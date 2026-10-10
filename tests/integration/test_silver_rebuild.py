"""Real persistence lifecycle: lossless rebuild, scope replacement and rollback.

These own storage risks not exercised by the in-memory conformance tests. No
database doubles or production failure switches are involved.
"""

import json
import shutil
import subprocess
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest
from mountainash_data import IbisBackend
from polars.testing import assert_frame_equal

TABLES = (
    "contexts",
    "segments",
    "observations",
    "interpretations",
    "applied_mappings",
    "lineage",
    "relationships",
)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def retained(
    tmp_path, project_root, cba_bundle, westpac_bundle, nab_bundle, anz_bundle
):
    from rwa_analysis.storage.bronze import save_bronze

    root = tmp_path / "project"
    root.mkdir()
    for directory in ("catalogue", "src"):
        shutil.copytree(
            project_root / directory,
            root / directory,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    for name in ("uv.lock", "pyproject.toml"):
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
        "Retained implementation and catalogue",
    )
    refs = tuple(
        save_bronze(b, "v1", root, git(root, "rev-parse", "HEAD"))
        for b in (cba_bundle, westpac_bundle, nab_bundle, anz_bundle)
    )
    return root, refs, git(root, "rev-parse", "HEAD")


def manifest(
    retained, revision="r1", refs=None, release="catalogue/releases/cr6-v1.json"
):
    from rwa_analysis.storage.manifests import RebuildRequest, save_manifest

    root, selected, code = retained
    request = RebuildRequest(
        revision_id=revision,
        bronze_refs=selected if refs is None else refs,
        catalogue_release_path=release,
        conformance_schema_version="cr6-v1",
    )
    return save_manifest(request, root, code)


def read_snapshot(path: Path) -> dict[str, pl.DataFrame]:
    with IbisBackend(dialect="duckdb", database=str(path)) as db:
        result = {
            name: pl.from_arrow(db.table(name, namespace="silver").to_pyarrow())
            for name in TABLES
        }
        result["publication"] = pl.from_arrow(
            db.table("silver_publication", namespace="ops").to_pyarrow()
        )
        return result


def compare(left, right, *, logical=False):
    for name in left:
        a, b = left[name], right[name]
        if logical:
            ignored = [
                c
                for c in (
                    "silver_revision_id",
                    "published_at",
                    "manifest_path",
                    "manifest_sha256",
                )
                if c in a.columns
            ]
            a, b = a.drop(ignored), b.drop(ignored)
        keys = [c for c, dtype in a.schema.items() if not dtype.is_nested()]
        assert_frame_equal(a.sort(keys), b.sort(keys))


def test_fresh_rebuild_identity_and_exact_manifest_repeat(retained, tmp_path):
    from rwa_analysis.storage.silver import rebuild

    root, _, _ = retained
    m1, m2 = manifest(retained), manifest(retained, "r2")
    a, b = tmp_path / "a.duckdb", tmp_path / "b.duckdb"
    assert not (root / "raw").exists() and not (root / "tests").exists()
    assert rebuild(m1, root, a) == "r1"
    first = read_snapshot(a)
    assert rebuild(m2, root, b) == "r2"
    compare(first, read_snapshot(b), logical=True)
    assert len(first["observations"]) == 36
    assert len(first["interpretations"]) == len(first["lineage"]) == 432
    assert len(first["relationships"]) == 32
    assert first["observations"].schema["ead_amount"] == pl.Decimal(22, 8)
    oid = "au/cba/2025-06-30/aps330/cr6-residential-mortgages/band-1"
    assert first["observations"].filter(pl.col("observation_id") == oid)["ead_amount"][
        0
    ] == Decimal(281508000000)
    for name in ("interpretations", "lineage"):
        assert len(first[name].filter(pl.col("observation_id") == oid)) == 12
    marker = first["publication"].row(0, named=True)
    assert marker["status"] == "published" and marker["silver_revision_id"] == "r1"
    assert marker["manifest_path"] == "data/manifests/r1.json"
    assert rebuild(m1, root, a) == "r1"
    compare(first, read_snapshot(a))  # Includes unchanged publication timestamp.
    a.unlink()
    assert rebuild(m1, root, a) == "r1"
    compare(first, read_snapshot(a), logical=True)


def test_real_view_obstruction_rolls_back_all_tables_and_marker(retained, tmp_path):
    from rwa_analysis.catalogue.load import load_catalogue
    from rwa_analysis.normalization.cr6 import conform_cr6
    from rwa_analysis.storage.bronze import load_bronze
    from rwa_analysis.storage.silver import publish_candidate, rebuild

    root, refs, _ = retained
    warehouse = tmp_path / "rollback.duckdb"
    rebuild(manifest(retained), root, warehouse)
    before = read_snapshot(warehouse)
    later = manifest(retained, "r2")
    candidate = conform_cr6(
        tuple(load_bronze(r, root) for r in refs),
        refs,
        load_catalogue(root / "catalogue/releases/cr6-v1.json"),
        "r2",
    )
    with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
        raw = db.raw_driver_connection()
        raw.execute(
            "ALTER TABLE silver.applied_mappings RENAME TO saved_applied_mappings"
        )
        raw.execute(
            "CREATE VIEW silver.applied_mappings AS SELECT * FROM silver.saved_applied_mappings"
        )
    try:
        with pytest.raises(
            Exception, match="applied_mappings.*View|View.*applied_mappings"
        ):
            publish_candidate(candidate, later, warehouse)
        compare(before, read_snapshot(warehouse))
    finally:
        with IbisBackend(dialect="duckdb", database=str(warehouse)) as db:
            raw = db.raw_driver_connection()
            raw.execute("DROP VIEW silver.applied_mappings")
            raw.execute(
                "ALTER TABLE silver.saved_applied_mappings RENAME TO applied_mappings"
            )
    broken = replace(
        candidate,
        tables=candidate.tables | {"lineage": candidate.tables["lineage"].slice(1)},
    )
    with pytest.raises(ValueError, match="lineage"):
        publish_candidate(broken, later, warehouse)
    compare(before, read_snapshot(warehouse))


def test_mapping_revision_and_selected_scope_replacement(retained, tmp_path):
    from rwa_analysis.storage.bronze import load_bronze, save_bronze
    from rwa_analysis.storage.silver import rebuild

    root, refs, _ = retained
    warehouse = tmp_path / "correction.duckdb"
    rebuild(manifest(retained), root, warehouse)
    before = read_snapshot(warehouse)
    path = root / "catalogue/mappings/cba-2025-06-30-v1.json"
    mapping = json.loads(path.read_text())
    member = next(
        m for m in mapping["members"] if m["revision_id"] == "cba.cr6.average_lgd@v1"
    )
    member["revision_id"] = "cba.cr6.average_lgd@v2"
    annotation = next(a for a in member["attributes"] if a["name"] == "weighting")
    annotation.update(
        value="Synthetic reviewed annotation correction", status="provisional"
    )
    changed = root / "catalogue/mappings/cba-review-v2.json"
    changed.write_text(json.dumps(mapping))
    release = json.loads((root / "catalogue/releases/cr6-v1.json").read_text())
    release["id"] = "cr6-v2"
    for selected in release["selection"]:
        if selected["revision_id"] == "cba.cr6.average_lgd@v1":
            selected.update(
                path="mappings/cba-review-v2.json", revision_id="cba.cr6.average_lgd@v2"
            )
    (root / "catalogue/releases/cr6-v2.json").write_text(json.dumps(release))
    rebuild(
        manifest(retained, "corrected", release="catalogue/releases/cr6-v2.json"),
        root,
        warehouse,
    )
    after = read_snapshot(warehouse)
    compare(
        {"observations": before["observations"]},
        {"observations": after["observations"]},
        logical=True,
    )
    assert "cba.cr6.average_lgd@v2" in after["applied_mappings"]["mapping_revision_ref"]
    assert (
        "cba.cr6.average_lgd@v1"
        not in after["applied_mappings"]["mapping_revision_ref"]
    )
    assert "Synthetic reviewed annotation correction" in str(
        after["interpretations"].to_dicts()
    )
    september = manifest(retained, "september", refs=refs[1:])
    rebuild(september, root, warehouse)
    selected = read_snapshot(warehouse)
    assert len(selected["observations"]) == 27
    assert len(selected["interpretations"]) == len(selected["lineage"]) == 324
    assert len(selected["contexts"]) == 3 and len(selected["segments"]) == 24
    assert len(selected["relationships"]) == 24
    assert selected["lineage"]["bundle_key"].n_unique() == 3
    for name in TABLES:
        assert "au/cba/" not in str(selected[name].to_dicts())
    # Shared concepts still cite CBA's retained provenance. A later source
    # version must not alter the separately pinned supporting-evidence input.
    save_bronze(load_bronze(refs[0], root), "v2", root, retained[2])
    rebuild(september, root, warehouse)
    compare(selected, read_snapshot(warehouse))
    with pytest.raises(ValueError, match="unambiguous"):
        manifest(retained, "ambiguous-support", refs=refs[1:])
    assert not (root / "data/manifests/ambiguous-support.json").exists()


@pytest.mark.parametrize(
    "change",
    [
        {"corrections": []},
        {"revision_id": "../escape"},
        {"revision_id": 1},
        {"catalogue_release_path": "/absolute.json"},
        {"catalogue_release_path": "catalogue/../escape.json"},
        {"conformance_schema_version": "latest"},
        {
            "bronze_refs": [
                {
                    "bundle_key": "au/cba/2025-06-30/aps330",
                    "output_version": "v1",
                    "ignored": True,
                }
            ]
        },
        {
            "bronze_refs": [
                {"bundle_key": "au/cba/2025-06-30/aps330", "output_version": v}
                for v in ("v1", "v2")
            ]
        },
    ],
)
def test_request_rejects_ambiguous_or_unsafe_inputs(change):
    from rwa_analysis.storage.manifests import RebuildRequest

    raw = {
        "revision_id": "r",
        "bronze_refs": [],
        "catalogue_release_path": "catalogue/releases/cr6-v1.json",
        "conformance_schema_version": "cr6-v1",
    }
    with pytest.raises(ValueError):
        RebuildRequest.model_validate_json(json.dumps(raw | change))


def test_manifest_is_immutable_and_rejects_changed_retained_inputs(retained, tmp_path):
    from rwa_analysis.storage.manifests import RebuildRequest, save_manifest
    from rwa_analysis.storage.silver import rebuild

    root, refs, _ = retained
    path = manifest(retained)
    frozen = path.read_bytes()
    with pytest.raises(FileExistsError):
        manifest(retained, refs=refs[1:])
    assert path.read_bytes() == frozen
    request = RebuildRequest(
        revision_id="bad-code",
        bronze_refs=refs,
        catalogue_release_path="catalogue/releases/cr6-v1.json",
        conformance_schema_version="cr6-v1",
    )
    with pytest.raises(ValueError, match="implementation"):
        save_manifest(request, root, "not-a-commit")
    assert not (root / "data/manifests/bad-code.json").exists()
    for relative in (
        "uv.lock",
        "catalogue/mappings/cba-2025-06-30-v1.json",
        f"data/bronze/{refs[0].bundle_key}/v1/bundle.json",
    ):
        source = root / relative
        original = source.read_bytes()
        source.write_bytes(original + b"\n")
        try:
            with pytest.raises(ValueError, match="changed|match"):
                rebuild(path, root, tmp_path / "absent.duckdb")
        finally:
            source.write_bytes(original)
    assert not (tmp_path / "absent.duckdb").exists()
    (root / "src/rwa_analysis/__init__.py").write_text("# Different implementation\n")
    git(root, "add", "src")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-qm",
        "Different implementation",
    )
    with pytest.raises(ValueError, match="implementation"):
        save_manifest(request, root, git(root, "rev-parse", "HEAD"))


def test_same_revision_from_different_retained_selection_is_not_idempotent(
    retained, tmp_path
):
    from rwa_analysis.storage.silver import rebuild

    root, refs, code = retained
    warehouse = tmp_path / "shared.duckdb"
    rebuild(manifest(retained), root, warehouse)
    before = read_snapshot(warehouse)
    other = tmp_path / "other-project"
    shutil.copytree(root, other, ignore=shutil.ignore_patterns("manifests"))
    # Another data root must not silently claim an existing warehouse's revision
    # solely because its relative manifest filename and catalogue ID coincide.
    different = manifest((other, tuple(reversed(refs)), code))
    with pytest.raises(ValueError, match="different manifest"):
        rebuild(different, other, warehouse)
    compare(before, read_snapshot(warehouse))


@pytest.mark.parametrize("missing", ["bronze", "catalogue", "lock"])
def test_missing_input_cannot_leave_a_manifest(retained, missing):
    root, refs, _ = retained
    paths = {
        "bronze": f"data/bronze/{refs[0].bundle_key}/v1/bundle.json",
        "catalogue": "catalogue/mappings/cba-2025-06-30-v1.json",
        "lock": "uv.lock",
    }
    (root / paths[missing]).unlink()
    with pytest.raises(FileNotFoundError):
        manifest(retained)
    assert not (root / "data/manifests/r1.json").exists()
