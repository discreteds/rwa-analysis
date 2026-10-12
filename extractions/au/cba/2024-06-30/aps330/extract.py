"""Bespoke CBA FY24 mortgage selection: tables 9d(ii), 9f(ii) and 9f(iii)."""

import re
from datetime import date
from decimal import Decimal

import pdfplumber

from rwa_analysis.extraction.datasets import ExtractionBundle
from rwa_analysis.extraction.models import (
    BandDefinition,
    Knowledge,
    Qualification,
    ReportedValue,
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
    SourceCell,
    SourceTable,
    SourceTableMetadata,
    TableContext,
    TableField,
)
from rwa_analysis.extraction.temporal import TemporalDescriptor
from rwa_analysis.extraction.values import parse_decimal_token

DOCUMENT = "cba-2024-06-30-aps330"
PORTFOLIO = "Residential mortgage"


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, str(page - 2) if page > 2 else "", location, row, column
    )


def paragraph(text, start, end):
    return " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())


def note(id, text, page, scope=(), row=None):
    return Qualification(id, text, (ref(page, id, row),), scope)


def context(id, title, template, label, page):
    return TableContext(
        "context",
        date(2024, 6, 30),
        label,
        template,
        title,
        PORTFOLIO,
        Knowledge(
            "CBA and its subsidiaries (the Group)", "established", ("report-entity",)
        ),
        Knowledge("Level 2", "established", ("level-2",)),
        Knowledge("IRB", "established", ("regulatory-basis",)),
        Knowledge(),
        Knowledge(),
        ("report-entity", "level-2", "regulatory-basis"),
        (ref(1, "Cover"), ref(page, title)),
    )


def common_notes(id):
    scope = (SourceEndpoint("dataset", id),)
    return (
        note(
            "report-entity",
            "This document is prepared for CBA and its subsidiaries (the Group) in accordance with a Board approved policy and reporting requirements set out in APRA Prudential Standard (APS) APS 330 Public Disclosure (APS 330).",
            4,
            scope,
        ),
        note(
            "level-2",
            "The Group is required to report its assessment of capital adequacy on a Level 2 basis. Level 2 is defined as the Consolidated Banking Group excluding an insurance entity and certain entities through which securitisation of Group assets is conducted.",
            4,
            scope,
        ),
        note(
            "regulatory-basis",
            "The Group, with the exception of some relatively small portfolios, is accredited to use Internal Ratings-based approaches to calculate its capital requirements under APS 113 Capital Adequacy: Internal Ratings-based Approach to Credit Risk (APS 113).",
            43,
            scope,
        ),
    )


def axis(id, kind, label, order, page, title, parents=(), qualifications=()):
    return SourceAxisItem(
        id,
        kind,
        label,
        order,
        parents,
        ("context",),
        qualifications,
        ref(
            page,
            title,
            label if kind == "row" else None,
            label if kind == "column" else None,
        ),
    )


def field(
    id, label, unit, scale, page, title, path, quals=(), attrs=(), form="table_body"
):
    return TableField(
        id,
        label,
        path,
        unit,
        Decimal(scale),
        quals,
        attrs,
        ref(
            page,
            title,
            row=label if title.startswith("Table 9d") else None,
            column=label if title.startswith("Table 9f") else None,
        ),
        "decimal",
        "money" if unit.startswith("$") else "scalar",
        form,
    )


def cell(
    id,
    f,
    row,
    column,
    token,
    page,
    title,
    segments=(),
    quals=(),
    row_label=PORTFOLIO,
    column_label=None,
):
    value = parse_decimal_token(token)
    reported = ReportedValue(
        value,
        token,
        max(0, -value.as_tuple().exponent) if value is not None else None,
        None
        if value is not None
        else "dash_unresolved"
        if token
        else "blank_unresolved",
        ref(page, title, row_label, column_label or f.source_label),
    )
    return SourceCell(
        id, f.id, row, column, ("context",), segments, quals, "decimal", reported
    )


