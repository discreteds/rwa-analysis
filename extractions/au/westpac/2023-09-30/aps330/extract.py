"""Westpac September 2023 selected mortgage exposure and historical backtesting.

PDF text selection and source-specific meaning live here. Shared source-table
objects, numeric parsing and the normal SourceTablePipeline own representation
and downstream processing; this module does not import another dated extractor.
"""

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

DOCUMENT = "westpac-2023-09-30-aps330"
PORTFOLIO = "Residential mortgages"
PANELS = (
    ("2023-09-30", "30 September 2023"),
    ("2023-03-31", "31 March 2023"),
    ("2022-09-30", "30 September 2022"),
)
HISTORY_FIELDS = (
    "predicted_pd",
    "observed_pd",
    "predicted_lgd",
    "observed_lgd",
    "ead_variance",
)


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, "" if page == 2 else str(page - 2), location, row, column
    )


def passage(text, start, end=None):
    selected = start + text.split(start, 1)[1]
    if end:
        selected = selected.split(end, 1)[0]
    return " ".join(selected.split()).replace(
        "transaction- managed", "transaction-managed"
    )


def note(texts, key, page, start, end, targets, kind="field"):
    return Qualification(
        key,
        passage(texts[page], start, end),
        (ref(page, key),),
        tuple(SourceEndpoint(kind, target) for target in targets),
    )


def common_notes(texts, dataset):
    return [
        note(texts, key, page, start, end, (dataset,), "dataset")
        for key, page, start, end in (
            ("report-entity", 2, "In this report references", "In this report, unless"),
            (
                "currency",
                2,
                "In this report, unless otherwise stated or the context otherwise requires",
                "References to ‘US$’",
            ),
            ("rounding", 2, "Any discrepancies", "In this report"),
            ("level-2", 13, "Unless otherwise specified", "The Westpac Group"),
            ("regulatory-basis", 6, "Westpac uses the Advanced", "In accordance"),
        )
    ]


def context(label, title, template, page, qualifications=()):
    return TableContext(
        "context",
        date(2023, 9, 30),
        label,
        template,
        title,
        PORTFOLIO,
        Knowledge(
            "Westpac Banking Corporation and its controlled entities",
            "established",
            ("report-entity",),
        ),
        Knowledge("Level 2", "established", ("level-2",)),
        Knowledge("Advanced IRB", "established", ("regulatory-basis",)),
        Knowledge(),
        Knowledge("AUD", "established", ("currency",)),
        ("report-entity", "currency", "rounding", "level-2", "regulatory-basis")
        + qualifications,
        (ref(page, title),),
    )


