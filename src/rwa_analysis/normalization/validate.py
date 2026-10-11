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
    convert_dataset,
    decimal_type,
    interpretation,
    lineage,
    metadata_rows,
    source_ids,
)
from .models import FIELD_MAP, KEYS, SCHEMAS, SilverCandidate, tabular


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
        conform_frame(ma.relation(data).select(*scalar).to_polars(), spec)
    except Exception as error:
        raise ValueError(f"{name}: frame contract: {error}") from error


def _foreign_key(tables, child, parent, left, right):
    keys = ma.relation(tables[child]).select(*left).drop_nulls()
    missing = (
        keys
        .join(ma.relation(tables[parent]).select(*right), left_on=left, right_on=right, how="anti")
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
        set(tables) == set(SCHEMAS), "candidate.tables: expected three Silver tables"
    )
    for name, data in tables.items():
        _contract(name, data)
        _require(
            ma.relation(data).filter(ma.col("silver_revision_id") != revision).count_rows() == 0,
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

    observations = {r["observation_id"]: r for r in tables["cr6_observations"].to_dicts()}
    _require(
        set(observations) == set(sources), "observations: source row coverage mismatch"
    )
    expected_fields = {
        (oid, target) for oid in sources for target in FIELD_MAP.values()
    }
    indexed = {}
    for name in ("cr6_fields",):
        indexed[name] = {
            (r["observation_id"], r["field_key"]): r for r in tables[name].to_dicts()
        }
        _require(
            set(indexed[name]) == expected_fields
            and len(tables[name]) == len(expected_fields),
            f"{name}: exact field coverage mismatch",
        )

    for child, parent, left, right in [
        ("cr6_fields", "cr6_observations", KEYS["cr6_observations"], KEYS["cr6_observations"]),
        (
            "cr6_relationships",
            "cr6_observations",
            ["silver_revision_id", "parent_observation_id"],
            KEYS["cr6_observations"],
        ),
        (
            "cr6_relationships",
            "cr6_observations",
            ["silver_revision_id", "child_observation_id"],
            KEYS["cr6_observations"],
        ),
    ]:
        _foreign_key(tables, child, parent, left, right)

    # These tables are lossless source projections; compare every attribute,
    # including endpoints, evidence, provisional knowledge and band inclusivity.
    metadata = metadata_rows(bundles, bronze_refs, revision)
    contexts = {r.context_id: tabular(r) for r in metadata["contexts"]}
    segments = {r.segment_id: tabular(r) for r in metadata["segments"]}
    relationships = {r["relationship_id"]: r for r in tables["cr6_relationships"].to_dicts()}
    wanted = {r.relationship_id: tabular(r) for r in metadata["relationships"]}
    _require(relationships.keys() == wanted.keys(), "relationships: source coverage mismatch")
    for key, value in wanted.items():
        _compare(relationships[key], value, f"relationships/{key}")

    numeric_sources = {source: [] for source in FIELD_MAP}
    numeric_factors = {source: [] for source in FIELD_MAP}
    for oid, (bundle, ref, ds, record) in sources.items():
        obs = observations[oid]
        cid = source_ids(bundle, ds)
        _compare(obs, contexts[cid], f"observations/{oid}")
        if obs["segment_id"] is not None:
            segment = segments[obs["segment_id"]]
            _compare(obs, {k: v for k, v in segment.items() if k not in ("lower_fraction", "upper_fraction")}, f"observations/{oid}")
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
                indexed["cr6_fields"][key],
                tabular(
                    lineage(
                        revision, oid, target, bundle, ref, ds, record, source, meaning
                    )
                ),
                f"lineage/{oid}/{target}",
            )
            _compare(
                indexed["cr6_fields"][key],
                tabular(
                    interpretation(revision, oid, target, cell, meaning, catalogue)
                ),
                f"interpretations/{oid}/{target}",
            )
            numeric_sources[source].append({"observation_id": oid, source: cell.value})
            numeric_factors[source].append({"observation_id": oid, f"{source}__factor": meaning.unit_factor})
            _require(indexed["cr6_fields"][key]["mapping_revision_refs"] == [m.revision_id for m in meaning.mapping_refs], f"cr6_fields/{oid}/{target}: mapping_revision_refs differ")
        role, status = (
            next(iter(role_values)) if len(role_values) == 1 else (None, "conflicting")
        )
        _compare(
            obs,
            {"canonical_row_role": role, "row_role_status": status},
            f"observations/{oid}",
        )
    for source, target in FIELD_MAP.items():
        from decimal import Decimal

        rows = numeric_sources[source]
        for row in rows:
            if row[source] is not None:
                row[source] = Decimal(row[source])
        factor = f"{source}__factor"
        expected = convert_dataset(
            pl.DataFrame(rows, schema={"observation_id": pl.String, source: decimal_type([r[source] for r in rows], source)}),
            pl.DataFrame(numeric_factors[source], schema={"observation_id": pl.String, factor: decimal_type([r[factor] for r in numeric_factors[source]], source)}),
            ["observation_id"], {source: target},
        )
        actual = ma.relation(tables["cr6_observations"]).select("observation_id", ma.col(target).alias("actual"))
        compared = actual.join(expected, on="observation_id")
        different = compared.filter((ma.col("actual") != ma.col(target)) | (ma.col("actual").is_null() != ma.col(target).is_null()))
        _require(different.count_rows() == 0, f"observations.{target}: inconsistent converted value/value_state")
