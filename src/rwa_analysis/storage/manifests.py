"""Durable single-writer rebuild selections, independent of the warehouse.

Git retains implementation/lock/configuration; versioned Bronze and catalogue
files remain retained inputs. Digests detect edits to those saved inputs, not
PDF acquisition identity. Recovery uses the recorded Git commit and lockfile.
"""

import hashlib
import os
import re
import subprocess
import sys
from dataclasses import asdict, fields, is_dataclass
from importlib.metadata import version
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import EvidenceRef
from rwa_analysis.storage.bronze import BronzeRef, load_bronze


def _relative(value: str) -> str:
    if not value or any(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", p) is None for p in value.split("/")
    ):
        raise ValueError(f"Unsafe relative path: {value!r}")
    return value


def _path(root: Path, relative: str) -> Path:
    path = root / _relative(relative)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project root: {relative}")
    return path


class RebuildRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    revision_id: str
    bronze_refs: tuple[BronzeRef, ...]
    catalogue_release_path: str
    conformance_schema_version: Literal["cr6-v1"]

    @field_validator("revision_id")
    @classmethod
    def safe_id(cls, value):
        if "/" in value:
            raise ValueError("revision_id must be a single identifier")
        return _relative(value)

    @field_validator("catalogue_release_path")
    @classmethod
    def safe_release(cls, value):
        _relative(value)
        if not value.startswith("catalogue/releases/") or not value.endswith(".json"):
            raise ValueError("Select an explicit catalogue/releases JSON path")
        return value

    @field_validator("bronze_refs", mode="before")
    @classmethod
    def strict_refs(cls, value):
        if not isinstance(value, (tuple, list)):
            # Pydantic wraps ValueError as a request-validation failure.
            raise ValueError("bronze_refs must be an array")  # noqa: TRY004
        refs = []
        for item in value:
            if isinstance(item, BronzeRef):
                refs.append(item)
            elif type(item) is dict and set(item) == {"bundle_key", "output_version"}:
                refs.append(BronzeRef(**item))
            else:
                raise ValueError("Invalid BronzeRef fields")
        return tuple(refs)

    @model_validator(mode="after")
    def unique_bundles(self):
        keys = [ref.bundle_key for ref in self.bronze_refs]
        if len(keys) != len(set(keys)):
            raise ValueError("Select only one version of each Bronze bundle")
        return self


class RebuildManifest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    manifest_schema_version: Literal["cr6-v1"] = "cr6-v1"
    request: RebuildRequest
    implementation_revision: str
    catalogue_release_id: str
    catalogue_members: tuple[dict[str, str], ...]
    evidence_bronze_refs: tuple[BronzeRef, ...]
    input_digests: dict[str, str]
    environment: dict[str, str]


