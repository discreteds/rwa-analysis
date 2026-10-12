"""Westpac September 2024: complete selected mortgage tables 9(d) and 9(f)."""

import re
from dataclasses import replace
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

DOCUMENT = "westpac-2024-09-30-aps330"
PORTFOLIO = "Residential Mortgages"
PANELS = (
    ("2024-09-30", "30 September 2024"),
    ("2024-03-31", "31 March 2024"),
    ("2023-09-30", "30 September 2023"),
)


def ref(page, location, row=None, column=None):
    return SourceReference(DOCUMENT, page, str(page), location, row, column)


def passage(text, start, end=None):
    selected = start + text.split(start, 1)[1]
    if end:
        selected = selected.split(end, 1)[0]
    return (
        " ".join(selected.split())
        .replace("fi nancial", "financial")
        .replace("non- defaulted", "non-defaulted")
    )


def qualification(key, text, page, targets, kind="field"):
    return Qualification(
        key, text, (ref(page, key),), tuple(SourceEndpoint(kind, t) for t in targets)
    )


def common_notes(texts, id):
    return (
        qualification(
            "report-entity",
            passage(texts[2], "In this report references", "In this report, unless"),
            2,
            (id,),
            "dataset",
        ),
        qualification(
            "currency",
            passage(
                texts[2],
                "In this report, unless otherwise stated or the context otherwise requires",
                "References to ‘US$’",
            ),
            2,
            (id,),
            "dataset",
        ),
        qualification(
            "level-2",
            passage(texts[14], "Unless otherwise specified", "The Westpac Group"),
            14,
            (id,),
            "dataset",
        ),
        qualification(
            "regulatory-basis",
            passage(texts[7], "Westpac uses the Advanced", "In accordance"),
            7,
            (id,),
            "dataset",
        ),
        qualification(
            "rounding",
            passage(texts[2], "Any discrepancies", "In this report"),
            2,
            (id,),
            "dataset",
        ),
    )


