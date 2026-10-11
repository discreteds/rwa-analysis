"""Explicit retained rebuild inputs, independent of disposable Silver."""

import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import BaseModel, ConfigDict

from rwa_analysis.storage.bronze import BronzeRef


class CatalogueSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    release_path: str
    evidence_refs: tuple[BronzeRef, ...] = ()


class RebuildSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    bronze_refs: tuple[BronzeRef, ...]
    catalogue: CatalogueSelection


class RebuildManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["cr6-normalised-v1"] = "cr6-normalised-v1"
    revision: str
    organisation_id: str
    selection: RebuildSelection
    catalogue_release_id: str
    bronze_root: Path
    project_root: Path
    implementation_revision: str = "unrecorded"


def identifier(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) is None:
        raise ValueError(f"Expected a single path identifier: {value!r}")
    return value


def retain_manifest(path: Path, manifest: RebuildManifest) -> None:
    """Retain a selection once; repeated publication can reuse that selection."""
    if path.exists():
        if RebuildManifest.model_validate_json(path.read_bytes()) != manifest:
            raise ValueError(f"Revision already names a different selection: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, prefix=".manifest-", mode="w") as staging:
        staging.write(manifest.model_dump_json(indent=2) + "\n")
        staging.flush()
        os.fsync(staging.fileno())
        os.link(staging.name, path)
