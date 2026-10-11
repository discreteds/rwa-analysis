"""ANZ September 2025: reviewed AIRB mortgage rows 10–18 on PDF page 57."""

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

DOCUMENT_ID = "anz-2025-09-30-aps330"
DATASET_ID = "cr6-residential-mortgages"
BUNDLE_KEY = "au/anz/2025-09-30/aps330"
# Reviewed word-start gutters, including multiline headers and empty cells.
COLUMN_EDGES = (218, 270, 322, 370, 418, 466, 518, 566, 614, 653, 706, 752, 796)
HEADERS = (
    "Original on-\nbalance\nsheet gross\nexposure",
    "Off-balance\nsheet\nexposures",
    "Average\nCCF",
    "EAD\npost CRM\nand post-\nCCF",
    "Average\nPD",
    "Number of\nBorrowers",
    "Average\nLGD",
    "Average\nmaturity",
    "RWA",
    "RWA density",
    "EL",
    "Provisions",
)
UNITS = ("$M", "$M", "%", "$M", "%", "", "%", "Yr", "$M", "%", "$M", "$M")
FIELD_QUALIFICATIONS = {
    "average_pd": ("pd-definition",),
    "ead": ("ead-definition",),
    "average_lgd": ("lgd-definition",),
    "reported_borrower_count": ("borrower-definition",),
    "average_maturity": ("maturity-definition", "maturity-modification"),
    "rwa": ("cms2-overlay-context",),
    "rwa_density": ("cms2-overlay-context",),
}
CONTEXT_QUALIFICATIONS = (
    "report-entity",
    "entity-hierarchy",
    "level-2",
    "suncorp-entity",
    "suncorp-exclusion",
    "currency-rounding",
    "cr6-introduction",
    "slotting-exclusion",
    "cms2-suncorp-context",
    "nz-separate",
)


def reference(page=57, location="CR6", row=None, column=None):
    return SourceReference(
        DOCUMENT_ID, page, "" if page == 1 else str(page), location, row, column
    )


def require(actual, expected):
    if actual != expected:
        raise ValueError(f"Unexpected ANZ source: {actual!r}; expected {expected!r}")
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
    # Delimiters select source prose; all retained text is read from this PDF.
    passages = (
        (
            "report-entity",
            6,
            "Introduction: reporting entity",
            "This document is prepared for",
            "requirements.",
            (),
        ),
        (
            "entity-hierarchy",
            6,
            "Introduction: entity hierarchy",
            "Australia and New Zealand Banking Group Limited (ANZBGL) is",
            "as the ANZGHL Group.",
            (),
        ),
        (
            "level-2",
            6,
            "Introduction: Level 2",
            "The APS 330 disclosure has been prepared",
            "Any reference to ANZ / the Group refers to ANZ’s Level 2 Banking Group.",
            (),
        ),
        (
            "suncorp-entity",
            6,
            "Suncorp Bank Acquisition",
            "Suncorp Bank is the trading name",
            "Banking Group Limited (ANZBGL).",
            (),
        ),
        (
            "suncorp-exclusion",
            54,
            "CRE: Suncorp IRB exclusion",
            "On 31 July 2024 ANZ added",
            "IRB specific disclosure tables.",
            (),
        ),
        (
            "currency-rounding",
            7,
            "Currency statement",
            "Unless otherwise stated, all amounts",
            "AUD millions.",
            (),
        ),
        (
            "cr6-introduction",
            57,
            "CR6 introduction",
            "The table below provides",
            "under the IRB approach.",
            (),
        ),
        (
            "slotting-exclusion",
            57,
            "CR6 footnote 1",
            "Excludes Specialised Lending",
            "supervisory slotting.",
            (),
        ),
        (
            "maturity-definition",
            57,
            "CR6 footnote 2",
            "Average maturity has been excluded",
            "the RWA calculation.",
            ("average_maturity",),
        ),
        (
            "borrower-definition",
            57,
            "CR6 footnote 3",
            "The definition of a “borrower”",
            "more than one PD band.",
            ("reported_borrower_count",),
        ),
        (
            "maturity-modification",
            116,
            "Appendix 1: CR6, column h, rationale",
            "Average maturity has been excluded",
            "information for users.",
            ("average_maturity",),
        ),
        (
            "cms2-overlay-context",
            23,
            "CMS2 Sep 25 footnote 2 (cross-table context)",
            "Retail Residential Mortgages RWA include",
            "30 June 2024 reporting period.",
            ("rwa", "rwa_density"),
        ),
        (
            "cms2-suncorp-context",
            23,
            "CMS2: Suncorp standardised scope",
            "Suncorp Bank is a standardised ADI",
            "Residential Mortgages Asset Classes.",
            (),
        ),
        (
            "nz-separate",
            60,
            "CR6 separate NZ block heading",
            "RBNZ regulated entities",
            "RBNZ regulated entities",
            (),
        ),
        (
            "pd-definition",
            36,
            "CRA: PD definition",
            "Probability of Default (PD) is",
            "over a 12-month horizon;",
            ("average_pd",),
        ),
        (
            "ead-definition",
            36,
            "CRA: EAD definition",
            "Exposure at Default (EAD) represents",
            "under committed limits); and",
            ("ead",),
        ),
        (
            "lgd-definition",
            36,
            "CRA: LGD definition",
            "Loss Given Default (LGD) is",
            "percentage of the facility’s EAD.",
            ("average_lgd",),
        ),
    )
    texts = {
        page: " ".join(pdf.pages[page - 1].extract_text().split())
        for page in {item[1] for item in passages}
    }
    # Column-aware read prevents the adjacent "exposures" line entering rationale.
    texts[116] = " ".join(
        pdf.pages[115].crop((612, 200, 786, 238)).extract_text().split()
    )
    notes = []
    for id, page, location, start, end, fields in passages:
        text = texts[page]
        begin = text.index(start)
        finish = text.index(end, begin) + len(end)
        scope = (
            tuple(SourceEndpoint("field", name) for name in fields)
            if fields
            else (SourceEndpoint("dataset", DATASET_ID),)
        )
        notes.append(
            Qualification(id, text[begin:finish], (reference(page, location),), scope)
        )
    return tuple(notes)


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
        reference(location=location, row=row, column=column),
    )


