"""Concrete source selection and conformance operations assembled for a session."""

from dataclasses import dataclass, replace
from pathlib import Path

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.domains.cr6.pipeline import Cr6Pipeline
from rwa_analysis.domains.cr9.pipeline import Cr9Pipeline
from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.extraction.source_tables import SourceTable
from rwa_analysis.storage.bronze import LoadedBronze
from rwa_analysis.storage.manifests import CatalogueSelection, RebuildSelection
from rwa_analysis.storage.silver import SilverCandidate


@dataclass(frozen=True)
class DocumentSelection:
    extractor_path: str
    pdf_path: str


@dataclass(frozen=True)
class ExtractionOperation:
    project_root: Path

    def extract(
        self, documents: tuple[DocumentSelection, ...]
    ) -> tuple[ExtractionBundle, ...]:
        return tuple(
            run_extractor(
                self.project_root / doc.extractor_path, self.project_root / doc.pdf_path
            )
            for doc in documents
        )


@dataclass(frozen=True)
class ConformanceOperation:
    project_root: Path
    cr6: Cr6Pipeline
    cr9: Cr9Pipeline

    def conform(
        self, inputs: tuple[LoadedBronze, ...], catalogue: CatalogueSelection
    ) -> SilverCandidate:
        release = load_catalogue(self.project_root / catalogue.release_path)
        native_inputs = tuple(
            replace(
                item,
                bundle=replace(
                    item.bundle,
                    datasets=tuple(
                        ds for ds in item.bundle.datasets if isinstance(ds, SourceTable)
                    ),
                ),
            )
            for item in inputs
        )
        return SilverCandidate(
            self.cr6.conform(inputs, release),
            self.cr9.conform(inputs, release),
            RebuildSelection(
                bronze_refs=tuple(item.ref for item in inputs), catalogue=catalogue
            ),
            release.id,
            SourceTablePipeline().conform(native_inputs, release),
        )
