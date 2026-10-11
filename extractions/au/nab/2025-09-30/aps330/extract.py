"""NAB September 2025 mortgage CR6: source-specific geometry and definitions."""

import re
from datetime import date, datetime
from decimal import Decimal
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

DOCUMENT_ID = "nab-2025-09-30-aps330"
DATASET_ID = "cr6-residential-mortgages"
BUNDLE_KEY = "au/nab/2025-09-30/aps330"
# Word-start gutters: a few long header words extend left of the cell border.
COLUMN_EDGES = (166, 225, 286, 330, 384, 429, 480, 531, 582, 633, 684, 733, 786)
COLUMN_IDS = tuple("abcdefghijkl")
EXPECTED_HEADERS = (
    "On-balance\nsheet EaD\npre-CRM",
    "Off-balance\nsheet EaD\npre-CCF and\npre-CRM",
    "Average\nCCF",
    "EaD\npost-CCF\nand\npost-CRM",
    "Weighted\naverage\nPD",
    "Number\nof\nborrowers",
    "Average\nloss given\ndefault\n(LGD)",
    "Average\nmaturity",
    "RWA",
    "RWA\ndensity",
    "Expected\nloss",
    "Provision\nfor credit\nimpairment",
)
EXPECTED_UNITS = ("$m", "$m", "%", "$m", "%", "", "%", "years", "$m", "%", "$m", "$m")
FIELD_QUALIFICATIONS = {
    "reported_borrower_count": ("borrower-definition",),
    "average_maturity": ("maturity-definition",),
    "rwa": ("overlay-exclusion",),
    "rwa_density": ("overlay-exclusion",),
    "provisions": ("provision-definition",),
}
CONTEXT_QUALIFICATIONS = (
    "report-entity",
    "currency-rounding",
    "regulatory-basis",
    "level-2-definition",
    "level-2",
    "cr6-introduction",
    "approach",
)


def reference(page=49, location="CR6", row=None, column=None):
    return SourceReference(
        DOCUMENT_ID, page, "" if page == 1 else str(page - 2), location, row, column
    )


def require(actual, expected):
    if actual != expected:
        raise ValueError(f"Unexpected NAB source: {actual!r}; expected {expected!r}")
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


def qualifications(pdf):
    dataset = (SourceEndpoint("dataset", DATASET_ID),)

    def field(*names):
        return tuple(SourceEndpoint("field", name) for name in names)

    # Only delimiters are prescribed here; the retained prose comes from the PDF.
    passages = (
        (
            "report-entity",
            4,
            "Introduction",
            "The Group, being NAB",
            "measure capital adequacy.",
            dataset,
        ),
        (
            "currency-rounding",
            4,
            "Introduction",
            "Amounts are presented",
            "except where indicated.",
            dataset,
        ),
        (
            "regulatory-basis",
            4,
            "Introduction",
            "National Australia Bank Limited (NAB)",
            "Attachment A of APS 330.",
            dataset,
        ),
        (
            "level-2-definition",
            4,
            "Scope of consolidation",
            "Level 2 comprises NAB",
            "leasing companies.",
            dataset,
        ),
        (
            "level-2",
            4,
            "Scope of consolidation",
            "This report applies",
            "unless otherwise stated.",
            dataset,
        ),
        (
            "cr6-introduction",
            48,
            "CR6 introduction",
            "The following tables provide",
            "band, where:",
            dataset,
        ),
        (
            "approach",
            48,
            "CR6 approach heading",
            "Credit risk exposures subject",
            "by asset class and PD band",
            dataset,
        ),
        (
            "borrower-definition",
            48,
            "CR6 column (f) definition",
            "The number of borrowers in column (f)",
            "subsidiary's underlying asset classes.",
            field("reported_borrower_count"),
        ),
        (
            "maturity-definition",
            48,
            "CR6 column (h) definition",
            "Average maturity in column (h)",
            "template prescribed by APS 330.",
            field("average_maturity"),
        ),
        (
            "overlay-exclusion",
            48,
            "CR6 columns (i) and (j) definition",
            "RWA in column (i)",
            "exclude RWA overlay adjustments.",
            field("rwa", "rwa_density"),
        ),
        (
            "provision-definition",
            48,
            "CR6 column (l) definition",
            "The provision for credit impairment in column (l)",
            "template prescribed by APS 330.",
            field("provisions"),
        ),
    )
    texts = {
        page: " ".join(pdf.pages[page - 1].extract_text().split()) for page in (4, 48)
    }
    notes = []
    for id, page, location, start, end, scope in passages:
        text = texts[page]
        begin = text.index(start)
        finish = text.index(end, begin) + len(end)
        notes.append(
            Qualification(id, text[begin:finish], (reference(page, location),), scope)
        )
    return tuple(notes)


