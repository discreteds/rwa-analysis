"""Organisation publication and readback through one owned DuckDB transaction."""

from dataclasses import dataclass, replace
from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.domains.cr6.contracts import TABLES
from rwa_analysis.domains.cr6.models import Cr6Output
from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.storage.bronze import BronzeStore
from rwa_analysis.storage.manifests import (
    RebuildManifest,
    RebuildSelection,
    identifier,
    retain_manifest,
)


@dataclass(frozen=True)
class SilverCandidate:
    cr6: Cr6Output
    selection: RebuildSelection
    catalogue_release_id: str


@dataclass(frozen=True)
class Publication:
    database: Path
    manifest_path: Path
    revision: str


@dataclass(frozen=True)
class SilverStore:
    database: Path
    manifest_root: Path
    organisation_id: str
    project_root: Path
    bronze_root: Path

    def publish(self, candidate: SilverCandidate, revision: str) -> Publication:
        manifest_path = (
            self.manifest_root
            / identifier(self.organisation_id)
            / f"{identifier(revision)}.json"
        )
        manifest = RebuildManifest(
            revision=revision,
            organisation_id=self.organisation_id,
            selection=candidate.selection,
            catalogue_release_id=candidate.catalogue_release_id,
            bronze_root=self.bronze_root,
            project_root=self.project_root,
        )
        output = replace(
            candidate.cr6,
            **{
                table.member: getattr(candidate.cr6, table.member).with_columns(
                    ma.lit(revision).alias("silver_revision_id")
                )
                for table in TABLES
            },
        )
        retain_manifest(manifest_path, manifest)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        marker = pl.DataFrame(
            {
                "silver_revision_id": [revision],
                "manifest_path": [str(manifest_path)],
                "schema_version": [manifest.schema_version],
            }
        )
        with IbisBackend(dialect="duckdb", database=str(self.database)) as db:
            for namespace in ("silver", "ops"):
                if namespace not in db.list_namespaces():
                    db.ibis_connection().create_database(namespace)
            with db.transaction():
                for table in TABLES:
                    db.create_table(
                        table.table,
                        getattr(output, table.member).to_arrow(),
                        namespace="silver",
                        overwrite=True,
                    )
                db.create_table(
                    "silver_publication",
                    marker.to_arrow(),
                    namespace="ops",
                    overwrite=True,
                )
        return Publication(self.database, manifest_path, revision)

    def read_manifest(self, publication: Publication) -> RebuildManifest:
        return RebuildManifest.model_validate_json(
            publication.manifest_path.read_bytes()
        )

    def read_sources(self, publication: Publication) -> tuple[ExtractionBundle, ...]:
        manifest = self.read_manifest(publication)
        store = BronzeStore(manifest.bronze_root)
        return tuple(store.load(ref).bundle for ref in manifest.selection.bronze_refs)

    def read(self, publication: Publication) -> Cr6Output:
        with IbisBackend(
            dialect="duckdb", database=str(publication.database), read_only=True
        ) as db:
            marker = ma.relation(db.table("silver_publication", namespace="ops"))
            if marker.item("silver_revision_id") != publication.revision:
                raise ValueError(
                    "Database publication revision differs from selected publication"
                )
            # Materialize before closing the connection, retaining exact Decimal values.
            return Cr6Output(
                **{
                    table.member: ma.relation(
                        ma.relation(
                            db.table(table.table, namespace="silver")
                        ).to_polars()
                    )
                    for table in TABLES
                }
            )
