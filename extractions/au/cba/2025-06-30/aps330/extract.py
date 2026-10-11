"""CBA June 2025, selected mortgage CR6 block. Geometry belongs to this PDF."""

import re
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import pdfplumber

from rwa_analysis.extraction.cr6 import (
    CR6_FIELDS,
    BronzeCreditRiskExposureRow,
    Cr6Dataset,
)
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
from rwa_analysis.extraction.values import parse_count_token, parse_decimal_token

DOCUMENT_ID = "cba-2025-06-30-aps330"
DATASET_ID = "cr6-residential-mortgages"
BUNDLE_KEY = "au/cba/2025-06-30/aps330"
# Inspected p55 header gutters, in PDF points (page 841.92 x 595.32).
# In particular, the maturity and provisions windows must stay in the grid.
COLUMN_EDGES = (232, 280, 325, 370, 416, 458, 506, 550, 595, 638, 682, 724, 770)
EXPECTED_HEADERS = (
    "Original\non-balance\nsheet\ngross\nexposure",
    "Off-\nbalance\nsheet\nexposures\npre CCF",
    "Average\nCCF",
    "EAD post\nCRM and\npost-CCF",
    "Average\nPD ¹",
    "Number\nof\nborrowers",
    "Average\nLGD",
    "Average\nmaturity",
    "RWA ²",
    "RWA\ndensity ³",
    "Expected\nLoss",
    "Provisions",
)
FIELD_QUALIFICATIONS = {
    "average_pd": ("pd-weighting", "pd-definition", "pd-long-run"),
    "average_lgd": ("lgd-definition", "lgd-downturn"),
    "ead": ("ead-definition", "ccf-definition"),
    "average_ccf": ("ccf-definition",),
    "rwa": ("rwa-overlays",),
    "rwa_density": ("density-rounding",),
    "regulatory_expected_loss": ("el-performing", "el-default"),
}


def reference(page=55, location="CR6", row=None, column=None):
    # The cover has no printed page label; PDF position is still one-based.
    printed_page = "" if page == 1 else str(page)
    return SourceReference(DOCUMENT_ID, page, printed_page, location, row, column)


def window(words, left, right, top, bottom, *, multiline=False):
    selected = [
        w for w in words if left <= w["x0"] < right and top <= w["top"] < bottom
    ]
    lines = []
    for word in sorted(selected, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(word["top"] - lines[-1][0]["top"]) > 1:
            lines.append([])
        lines[-1].append(word)
    text = [
        " ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"]))
        for line in lines
    ]
    return ("\n" if multiline else " ").join(text)


def require(actual, expected):
    if actual != expected:
        raise ValueError(
            f"Unexpected CBA source label: {actual!r}; expected {expected!r}"
        )
    return actual


def source_passage(pdf, page, start, end):
    # Preserve wording, while joining prose line-wraps (including non-\ndefaulted).
    text = " ".join(pdf.pages[page - 1].extract_text().replace("-\n", "-").split())
    begin = text.index(start)
    finish = text.index(end, begin) + len(end)
    return text[begin:finish]


