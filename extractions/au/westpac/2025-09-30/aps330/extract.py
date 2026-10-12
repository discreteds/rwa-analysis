"""Westpac September 2025 mortgage CR6; geometry and semantics are PDF-specific."""

import re
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pdfplumber

from rwa_analysis.extraction.cr6 import (
    CR6_FIELDS,
    BronzeCreditRiskExposureRow,
    Cr6Dataset,
)
from rwa_analysis.extraction.cr9 import Cr9BacktestingRow, Cr9Context, Cr9Dataset
from rwa_analysis.extraction.datasets import DatasetMetadata, ExtractionBundle
from rwa_analysis.extraction.models import (
    BandDefinition,
    DatasetContext,
    Knowledge,
    PublishedField,
    Qualification,
    ReportedValue,
    SegmentationDefinition,
    SemanticAttribute,
    SourceAxisItem,
    SourceDocument,
    SourceEndpoint,
    SourceReference,
    SourceRelationship,
    ValueBinding,
)
from rwa_analysis.extraction.temporal import TemporalBinding, TemporalDescriptor
from rwa_analysis.extraction.values import parse_count_token, parse_decimal_token

DOCUMENT_ID = "westpac-2025-09-30-aps330"
DATASET_ID = "cr6-residential-mortgages"
BUNDLE_KEY = "au/westpac/2025-09-30/aps330"
# Inspected p48 gutters in PDF points. Retain the empty maturity/provisions grid.
COLUMN_EDGES = (190, 245, 295, 345, 395, 445, 493, 542, 590, 640, 689, 738, 787)
EXPECTED_HEADERS = (
    "Original on-\nbalance sheet\ngross\nexposure",
    "Off-balance\nsheet\nexposure pre\nCCF",
    "Average CCF\n(%)",
    "EAD post\nCRM and\npost-CCF",
    "Average PD\n(%)",
    "Number of\nborrowers",
    "Average LGD\n(%)",
    "Average\nmaturity\n(years)",
    "RWA",
    "RWA density\n(%)a",
    "EL",
    "Provisions",
)
FIELD_QUALIFICATIONS = {
    "on_balance_exposure": ("on-balance-definition",),
    "off_balance_exposure": ("off-balance-definition",),
    "average_ccf": ("ccf-definition",),
    "ead": ("ead-definition",),
    "average_pd": ("pd-definition", "pd-long-run"),
    "average_lgd": ("lgd-downturn",),
    "rwa_density": ("density-rounding",),
    "regulatory_expected_loss": ("el-definition",),
    "provisions": ("provision-definition",),
}
CONTEXT_QUALIFICATIONS = (
    "report-entity",
    "currency",
    "rounding",
    "regulatory-basis",
    "level-2-definition",
    "level-2",
    "portfolio-definition",
    "cr6-introduction",
)


def reference(page=48, location="CR6", row=None, column=None):
    return SourceReference(
        DOCUMENT_ID, page, "" if page == 1 else str(page), location, row, column
    )


def require(actual, expected):
    if actual != expected:
        raise ValueError(
            f"Unexpected Westpac source label: {actual!r}; expected {expected!r}"
        )
    return actual


def window(words, left, right, top, bottom, *, multiline=False):
    selected = [
        w for w in words if left <= w["x0"] < right and top <= w["top"] < bottom
    ]
    lines = []
    for word in sorted(selected, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(word["top"] - lines[-1][0]["top"]) > 1:
            lines.append([])
        lines[-1].append(word)
    return ("\n" if multiline else " ").join(
        " ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"]))
        for line in lines
    )


def source_passage(pdf, page, start, end, left=0):
    source = pdf.pages[page - 1]
    # Definition tables have a separate label column; avoid interleaving it.
    text = source.crop((left, 0, source.width, source.height)).extract_text()
    text = " ".join(text.replace("-\n", "-").split())
    begin = text.index(start)
    finish = text.index(end, begin) + len(end)
    return text[begin:finish]


