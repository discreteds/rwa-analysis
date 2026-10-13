"""NAB FY24 mortgage source tables, including separately named RBNZ mortgages."""

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

DOCUMENT = "nab-2024-09-30-aps330"
PORTFOLIO = "Residential mortgage"


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page - 2), location, row, column)


def quote(text, start, end):
    return " ".join((start + text.split(start, 1)[1].split(end, 1)[0]).split())


def note(key, text, page, scope):
    return Qualification(key, text, (ref(page, key),), scope)


def endpoints(kind, *ids):
    return tuple(SourceEndpoint(kind, key) for key in ids)


def common_notes(texts, id):
    scope = endpoints("dataset", id)
    return [
        note(
            "report-entity",
            quote(texts[4], "This document describes", "Amounts are"),
            4,
            scope,
        ),
        note(
            "currency",
            quote(texts[4], "Amounts are presented", "Capital adequacy methodologies"),
            4,
            scope,
        ),
        note(
            "level-2",
            "This report applies to the Level 2 Group, headed by NAB, unless otherwise stated.",
            4,
            scope,
        ),
    ]


def context(title, template, label, page, exposure=False):
    return TableContext(
        "context",
        date(2024, 9, 30),
        label,
        template,
        title,
        PORTFOLIO,
        Knowledge("NAB and its controlled entities", "established", ("report-entity",)),
        Knowledge("Level 2", "established", ("level-2",)),
        Knowledge("advanced IRB", "established", ("approach",))
        if exposure
        else Knowledge(),
        Knowledge(),
        Knowledge("AUD", "established", ("currency",)),
        ("report-entity", "currency", "level-2"),
        (ref(4, "Introduction"), ref(page, title)),
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


def field(key, label, unit, page, title, quals=(), attrs=(), transposed=False):
    return TableField(
        key,
        label,
        ("panel", key),
        unit,
        Decimal("1000000" if unit == "$m" else "1"),
        quals,
        attrs,
        ref(page, title, label if transposed else None, None if transposed else label),
        "decimal",
        "money" if unit == "$m" else "scalar",
        "table_body",
    )


def cell(
    key, f, row, col, token, page, title, row_label, column_label, quals=(), segments=()
):
    value = parse_decimal_token(token)
    return SourceCell(
        key,
        f.id,
        row,
        col,
        ("context",),
        segments,
        quals,
        "decimal",
        ReportedValue(
            value,
            token,
            max(0, -value.as_tuple().exponent) if value is not None else None,
            None if value is not None else "dash_unresolved",
            ref(page, title, row_label, column_label),
        ),
    )


def exposure(texts, page, day, label):
    text = texts[page]
    id = "table5-3-b-" + day
    title = "Table 5.3.B Retail exposures by risk grade"
    notes = common_notes(texts, id)
    specs = (
        ("exposure", "Exposure at default", "$m", ("ead-definition",)),
        ("undrawn", "Undrawn commitments", "$m", ("undrawn",)),
        (
            "average_ead",
            "Average exposure at default ($m)",
            "$m",
            ("average-arrangements", "ead-definition"),
        ),
        (
            "lgd",
            "Exposure-weighted average LGD (%)",
            "%",
            ("lgd-definition", "lgd-downturn", "retail-lgd"),
        ),
        ("risk_weight", "Exposure-weighted average risk-weight (%)", "%", ("overlay",)),
    )
    for key, start, end, targets in (
        ("undrawn", "Undrawn commitments are included", "\n(", ("undrawn",)),
        ("average-arrangements", "Simple average of exposure", "\n(", ("average_ead",)),
        ("overlay", "RWA overlay adjustments", "\n", ("risk_weight",)),
    ):
        notes.append(
            note(key, quote(text, start, end), page, endpoints("field", *targets))
        )
    if page == 50:
        notes.append(
            note(
                "pd-model-change",
                quote(text, "In the six months ended", "\n(2)"),
                page,
                endpoints("field", "exposure", "undrawn"),
            )
        )
    notes.extend(
        [
            note(
                "approach",
                "Subject to advanced IRB approach",
                page,
                endpoints("dataset", id),
            ),
            note(
                "pd-horizon",
                "PD measures the likelihood that a customer will default within a 12-month period.",
                45,
                endpoints("band", *(f"band-{j}" for j in range(6))),
            ),
            note(
                "pd-through-cycle",
                quote(texts[46], "Through-the-cycle,", "The Group has"),
                46,
                endpoints("band", *(f"band-{j}" for j in range(6))),
            ),
            note(
                "ead-definition",
                quote(texts[46], "EaD is calculated", "Credit rating system control"),
                46,
                endpoints("field", "exposure", "average_ead"),
            ),
            note(
                "ead-glossary",
                "An estimate of the credit exposure amount outstanding if a customer defaults. EaD is presented net of eligible financial collateral, except where indicated.",
                76,
                endpoints("field", "exposure", "average_ead"),
            ),
            note(
                "lgd-definition",
                quote(texts[46], "LGD measures", "The Group applies stresses"),
                46,
                endpoints("field", "lgd"),
            ),
            note(
                "lgd-downturn",
                quote(texts[46], "The Group applies stresses", "Exposure at default"),
                46,
                endpoints("field", "lgd"),
            ),
            note(
                "retail-lgd",
                quote(texts[47], "Key account variables", "Full Year Pillar"),
                47,
                endpoints("field", "lgd"),
            ),
            note(
                "default-definition",
                "Aligned to the definition in APS 220 'Credit Risk Management', default occurs when a loan obligation is contractually 90 days or more past due, or when it is considered unlikely that the credit obligation will be paid in full without remedial action, such as realisation of security.",
                76,
                endpoints("band", "band-5"),
            ),
        ]
    )
    labels = next(
        line for line in text.splitlines() if line.startswith("0<0.1%")
    ).split()
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("pd-bands", "header", "PD risk grade", 1, page, title, ("panel",)),
    ]
    bands = []
    for j, band_label in enumerate(labels):
        key = f"band-{j}"
        bounds = band_label.rstrip("%").split("<") if j < 5 else (None, None)
        quals = ("pd-horizon", "pd-through-cycle") + (
            ("default-definition",) if j == 5 else ()
        )
        axes.append(
            axis(
                key, "column", band_label, j, page, title, ("panel", "pd-bands"), quals
            )
        )
        bands.append(
            BandDefinition(
                key,
                band_label,
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
                ref(page, title, column=band_label),
            )
        )
    lines = [line for line in text.splitlines() if line.startswith(PORTFOLIO)]
    fields, cells = [], []
    for i, ((key, name, unit, quals), line) in enumerate(
        zip(specs, lines, strict=True)
    ):
        heading = next(line for line in text.splitlines() if line.startswith(name))
        if page == 50 and key in ("exposure", "undrawn"):
            quals += ("pd-model-change",)
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
        f = field(key, heading, unit, page, title, quals, attrs, transposed=True)
        fields.append(f)
        row_label = line.rsplit(" ", 6)[0]
        axes.extend(
            [
                axis(key, "block", heading, i, page, title, ("panel",), quals),
                axis(
                    key + "-approach",
                    "block",
                    "Subject to advanced IRB approach",
                    i,
                    page,
                    title,
                    ("panel", key),
                    ("approach",),
                ),
                axis(
                    key + "-mortgage",
                    "row",
                    row_label,
                    i,
                    page,
                    title,
                    ("panel", key, key + "-approach"),
                    quals,
                ),
            ]
        )
        for j, token in enumerate(line.split()[-6:]):
            cells.append(
                cell(
                    key + f"/band-{j}",
                    f,
                    key + "-mortgage",
                    f"band-{j}",
                    token,
                    page,
                    title,
                    row_label,
                    labels[j],
                    quals,
                    (f"band-{j}",),
                )
            )
    relationships = tuple(
        SourceRelationship(
            f"undrawn-{j}",
            "subset",
            "included in total exposure shown above",
            SourceEndpoint("cell", f"exposure/band-{j}"),
            endpoints("cell", f"undrawn/band-{j}"),
            endpoints("band", f"band-{j}"),
            None,
            None,
            (ref(page, "Undrawn commitments footnote"),),
        )
        for j in range(6)
    )
    meta = SourceTableMetadata(
        context(title, "Table 5.3.B", label, page, True),
        tuple(axes),
        tuple(fields),
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
        ),
        tuple(notes),
        relationships,
        (
            TemporalDescriptor(
                "measurement",
                label,
                point=day,
                point_status="established",
                evidence=(ref(page, "Panel heading"),),
            ),
        ),
        tuple(CellTemporalBinding(c.id, "measurement", "measurement") for c in cells),
    )
    return SourceTable(id, meta, tuple(cells))