def exposure(text, page, panel_date, label):
    id = "table9d-ii-" + panel_date
    title = next(line for line in text.splitlines() if line.startswith("Table 9d (ii)"))
    specs = (
        ("exposure", "Total credit risk exposures", "$M", "1000000", ()),
        ("undrawn", "Undrawn commitments ¹", "$M", "1000000", ("undrawn",)),
        ("average_ead", "Exposure - average EAD ($M)", "$M", "1000000", ()),
        (
            "lgd",
            "Exposure - weighted average LGD (%)",
            "%",
            "1",
            ("overlay", "lgd-definition"),
        ),
        (
            "risk_weight",
            "Exposure - weighted average risk weight (%) ³",
            "%",
            "1",
            ("scaling",),
        ),
    )
    band_line = next(line for line in text.splitlines() if line.startswith("0 < 0.1%"))
    labels = tuple(re.findall(r"[\d.]+%? < [\d.]+%|Default|Total", band_line))
    bounds = (
        ("0", "0.1"),
        ("0.1", "0.3"),
        ("0.3", "0.5"),
        ("0.5", "3"),
        ("3", "10"),
        ("10", "100"),
    )
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("pd-bands", "header", "PD Band", 1, page, title, ("panel",)),
    ]
    bands = []
    for j, band_label in enumerate(labels):
        bid = f"band-{j}"
        axes.append(
            axis(bid, "column", band_label, j, page, title, ("panel", "pd-bands"))
        )
        bands.append(
            BandDefinition(
                bid,
                band_label,
                j,
                "interval" if j < 6 else "default" if j == 6 else "category",
                "%",
                Decimal(bounds[j][0]) if j < 6 else None,
                Decimal(bounds[j][1]) if j < 6 else None,
                None,
                False if j < 6 else None,
                "established" if j < 6 else "not_applicable",
                "established" if j < 6 else "not_applicable",
                None if j < 6 else band_label,
                ref(page, title, column=band_label),
            )
        )
    notes = list(common_notes(id))
    for key, num, scopes in (
        ("undrawn", "1", ("undrawn",)),
        ("overlay", "2", ("lgd",)),
        ("scaling", "3", ("risk_weight",)),
    ):
        quoted = next(
            line[len(num) + 1 :]
            for line in text.splitlines()
            if line.startswith(num + " ")
        )
        notes.append(
            note(key, quoted, page, tuple(SourceEndpoint("field", f) for f in scopes))
        )
    notes.extend(
        (
            note(
                "lgd-definition",
                "LGD is estimated as the net present value of the post default loss, including an allowance for internal and external costs, expressed as a percentage of the EAD.",
                44,
                (SourceEndpoint("field", "lgd"),),
            ),
            note(
                "default-definition",
                "Common PD, EAD and LGD methodologies are followed in constructing the internal ratings process for residential mortgages, qualifying revolving retail exposures and other retail advances with the default definition applied when payment on a facility is 90 days or more past due, or there are indications of unlikeliness to pay (e.g. a write-off amount exists against the facility).",
                44,
                (SourceEndpoint("band", "band-6"),),
            ),
            note(
                "ead-definition",
                "EAD is the estimate of the amount of a facility that will be outstanding in the event of default. For defaulted facilities, it is the actual amount outstanding at the time of default.",
                44,
                (SourceEndpoint("field", "average_ead"),),
            ),
        )
    )
    rows = [line for line in text.splitlines() if line.startswith(PORTFOLIO)]
    fields, cells, relationships = [], [], []
    for i, ((key, name, unit, scale, quals), line) in enumerate(
        zip(specs, rows, strict=True)
    ):
        attrs = (
            (SemanticAttribute("counted_entity", None, "unresolved", ()),)
            if key == "average_ead"
            else ()
        )
        f = field(key, name, unit, scale, page, title, ("panel", key), quals, attrs)
        fields.append(f)
        row_label = PORTFOLIO + (" ²" if key == "lgd" else "")
        axes.extend(
            (
                axis(key, "block", name, i, page, title, ("panel",), quals),
                axis(
                    key + "-mortgage",
                    "row",
                    row_label,
                    i,
                    page,
                    title,
                    ("panel", key),
                    quals,
                ),
            )
        )
        for j, token in enumerate(line.split()[-8:]):
            bid = f"band-{j}"
            cells.append(
                cell(
                    key + "/" + bid,
                    f,
                    key + "-mortgage",
                    bid,
                    token,
                    page,
                    title,
                    (bid,),
                    quals,
                    row_label,
                    labels[j],
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
                (ref(page, "Footnote 1"),),
            )
        )
    quoted = {q.id: q.source_text for q in notes}
    for key, unit, scale, token in (
        (
            "overlay",
            "$ billion",
            "1000000000",
            re.search(r"\$([\d.]+)", quoted["overlay"])[1],
        ),
        (
            "scaling",
            "ratio",
            "1",
            re.search(r"Includes ([\d.]+)", quoted["scaling"])[1],
        ),
    ):
        f = field(key, quoted[key], unit, scale, page, key, (), (key,), form="note")
        fields.append(f)
        cells.append(
            cell(key, f, None, None, token, page, key, quals=(key,), row_label=None)
        )
    descriptor = TemporalDescriptor(
        "measurement",
        label,
        point=panel_date,
        point_status="established",
        evidence=(ref(page, "Panel heading"),),
    )
    meta = SourceTableMetadata(
        context(id, title, "Table 9d(ii)", label, page),
        tuple(axes),
        tuple(fields),
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
        tuple(notes),
        tuple(relationships),
        (descriptor,),
        tuple(CellTemporalBinding(c.id, "measurement", "measurement") for c in cells),
    )
    return SourceTable(id, meta, tuple(cells))


