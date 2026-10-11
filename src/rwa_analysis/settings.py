"""Execution configuration loaded with Mountainash's native file layering."""

from pathlib import Path

from mountainash_settings import MountainAshBaseSettings
from pydantic import Field, ValidationInfo, field_validator


class ProjectSettings(MountainAshBaseSettings):
    project_root: Path
    bronze_root: Path = Field(default=Path("data/bronze"), validate_default=True)
    manifest_root: Path = Field(default=Path("data/manifests"), validate_default=True)
    master_path: Path = Field(
        default=Path("data/silver/master.duckdb"), validate_default=True
    )

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
