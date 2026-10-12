"""Organisation publication and readback through one owned DuckDB transaction."""

from dataclasses import dataclass, field, replace
from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash_data import IbisBackend

from rwa_analysis.domains.cr6.models import Cr6Output
from rwa_analysis.domains.cr9.models import Cr9Output
from rwa_analysis.domains.source_tables.contracts import empty_output
from rwa_analysis.domains.source_tables.models import SourceTableOutput
from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.storage.bronze import BronzeStore
from rwa_analysis.storage.manifests import (
    RebuildManifest,
    RebuildSelection,
    identifier,
    retain_manifest,
)
from rwa_analysis.storage.tables import DOMAINS


@dataclass(frozen=True)
class SilverOutput:
    cr6: Cr6Output
    cr9: Cr9Output
    source_tables: SourceTableOutput = field(default_factory=empty_output)


@dataclass(frozen=True)
class SilverCandidate:
    cr6: Cr6Output
    cr9: Cr9Output
    selection: RebuildSelection
    catalogue_release_id: str
    source_tables: SourceTableOutput = field(default_factory=empty_output)


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
        output = SilverOutput(
            **{
                domain: replace(
                    getattr(candidate, domain),
                    **{
                        table.member: getattr(
                            getattr(candidate, domain), table.member
                        ).with_columns(ma.lit(revision).alias("silver_revision_id"))
                        for table in tables
                    },
                )
                for domain, _, tables in DOMAINS
            }
        )
        retain_manifest(manifest_path, manifest)
        return self.write(output, manifest_path, revision, manifest.schema_version)

    def write(
        self,
        output: SilverOutput,
        manifest_path: Path,
        revision: str,
        schema_version: str,
    ) -> Publication:
        """Replace the declared tables atomically, retaining the supplied row revisions."""
        self.database.parent.mkdir(parents=True, exist_ok=True)
        marker = pl.DataFrame(
            {
                "silver_revision_id": [revision],
                "manifest_path": [str(manifest_path)],
                "schema_version": [schema_version],
            }
        )
        with IbisBackend(dialect="duckdb", database=str(self.database)) as db:
            for namespace in ("silver", "ops"):
                if namespace not in db.list_namespaces():
                    db.ibis_connection().create_database(namespace)
            with db.transaction():
                for domain, _, tables in DOMAINS:
                    for table in tables:
                        db.create_table(
                            table.table,
                            getattr(getattr(output, domain), table.member).to_pyarrow(),
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

    def read(self, publication: Publication) -> SilverOutput:
        with IbisBackend(
            dialect="duckdb", database=str(publication.database), read_only=True
        ) as db:
            # Materialize before closing the connection, retaining exact Decimal values.
            return SilverOutput(
                **{
                    domain: output_type(
                        **{
                            table.member: ma.relation(
                                ma.relation(
                                    db.table(table.table, namespace="silver")
                                ).to_polars()
                            )
                            for table in tables
                        }
                    )
                    for domain, output_type, tables in DOMAINS
                }
            )
