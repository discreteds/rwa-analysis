"""ANZ September 2024: selected mortgage rows of Tables 9(d) and 9(f)."""

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

DOCUMENT = "anz-2024-09-30-aps330"
PORTFOLIO = "Residential Mortgage"


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page - 1), location, row, column)


def paragraph(text, start, end):
    return " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())


def qualification(key, text, page, scope, location=None):
    return Qualification(key, text, (ref(page, location or key),), scope)


def common_notes(texts, dataset):
    scope = (SourceEndpoint("dataset", dataset),)
    specs = (
        ("report-entity", 4, "This document is prepared", "It presents"),
        ("level-2", 4, "The APS 330 disclosure", "Any reference"),
        ("currency", 4, "Unless otherwise stated", "Suncorp Bank Acquisition"),
        ("suncorp", 46, "On 31 July 2024", "\n45"),
        ("regulatory-basis", 46, "Residential Mortgages", "Qualifying Revolving"),
        (
            "default-definition",
            28,
            "ANZ uses the following definition",
            "Non-performing facilities",
        ),
    )
    notes = [
        qualification(key, paragraph(texts[page], start, end), page, scope)
        for key, page, start, end in specs
    ]
    targets = (
        ("ead_ratio",)
        if dataset.startswith("table9f")
        else ("exposure", "undrawn", "average_ead")
    )
    notes.append(
        qualification(
            "ead-net-offsets",
            paragraph(texts[27], "Unless otherwise stated", "Past due facilities"),
            27,
            tuple(SourceEndpoint("field", key) for key in targets),
            "Exposure at Default (EAD)",
        )
    )
    return notes


def context(label, title, template, page):
    return TableContext(
        "context",
        date(2024, 9, 30),
        label,
        template,
        title,
        PORTFOLIO,
        Knowledge(
            "ANZ BH Pty Ltd (ANZ Bank HoldCo)", "established", ("report-entity",)
        ),
        Knowledge("Level 2", "established", ("level-2",)),
        Knowledge("AIRB", "established", ("regulatory-basis",)),
        Knowledge(),
        Knowledge("AUD", "established", ("currency",)),
        (
            "report-entity",
            "level-2",
            "currency",
            "regulatory-basis",
            "suncorp",
            "default-definition",
        ),
        (ref(4, "Purpose of this document"), ref(page, title)),
    )


def axis(key, kind, label, order, page, title, path=(), quals=()):
    return SourceAxisItem(
        key,
        kind,
        label,
        order,
        path,
        ("context",),
        quals,
        ref(
            page,
            title,
            label if kind == "row" else None,
            label if kind == "column" else None,
        ),
    )


def field(key, label, unit, page, title, quals=(), attrs=()):
    return TableField(
        key,
        label,
        ("panel", key),
        unit,
        Decimal("1000000" if unit == "$M" else "1"),
        quals,
        attrs,
        ref(
            page,
            title,
            label if title.startswith("Table 9(d)") else None,
            label if title.startswith("Table 9(f)") else None,
        ),
        "decimal",
        "money" if unit == "$M" else "scalar",
    )


def cell(key, f, row, column, token, page, title, label, segments=()):
    value = parse_decimal_token(token.rstrip("%"))
    reported = ReportedValue(
        value,
        token,
        max(0, -value.as_tuple().exponent) if value is not None else None,
        None
        if value is not None
        else "dash_unresolved"
        if token
        else "blank_unresolved",
        ref(page, title, PORTFOLIO, label),
    )
    return SourceCell(
        key,
        f.id,
        row,
        column,
        ("context",),
        segments,
        f.qualification_refs,
        "decimal",
        reported,
    )


