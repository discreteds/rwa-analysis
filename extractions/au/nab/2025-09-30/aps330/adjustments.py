"""NAB overview amounts and qualified overlay note; PDF 13 / printed 11."""

from decimal import Decimal

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
    bundle = definition.bundle_key

    def reader(key, location, pattern):
        return PhysicalBinding(
            key + "@1",
            "line",
            (PhysicalParameter("pattern", pattern),),
            SourceReference(definition.document.document_id, 13, "11", location),
        )

    def observation(key, slot, label, classification, portfolio, **kwargs):
        return NumericalObservation(
            id=key,
            slot=slot,
            label=label,
            unit=kwargs.pop("unit", "$ billion"),
            scale=Decimal(kwargs.pop("scale", "1000000000")),
            point="2025-09-30",
            classification=classification,
            portfolio=portfolio,
            **kwargs,
        )

    overlays = tuple(
        observation(
            key,
            slot,
            label,
            "credit_rwa_overlay",
            portfolio,
            links=()
            if key == "credit-overlay"
            else (
                OccurrenceLink(
                    "subset_of",
                    OccurrenceRef(bundle, "rwa-adjustments", "cell", "credit-overlay"),
                ),
            ),
        )
        for key, slot, label, portfolio in (
            (
                "credit-overlay",
                "all_credit",
                "Off-balance sheet measurement RWA overlay",
                "Credit risk excluding CCR",
            ),
            (
                "rbnz-credit-overlay",
                "rbnz",
                "RBNZ regulated banking subsidiary overlay",
                "RBNZ regulated banking subsidiary",
            ),
            (
                "corporate-credit-overlay",
                "corporate",
                "A-IRB corporate overlay",
                "A-IRB corporate",
            ),
        )
    )
    columns = (
        (
            "mortgage-overview-ead",
            "credit_ead",
            "EaD: Credit risk",
            "exposure.at-default@v1",
        ),
        (
            "mortgage-overview-ccr-ead",
            "ccr_ead",
            "EaD: Counterparty credit risk",
            "exposure.at-default@v1",
        ),
        (
            "mortgage-overview-total-ead",
            "total_ead",
            "EaD: Total",
            "exposure.at-default@v1",
        ),
        (
            "mortgage-overview-rwa",
            "credit_rwa",
            "RWA: Credit risk",
            "capital.risk-weighted-assets@v1",
        ),
        (
            "mortgage-overview-ccr-rwa",
            "ccr_rwa",
            "RWA: Counterparty credit risk",
            "capital.risk-weighted-assets@v1",
        ),
        (
            "mortgage-overview-total-rwa",
            "total_rwa",
            "RWA: Total",
            "capital.risk-weighted-assets@v1",
        ),
    )
    row = tuple(
        observation(
            key,
            slot,
            label,
            "reported_total",
            "A-IRB residential mortgage",
            unit="$m",
            scale="1000000",
            concept=concept,
            source_form="table_body",
            attributes=(SemanticAttribute("AUD", "established", name="currency"),),
        )
        for key, slot, label, concept in columns
    )
    return with_numerical_notes(
        definition,
        (
            (
                reader(
                    "credit-overlay-note",
                    "Overview, footnote 2",
                    r"(?P<text>\(2\) Credit RWA \(excluding CCR\) includes an RWA overlay[^\n]*\$(?P<all_credit>[\d.]+) billion\.[\s\S]*?"
                    r"RBNZ regulated banking subsidiary \(\$(?P<rbnz>[\d.]+) billion\) and corporate exposures under the A-IRB approach \(\$(?P<corporate>[\d.]+) billion\)\.)",
                ),
                overlays,
            ),
            (
                reader(
                    "mortgage-overview-row",
                    "Overview, A-IRB Residential mortgage row",
                    r"^(?P<text>Residential mortgage "
                    + " ".join(rf"(?P<{slot}>[\d,]+|-)" for _, slot, *_ in columns)
                    + r")$",
                ),
                row,
            ),
            (
                reader(
                    "group-output-floor",
                    "Overview, Floor adjustment",
                    r"^(?P<text>Floor adjustment (?P<number>[\d,]+))$",
                ),
                (
                    observation(
                        "group-output-floor",
                        "number",
                        "Floor adjustment",
                        "group_output_floor",
                        "Level 2 group",
                        unit="$m",
                        scale="1000000",
                        source_form="table_body",
                    ),
                ),
            ),
        ),
    )
