"""ANZ September 2023 mortgage Tables 9(d)/9(f), including reform comparatives."""

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

DOCUMENT = "anz-2023-09-30-aps330"
PORTFOLIO = "Residential Mortgage"


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page - 1), location, row, column)


def paragraph(text, start, end):
    return " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())


def qualification(key, text, page, scope, location=None):
    return Qualification(key, text, (ref(page, location or key),), scope)


def reform_matrix(page):
    # Explicit outside edges retain the asset-class and post-reform columns.
    rows = page.extract_tables(
        {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": [78.84, 175.98, 367.44, 449.76, 532.44],
            "horizontal_strategy": "lines",
        }
    )[0]
    headers = [" ".join(value.split()) for value in rows[0]]
    lines = page.extract_text().splitlines()
    notes = {}
    for key, section, asset in (
        ("regulatory-basis", "Remains post-January", "Residential Mortgages"),
        ("nz-separation", "New from January", "Exposures of New"),
    ):
        # Section headings span cells; read them without artificial vertical splits.
        heading = next(line for line in lines if line.startswith(section))
        row = next(row for row in rows if row[0] and row[0].startswith(asset))
        notes[key] = "\n".join(
            [heading]
            + [
                header + ": " + " ".join(value.split())
                for header, value in zip(headers, row, strict=True)
            ]
        )
    return notes


def common_notes(texts, dataset, matrix):
    specs = (
        ("report-entity", 4, "This document is prepared for", "It presents"),
        ("restructure", 4, "On 3 January 2023", "The APS 330 disclosure"),
        ("level-2", 4, "The APS 330 disclosure", "Basel in ANZ"),
        ("capital-reform", 4, "APRA released new", "In addition, operational"),
        (
            "comparative-basis",
            4,
            "The revisions to the prudential",
            "The application of APRA",
        ),
        ("currency", 5, "Unless otherwise stated", "Suncorp Bank Acquisition"),
        (
            "default-definition",
            30,
            "ANZ uses the following definition",
            "Non-performing facilities",
        ),
    )
    notes = [
        qualification(
            key,
            paragraph(texts[p], start, end),
            p,
            (SourceEndpoint("dataset", dataset),),
        )
        for key, p, start, end in specs
    ]
    notes.extend(
        qualification(
            key,
            text,
            45,
            (SourceEndpoint("dataset", dataset),),
            "Table 9 IRB asset class / rating approach matrix",
        )
        for key, text in matrix.items()
    )
    targets = (
        ("ead_ratio",)
        if dataset.startswith("table9f")
        else ("exposure", "undrawn", "average_ead")
    )
    notes.append(
        qualification(
            "ead-net-offsets",
            paragraph(texts[29], "Unless otherwise stated", "Past due facilities"),
            29,
            tuple(SourceEndpoint("field", k) for k in targets),
            "Exposure at Default (EAD)",
        )
    )
    return notes


