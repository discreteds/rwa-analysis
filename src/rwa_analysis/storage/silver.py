"""Full, validated selected-scope replacement in one owned DuckDB transaction."""

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.normalization.cr6 import conform_cr6
from rwa_analysis.normalization.models import SilverCandidate
from rwa_analysis.normalization.validate import validate_candidate
from rwa_analysis.storage.manifests import load_manifest

TABLE_ORDER = (
    "contexts",
    "segments",
    "observations",
    "interpretations",
    "applied_mappings",
    "lineage",
    "relationships",
)


def rebuild(manifest_path: Path, project_root: Path, warehouse_path: Path) -> str:
    manifest, bundles, catalogue, evidence_bundles = load_manifest(
        manifest_path, project_root
    )
    request = manifest.request
    candidate = conform_cr6(
        bundles,
        request.bronze_refs,
        catalogue,
        request.revision_id,
        evidence_bundles=evidence_bundles,
    )
    publish_candidate(candidate, manifest_path, warehouse_path)
    return request.revision_id


def publish_candidate(
    candidate: SilverCandidate, manifest_path: Path, warehouse_path: Path
) -> None:
    # Public callers cannot bypass source-aware validation by supplying frames.
    manifest_path = manifest_path.resolve(strict=True)
    root = manifest_path.parent.parent.parent
    manifest, bundles, catalogue, evidence_bundles = load_manifest(manifest_path, root)
    request = manifest.request
    if candidate.revision_id != request.revision_id:
        raise ValueError("Candidate revision differs from manifest")
    if set(candidate.tables) != set(TABLE_ORDER):
        raise ValueError("Expected exactly seven Silver tables")
    validate_candidate(
        candidate,
        bundles,
        request.bronze_refs,
        catalogue,
        evidence_bundles=evidence_bundles,
    )
    reference = manifest_path.relative_to(root).as_posix()
    marker = pl.DataFrame(
        [
            {
                "silver_revision_id": candidate.revision_id,
                "manifest_path": reference,
                "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
                "catalogue_release_id": catalogue.id,
                "schema_version": request.conformance_schema_version,
                "published_at": datetime.now(UTC),
                "status": "published",
            }
        ],
        schema={
            "silver_revision_id": pl.String,
            "manifest_path": pl.String,
            "manifest_sha256": pl.String,
            "catalogue_release_id": pl.String,
            "schema_version": pl.String,
            "published_at": pl.Datetime("us", "UTC"),
            "status": pl.String,
        },
    )
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    with IbisBackend(dialect="duckdb", database=str(warehouse_path)) as db:
        raw = db.raw_driver_connection()
        raw.execute("CREATE SCHEMA IF NOT EXISTS silver")
        raw.execute("CREATE SCHEMA IF NOT EXISTS ops")
        exists = raw.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'ops' AND table_name = 'silver_publication'"
        ).fetchone()[0]
        if exists:
            previous = pl.from_arrow(
                db.table("silver_publication", namespace="ops").to_pyarrow()
            )
            if (
                previous.height == 1
                and previous["silver_revision_id"][0] == candidate.revision_id
            ):
                if (
                    previous.drop("published_at").to_dicts()
                    != marker.drop("published_at").to_dicts()
                ):
                    raise ValueError(
                        "Published revision has a different manifest selection"
                    )
                return
        with db.transaction():
            for name in TABLE_ORDER:
                db.create_table(
                    name,
                    candidate.tables[name].to_arrow(),
                    namespace="silver",
                    overwrite=True,
                )
            db.create_table(
                "silver_publication", marker.to_arrow(), namespace="ops", overwrite=True
            )
