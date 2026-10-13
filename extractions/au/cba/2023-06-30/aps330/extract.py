"""CBA FY23 mortgage panels, including the pre-reform comparatives and backtesting."""

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

DOCUMENT = "cba-2023-06-30-aps330"
PORTFOLIO = "Residential mortgage"
COMMON = (
    (
        "report-entity",
        4,
        "This document is prepared for CBA and its subsidiaries (the Group) in accordance with a Board approved policy and APRA Prudential Standard (APS) 330 Public Disclosure (APS 330).",
    ),
    (
        "level-2",
        4,
        "The Group is required to report its assessment of capital adequacy on a Level 2 basis. Level 2 is defined as the Consolidated Banking Group excluding the insurance business and certain entities through which securitisation of Group assets is conducted.",
    ),
    (
        "regulatory-basis",
        45,
        "The Group, with the exception of some relatively small portfolios, is accredited to use Internal Ratings-based approaches to calculate its capital requirements under APS 113 Capital Adequacy: Internal Ratings-based Approach to Credit Risk (APS 113).",
    ),
)
DEFINITIONS = (
    (
        "pd-horizon",
        45,
        "The PD, expressed as a percentage, is the estimate of the population of borrowers or counterparties assigned to a PD grade that will default within a one year period. It reflects a borrower’s ability to generate sufficient cash flows in the future to meet the terms of all of its credit obligations to the Group.",
        "band",
        tuple(f"band-{j}" for j in range(7)),
    ),
    (
        "pd-long-run",
        45,
        "PD estimates are based on a long-run average default rate based on the Group’s historical data, supplemented with external data where applicable.",
        "band",
        tuple(f"band-{j}" for j in range(7)),
    ),
    (
        "lgd-definition",
        46,
        "LGD is estimated as the net present value of the post default loss, including an allowance for internal and external costs, expressed as a percentage of the EAD.",
        "field",
        ("lgd",),
    ),
    (
        "lgd-downturn",
        46,
        "For calculating regulatory capital an estimated downturn LGD is used that reflects likely recovery rates under stressed economic conditions.",
        "field",
        ("lgd",),
    ),
    (
        "default-definition",
        46,
        "Common PD, EAD and LGD methodologies are followed in constructing the internal ratings process for residential mortgages, qualifying revolving retail exposures and other retail advances with the default definition applied when payment on a facility is 90 days or more past due, or there are indications of unlikeliness to pay (e.g. a write-off amount exists against the facility).",
        "band",
        ("band-6",),
    ),
    (
        "ead-definition",
        46,
        "EAD is the estimate of the amount of a facility that will be outstanding in the event of default. For defaulted facilities, it is the actual amount outstanding at the time of default.",
        "field",
        ("average_ead",),
    ),
)


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, str(page - 2) if page > 2 else "", location, row, column
    )


def note(id, text, page, kind, targets, row=None):
    return Qualification(
        id,
        text,
        (ref(page, id, row),),
        tuple(SourceEndpoint(kind, target) for target in targets),
    )


def paragraph(text, start, end):
    return " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())


def footnote(text, number):
    return next(
        line[len(number) + 1 :]
        for line in text.splitlines()
        if line.startswith(number + " ")
    )


def context(title, template, label, page, extra):
    return TableContext(
        "context",
        date(2023, 6, 30),
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
        ("report-entity", "level-2", "regulatory-basis", *extra),
        (ref(1, "Cover"), ref(page, title)),
    )


def common_notes(id):
    return [note(key, quote, page, "dataset", (id,)) for key, page, quote in COMMON]


def axis(id, kind, label, order, page, title, parents=(), quals=()):
    return SourceAxisItem(
        id,
        kind,
        label,
        order,
        parents,
        ("context",),
        quals,
        ref(
            page,
            title,
            label if kind == "row" else None,
            label if kind == "column" else None,
        ),
    )


def field(id, label, unit, scale, page, title, quals=(), attrs=(), form="table_body"):
    return TableField(
        id,
        label,
        ("panel", id) if form == "table_body" else (),
        unit,
        Decimal(scale),
        quals,
        attrs,
        ref(
            page,
            title,
            label if title.startswith("Table 9d") else None,
            label if title.startswith("Table 9f") else None,
        ),
        "decimal",
        "money" if unit.startswith("$") else "scalar",
        form,
    )


