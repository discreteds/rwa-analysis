"""ANZ adjustment statements and supporting overview row, not band allocations."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef, SemanticAttribute
from rwa_analysis.extraction.definitions import (
    ContextDefinition,
    OccurrenceLink,
    PhysicalBinding,
    PhysicalParameter,
)
from rwa_analysis.extraction.models import OccurrenceRef, SourceReference
from rwa_analysis.extraction.numerical_notes import (
    NumericalObservation,
    with_numerical_notes,
)
from rwa_analysis.extraction.temporal import TemporalDescriptor


def extend(definition):
    bundle, document = definition.bundle_key, definition.document.document_id
    catalogue = load_catalogue(
        Path(__file__).resolve().parents[5]
        / "catalogue/releases/adjustment-evidence-v1.json"
    )

    def reader(key, page, location, pattern):
        return PhysicalBinding(
            key + "@1",
            "line",
            (PhysicalParameter("pattern", pattern),),
            SourceReference(document, page, str(page), location),
        )

    def observation(key, slot, label, classification, portfolio, **kwargs):
        return NumericalObservation(
            id=key,
            slot=slot,
            label=label,
            unit=kwargs.pop("unit", "$ billion"),
            scale=Decimal(kwargs.pop("scale", "1000000000")),
            point=kwargs.pop("point", "2025-09-30"),
            classification=classification,
            portfolio=portfolio,
            **kwargs,
        )

    decision = RevisionRef("decision", "agreed.anz-2025-aggregate-overlay@v1")
    evidence = (
        EvidenceRef(
            bundle, document, "rwa-adjustments", "comment", "mortgage-pd-overlay@1"
        ),
    )
    accepted = SemanticAttribute(
        "included",
        "established",
        evidence_refs=evidence,
        decision_refs=(decision,),
        name="overlay_treatment",
    )
    mortgage = observation(
        "mortgage-pd-overlay",
        "number",
        "Australian Residential Mortgages PD model overlay",
        "mortgage_pd_overlay",
        "Australian AIRB residential mortgages",
        attributes=(accepted,),
        temporal=(
            TemporalDescriptor(
                "effective_from",
                "introduced from 30 June 2024 reporting period",
                point="2024-06-30",
                point_status="established",
                evidence=(SourceReference(document, 19, "19", "Overview, footnote 2"),),
            ),
        ),
        links=(
            OccurrenceLink(
                "included_in",
                OccurrenceRef(
                    bundle, "rwa-adjustments", "cell", "mortgage-overview-rwa"
                ),
            ),
            OccurrenceLink(
                "included_in_by_interpretation",
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
            "credit_ead",
            "EAD: Credit risk",
            "exposure.at-default@v1",
        ),
        (
            "mortgage-overview-ccr-ead",
            "ccr_ead",
            "EAD: Counterparty credit risk",
            "exposure.at-default@v1",
        ),
        (
            "mortgage-overview-total-ead",
            "total_ead",
            "EAD: Total",
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
            "AIRB residential mortgages",
            unit="$m",
            scale="1000000",
            concept=concept,
            source_form="table_body",
        )
        for key, slot, label, concept in columns
    )
    operational = tuple(
        observation(
            "operational-" + kind + "-overlay" + suffix,
            slot,
            "Operational risk " + kind + " overlay",
            "operational_" + kind + "_overlay",
            "Level 1 and Level 2",
            point=point,
            unit=unit,
            scale=scale,
            concept="capital.requirement@v1"
            if kind == "capital"
            else "capital.risk-weighted-assets@v1",
        )
        for suffix, point in (("", "2025-09-30"), ("-june", "2025-06-30"))
        for kind, slot, unit, scale in (
            ("rwa", "rwa", "$ billion", "1000000000"),
            ("capital", "capital", "$ billion", "1000000000"),
        )
    )
    prior = tuple(
        observation(
            "operational-" + kind + "-overlay-march",
            slot,
            "Operational risk " + kind + " overlay",
            "operational_" + kind + "_overlay",
            "Level 1 and Level 2",
            point="2025-03-31",
            unit=unit,
            scale=scale,
            concept="capital.requirement@v1"
            if kind == "capital"
            else "capital.risk-weighted-assets@v1",
        )
        for kind, slot, unit, scale in (
            ("rwa", "rwa", "$ billion", "1000000000"),
            ("capital", "capital", "$ million", "1000000"),
        )
    )
    result = with_numerical_notes(
        definition,
        (
            (
                reader(
                    "mortgage-pd-overlay",
                    19,
                    "Overview, footnote 2",
                    r"^(?P<text>2 Includes a \$(?P<number>[\d.]+) billion RWA overlay relating to the Australian Residential Mortgages PD model[^\n]*)$",
                ),
                (mortgage,),
            ),
            (
                reader(
                    "mortgage-overview-row",
                    19,
                    "Overview, AIRB row 4, Residential mortgage",
                    r"^(?P<text>4 of which Residential mortgage2 "
                    + " ".join(rf"(?P<{slot}>[\d,]+|-)" for _, slot, *_ in columns)
                    + r")$",
                ),
                row,
            ),
            (
                reader(
                    "group-output-floor",
                    19,
                    "Overview, row 26, Floor adjustment",
                    r"^(?P<text>26 Floor adjustment (?P<number>[\d,]+))$",
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
            (
                reader(
                    "operational-overlay",
                    17,
                    "OV1 footnote 3, September and June",
                    r"^(?P<text>3 Reporting periods[^\n]*include \$(?P<rwa>[\d.]+) billion \(\$(?P<capital>[\d.]+) billion capital\)[^\n]*)$",
                ),
                operational,
            ),
            (
                reader(
                    "operational-overlay-march",
                    17,
                    "OV1 footnote 3, March comparative",
                    r"^(?P<text>Corresponding overlay for 31 March 2025 was \$(?P<rwa>[\d.]+) billion RWA \(\$(?P<capital>[\d.]+) million capital\)\.)$",
                ),
                prior,
            ),
        ),
        semantic_definitions=catalogue.members,
    )
    cid = "agreed.anz-cr6-aggregate-overlay-context@v1"
    snapshot = result.snapshot
    return replace(
        result,
        snapshot=replace(
            snapshot,
            contexts=(*snapshot.contexts, ContextDefinition(cid, (accepted,))),
            occurrences=tuple(
                replace(b, context_refs=(*b.context_refs, cid))
                if b.ref.scope == "cr6-residential-mortgages"
                and b.ref.kind == "cell"
                and b.ref.local_id
                in ("portfolio-aggregate/rwa", "portfolio-aggregate/rwa_density")
                else b
                for b in snapshot.occurrences
            ),
        ),
    )