def axis(key, kind, label, order, page, title, parents=(), quals=()):
    return SourceAxisItem(
        key,
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


def field(key, label, unit, page, title, path, quals=(), attrs=(), form="table_body"):
    return TableField(
        key,
        label,
        path,
        unit,
        Decimal("1000000" if unit == "$m" else "1"),
        quals,
        attrs,
        ref(page, title, column=label),
        "decimal",
        "money" if unit == "$m" else "scalar",
        form,
    )


def cell(key, f, row, token, page, title, row_label, segments=()):
    # N/A is a published numeric-field missing token; the common decimal parser
    # intentionally has no source-specific interpretation for it.
    value = None if token == "N/A" else parse_decimal_token(token)
    missing = (
        "not_applicable"
        if token == "N/A"
        else "dash_unresolved"
        if token == "-"
        else None
    )
    return SourceCell(
        key,
        f.id,
        row,
        f.id if row else None,
        ("context",),
        segments,
        f.qualification_refs,
        "decimal",
        ReportedValue(
            value,
            token,
            max(0, -value.as_tuple().exponent) if value is not None else None,
            missing,
            ref(page, title, row_label, f.source_label),
        ),
    )


def measurement(day, label, page):
    return TemporalDescriptor(
        "measurement",
        label,
        point=day,
        point_status="established",
        evidence=(ref(page, "Panel heading"),),
    )


def exposure(texts, day, label):
    dataset, page = "table9d-" + day, 44
    title = "Residential mortgages portfolio by PD band¹,²"
    specs = (
        ("outstandings", "Outstandings³", "$m", ("outstandings",)),
        ("undrawn", "Committed Undrawn⁴", "$m", ("undrawn",)),
        ("ead", "Exposure at Default", "$m", ("ead-definition",)),
        ("pd", "Probability of Default", "%", ("pd-bands", "pd-definition")),
        ("lgd", "Loss Given Default", "%", ("lgd-definition",)),
        (
            "expected_loss",
            "Regulatory Expected Loss",
            "$m",
            ("expected-loss-definition",),
        ),
        ("rwa", "Risk Weighted Assets", "$m", ("rwa-definition", "risk-weight-floor")),
        ("risk_weight", "Average Risk Weight", "%", ("risk-weight-floor",)),
    )
    fields = [
        field(k, name, unit, page, title, ("panel", k), qs)
        for k, name, unit, qs in specs
    ]
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("pd-bands", "header", "PD band", 1, page, title, ("panel",)),
    ]
    axes.extend(
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
        for j, f in enumerate(fields)
    )
    notes = common_notes(texts, dataset)
    for key, source, start, end, targets in (
        ("outstandings", 44, "Outstandings are", "4. ", ("outstandings",)),
        ("undrawn", 44, "Committed undrawn balances", None, ("undrawn",)),
        (
            "risk-weight-floor",
            44,
            "The above table reflects",
            "3. ",
            ("rwa", "risk_weight")
            + (("risk_weight_floor",) if day == "2022-09-30" else ()),
        ),
        (
            "expected-loss-definition",
            41,
            "For both non-defaulted",
            "From 31 March",
            ("expected_loss",),
        ),
        ("ead-definition", 110, "EAD is calculated", "Expected credit loss", ("ead",)),
        ("lgd-definition", 111, "The LGD represents", "Maturity", ("lgd",)),
        ("rwa-definition", 112, "Assets (both", "Securitisation purchased", ("rwa",)),
    ):
        notes.append(note(texts, key, source, start, end, targets))
    # PD defines both the numeric field and interval segmentation, not all fields.
    for key, source, start, end in (
        ("pd-bands", 41, "Westpac’s program-managed", "For both"),
        ("pd-definition", 112, "Probability of default is", "Resecuritisation"),
    ):
        notes.append(
            Qualification(
                key,
                passage(texts[source], start, end),
                (ref(source, key),),
                (SourceEndpoint("field", "pd"),)
                + tuple(SourceEndpoint("band", f"band-{i}") for i in range(6)),
            )
        )
    if day == "2022-09-30":
        default_quals = ("default-pre-2023",)
        notes.append(
            note(
                texts,
                "default-pre-2023",
                110,
                "Pre – 1 January 2023:",
                "From 1 January 2023:",
                ("band-7",),
                "band",
            )
        )
    else:
        default_quals = ("default-from-2023", "npe-definition")
        notes.extend(
            (
                note(
                    texts,
                    "default-from-2023",
                    110,
                    "From 1 January 2023:",
                    "Defaulted not impaired",
                    ("band-7",),
                    "band",
                ),
                note(
                    texts,
                    "npe-definition",
                    112,
                    "Credit default exposures",
                    "Non-Performing Exposures –",
                    ("band-7",),
                    "band",
                ),
            )
        )
    context_quals = ()
    if day != "2022-09-30":
        context_quals = (
            "asset-class-transition",
            "mortgage-definition",
            "nz-perimeter",
        )
        for key, source, start, end in (
            ("asset-class-transition", 41, "From 31 March 2023", "Corporate portfolio"),
            (
                "mortgage-definition",
                22,
                "Residential Mortgages asset class",
                "Australian Credit Cards",
            ),
            (
                "nz-perimeter",
                22,
                "RBNZ regulated exposures",
                "Standardised and Securitised",
            ),
        ):
            notes.append(note(texts, key, source, start, end, (dataset,), "dataset"))
    # Printed panel headers precede the body; start at the first actual PD row.
    section = texts[page].split(label, 1)[1].split("0.0 to 0.10", 1)[1]
    lines = ("0.0 to 0.10" + section).splitlines()[:9]
    bands, cells = [], []
    for i, line in enumerate(lines):
        tokens = line.split()
        row_label = " ".join(tokens[:-8])
        bid = f"band-{i}"
        bounds = row_label.split(" to ") if i < 6 else (None, None)
        qs = ("pd-bands", "pd-definition") if i < 6 else default_quals if i == 7 else ()
        axes.append(
            axis(bid, "row", row_label, i, page, title, ("panel", "pd-bands"), qs)
        )
        bands.append(
            BandDefinition(
                bid,
                row_label,
                i,
                "interval" if i < 6 else "default" if i == 7 else "category",
                "%",
                Decimal(bounds[0]) if i < 6 else None,
                Decimal(bounds[1]) if i < 6 else None,
                None,
                None,
                "established" if i < 6 else "not_applicable",
                "established" if i < 6 else "not_applicable",
                None if i < 6 else row_label,
                ref(page, title, row_label),
            )
        )
        cells.extend(
            cell(bid + "/" + f.id, f, bid, token, page, title, row_label, (bid,))
            for f, token in zip(fields, tokens[-8:], strict=True)
        )
    if day == "2023-09-30":
        keys = ("irb_rwa", "standardised_rwa")
        q = note(texts, "supplementary-rwa", 44, "As at 30 September 2023", "2. ", keys)
        notes.append(q)
        for key, name, token in zip(
            keys,
            (
                "Residential Mortgages risk weighted assets under the IRB approach",
                "standardised approach equivalent",
            ),
            re.findall(r"\$([\d,]+) million", q.source_text),
            strict=True,
        ):
            f = field(key, name, "$m", page, "Footnote 1", (), (q.id,), form="note")
            fields.append(f)
            cells.append(cell(key, f, None, token, page, "Footnote 1", None))
    if day == "2022-09-30":
        q = next(q for q in notes if q.id == "risk-weight-floor")
        token = re.search(r"floor of (\d+%)", q.source_text).group(1)
        f = field(
            "risk_weight_floor",
            "floor of 25% to its residential mortgage risk weights",
            "%",
            page,
            "Footnote 2",
            (),
            (q.id,),
            form="note",
        )
        fields.append(f)
        cells.append(cell(f.id, f, None, token, page, "Footnote 2", None))
    relationships = tuple(
        SourceRelationship(
            key,
            "total",
            name,
            SourceEndpoint("row", parent),
            tuple(SourceEndpoint("row", child) for child in children),
            (SourceEndpoint("dataset", dataset),),
            None,
            None,
            (ref(page, title, name),),
        )
        for key, name, parent, children in (
            ("subtotal", "Subtotal", "band-6", tuple(f"band-{i}" for i in range(6))),
            ("total", "Total", "band-8", ("band-6", "band-7")),
        )
    )
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context(label, title, "Table 9(d)", page, context_quals),
            tuple(axes),
            tuple(fields),
            (
                SegmentationDefinition(
                    "pd-bands",
                    "PD band",
                    tuple(bands),
                    ("context",),
                    Knowledge(),
                    Knowledge(),
                    (ref(page, title),),
                ),
            ),
            tuple(notes),
            relationships,
            (measurement(day, label, page),),
            tuple(
                CellTemporalBinding(c.id, "measurement", "measurement") for c in cells
            ),
        ),
        tuple(cells),
    )