def cell(
    id,
    f,
    token,
    page,
    title,
    row=None,
    column=None,
    row_label=None,
    column_label=None,
    segments=(),
    quals=(),
):
    value = parse_decimal_token(token)
    return SourceCell(
        id,
        f.id,
        row,
        column,
        ("context",),
        segments,
        quals,
        "decimal",
        ReportedValue(
            value,
            token,
            max(0, -value.as_tuple().exponent) if value is not None else None,
            None
            if value is not None
            else "dash_unresolved"
            if token
            else "blank_unresolved",
            ref(page, title, row_label, column_label),
        ),
    )


def exposure(text, page, panel_date):
    """FY23 changes are explicit here: heading, markers, framework and note inventory."""
    current = panel_date == "2023-06-30"
    id = "table9d-ii-" + panel_date
    title = next(line for line in text.splitlines() if line.startswith("Table 9d (ii)"))
    label = next(
        line
        for line in text.splitlines()
        if re.match(r"(?:30 June|31 December) 202[23]", line)
    )
    specs = (
        ("exposure", "Total credit risk exposures", "$M", "1000000", ()),
        (
            "undrawn",
            "Undrawn commitments " + ("²" if current else "¹"),
            "$M",
            "1000000",
            ("undrawn",),
        ),
        (
            "average_ead",
            "Exposure - average EAD ($M)",
            "$M",
            "1000000",
            ("ead-definition",),
        ),
        (
            "lgd",
            "Exposure - weighted average LGD (%)",
            "%",
            "1",
            (("overlay",) if current else ()) + ("lgd-definition", "lgd-downturn"),
        ),
        (
            "risk_weight",
            "Exposure - weighted average risk weight (%) " + ("³" if current else "²"),
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
        axis(
            "panel",
            "header",
            label,
            0,
            page,
            title,
            quals=("revised-framework",) if current else (),
        ),
        axis("pd-bands", "header", "PD Band", 1, page, title, ("panel",)),
    ]
    bands = []
    for j, band_label in enumerate(labels):
        bid = f"band-{j}"
        quals = ("pd-horizon", "pd-long-run") if j < 7 else ()
        if j == 6:
            quals += ("default-definition",)
        axes.append(
            axis(
                bid, "column", band_label, j, page, title, ("panel", "pd-bands"), quals
            )
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
    notes = common_notes(id)
    notes.extend(
        note(key, quote, p, kind, targets)
        for key, p, quote, kind, targets in DEFINITIONS
    )
    notes.extend(
        (
            note(
                "undrawn",
                footnote(text, "2" if current else "1"),
                page,
                "field",
                ("undrawn",),
            ),
            note(
                "scaling",
                footnote(text, "3" if current else "2"),
                page,
                "field",
                ("risk_weight",),
            ),
        )
    )
    extra = ()
    if current:
        notes.extend(
            (
                note("overlay", footnote(text, "4"), page, "field", ("lgd",)),
                note("revised-framework", footnote(text, "1"), page, "dataset", (id,)),
            )
        )
        extra = ("revised-framework",)
    else:
        notes.append(
            note(
                "prior-framework",
                "As a result of receiving advanced Basel II accreditation, the Group predominantly used the AIRB approach for credit risk and the AMA for operational risk in the calculation of RWA from 1 January 2008 until 31 December 2022.",
                5,
                "dataset",
                (id,),
            )
        )
        extra = ("prior-framework",)
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
        f = field(key, name, unit, scale, page, title, quals, attrs)
        fields.append(f)
        row_label = PORTFOLIO + (" ⁴" if key == "lgd" and current else "")
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
                    token,
                    page,
                    title,
                    key + "-mortgage",
                    bid,
                    row_label,
                    labels[j],
                    (bid,),
                    quals,
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
    quotes = {q.id: q.source_text for q in notes}
    numeric_notes = [
        ("scaling", "ratio", "1", re.search(r"Includes ([\d.]+)", quotes["scaling"])[1])
    ]
    if current:
        numeric_notes.insert(
            0,
            (
                "overlay",
                "$ billion",
                "1000000000",
                re.search(r"\$([\d.]+)", quotes["overlay"])[1],
            ),
        )
    for key, unit, scale, token in numeric_notes:
        f = field(key, quotes[key], unit, scale, page, key, (key,), form="note")
        fields.append(f)
        cells.append(cell(key, f, token, page, key, quals=(key,)))
    metadata = SourceTableMetadata(
        context(title, "Table 9d(ii)", label, page, extra),
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
        (
            TemporalDescriptor(
                "measurement",
                label,
                point=panel_date,
                point_status="established",
                evidence=(ref(page, "Panel heading"),),
            ),
        ),
        tuple(CellTemporalBinding(c.id, "measurement", "measurement") for c in cells),
    )
    return SourceTable(id, metadata, tuple(cells))


def backtesting(text, kind):
    page, label = 57, "30 June 2023"
    id = f"table9f-{kind}-2023-06-30"
    title = next(
        line for line in text.splitlines() if line.startswith(f"Table 9f ({kind}) –")
    )
    is_pd = kind == "ii"
    row_label = PORTFOLIO + (" ¹" if is_pd else " ² ³")
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
            ("actual_lgd", "Average actual LGD", "%", ("lgd-history", "restatement")),
            (
                "ead_ratio",
                "Ratio of estimated EAD to actual EAD",
                "ratio",
                ("ead-history", "restatement"),
            ),
        )
    )
    notes = common_notes(id)
    notes.append(
        note(
            "framework",
            paragraph(text, "The following tables", "Probability of Default"),
            page,
            "dataset",
            (id,),
        )
    )
    notes.append(
        note(
            "restatement",
            footnote(text, "1" if is_pd else "3"),
            page,
            "row",
            ("mortgage",),
            row_label,
        )
    )
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
                quotes["ead-history"],
                qualification_refs=("ead-history",),
                evidence=(ref(page, "EAD ratio"),),
            ),
        )
    for key, quote in quotes.items():
        notes.append(
            note(
                key,
                quote,
                page,
                "field",
                tuple(name for name, _, _, qs in specs if key in qs),
            )
        )
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("portfolio", "header", "Portfolio Type", 1, page, title),
        axis(
            "mortgage",
            "row",
            row_label,
            0,
            page,
            title,
            ("panel", "portfolio"),
            ("restatement",),
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
        f = field(key, name, unit, "1", page, title, quals)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, ("panel",), quals))
        c = cell(
            "mortgage/" + key,
            f,
            token,
            page,
            title,
            "mortgage",
            key,
            row_label,
            name,
            quals=quals,
        )
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
    return SourceTable(
        id,
        SourceTableMetadata(
            context(title, f"Table 9f({kind})", label, page, ("framework",)),
            tuple(axes),
            tuple(fields),
            (),
            tuple(notes),
            (),
            descriptors,
            tuple(bindings),
        ),
        tuple(cells),
    )


def extract(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tables = [
            exposure(pdf.pages[page - 1].extract_text(), page, day)
            for page, day in (
                (51, "2023-06-30"),
                (52, "2022-12-31"),
                (53, "2022-06-30"),
            )
        ]
        text = pdf.pages[56].extract_text()
        tables.extend(backtesting(text, kind) for kind in ("ii", "iii"))
    return ExtractionBundle(
        SourceDocument(
            DOCUMENT,
            "raw/cba-2023-06-30-aps330.pdf",
            "cba",
            "Commonwealth Bank of Australia",
            "Basel III Pillar 3 – Capital Adequacy and Risk Disclosures as at 30 June 2023",
            date(2023, 6, 30),
            None,
            "au",
            "https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy23/CBA-FY23-Basel-III-Pillar-3-Disclosure.pdf",
        ),
        "au/cba/2023-06-30/aps330",
        "extractions/au/cba/2023-06-30/aps330/extract.py",
        "disclosure-v3",
        tuple(tables),
    )
