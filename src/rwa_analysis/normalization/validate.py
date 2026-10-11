"""Silver transition boundary: types, identity, coverage and retained references."""

from dataclasses import fields, is_dataclass

import mountainash as ma
import polars as pl

from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef
from rwa_analysis.contracts.frames import conform_frame

from .cr6 import source_ids
from .models import FIELD_KEY, FIELD_MAP, KEYS, SCHEMAS


def require_empty(relation, message):
    if relation.count_rows():
        raise ValueError(message)


def contract(name, data, revision):
    if data.schema != SCHEMAS[name]:
        raise ValueError(f"{name}: physical schema mismatch")
    scalar = {key: dtype for key, dtype in data.schema.items() if not dtype.is_nested()}
    kinds = {pl.Date: "date", pl.Boolean: "boolean", pl.Int64: "integer"}
    spec = ma.TypeSpec.from_frictionless(
        {
            "fields": [
                {
                    "name": key,
                    "type": "number"
                    if dtype.is_decimal()
                    else kinds.get(dtype, "string"),
                    "constraints": {"required": key in KEYS[name]},
                }
                for key, dtype in scalar.items()
            ],
            "primaryKey": KEYS[name],
            "missingValues": [],
        }
    )
    relation = ma.relation(data)
    try:
        conform_frame(relation.select(*scalar).to_polars(), spec)
    except Exception as error:
        raise ValueError(f"{name}: frame contract: {error}") from error
    require_empty(
        relation.filter(ma.col("silver_revision_id") != revision),
        f"{name}: wrong revision",
    )


def same_keys(actual, expected, keys, name):
    require_empty(
        actual.join(expected, on=keys, how="anti"),
        f"{name}: unexpected source coverage",
    )
    require_empty(
        expected.join(actual, on=keys, how="anti"), f"{name}: missing source coverage"
    )


def validate_support(value, catalogue, source_sets, visited):
    """Nested research evidence is object metadata, not a numeric ETL pass."""
    if isinstance(value, EvidenceRef):
        key = (value.bundle_key, value.document_id, value.dataset_id, value.kind)
        if value.ref_id not in source_sets.get(key, set()):
            raise ValueError(f"interpretations: absent source evidence {value}")
    elif isinstance(value, RevisionRef):
        if value not in visited:
            visited.add(value)
            validate_support(catalogue.member(value), catalogue, source_sets, visited)
    elif is_dataclass(value):
        for field in fields(value):
            if field.name not in ("supersedes_refs", "overrides_refs"):
                validate_support(
                    getattr(value, field.name), catalogue, source_sets, visited
                )
    elif isinstance(value, tuple):
        for item in value:
            validate_support(item, catalogue, source_sets, visited)


def validate_candidate(
    candidate, bundles, bronze_refs, catalogue, *, evidence_bundles=()
):
    """Validate the built candidate once; never re-run its transformations."""
    if not candidate.revision_id or set(candidate.tables) != set(SCHEMAS):
        raise ValueError("Expected a revision and three Silver tables")
    for name, data in candidate.tables.items():
        contract(name, data, candidate.revision_id)
    observations = ma.relation(candidate.tables["cr6_observations"])
    field_rows = ma.relation(candidate.tables["cr6_fields"])
    relationships = ma.relation(candidate.tables["cr6_relationships"])

    source_keys = pl.DataFrame(
        [
            {
                "silver_revision_id": candidate.revision_id,
                "observation_id": source_ids(bundle, ds, record),
            }
            for bundle in bundles
            for ds in bundle.datasets
            for record in ds.records
        ],
        schema={key: pl.String for key in KEYS["cr6_observations"]},
    )
    expected = ma.relation(source_keys)
    same_keys(observations, expected, KEYS["cr6_observations"], "observations")
    expected_fields = expected.join(
        pl.DataFrame({"field_key": list(FIELD_MAP.values())}), how="cross"
    )
    same_keys(field_rows, expected_fields, FIELD_KEY, "cr6_fields")
    for endpoint in ("parent_observation_id", "child_observation_id"):
        require_empty(
            relationships.join(
                observations,
                left_on=["silver_revision_id", endpoint],
                right_on=KEYS["cr6_observations"],
                how="anti",
            ),
            f"relationships: unresolved {endpoint}",
        )

    # A present field must have a value; legitimate source missingness and
    # unresolved conversions remain null. No second implementation of the maths.
    for target in FIELD_MAP.values():
        selected = field_rows.filter(ma.col("field_key") == target).join(
            observations.select(*KEYS["cr6_observations"], target),
            on=KEYS["cr6_observations"],
        )
        require_empty(
            selected.filter(
                (ma.col("value_state") == "present") != ma.col(target).is_not_null()
            ),
            f"observations.{target}: inconsistent value_state",
        )

    revisions = pl.DataFrame(
        {"revision_ref": [m.revision_id for m in catalogue.members]}
    )
    for column in (
        "concept_revision_ref",
        "measure_revision_ref",
        "result_unit_revision_ref",
    ):
        require_empty(
            field_rows.select(column)
            .drop_nulls()
            .join(revisions, left_on=column, right_on="revision_ref", how="anti"),
            f"interpretations: unresolved {column}",
        )
    mappings = (
        field_rows.select("mapping_revision_refs")
        .explode("mapping_revision_refs")
        .drop_nulls()
    )
    require_empty(
        mappings.join(
            revisions,
            left_on="mapping_revision_refs",
            right_on="revision_ref",
            how="anti",
        ),
        "cr6_fields: unresolved mapping_revision_refs",
    )

    source_sets = {}
    for bundle in (*bundles, *evidence_bundles):
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
    used = {row[0] for row in mappings.to_tuples()}
    validate_support(
        tuple(m for m in catalogue.members if m.revision_id in used),
        catalogue,
        source_sets,
        set(),
    )