def qualifications(pdf):
    dataset = (SourceEndpoint("dataset", DATASET_ID),)

    def field(name):
        return (SourceEndpoint("field", name),)

    # Delimiters select actual source prose; they do not substitute definitions.
    passages = (
        (
            "report-entity",
            2,
            "Report conventions",
            "In this report references",
            "just Westpac Banking Corporation.",
            dataset,
            0,
        ),
        (
            "currency",
            2,
            "Report conventions",
            "In this report, unless otherwise stated or the context",
            "are to Australian dollars.",
            dataset,
            0,
        ),
        (
            "rounding",
            2,
            "Report conventions",
            "Any discrepancies between totals",
            "are due to rounding.",
            dataset,
            0,
        ),
        (
            "regulatory-basis",
            2,
            "Report conventions",
            "In this report, unless otherwise stated, disclosures",
            "implementation of Basel III.",
            dataset,
            0,
        ),
        (
            "level-2-definition",
            8,
            "Group Structure",
            "Level 2, the consolidation",
            "Westpac Banking Corporation; and",
            dataset,
            0,
        ),
        (
            "level-2",
            8,
            "Group Structure",
            "Unless otherwise specified, all quantitative",
            "on a Level 2 basis2.",
            dataset,
            0,
        ),
        (
            "portfolio-definition",
            33,
            "CRA: Residential Mortgages",
            "Residential Mortgages asset class covers",
            "internally-modelled Retail IRB approach).",
            dataset,
            164,
        ),
        (
            "cr6-introduction",
            48,
            "CR6 A-IRB introduction",
            "The following table provides the key parameters",
            "APRA supervisory estimates for EAD).",
            dataset,
            0,
        ),
        (
            "density-rounding",
            49,
            "CR6 footnote a",
            "RWA density is calculated",
            "based on unrounded numbers.",
            field("rwa_density"),
            0,
        ),
        (
            "pd-definition",
            98,
            "Glossary: Probability of default (PD)",
            "Probability of default is a through-the-cycle",
            "obligations within one year.",
            field("average_pd"),
            133,
        ),
        (
            "pd-long-run",
            47,
            "CRE: Program-managed approach",
            "PD models are calibrated",
            "long-run average default risk.",
            field("average_pd"),
            0,
        ),
        (
            "lgd-downturn",
            47,
            "CRE: Program-managed approach",
            "LGD estimates are",
            "during a downturn period.",
            field("average_lgd"),
            0,
        ),
        (
            "ccf-definition",
            98,
            "Glossary: Credit conversion factor (CCF)",
            "Represents the proportion of undrawn limit",
            "when a facility enters default.",
            field("average_ccf"),
            133,
        ),
        (
            "ead-definition",
            98,
            "Glossary: Exposure at default (EAD)",
            "EAD is calculated at facility level",
            "in the event of a future default.",
            field("ead"),
            133,
        ),
        (
            "on-balance-definition",
            98,
            "Glossary: On-balance sheet exposure",
            "Credit exposures arising from facilities that are recorded",
            "accounting methodology).",
            field("on_balance_exposure"),
            133,
        ),
        (
            "off-balance-definition",
            98,
            "Glossary: Off-balance sheet exposure",
            "Credit exposures arising from facilities that are not recorded",
            "included in off-balance sheet exposure.",
            field("off_balance_exposure"),
            133,
        ),
        (
            "default-definition",
            34,
            "CRB: Non-performing exposures",
            "Default occurs",
            "on a credit obligation to Westpac.",
            (SourceEndpoint("row", "band-8"),),
            0,
        ),
        (
            "el-definition",
            97,
            "Appendix III footnote b",
            "Regulatory expected loss is calculated",
            "for defaulted and non-defaulted exposures.",
            field("regulatory_expected_loss"),
            0,
        ),
        (
            "provision-definition",
            44,
            "CRE: Provisioning",
            "Credit provisions are held by Westpac",
            "present value of future cashflows.",
            field("provisions"),
            0,
        ),
    )
    return tuple(
        Qualification(
            id,
            source_passage(pdf, page, start, end, left),
            (reference(page, location),),
            scope,
        )
        for id, page, location, start, end, scope, left in passages
    )


