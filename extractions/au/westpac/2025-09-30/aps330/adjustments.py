"""Non-retail and operational overlays; October release is a subsequent event."""

from decimal import Decimal
from pathlib import Path

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.extraction.definitions import (
    OccurrenceLink,
    PhysicalBinding,
    PhysicalParameter,
)
from rwa_analysis.extraction.models import OccurrenceRef, SourceReference
from rwa_analysis.extraction.numerical_notes import (
    NumericalObservation,
    with_numerical_notes,
)


def extend(definition):
    catalogue = load_catalogue(
        Path(__file__).resolve().parents[5]
        / "catalogue/releases/adjustment-evidence-v1.json"
    )

    def reader(key, page, location, pattern):
        return PhysicalBinding(
            key + "@1",
            "line",
            (PhysicalParameter("pattern", pattern),),
            SourceReference(definition.document.document_id, page, str(page), location),
        )

    return with_numerical_notes(
        definition,
        (
            (
                reader(
                    "nonretail-credit-overlay",
                    6,
                    "Key metrics, RWA footnote b",
                    r"(?P<text>b\. Includes a \$(?P<number>[\d.]+) billion APRA RWA overlay[^\n]*\nretail exposures\.)",
                ),
                (
                    NumericalObservation(
                        id="nonretail-credit-overlay",
                        slot="number",
                        label="APRA non-retail RWA overlay",
                        unit="$ billion",
                        scale=Decimal(1000000000),
                        point="2025-09-30",
                        classification="credit_rwa_overlay",
                        portfolio="Small subset of non-retail exposures",
                    ),
                ),
            ),
            (
                reader(
                    "operational-capital-overlay",
                    15,
                    "OV1 footnote b",
                    r"(?P<text>b\. Includes \$(?P<number>[\d,]+) million capital overlay[^\n]*\n[^\n]*2025\.)",
                ),
                (
                    NumericalObservation(
                        id="operational-capital-overlay",
                        slot="number",
                        label="Operational risk capital overlay",
                        unit="$ million",
                        scale=Decimal(1000000),
                        point="2025-09-30",
                        classification="operational_capital_overlay",
                        portfolio="Group operational risk",
                        concept="capital.requirement@v1",
                    ),
                ),
            ),
            (
                reader(
                    "operational-overlay-release",
                    10,
                    "Operational risk capital overlays, 15 October 2025 release",
                    r"(?P<text>On 15 October 2025,[\s\S]*?The removal of the \$(?P<capital>[\d,]+) million capital overlay will mean\n"
                    r"Westpac’s CET1 capital ratio will increase by approximately (?P<bps>[\d.]+) basis points, reflecting a reduction in risk weighted\n"
                    r"assets of \$(?P<rwa>[\d,]+) million\.[^\n]*)",
                ),
                (
                    NumericalObservation(
                        id="operational-capital-removal",
                        slot="capital",
                        label="Capital overlay removed",
                        unit="$ million",
                        scale=Decimal(1000000),
                        point="2025-10-15",
                        classification="operational_capital_removal",
                        portfolio="Group operational risk",
                        concept="capital.requirement@v1",
                        links=(
                            OccurrenceLink(
                                "removes",
                                OccurrenceRef(
                                    definition.bundle_key,
                                    "rwa-adjustments",
                                    "cell",
                                    "operational-capital-overlay",
                                ),
                            ),
                        ),
                    ),
                    NumericalObservation(
                        id="operational-rwa-removal",
                        slot="rwa",
                        label="Reduction in risk weighted assets",
                        unit="$ million",
                        scale=Decimal(1000000),
                        point="2025-10-15",
                        classification="operational_rwa_removal",
                        portfolio="Group operational risk",
                        links=(
                            OccurrenceLink(
                                "same_removal_event",
                                OccurrenceRef(
                                    definition.bundle_key,
                                    "rwa-adjustments",
                                    "cell",
                                    "operational-capital-removal",
                                ),
                            ),
                        ),
                    ),
                    NumericalObservation(
                        id="cet1-ratio-increase",
                        slot="bps",
                        label="Approximate increase in CET1 capital ratio",
                        unit="basis points",
                        scale=Decimal("0.0001"),
                        point="2025-10-15",
                        classification="estimated_cet1_ratio_increase",
                        portfolio="Group",
                        concept="capital.cet1-ratio-change@v1",
                        result_kind="scalar",
                    ),
                ),
            ),
        ),
        semantic_definitions=tuple(
            m for m in catalogue.members if not m.revision_id.startswith("agreed.anz")
        ),
    )