def backtesting(texts, kind, page, day, label, panel):
    id = f"table5-1-j-{kind}-{day}"
    title = (
        "Table 5.1.J ("
        + kind
        + ") Accuracy of risk estimates for "
        + (
            "probability of default and exposure at default"
            if kind == "ii"
            else "loss given default"
        )
    )
    is_pd = kind == "ii"
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
        if is_pd
        else (
            ("estimated_lgd", "Average estimated downturn LGD", "%", ("lgd-estimate",)),
            ("actual_lgd", "Average actual LGD", "%", ("lgd-history",)),
        )
    )
    notes = common_notes(texts, id)
    notes.append(
        note(
            "framework-history",
            quote(texts[38], "Changes in asset class definitions", "\nTable 5.1.J (i)"),
            38,
            endpoints("dataset", id),
        )
    )
    if is_pd:
        notes.extend(
            [
                note(
                    "pd-cohort",
                    quote(
                        texts[40],
                        "The following table provides internal",
                        "Accuracy of risk estimates for exposure",
                    ),
                    40,
                    endpoints("field", "estimated_pd", "actual_pd"),
                ),
                note(
                    "ead-comparison",
                    quote(texts[40], "The ratio of estimated", "As at"),
                    40,
                    endpoints("field", "ead_ratio"),
                ),
            ]
        )
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
                "pd-outcome",
                "12-month period",
                duration_amount=Decimal(12),
                duration_unit="month",
                duration_status="established",
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
        notes.extend(
            [
                note(
                    "lgd-estimate",
                    quote(
                        texts[41], "The following table compares internal", "Actual LGD"
                    ),
                    41,
                    endpoints("field", "estimated_lgd"),
                ),
                note(
                    "lgd-history",
                    quote(texts[41], "Actual LGD has been", "As at 30 Sep 24"),
                    41,
                    endpoints("field", "actual_lgd"),
                ),
                note(
                    "apra-floor",
                    "Estimated downturn LGD subject to APRA imposed regulatory floors.",
                    page,
                    endpoints("cell", "main/estimated_lgd"),
                ),
                note(
                    "rbnz-lgd",
                    "RBNZ prudential rules prescribe LGDs for residential mortgages.",
                    page,
                    endpoints("cell", "rbnz/estimated_lgd"),
                ),
            ]
        )
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
    materiality = "Risk estimate information has only been disclosed for the RBNZ regulated banking subsidiary’s significant asset classes on the basis of materiality."
    notes.append(note("rbnz-materiality", materiality, page, endpoints("row", "rbnz")))
    axes = [axis("panel", "header", label, 0, page, title)]
    fields = tuple(
        field(key, name, unit, page, title, quals) for key, name, unit, quals in specs
    )
    for j, f in enumerate(fields):
        axes.append(
            axis(
                f.id,
                "column",
                f.source_label,
                j,
                page,
                title,
                ("panel",),
                f.qualification_refs,
            )
        )
    lines = [line for line in panel.splitlines() if line.startswith(PORTFOLIO)]
    cells, bindings = [], []
    for j, (population, line) in enumerate(zip(("main", "rbnz"), lines, strict=True)):
        block = next(
            line
            for line in panel.splitlines()
            if line.startswith(
                "Exposure type" if population == "main" else "RBNZ regulated"
            )
        )
        row_label = line.rsplit(" ", len(fields))[0]
        quals = (
            ("rbnz-materiality",) if population == "rbnz" else ("framework-history",)
        )
        axes.extend(
            [
                axis(
                    population + "-block",
                    "block",
                    block,
                    j,
                    page,
                    title,
                    ("panel",),
                    quals,
                ),
                axis(
                    population,
                    "row",
                    row_label,
                    j,
                    page,
                    title,
                    ("panel", population + "-block"),
                    quals,
                ),
            ]
        )
        for f, token in zip(fields, line.split()[-len(fields) :], strict=True):
            cq = quals + f.qualification_refs
            if f.id == "estimated_lgd":
                cq += ("apra-floor" if population == "main" else "rbnz-lgd",)
            c = cell(
                population + "/" + f.id,
                f,
                population,
                f.id,
                token,
                page,
                title,
                row_label,
                f.source_label,
                cq,
            )
            cells.append(c)
            if f.id in ("estimated_pd", "actual_pd"):
                bindings.extend(
                    CellTemporalBinding(c.id, role, descriptor)
                    for role, descriptor in (
                        ("history_window", "pd-history"),
                        ("cohort_anchor", "pd-anchor"),
                        ("outcome_window", "pd-outcome"),
                    )
                )
            elif f.id == "ead_ratio":
                bindings.extend(
                    (
                        CellTemporalBinding(c.id, "cohort_anchor", "ead-anchor"),
                        CellTemporalBinding(c.id, "measurement", "ead-default"),
                    )
                )
            else:
                role, descriptor = (
                    ("measurement", "lgd-estimate")
                    if f.id == "estimated_lgd"
                    else ("history_window", "lgd-history")
                )
                bindings.append(CellTemporalBinding(c.id, role, descriptor))
    return SourceTable(
        id,
        SourceTableMetadata(
            context(title, f"Table 5.1.J ({kind})", label, page),
            tuple(axes),
            fields,
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
            n: pdf.pages[n - 1].extract_text()
            for n in (4, 38, 40, 41, 42, 45, 46, 47, 50, 51)
        }
    dates = (
        ("2024-09-30", "As at 30 Sep 24"),
        ("2024-03-31", "As at 31 Mar 24"),
        ("2023-09-30", "As at 30 Sep 23"),
    )
    tables = [
        exposure(texts, page, day, label)
        for page, (day, label) in zip((50, 51), dates[:2], strict=True)
    ]
    for kind, pages in (("ii", (40, 40, 41)), ("iii", (41, 42, 42))):
        for page, (day, label) in zip(pages, dates, strict=True):
            panel = texts[page].split(label, 1)[1]
            panel = re.split(r"As at |Table 5\.1\.J", panel, maxsplit=1)[0]
            tables.append(backtesting(texts, kind, page, day, label, panel))
    document = SourceDocument(
        DOCUMENT,
        "raw/nab-2024-09-30-aps330.pdf",
        "nab",
        "National Australia Bank Limited",
        "Full Year Pillar 3 Report 2024",
        date(2024, 9, 30),
        None,
        "au",
        "https://www.nab.com.au/content/dam/nab/documents/reports/corporate/2024-full-year-pillar-3-report.pdf",
    )
    return ExtractionBundle(
        document,
        "au/nab/2024-09-30/aps330",
        "extractions/au/nab/2024-09-30/aps330/extract.py",
        "disclosure-v3",
        tuple(tables),
    )
