"""NAB September 2025 mortgage CR6/CR9: source geometry and definitions."""

import re
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from itertools import pairwise
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
            "disclosure-v2",
            (dataset, extract_cr9(pdf, dataset)),
        )


def extract_cr9(pdf, cr6):
    """The first PDF61 block excludes the separately labelled BNZ mortgages."""
    dataset_id = "cr9-residential-mortgages"
    words = pdf.pages[60].extract_words()
    intro = " ".join(pdf.pages[59].extract_text().split())
    title = next(
        s for s in pdf.pages[59].extract_text().splitlines() if s.startswith("CR9:")
    )
    field_names = (
        "weighted_average_pd",
        "arithmetic_average_pd",
        "current_year_borrower_count",
        "previous_year_borrower_count",
        "defaulted_borrower_count",
        "new_defaulted_borrower_count",
        "historical_annual_default_rate",
    )
    edges = (191, 240, 290, 340, 389, 439, 489, 539)
    headers = tuple(
        window(
            words,
            left,
            right,
            128 if i in (2, 3) else 94,
            145 if i in (2, 3) else 140,
            multiline=True,
        )
        for i, (left, right) in enumerate(pairwise(edges))
    )
    counts = field_names[2:6]
    field_notes = {
        "weighted_average_pd": ("cr9-weighting",),
        "arithmetic_average_pd": ("cr9-weighting", "borrower-definition"),
        **{name: ("cr9-counting", "borrower-definition") for name in counts},
        "historical_annual_default_rate": ("cr9-history", "cr9-framework"),
    }
    field_notes["defaulted_borrower_count"] += ("cr9-defaults",)
    field_notes["new_defaulted_borrower_count"] += ("cr9-defaults", "cr9-new-defaults")
    shared = (
        "report-entity",
        "currency-rounding",
        "regulatory-basis",
        "level-2-definition",
        "level-2",
    )
    notes = [
        replace(q, scope=(SourceEndpoint("dataset", dataset_id),))
        for q in cr6.metadata.qualifications
        if q.id in shared
    ]
    notes.append(
        replace(
            next(
                q for q in cr6.metadata.qualifications if q.id == "borrower-definition"
            ),
            scope=tuple(
                SourceEndpoint("field", f) for f in (*counts, "arithmetic_average_pd")
            ),
        )
    )
    passages = (
        ("cr9-introduction", "The following tables provide results", "for each ECAI."),
        (
            "cr9-weighting",
            "Weighted average PD in column (a)",
            "divided by the number of borrowers.",
        ),
        ("cr9-counting", "The approach to measure", "probability of default range."),
        ("cr9-defaults", "A borrower is included", "during the year."),
        (
            "cr9-new-defaults",
            "The number of borrowers in column (e)",
            "during the financial year.",
        ),
        ("cr9-history", "A 10-year observation period", "has been averaged."),
        (
            "cr9-framework",
            "Changes in asset class definitions",
            "best endeavours basis.",
        ),
        (
            "cr9-bnz-separation",
            "APS 330 requires information",
            "represents 91% of credit RWA.",
        ),
    )
    for name, start, end in passages:
        begin = intro.index(start)
        text = intro[begin : intro.index(end, begin) + len(end)]
        scope = tuple(
            SourceEndpoint("field", f) for f in field_names if name in field_notes[f]
        )
        notes.append(
            Qualification(
                name,
                text,
                (reference(60, name),),
                scope or (SourceEndpoint("dataset", dataset_id),),
            )
        )
    old = cr6.metadata.context
    portfolio = window(words, 45, 190, 153, 163)
    context = Cr9Context(
        "context",
        old.document_date,
        "CR9",
        title,
        portfolio,
        old.reporting_entity,
        old.consolidation_scope,
        Knowledge("A-IRB", "established", ("cr9-introduction",)),
        Knowledge(),
        old.currency,
        shared + ("cr9-introduction", "cr9-bnz-separation"),
        (
            reference(60, "CR9 introduction and A-IRB heading"),
            reference(61, "CR9 headings"),
        ),
    )

    def item(
        id, kind, label, order, parents=(), quals=(), page=61, row=None, column=None
    ):
        return SourceAxisItem(
            id,
            kind,
            label,
            order,
            parents,
            ("context",),
            quals,
            reference(page, "CR9" if page == 61 else "External ratings", row, column),
        )

    axes = [
        item("mortgage-block", "block", portfolio, 0),
        item("pd-heading", "header", window(words, 45, 100, 139, 149), 1),
        item("borrower-counts", "header", window(words, 290, 389, 94, 102), 2),
    ]
    row_ids = tuple(f"band-{i}" for i in range(1, 9))
    published, bindings = [], []
    for i, (name, header) in enumerate(zip(field_names, headers)):
        refs = field_notes[name]
        parents = ("borrower-counts",) if i in (2, 3) else ()
        axes.append(
            item("column-" + name, "column", header, i, parents, refs, column=header)
        )
        attrs = ()
        if name in counts:
            attrs = (
                SemanticAttribute(
                    "counted_entity",
                    "agreement",
                    "established",
                    ("cr9-counting", "borrower-definition"),
                ),
                SemanticAttribute("distinctness", None, "unresolved", ()),
            )
        elif name == "weighted_average_pd":
            attrs = (
                SemanticAttribute(
                    "weighting", "EAD", "established", ("cr9-weighting",)
                ),
            )
        elif name == "arithmetic_average_pd":
            attrs = (
                SemanticAttribute(
                    "weighting", "arithmetic_by_agreements", "established", refs
                ),
            )
        if i >= 4:
            attrs += (
                SemanticAttribute(
                    "default_cell_presentation", "shaded", "established", ()
                ),
            )
        published.append(
            PublishedField(
                name,
                header,
                parents + ("column-" + name,),
                "" if name in counts else "%",
                Decimal(1),
                refs,
                attrs,
                reference(61, "CR9 header", column=header),
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
    rating_words = pdf.pages[45].extract_words()
    rating_edges = (340, 440, 550)
    agencies = tuple(
        window(rating_words, l, r, 139, 157, multiline=True)
        for l, r in pairwise(rating_edges)
    )
    for j, agency in enumerate(agencies):
        axes.append(
            item(
                f"rating-{j}", "column", agency, j, quals=("cr9-introduction",), page=46
            )
        )
    tops = sorted(
        w["top"] for w in words if 48 <= w["x0"] < 49 and 165 < w["top"] < 260
    )
    rating_tops = sorted(
        w["top"] for w in rating_words if 255 <= w["x0"] < 256 and 159 < w["top"] < 255
    )
    rows, bands, relationships = [], [], []
    for i, top in enumerate(tops):
        rid = row_ids[i]
        label = window(words, 45, 190, top - 1, top + 8)
        axes.append(
            item(rid, "row", label, i, ("mortgage-block", "pd-heading"), row=label)
        )
        for j, (left, right) in enumerate(pairwise(rating_edges)):
            axes.append(
                item(
                    f"{rid}-rating-{j}",
                    "header",
                    window(
                        rating_words,
                        left,
                        right,
                        rating_tops[i] - 1,
                        rating_tops[i] + 8,
                    ),
                    j,
                    (rid, f"rating-{j}"),
                    ("cr9-introduction",),
                    46,
                    label,
                    agencies[j],
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
                reference(61, "CR9", row=label),
            )
        )
        cells = {}
        for name, header, left, right in zip(field_names, headers, edges, edges[1:]):
            token = window(words, left, right, top - 1, top + 8)
            value = (
                parse_count_token(token)
                if name in counts
                else parse_decimal_token(token)
            )
            precision = (
                None
                if value is None
                else 0
                if name in counts
                else max(0, -value.as_tuple().exponent)
            )
            cells[name] = ReportedValue(
                value,
                token,
                precision,
                ("dash_unresolved" if token == "-" else "blank_unresolved")
                if value is None
                else None,
                reference(61, "CR9 Residential mortgage", label, header),
            )
        rows.append(
            Cr9BacktestingRow(
                rid, rid, "band", (f"pd-band-{i + 1}",), ("mortgage-block",), **cells
            )
        )
        if interval:
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
                        reference(60, "cr9-new-defaults"),
                        reference(61, "CR9", label, headers[5]),
                    ),
                )
            )
    descriptors = (
        TemporalDescriptor(
            "current-year",
            "As at 30 Sep 25",
            point="2025-09-30",
            point_status="established",
            evidence=(reference(61, "CR9 count header"),),
        ),
        TemporalDescriptor(
            "previous-year",
            "As at 30 Sep 24",
            point="2024-09-30",
            point_status="established",
            evidence=(reference(61, "CR9 count header"),),
        ),
        TemporalDescriptor(
            "annual",
            "financial year",
            start="2024-10-01",
            end="2025-09-30",
            start_status="established",
            end_status="established",
            duration_amount=Decimal(1),
            duration_unit="years",
            duration_status="established",
            qualification_refs=("cr9-defaults",),
            evidence=(
                reference(1, "Full Year report cover"),
                reference(60, "cr9-defaults"),
            ),
        ),
        TemporalDescriptor(
            "history",
            "10-year observation period",
            duration_amount=Decimal(10),
            duration_unit="years",
            duration_status="established",
            qualification_refs=("cr9-history", "cr9-framework"),
            evidence=(reference(60, "cr9-history"),),
        ),
        TemporalDescriptor(
            "unspecified", "", evidence=(reference(60, "CR9 definitions"),)
        ),
    )
    roles = (
        ("weighted_average_pd", "measurement", "current-year"),
        ("weighted_average_pd", "weight_measurement", "current-year"),
        ("arithmetic_average_pd", "measurement", "unspecified"),
        ("current_year_borrower_count", "measurement", "current-year"),
        ("previous_year_borrower_count", "measurement", "previous-year"),
        ("defaulted_borrower_count", "outcome_window", "annual"),
        ("new_defaulted_borrower_count", "outcome_window", "annual"),
        ("historical_annual_default_rate", "history_window", "history"),
    )
    segmentation = SegmentationDefinition(
        "pd-segmentation",
        "PD scale",
        tuple(bands),
        ("context",),
        Knowledge(),
        Knowledge(
            "Non-overlapping printed intervals and separate default category",
            "established",
        ),
        (reference(61, "CR9 PD scale"),),
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
            tuple(
                TemporalBinding(rid, f, role, t)
                for rid in row_ids
                for f, role, t in roles
            ),
        ),
        tuple(rows),
    )
