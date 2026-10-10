"""Immutable, lossless Bronze publication through mountainash-files.

Publication assumes a single writer. A complete validated staging directory is
renamed on the same filesystem; readers select explicit versions, never latest.
"""

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import distributions
from pathlib import Path
from tempfile import TemporaryDirectory

from mountainash_files import FileSinkSpec, parse_bytes, write

from rwa_analysis.extraction.codec import (
    decode_envelope,
    encode_envelope,
    encode_payload,
)
from rwa_analysis.extraction.cr6 import ExtractionBundle


@dataclass(frozen=True)
class BronzeRef:
    bundle_key: str
    output_version: str

    def __post_init__(self):
        for name, value, components in (
            ("bundle_key", self.bundle_key, 4),
            ("output_version", self.output_version, 1),
        ):
            if type(value) is not str:
                raise ValueError(f"{name}: expected string identifier")
            parts = value.split("/")
            if len(parts) != components or any(
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part) is None
                for part in parts
            ):
                raise ValueError(f"{name}: invalid path identifier {value!r}")
        if self.output_version.lower() == "latest":
            raise ValueError("output_version: select an explicit version, not latest")


def _destination(ref: BronzeRef, project_root: Path) -> Path:
    root = project_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project root must be a directory")
    destination = root / "data/bronze" / ref.bundle_key / ref.output_version
    if not (destination / "bundle.json").resolve().is_relative_to(root):
        raise ValueError("Bronze path escapes project root")
    return destination


def read_staged_bundle(
    path: Path, *, expected_reference: BronzeRef | None = None
) -> ExtractionBundle:
    """Private shared reader for staged and published bundles."""
    # Validate the original JSON before Arrow unifies nested records: otherwise
    # an absent required key can be silently restored as a nullable field.
    # Both decoders consume the same bytes, including during staged readback.
    raw = path.read_bytes()
    envelope = json.loads(raw)
    bundle = decode_envelope(
        envelope,
        expected_reference=asdict(expected_reference) if expected_reference else None,
    )
    BronzeRef(**envelope["reference"])
    result = parse_bytes(raw, "json", output="pydata")
    if type(result.data) is not list or len(result.data) != 1:
        raise ValueError("Bronze envelope: expected one JSON object")
    if result.data[0] != envelope:
        raise ValueError("Bronze normalization changed source evidence or provenance")
    return bundle


def save_bronze(
    bundle: ExtractionBundle,
    output_version: str,
    project_root: Path,
    implementation_revision: str,
) -> BronzeRef:
    """Publish a new version only after an exact source-contract readback."""
    ref = BronzeRef(bundle.bundle_key, output_version)
    destination = _destination(ref, project_root)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    dependencies = {
        re.sub(r"[-_.]+", "-", d.metadata["Name"]).lower(): d.version
        for d in distributions()
    }
    dependencies["python"] = sys.version
    envelope = encode_envelope(
        bundle,
        output_version=output_version,
        implementation_revision=implementation_revision,
        dependency_versions=dependencies,
        executed_at=datetime.now(UTC).isoformat(),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=f".{output_version}-", dir=destination.parent
    ) as temp:
        staging = Path(temp)
        write(FileSinkSpec(path=str(staging / "bundle.json"), format="json"), envelope)
        restored = read_staged_bundle(staging / "bundle.json", expected_reference=ref)
        if encode_payload(restored) != envelope["payload"]:
            raise ValueError("Bronze serialization changed source evidence")
        # Never replace even an empty version directory. Single-writer ownership
        # excludes a concurrent creation between this check and rename.
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        staging.rename(destination)
    return ref


def load_bronze(ref: BronzeRef, project_root: Path) -> ExtractionBundle:
    """Load exactly the retained version selected by the caller."""
    return read_staged_bundle(
        _destination(ref, project_root) / "bundle.json", expected_reference=ref
    )