def qualifications(pdf, words):
    dataset = (SourceEndpoint("dataset", DATASET_ID),)
    field = lambda name: (SourceEndpoint("field", name),)
    # Passage delimiters are guards and selectors, not substitute source text.
    passages = (
        (
            "report-entity",
            6,
            "Introduction",
            "This document is prepared",
            "1 January 2025.",
            dataset,
        ),
        (
            "level-2",
            115,
            "Glossary: Level 2",
            "The level at which the Group reports",
            "this report has been produced.",
            dataset,
        ),
        (
            "portfolio-definition",
            116,
            "Glossary: Residential Mortgage",
            "Basel asset class – retail exposures secured",
            "residential mortgage property.",
            dataset,
        ),
        (
            "cr6-introduction",
            54,
            "CR6 introduction",
            "The table below shows the detailed",
            "asset class and PD range.",
            dataset,
        ),
    )
    result = [
        Qualification(
            id, source_passage(pdf, p, start, end), (reference(p, loc),), scope
        )
        for id, p, loc, start, end, scope in passages
    ]
    for id, name, number, top, bottom in (
        ("pd-weighting", "average_pd", 1, 507, 515),
        ("rwa-overlays", "rwa", 2, 516, 524),
        ("density-rounding", "rwa_density", 3, 524, 533),
    ):
        require(window(words, 62, 70, top, bottom), str(number))
        result.append(
            Qualification(
                id,
                window(words, 80, 500, top, bottom),
                (reference(55, f"CR6 footnote {number}"),),
                field(name),
            )
        )
    definitions = (
        (
            "pd-definition",
            50,
            "Probability of Default (PD)",
            "The PD, expressed as a percentage,",
            "within a one year period.",
            field("average_pd"),
        ),
        (
            "pd-long-run",
            50,
            "Probability of Default (PD)",
            "PD estimates are based on a long-run",
            "external data where applicable.",
            field("average_pd"),
        ),
        (
            "lgd-definition",
            52,
            "Loss Given Default (LGD)",
            "LGD is estimated as the net present value",
            "percentage of the EAD.",
            field("average_lgd"),
        ),
        (
            "lgd-downturn",
            52,
            "Loss Given Default (LGD)",
            "For calculating regulatory capital",
            "under stressed economic conditions.",
            field("average_lgd"),
        ),
        (
            "ead-definition",
            52,
            "Exposure at Default (EAD)",
            "EAD is the estimate of the amount",
            "it is the actual amount outstanding.",
            field("ead"),
        ),
        (
            "ccf-definition",
            52,
            "Exposure at Default (EAD)",
            "EAD for loans and commitments",
            "as a facility enters default.",
            field("ead") + field("average_ccf"),
        ),
        (
            "el-performing",
            52,
            "Expected Loss (EL)",
            "Regulatory EL is a hybrid",
            "EAD for non-defaulted exposures.",
            field("regulatory_expected_loss"),
        ),
        (
            "el-default",
            52,
            "Expected Loss (EL): defaulted exposures",
            "the Best Estimate of Expected Loss (BEEL)",
            "defaulted exposure; and",
            field("regulatory_expected_loss") + (SourceEndpoint("row", "band-8"),),
        ),
    )
    result.extend(
        Qualification(
            id, source_passage(pdf, p, start, end), (reference(p, loc),), scope
        )
        for id, p, loc, start, end, scope in definitions
    )
    return tuple(result)


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
        reference(55, location, row, column),
    )


