"""Explicit stage sequencing; operations own the work."""

from dataclasses import dataclass

import polars as pl

from rwa_analysis.domains.cr6.reconstruction import reconstruct_cr6
from rwa_analysis.domains.cr9.reconstruction import reconstruct_cr9
from rwa_analysis.domains.source_tables.reconstruction import reconstruct_source_tables
from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.operations import (
    ConformanceOperation,
    DocumentSelection,
    ExtractionOperation,
)
from rwa_analysis.storage.bronze import BronzeRef, BronzeStore, LoadedBronze
from rwa_analysis.storage.manifests import CatalogueSelection
from rwa_analysis.storage.silver import Publication, SilverCandidate, SilverStore


@dataclass(frozen=True)
class RunResult:
    publication: Publication
    tables: dict[str, pl.DataFrame]
    bundles: tuple[ExtractionBundle, ...]


@dataclass(frozen=True)
class OrganisationSession:
    extraction: ExtractionOperation
    bronze: BronzeStore
    conformance: ConformanceOperation
    silver: SilverStore

    def extract(
        self, documents: tuple[DocumentSelection, ...]
    ) -> tuple[ExtractionBundle, ...]:
        return self.extraction.extract(documents)

    def save_bronze(
        self, bundles: tuple[ExtractionBundle, ...], run_name: str
    ) -> tuple[BronzeRef, ...]:
        return tuple(self.bronze.save(bundle, run_name) for bundle in bundles)

    def load_bronze(self, refs: tuple[BronzeRef, ...]) -> tuple[LoadedBronze, ...]:
        return tuple(self.bronze.load(ref) for ref in refs)

    def conform(
        self, inputs: tuple[LoadedBronze, ...], *, catalogue: CatalogueSelection
    ) -> SilverCandidate:
        return self.conformance.conform(inputs, catalogue)

    def publish(self, candidate: SilverCandidate, revision: str) -> Publication:
        return self.silver.publish(candidate, revision)

    def reconstruct(self, publication: Publication) -> dict[str, pl.DataFrame]:
        output = self.silver.read(publication)
        bundles = self.silver.read_sources(publication)
        return {
            **reconstruct_cr6(output.cr6, bundles),
            **reconstruct_cr9(output.cr9, bundles),
            **{
                key: value.frame
                for key, value in reconstruct_source_tables(
                    output.source_tables
                ).items()
            },
        }

    def run(
        self,
        *,
        documents: tuple[DocumentSelection, ...],
        catalogue: CatalogueSelection,
        run_name: str,
        revision: str,
    ) -> RunResult:
        bundles = self.extract(documents)
        refs = self.save_bronze(bundles, run_name)
        inputs = self.load_bronze(refs)
        candidate = self.conform(inputs, catalogue=catalogue)
        publication = self.publish(candidate, revision)
        return RunResult(
            publication,
            self.reconstruct(publication),
            tuple(item.bundle for item in inputs),
        )
