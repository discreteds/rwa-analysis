"""Concrete source selection and conformance operations assembled for a session."""

from dataclasses import dataclass, fields
from pathlib import Path

import mountainash as ma

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.domains.cr6.projection import project_cr6
from rwa_analysis.domains.cr9.projection import project_cr9
from rwa_analysis.domains.source_tables.legacy import domain_bindings
from rwa_analysis.domains.source_tables.models import SourceTableOutput
from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline
from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.extraction.definitions import CapturedBundle
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
    ) -> tuple[ExtractionBundle | CapturedBundle, ...]:
        return tuple(
            run_extractor(
                self.project_root / doc.extractor_path, self.project_root / doc.pdf_path
            )
            for doc in documents
        )


@dataclass(frozen=True)
class ConformanceOperation:
    project_root: Path

    def conform(
        self, inputs: tuple[LoadedBronze, ...], catalogue: CatalogueSelection
    ) -> SilverCandidate:
        release = load_catalogue(self.project_root / catalogue.release_path)
        source = SourceTablePipeline().conform(inputs, release)
        bindings = tuple(b for item in inputs for b in domain_bindings(item.bundle))
        native_ids = [
            f"{item.bundle.bundle_key}/{ds.id}"
            for item in inputs
            for ds in item.bundle.datasets
            if isinstance(ds, SourceTable)
        ] + [
            item.bundle.bundle_key
            for item in inputs
            if isinstance(item.bundle, CapturedBundle)
        ]
        native = SourceTableOutput(
            **{
                f.name: getattr(source, f.name).filter(
                    ma.col("table_id").is_in(native_ids)
                )
                for f in fields(SourceTableOutput)
            }
        )
        return SilverCandidate(
            project_cr6(source, bindings),
            project_cr9(source, bindings),
            RebuildSelection(
                bronze_refs=tuple(item.ref for item in inputs), catalogue=catalogue
            ),
            release.id,
            native,
        )