def exposure(texts, page, day, label):
    text = texts[page]
    dataset = "table9d-" + day
    title = next(line for line in text.splitlines() if line.startswith("Table 9(d)"))
    if "(continued)" in text:
        title += " (continued)"
    specs = (
        ("exposure", "Exposure at Default", "$M", ("ead-definition", "ead-glossary")),
        ("undrawn", "Undrawn commitments (included in above)", "$M", ("undrawn",)),
        (
            "average_ead",
            "Average Exposure at Default",
            "$M",
            ("ead-definition", "ead-glossary"),
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
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("0.00%"))
    lower, upper = lines[header].split(), lines[header + 1].split()
    labels = [lower[j] + "\n" + upper[j] for j in range(6)] + lower[6:]
    axes = [axis("panel", "header", label, 0, page, title)]
    bands = []
    for j, band_label in enumerate(labels):
        key = f"band-{j}"
        axes.append(
            axis(
                key,
                "column",
                band_label,
                j,
                page,
                title,
                ("panel",),
                ("pd-definition",) if j < 7 else (),
            )
        )
        bands.append(
            BandDefinition(
                key,
                band_label,
                j,
                "interval" if j < 6 else "default" if j == 6 else "category",
                "%",
                Decimal(lower[j].rstrip("%")) if j < 6 else None,
                Decimal(upper[j].strip("<%")) if j < 6 else None,
                None,
                False if j < 6 else None,
                "established" if j < 6 else "not_applicable",
                "established" if j < 6 else "not_applicable",
                None if j < 6 else band_label,
                ref(page, title, column=band_label),
            )
        )
    notes = common_notes(texts, dataset)
    for key, p, start, end, targets in (
        (
            "pd-definition",
            47,
            "PD is an estimate",
            " EAD",
            tuple(SourceEndpoint("band", f"band-{j}") for j in range(7)),
        ),
        (
            "ead-definition",
            49,
            "EAD represents",
            "\n48",
            tuple(SourceEndpoint("field", k) for k in ("exposure", "average_ead")),
        ),
        (
            "ead-glossary",
            100,
            "Exposure At Default is defined",
            "Impaired assets",
            tuple(SourceEndpoint("field", k) for k in ("exposure", "average_ead")),
        ),
        (
            "lgd-definition",
            47,
            "LGD is an estimate",
            "Effective maturity",
            (SourceEndpoint("field", "lgd"),),
        ),
        (
            "regulatory-adjustments",
            48,
            "For the wholesale asset class",
            "Controls surrounding",
            tuple(SourceEndpoint("field", k) for k in ("lgd", "risk_weight")),
        ),
    ):
        notes.append(qualification(key, paragraph(texts[p], start, end), p, targets))
    notes.append(
        qualification(
            "undrawn", specs[1][1], page, (SourceEndpoint("field", "undrawn"),), title
        )
    )
    rows = [line for line in lines if line.startswith(PORTFOLIO)]
    fields, cells, relationships = [], [], []
    for i, ((key, name, unit, quals), line) in enumerate(zip(specs, rows, strict=True)):
        attrs = (
            (SemanticAttribute("counted_entity", None, "unresolved", ()),)
            if key == "average_ead"
            else ()
        )
        f = field(key, name, unit, page, title, quals, attrs)
        fields.append(f)
        axes.extend(
            (
                axis(key, "block", name, i, page, title, ("panel",), quals),
                axis(
                    key + "-mortgage",
                    "row",
                    PORTFOLIO,
                    i,
                    page,
                    title,
                    ("panel", key),
                    quals,
                ),
            )
        )
        for j, token in enumerate(line.split()[-8:]):
            band = f"band-{j}"
            cells.append(
                cell(
                    key + "/" + band,
                    f,
                    key + "-mortgage",
                    band,
                    token,
                    page,
                    title,
                    labels[j],
                    (band,),
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
                (ref(page, title, PORTFOLIO, "Total"),),
            )
        )
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
                (ref(page, specs[1][1], PORTFOLIO, labels[j]),),
            )
        )
    temporal = TemporalDescriptor(
        "measurement",
        label,
        point=day,
        point_status="established",
        evidence=(ref(page, title),),
    )
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context(label, title, "Table 9(d)", page),
            tuple(axes),
            tuple(fields),
            (
                SegmentationDefinition(
                    "risk-grades",
                    "risk grade",
                    tuple(bands),
                    ("context",),
                    Knowledge(),
                    Knowledge(),
                    (ref(page, title),),
                ),
            ),
            tuple(notes),
            tuple(relationships),
            (temporal,),
            tuple(
                CellTemporalBinding(c.id, "measurement", "measurement") for c in cells
            ),
        ),
        tuple(cells),
    )


