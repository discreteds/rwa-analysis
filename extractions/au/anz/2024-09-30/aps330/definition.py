"""Reviewed ANZ 2024 selection and bindings; no PDF-dependent metadata construction."""

from dataclasses import replace
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

DOCUMENT = "anz-2024-09-30-aps330"
BUNDLE = "au/anz/2024-09-30/aps330"
PORTFOLIO = "Residential Mortgage"
EXPOSURE_TITLE = "Table 9(d): Retail Exposure at Default subject to Internal Ratings Based (IRB) approach by risk grade"
BACKTEST_TITLE = "Table 9(f): Average estimated vs. actual PD, EAD and LGD – IRB"
BANDS = (
    "0.00%\n<0.11%",
    "0.11%\n<0.30%",
    "0.30%\n<0.51%",
    "0.51%\n<3.49%",
    "3.49%\n<10.09%",
    "10.09%\n<100.00%",
    "Default",
    "Total",
)
EXPOSURE_FIELDS = (
    (
        "exposure",
        "Exposure at Default",
        "$M",
        ("ead-definition", "ead-glossary", "ead-net-offsets"),
    ),
    (
        "undrawn",
        "Undrawn commitments (included in above)",
        "$M",
        ("undrawn", "ead-net-offsets"),
    ),
    (
        "average_ead",
        "Average Exposure at Default",
        "$M",
        ("ead-definition", "ead-glossary", "ead-net-offsets"),
    ),
    (
        "lgd",
        "Exposure-weighted average Loss Given Default (%)",
        "%",
        ("lgd-definition", "regulatory-adjustments"),
    ),
    (
        "risk_weight",
        "Exposure-weighted average risk weight (%)",
        "%",
        ("regulatory-adjustments",),
    ),
)
BACKTEST_FIELDS = (
    ("estimated_pd", "Average Estimated PD %", "%", ("pd-history",)),
    ("actual_pd", "Average Actual PD %", "%", ("pd-history",)),
    (
        "ead_ratio",
        "Average estimated to actual EAD ratio",
        "ratio",
        ("ead-history", "ead-net-offsets"),
    ),
    ("estimated_lgd", "Average Estimated LGD %", "%", ("lgd-history",)),
    ("actual_lgd", "Average Actual LGD %", "%", ("lgd-history",)),
)
# Each reviewed panel supplies its own date and title; no preceding-vintage template.
PANELS = (
    (53, "table9d-2024-09-30", "2024-09-30", "Sep 24", EXPOSURE_TITLE),
    (54, "table9d-2024-03-31", "2024-03-31", "Mar 24", EXPOSURE_TITLE + " (continued)"),
    (55, "table9d-2023-09-30", "2023-09-30", "Sep 23", EXPOSURE_TITLE + " (continued)"),
    (57, "table9f-2024-09-30", None, "Sep 24", BACKTEST_TITLE),
)
COMMON = (
    "report-entity",
    "level-2",
    "currency",
    "regulatory-basis",
    "suncorp",
    "default-definition",
)


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page - 1), location, row, column)


def address(scope, kind, key):
    return OccurrenceRef(BUNDLE, scope, kind, key)


def physical(key, operation, page, location, **parameters):
    return PhysicalBinding(
        key + "@1",
        operation,
        tuple(PhysicalParameter(k, v) for k, v in parameters.items()),
        ref(page, location),
    )


def assertion(name, value, *comments):
    return Assertion(
        value,
        "established" if value is not None else "unresolved",
        evidence_refs=tuple(
            EvidenceRef(BUNDLE, DOCUMENT, "", "comment", q) for q in comments
        ),
        name=name,
    )


COMMON_CONTEXT = ContextDefinition(
    "anz-2024/common@1",
    (
        assertion(
            "reporting_entity", "ANZ BH Pty Ltd (ANZ Bank HoldCo)", "report-entity"
        ),
        assertion("consolidation_scope", "Level 2", "level-2"),
        assertion("regulatory_scope", "AIRB", "regulatory-basis"),
        assertion("geography", None),
        assertion("currency", "AUD", "currency"),
    ),
    evidence=(ref(4, "Purpose of this document"),),
)

