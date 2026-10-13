"""Reviewed ANZ selection: physical parameters, reusable contexts and explicit bindings.

Financial meaning stays in the selected catalogue. No PDF is opened at authoring time.
"""

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

DOCUMENT = "anz-2023-09-30-aps330"
BUNDLE = "au/anz/2023-09-30/aps330"
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


# Shared paragraphs are physically captured once; targets are composed below.
PARAGRAPHS = (
    ("report-entity", 4, "This document is prepared for", "It presents", ""),
    ("restructure", 4, "On 3 January 2023", "The APS 330 disclosure", ""),
    ("level-2", 4, "The APS 330 disclosure", "Basel in ANZ", ""),
    ("capital-reform", 4, "APRA released new", "In addition, operational", ""),
    (
        "comparative-basis",
        4,
        "The revisions to the prudential",
        "The application of APRA",
        "",
    ),
    ("currency", 5, "Unless otherwise stated", "Suncorp Bank Acquisition", ""),
    (
        "default-definition",
        30,
        "ANZ uses the following definition",
        "Non-performing facilities",
        "",
    ),
    ("ead-net-offsets", 29, "Unless otherwise stated", "Past due facilities", ""),
    ("pd-definition", 46, "PD is an estimate", " EAD", ""),
    ("ead-definition", 48, "EAD represents", "\n47", ""),
    ("ead-glossary", 96, "Exposure At Default is defined", "Impaired assets", ""),
    ("lgd-definition", 46, "LGD is an estimate", "Effective maturity", ""),
    (
        "regulatory-adjustments",
        47,
        "For the wholesale asset class",
        "Controls surrounding",
        "",
    ),
    ("framework", 56, "APS 330 Table 9(f)", "Estimated PD and LGD", ""),
    ("pd-history", 56, "The estimated PD", "The EAD ratio", "Retail Portfolios"),
    ("ead-history", 56, "The EAD ratio", "The estimated LGD", "Retail Portfolios"),
    ("lgd-history", 56, "The estimated LGD", "\n55", "Retail Portfolios"),
    ("lgd-review", 56, "A review of historical", "Retail Portfolios", ""),
)
COMMON = (
    "report-entity",
    "restructure",
    "level-2",
    "capital-reform",
    "comparative-basis",
    "currency",
    "regulatory-basis",
    "nz-separation",
    "default-definition",
)


def assertion(name, value, *comments):
    return Assertion(
        value,
        "established" if value is not None else "unresolved",
        evidence_refs=tuple(
            EvidenceRef(BUNDLE, DOCUMENT, "", "comment", key) for key in comments
        ),
        name=name,
    )


COMMON_CONTEXT = ContextDefinition(
    "anz-2023/common@1",
    (
        assertion("consolidation_scope", "Level 2", "level-2"),
        assertion("regulatory_scope", "AIRB", "regulatory-basis"),
        assertion("geography", None),
        assertion("currency", "AUD", "currency"),
    ),
    evidence=(ref(4, "Purpose of this document"),),
)
CURRENT_ENTITY = ContextDefinition(
    "anz-2023/current-entity@1",
    (
        assertion(
            "reporting_entity",
            "ANZ BH Pty Ltd (ANZ Bank HoldCo)",
            "level-2",
            "report-entity",
        ),
    ),
)
PREVIOUS_ENTITY = ContextDefinition(
    "anz-2023/previous-entity@1",
    (
        assertion(
            "reporting_entity",
            "Australia and New Zealand Banking Group Limited",
            "level-2",
            "report-entity",
        ),
    ),
)


