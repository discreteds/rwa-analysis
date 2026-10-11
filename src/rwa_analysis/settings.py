"""Execution configuration loaded with Mountainash's native file layering."""

from pathlib import Path

from mountainash_settings import MountainAshBaseSettings
from pydantic import ValidationInfo, field_validator


class ProjectSettings(MountainAshBaseSettings):
    project_root: Path
    bronze_root: Path = Path("data/bronze")
    manifest_root: Path = Path("data/manifests")
    master_path: Path = Path("data/silver/master.duckdb")

    @field_validator("project_root")
    @classmethod
    def absolute_root(cls, value: Path) -> Path:
        return value.resolve()

    @field_validator(
        "bronze_root",
        "manifest_root",
        "master_path",
        "staging_path",
        check_fields=False,
    )
    @classmethod
    def resolve_path(cls, value: Path, info: ValidationInfo) -> Path:
        return (info.data["project_root"] / value).resolve()


class OrganisationSettings(ProjectSettings):
    organisation_id: str
    staging_path: Path
