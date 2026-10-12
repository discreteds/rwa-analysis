"""Storage owns lossless transport, immutable publication and strict decoding."""

import json
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from importlib.metadata import version

import pytest

from rwa_analysis.extraction.codec import encode_payload


def test_mixed_transport_preserves_temporal_precision_and_missingness(
    tmp_path, legacy_bundle
):
    from decimal import Decimal

    from rwa_analysis.extraction.cr9 import Cr9BacktestingRow, Cr9Context, Cr9Dataset
    from rwa_analysis.extraction.datasets import DatasetMetadata
    from rwa_analysis.extraction.models import ReportedValue
    from rwa_analysis.extraction.temporal import TemporalBinding, TemporalDescriptor
    from rwa_analysis.storage.bronze import BronzeStore

    old = legacy_bundle.datasets[0]
    context = old.metadata.context
    ref = context.evidence[0]
    cr9_context = Cr9Context(
        context.id,
        context.document_date,
        "CR9",
        "Synthetic",
        "Mortgages",
        context.reporting_entity,
        context.consolidation_scope,
        context.regulatory_scope,
        context.geography,
        context.currency,
        (),
        (ref,),
    )
    rate = ReportedValue(Decimal("0.0600"), "0.0600%", 4, None, ref)
    missing = ReportedValue(None, "", None, "blank_unresolved", ref)
    row = Cr9BacktestingRow(
        "band-1",
        "band-1",
        "band",
        (),
        (),
        rate,
        rate,
        rate,
        ReportedValue(0, "0", 0, None, ref),
        missing,
        missing,
        missing,
    )
    history = TemporalDescriptor(
        "history",
        "since 2014; 2.5 years",
        start="2014",
        start_status="established",
        duration_amount=Decimal("2.5"),
        duration_unit="years",
        duration_status="established",
        evidence=(ref,),
    )
    metadata = DatasetMetadata(
        cr9_context,
        (),
        (),
        (),
        (),
        (),
        (),
        (history,),
        (
            TemporalBinding(
                "band-1", "historical_annual_default_rate", "history_window", "history"
            ),
        ),
    )
    dataset = Cr9Dataset("cr9", metadata, (row,))
    bundle = replace(
        legacy_bundle, schema_version="disclosure-v2", datasets=(old, dataset)
    )
    store = BronzeStore(tmp_path / "bronze")
    saved = store.save(bundle, "mixed")
    loaded = store.load(saved).bundle
    assert loaded == bundle
    wire = json.loads(store.path(saved).read_text())
    assert wire["schema_version"] == "disclosure-v2"
    assert [d["domain"] for d in wire["payload"]["datasets"]] == ["cr6", "cr9"]
    assert (
        wire["payload"]["datasets"][1]["metadata"]["temporal_descriptors"][0]["start"]
        == "2014"
    )
    assert (
        wire["payload"]["datasets"][1]["backtesting_rows"][0]["weighted_average_pd"][
            "value"
        ]
        == "0.0600"
    )


def test_legacy_wire_has_no_new_metadata_members(legacy_payload, legacy_bundle):
    assert legacy_bundle.datasets[0].metadata.temporal_descriptors == ()
    assert legacy_bundle.datasets[0].metadata.temporal_bindings == ()
    assert encode_payload(legacy_bundle) == legacy_payload


@pytest.mark.parametrize(
    "bundle_fixture", ["cba_bundle", "westpac_bundle", "nab_bundle", "anz_bundle"]
)
def test_saved_bronze_is_exact_and_immutable(tmp_path, request, bundle_fixture):
    from rwa_analysis.storage.bronze import BronzeStore

    bundle = request.getfixturevalue(bundle_fixture)
    before = datetime.now(UTC)
    store = BronzeStore(tmp_path / "data/bronze")
    ref = store.save(bundle, "v1", "test-code-revision")
    assert encode_payload(store.load(ref).bundle) == encode_payload(bundle)
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
        store.save(bundle, "v1", "different-code-revision")
    assert path.read_bytes() == original
    newer = store.save(bundle, "v2", "new-code-revision")
    assert encode_payload(store.load(newer).bundle) == encode_payload(bundle)
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("field_path", "replacement", "remove", "error"),
    [
        (("schema_version",), "future", False, "schema_version"),
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
    tmp_path, legacy_bundle, field_path, replacement, remove, error
):
    from rwa_analysis.storage.bronze import BronzeStore

    store = BronzeStore(tmp_path / "data/bronze")
    ref = store.save(legacy_bundle, "v1", "test-revision")
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
        store.load(ref)


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
    from rwa_analysis.storage.bronze import BronzeRef, BronzeStore

    with pytest.raises(ValueError):
        BronzeRef(bundle_key, output_version)
    with pytest.raises(ValueError):
        BronzeStore(tmp_path / "data/bronze").save(
            replace(cba_bundle, bundle_key=bundle_key), output_version, "r"
        )
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("failure", ["write", "changed_evidence", "missing_field"])
def test_failed_staging_leaves_previous_version_and_no_partial_output(
    tmp_path, legacy_bundle, monkeypatch, failure
):
    from rwa_analysis.storage import bronze

    store = bronze.BronzeStore(tmp_path / "data/bronze")
    ref = store.save(legacy_bundle, "v1", "r1")
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
        store.save(legacy_bundle, "v2", "r2")
    assert sorted(p.name for p in parent.iterdir()) == ["v1"]
    assert (parent / "v1/bundle.json").read_bytes() == previous


def test_symlink_cannot_redirect_bundle_outside_store(tmp_path, cba_bundle):
    from rwa_analysis.storage.bronze import BronzeRef, BronzeStore

    root = tmp_path / "project"
    (root / "data/bronze").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "data/bronze/au").symlink_to(outside, target_is_directory=True)
    store = BronzeStore(root / "data/bronze")
    ref = BronzeRef(cba_bundle.bundle_key, "v1")
    with pytest.raises(ValueError, match="store root"):
        store.save(cba_bundle, "v1", "r")
    with pytest.raises(ValueError, match="store root"):
        store.load(ref)
    assert list(outside.iterdir()) == []