def axis(
    id, kind, label, order, parents=(), quals=(), location="CR6", row=None, column=None
):
    return SourceAxisItem(
        id,
        kind,
        label,
        order,
        parents,
        ("context",),
        quals,
        reference(48, location, row, column),
    )


def extract(pdf_path: Path) -> ExtractionBundle:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[47]
        words = page.extract_words()
        title = require(
            next(
                line
                for line in page.extract_text().splitlines()
                if line.startswith("CR6:")
            ),
            "CR6: IRB - Credit risk exposures by portfolio and PD ranges",
        )
        date_label = require(
            window(words, 30, 150, 201, 208), "As at 30 September 2025"
        )
        approach = require(window(words, 30, 90, 194, 201), "A-IRB")
        monetary_unit = require(window(words, 30, 90, 215, 223), "$m")
        pd_heading = require(window(words, 114, 185, 215, 223), "PD scale")
        portfolio = require(
            window(words, 30, 110, 428, 445, multiline=True), "Residential\nMortgages"
        )
        require(
            window(words, 30, 190, 388, 397),
            "Total RBNZ Regulated Entities - Non retail",
        )
        headers = tuple(
            require(window(words, left, right, 194, 223, multiline=True), expected)
            for left, right, expected in zip(
                COLUMN_EDGES, COLUMN_EDGES[1:], EXPECTED_HEADERS
            )
        )
        notes = qualifications(pdf)
        cover = pdf.pages[0].extract_text().splitlines()
        entity = require(cover[-2], "WESTPAC BANKING CORPORATION")
        document_title = " ".join(cover[:-2])
        report_date = datetime.strptime(date_label, "As at %d %B %Y").date()
        require(cover[3], report_date.strftime("%B %Y").upper())
        context = DatasetContext(
            "context",
            report_date,
            report_date,
            date_label,
            "CR6",
            title,
            portfolio,
            Knowledge(
                "Westpac Banking Corporation and its subsidiaries",
                "established",
                ("report-entity",),
            ),
            Knowledge("Level 2", "established", ("level-2-definition", "level-2")),
            Knowledge(
                approach, "established", ("regulatory-basis", "cr6-introduction")
            ),
            Knowledge(),
            Knowledge("AUD", "established", ("currency",)),
            CONTEXT_QUALIFICATIONS,
            (
                reference(1, "Cover"),
                reference(48, "CR6 date, approach and portfolio headings"),
            ),
        )
        axes = [
            axis("date", "header", date_label, 0),
            axis("approach", "header", approach, 1),
            axis("monetary-unit", "header", monetary_unit, 2),
            axis("pd-heading", "header", pd_heading, 3),
            axis("mortgage-block", "block", portfolio, 4, ("approach",)),
        ]
        for i, (name, header) in enumerate(zip(CR6_FIELDS, headers)):
            axes.append(
                axis(
                    "column-" + name,
                    "column",
                    header,
                    i,
                    ("date",),
                    FIELD_QUALIFICATIONS.get(name, ()),
                    "CR6 header",
                    column=header,
                )
            )
        # All eight PD rows start at x114.43, including three ABOVE the heading.
        row_tops = sorted(
            w["top"] for w in words if 114 <= w["x0"] < 115 and 398 < w["top"] < 474
        )
        total_tops = [
            w["top"]
            for w in words
            if 30 <= w["x0"] < 32 and 474 < w["top"] < 484 and w["text"] == "Total"
        ]
        if len(row_tops) != 8 or len(total_tops) != 1:
            raise ValueError("Unexpected Westpac mortgage row structure")
        labels = tuple(window(words, 114, 185, top - 1, top + 7) for top in row_tops)
        total = require(
            window(words, 30, 190, total_tops[0] - 1, total_tops[0] + 7),
            "Total Residential Mortgages",
        )
        labels += (total,)
        row_tops += total_tops
        row_ids = tuple(f"band-{i + 1}" for i in range(8)) + ("portfolio-aggregate",)
        records, bands = [], []
        for i, (id, label, top) in enumerate(zip(row_ids, labels, row_tops)):
            aggregate = label == total
            default = label == "100.00 (Default)"
            axes.append(
                axis(
                    id,
                    "row",
                    label,
                    i,
                    ("mortgage-block", "pd-heading"),
                    ("default-definition",) if default else (),
                    "CR6 Residential Mortgages",
                    row=label,
                )
            )
            if not aggregate:
                interval = re.fullmatch(r"(\d+\.\d+) to <(\d+\.\d+)", label)
                if interval:
                    lower, upper = map(Decimal, interval.groups())
                    status = "established"
                else:
                    require(label, "100.00 (Default)")
                    lower, upper, status = None, None, "not_applicable"
                bands.append(
                    BandDefinition(
                        f"pd-band-{i + 1}",
                        label,
                        i,
                        "interval" if interval else "default",
                        "%",
                        lower,
                        upper,
                        True if interval else None,
                        False if interval else None,
                        status,
                        status,
                        None if interval else label,
                        reference(48, "CR6 Residential Mortgages", row=label),
                    )
                )
            values = {}
            for name, header, left, right in zip(
                CR6_FIELDS, headers, COLUMN_EDGES, COLUMN_EDGES[1:]
            ):
                token = window(words, left, right, top - 1, top + 7)
                number = parse_decimal_token(token)
                parsed = (
                    parse_count_token(token)
                    if name == "reported_borrower_count"
                    else number
                )
                precision = (
                    None if number is None else max(0, -number.as_tuple().exponent)
                )
                missing = None
                if parsed is None:
                    if token in {"-", "–"}:
                        missing = "dash_unresolved"
                    elif name == "provisions" and not aggregate:
                        missing = "not_disclosed_at_this_grain"
                    else:
                        missing = "blank_unresolved"
                values[name] = ReportedValue(
                    parsed,
                    token,
                    precision,
                    missing,
                    reference(48, "CR6 Residential Mortgages", label, header),
                )
            records.append(
                BronzeCreditRiskExposureRow(
                    id,
                    id,
                    total if aggregate else "band",
                    () if aggregate else (f"pd-band-{i + 1}",),
                    ("mortgage-block",),
                    **values,
                )
            )
        published, bindings = [], []
        for name, header in zip(CR6_FIELDS, headers):
            # Units come from the reviewed header paths, not the adjacent count.
            unit = (
                "%"
                if "(%)" in header
                else "years"
                if "(years)" in header
                else ""
                if name == "reported_borrower_count"
                else monetary_unit
            )
            refs = FIELD_QUALIFICATIONS.get(name, ())
            attrs = ()
            if name.startswith("average_"):
                attrs = (SemanticAttribute("weighting", None, "unresolved", ()),)
            if name == "reported_borrower_count":
                attrs = (SemanticAttribute("counted_entity", None, "unresolved", ()),)
            parents = ("date", "column-" + name) + (
                ("monetary-unit",) if unit == monetary_unit else ()
            )
            published.append(
                PublishedField(
                    name,
                    header,
                    parents,
                    unit,
                    Decimal(1000000) if unit == monetary_unit else Decimal(1),
                    refs,
                    attrs,
                    reference(48, "CR6 header", column=header),
                )
            )
            bindings.append(
                ValueBinding(
                    "binding-" + name,
                    name,
                    name,
                    row_ids,
                    ("column-" + name,),
                    ("context",),
                    refs,
                )
            )
        evidence = (reference(48, "CR6 Residential Mortgages PD scale and Total"),)
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            pd_heading,
            tuple(bands),
            ("context",),
            Knowledge(
                "Displayed PD ranges and default category cover the total",
                "established",
                ("cr6-introduction",),
            ),
            Knowledge(
                "Non-overlapping printed intervals and separate default category",
                "established",
                ("cr6-introduction",),
            ),
            evidence,
        )
        relationship = SourceRelationship(
            "mortgage-total",
            "total",
            total,
            SourceEndpoint("row", row_ids[-1]),
            tuple(SourceEndpoint("row", id) for id in row_ids[:-1]),
            (SourceEndpoint("block", "mortgage-block"),),
            True,
            True,
            evidence,
        )
        dataset = Cr6Dataset(
            DATASET_ID,
            DatasetMetadata(
                context,
                tuple(axes),
                tuple(published),
                tuple(bindings),
                (segmentation,),
                notes,
                (relationship,),
            ),
            tuple(records),
        )
        document = SourceDocument(
            DOCUMENT_ID,
            f"raw/{DOCUMENT_ID}.pdf",
            "westpac",
            entity,
            document_title,
            report_date,
            # Acquisition metadata recorded in raw/index.md, not a cover claim.
            date(2025, 11, 3),
            "au",
            "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-September-2025-Pillar-3-Report-2025.pdf",
        )
        return ExtractionBundle(
            document,
            BUNDLE_KEY,
            f"extractions/{BUNDLE_KEY}/extract.py",
            "disclosure-v2",
            (dataset, extract_cr9(pdf, dataset)),
        )