def extract(pdf_path: Path) -> ExtractionBundle:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[56]
        words = page.extract_words()
        title = require(
            page.extract_text().splitlines()[2],
            "CR6: IRB – Credit risk exposures by portfolio and PD range",
        )
        date_label = require(window(words, 490, 525, 125, 135), "Sep 25")
        approach = require(window(words, 75, 115, 190, 200), "AIRB")
        pd_heading = require(
            window(words, 75, 125, 172, 190, multiline=True), "Portfolio/\nPD scale"
        )
        portfolio = require(window(words, 75, 218, 314, 325), "Residential Mortgages")
        headers, units = [], []
        for left, right, header, unit in zip(
            COLUMN_EDGES, COLUMN_EDGES[1:], HEADERS, UNITS
        ):
            headers.append(
                require(window(words, left, right, 135, 170, multiline=True), header)
            )
            units.append(require(window(words, left, right, 190, 200), unit))
        cover = pdf.pages[0].extract_text().splitlines()
        reporting_date = datetime.strptime(cover[4], "As at %d %B %Y").date()
        require(reporting_date, date(2025, 9, 30))
        require(reporting_date.strftime("%b %y"), date_label)
        notes = qualifications(pdf)
        entity_note = next(
            note.source_text for note in notes if note.id == "report-entity"
        )
        entity = require(
            entity_note.split("prepared for ")[1].split(" (")[0], "ANZ BH Pty Ltd"
        )
        context = DatasetContext(
            "context",
            reporting_date,
            reporting_date,
            date_label,
            "CR6",
            title,
            portfolio,
            Knowledge(entity, "established", ("report-entity", "entity-hierarchy")),
            Knowledge("Level 2", "established", ("level-2",)),
            Knowledge(
                approach, "established", ("cr6-introduction", "suncorp-exclusion")
            ),
            # Separate NZ disclosure supports the working Australian selection,
            # but does not establish every exposure's collateral geography.
            Knowledge("Australia", "provisional", ("nz-separate", "suncorp-exclusion")),
            Knowledge("AUD", "established", ("currency-rounding",)),
            CONTEXT_QUALIFICATIONS,
            (
                reference(1, "Cover reporting date"),
                reference(6, "Introduction: entity and perimeter"),
                reference(57, "CR6 date, AIRB and portfolio headings"),
            ),
        )
        axes = [
            axis("date", "header", date_label, 0),
            axis("approach", "header", approach, 1),
            axis("pd-heading", "header", pd_heading, 2),
            axis("mortgage-block", "block", portfolio, 3, ("approach",)),
        ]
        columns = tuple(f"column-{i}" for i in range(1, 13))
        for i, (name, column, header) in enumerate(zip(CR6_FIELDS, columns, headers)):
            axes.append(
                axis(
                    column,
                    "column",
                    header,
                    i,
                    ("date",),
                    FIELD_QUALIFICATIONS.get(name, ()),
                    "CR6 header",
                    column=column,
                )
            )

        # Identify the reviewed numbered rows, not another mortgage block or date.
        markers = sorted(
            (w for w in words if 63 < w["x0"] < 66 and 325 < w["top"] < 430),
            key=lambda w: w["top"],
        )
        require(tuple(w["text"] for w in markers), tuple(str(n) for n in range(10, 19)))
        row_ids = tuple(f"band-{i}" for i in range(1, 9)) + ("portfolio-aggregate",)
        records, bands = [], []
        for i, (id, marker) in enumerate(zip(row_ids, markers)):
            top, source_row = marker["top"], marker["text"]
            label = window(words, 75, 218, top - 1, top + 8)
            aggregate = i == 8
            if aggregate:
                require(label, "Sub-Total AIRB Residential Mortgages")
            axes.append(
                axis(
                    id,
                    "row",
                    label,
                    i,
                    ("mortgage-block", "pd-heading"),
                    location="CR6 Residential Mortgages",
                    row=source_row,
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
                        reference(location="CR6 Residential Mortgages", row=source_row),
                    )
                )
            values = {}
            for name, column, left, right in zip(
                CR6_FIELDS, columns, COLUMN_EDGES, COLUMN_EDGES[1:]
            ):
                token = window(words, left, right, top - 1, top + 8)
                number = parse_decimal_token(token)
                value = (
                    parse_count_token(token)
                    if name == "reported_borrower_count"
                    else number
                )
                missing = None
                if number is None:
                    if name == "average_maturity" and token == "-":
                        missing = "not_applicable"
                    elif name == "provisions" and not aggregate and token == "":
                        missing = "not_disclosed_at_this_grain"
                    else:
                        missing = "dash_unresolved" if token else "blank_unresolved"
                values[name] = ReportedValue(
                    value,
                    token,
                    None if number is None else max(0, -number.as_tuple().exponent),
                    missing,
                    reference(
                        location="CR6 Residential Mortgages",
                        row=source_row,
                        column=column,
                    ),
                )
            records.append(
                BronzeCreditRiskExposureRow(
                    id,
                    id,
                    label if aggregate else "band",
                    () if aggregate else (f"pd-band-{i + 1}",),
                    ("mortgage-block",),
                    **values,
                )
            )
        published, bindings = [], []
        for name, column, header, unit in zip(CR6_FIELDS, columns, headers, units):
            refs = FIELD_QUALIFICATIONS.get(name, ())
            attrs = (
                (SemanticAttribute("weighting", None, "unresolved", ()),)
                if name.startswith("average_")
                else ()
            )
            if name == "reported_borrower_count":
                attrs = (
                    SemanticAttribute("counted_entity", None, "unresolved", refs),
                    SemanticAttribute("distinctness", None, "unresolved", refs),
                )
            if name in {"rwa", "rwa_density"}:
                # CMS2's statement is evidence, not a CR6 applicability decision.
                attrs = (
                    SemanticAttribute("overlay_treatment", None, "unresolved", refs),
                )
            if name == "average_maturity":
                attrs += (
                    SemanticAttribute(
                        "missing_cell_presentation", "dash", "established", refs
                    ),
                )
            if name == "provisions":
                attrs = (
                    SemanticAttribute(
                        "band_cell_presentation", "blank", "established", ()
                    ),
                )
            published.append(
                PublishedField(
                    name,
                    header,
                    ("date", column),
                    unit,
                    Decimal(1000000) if unit == "$M" else Decimal(1),
                    refs,
                    attrs,
                    reference(location="CR6 header", column=column),
                )
            )
            bindings.append(
                ValueBinding(
                    "binding-" + name,
                    name,
                    name,
                    row_ids,
                    (column,),
                    ("context",),
                    refs,
                )
            )
        evidence = (
            reference(
                location="CR6 Residential Mortgages PD scale and Sub-Total", row="10–18"
            ),
        )
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
            records[-1].source_row_role,
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
            "anz",
            entity,
            " ".join(cover),
            reporting_date,
            date(2025, 11, 10),
            "au",
            "https://www.anz.com/content/dam/anzcom/shareholder/full-year-results-announcement/2025-september-pillar-3-disclosure.pdf",
        )
        return ExtractionBundle(
            document,
            BUNDLE_KEY,
            f"extractions/{BUNDLE_KEY}/extract.py",
            "cr6-v1",
            (dataset,),
        )