def context(label, title, template, page):
    # The source explicitly names the former Level-2 parent for prior years.
    entity = (
        "Australia and New Zealand Banking Group Limited"
        if label == "Sep 22"
        else "ANZ BH Pty Ltd (ANZ Bank HoldCo)"
    )
    return TableContext(
        "context",
        date(2023, 9, 30),
        label,
        template,
        title,
        PORTFOLIO,
        Knowledge(entity, "established", ("level-2", "report-entity")),
        Knowledge("Level 2", "established", ("level-2",)),
        Knowledge("AIRB", "established", ("regulatory-basis",)),
        Knowledge(),
        Knowledge("AUD", "established", ("currency",)),
        (
            "report-entity",
            "restructure",
            "level-2",
            "capital-reform",
            "comparative-basis",
            "currency",
            "regulatory-basis",
            "nz-separation",
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


def exposure(texts, page, day, label, matrix):
    text = texts[page]
    dataset = "table9d-" + day
    title = next(line for line in text.splitlines() if line.startswith("Table 9(d)"))
    if "(continued)" in text:
        title += " (continued)"
    specs = (
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
    notes = common_notes(texts, dataset, matrix)
    for key, p, start, end, targets in (
        (
            "pd-definition",
            46,
            "PD is an estimate",
            " EAD",
            tuple(SourceEndpoint("band", f"band-{j}") for j in range(7)),
        ),
        (
            "ead-definition",
            48,
            "EAD represents",
            "\n47",
            tuple(SourceEndpoint("field", k) for k in ("exposure", "average_ead")),
        ),
        (
            "ead-glossary",
            96,
            "Exposure At Default is defined",
            "Impaired assets",
            tuple(SourceEndpoint("field", k) for k in ("exposure", "average_ead")),
        ),
        (
            "lgd-definition",
            46,
            "LGD is an estimate",
            "Effective maturity",
            (SourceEndpoint("field", "lgd"),),
        ),
        (
            "regulatory-adjustments",
            47,
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


def backtesting(texts, matrix):
    page, dataset = 56, "table9f-2023-09-30"
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
    notes = common_notes(texts, dataset, matrix)
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
        ("lgd-history", "The estimated LGD", "\n55"),
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
        axis("panel", "header", "Sep 23", 0, page, title),
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
        quals = (qual, "ead-net-offsets") if key == "ead_ratio" else (qual,)
        f = field(key, name, unit, page, title, quals, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, i, page, title, ("panel",), quals))
        c = cell("mortgage/" + key, f, "mortgage", key, token, page, title, name)
        cells.append(c)
        bindings.append(CellTemporalBinding(c.id, "history_window", qual))
        if key in ("actual_pd", "estimated_lgd", "actual_lgd"):
            bindings.append(
                CellTemporalBinding(
                    c.id,
                    "outcome_window",
                    "pd-cutoff" if key == "actual_pd" else "lgd-cutoff",
                )
            )
    descriptors = [
        TemporalDescriptor(
            key,
            label,
            start=start,
            end=end,
            start_status="established",
            end_status="established",
            qualification_refs=(key,),
            evidence=(ref(page, "Retail Portfolios"),),
        )
        for key, label, start, end in (
            ("pd-history", "2018 to 2022", "2018", "2022"),
            ("ead-history", "2018 to 2023", "2018", "2023"),
            ("lgd-history", "2017 to 2021", "2017", "2021"),
        )
    ]
    descriptors.extend(
        TemporalDescriptor(
            key,
            label,
            end=end,
            end_status="established",
            qualification_refs=(qual,),
            evidence=(ref(page, "Retail Portfolios"),),
        )
        for key, label, end, qual in (
            ("pd-cutoff", "up to September 2023", "2023-09", "pd-history"),
            (
                "lgd-cutoff",
                "Defaults occurring after September 2022 have been excluded",
                "2022-09",
                "lgd-history",
            ),
        )
    )
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context("Sep 23", title, "Table 9(f)", page),
            tuple(axes),
            tuple(fields),
            (),
            tuple(notes),
            (),
            tuple(descriptors),
            tuple(bindings),
        ),
        tuple(cells),
    )


def extract(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        texts = {
            p: pdf.pages[p - 1].extract_text()
            for p in (4, 5, 29, 30, 45, 46, 47, 48, 52, 53, 54, 56, 96)
        }
        matrix = reform_matrix(pdf.pages[44])
    tables = [
        exposure(texts, p, day, label, matrix)
        for p, day, label in (
            (52, "2023-09-30", "Sep 23"),
            (53, "2023-03-31", "Mar 23"),
            (54, "2022-09-30", "Sep 22"),
        )
    ]
    tables.append(backtesting(texts, matrix))
    return ExtractionBundle(
        SourceDocument(
            DOCUMENT,
            "raw/anz-2023-09-30-aps330.pdf",
            "anz",
            "ANZ BH Pty Ltd (ANZ Bank HoldCo)",
            "Basel III Pillar 3 Disclosure As at 30 September 2023",
            date(2023, 9, 30),
            None,
            "au",
            "https://www.anz.com/content/dam/anzcom/shareholder/2023-september-pillar-3-disclosure.pdf",
        ),
        "au/anz/2023-09-30/aps330",
        "extractions/au/anz/2023-09-30/aps330/extract.py",
        "disclosure-v3",
        tuple(tables),
    )
