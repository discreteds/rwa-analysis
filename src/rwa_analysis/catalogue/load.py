"""Strict, pinned catalogue loading and internal reference-graph validation."""

import json
from dataclasses import MISSING, fields, is_dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import UnionType
from typing import Literal, get_args, get_origin, get_type_hints

from .models import (
    CatalogueRelease,
    ConceptRelationshipRevision,
    ConceptRevision,
    InterpretationDecisionRevision,
    MeasureRevision,
    MemberSelection,
    RevisionRef,
    SourceMappingRevision,
)

TYPES = {
    "concept": ConceptRevision,
    "relationship": ConceptRelationshipRevision,
    "measure": MeasureRevision,
    "decision": InterpretationDecisionRevision,
    "mapping": SourceMappingRevision,
}


def _decode(value, annotation):
    """Catalogue defaults are explicit dataclass defaults, not dropped metadata."""
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is UnionType:
        for option in args:
            try:
                return _decode(value, option)
            except (TypeError, ValueError):
                pass
        raise ValueError(f"Invalid {annotation}: {value!r}")
    if origin is Literal:
        if not any(type(value) is type(x) and value == x for x in args):
            raise ValueError(f"Expected {args}, got {value!r}")
        return value
    if origin is tuple:
        if type(value) is not list:
            raise ValueError("Expected JSON array")
        return tuple(_decode(v, args[0]) for v in value)
    if is_dataclass(annotation):
        if type(value) is not dict:
            raise ValueError(f"Expected {annotation.__name__} object")
        declared = {f.name: f for f in fields(annotation)}
        required = {
            k
            for k, f in declared.items()
            if f.default is MISSING and f.default_factory is MISSING
        }
        if set(value) - declared.keys() or required - value.keys():
            raise ValueError(
                f"{annotation.__name__}: unknown {set(value) - declared.keys()}, missing {required - value.keys()}"
            )
        hints = get_type_hints(annotation)
        return annotation(**{k: _decode(v, hints[k]) for k, v in value.items()})
    if annotation is date:
        if type(value) is not str:
            raise ValueError("Expected ISO date string")
        return date.fromisoformat(value)
    if annotation is Decimal:
        if type(value) is not str:
            raise ValueError("Expected Decimal string")
        try:
            result = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("Invalid Decimal") from error
        if not result.is_finite():
            raise ValueError("Nonfinite Decimal")
        return result
    if annotation not in (str, int, bool, type(None)) or type(value) is not annotation:
        raise ValueError(f"Expected {annotation}, got {value!r}")
    return value


def _references(value):
    if isinstance(value, RevisionRef):
        yield value
    elif is_dataclass(value):
        for field in fields(value):
            yield from _references(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _references(item)


def load_catalogue(release_path: Path) -> CatalogueRelease:
    release_path = Path(release_path)
    root = release_path.parent.parent.resolve()
    raw = json.loads(release_path.read_text())
    selection = _decode(raw.get("selection"), tuple[MemberSelection, ...])
    if len({s.revision_id for s in selection}) != len(selection):
        raise ValueError("Duplicate selected revision")
    cache, members = {}, []
    for selected in selection:
        path = (root / selected.path).resolve()
        if not path.is_relative_to(root) or Path(selected.path).is_absolute():
            raise ValueError(f"Catalogue member path outside root: {selected.path}")
        if path not in cache:
            content = json.loads(path.read_text())
            if (
                set(content) != {"schema_version", "members"}
                or content["schema_version"] != "cr6-v1"
            ):
                raise ValueError(f"Invalid catalogue member file: {path}")
            if type(content["members"]) is not list:
                raise ValueError("Expected members array")
            ids = [m["revision_id"] for m in content["members"]]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate file member revision: {path}")
            cache[path] = dict(zip(ids, content["members"], strict=True))
        if selected.revision_id not in cache[path]:
            raise ValueError(f"Unresolved selected revision: {selected.revision_id}")
        members.append(_decode(cache[path][selected.revision_id], TYPES[selected.kind]))
    # Validate the release envelope with the same strict schema, then attach
    # already-resolved immutable members (no union guessing for revision kinds).
    if set(raw) != {"id", "schema_version", "created_on", "selection"}:
        raise ValueError("Invalid release fields")
    cat = CatalogueRelease(
        _decode(raw["id"], str),
        _decode(raw["schema_version"], Literal["cr6-v1"]),
        _decode(raw["created_on"], date),
        selection,
        tuple(members),
    )
    graph = {}
    for selected, member in zip(selection, members, strict=True):
        refs = tuple(_references(member))
        for ref in refs:
            cat.member(ref)
        graph[selected.revision_id] = tuple(r.revision_id for r in refs)
        for attribute in getattr(member, "attributes", ()):
            if attribute.name == "result_unit" and attribute.value is not None:
                unit = cat.member(attribute.value)
                if not isinstance(unit, ConceptRevision) or unit.category != "unit":
                    raise ValueError(f"Invalid result unit: {attribute.value}")
        if isinstance(member, MeasureRevision):
            unit = cat.member(member.result_unit_ref)
            if not isinstance(unit, ConceptRevision) or unit.category != "unit":
                raise ValueError(f"Invalid result unit: {member.result_unit_ref}")
        if isinstance(member, ConceptRelationshipRevision) and (
            member.parent_ref.kind != "concept" or member.child_ref.kind != "concept"
        ):
            raise ValueError("Relationship endpoints must be concepts")
        if (
            isinstance(member, SourceMappingRevision)
            and member.measure_ref
            and member.concept_ref
            and cat.member(member.measure_ref).concept_ref != member.concept_ref
        ):
            raise ValueError(
                f"Mapping concept disagrees with measure: {member.revision_id}"
            )

    visited, active = set(), set()

    def visit(node):
        if node in active:
            raise ValueError(f"Cycle in catalogue revisions: {node}")
        if node in visited:
            return
        active.add(node)
        for dependency in graph[node]:
            visit(dependency)
        active.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    for member in members:
        if isinstance(member, SourceMappingRevision):
            for ref in member.overrides_refs:
                target = cat.member(ref)
                if not member.scope.narrows(target.scope) or not (
                    member.evidence_refs or member.decision_refs
                ):
                    raise ValueError(
                        f"Override requires supported narrower scope: {member.revision_id}"
                    )
    return cat
