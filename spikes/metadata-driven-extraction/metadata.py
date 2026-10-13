"""DISPOSABLE: data declarations and reusable meanings, independent of operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    revision: str
    assertions: tuple[tuple[str, str | None, str], ...] = ()
    evidence: tuple[str, ...] = ()
    unit: str = ""
    factor: str | None = None
    overrides: tuple[str, ...] = ()


@dataclass(frozen=True)
class Physical:
    id: str
    operation: str
    page: int
    printed_page: str
    parameters: dict


@dataclass(frozen=True)
class Occurrence:
    id: str
    kind: str
    physical: str
    slot: str
    definitions: tuple[str, ...]
    value_kind: str = "text"
    unit: str = ""


@dataclass(frozen=True)
class Link:
    owner: str
    role: str
    target: str


@dataclass(frozen=True)
class Extraction:
    revision: str
    bundle_key: str
    document_id: str
    pdf_path: str
    physical: tuple[Physical, ...]
    occurrences: tuple[Occurrence, ...]
    definitions: tuple[Definition, ...]
    links: tuple[Link, ...]


# Reused across all occurrence kinds and field/cell pairs. No ANZ dates or geometry.
ROLES = tuple(
    Definition(f"role.{kind}@1", (("role", kind, "established"),))
    for kind in ("table", "header", "row", "column", "field", "cell", "comment")
)
PERCENT = Definition("unit.percent@1", unit="%", factor="0.01")
RATIO = Definition("unit.ratio@1", unit="ratio", factor="1")