def _git(root: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(
            "implementation revision unavailable in retained Git repository"
        ) from error


def _implementation(root: Path, revision: str) -> str:
    """Compare the executing package, not merely a supplied checkout's HEAD.

    A separate data root may use the installed editable checkout's Git objects.
    A restored clone may provide its own objects. Neither accepts an arbitrary
    existing directory as evidence of a matching implementation revision.
    """
    installed = Path(__file__).resolve().parents[3]
    repo = root if (root / ".git").exists() else installed
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("implementation_revision must be a full Git commit")
    commit = (
        _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    )
    paths = (
        _git(repo, "ls-tree", "-r", "--name-only", commit, "src/rwa_analysis")
        .decode()
        .splitlines()
    )
    actual = {
        p.relative_to(installed).as_posix()
        for p in (installed / "src/rwa_analysis").rglob("*.py")
    }
    expected = {p for p in paths if p.endswith(".py")}
    if actual != expected or not expected:
        raise ValueError("Running implementation file set does not match Git revision")
    for relative in sorted(expected):
        if (installed / relative).read_bytes() != _git(
            repo, "show", f"{commit}:{relative}"
        ):
            raise ValueError(
                f"Running implementation does not match revision: {relative}"
            )
    for relative in ("pyproject.toml", "uv.lock"):
        if _path(root, relative).read_bytes() != _git(
            repo, "show", f"{commit}:{relative}"
        ):
            raise ValueError(
                f"Retained configuration does not match implementation: {relative}"
            )
    return commit


def _environment() -> dict[str, str]:
    packages = (
        "mountainash",
        "mountainash-data",
        "mountainash-files",
        "polars",
        "duckdb",
        "ibis-framework",
        "pyarrow",
        "pydantic",
    )
    return {"python": sys.version} | {name: version(name) for name in packages}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_keys(value):
    if isinstance(value, EvidenceRef):
        yield value.bundle_key
    elif is_dataclass(value):
        for field in fields(value):
            yield from _evidence_keys(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _evidence_keys(item)


def _inputs(request: RebuildRequest, root: Path, evidence_refs=None):
    bundles = tuple(load_bronze(ref, root) for ref in request.bronze_refs)
    catalogue = load_catalogue(_path(root, request.catalogue_release_path))
    # A release's research provenance survives removal of a bank from Silver.
    # Resolve only an unambiguous saved version, then freeze it in the manifest;
    # rebuild never rediscovers versions or chooses "latest".
    support_keys = set(_evidence_keys(catalogue.members)) - {
        r.bundle_key for r in request.bronze_refs
    }
    if evidence_refs is None:
        evidence_refs = []
        for key in sorted(support_keys):
            versions = sorted(_path(root, f"data/bronze/{key}").glob("*/bundle.json"))
            if len(versions) != 1:
                raise ValueError(
                    f"Supporting Bronze evidence requires one unambiguous retained version: {key}"
                )
            evidence_refs.append(BronzeRef(key, versions[0].parent.name))
        evidence_refs = tuple(evidence_refs)
    if {ref.bundle_key for ref in evidence_refs} != support_keys or len(
        evidence_refs
    ) != len(support_keys):
        raise ValueError(
            "Manifest supporting evidence selection does not match catalogue"
        )
    evidence_bundles = tuple(load_bronze(ref, root) for ref in evidence_refs)
    paths = {"uv.lock", "pyproject.toml", request.catalogue_release_path}
    paths.update(
        f"data/bronze/{ref.bundle_key}/{ref.output_version}/bundle.json"
        for ref in (*request.bronze_refs, *evidence_refs)
    )
    paths.update(f"catalogue/{member.path}" for member in catalogue.selection)
    digests = {relative: _digest(_path(root, relative)) for relative in sorted(paths)}
    return bundles, catalogue, digests, evidence_refs, evidence_bundles


def save_manifest(
    request: RebuildRequest, project_root: Path, implementation_revision: str
) -> Path:
    root = project_root.resolve(strict=True)
    destination = _path(root, f"data/manifests/{request.revision_id}.json")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    revision = _implementation(root, implementation_revision)
    _, catalogue, digests, evidence_refs, _ = _inputs(request, root)
    manifest = RebuildManifest(
        request=request,
        implementation_revision=revision,
        catalogue_release_id=catalogue.id,
        catalogue_members=tuple(asdict(m) for m in catalogue.selection),
        evidence_bronze_refs=evidence_refs,
        input_digests=digests,
        environment=_environment(),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Hard-link publication is atomic and cannot replace an existing manifest.
    with NamedTemporaryFile(
        dir=destination.parent, prefix=".manifest-", mode="w"
    ) as staging:
        staging.write(manifest.model_dump_json(indent=2) + "\n")
        staging.flush()
        os.fsync(staging.fileno())
        os.link(staging.name, destination)
    return destination


def load_manifest(manifest_path: Path, project_root: Path, *, verify_runtime=True):
    """Load retained inputs, verifying runtime for execution by default.

    Read-only historical review may use a newer renderer: it validates the same
    retained bytes without claiming to execute the publication's implementation.
    Rebuild callers must retain the default runtime verification.
    """
    root = project_root.resolve(strict=True)
    manifest = RebuildManifest.model_validate_json(manifest_path.read_bytes())
    expected = _path(root, f"data/manifests/{manifest.request.revision_id}.json")
    if manifest_path.resolve() != expected.resolve():
        raise ValueError("Manifest must use its retained revision path")
    if verify_runtime:
        _implementation(root, manifest.implementation_revision)
        if _environment() != manifest.environment:
            raise ValueError(
                "Environment changed; restore the recorded lock/environment"
            )
    # Check bytes before decoding, so even edits which remain valid cannot reuse
    # the recorded revision. Then ensure the inventory itself is complete.
    for relative, digest in manifest.input_digests.items():
        if _digest(_path(root, relative)) != digest:
            raise ValueError(f"Retained input changed: {relative}")
    bundles, catalogue, digests, _, evidence_bundles = _inputs(
        manifest.request, root, manifest.evidence_bronze_refs
    )
    if (
        digests != manifest.input_digests
        or catalogue.id != manifest.catalogue_release_id
        or tuple(asdict(m) for m in catalogue.selection) != manifest.catalogue_members
    ):
        raise ValueError("Manifest selection does not match retained inputs")
    return manifest, bundles, catalogue, evidence_bundles