def extract_cr9(pdf, cr6):
    """Reviewed p55 mortgage block and p56 notes; keep its own field timing."""
    page = pdf.pages[54]
    words = page.extract_words(y_tolerance=1)
    title = next(
        line for line in page.extract_text().splitlines() if line.startswith("CR9:")
    )
    portfolio = window(words, 65, 125, 300, 318, multiline=True)
    # Header/cell gutters reviewed against the rendered table. Rating columns
    # are lexical axes, including the blank default-row rating equivalents.
    edges = (400, 455, 515, 577, 636, 699, 754, 815)
    field_names = (
        "weighted_average_pd",
        "arithmetic_average_pd",
        "previous_year_borrower_count",
        "current_year_borrower_count",
        "defaulted_borrower_count",
        "new_defaulted_borrower_count",
        "historical_annual_default_rate",
    )
    header_tops = (175, 166, 173, 173, 166, 163, 166)
    headers = tuple(
        window(words, l, r, t, 193, multiline=True)
        for l, r, t in zip(edges, edges[1:], header_tops)
    )
    field_notes = {
        "weighted_average_pd": ("pd-definition", "pd-long-run", "cr9-weighting"),
        "arithmetic_average_pd": ("pd-definition", "pd-long-run"),
        "defaulted_borrower_count": ("default-definition", "cr9-defaults"),
        "new_defaulted_borrower_count": ("default-definition", "cr9-defaults"),
        "historical_annual_default_rate": ("cr9-history",),
    }
    dataset_id = "cr9-residential-mortgages"
    shared = (
        "report-entity",
        "currency",
        "rounding",
        "regulatory-basis",
        "level-2-definition",
        "level-2",
        "portfolio-definition",
        "pd-definition",
        "pd-long-run",
        "default-definition",
    )
    notes = []
    for note in cr6.metadata.qualifications:
        if note.id not in shared:
            continue
        if note.id in ("pd-definition", "pd-long-run"):
            scope = tuple(
                SourceEndpoint("field", f)
                for f in ("weighted_average_pd", "arithmetic_average_pd")
            )
        elif note.id == "default-definition":
            scope = (
                SourceEndpoint("row", "band-8"),
                SourceEndpoint("field", "defaulted_borrower_count"),
                SourceEndpoint("field", "new_defaulted_borrower_count"),
            )
        else:
            scope = (SourceEndpoint("dataset", dataset_id),)
        notes.append(replace(note, scope=scope))
    passages = (
        (
            "cr9-introduction",
            55,
            "The following table provides a comparison",
            "for all portfolio types.",
        ),
        ("cr9-weighting", 56, "Observation point is June 2024", "is as at June 2024."),
        (
            "cr9-defaults",
            56,
            "Defaulted borrowers in the year include:",
            "(new defaulted borrowers).",
        ),
        (
            "cr9-history",
            56,
            "Average historical default rate is calculated",
            "over 10 years.",
        ),
    )
    for name, p, start, end in passages:
        scope = (
            (SourceEndpoint("dataset", dataset_id),)
            if name == "cr9-introduction"
            else tuple(
                SourceEndpoint("field", f)
                for f, refs in field_notes.items()
                if name in refs
            )
        )
        notes.append(
            Qualification(
                name, source_passage(pdf, p, start, end), (reference(p, name),), scope
            )
        )
    old = cr6.metadata.context
    context = Cr9Context(
        "context",
        old.document_date,
        "CR9",
        title,
        portfolio,
        old.reporting_entity,
        old.consolidation_scope,
        Knowledge("A-IRB", "established", ("regulatory-basis", "cr9-introduction")),
        old.geography,
        old.currency,
        tuple(
            "cr9-introduction" if q == "cr6-introduction" else q
            for q in old.qualification_refs
        ),
        (reference(1, "Cover"), reference(55, "CR9 headings")),
    )

    def item(id, kind, label, order, parents=(), quals=(), row=None, column=None):
        return SourceAxisItem(
            id,
            kind,
            label,
            order,
            parents,
            ("context",),
            quals,
            reference(55, "CR9", row, column),
        )

    axes = [
        item("approach", "header", window(words, 55, 100, 154, 163), 0),
        item("pd-heading", "header", window(words, 130, 200, 184, 193), 1),
        item("mortgage-block", "block", portfolio, 2, ("approach",)),
        item("external-ratings", "header", window(words, 280, 400, 163, 171), 3),
        item("borrower-counts", "header", window(words, 530, 635, 163, 171), 4),
    ]
    published, bindings = [], []
    row_ids = tuple(f"band-{i}" for i in range(1, 9))
    for i, (name, header) in enumerate(zip(field_names, headers)):
        refs = field_notes.get(name, ())
        parents = (
            ("borrower-counts",)
            if name in ("previous_year_borrower_count", "current_year_borrower_count")
            else ()
        )
        axes.append(
            item("column-" + name, "column", header, i, parents, refs, column=header)
        )
        attrs = ()
        if name == "weighted_average_pd":
            attrs = (
                SemanticAttribute(
                    "weighting", "EAD", "established", ("cr9-weighting",)
                ),
            )
        elif name == "arithmetic_average_pd":
            attrs = (SemanticAttribute("weighting", "borrowers", "established", ()),)
        elif name.endswith("count"):
            attrs = (SemanticAttribute("counted_entity", None, "unresolved", ()),)
        published.append(
            PublishedField(
                name,
                header,
                parents + ("column-" + name,),
                "" if name.endswith("count") else "%",
                Decimal(1),
                refs,
                attrs,
                reference(55, "CR9", column=header),
            )
        )
        bindings.append(
            ValueBinding(
                "binding-" + name,
                name,
                name,
                row_ids,
                ("column-" + name,),
                ("context",),
                refs,
            )
        )
    agencies = (window(words, 290, 330, 184, 193), window(words, 365, 400, 184, 193))
    for i, agency in enumerate(agencies):
        axes.append(
            item(
                f"rating-{i}", "column", agency, i, ("external-ratings",), column=agency
            )
        )
    tops = sorted(
        w["top"] for w in words if 135 <= w["x0"] < 136 and 270 < w["top"] < 347
    )
    rows, bands, relationships = [], [], []
    for i, top in enumerate(tops):
        rid = row_ids[i]
        label = window(words, 130, 260, top - 1, top + 7)
        default = label == "100.00 (Default)"
        axes.append(
            item(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                ("default-definition",) if default else (),
                row=label,
            )
        )
        for j, (left, right) in enumerate(((260, 330), (330, 400))):
            axes.append(
                item(
                    f"{rid}-rating-{j}",
                    "header",
                    window(words, left, right, top - 1, top + 7),
                    j,
                    (rid, f"rating-{j}"),
                    row=label,
                    column=agencies[j],
                )
            )
        interval = re.fullmatch(r"(\d+\.\d+) to <(\d+\.\d+)", label)
        lower, upper = map(Decimal, interval.groups()) if interval else (None, None)
        status = "established" if interval else "not_applicable"
        bands.append(
            BandDefinition(
                f"pd-band-{i + 1}",
                label,
                i,
                "interval" if interval else "default",
                "%",
                lower,
                upper,
                True if interval else None,
                False if interval else None,
                status,
                status,
                None if interval else label,
                reference(55, "CR9", row=label),
            )
        )
        cells = {}
        for name, header, left, right in zip(field_names, headers, edges, edges[1:]):
            token = window(words, left, right, top - 1, top + 7)
            count = name.endswith("count")
            value = parse_count_token(token) if count else parse_decimal_token(token)
            precision = (
                None
                if value is None
                else 0
                if count
                else max(0, -value.as_tuple().exponent)
            )
            cells[name] = ReportedValue(
                value,
                token,
                precision,
                ("dash_unresolved" if token == "-" else "blank_unresolved")
                if value is None
                else None,
                reference(55, "CR9", label, header),
            )
        rows.append(
            Cr9BacktestingRow(
                rid, rid, "band", (f"pd-band-{i + 1}",), ("mortgage-block",), **cells
            )
        )
        if not default:
            relationships.append(
                SourceRelationship(
                    "new-defaults-" + rid,
                    "subset",
                    headers[5],
                    SourceEndpoint("field", "defaulted_borrower_count"),
                    (SourceEndpoint("field", "new_defaulted_borrower_count"),),
                    (SourceEndpoint("row", rid),),
                    False,
                    None,
                    (
                        reference(55, "CR9", label, headers[5]),
                        reference(56, "cr9-defaults"),
                    ),
                )
            )
    segmentation = SegmentationDefinition(
        "pd-segmentation",
        "PD Range",
        tuple(bands),
        ("context",),
        Knowledge(),
        Knowledge(
            "Non-overlapping printed intervals and separate default category",
            "established",
            (),
        ),
        (reference(55, "CR9 PD Range"),),
    )
    descriptors = (
        TemporalDescriptor(
            "pd-measurement",
            "June 2024",
            point="2024-06",
            point_status="established",
            qualification_refs=("cr9-weighting",),
            evidence=(reference(56, "cr9-weighting"),),
        ),
        TemporalDescriptor(
            "annual",
            "1 July 2024 to 30 June 2025",
            start="2024-07-01",
            end="2025-06-30",
            start_status="established",
            end_status="established",
            duration_amount=Decimal(12),
            duration_unit="months",
            duration_status="established",
            qualification_refs=("cr9-introduction", "cr9-defaults"),
            evidence=(reference(55, "cr9-introduction"), reference(56, "cr9-defaults")),
        ),
        TemporalDescriptor(
            "history",
            "10 years",
            duration_amount=Decimal(10),
            duration_unit="years",
            duration_status="established",
            qualification_refs=("cr9-history",),
            evidence=(reference(56, "cr9-history"),),
        ),
        TemporalDescriptor(
            "previous-year",
            "End of previous year",
            point="2024-06-30",
            point_status="established",
            qualification_refs=("cr9-introduction",),
            evidence=(
                reference(55, "cr9-introduction"),
                reference(55, "CR9", column=headers[2]),
            ),
        ),
        TemporalDescriptor(
            "current-year",
            "End of the year",
            point="2025-06-30",
            point_status="established",
            qualification_refs=("cr9-introduction",),
            evidence=(
                reference(55, "cr9-introduction"),
                reference(55, "CR9", column=headers[3]),
            ),
        ),
        TemporalDescriptor(
            "unspecified", "", evidence=(reference(55, "CR9 headings"),)
        ),
    )
    roles = (
        ("weighted_average_pd", "measurement", "pd-measurement"),
        ("weighted_average_pd", "weight_measurement", "pd-measurement"),
        ("arithmetic_average_pd", "measurement", "unspecified"),
        ("previous_year_borrower_count", "measurement", "previous-year"),
        ("current_year_borrower_count", "measurement", "current-year"),
        ("defaulted_borrower_count", "outcome_window", "annual"),
        ("new_defaulted_borrower_count", "outcome_window", "annual"),
        ("historical_annual_default_rate", "history_window", "history"),
    )
    temporal = tuple(
        TemporalBinding(rid, f, role, descriptor)
        for rid in row_ids
        for f, role, descriptor in roles
    )
    return Cr9Dataset(
        dataset_id,
        DatasetMetadata(
            context,
            tuple(axes),
            tuple(published),
            tuple(bindings),
            (segmentation,),
            tuple(notes),
            tuple(relationships),
            descriptors,
            temporal,
        ),
        tuple(rows),
    )