def build():
    physicals = [
        physical(
            key,
            "paragraph",
            page,
            key,
            start=start,
            end=end,
            **({"after": after} if after else {}),
        )
        for key, page, start, end, after in PARAGRAPHS
    ]
    matrix = physical(
        "matrix",
        "matrix",
        45,
        "Table 9 IRB asset class / rating approach matrix",
        edges=("78.84", "175.98", "367.44", "449.76", "532.44"),
        columns=("asset", "borrower", "pre", "post"),
        rows=("mortgage", "nz"),
        prefixes=("Residential Mortgages", "Exposures of New"),
        sections=("Remains post-January", "New from January"),
    )
    physicals.append(matrix)
    occurrences, contexts, tables = (
        [],
        [COMMON_CONTEXT, CURRENT_ENTITY, PREVIOUS_ENTITY],
        [],
    )
    comment_targets = {key: [] for key, *_ in PARAGRAPHS}
    comment_targets.update({"regulatory-basis": [], "nz-separation": []})
    for page, day, label in (
        (52, "2023-09-30", "Sep 23"),
        (53, "2023-03-31", "Mar 23"),
        (54, "2022-09-30", "Sep 22"),
        (56, "2023-09-30", "Sep 23"),
    ):
        backtest = page == 56
        tid = ("table9f-" if backtest else "table9d-") + day
        title = (
            BACKTEST_TITLE
            if backtest
            else EXPOSURE_TITLE + (" (continued)" if page in (53, 54) else "")
        )
        specs = BACKTEST_FIELDS if backtest else EXPOSURE_FIELDS
        entity = PREVIOUS_ENTITY if day == "2022-09-30" else CURRENT_ENTITY
        context_id = tid + "/context@1"
        context_refs = (COMMON_CONTEXT.revision_id, entity.revision_id, context_id)
        attributes = entity.attributes + COMMON_CONTEXT.attributes
        context = TableContext(
            "context",
            date(2023, 9, 30),
            label,
            "Table 9(f)" if backtest else "Table 9(d)",
            title,
            PORTFOLIO,
            *(
                Knowledge(a.value, a.status, tuple(e.ref_id for e in a.evidence_refs))
                for a in attributes
            ),
            COMMON,
            (ref(4, "Purpose of this document"), ref(page, title)),
        )
        descriptors = []
        if backtest:
            for key, start, end in (
                ("pd-history", "2018", "2022"),
                ("ead-history", "2018", "2023"),
                ("lgd-history", "2017", "2021"),
            ):
                descriptors.append(
                    TemporalDescriptor(
                        key,
                        f"{start} to {end}",
                        start=start,
                        end=end,
                        start_status="established",
                        end_status="established",
                        qualification_refs=(key,),
                        evidence=(ref(page, "Retail Portfolios"),),
                    )
                )
            for key, text, end, qual in (
                ("pd-cutoff", "up to September 2023", "2023-09", "pd-history"),
                (
                    "lgd-cutoff",
                    "Defaults occurring after September 2022 have been excluded",
                    "2022-09",
                    "lgd-history",
                ),
            ):
                descriptors.append(
                    TemporalDescriptor(
                        key,
                        text,
                        end=end,
                        end_status="established",
                        qualification_refs=(qual,),
                        evidence=(ref(page, "Retail Portfolios"),),
                    )
                )
        else:
            descriptors.append(
                TemporalDescriptor(
                    "measurement",
                    label,
                    point=day,
                    point_status="established",
                    evidence=(ref(page, title),),
                )
            )
        contexts.append(
            ContextDefinition(context_id, (), tuple(descriptors), context.evidence)
        )
        title_reader = physical(
            tid + "/title",
            "paragraph",
            page,
            title,
            start="Table 9(f)" if backtest else "Table 9(d)",
            end="\n",
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
        if backtest:
            axis("portfolio", "header", "Portfolio Type", 1)
            axis("mortgage", "row", PORTFOLIO, 0, ("portfolio",))
        else:
            band_physical = physical(
                tid + "/bands", "bands", page, title, prefix="0.00%", intervals=6
            )
            physicals.append(band_physical)
            for j, text in enumerate(BANDS):
                key = f"band-{j}"
                axis(
                    key,
                    "column",
                    text,
                    j,
                    ("panel",),
                    ("pd-definition",) if j < 7 else (),
                    (FragmentRef(band_physical.revision_id, str(j)),),
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
                    ("245", "299"),
                    ("303", "355"),
                    ("357", "416"),
                    ("421", "477"),
                    ("481", "533"),
                )[i]
                header = physical(
                    tid + "/" + key + "/header",
                    "region",
                    page,
                    title,
                    box=(left, "96", right, "130"),
                )
            else:
                header = physical(
                    tid + "/" + key + "/header",
                    "paragraph",
                    page,
                    title,
                    start=text,
                    end="\n",
                )
            physicals.append(header)
            header_slot = (FragmentRef(header.revision_id, "text"),)
            occurrences.append(
                OccurrenceBinding(
                    address(tid, "field", key), header_slot, context_refs=context_refs
                )
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
                    [("history_window", quals[0])]
                    if backtest
                    else [("measurement", "measurement")]
                )
                if key in ("actual_pd", "estimated_lgd", "actual_lgd"):
                    roles.append(
                        (
                            "outcome_window",
                            "pd-cutoff" if key == "actual_pd" else "lgd-cutoff",
                        )
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
            scopes["framework"] = (SourceEndpoint("dataset", tid),)
            scopes["lgd-review"] = ()
            scopes.update(
                {
                    q: tuple(
                        SourceEndpoint("field", k) for k, _, _, qs in specs if q in qs
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
            source = (
                matrix.source_reference
                if q in ("regulatory-basis", "nz-separation")
                else next(
                    p.source_reference for p in physicals if p.revision_id == q + "@1"
                )
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
            # Unscoped evidence remains reachable without asserting applicability.
            if not endpoints:
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
            q = physical(
                tid + "/undrawn",
                "paragraph",
                page,
                title,
                start=EXPOSURE_FIELDS[1][1],
                end="\n",
            )
            physicals.append(q)
            notes.append(
                Qualification(
                    "undrawn",
                    "",
                    (q.source_reference,),
                    (SourceEndpoint("field", "undrawn"),),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, "comment", "undrawn"),
                    (FragmentRef(q.revision_id, "text"),),
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
                    tuple(descriptors),
                    tuple(temporal),
                ),
                (),
            )
        )
    for key, targets in comment_targets.items():
        slot = (
            FragmentRef(
                matrix.revision_id, "mortgage" if key == "regulatory-basis" else "nz"
            )
            if key in ("regulatory-basis", "nz-separation")
            else FragmentRef(key + "@1", "text")
        )
        links = tuple(OccurrenceLink("qualifies", target) for target in targets)
        if key in ("regulatory-basis", "nz-separation"):
            row = "mortgage" if key == "regulatory-basis" else "nz"
            links += tuple(
                OccurrenceLink(
                    "evidence", address(None, "column", "matrix/" + row + "/" + col)
                )
                for col in ("asset", "borrower", "pre", "post")
            )
        occurrences.append(
            OccurrenceBinding(address(None, "comment", key), (slot,), links=links)
        )
    for column in ("asset", "borrower", "pre", "post"):
        occurrences.append(
            OccurrenceBinding(
                address(None, "header", "matrix/header/" + column),
                (FragmentRef(matrix.revision_id, "header/" + column),),
            )
        )
        for row in ("mortgage", "nz"):
            occurrences.append(
                OccurrenceBinding(
                    address(None, "column", "matrix/" + row + "/" + column),
                    (FragmentRef(matrix.revision_id, row + "/" + column),),
                    links=(
                        OccurrenceLink(
                            "header", address(None, "header", "matrix/header/" + column)
                        ),
                    ),
                )
            )
    snapshot = CaptureSnapshot(
        "anz-2023-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
    )
    document = SourceDocument(
        DOCUMENT,
        "raw/anz-2023-09-30-aps330.pdf",
        "anz",
        "ANZ BH Pty Ltd (ANZ Bank HoldCo)",
        "Basel III Pillar 3 Disclosure As at 30 September 2023",
        date(2023, 9, 30),
        None,
        "au",
        "https://www.anz.com/content/dam/anzcom/shareholder/2023-september-pillar-3-disclosure.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        "extractions/au/anz/2023-09-30/aps330/extract.py",
        tuple(tables),
        snapshot,
    )


DEFINITION = build()
