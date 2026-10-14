"""Reviewed FY23 source declarations, independent of PDF execution and later vintages."""

import re
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

DOCUMENT = "cba-2023-06-30-aps330"
BUNDLE = "au/cba/2023-06-30/aps330"
PORTFOLIO = "Residential mortgage"
EXPOSURE_TITLE = "Table 9d (ii) – Retail exposures by portfolio type and PD band"
BANDS = (
    "0 < 0.1%",
    "0.1% < 0.3%",
    "0.3% < 0.5%",
    "0.5% < 3%",
    "3% < 10%",
    "10% < 100%",
    "Default",
    "Total",
)
BOUNDS = (
    ("0", "0.1"),
    ("0.1", "0.3"),
    ("0.3", "0.5"),
    ("0.5", "3"),
    ("3", "10"),
    ("10", "100"),
)
COMMON = ("report-entity", "level-2", "regulatory-basis")
LEFT = ("40", "60", "300", "795")
RIGHT = ("300", "60", "560", "795")


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, str(page - 2) if page > 2 else "", location, row, column
    )


def address(scope, kind, key):
    return OccurrenceRef(BUNDLE, scope, kind, key)


def physical(key, operation, page, location, *, row=None, **parameters):
    return PhysicalBinding(
        key + "@1",
        operation,
        tuple(PhysicalParameter(k, v) for k, v in parameters.items()),
        ref(page, location, row),
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
    "cba-2023/common@1",
    (
        assertion(
            "reporting_entity", "CBA and its subsidiaries (the Group)", "report-entity"
        ),
        assertion("consolidation_scope", "Level 2", "level-2"),
        assertion("regulatory_scope", "IRB", "regulatory-basis"),
        assertion("geography", None),
        assertion("currency", None),
    ),
    evidence=(
        ref(4, "Introduction"),
        ref(45, "Portfolios Subject to Internal Ratings-based Approaches"),
    ),
)