def backtesting(texts, day, label):
    dataset = "table9f-" + day
    page = 56 if day == "2023-09-30" else 57
    title = "Regulatory loss estimates and actual losses" + (
        " (continued)" if page == 57 else ""
    )
    label = label.replace("September", "Sept")
    shared = ("backtesting-framework", "nz-history")
    specs = (
        (
            "expected_loss",
            "Regulatory Expected Loss¹",
            "$m",
            None,
            ("expected-loss-population",),
        ),
        ("predicted_pd", "Predicted", "%", "default-rate", shared + ("default-rates",)),
        ("observed_pd", "Observed", "%", "default-rate", shared + ("default-rates",)),
        ("predicted_lgd", "Predicted", "%", "lgd", shared + ("lgd-workout",)),
        ("observed_lgd", "Observed", "%", "lgd", shared + ("lgd-workout",)),
        (
            "ead_variance",
            "Observed EAD variance to Predicted²",
            "%",
            None,
            shared + ("ead-variance-method", "negative-variance"),
        ),
    )
    notes = common_notes(texts, dataset)
    for key, source, start, end, targets in (
        (
            "backtesting-framework",
            56,
            "The table below compares",
            "Default rates",
            HISTORY_FIELDS,
        ),
        (
            "default-rates",
            56,
            "At the start of each year",
            "Loss Given Default (LGD)",
            HISTORY_FIELDS[:2],
        ),
        (
            "lgd-workout",
            56,
            "The LGD analysis",
            "Exposure at Default (EAD)",
            HISTORY_FIELDS[2:4],
        ),
        (
            "ead-variance-method",
            56,
            "The EAD variance",
            "30 Sept 2023",
            ("ead_variance",),
        ),
        (
            "expected-loss-population",
            page,
            "Includes regulatory expected losses",
            "2. ",
            ("expected_loss",),
        ),
        ("negative-variance", page, "A negative outcome", "3. ", ("ead_variance",)),
        ("nz-history", page, "Historical Default Rate", None, HISTORY_FIELDS),
    ):
        notes.append(note(texts, key, source, start, end, targets))
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("mortgage", "row", PORTFOLIO, 0, page, title, ("panel",)),
        axis("default-rate", "header", "Default rate", 0, page, title, ("panel",)),
        axis("lgd", "header", "Loss Given Default", 1, page, title, ("panel",)),
    ]
    row = next(
        line
        for line in texts[page].split(label, 1)[1].splitlines()
        if line.startswith(PORTFOLIO)
    )
    fields, cells = [], []
    for j, ((key, name, unit, parent, qs), token) in enumerate(
        zip(specs, row.split()[-6:], strict=True)
    ):
        parents = ("panel", parent) if parent else ("panel",)
        attrs = (
            (SemanticAttribute("weighting", None, "unresolved", ()),)
            if key in HISTORY_FIELDS
            else ()
        )
        f = field(key, name, unit, page, title, parents + (key,), qs, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, parents, qs))
        cells.append(
            cell("mortgage/" + key, f, "mortgage", token, page, title, PORTFOLIO)
        )
    descriptors = [measurement(day, label, page)]
    for key, text, qs, location in (
        (
            "history",
            "since IRB accreditation; 2008 for most portfolios",
            ("backtesting-framework", "default-rates", "nz-history"),
            "Default rates",
        ),
        (
            "lgd-history",
            "since IRB accreditation, excluding recent defaults; two-year residential mortgage workout",
            ("backtesting-framework", "lgd-workout", "nz-history"),
            "Loss Given Default (LGD)",
        ),
        (
            "ead-history",
            "all obligors that defaulted over the observation period",
            ("backtesting-framework", "ead-variance-method", "nz-history"),
            "Exposure at Default (EAD)",
        ),
        (
            "annual-anchor",
            "At the start of each year",
            ("default-rates",),
            "Default rates",
        ),
        (
            "annual-outcome",
            "during the one-year period",
            ("default-rates",),
            "Default rates",
        ),
        (
            "ead-prediction",
            "up to one year prior to default",
            ("ead-variance-method",),
            "Exposure at Default (EAD)",
        ),
    ):
        descriptors.append(
            TemporalDescriptor(
                key,
                text,
                duration_amount=Decimal(1) if key == "annual-outcome" else None,
                duration_unit="year" if key == "annual-outcome" else None,
                duration_status="established"
                if key == "annual-outcome"
                else "unresolved",
                qualification_refs=qs,
                evidence=(ref(56, location),),
            )
        )
    bindings = [
        CellTemporalBinding("mortgage/expected_loss", "measurement", "measurement")
    ]
    for key in HISTORY_FIELDS:
        descriptor = (
            "history"
            if key.endswith("pd")
            else "lgd-history"
            if key.endswith("lgd")
            else "ead-history"
        )
        bindings.append(
            CellTemporalBinding("mortgage/" + key, "history_window", descriptor)
        )
    for key, role, descriptor in (
        ("predicted_pd", "cohort_anchor", "annual-anchor"),
        ("observed_pd", "cohort_anchor", "annual-anchor"),
        ("predicted_pd", "rating_assignment", "annual-anchor"),
        ("observed_pd", "outcome_window", "annual-outcome"),
        ("ead_variance", "measurement", "ead-prediction"),
    ):
        bindings.append(CellTemporalBinding("mortgage/" + key, role, descriptor))
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context(label, title, "Table 9(f)", page),
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
            n: pdf.pages[n - 1].extract_text()
            for n in (6, 13, 22, 41, 44, 56, 57, 110, 111, 112)
        }
        # This PDF contains an obscured annual-report layer on page 2. The visible
        # Pillar 3 body uses WFANIQ+Gotham-Light, verified against the rendered page.
        texts[2] = (
            pdf.pages[1]
            .filter(
                lambda obj: (
                    obj.get("object_type") != "char"
                    or obj.get("fontname", "").startswith("WFANIQ+")
                )
            )
            .extract_text()
        )
    tables = tuple(exposure(texts, day, label) for day, label in PANELS)
    tables += tuple(backtesting(texts, day, label) for day, label in PANELS)
    return ExtractionBundle(
        SourceDocument(
            DOCUMENT,
            "raw/westpac-2023-09-30-aps330.pdf",
            "westpac",
            "Westpac Banking Corporation",
            "September 2023 Pillar 3 Report",
            date(2023, 9, 30),
            None,
            "au",
            "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/september-2023-Pillar-3-report.pdf",
        ),
        "au/westpac/2023-09-30/aps330",
        "extractions/au/westpac/2023-09-30/aps330/extract.py",
        "disclosure-v3",
        tables,
    )