# A shared passage is sourced once. The links below own its applicability.
PARAGRAPHS = (
    (
        "report-entity",
        4,
        "This document is prepared",
        "It presents",
        "",
        "report-entity",
    ),
    ("level-2", 4, "The APS 330 disclosure", "Any reference", "", "level-2"),
    (
        "currency",
        4,
        "Unless otherwise stated",
        "Suncorp Bank Acquisition",
        "",
        "currency",
    ),
    ("suncorp", 46, "On 31 July 2024", "\n45", "", "suncorp"),
    (
        "regulatory-basis",
        46,
        "Residential Mortgages",
        "Qualifying Revolving",
        "",
        "regulatory-basis",
    ),
    (
        "default-definition",
        28,
        "ANZ uses the following definition",
        "Non-performing facilities",
        "",
        "default-definition",
    ),
    (
        "ead-net-offsets",
        27,
        "Unless otherwise stated",
        "Past due facilities",
        "",
        "Exposure at Default (EAD)",
    ),
    ("pd-definition", 47, "PD is an estimate", " EAD", "", "pd-definition"),
    ("ead-definition", 49, "EAD represents", "\n48", "", "ead-definition"),
    (
        "ead-glossary",
        100,
        "Exposure At Default is defined",
        "Impaired assets",
        "",
        "ead-glossary",
    ),
    (
        "lgd-definition",
        47,
        "LGD is an estimate",
        "Effective maturity",
        "",
        "lgd-definition",
    ),
    (
        "regulatory-adjustments",
        48,
        "For the wholesale asset class",
        "Controls surrounding",
        "",
        "regulatory-adjustments",
    ),
    ("framework", 57, "APS 330 Table 9(f)", "Estimated PD and LGD", "", BACKTEST_TITLE),
    (
        "pd-history",
        57,
        "The estimated PD",
        "The EAD ratio",
        "Retail Portfolios",
        "Retail Portfolios",
    ),
    (
        "ead-history",
        57,
        "The EAD ratio",
        "The estimated LGD",
        "Retail Portfolios",
        "Retail Portfolios",
    ),
    (
        "lgd-history",
        57,
        "The estimated LGD",
        "\n56",
        "Retail Portfolios",
        "Retail Portfolios",
    ),
    (
        "lgd-review",
        57,
        "A review of historical",
        "Retail Portfolios",
        "",
        "Wholesale Portfolios",
    ),
)
BACKTEST_TIME = (
    TemporalDescriptor(
        "pd-ead-history",
        "2019 to 2023",
        start="2019",
        end="2023",
        start_status="established",
        end_status="established",
        qualification_refs=("pd-history", "ead-history"),
        evidence=(ref(57, "Retail Portfolios"),),
    ),
    TemporalDescriptor(
        "lgd-history",
        "2018 to 2022",
        start="2018",
        end="2022",
        start_status="established",
        end_status="established",
        qualification_refs=("lgd-history",),
        evidence=(ref(57, "Retail Portfolios"),),
    ),
    TemporalDescriptor(
        "default-cutoff",
        "up to September 2023 / Defaults occurring after September 2023 have been excluded",
        end="2023-09",
        end_status="established",
        qualification_refs=("pd-history", "lgd-history"),
        evidence=(ref(57, "Retail Portfolios"),),
    ),
)
BACKTEST_ROLES = {
    "estimated_pd": (("history_window", "pd-ead-history"),),
    "actual_pd": (
        ("history_window", "pd-ead-history"),
        ("outcome_window", "default-cutoff"),
    ),
    "ead_ratio": (("history_window", "pd-ead-history"),),
    "estimated_lgd": (
        ("history_window", "lgd-history"),
        ("outcome_window", "default-cutoff"),
    ),
    "actual_lgd": (
        ("history_window", "lgd-history"),
        ("outcome_window", "default-cutoff"),
    ),
}