def build():
    physicals = [
        physical(
            "report-entity",
            "paragraph",
            4,
            "Introduction",
            start="This document is prepared",
            end="It presents",
        ),
        physical(
            "level-2",
            "paragraph",
            4,
            "Introduction",
            start="The Group is required to report",
            end="The Group is predominantly",
        ),
    ]
    # Cropped columns prevent interleaving unrelated prose in the PDF text layer.
    for key, page, box, start, end in (
        (
            "regulatory-basis",
            45,
            LEFT,
            "The Group, with the exception",
            "Credit Risk Measurement",
        ),
        ("pd-horizon", 45, LEFT, "The PD, expressed", "The PD rating methodology"),
        (
            "pd-long-run",
            45,
            LEFT,
            "PD estimates are based",
            "Borrower or counterparty risk",
        ),
        ("lgd-definition", 46, LEFT, "LGD is estimated", "Amounts recovered"),
        (
            "lgd-downturn",
            46,
            RIGHT,
            "For calculating regulatory capital",
            "It is recognised",
        ),
        (
            "default-definition",
            46,
            LEFT,
            "Common PD, EAD and LGD",
            "Loss Given Default",
        ),
        (
            "ead-definition",
            46,
            RIGHT,
            "EAD is the estimate",
            "For non-defaulted committed",
        ),
        (
            "prior-framework",
            5,
            LEFT,
            "As a result of receiving",
            "Portfolios that attract",
        ),
    ):
        physicals.append(
            physical(key, "region", page, key, box=box, start=start, end=end)
        )
    for key, start, end in (
        ("framework", "The following tables", "Probability of Default"),
        ("pd-history", "Table 9f (ii) compares", "Average estimated PD is based"),
        ("pd-cohort", "Average estimated PD is based", "Table 9f (ii) –"),
        ("lgd-history", "LGDs for non-retail", "The EAD ratio"),
        ("ead-history", "The EAD ratio", "Table 9f (iii) –"),
    ):
        physicals.append(physical(key, "paragraph", 57, key, start=start, end=end))
    physicals.append(
        physical(
            "lgd-floor",
            "line",
            57,
            "Footnote 2",
            after="Table 9f (iii) –",
            pattern=r"^2 (?P<text>Estimated downturn LGD.*)$",
        )
    )
    shared = {p.revision_id[:-2]: p for p in physicals}
    targets = {key: [] for key in shared}
    occurrences, tables, contexts = [], [], [COMMON_CONTEXT]

    def shared_notes(tid, scopes):
        notes = []
        for key, endpoints in scopes.items():
            notes.append(
                Qualification(key, "", (shared[key].source_reference,), endpoints)
            )
            targets[key].extend(
                address(
                    tid,
                    {"dataset": "table", "band": "column"}.get(e.kind, e.kind),
                    e.id,
                )
                for e in endpoints
            )
        return notes

    def finish(
        tid,
        title,
        label,
        template,
        page,
        axes,
        fields,
        notes,
        relationships,
        descriptors,
        bindings,
        axis_slots,
        field_slots,
        extra=(),
        segmentations=(),
    ):
        context_id = BUNDLE + "/" + tid + "/context@1"
        context_refs = (COMMON_CONTEXT.revision_id, context_id)
        context = TableContext(
            "context",
            date(2023, 6, 30),
            label,
            template,
            title,
            PORTFOLIO,
            *(
                Knowledge(a.value, a.status, tuple(e.ref_id for e in a.evidence_refs))
                for a in COMMON_CONTEXT.attributes
            ),
            (*COMMON, *extra),
            (ref(1, "Cover"), ref(page, title)),
        )
        contexts.append(
            ContextDefinition(
                context_id, temporal=tuple(descriptors), evidence=context.evidence
            )
        )
        title_reader = physical(
            tid + "/title",
            "line",
            page,
            title,
            pattern=r"^(?P<text>" + re.escape(title) + r")$",
        )
        physicals.append(title_reader)
        occurrences.append(
            OccurrenceBinding(
                address(tid, "table", tid),
                (FragmentRef(title_reader.revision_id, "text"),),
                context_refs,
            )
        )
        for a in axes:
            occurrences.append(
                OccurrenceBinding(
                    address(tid, a.axis, a.id), (axis_slots[a.id],), context_refs
                )
            )
        for f in fields:
            occurrences.append(
                OccurrenceBinding(
                    address(tid, "field", f.id), (field_slots[f.id],), context_refs
                )
            )
        temporal = []
        for binding, role, descriptor in bindings:
            occurrences.append(
                replace(
                    binding,
                    context_refs=context_refs,
                    temporal_roles=(TemporalRole(role, context_id, descriptor),),
                )
            )
            temporal.append(CellTemporalBinding(binding.ref.local_id, role, descriptor))
        tables.append(
            SourceTable(
                tid,
                SourceTableMetadata(
                    context,
                    tuple(axes),
                    tuple(fields),
                    tuple(segmentations),
                    tuple(notes),
                    tuple(relationships),
                    tuple(descriptors),
                    tuple(temporal),
                ),
                (),
            )
        )

    for page, day, label, current in (
        (51, "2023-06-30", "30 June 2023 Revised Framework ¹", True),
        (52, "2022-12-31", "31 December 2022", False),
        (53, "2022-06-30", "30 June 2022", False),
    ):
        tid = "table9d-ii-" + day
        title = EXPOSURE_TITLE + ("" if current else " (continued)")
        specs = (
            ("exposure", "Total credit risk exposures", "$M", ()),
            (
                "undrawn",
                "Undrawn commitments " + ("²" if current else "¹"),
                "$M",
                ("undrawn",),
            ),
            ("average_ead", "Exposure - average EAD ($M)", "$M", ("ead-definition",)),
            (
                "lgd",
                "Exposure - weighted average LGD (%)",
                "%",
                (("overlay",) if current else ()) + ("lgd-definition", "lgd-downturn"),
            ),
            (
                "risk_weight",
                "Exposure - weighted average risk weight (%) "
                + ("³" if current else "²"),
                "%",
                ("scaling",),
            ),
        )
        axes, fields, relationships, bindings, bands = [], [], [], [], []
        axis_slots, field_slots = {}, {}
        for key, text, order, path in (
            ("panel", label, 0, ()),
            ("pd-bands", "PD Band", 1, ("panel",)),
        ):
            reader = physical(
                tid + "/" + key,
                "line",
                page,
                title,
                pattern=r"^(?P<text>" + re.escape(text) + r")$",
            )
            physicals.append(reader)
            axis_slots[key] = FragmentRef(reader.revision_id, "text")
            axes.append(
                SourceAxisItem(
                    key,
                    "header",
                    text,
                    order,
                    path,
                    ("context",),
                    ("revised-framework",) if key == "panel" and current else (),
                    ref(page, title),
                )
            )
        reader = physical(
            tid + "/bands",
            "bands",
            page,
            title,
            prefix="0 < 0.1%",
            pattern=r"[\d.]+%? < [\d.]+%|Default|Total",
        )
        physicals.append(reader)
        for j, text in enumerate(BANDS):
            key = f"band-{j}"
            quals = ("pd-horizon", "pd-long-run") if j < 7 else ()
            if j == 6:
                quals += ("default-definition",)
            axes.append(
                SourceAxisItem(
                    key,
                    "column",
                    text,
                    j,
                    ("panel", "pd-bands"),
                    ("context",),
                    quals,
                    ref(page, title, column=text),
                )
            )
            axis_slots[key] = FragmentRef(reader.revision_id, str(j))
            bands.append(
                BandDefinition(
                    key,
                    text,
                    j,
                    "interval" if j < 6 else "default" if j == 6 else "category",
                    "%",
                    Decimal(BOUNDS[j][0]) if j < 6 else None,
                    Decimal(BOUNDS[j][1]) if j < 6 else None,
                    None,
                    False if j < 6 else None,
                    "established" if j < 6 else "not_applicable",
                    "established" if j < 6 else "not_applicable",
                    None if j < 6 else text,
                    ref(page, title, column=text),
                )
            )
        scopes = {q: (SourceEndpoint("dataset", tid),) for q in COMMON}
        scopes.update(
            {
                q: tuple(SourceEndpoint("band", f"band-{j}") for j in range(7))
                for q in ("pd-horizon", "pd-long-run")
            }
        )
        scopes.update(
            {
                q: (SourceEndpoint("field", "lgd"),)
                for q in ("lgd-definition", "lgd-downturn")
            }
        )
        scopes.update(
            {
                "default-definition": (SourceEndpoint("band", "band-6"),),
                "ead-definition": (SourceEndpoint("field", "average_ead"),),
            }
        )
        if not current:
            scopes["prior-framework"] = (SourceEndpoint("dataset", tid),)
        notes = shared_notes(tid, scopes)
        values = physical(
            tid + "/values",
            "rows",
            page,
            title,
            after=title,
            prefix=PORTFOLIO,
            columns=8,
            labels=BANDS,
        )
        physicals.append(values)
        for i, (key, text, unit, quals) in enumerate(specs):
            header = physical(
                tid + "/" + key + "/header",
                "line",
                page,
                title,
                after=label,
                pattern=r"^(?P<text>" + re.escape(text) + r")$",
            )
            physicals.append(header)
            slot = FragmentRef(header.revision_id, "text")
            field_slots[key] = axis_slots[key] = slot
            row = PORTFOLIO + (" ⁴" if key == "lgd" and current else "")
            fields.append(
                TableField(
                    key,
                    text,
                    ("panel", key),
                    unit,
                    Decimal("1000000" if unit == "$M" else "1"),
                    quals,
                    (SemanticAttribute("counted_entity", None, "unresolved", ()),)
                    if key == "average_ead"
                    else (),
                    ref(page, title, row=text),
                    "decimal",
                    "money" if unit == "$M" else "scalar",
                )
            )
            axes.extend(
                (
                    SourceAxisItem(
                        key,
                        "block",
                        text,
                        i,
                        ("panel",),
                        ("context",),
                        quals,
                        ref(page, title),
                    ),
                    SourceAxisItem(
                        key + "-mortgage",
                        "row",
                        row,
                        i,
                        ("panel", key),
                        ("context",),
                        quals,
                        ref(page, title, row=row),
                    ),
                )
            )
            axis_slots[key + "-mortgage"] = FragmentRef(values.revision_id, f"row/{i}")
            for j in range(8):
                cid = key + f"/band-{j}"
                bindings.append(
                    (
                        OccurrenceBinding(
                            address(tid, "cell", cid),
                            (FragmentRef(values.revision_id, f"{i}/{j}"),),
                            cell=CellBinding(
                                key,
                                key + "-mortgage",
                                f"band-{j}",
                                (f"band-{j}",),
                                quals,
                            ),
                        ),
                        "measurement",
                        "measurement",
                    )
                )
            relationships.append(
                SourceRelationship(
                    "total-" + key,
                    "total",
                    "Total",
                    SourceEndpoint("cell", key + "/band-7"),
                    tuple(SourceEndpoint("cell", key + f"/band-{j}") for j in range(7)),
                    (SourceEndpoint("field", key),),
                    None,
                    None,
                    (ref(page, title, column="Total"),),
                )
            )
        for j in range(8):
            relationships.append(
                SourceRelationship(
                    f"undrawn-{j}",
                    "subset",
                    "included in Total credit risk exposures",
                    SourceEndpoint("cell", f"exposure/band-{j}"),
                    (SourceEndpoint("cell", f"undrawn/band-{j}"),),
                    (SourceEndpoint("band", f"band-{j}"),),
                    None,
                    None,
                    (ref(page, "Footnote " + ("2" if current else "1")),),
                )
            )
        for key, number, kind, target, pattern in (
            ("undrawn", "2" if current else "1", "field", "undrawn", r".*"),
            (
                "scaling",
                "3" if current else "2",
                "field",
                "risk_weight",
                r"Includes (?P<number>[\d.]+) scaling factor\.",
            ),
            *(
                (
                    (
                        "overlay",
                        "4",
                        "field",
                        "lgd",
                        r"Excludes a \$(?P<number>[\d.]+).*",
                    ),
                    ("revised-framework", "1", "dataset", tid, r".*"),
                )
                if current
                else ()
            ),
        ):
            reader = physical(
                tid + "/" + key,
                "line",
                page,
                "Footnote " + number,
                pattern="^" + number + " (?P<text>" + pattern + ")$",
            )
            physicals.append(reader)
            notes.append(
                Qualification(
                    key, "", (reader.source_reference,), (SourceEndpoint(kind, target),)
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, "comment", key),
                    (FragmentRef(reader.revision_id, "text"),),
                    links=(
                        OccurrenceLink(
                            "qualifies",
                            address(
                                tid, "table" if kind == "dataset" else kind, target
                            ),
                        ),
                    ),
                )
            )
            if key not in ("overlay", "scaling"):
                continue
            text = (
                "Excludes a $7.4 billion RWA overlay that has been applied at 30 June 2023 for regulatory capital purposes."
                if key == "overlay"
                else "Includes " + ("1.10" if current else "1.06") + " scaling factor."
            )
            fields.append(
                TableField(
                    key,
                    text,
                    (),
                    "$ billion" if key == "overlay" else "ratio",
                    Decimal("1000000000" if key == "overlay" else "1"),
                    (key,),
                    (),
                    ref(page, "Footnote " + number),
                    "decimal",
                    "money" if key == "overlay" else "scalar",
                    "note",
                )
            )
            field_slots[key] = FragmentRef(reader.revision_id, "text")
            bindings.append(
                (
                    OccurrenceBinding(
                        address(tid, "cell", key),
                        (FragmentRef(reader.revision_id, "number"),),
                        links=(
                            OccurrenceLink("evidence", address(tid, "comment", key)),
                        ),
                        cell=CellBinding(key, None, None, qualification_refs=(key,)),
                    ),
                    "measurement",
                    "measurement",
                )
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
        finish(
            tid,
            title,
            label,
            "Table 9d(ii)",
            page,
            axes,
            fields,
            notes,
            relationships,
            descriptors,
            bindings,
            axis_slots,
            field_slots,
            ("revised-framework" if current else "prior-framework",),
            (
                SegmentationDefinition(
                    "pd-bands",
                    "PD Band",
                    tuple(bands),
                    ("context",),
                    Knowledge(),
                    Knowledge(),
                    (ref(page, title),),
                ),
            ),
        )

    for kind in ("ii", "iii"):
        is_pd = kind == "ii"
        page, label = 57, "30 June 2023"
        tid = f"table9f-{kind}-2023-06-30"
        title = f"Table 9f ({kind}) – Accuracy of risk estimates – " + (
            "PD" if is_pd else "LGD and EAD"
        )
        row = PORTFOLIO + (" ¹" if is_pd else " ² ³")
        specs = (
            (
                (
                    "estimated_pd",
                    "Average estimated PD",
                    "%",
                    ("pd-history", "pd-cohort", "restatement"),
                ),
                (
                    "actual_pd",
                    "Average actual PD",
                    "%",
                    ("pd-history", "pd-cohort", "restatement"),
                ),
            )
            if is_pd
            else (
                (
                    "estimated_lgd",
                    "Average estimated downturn LGD",
                    "%",
                    ("lgd-history", "lgd-floor", "restatement"),
                ),
                (
                    "actual_lgd",
                    "Average actual LGD",
                    "%",
                    ("lgd-history", "restatement"),
                ),
                (
                    "ead_ratio",
                    "Ratio of estimated EAD to actual EAD",
                    "ratio",
                    ("ead-history", "restatement"),
                ),
            )
        )
        scopes = {q: (SourceEndpoint("dataset", tid),) for q in (*COMMON, "framework")}
        for q in (
            ("pd-history", "pd-cohort")
            if is_pd
            else ("lgd-history", "ead-history", "lgd-floor")
        ):
            scopes[q] = tuple(
                SourceEndpoint("field", key) for key, _, _, qs in specs if q in qs
            )
        notes = shared_notes(tid, scopes)
        restatement = physical(
            tid + "/restatement",
            "line",
            page,
            "Footnote " + ("1" if is_pd else "3"),
            row=row,
            after=title,
            pattern=r"^" + ("1" if is_pd else "3") + r" (?P<text>Historical data.*)$",
        )
        physicals.append(restatement)
        notes.append(
            Qualification(
                "restatement",
                "",
                (restatement.source_reference,),
                (SourceEndpoint("row", "mortgage"),),
            )
        )
        occurrences.append(
            OccurrenceBinding(
                address(tid, "comment", "restatement"),
                (FragmentRef(restatement.revision_id, "text"),),
                links=(OccurrenceLink("qualifies", address(tid, "row", "mortgage")),),
            )
        )
        descriptors = (
            (
                TemporalDescriptor(
                    "history",
                    "from 2016",
                    start="2016",
                    start_status="established",
                    qualification_refs=("pd-history", "pd-cohort"),
                    evidence=(ref(page, "Probability of Default"),),
                ),
            )
            if is_pd
            else (
                TemporalDescriptor(
                    "lgd-history",
                    "2016 to 2022 financial years",
                    start="2016",
                    end="2022",
                    start_status="established",
                    end_status="established",
                    qualification_refs=("lgd-history",),
                    evidence=(ref(page, "Loss Given Default and Exposure at Default"),),
                ),
                TemporalDescriptor(
                    "ead-history",
                    "The EAD ratio compares estimates of EAD prior to default to realised EAD for borrowers that defaulted.",
                    qualification_refs=("ead-history",),
                    evidence=(ref(page, "EAD ratio"),),
                ),
            )
        )
        axes, fields, bindings, axis_slots, field_slots = [], [], [], {}, {}
        panel = physical(
            tid + "/panel",
            "line",
            page,
            title,
            after=title,
            pattern=r"^(?P<text>30 June 2023)$",
        )
        portfolio = physical(
            tid + "/portfolio",
            "line",
            page,
            title,
            after=title,
            pattern=r"^(?P<text>Portfolio Type) % %$",
        )
        values = physical(
            tid + "/values",
            "rows",
            page,
            title,
            after=title,
            prefix=PORTFOLIO,
            columns=len(specs),
            labels=tuple(s[1] for s in specs),
            before="Loss Given Default and Exposure at Default"
            if is_pd
            else "1 Average estimated LGD",
        )
        physicals.extend((panel, portfolio, values))
        axes.extend(
            (
                SourceAxisItem(
                    "panel", "header", label, 0, (), ("context",), (), ref(page, title)
                ),
                SourceAxisItem(
                    "portfolio",
                    "header",
                    "Portfolio Type",
                    1,
                    (),
                    ("context",),
                    (),
                    ref(page, title),
                ),
                SourceAxisItem(
                    "mortgage",
                    "row",
                    row,
                    0,
                    ("panel", "portfolio"),
                    ("context",),
                    ("restatement",),
                    ref(page, title, row=row),
                ),
            )
        )
        axis_slots.update(
            panel=FragmentRef(panel.revision_id, "text"),
            portfolio=FragmentRef(portfolio.revision_id, "text"),
            mortgage=FragmentRef(values.revision_id, "row/0"),
        )
        boxes = (
            (("428", "237", "475", "254"), ("492", "237", "534", "254"))
            if is_pd
            else (
                ("358", "547", "411", "572"),
                ("416", "547", "469", "572"),
                ("474", "547", "530", "572"),
            )
        )
        for i, (key, text, unit, quals) in enumerate(specs):
            header = physical(
                tid + "/" + key + "/header", "region", page, title, box=boxes[i]
            )
            physicals.append(header)
            field_slots[key] = axis_slots[key] = FragmentRef(header.revision_id, "text")
            fields.append(
                TableField(
                    key,
                    text,
                    ("panel", key),
                    unit,
                    Decimal(1),
                    quals,
                    (),
                    ref(page, title, column=text),
                    "decimal",
                    "scalar",
                )
            )
            axes.append(
                SourceAxisItem(
                    key,
                    "column",
                    text,
                    i,
                    ("panel",),
                    ("context",),
                    quals,
                    ref(page, title, column=text),
                )
            )
            bindings.append(
                (
                    OccurrenceBinding(
                        address(tid, "cell", "mortgage/" + key),
                        (FragmentRef(values.revision_id, f"0/{i}"),),
                        cell=CellBinding(
                            key, "mortgage", key, qualification_refs=quals
                        ),
                    ),
                    "history_window",
                    "history"
                    if is_pd
                    else "ead-history"
                    if key == "ead_ratio"
                    else "lgd-history",
                )
            )
        finish(
            tid,
            title,
            label,
            f"Table 9f({kind})",
            page,
            axes,
            fields,
            notes,
            (),
            descriptors,
            bindings,
            axis_slots,
            field_slots,
            ("framework",),
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
    document = SourceDocument(
        DOCUMENT,
        "raw/cba-2023-06-30-aps330.pdf",
        "cba",
        "Commonwealth Bank of Australia",
        "Basel III Pillar 3 – Capital Adequacy and Risk Disclosures as at 30 June 2023",
        date(2023, 6, 30),
        None,
        "au",
        "https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy23/CBA-FY23-Basel-III-Pillar-3-Disclosure.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        "extractions/au/cba/2023-06-30/aps330/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "cba-2023-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
        ),
    )


DEFINITION = build()