def axis(
    id,
    kind,
    label,
    order,
    parents=(),
    quals=(),
    location="CR6",
    row=None,
    column=None,
    page=49,
):
    return SourceAxisItem(
        id,
        kind,
        label,
        order,
        parents,
        ("context",),
        quals,
        reference(page, location, row, column),
    )


def is_shaded(page, left, right, top):
    """Observed dark-grey cell fill, distinct from the light table background."""
    x = (left + right) / 2
    return any(
        rect["x0"] < x < rect["x1"]
        and rect["top"] < top < rect["bottom"]
        and rect["non_stroking_color"] == (0, 0, 0, 0.4)
        for rect in page.rects
    )


def extract(pdf_path: Path) -> ExtractionBundle:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[48]
        words = page.extract_words()
        definition_lines = pdf.pages[47].extract_text().splitlines()
        title = require(
            next(line for line in definition_lines if line.startswith("CR6:")),
            "CR6: IRB – credit risk exposures by portfolio and probability of default range",
        )
        approach = require(
            next(
                line
                for line in definition_lines
                if line.startswith("Credit risk exposures subject")
            ),
            "Credit risk exposures subject to the A-IRB approach by asset class and PD band",
        )
        date_label = require(window(words, 440, 520, 80, 90), "As at 30 Sep 25")
        pd_heading = require(window(words, 60, 160, 142, 153), "PD scale")
        portfolio = require(window(words, 60, 165, 282, 295), "Residential mortgage")
        require(window(words, 60, 165, 156, 168), "Retail SME")
        headers, units = [], []
        for left, right, letter, header, unit in zip(
            COLUMN_EDGES, COLUMN_EDGES[1:], COLUMN_IDS, EXPECTED_HEADERS, EXPECTED_UNITS
        ):
            require(window(words, left, right, 93, 102), letter)
            headers.append(
                require(window(words, left, right, 105, 141, multiline=True), header)
            )
            units.append(require(window(words, left, right, 143, 153), unit))
        notes = qualifications(pdf)
        report_date = datetime.strptime(date_label, "As at %d %b %y").date()
        cover = pdf.pages[0].extract_text().splitlines()
        require(cover[1], report_date.strftime("as at %d %B %Y"))
        entity = require(cover[-1].split(" ABN ")[0], "National Australia Bank Limited")
        context = DatasetContext(
            "context",
            report_date,
            report_date,
            date_label,
            "CR6",
            title,
            portfolio,
            Knowledge(
                "NAB and its controlled entities", "established", ("report-entity",)
            ),
            Knowledge("Level 2", "established", ("level-2-definition", "level-2")),
            Knowledge("A-IRB", "established", ("regulatory-basis", "approach")),
            Knowledge(),
            Knowledge("AUD", "established", ("currency-rounding",)),
            CONTEXT_QUALIFICATIONS,
            (
                reference(1, "Cover"),
                reference(48, "CR6 title and approach"),
                reference(49, "CR6 date and portfolio headings"),
            ),
        )
        axes = [
            axis("date", "header", date_label, 0),
            axis("approach", "header", approach, 1, page=48),
            axis("pd-heading", "header", pd_heading, 2),
            axis("mortgage-block", "block", portfolio, 3, ("approach",)),
        ]
        for i, (name, letter, header) in enumerate(
            zip(CR6_FIELDS, COLUMN_IDS, headers)
        ):
            axes.append(
                axis(
                    letter,
                    "column",
                    header,
                    i,
                    ("date",),
                    FIELD_QUALIFICATIONS.get(name, ()),
                    "CR6 header",
                    column=letter,
                )
            )

        # Start coordinates select the nine source rows below the mortgage heading.
        # Empty shaded windows are read individually, never removed before zipping.
        row_tops = sorted(
            w["top"] for w in words if 62 <= w["x0"] < 63 and 295 < w["top"] < 410
        )
        if len(row_tops) != 9:
            raise ValueError("Unexpected NAB mortgage row structure")
        labels = tuple(window(words, 60, 165, top - 1, top + 8) for top in row_tops)
        total = require(labels[-1], "Sub-total")
        row_ids = tuple(f"band-{i + 1}" for i in range(8)) + ("portfolio-aggregate",)
        records, bands = [], []
        for i, (id, label, top) in enumerate(zip(row_ids, labels, row_tops)):
            aggregate = i == 8
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
                        reference(49, "CR6 Residential mortgage", row=label),
                    )
                )
            values = {}
            for name, letter, left, right in zip(
                CR6_FIELDS, COLUMN_IDS, COLUMN_EDGES, COLUMN_EDGES[1:]
            ):
                token = window(words, left, right, top - 1, top + 8)
                number = parse_decimal_token(token)
                parsed = (
                    parse_count_token(token)
                    if name == "reported_borrower_count"
                    else number
                )
                precision = (
                    None if number is None else max(0, -number.as_tuple().exponent)
                )
                shaded = name == "average_maturity" or (
                    name == "provisions" and not aggregate
                )
                require(is_shaded(page, left, right, top), shaded)
                missing = None
                if parsed is None:
                    if token in {"-", "–"}:
                        missing = "dash_unresolved"
                    elif name == "average_maturity":
                        # PDF 48 defines omission for classes not using it in RWA.
                        missing = "not_applicable"
                    elif name == "provisions" and not aggregate:
                        # PDF 48 expressly says disclosure is by asset class only.
                        missing = "not_disclosed_at_this_grain"
                    else:
                        missing = "blank_unresolved"
                values[name] = ReportedValue(
                    parsed,
                    token,
                    precision,
                    missing,
                    reference(49, "CR6 Residential mortgage", label, letter),
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
        for name, letter, header, unit in zip(CR6_FIELDS, COLUMN_IDS, headers, units):
            refs = FIELD_QUALIFICATIONS.get(name, ())
            attrs = ()
            if name.startswith("average_"):
                attrs = (SemanticAttribute("weighting", None, "unresolved", ()),)
            if name == "reported_borrower_count":
                attrs = (
                    SemanticAttribute(
                        "counted_entity", "agreement", "established", refs
                    ),
                    SemanticAttribute("distinctness", None, "unresolved", ()),
                )
            if name in {"rwa", "rwa_density"}:
                attrs = (
                    SemanticAttribute(
                        "overlay_treatment", "excluded", "established", refs
                    ),
                )
            if name == "average_maturity":
                attrs += (
                    SemanticAttribute(
                        "missing_cell_presentation", "shaded", "established", refs
                    ),
                )
            if name == "provisions":
                attrs = (
                    SemanticAttribute(
                        "band_cell_presentation", "shaded", "established", refs
                    ),
                )
            published.append(
                PublishedField(
                    name,
                    header,
                    ("date", letter),
                    unit,
                    Decimal(1000000) if unit == "$m" else Decimal(1),
                    refs,
                    attrs,
                    reference(49, "CR6 header", column=letter),
                )
            )
            bindings.append(
                ValueBinding(
                    "binding-" + name,
                    name,
                    name,
                    row_ids,
                    (letter,),
                    ("context",),
                    refs,
                )
            )
        evidence = (reference(49, "CR6 Residential mortgage PD scale and Sub-total"),)
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
            "nab",
            entity,
            " ".join(cover[:-1]),
            report_date,
            # Publication date and official source are acquisition metadata.
            date(2025, 11, 6),
            "au",
            "https://www.nab.com.au/content/dam/nab/documents/notice/corporate/2025-full-year-pillar-3-report.pdf",
        )
        return ExtractionBundle(
            document,
            BUNDLE_KEY,
            f"extractions/{BUNDLE_KEY}/extract.py",
            "cr6-v1",
            (dataset,),
        )
