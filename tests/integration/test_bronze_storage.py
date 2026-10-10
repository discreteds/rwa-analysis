"""Storage owns lossless transport, immutable publication and strict decoding."""

import json
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from importlib.metadata import version

import pytest

from rwa_analysis.extraction.codec import encode_payload


@pytest.mark.parametrize(
    "bundle_fixture", ["cba_bundle", "westpac_bundle", "nab_bundle", "anz_bundle"]
)
def test_saved_bronze_is_exact_and_immutable(tmp_path, request, bundle_fixture):
    from rwa_analysis.storage.bronze import load_bronze, save_bronze

    bundle = request.getfixturevalue(bundle_fixture)
    before = datetime.now(UTC)
    ref = save_bronze(bundle, "v1", tmp_path, "test-code-revision")
    assert encode_payload(load_bronze(ref, tmp_path)) == encode_payload(bundle)
    path = tmp_path / "data/bronze" / ref.bundle_key / "v1/bundle.json"
    original = path.read_bytes()
    envelope = json.loads(original)
    assert envelope["reference"] == {
        "bundle_key": bundle.bundle_key,
        "output_version": "v1",
    }
    assert envelope["implementation_revision"] == "test-code-revision"
    assert envelope["dependency_versions"]["mountainash-files"] == version(
        "mountainash-files"
    )
    assert envelope["extraction_workflow_version"]
    assert (
        before <= datetime.fromisoformat(envelope["executed_at"]) <= datetime.now(UTC)
    )
    with pytest.raises(FileExistsError):
        save_bronze(bundle, "v1", tmp_path, "different-code-revision")
    assert path.read_bytes() == original
    newer = save_bronze(bundle, "v2", tmp_path, "new-code-revision")
    assert encode_payload(load_bronze(newer, tmp_path)) == encode_payload(bundle)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("field_path", "replacement", "remove", "error"),
    [
        (("schema_version",), "future", False, "schema_version"),
        (("payload", "document"), None, True, "document"),
        (("payload", "surprise"), 1, False, "surprise"),
        (("surprise",), 1, False, "surprise"),
        (("implementation_revision",), None, True, "implementation_revision"),
        (("implementation_revision",), 1, False, "implementation_revision"),
        (("dependency_versions",), [], False, "dependency_versions"),
        (("dependency_versions", "mountainash-files"), 1, False, "dependency_versions"),
        (
            ("extraction_workflow_version",),
            "future",
            False,
            "extraction_workflow_version",
        ),
        (("executed_at",), "yesterday", False, "executed_at"),
        (("executed_at",), "2026-10-10T00:00:00", False, "executed_at"),
        (("reference", "output_version"), "v2", False, "reference"),
        (("reference", "bundle_key"), "au/other/2025-06-30/aps330", False, "reference"),
        (("reference", "extra"), None, False, "extra"),
        (("reference", "output_version"), 1, False, "output_version"),
        (("payload", "datasets"), {}, False, "datasets"),
        pytest.param(
            ("payload", "datasets", 0, "records", 0, "ead", "displayed_precision"),
            None,
            True,
            "displayed_precision",
            id="missing-one-cell-precision-before-arrow-null-fill",
        ),
    ],
)
def test_load_rejects_invalid_envelope(
    tmp_path, cba_bundle, field_path, replacement, remove, error
):
    from rwa_analysis.storage.bronze import load_bronze, save_bronze

    ref = save_bronze(cba_bundle, "v1", tmp_path, "test-revision")
    path = tmp_path / "data/bronze" / ref.bundle_key / "v1/bundle.json"
    envelope = deepcopy(json.loads(path.read_text()))
    target = envelope
    for field in field_path[:-1]:
        target = target[field]
    if field_path[-1] == "displayed_precision":
        # Only one populated cell loses the key. Sibling cells retain it, which
        # makes Arrow silently restore the omitted field as None.
        assert target["displayed_precision"] == 0
        records = envelope["payload"]["datasets"][0]["records"]
        assert records[1]["ead"]["displayed_precision"] == 0
    if remove:
        del target[field_path[-1]]
    else:
        target[field_path[-1]] = replacement
    path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError, match=error):
        load_bronze(ref, tmp_path)


@pytest.mark.parametrize(
    ("bundle_key", "output_version"),
    [
        ("../outside", "v1"),
        ("/au/cba/2025-06-30/aps330", "v1"),
        ("au//cba/aps330", "v1"),
        ("au/cba/../aps330", "v1"),
        ("au/cba/2025-06-30/aps330", "../v1"),
        ("au/cba/2025-06-30/aps330", "v1/other"),
        ("au/cba/2025-06-30/aps330", "..\\v1"),
        ("au/cba/2025-06-30/aps330", "latest"),
        ("au/cba/2025-06-30/aps330", ""),
    ],
)
def test_unsafe_references_cannot_be_saved(
    tmp_path, cba_bundle, bundle_key, output_version
):
    from rwa_analysis.storage.bronze import BronzeRef, save_bronze

    with pytest.raises(ValueError):
        BronzeRef(bundle_key, output_version)
    with pytest.raises(ValueError):
        save_bronze(
            replace(cba_bundle, bundle_key=bundle_key), output_version, tmp_path, "r"
        )
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("failure", ["write", "changed_evidence", "missing_field"])
def test_failed_staging_leaves_previous_version_and_no_partial_output(
    tmp_path, cba_bundle, monkeypatch, failure
):
    from rwa_analysis.storage import bronze

    ref = bronze.save_bronze(cba_bundle, "v1", tmp_path, "r1")
    parent = tmp_path / "data/bronze" / ref.bundle_key
    previous = (parent / "v1/bundle.json").read_bytes()
    real_write = bronze.write

    def faulty_write(sink, envelope):
        # Inject an IO/transport fault; real writing, decoding and publication run.
        changed = deepcopy(envelope)
        if failure == "missing_field":
            cell = changed["payload"]["datasets"][0]["records"][0]["ead"]
            assert cell.pop("missing_reason") is None
        else:
            changed["payload"]["document"]["title"] += " corrupted"
        real_write(sink, changed)
        assert not (parent / "v2").exists()
        if failure == "write":
            raise OSError("injected write failure")

    monkeypatch.setattr(bronze, "write", faulty_write)
    with pytest.raises(
        (OSError, ValueError), match="failure|changed source evidence|missing_reason"
    ):
        bronze.save_bronze(cba_bundle, "v2", tmp_path, "r2")
    assert sorted(p.name for p in parent.iterdir()) == ["v1"]
    assert (parent / "v1/bundle.json").read_bytes() == previous


def test_symlink_cannot_redirect_bronze_outside_project(tmp_path, cba_bundle):
    from rwa_analysis.storage.bronze import BronzeRef, load_bronze, save_bronze

    root = tmp_path / "project"
    (root / "data").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "data/bronze").symlink_to(outside, target_is_directory=True)
    ref = BronzeRef(cba_bundle.bundle_key, "v1")
    with pytest.raises(ValueError, match="project root"):
        save_bronze(cba_bundle, "v1", root, "r")
    with pytest.raises(ValueError, match="project root"):
        load_bronze(ref, root)
    assert list(outside.iterdir()) == []