def context(id, label, title, template, page):
    return TableContext(
        "context",
        date(2024, 9, 30),
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
        ("report-entity", "level-2", "regulatory-basis", "currency", "rounding"),
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


def cell(key, f, row, token, page, title, label, segments=()):
    value = parse_decimal_token(token)
    reported = ReportedValue(
        value,
        token,
        max(0, -value.as_tuple().exponent) if value is not None else None,
        "dash_unresolved" if token == "-" else None,
        ref(page, title, label, f.source_label),
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
        reported,
    )


def exposure(texts, day, label):
    id, page = "table9d-" + day, 45
    title = "Residential Mortgages portfolio by PD band¹"
    specs = (
        ("outstandings", "Outstandingsᵃ", "$m", ("outstandings",)),
        ("undrawn", "Committed Undrawnᵇ", "$m", ("undrawn",)),
        ("ead", "Exposure at Default", "$m", ("ead-definition",)),
        ("pd", "Probability of Default", "%", ("pd-bands", "pd-definition")),
        ("lgd", "Loss Given Default", "%", ("lgd-definition",)),
        (
            "expected_loss",
            "Regulatory Expected Loss",
            "$m",
            ("expected-loss-definition",),
        ),
        ("rwa", "Risk Weighted Assets", "$m", ("rwa-definition",)),
        ("risk_weight", "Average Risk Weight", "%", ()),
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
    notes = list(common_notes(texts, id))
    for key, start, end, targets in (
        ("outstandings", "Outstandings are", "b. ", ("outstandings",)),
        ("undrawn", "Committed undrawn balances", "1. ", ("undrawn",)),
    ):
        notes.append(qualification(key, passage(texts[45], start, end), 45, targets))
    notes.extend(
        (
            qualification(
                "expected-loss-definition",
                passage(texts[42], "For both non-defaulted", "Corporate portfolio"),
                42,
                ("expected_loss",),
            ),
            qualification(
                "pd-bands",
                passage(texts[42], "Westpac’s program-", "For both").replace(
                    "program- managed", "program-managed"
                ),
                42,
                ("pd",),
            ),
        )
    )
    # Glossary labels interrupt the RWA description on its second line.
    glossary = texts[113].replace("assets (RWA) ", "")
    for key, source, start, end, targets in (
        ("ead-definition", 114, "EAD is calculated", "Geography", ("ead",)),
        (
            "pd-definition",
            114,
            "Probability of default is",
            "Substitution approach",
            ("pd",),
        ),
        (
            "lgd-definition",
            114,
            "The LGD represents",
            "Non-Performing exposures",
            ("lgd",),
        ),
        ("rwa-definition", 113, "Assets (both", "Tier 2 capital", ("rwa",)),
    ):
        notes.append(
            qualification(
                key,
                passage(glossary if source == 113 else texts[source], start, end),
                source,
                targets,
            )
        )
    notes.extend(
        (
            qualification(
                "default-definition",
                passage(texts[114], "Default From", "Defaulted but").removeprefix(
                    "Default "
                ),
                114,
                ("band-7",),
                "band",
            ),
            qualification(
                "npe-definition",
                passage(
                    texts[114], "Credit default exposures", "Non-Performing Exposures"
                ),
                114,
                ("band-7",),
                "band",
            ),
        )
    )
    notes = [
        replace(
            q,
            scope=q.scope
            + tuple(SourceEndpoint("band", f"band-{i}") for i in range(6)),
        )
        if q.id in ("pd-bands", "pd-definition")
        else q
        for q in notes
    ]
    section = texts[45].split(label, 1)[1]
    lines = section.strip().splitlines()[:9]
    bands, cells = [], []
    for i, line in enumerate(lines):
        tokens = line.split()
        row_label = " ".join(tokens[:-8])
        bid = f"band-{i}"
        bounds = row_label.split(" to ") if i < 6 else (None, None)
        qs = (
            ("pd-bands", "pd-definition")
            if i < 6
            else ("default-definition", "npe-definition")
            if i == 7
            else ()
        )
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
    if day == "2024-09-30":
        quoted = passage(texts[45], "As at 30 September 2024")
        keys = ("irb_rwa", "standardised_rwa")
        notes.append(qualification("supplementary-rwa", quoted, page, keys))
        for key, name, token in zip(
            keys,
            (
                "Residential Mortgages risk weighted assets under the IRB approach",
                "standardised approach equivalent",
            ),
            re.findall(r"\$([\d,]+) million", quoted),
            strict=True,
        ):
            f = field(
                key,
                name,
                "$m",
                page,
                "Footnote 1",
                (),
                ("supplementary-rwa",),
                form="note",
            )
            fields.append(f)
            cells.append(cell(key, f, None, token, page, "Footnote 1", None))
    relationships = tuple(
        SourceRelationship(
            key,
            "total",
            name,
            SourceEndpoint("row", parent),
            tuple(SourceEndpoint("row", child) for child in children),
            (SourceEndpoint("dataset", id),),
            None,
            None,
            (ref(page, title, name),),
        )
        for key, name, parent, children in (
            ("subtotal", "Subtotal", "band-6", tuple(f"band-{i}" for i in range(6))),
            ("total", "Total", "band-8", ("band-6", "band-7")),
        )
    )
    descriptor = TemporalDescriptor(
        "measurement",
        label,
        point=day,
        point_status="established",
        evidence=(ref(page, "Panel heading"),),
    )
    return SourceTable(
        id,
        SourceTableMetadata(
            context(id, label, title, "Table 9(d)", page),
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
            (descriptor,),
            tuple(
                CellTemporalBinding(c.id, "measurement", "measurement") for c in cells
            ),
        ),
        tuple(cells),
    )


def backtesting(texts, day, label):
    id = "table9f-" + day
    page = 58 if day == "2023-09-30" else 57
    title = "Regulatory loss estimates and actual losses"
    history_fields = (
        "predicted_pd",
        "observed_pd",
        "predicted_lgd",
        "observed_lgd",
        "ead_variance",
    )
    shared = ("backtesting-framework", "nz-history")
    specs = (
        (
            "expected_loss",
            "Regulatory Expected Lossᵃ",
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
            "Observed EAD variance to Predictedᵇ",
            "%",
            None,
            shared + ("ead-variance-method", "negative-variance"),
        ),
    )
    notes = list(common_notes(texts, id))
    for key, source, start, end, targets in (
        (
            "backtesting-framework",
            56,
            "The table below compares",
            "Default rates",
            history_fields,
        ),
        (
            "default-rates",
            56,
            "At the start of each year",
            "Loss Given Default (LGD)",
            history_fields[:2],
        ),
        ("lgd-workout", 56, "LGD estimates are", None, history_fields[2:4]),
        (
            "ead-variance-method",
            57,
            "The EAD variance",
            "Regulatory Observed EAD",
            ("ead_variance",),
        ),
        (
            "expected-loss-population",
            page,
            "Includes regulatory expected losses",
            "b. ",
            ("expected_loss",),
        ),
        ("negative-variance", page, "A negative outcome", "c. ", ("ead_variance",)),
        ("nz-history", page, "Historical Default Rate", None, history_fields),
    ):
        notes.append(
            qualification(key, passage(texts[source], start, end), source, targets)
        )
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
            if key in history_fields
            else ()
        )
        f = field(key, name, unit, page, title, parents + (key,), qs, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, parents, qs))
        cells.append(
            cell("mortgage/" + key, f, "mortgage", token, page, title, PORTFOLIO)
        )
    descriptors = (
        TemporalDescriptor(
            "measurement",
            label,
            point=day,
            point_status="established",
            evidence=(ref(page, "Panel heading"),),
        ),
        TemporalDescriptor(
            "history",
            "since IRB accreditation; 2008 for most portfolios",
            qualification_refs=("backtesting-framework", "default-rates", "nz-history"),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "lgd-history",
            "since IRB accreditation, excluding recent defaults; two-year residential mortgage workout",
            qualification_refs=("backtesting-framework", "lgd-workout", "nz-history"),
            evidence=(ref(56, "Loss Given Default (LGD)"),),
        ),
        TemporalDescriptor(
            "ead-history",
            "all obligors that defaulted over the observation period",
            qualification_refs=(
                "backtesting-framework",
                "ead-variance-method",
                "nz-history",
            ),
            evidence=(ref(57, "Exposure at Default (EAD)"),),
        ),
        TemporalDescriptor(
            "annual-anchor",
            "At the start of each year",
            qualification_refs=("default-rates",),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "annual-outcome",
            "during the one-year period",
            duration_amount=Decimal(1),
            duration_unit="year",
            duration_status="established",
            qualification_refs=("default-rates",),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "ead-prediction",
            "up to one year prior to default",
            qualification_refs=("ead-variance-method",),
            evidence=(ref(57, "Exposure at Default (EAD)"),),
        ),
    )
    bindings = [
        CellTemporalBinding("mortgage/expected_loss", "measurement", "measurement")
    ]
    for key in history_fields:
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
        id,
        SourceTableMetadata(
            context(id, label, title, "Table 9(f)", page),
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
            n: pdf.pages[n - 1].extract_text()
            for n in (2, 7, 14, 42, 45, 56, 57, 58, 113, 114)
        }
    tables = tuple(exposure(texts, day, label) for day, label in PANELS)
    tables += tuple(backtesting(texts, day, label) for day, label in PANELS)
    document = SourceDocument(
        DOCUMENT,
        "raw/westpac-2024-09-30-aps330.pdf",
        "westpac",
        "Westpac Banking Corporation",
        "September 2024 Pillar 3 Report",
        date(2024, 9, 30),
        None,
        "au",
        "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-pillar-3-report-september-2024.pdf",
    )
    return ExtractionBundle(
        document,
        "au/westpac/2024-09-30/aps330",
        "extractions/au/westpac/2024-09-30/aps330/extract.py",
        "disclosure-v3",
        tables,
    )
