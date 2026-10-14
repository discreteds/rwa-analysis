"""Reviewed FY23 NAB capture metadata; financial definitions stay in the catalogue."""

from datetime import date
from decimal import Decimal

from rwa_analysis.catalogue.models import EvidenceRef
from rwa_analysis.catalogue.models import SemanticAttribute as Assertion
from rwa_analysis.extraction.definitions import (
    CaptureDefinition,
    CaptureSnapshot,
    CellBinding,
    ContextDefinition,
    FragmentRef,
    OccurrenceBinding,
    OccurrenceLink,
    OccurrenceRef,
    PhysicalBinding,
    PhysicalParameter,
    TemporalRole,
)
from rwa_analysis.extraction.models import (
    BandDefinition,
    Knowledge,
    Qualification,
    SegmentationDefinition,
    SemanticAttribute,
    SourceAxisItem,
    SourceDocument,
    SourceEndpoint,
    SourceReference,
    SourceRelationship,
)
from rwa_analysis.extraction.source_tables import (
    CellTemporalBinding,
    SourceTable,
    SourceTableMetadata,
    TableContext,
    TableField,
)
from rwa_analysis.extraction.temporal import TemporalDescriptor

DOCUMENT = "nab-2023-09-30-aps330"
BUNDLE = "au/nab/2023-09-30/aps330"
PORTFOLIO = "Residential mortgage"
BANDS = ("0<0.1%", "0.1<0.5%", "0.5<2.0%", "2.0<5.0%", "5.0<99.9%", "100%")
EXPOSURE_TITLE = "Table 5.3.B Retail exposures by risk grade"
PD_TITLE = "Table 5.1.J (ii) Accuracy of risk estimates for Probability of Default and Exposure at Default"
LGD_TITLE = "Table 5.1.J (iii) Accuracy of risk estimates for Loss Given Default"


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page - 2), location, row, column)


def address(scope, kind, key):
    return OccurrenceRef(BUNDLE, scope, kind, key)


def physical(key, operation, page, location, **parameters):
    return PhysicalBinding(
        key + "@1",
        operation,
        tuple(PhysicalParameter(k, v) for k, v in parameters.items()),
        ref(page, location),
    )


def assertion(name, value, *comments, scope=""):
    return Assertion(
        value,
        "established" if value is not None else "unresolved",
        evidence_refs=tuple(
            EvidenceRef(BUNDLE, DOCUMENT, scope, "comment", q) for q in comments
        ),
        name=name,
    )


COMMON = ("report-entity", "currency", "level-2")
COMMON_CONTEXT = ContextDefinition(
    "nab-2023/common@1",
    (
        assertion(
            "reporting_entity", "NAB and its controlled entities", "report-entity"
        ),
        assertion("consolidation_scope", "Level 2", "level-2"),
        assertion("currency", "AUD", "currency"),
        assertion("geography", None),
    ),
    evidence=(ref(4, "Introduction"),),
)

# Each physical paragraph is captured once, then linked to its reviewed targets.
PARAGRAPHS = (
    ("report-entity", 4, "This document describes", "Amounts are"),
    ("currency", 4, "Amounts are presented", "Capital adequacy methodologies"),
    ("level-2", 4, "This report applies", "\n"),
    ("pd-horizon", 45, "PD measures", " The Group uses"),
    ("pd-through-cycle", 46, "Through-the-cycle,", "The Group has"),
    ("ead-definition", 46, "EaD is calculated", "Credit rating system control"),
    ("retail-ead", 47, "Retail EaD models", "LGD models"),
    ("lgd-definition", 46, "LGD measures", "The Group applies stresses"),
    ("lgd-downturn", 46, "The Group applies stresses", "Exposure at Default"),
    ("retail-lgd", 47, "Key account variables", "Full Year Pillar"),
    ("default-definition", 23, "Default occurs", "Full Year Pillar"),
    (
        "framework-history",
        38,
        "The revised capital framework",
        "As a significant portion",
    ),
    (
        "backtesting-perimeter",
        38,
        "As a significant portion",
        "Table 5.1.J (i) Loss experience",
    ),
    (
        "pd-cohort",
        40,
        "The following table provides internal",
        "Accuracy of risk estimates for Exposure",
    ),
    ("ead-comparison", 40, "The ratio of estimated", "As at"),
    ("lgd-estimate", 41, "The following table compares internal", "Actual LGD"),
    ("lgd-history", 41, "Actual LGD has been", "As at 30 Sep 23"),
)