def build():
    physicals = [
        physical(
            key,
            "paragraph",
            page,
            location,
            start=start,
            end=end,
            **({"after": after} if after else {}),
        )
        for key, page, start, end, after, location in PARAGRAPHS
    ]
    occurrences, contexts, tables = [], [COMMON_CONTEXT], []
    comment_targets = {key: [] for key, *_ in PARAGRAPHS}
    for page, tid, day, label, title in PANELS:
        backtest = tid == "table9f-2024-09-30"
        specs = BACKTEST_FIELDS if backtest else EXPOSURE_FIELDS
        context_id = tid + "/context@1"
        context_refs = (COMMON_CONTEXT.revision_id, context_id)
        context = TableContext(
            "context",
            date(2024, 9, 30),
            label,
            "Table 9(f)" if backtest else "Table 9(d)",
            title,
            PORTFOLIO,
            *(
                Knowledge(a.value, a.status, tuple(e.ref_id for e in a.evidence_refs))
                for a in COMMON_CONTEXT.attributes
            ),
            COMMON,
            (ref(4, "Purpose of this document"), ref(page, title)),
        )
        descriptors = (
            BACKTEST_TIME
            if backtest
            else (
                TemporalDescriptor(
                    "measurement",
                    label,
                    point=day,
                    point_status="established",
                    evidence=(ref(page, title),),
                ),
            )
        )
        contexts.append(
            ContextDefinition(context_id, (), descriptors, context.evidence)
        )
        title_reader = physical(
            tid + "/title",
            "paragraph",
            page,
            title,
            start="Table 9(f)" if backtest else "Table 9(d)",
            end=label,
        )
        physicals.append(title_reader)
        occurrences.append(
            OccurrenceBinding(
                address(tid, "table", tid),
                (FragmentRef(title_reader.revision_id, "text"),),
                context_refs=context_refs,
            )
        )
        axes, fields, temporal, relationships, bands = [], [], [], [], []

        def axis(
            key,
            kind,
            text,
            order,
            path=(),
            quals=(),
            fragments=(),
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
                    kind,
                    text,
                    order,
                    path,
                    ("context",),
                    quals,
                    ref(
                        page,
                        title,
                        text if kind == "row" else None,
                        text if kind == "column" else None,
                    ),
                )
            )
            occurrences.append(
                OccurrenceBinding(address(tid, kind, key), fragments, context_refs)
            )

        panel = physical(
            tid + "/panel", "paragraph", page, title, start=label, end="\n"
        )
        physicals.append(panel)
        axis(
            "panel",
            "header",
            label,
            0,
            fragments=(FragmentRef(panel.revision_id, "text"),),
        )
        reader = physical(
            tid + "/values",
            "rows",
            page,
            title,
            prefix=PORTFOLIO,
            columns=5 if backtest else 8,
            labels=tuple(s[1] for s in specs) if backtest else BANDS,
        )
        physicals.append(reader)
        if backtest:
            portfolio = physical(
                tid + "/portfolio",
                "region",
                page,
                title,
                box=("80", "103", "140", "138"),
            )
            physicals.append(portfolio)
            axis(
                "portfolio",
                "header",
                "Portfolio Type",
                1,
                fragments=(FragmentRef(portfolio.revision_id, "text"),),
            )
            axis(
                "mortgage",
                "row",
                PORTFOLIO,
                0,
                ("portfolio",),
                fragments=(FragmentRef(reader.revision_id, "row/0"),),
            )
        else:
            band_reader = physical(
                tid + "/bands", "bands", page, title, prefix="0.00%", intervals=6
            )
            physicals.append(band_reader)
            for j, text in enumerate(BANDS):
                key = f"band-{j}"
                axis(
                    key,
                    "column",
                    text,
                    j,
                    ("panel",),
                    ("pd-definition",) if j < 7 else (),
                    (FragmentRef(band_reader.revision_id, str(j)),),
                )
                lower, upper = text.split("\n") if j < 6 else (None, None)
                bands.append(
                    BandDefinition(
                        key,
                        text,
                        j,
                        "interval" if j < 6 else "default" if j == 6 else "category",
                        "%",
                        Decimal(lower.rstrip("%")) if lower else None,
                        Decimal(upper.strip("<%")) if upper else None,
                        None,
                        False if j < 6 else None,
                        "established" if j < 6 else "not_applicable",
                        "established" if j < 6 else "not_applicable",
                        None if j < 6 else text,
                        ref(page, title, column=text),
                    )
                )
        for i, (key, text, unit, quals) in enumerate(specs):
            attrs = (
                (SemanticAttribute("counted_entity", None, "unresolved", ()),)
                if key == "average_ead"
                else (
                    SemanticAttribute(
                        "historical_review_applicability",
                        None,
                        "unresolved",
                        ("lgd-review",),
                    ),
                )
                if key == "actual_lgd"
                else ()
            )
            fields.append(
                TableField(
                    key,
                    text,
                    ("panel", key),
                    unit,
                    Decimal("1000000" if unit == "$M" else "1"),
                    quals,
                    attrs,
                    ref(
                        page,
                        title,
                        None if backtest else text,
                        text if backtest else None,
                    ),
                    "decimal",
                    "money" if unit == "$M" else "scalar",
                )
            )
            if backtest:
                left, right = (
                    ("245", "292"),
                    ("303", "349"),
                    ("357", "411"),
                    ("421", "469"),
                    ("481", "530"),
                )[i]
                header = physical(
                    tid + "/" + key + "/header",
                    "region",
                    page,
                    title,
                    box=(left, "103", right, "138"),
                )
            else:
                # The first heading repeats in the title. Average EAD wraps on p.53.
                header = physical(
                    tid + "/" + key + "/header",
                    "paragraph",
                    page,
                    title,
                    start="Average Exposure at" if key == "average_ead" else text,
                    end=PORTFOLIO,
                    after=label,
                )
            physicals.append(header)
            header_slot = (FragmentRef(header.revision_id, "text"),)
            occurrences.append(
                OccurrenceBinding(address(tid, "field", key), header_slot, context_refs)
            )
            if backtest:
                axis(key, "column", text, i, ("panel",), quals, header_slot)
            else:
                axis(key, "block", text, i, ("panel",), quals, header_slot)
                axis(
                    key + "-mortgage",
                    "row",
                    PORTFOLIO,
                    i,
                    ("panel", key),
                    quals,
                    (FragmentRef(reader.revision_id, f"row/{i}"),),
                )
            for j in range(1 if backtest else 8):
                cid = "mortgage/" + key if backtest else key + f"/band-{j}"
                roles = (
                    BACKTEST_ROLES[key]
                    if backtest
                    else (("measurement", "measurement"),)
                )
                temporal.extend(
                    CellTemporalBinding(cid, role, descriptor)
                    for role, descriptor in roles
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "cell", cid),
                        (
                            FragmentRef(
                                reader.revision_id, f"0/{i}" if backtest else f"{i}/{j}"
                            ),
                        ),
                        context_refs,
                        temporal_roles=tuple(
                            TemporalRole(role, context_id, descriptor)
                            for role, descriptor in roles
                        ),
                        cell=CellBinding(
                            key,
                            "mortgage" if backtest else key + "-mortgage",
                            key if backtest else f"band-{j}",
                            () if backtest else (f"band-{j}",),
                            quals,
                        ),
                    )
                )
            if not backtest:
                relationships.append(
                    SourceRelationship(
                        "total-" + key,
                        "total",
                        "Total",
                        SourceEndpoint("cell", key + "/band-7"),
                        tuple(
                            SourceEndpoint("cell", key + f"/band-{j}") for j in range(7)
                        ),
                        (SourceEndpoint("field", key),),
                        None,
                        None,
                        (ref(page, title, PORTFOLIO, "Total"),),
                    )
                )
        if not backtest:
            for j in range(8):
                relationships.append(
                    SourceRelationship(
                        f"undrawn-{j}",
                        "subset",
                        "included in above",
                        SourceEndpoint("cell", f"exposure/band-{j}"),
                        (SourceEndpoint("cell", f"undrawn/band-{j}"),),
                        (SourceEndpoint("band", f"band-{j}"),),
                        None,
                        None,
                        (ref(page, EXPOSURE_FIELDS[1][1], PORTFOLIO, BANDS[j]),),
                    )
                )
        scopes = {q: (SourceEndpoint("dataset", tid),) for q in COMMON}
        scopes["ead-net-offsets"] = tuple(
            SourceEndpoint("field", key)
            for key in (
                ("ead_ratio",) if backtest else ("exposure", "undrawn", "average_ead")
            )
        )
        if backtest:
            scopes.update(
                {"framework": (SourceEndpoint("dataset", tid),), "lgd-review": ()}
            )
            scopes.update(
                {
                    q: tuple(
                        SourceEndpoint("field", key)
                        for key, _, _, qs in specs
                        if q in qs
                    )
                    for q in ("pd-history", "ead-history", "lgd-history")
                }
            )
        else:
            scopes.update(
                {
                    "pd-definition": tuple(
                        SourceEndpoint("band", f"band-{j}") for j in range(7)
                    ),
                    "ead-definition": (
                        SourceEndpoint("field", "exposure"),
                        SourceEndpoint("field", "average_ead"),
                    ),
                    "ead-glossary": (
                        SourceEndpoint("field", "exposure"),
                        SourceEndpoint("field", "average_ead"),
                    ),
                    "lgd-definition": (SourceEndpoint("field", "lgd"),),
                    "regulatory-adjustments": (
                        SourceEndpoint("field", "lgd"),
                        SourceEndpoint("field", "risk_weight"),
                    ),
                }
            )
        notes = []
        for q, endpoints in scopes.items():
            source = next(
                p.source_reference for p in physicals if p.revision_id == q + "@1"
            )
            notes.append(Qualification(q, "", (source,), endpoints))
            comment_targets[q].extend(
                address(
                    tid,
                    {"dataset": "table", "band": "column"}.get(e.kind, e.kind),
                    e.id,
                )
                for e in endpoints
            )
            if not endpoints:
                # Keep wholesale evidence reachable without claiming it qualifies retail.
                index = next(
                    i
                    for i, b in enumerate(occurrences)
                    if b.ref == address(tid, "table", tid)
                )
                occurrences[index] = replace(
                    occurrences[index],
                    links=occurrences[index].links
                    + (OccurrenceLink("evidence", address(None, "comment", q)),),
                )
        if not backtest:
            header = next(
                p for p in physicals if p.revision_id == tid + "/undrawn/header@1"
            )
            notes.append(
                Qualification(
                    "undrawn",
                    "",
                    (header.source_reference,),
                    (SourceEndpoint("field", "undrawn"),),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, "comment", "undrawn"),
                    (FragmentRef(header.revision_id, "text"),),
                    links=(
                        OccurrenceLink("qualifies", address(tid, "field", "undrawn")),
                    ),
                )
            )
        segmentations = (
            ()
            if backtest
            else (
                SegmentationDefinition(
                    "risk-grades",
                    "risk grade",
                    tuple(bands),
                    ("context",),
                    Knowledge(),
                    Knowledge(),
                    (ref(page, title),),
                ),
            )
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
    occurrences.extend(
        OccurrenceBinding(
            address(None, "comment", key),
            (FragmentRef(key + "@1", "text"),),
            links=tuple(OccurrenceLink("qualifies", target) for target in targets),
        )
        for key, targets in comment_targets.items()
    )
    return CaptureDefinition(
        SourceDocument(
            DOCUMENT,
            "raw/anz-2024-09-30-aps330.pdf",
            "anz",
            "ANZ BH Pty Ltd (ANZ Bank HoldCo)",
            "Basel III Pillar 3 Disclosure As at 30 September 2024",
            date(2024, 9, 30),
            None,
            "au",
            "https://www.anz.com/content/dam/anzcom/shareholder/2024-september-pillar-3-disclosure.pdf",
        ),
        BUNDLE,
        "extractions/au/anz/2024-09-30/aps330/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "anz-2024-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
        ),
    )


DEFINITION = build()
