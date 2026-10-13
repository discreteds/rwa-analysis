"""DISPOSABLE: execution locations only; no source layout or financial meaning."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    project_root: Path
    output_root: Path
