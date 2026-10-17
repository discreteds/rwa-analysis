"""June mortgage floor and its overview row, reviewed against PDF page 18."""

from decimal import Decimal
from pathlib import Path

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import SemanticAttribute
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
    document = definition.document.document_id
    bundle = definition.bundle_key

    def reader(key, location, pattern):
        return PhysicalBinding(
            key + "@1",
            "line",
            (PhysicalParameter("pattern", pattern),),
            SourceReference(document, 18, "18", location),
        )

    included = (SemanticAttribute("included", "established", name="overlay_treatment"),)
    floor = NumericalObservation(
        id="mortgage-floor",
        slot="number",
        label="Self-imposed residential mortgage risk weight floor",
        unit="$ billion",
        scale=Decimal(1000000000),
        point="2025-06-30",
        classification="mortgage_floor",
        portfolio="AIRB residential mortgage",
        attributes=included,
        links=(
            OccurrenceLink(
                "included_in",
                OccurrenceRef(
                    bundle, "rwa-adjustments", "cell", "mortgage-overview-rwa"
                ),
            ),
            OccurrenceLink(
                "included_in",
                OccurrenceRef(
                    bundle,
                    "cr6-residential-mortgages",
                    "cell",
                    "portfolio-aggregate/rwa",
                ),
            ),
        ),
    )
    columns = (
        (
            "mortgage-overview-ead",
            "ead",
            "EAD $M",
            "2025-06-30",
            "exposure.at-default@v1",
            "$M",
            "1000000",
        ),
        (
            "mortgage-overview-ead-share",
            "eadshare",
            "EAD %",
            "2025-06-30",
            "ratio.reported-share@v1",
            "%",
            "0.01",
        ),
        (
            "mortgage-overview-rwa",
            "rwa",
            "RWA $M",
            "2025-06-30",
            "capital.risk-weighted-assets@v1",
            "$M",
            "1000000",
        ),
        (
            "mortgage-overview-rwa-share",
            "rwashare",
            "RWA %",
            "2025-06-30",
            "ratio.reported-share@v1",
            "%",
            "0.01",
        ),
        (
            "mortgage-comparative-ead",
            "previous_ead",
            "EAD $M",
            "2024-12-31",
            "exposure.at-default@v1",
            "$M",
            "1000000",
        ),
        (
            "mortgage-comparative-ead-share",
            "previous_eadshare",
            "EAD %",
            "2024-12-31",
            "ratio.reported-share@v1",
            "%",
            "0.01",
        ),
        (
            "mortgage-comparative-rwa",
            "previous_rwa",
            "RWA $M",
            "2024-12-31",
            "capital.risk-weighted-assets@v1",
            "$M",
            "1000000",
        ),
        (
            "mortgage-comparative-rwa-share",
            "previous_rwashare",
            "RWA %",
            "2024-12-31",
            "ratio.reported-share@v1",
            "%",
            "0.01",
        ),
    )
    row = tuple(
        NumericalObservation(
            id=key,
            slot=slot,
            label=label,
            unit=unit,
            scale=Decimal(scale),
            point=point,
            classification="reported_total",
            portfolio="AIRB residential mortgage",
            concept=concept,
            result_kind="scalar" if unit == "%" else "money",
            source_form="table_body",
            attributes=included if key == "mortgage-overview-rwa" else (),
        )
        for key, slot, label, point, concept, unit, scale in columns
    )
    catalogue = load_catalogue(
        Path(__file__).resolve().parents[5]
        / "catalogue/releases/adjustment-evidence-v1.json"
    )
    return with_numerical_notes(
        definition,
        (
            (
                reader(
                    "mortgage-floor",
                    "CRE(e), footnote 2",
                    r"^(?P<text>2 Includes a \$(?P<number>[\d.]+) billion self-imposed residential mortgage risk weight floor[^\n]*)$",
                ),
                (floor,),
            ),
            (
                reader(
                    "mortgage-overview-row",
                    "CRE(e), AIRB Residential mortgage row; June/December columns",
                    r"^(?P<text>Residential mortgage ² "
                    + " ".join(rf"(?P<{slot}>[\d,.]+)" for _, slot, *_ in columns)
                    + r")$",
                ),
                row,
            ),
        ),
        semantic_definitions=tuple(
            m for m in catalogue.members if m.revision_id == "ratio.reported-share@v1"
        ),
    )
