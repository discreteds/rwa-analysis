"""Full master replacement from explicitly selected organisation publications."""

from dataclasses import dataclass

import mountainash as ma
import polars as pl
from mountainash.typespec.converters import to_polars_schema

from rwa_analysis.domains.cr6.contracts import TABLES
from rwa_analysis.domains.cr6.models import Cr6Output
from rwa_analysis.domains.cr6.reconstruction import reconstruct_cr6
from rwa_analysis.storage.bronze import BronzeStore
from rwa_analysis.storage.manifests import (
    MasterManifest,
    RebuildManifest,
    identifier,
    retain_manifest,
)
from rwa_analysis.storage.silver import Publication, SilverStore


@dataclass(frozen=True)
class SilverConsolidator:
    store: SilverStore

    def consolidate(
        self, publications: tuple[Publication, ...], *, revision: str
    ) -> Publication:
        outputs = tuple(self.store.read(publication) for publication in publications)
        combined = Cr6Output(
            **{
                table.member: ma.concat(
                    [getattr(output, table.member) for output in outputs]
                )
                if outputs
                else ma.relation(pl.DataFrame(schema=to_polars_schema(table.spec)))
                for table in TABLES
            }
        )
        manifest = MasterManifest(
            revision=revision,
            staging_manifests=tuple(p.manifest_path.resolve() for p in publications),
        )
        path = self.store.manifest_root / "master" / f"{identifier(revision)}.json"
        retain_manifest(path, manifest)
        return self.store.write(combined, path, revision, manifest.schema_version)

    def read_manifest(self, publication: Publication) -> MasterManifest:
        return MasterManifest.model_validate_json(
            publication.manifest_path.read_bytes()
        )

    def reconstruct(self, publication: Publication) -> dict[str, pl.DataFrame]:
        bundles = []
        for path in self.read_manifest(publication).staging_manifests:
            source = RebuildManifest.model_validate_json(path.read_bytes())
            store = BronzeStore(source.bronze_root)
            bundles.extend(
                store.load(ref).bundle for ref in source.selection.bronze_refs
            )
        return reconstruct_cr6(self.store.read(publication), tuple(bundles))