def backtesting(text, kind):
    page, label = 56, "30 June 2024"
    id = f"table9f-{kind}-2024-06-30"
    title = next(
        line for line in text.splitlines() if line.startswith(f"Table 9f ({kind}) –")
    )
    is_pd = kind == "ii"
    specs = (
        (
            ("estimated_pd", "Average estimated PD", "%", ("pd-history", "pd-cohort")),
            ("actual_pd", "Average actual PD", "%", ("pd-history", "pd-cohort")),
        )
        if is_pd
        else (
            (
                "estimated_lgd",
                "Average estimated downturn LGD",
                "%",
                ("lgd-history", "lgd-floor"),
            ),
            ("actual_lgd", "Average actual LGD", "%", ("lgd-history",)),
            (
                "ead_ratio",
                "Ratio of estimated EAD to actual EAD",
                "ratio",
                ("ead-history",),
            ),
        )
    )
    framework = paragraph(text, "The following tables", "Probability of Default")
    notes = [
        *common_notes(id),
        note("framework", framework, page, (SourceEndpoint("dataset", id),)),
    ]
    if is_pd:
        quotes = {
            "pd-history": paragraph(
                text, "Table 9f (ii) compares", "Average estimated PD is based"
            ),
            "pd-cohort": paragraph(
                text, "Average estimated PD is based", "Table 9f (ii) –"
            ),
        }
        descriptors = (
            TemporalDescriptor(
                "history",
                "from 2016",
                start="2016",
                start_status="established",
                qualification_refs=("pd-history", "pd-cohort"),
                evidence=(ref(page, "Probability of Default"),),
            ),
        )
        restatement = "pd-restatement"
        restatement_text = next(
            line[2:]
            for line in text.splitlines()
            if line.startswith("2 Historical observed PD")
        )
        restatement_row = "RBNZ regulated entities: Retail ²"
    else:
        quotes = {
            "lgd-history": paragraph(text, "LGDs for non-retail", "The EAD ratio"),
            "ead-history": paragraph(text, "The EAD ratio", "Table 9f (iii) –"),
            "lgd-floor": next(
                line[2:]
                for line in text.splitlines()
                if line.startswith("2 Estimated downturn LGD")
            ),
        }
        descriptors = (
            TemporalDescriptor(
                "lgd-history",
                "2016 to 2023 financial years",
                start="2016",
                end="2023",
                start_status="established",
                end_status="established",
                qualification_refs=("lgd-history",),
                evidence=(ref(page, "Loss Given Default and Exposure at Default"),),
            ),
            TemporalDescriptor(
                "ead-history",
                quotes["ead-history"],
                qualification_refs=("ead-history",),
                evidence=(ref(page, "EAD ratio"),),
            ),
        )
        restatement = "lgd-restatement"
        restatement_text = next(
            line[2:]
            for line in text.splitlines()
            if line.startswith("3 Historical observed LGD")
        )
        restatement_row = "RBNZ regulated entities: Retail ³"
    for key, quote in quotes.items():
        notes.append(
            note(
                key,
                quote,
                page,
                tuple(
                    SourceEndpoint("field", name)
                    for name, _, _, qs in specs
                    if key in qs
                ),
            )
        )
    notes.append(note(restatement, restatement_text, page, row=restatement_row))
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("portfolio", "header", "Portfolio Type", 1, page, title),
        axis(
            "mortgage",
            "row",
            PORTFOLIO + (" ²" if not is_pd else ""),
            0,
            page,
            title,
            ("panel", "portfolio"),
        ),
    ]
    line = next(
        line
        for line in text.split(title, 1)[1].splitlines()
        if line.startswith(PORTFOLIO)
    )
    fields, cells, bindings = [], [], []
    for j, ((key, name, unit, quals), token) in enumerate(
        zip(specs, line.split()[-len(specs) :], strict=True)
    ):
        attrs = (
            (
                SemanticAttribute(
                    "restatement_applicability", None, "unresolved", (restatement,)
                ),
            )
            if key in ("actual_pd", "actual_lgd")
            else ()
        )
        f = field(key, name, unit, "1", page, title, ("panel", key), quals, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, ("panel",), quals))
        c = cell("mortgage/" + key, f, "mortgage", key, token, page, title, quals=quals)
        cells.append(c)
        bindings.append(
            CellTemporalBinding(
                c.id,
                "history_window",
                "history"
                if is_pd
                else "ead-history"
                if key == "ead_ratio"
                else "lgd-history",
            )
        )
    meta = SourceTableMetadata(
        context(id, title, f"Table 9f({kind})", label, page),
        tuple(axes),
        tuple(fields),
        (),
        tuple(notes),
        (),
        descriptors,
        tuple(bindings),
    )
    return SourceTable(id, meta, tuple(cells))


def extract(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tables = [
            exposure(pdf.pages[page - 1].extract_text(), page, day, label)
            for page, day, label in (
                (49, "2024-06-30", "30 June 2024"),
                (50, "2023-12-31", "31 December 2023"),
                (51, "2023-06-30", "30 June 2023"),
            )
        ]
        text = pdf.pages[55].extract_text()
        tables.extend(backtesting(text, k) for k in ("ii", "iii"))
    document = SourceDocument(
        DOCUMENT,
        "raw/cba-2024-06-30-aps330.pdf",
        "cba",
        "Commonwealth Bank of Australia",
        "Basel III Pillar 3 – Capital Adequacy and Risk Disclosures as at 30 June 2024",
        date(2024, 6, 30),
        None,
        "au",
        "https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy24/CBA-FY24-Basel-III-Pillar-3-Disclosure.pdf",
    )
    return ExtractionBundle(
        document,
        "au/cba/2024-06-30/aps330",
        "extractions/au/cba/2024-06-30/aps330/extract.py",
        "disclosure-v3",
        tuple(tables),
    )
