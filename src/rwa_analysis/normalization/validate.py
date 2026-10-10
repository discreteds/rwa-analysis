"""Publication boundary: physical contracts, revision FKs and source closure."""

from dataclasses import fields, is_dataclass

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.models import CatalogueRelease, EvidenceRef, RevisionRef
from rwa_analysis.catalogue.resolve import resolve_field
from rwa_analysis.contracts.frames import conform_frame
from rwa_analysis.extraction.cr6 import ExtractionBundle
from rwa_analysis.storage.bronze import BronzeRef

from .cr6 import (
    check_inputs,
    exact_conversion,
    interpretation,
    lineage,
    metadata_rows,
    source_ids,
)
from .models import FIELD_KEY, FIELD_MAP, KEYS, SCHEMAS, SilverCandidate, tabular


def _require(condition, path):
    if not condition:
        raise ValueError(path)


def _contract(name, data):
    _require(data.schema == SCHEMAS[name], f"{name}: physical schema mismatch")
    # Nested structs are checked against explicit physical schemas and the
    # source/catalogue below. Mountainash owns scalar types, required keys and
    # uniqueness; it does not currently express these tagged-union semantics.
    scalar = {key: dtype for key, dtype in data.schema.items() if not dtype.is_nested()}

    def kind(dtype):
        if dtype == pl.Date:
            return "date"
        if dtype == pl.Boolean:
            return "boolean"
        if dtype == pl.Int64:
            return "integer"
        if dtype.is_decimal():
            return "number"
        return "string"

    spec = ma.TypeSpec.from_frictionless(
        {
            "fields": [
                {
                    "name": key,
                    "type": kind(dtype),
                    "constraints": {"required": key in KEYS[name]},
                }
                for key, dtype in scalar.items()
            ],
            "primaryKey": KEYS[name],
            "missingValues": [],
        }
    )
    try:
        conform_frame(data.select(*scalar), spec)
    except Exception as error:
        raise ValueError(f"{name}: frame contract: {error}") from error


def _foreign_key(tables, child, parent, left, right):
    keys = tables[child].select(left).drop_nulls()
    missing = (
        ma.relation(keys)
        .join(tables[parent].select(right), left_on=left, right_on=right, how="anti")
        .collect()
    )
    _require(
        missing.is_empty(),
        f"{child}: unresolved revision-qualified {parent} reference {missing.to_dicts()}",
    )


def _compare(row, expected, path):
    for name, value in expected.items():
        _require(
            row[name] == value, f"{path}.{name}: differs from selected source/catalogue"
        )


def _validate_support(value, catalogue, source_sets, path, visited=None):
    """Bind even transitive definition/decision evidence to selected Bronze."""
    visited = set() if visited is None else visited
    if isinstance(value, EvidenceRef):
        key = (value.bundle_key, value.document_id, value.dataset_id, value.kind)
        _require(
            value.ref_id in source_sets.get(key, set()),
            f"{path}: absent source evidence {value}",
        )
    elif isinstance(value, RevisionRef):
        if value in visited:
            return
        visited.add(value)
        try:
            member = catalogue.member(value)
        except ValueError as error:
            raise ValueError(f"{path}: {error}") from error
        _validate_support(member, catalogue, source_sets, path, visited)
    elif is_dataclass(value):
        for f in fields(value):
            # Historical mappings are closure requirements in the catalogue,
            # not evidence used by this candidate's effective interpretation.
            if f.name not in ("supersedes_refs", "overrides_refs"):
                _validate_support(
                    getattr(value, f.name), catalogue, source_sets, path, visited
                )
    elif isinstance(value, tuple):
        for item in value:
            _validate_support(item, catalogue, source_sets, path, visited)