def backtesting(texts):
    page, dataset = 57, "table9f-2024-09-30"
    text = texts[page]
    title = next(line for line in text.splitlines() if line.startswith("Table 9(f)"))
    retail = text.split("Retail Portfolios", 1)[1]
    specs = (
        ("estimated_pd", "Average Estimated PD %", "%", "pd-history"),
        ("actual_pd", "Average Actual PD %", "%", "pd-history"),
        ("ead_ratio", "Average estimated to actual EAD ratio", "ratio", "ead-history"),
        ("estimated_lgd", "Average Estimated LGD %", "%", "lgd-history"),
        ("actual_lgd", "Average Actual LGD %", "%", "lgd-history"),
    )
    notes = common_notes(texts, dataset)
    notes.append(
        qualification(
            "framework",
            paragraph(text, "APS 330 Table 9(f)", "Estimated PD and LGD"),
            page,
            (SourceEndpoint("dataset", dataset),),
            title,
        )
    )
    for key, start, end in (
        ("pd-history", "The estimated PD", "The EAD ratio"),
        ("ead-history", "The EAD ratio", "The estimated LGD"),
        ("lgd-history", "The estimated LGD", "\n56"),
    ):
        notes.append(
            qualification(
                key,
                paragraph(retail, start, end),
                page,
                tuple(SourceEndpoint("field", k) for k, _, _, q in specs if q == key),
                "Retail Portfolios",
            )
        )
    notes.append(
        qualification(
            "lgd-review",
            paragraph(text, "A review of historical", "Retail Portfolios"),
            page,
            (),
            "Wholesale Portfolios",
        )
    )
    axes = [
        axis("panel", "header", "Sep 24", 0, page, title),
        axis("portfolio", "header", "Portfolio Type", 1, page, title),
        axis("mortgage", "row", PORTFOLIO, 0, page, title, ("portfolio",)),
    ]
    tokens = next(
        line for line in text.splitlines() if line.startswith(PORTFOLIO)
    ).split()[-5:]
    fields, cells, bindings = [], [], []
    for i, ((key, name, unit, qual), token) in enumerate(
        zip(specs, tokens, strict=True)
    ):
        attrs = (
            (
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
        f = field(key, name, unit, page, title, (qual,), attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, i, page, title, ("panel",), (qual,)))
        c = cell("mortgage/" + key, f, "mortgage", key, token, page, title, name)
        cells.append(c)
        bindings.append(
            CellTemporalBinding(
                c.id,
                "history_window",
                "lgd-history" if "lgd" in key else "pd-ead-history",
            )
        )
        if key in ("actual_pd", "estimated_lgd", "actual_lgd"):
            bindings.append(
                CellTemporalBinding(c.id, "outcome_window", "default-cutoff")
            )
    descriptors = (
        TemporalDescriptor(
            "pd-ead-history",
            "2019 to 2023",
            start="2019",
            end="2023",
            start_status="established",
            end_status="established",
            qualification_refs=("pd-history", "ead-history"),
            evidence=(ref(page, "Retail Portfolios"),),
        ),
        TemporalDescriptor(
            "lgd-history",
            "2018 to 2022",
            start="2018",
            end="2022",
            start_status="established",
            end_status="established",
            qualification_refs=("lgd-history",),
            evidence=(ref(page, "Retail Portfolios"),),
        ),
        TemporalDescriptor(
            "default-cutoff",
            "up to September 2023 / Defaults occurring after September 2023 have been excluded",
            end="2023-09",
            end_status="established",
            qualification_refs=("pd-history", "lgd-history"),
            evidence=(ref(page, "Retail Portfolios"),),
        ),
    )
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context("Sep 24", title, "Table 9(f)", page),
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
        texts = {
            p: pdf.pages[p - 1].extract_text()
            for p in (4, 27, 28, 46, 47, 48, 49, 53, 54, 55, 57, 100)
        }
    tables = [
        exposure(texts, p, day, label)
        for p, day, label in (
            (53, "2024-09-30", "Sep 24"),
            (54, "2024-03-31", "Mar 24"),
            (55, "2023-09-30", "Sep 23"),
        )
    ]
    tables.append(backtesting(texts))
    return ExtractionBundle(
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
        "au/anz/2024-09-30/aps330",
        "extractions/au/anz/2024-09-30/aps330/extract.py",
        "disclosure-v3",
        tuple(tables),
    )