def extract(pdf_path: Path) -> ExtractionBundle:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[54]
        words = page.extract_words()
        title = require(
            window(words, 60, 400, 79, 91),
            "CR6: IRB – Credit risk exposures by portfolio and PD range",
        )
        date_label = require(window(words, 460, 530, 94, 103), "30 June 2025")
        approach = require(window(words, 65, 170, 124, 135), "Subject to AIRB approach")
        portfolio_heading = require(window(words, 65, 120, 157, 167), "Portfolio Type")
        pd_heading = require(window(words, 165, 225, 157, 167), "PD Range")
        portfolio = require(window(words, 65, 155, 170, 180), "Residential mortgage")
        require(window(words, 65, 160, 279, 289), "Qualifying revolving retail")
        headers = tuple(
            require(window(words, left, right, 110, 154, multiline=True), expected)
            for left, right, expected in zip(
                COLUMN_EDGES, COLUMN_EDGES[1:], EXPECTED_HEADERS
            )
        )
        units = tuple(
            window(words, left, right, 157, 167)
            for left, right in pairwise(COLUMN_EDGES)
        )
        notes = qualifications(pdf, words)
        cover = pdf.pages[0].extract_text().splitlines()
        require(cover[-1], "Commonwealth Bank of Australia")
        document_title = " ".join(cover[:-1])
        source_date = re.search(r"\d{1,2} \w+ \d{4}", document_title).group()
        report_date = datetime.strptime(source_date, "%d %B %Y").date()
        publication_text = re.search(
            r"\d{1,2} August 2025", pdf.pages[1].extract_text()
        ).group()
        publication_date = datetime.strptime(publication_text, "%d %B %Y").date()
        context = DatasetContext(
            "context",
            report_date,
            datetime.strptime(date_label, "%d %B %Y").date(),
            date_label,
            "CR6",
            title,
            portfolio,
            Knowledge(
                "CBA and its subsidiaries (the Group)",
                "established",
                ("report-entity",),
            ),
            Knowledge("Level 2", "established", ("level-2",)),
            Knowledge(approach, "established", ("cr6-introduction",)),
            Knowledge(),
            Knowledge(),
            ("report-entity", "level-2", "portfolio-definition", "cr6-introduction"),
            (
                reference(1, "Cover"),
                reference(55, "CR6 date, approach and portfolio headings"),
            ),
        )
        axes = [
            axis("date", "header", date_label, 0),
            axis("approach", "header", approach, 1),
            axis("portfolio-heading", "header", portfolio_heading, 2),
            axis("pd-heading", "header", pd_heading, 3),
            axis(
                "mortgage-block",
                "block",
                portfolio,
                4,
                ("approach", "portfolio-heading"),
            ),
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
        # Locate every row by its PD-label start token, within the inspected block.
        row_tops = sorted(
            w["top"] for w in words if 167 <= w["x0"] <= 169 and 170 < w["top"] < 278
        )
        labels = tuple(window(words, 165, 230, top - 1, top + 8) for top in row_tops)
        if len(labels) != 9 or labels[-1] != "Sub-total":
            raise ValueError(f"Unexpected CBA mortgage row structure: {labels}")
        row_ids = tuple(f"band-{i + 1}" for i in range(len(labels) - 1)) + (
            "portfolio-aggregate",
        )
        records, bands = [], []
        for i, (id, label, top) in enumerate(zip(row_ids, labels, row_tops)):
            aggregate = label == "Sub-total"
            axes.append(
                axis(
                    id,
                    "row",
                    label,
                    i,
                    ("mortgage-block", "pd-heading"),
                    location="CR6 Residential mortgage",
                    row=label,
                )
            )
            if not aggregate:
                interval = re.fullmatch(r"(\d+\.\d+) to <(\d+\.\d+)", label)
                if interval:
                    lower, upper = map(Decimal, interval.groups())
                    kind, category, status = "interval", None, "established"
                else:
                    require(label, "100.00 (Default)")
                    lower, upper, kind, category, status = (
                        None,
                        None,
                        "default",
                        label,
                        "not_applicable",
                    )
                bands.append(
                    BandDefinition(
                        f"pd-band-{i + 1}",
                        label,
                        i,
                        kind,
                        "%",
                        lower,
                        upper,
                        True if interval else None,
                        False if interval else None,
                        status,
                        status,
                        category,
                        reference(55, "CR6 Residential mortgage", row=label),
                    )
                )
            values = {}
            for name, header, left, right in zip(
                CR6_FIELDS, headers, COLUMN_EDGES, COLUMN_EDGES[1:]
            ):
                token = window(words, left, right, top - 1, top + 8)
                parsed = (
                    parse_count_token(token)
                    if name == "reported_borrower_count"
                    else parse_decimal_token(token)
                )
                precision = (
                    None
                    if parsed is None
                    else max(0, -parse_decimal_token(token).as_tuple().exponent)
                )
                missing = None
                if parsed is None:
                    missing = (
                        "not_disclosed_at_this_grain"
                        if name == "provisions" and not aggregate
                        else "blank_unresolved"
                    )
                values[name] = ReportedValue(
                    parsed,
                    token,
                    precision,
                    missing,
                    reference(55, "CR6 Residential mortgage", label, header),
                )
            records.append(
                BronzeCreditRiskExposureRow(
                    id,
                    id,
                    "Sub-total" if aggregate else "band",
                    () if aggregate else (f"pd-band-{i + 1}",),
                    ("mortgage-block",),
                    **values,
                )
            )
        published, bindings = [], []
        for name, header, unit in zip(CR6_FIELDS, headers, units):
            refs = FIELD_QUALIFICATIONS.get(name, ())
            attrs = ()
            if name.startswith("average_"):
                attrs = (
                    SemanticAttribute(
                        "weighting",
                        "EAD at the end of the period"
                        if name == "average_pd"
                        else None,
                        "established" if name == "average_pd" else "unresolved",
                        ("pd-weighting",) if name == "average_pd" else (),
                    ),
                )
            if name == "reported_borrower_count":
                attrs = (SemanticAttribute("counted_entity", None, "unresolved", ()),)
            if unit not in {"$M", "%", "", "Years"}:
                raise ValueError(f"Unexpected source unit: {unit!r}")
            published.append(
                PublishedField(
                    name,
                    header,
                    ("date", "column-" + name),
                    unit,
                    Decimal(1000000) if unit == "$M" else Decimal(1),
                    refs,
                    attrs,
                    reference(55, "CR6 header", column=header),
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
        evidence = (reference(55, "CR6 Residential mortgage PD Range and Sub-total"),)
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            pd_heading,
            tuple(bands),
            ("context",),
            Knowledge(
                "Displayed PD ranges and default category cover the subtotal",
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
            "mortgage-subtotal",
            "total",
            labels[-1],
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
            "cba",
            cover[-1],
            document_title,
            report_date,
            publication_date,
            "au",
            "https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy25/basel-iii-pillar-3%E2%80%93capital-adequacy-risk-disclosures-30-june-2025.pdf",
        )
        return ExtractionBundle(
            document,
            BUNDLE_KEY,
            f"extractions/{BUNDLE_KEY}/extract.py",
            "cr6-v1",
            (dataset,),
        )
