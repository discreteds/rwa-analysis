"""Construct concrete components from already resolved execution settings."""

from rwa_analysis.domains.cr6.pipeline import Cr6Pipeline
from rwa_analysis.operations import ConformanceOperation, ExtractionOperation
from rwa_analysis.settings import OrganisationSettings, ProjectSettings
from rwa_analysis.storage.bronze import BronzeStore
from rwa_analysis.storage.consolidation import SilverConsolidator
from rwa_analysis.storage.silver import SilverStore
from rwa_analysis.workflow import OrganisationSession


def build_session(settings: OrganisationSettings) -> OrganisationSession:
    return OrganisationSession(
        extraction=ExtractionOperation(settings.project_root),
        bronze=BronzeStore(settings.bronze_root),
        conformance=ConformanceOperation(settings.project_root, Cr6Pipeline()),
        silver=SilverStore(
            settings.staging_path,
            settings.manifest_root,
            settings.organisation_id,
            settings.project_root,
            settings.bronze_root,
        ),
    )


def build_consolidator(settings: ProjectSettings) -> SilverConsolidator:
    return SilverConsolidator(
        SilverStore(
            settings.master_path,
            settings.manifest_root,
            "master",
            settings.project_root,
            settings.bronze_root,
        )
    )