def validate_candidate(
    candidate: SilverCandidate,
    bundles: tuple[ExtractionBundle, ...],
    bronze_refs: tuple[BronzeRef, ...],
    catalogue: CatalogueRelease,
    *,
    evidence_bundles: tuple[ExtractionBundle, ...] = (),
) -> None:
    check_inputs(bundles, bronze_refs)
    tables, revision = candidate.tables, candidate.revision_id
    _require(
        isinstance(revision, str) and bool(revision), "candidate.revision_id: required"
    )
    _require(
        set(tables) == set(SCHEMAS), "candidate.tables: expected seven Silver tables"
    )
    for name, data in tables.items():
        _contract(name, data)
        _require(
            all(r == revision for r in data["silver_revision_id"]),
            f"{name}.silver_revision_id: wrong revision",
        )

    # Canonical definitions may cite retained evidence outside the publication
    # scope. Supporting bundles validate those citations, never contribute rows.
    # Their exact versions are pinned separately by the rebuild manifest.
    source_sets, sources = {}, {}
    all_bundles = (*bundles, *evidence_bundles)
    _require(
        len({b.bundle_key for b in all_bundles}) == len(all_bundles),
        "evidence_bundles: duplicate or overlapping source scope",
    )
    for bundle in all_bundles:
        for ds in bundle.datasets:
            prefix = (bundle.bundle_key, bundle.document.document_id, ds.id)
            for kind, ids in {
                "context": {ds.context.id},
                "axis": {a.id for a in ds.axes},
                "field": {f.id for f in ds.published_fields},
                "qualification": {q.id for q in ds.qualifications},
                "band": {b.id for s in ds.segmentations for b in s.bands},
                "relationship": {r.id for r in ds.relationships},
            }.items():
                source_sets[(*prefix, kind)] = ids
    for bundle, ref in zip(bundles, bronze_refs, strict=True):
        for ds in bundle.datasets:
            for record in ds.records:
                sources[source_ids(bundle, ds, record)] = (bundle, ref, ds, record)

    observations = {r["observation_id"]: r for r in tables["observations"].to_dicts()}
    _require(
        set(observations) == set(sources), "observations: source row coverage mismatch"
    )
    expected_fields = {
        (oid, target) for oid in sources for target in FIELD_MAP.values()
    }
    indexed = {}
    for name in ("interpretations", "lineage"):
        indexed[name] = {
            (r["observation_id"], r["field_key"]): r for r in tables[name].to_dicts()
        }
        _require(
            set(indexed[name]) == expected_fields
            and len(tables[name]) == len(expected_fields),
            f"{name}: exact field coverage mismatch",
        )

    for child, parent, left, right in [
        (
            "observations",
            "contexts",
            ["silver_revision_id", "context_id"],
            KEYS["contexts"],
        ),
        (
            "observations",
            "segments",
            ["silver_revision_id", "segment_id"],
            KEYS["segments"],
        ),
        (
            "segments",
            "contexts",
            ["silver_revision_id", "context_id"],
            KEYS["contexts"],
        ),
        ("interpretations", "observations", KEYS["observations"], KEYS["observations"]),
        ("lineage", "interpretations", FIELD_KEY, FIELD_KEY),
        ("applied_mappings", "interpretations", FIELD_KEY, FIELD_KEY),
        ("relationships", "contexts", KEYS["contexts"], KEYS["contexts"]),
        (
            "relationships",
            "observations",
            ["silver_revision_id", "parent_observation_id"],
            KEYS["observations"],
        ),
        (
            "relationships",
            "observations",
            ["silver_revision_id", "child_observation_id"],
            KEYS["observations"],
        ),
    ]:
        _foreign_key(tables, child, parent, left, right)

    # These tables are lossless source projections; compare every attribute,
    # including endpoints, evidence, provisional knowledge and band inclusivity.
    for name, expected in metadata_rows(bundles, bronze_refs, revision).items():
        keys = KEYS[name]
        actual = {tuple(r[k] for k in keys): r for r in tables[name].to_dicts()}
        wanted = {tuple(tabular(r)[k] for k in keys): tabular(r) for r in expected}
        _require(actual.keys() == wanted.keys(), f"{name}: source coverage mismatch")
        for key, value in wanted.items():
            _compare(actual[key], value, f"{name}/{key}")

    expected_mappings = set()
    for oid, (bundle, ref, ds, record) in sources.items():
        obs = observations[oid]
        cid = source_ids(bundle, ds)
        _compare(
            obs,
            {
                "context_id": cid,
                "source_record_id": record.record_id,
                "source_row_ref": record.source_row_ref,
                "source_row_role": record.source_row_role,
                "segment_id": f"{cid}/{record.source_segment_memberships[0]}"
                if record.source_segment_memberships
                else None,
            },
            f"observations/{oid}",
        )
        role_values = set()
        for source, target in FIELD_MAP.items():
            key, cell = (oid, target), getattr(record, source)
            meaning = resolve_field(catalogue, ds, record, source)
            role = meaning.attribute("row_role")
            role_values.add((role.value, role.status))
            _validate_support(
                meaning, catalogue, source_sets, f"interpretations/{oid}/{target}"
            )
            _compare(
                indexed["lineage"][key],
                tabular(
                    lineage(
                        revision, oid, target, bundle, ref, ds, record, source, meaning
                    )
                ),
                f"lineage/{oid}/{target}",
            )
            _compare(
                indexed["interpretations"][key],
                tabular(
                    interpretation(revision, oid, target, cell, meaning, catalogue)
                ),
                f"interpretations/{oid}/{target}",
            )
            value = exact_conversion(
                cell.value,
                meaning.unit_factor,
                f"{oid}.{source}",
                count=target == "reported_entity_count",
            )
            _require(
                obs[target] == value,
                f"observations/{oid}.{target}: inconsistent converted value/value_state",
            )
            expected_mappings.update(
                (revision, oid, target, catalogue.id, m.revision_id)
                for m in meaning.mapping_refs
            )
        role, status = (
            next(iter(role_values)) if len(role_values) == 1 else (None, "conflicting")
        )
        _compare(
            obs,
            {"canonical_row_role": role, "row_role_status": status},
            f"observations/{oid}",
        )
    actual_mappings = {
        tuple(
            r[name]
            for name in (
                "silver_revision_id",
                "observation_id",
                "field_key",
                "catalogue_release_id",
                "mapping_revision_ref",
            )
        )
        for r in tables["applied_mappings"].to_dicts()
    }
    _require(
        actual_mappings == expected_mappings,
        "applied_mappings: selected mapping revision/coverage mismatch",
    )