def build():
    physicals = [
        physical(key, "paragraph", page, key, start=start, end=end)
        for key, page, start, end in PARAGRAPHS
    ]
    physicals.extend(
        (
            physical(
                "ead-glossary",
                "region",
                76,
                "Exposure at default (EaD)",
                box=("225", "50", "395", "810"),
                start="An estimate of the credit exposure amount",
                end="Extended Licensed Entity",
            ),
            physical(
                "mortgage-definition",
                "region",
                45,
                "Residential mortgage definition",
                box=("145", "456", "390", "475"),
            ),
        )
    )
    shared = {p.revision_id.removesuffix("@1"): p for p in physicals}
    targets = {key: [] for key in shared}
    contexts, occurrences, tables = [COMMON_CONTEXT], [], []
    panels = (
        ("exposure", 50, "2023-09-30", "As at 30 Sep 23"),
        ("exposure", 51, "2023-03-31", "As at 31 Mar 23"),
        ("ii", 40, "2023-09-30", "As at 30 Sep 23"),
        ("ii", 40, "2023-03-31", "As at 31 Mar 23"),
        ("ii", 41, "2022-09-30", "As at 30 Sep 22"),
        ("iii", 41, "2023-09-30", "As at 30 Sep 23"),
        ("iii", 42, "2023-03-31", "As at 31 Mar 23"),
        ("iii", 42, "2022-09-30", "As at 30 Sep 22"),
    )
    # Titles on continuation panels refer to the original printed title.
    for key, page, title in (
        ("exposure", 50, EXPOSURE_TITLE),
        ("ii", 40, PD_TITLE),
        ("iii", 41, LGD_TITLE),
    ):
        physicals.append(
            physical(key + "/title", "paragraph", page, title, start=title, end="\n")
        )
    for kind, page, day, label in panels:
        exposure = kind == "exposure"
        tid = ("table5-3-b-" if exposure else f"table5-1-j-{kind}-") + day
        title = EXPOSURE_TITLE if exposure else PD_TITLE if kind == "ii" else LGD_TITLE
        context_id = tid + "/context@1"
        context_refs = (COMMON_CONTEXT.revision_id, context_id)
        axes, fields, notes, relationships, bands, temporal = [], [], [], [], [], []
        attributes = (
            (assertion("regulatory_scope", "advanced IRB", "approach", scope=tid),)
            if exposure
            else ()
        )
        knowledge = {
            a.name: Knowledge(
                a.value, a.status, tuple(e.ref_id for e in a.evidence_refs)
            )
            for a in COMMON_CONTEXT.attributes + attributes
        }
        context = TableContext(
            "context",
            date(2023, 9, 30),
            label,
            "Table 5.3.B" if exposure else f"Table 5.1.J ({kind})",
            title,
            PORTFOLIO,
            knowledge["reporting_entity"],
            knowledge["consolidation_scope"],
            knowledge.get("regulatory_scope", Knowledge()),
            knowledge["geography"],
            knowledge["currency"],
            COMMON,
            (ref(4, "Introduction"), ref(page, title)),
        )

        def add_axis(
            key,
            axis_kind,
            text,
            order,
            path,
            quals,
            slots,
            *,
            axes=axes,
            page=page,
            title=title,
            tid=tid,
            context_refs=context_refs,
        ):
            axes.append(
                SourceAxisItem(
                    key,
                    axis_kind,
                    text,
                    order,
                    path,
                    ("context",),
                    quals,
                    ref(page, title),
                )
            )
            occurrences.append(
                OccurrenceBinding(address(tid, axis_kind, key), slots, context_refs)
            )

        def add_note(
            key, endpoint_kind, ids, reader=None, slot="text", *, notes=notes, tid=tid
        ):
            endpoints = tuple(SourceEndpoint(endpoint_kind, i) for i in ids)
            source = reader or shared[key]
            notes.append(Qualification(key, "", (source.source_reference,), endpoints))
            links = [
                address(
                    tid,
                    {"dataset": "table", "band": "column"}.get(
                        endpoint_kind, endpoint_kind
                    ),
                    i,
                )
                for i in ids
            ]
            if reader is None:
                targets[key].extend(links)
            else:
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "comment", key),
                        (FragmentRef(reader.revision_id, slot),),
                        links=tuple(
                            OccurrenceLink("qualifies", target) for target in links
                        ),
                    )
                )

        panel = physical(
            tid + "/panel", "paragraph", page, title, start=label, end="\n"
        )
        physicals.append(panel)
        occurrences.append(
            OccurrenceBinding(
                address(tid, "table", tid),
                (FragmentRef(kind + "/title@1", "text"),),
                context_refs,
            )
        )
        add_axis(
            "panel",
            "header",
            label,
            0,
            (),
            (),
            (FragmentRef(panel.revision_id, "text"),),
        )
        for key in COMMON:
            add_note(key, "dataset", (tid,))
        if exposure:
            specs = (
                ("exposure", "Exposure at default", "$m", ("ead-definition",)),
                (
                    "undrawn",
                    "Undrawn commitments" + ("(1)" if page == 50 else "(2)(3)"),
                    "$m",
                    ("undrawn",) + (("undrawn-restated",) if page == 51 else ()),
                ),
                (
                    "average_ead",
                    "Average exposure at default ($m)"
                    + ("(2)" if page == 50 else "(4)"),
                    "$m",
                    ("average-arrangements", "ead-definition"),
                ),
                (
                    "lgd",
                    "Exposure-weighted average LGD (%)",
                    "%",
                    ("lgd-definition", "lgd-downturn", "retail-lgd"),
                ),
                (
                    "risk_weight",
                    "Exposure-weighted average risk-weight (%)"
                    + ("(3)" if page == 50 else "(5)"),
                    "%",
                    ("overlay",),
                ),
            )
            descriptors = (
                TemporalDescriptor(
                    "measurement",
                    label,
                    point=day,
                    point_status="established",
                    evidence=(ref(page, "Panel heading"),),
                ),
            )
            for key, start, target in (
                ("undrawn", "Undrawn commitments are included", "undrawn"),
                ("average-arrangements", "Simple average of exposure", "average_ead"),
                ("overlay", "RWA overlay adjustments", "risk_weight"),
                *(
                    (
                        "undrawn-restated",
                        "Undrawn commitments have been restated",
                        "undrawn",
                    ),
                )
                * (page == 51),
            ):
                reader = physical(
                    tid + "/" + key, "paragraph", page, key, start=start, end="\n"
                )
                physicals.append(reader)
                add_note(key, "field", (target,), reader)
            for key, target_kind, ids in (
                ("mortgage-definition", "dataset", (tid,)),
                ("pd-horizon", "band", tuple(f"band-{j}" for j in range(6))),
                ("pd-through-cycle", "band", tuple(f"band-{j}" for j in range(6))),
                ("default-definition", "band", ("band-5",)),
                ("ead-definition", "field", ("exposure", "average_ead")),
                ("retail-ead", "field", ("exposure", "average_ead")),
                ("ead-glossary", "field", ("exposure", "average_ead")),
                ("lgd-definition", "field", ("lgd",)),
                ("lgd-downturn", "field", ("lgd",)),
                ("retail-lgd", "field", ("lgd",)),
            ):
                add_note(key, target_kind, ids)
            band_reader = physical(
                tid + "/bands", "bands", page, title, prefix="0<0.1%"
            )
            band_header = physical(
                tid + "/band-header",
                "paragraph",
                page,
                title,
                start="PD risk grade",
                end="\n",
                after=label,
            )
            physicals.extend((band_reader, band_header))
            add_axis(
                "pd-bands",
                "header",
                "PD risk grade",
                1,
                ("panel",),
                (),
                (FragmentRef(band_header.revision_id, "text"),),
            )
            for j, text in enumerate(BANDS):
                key = f"band-{j}"
                bounds = text.rstrip("%").split("<") if j < 5 else (None, None)
                quals = ("pd-horizon", "pd-through-cycle") + (
                    ("default-definition",) if j == 5 else ()
                )
                add_axis(
                    key,
                    "column",
                    text,
                    j,
                    ("panel", "pd-bands"),
                    quals,
                    (FragmentRef(band_reader.revision_id, str(j)),),
                )
                bands.append(
                    BandDefinition(
                        key,
                        text,
                        j,
                        "interval" if j < 5 else "default",
                        "%",
                        Decimal(bounds[0]) if j < 5 else None,
                        Decimal(bounds[1]) if j < 5 else None,
                        None,
                        False if j < 5 else None,
                        "established" if j < 5 else "not_applicable",
                        "established" if j < 5 else "not_applicable",
                        "default" if j == 5 else None,
                        ref(page, title, column=text),
                    )
                )
            relationships.extend(
                SourceRelationship(
                    f"undrawn-{j}",
                    "subset",
                    "included in total exposure shown above",
                    SourceEndpoint("cell", f"exposure/band-{j}"),
                    (SourceEndpoint("cell", f"undrawn/band-{j}"),),
                    (SourceEndpoint("band", f"band-{j}"),),
                    None,
                    None,
                    (ref(page, "Undrawn commitments footnote"),),
                )
                for j in range(6)
            )
        else:
            specs = (
                (
                    ("estimated_pd", "Average estimated PD", "%", ("pd-cohort",)),
                    ("actual_pd", "Average actual PD", "%", ("pd-cohort",)),
                    (
                        "ead_ratio",
                        "Ratio of estimated to actual EaD",
                        "ratio",
                        ("ead-comparison",),
                    ),
                )
                if kind == "ii"
                else (
                    (
                        "estimated_lgd",
                        "Average estimated downturn LGD",
                        "%",
                        ("lgd-estimate",),
                    ),
                    ("actual_lgd", "Average actual LGD", "%", ("lgd-history",)),
                )
            )
            add_note("framework-history", "dataset", (tid,))
            add_note("backtesting-perimeter", "row", ("main", "rbnz"))
            if kind == "ii":
                add_note("pd-cohort", "field", ("estimated_pd", "actual_pd"))
                add_note("ead-comparison", "field", ("ead_ratio",))
                descriptors = (
                    TemporalDescriptor(
                        "pd-history",
                        "10-year observation period",
                        duration_amount=Decimal(10),
                        duration_unit="year",
                        duration_status="established",
                        qualification_refs=("pd-cohort",),
                        evidence=(ref(40, "PD methodology"),),
                    ),
                    TemporalDescriptor(
                        "pd-anchor",
                        "beginning of the reporting period",
                        qualification_refs=("pd-cohort",),
                        evidence=(ref(40, "PD methodology"),),
                    ),
                    TemporalDescriptor(
                        "ead-anchor",
                        "beginning of the reporting period",
                        qualification_refs=("ead-comparison",),
                        evidence=(ref(40, "EaD methodology"),),
                    ),
                    TemporalDescriptor(
                        "ead-default",
                        "at the point of default",
                        qualification_refs=("ead-comparison",),
                        evidence=(ref(40, "EaD methodology"),),
                    ),
                )
            else:
                add_note("lgd-estimate", "field", ("estimated_lgd",))
                add_note("lgd-history", "field", ("actual_lgd",))
                for key, start, target in (
                    (
                        "apra-floor",
                        "Estimated downturn LGD subject",
                        "main/estimated_lgd",
                    ),
                    (
                        "rbnz-lgd",
                        "RBNZ prudential rules prescribe",
                        "rbnz/estimated_lgd",
                    ),
                ):
                    reader = physical(
                        tid + "/" + key,
                        "paragraph",
                        page,
                        key,
                        start=start,
                        end="\n",
                        after=label,
                    )
                    physicals.append(reader)
                    add_note(key, "cell", (target,), reader)
                descriptors = (
                    TemporalDescriptor(
                        "lgd-history",
                        "10-year observation period to the reporting date, excluding recent defaults",
                        end=day,
                        end_status="established",
                        duration_amount=Decimal(10),
                        duration_unit="year",
                        duration_status="established",
                        qualification_refs=("lgd-history",),
                        evidence=(ref(41, "LGD methodology"),),
                    ),
                    TemporalDescriptor(
                        "lgd-estimate",
                        "at the beginning of the year",
                        qualification_refs=("lgd-estimate",),
                        evidence=(ref(41, "LGD methodology"),),
                    ),
                )
            edges = (
                (
                    ("390", "445", "500", "550")
                    if page == 40
                    else ("376", "431", "486", "536")
                )
                if kind == "ii"
                else (("426", "481", "536") if page == 41 else ("440", "495", "550"))
            )
            headers = physical(
                tid + "/headers",
                "column_headers",
                page,
                title,
                panel=label,
                end="Exposure type subject",
                edges=edges,
            )
            physicals.append(headers)
        contexts.append(
            ContextDefinition(context_id, attributes, descriptors, context.evidence)
        )
        reader = physical(
            tid + "/values",
            "rows",
            page,
            title,
            panel=label,
            prefix=PORTFOLIO,
            columns=6 if exposure else len(specs),
            labels=BANDS if exposure else tuple(s[1] for s in specs),
        )
        physicals.append(reader)
        for i, (key, text, unit, quals) in enumerate(specs):
            attrs = (
                (
                    SemanticAttribute(
                        "counted_entity",
                        "arrangement",
                        "established",
                        ("average-arrangements",),
                    ),
                )
                if key == "average_ead"
                else ()
            )
            fields.append(
                TableField(
                    key,
                    text,
                    ("panel", key),
                    unit,
                    Decimal(1000000 if unit == "$m" else 1),
                    quals,
                    attrs,
                    ref(
                        page,
                        title,
                        text if exposure else None,
                        None if exposure else text,
                    ),
                    "decimal",
                    "money" if unit == "$m" else "scalar",
                )
            )
            if exposure:
                header = physical(
                    tid + "/" + key + "/header",
                    "paragraph",
                    page,
                    title,
                    start=text,
                    end="\n",
                    after=label,
                )
                approach = physical(
                    tid + "/" + key + "/approach",
                    "paragraph",
                    page,
                    title,
                    start="Subject to advanced IRB approach",
                    end="\n",
                    after=text,
                )
                physicals.extend((header, approach))
                slots = (FragmentRef(header.revision_id, "text"),)
                add_axis(key, "block", text, i, ("panel",), quals, slots)
                add_axis(
                    key + "-approach",
                    "block",
                    "Subject to advanced IRB approach",
                    i,
                    ("panel", key),
                    ("approach",),
                    (FragmentRef(approach.revision_id, "text"),),
                )
                add_axis(
                    key + "-mortgage",
                    "row",
                    PORTFOLIO,
                    i,
                    ("panel", key, key + "-approach"),
                    quals,
                    (FragmentRef(reader.revision_id, f"row/{i}"),),
                )
                if i == 0:
                    add_note("approach", "dataset", (tid,), approach)
            else:
                slots = (FragmentRef(headers.revision_id, str(i)),)
                add_axis(key, "column", text, i, ("panel",), quals, slots)
            occurrences.append(
                OccurrenceBinding(address(tid, "field", key), slots, context_refs)
            )
        if not exposure:
            for j, population in enumerate(("main", "rbnz")):
                prefix = (
                    "Exposure type subject to"
                    if population == "main"
                    else "RBNZ regulated"
                )
                block = physical(
                    tid + "/" + population,
                    "paragraph",
                    page,
                    title,
                    start=prefix,
                    end=" %" if population == "main" else "\n",
                    after=label,
                )
                physicals.append(block)
                quals = ("backtesting-perimeter",)
                add_axis(
                    population + "-block",
                    "block",
                    "",
                    j,
                    ("panel",),
                    quals,
                    (FragmentRef(block.revision_id, "text"),),
                )
                add_axis(
                    population,
                    "row",
                    PORTFOLIO,
                    j,
                    ("panel", population + "-block"),
                    quals,
                    (FragmentRef(reader.revision_id, f"row/{j}"),),
                )
        # Row-major bindings preserve published ordering, including transposed measures.
        for row in range(len(specs) if exposure else 2):
            for col in range(6 if exposure else len(specs)):
                key, _, _, quals = specs[row if exposure else col]
                population = ("main", "rbnz")[row] if not exposure else None
                cid = key + f"/band-{col}" if exposure else population + "/" + key
                if exposure:
                    roles = (("measurement", "measurement"),)
                elif key in ("estimated_pd", "actual_pd"):
                    roles = (
                        ("history_window", "pd-history"),
                        ("cohort_anchor", "pd-anchor"),
                    )
                elif key == "ead_ratio":
                    roles = (
                        ("cohort_anchor", "ead-anchor"),
                        ("measurement", "ead-default"),
                    )
                else:
                    roles = (
                        (("measurement", "lgd-estimate"),)
                        if key == "estimated_lgd"
                        else (("history_window", "lgd-history"),)
                    )
                if not exposure:
                    quals = ("backtesting-perimeter",) + quals
                    if key == "estimated_lgd":
                        quals += ("apra-floor" if population == "main" else "rbnz-lgd",)
                temporal.extend(
                    CellTemporalBinding(cid, role, descriptor)
                    for role, descriptor in roles
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "cell", cid),
                        (FragmentRef(reader.revision_id, f"{row}/{col}"),),
                        context_refs,
                        temporal_roles=tuple(
                            TemporalRole(role, context_id, descriptor)
                            for role, descriptor in roles
                        ),
                        cell=CellBinding(
                            key,
                            key + "-mortgage" if exposure else population,
                            f"band-{col}" if exposure else key,
                            (f"band-{col}",) if exposure else (),
                            quals,
                            missing_reason="dash_unresolved",
                        ),
                    )
                )
        segmentations = (
            (
                SegmentationDefinition(
                    "pd-bands",
                    "PD risk grade",
                    tuple(bands),
                    ("context",),
                    Knowledge(),
                    Knowledge(),
                    (ref(page, title),),
                ),
            )
            if exposure
            else ()
        )
        tables.append(
            SourceTable(
                tid,
                SourceTableMetadata(
                    context,
                    tuple(axes),
                    tuple(fields),
                    segmentations,
                    tuple(notes),
                    tuple(relationships),
                    descriptors,
                    tuple(temporal),
                ),
                (),
            )
        )
    for key, reader in shared.items():
        occurrences.append(
            OccurrenceBinding(
                address(None, "comment", key),
                (FragmentRef(reader.revision_id, "text"),),
                links=tuple(
                    OccurrenceLink("qualifies", target) for target in targets[key]
                ),
            )
        )
    return CaptureDefinition(
        SourceDocument(
            DOCUMENT,
            "raw/nab-2023-09-30-aps330.pdf",
            "nab",
            "National Australia Bank Limited",
            "Full Year Pillar 3 Report 2023",
            date(2023, 9, 30),
            None,
            "au",
            "https://www.nab.com.au/content/dam/nab/documents/reports/corporate/2023-full-year-pillar-3-report.pdf",
        ),
        BUNDLE,
        "extractions/au/nab/2023-09-30/aps330/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "nab-2023-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
        ),
    )


DEFINITION = build()
