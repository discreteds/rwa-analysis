"""ANZ September 2025 AIRB mortgage declarations, including partial CR9 timing."""

import itertools
from datetime import date
from decimal import Decimal
from pathlib import Path
from runpy import run_path

from rwa_analysis.catalogue.models import EvidenceRef
from rwa_analysis.catalogue.models import SemanticAttribute as Assertion
from rwa_analysis.extraction.definitions import (
    CaptureDefinition,
    CaptureSnapshot,
    CellBinding,
    ContextDefinition,
    DomainFieldBinding,
    FragmentRef,
    OccurrenceBinding,
    OccurrenceLink,
    OccurrenceRef,
    PhysicalBinding,
    PhysicalParameter,
    TemporalRole,
)
from rwa_analysis.extraction.models import (
    BandDefinition,
    Knowledge,
    Qualification,
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
    SourceTable,
    SourceTableMetadata,
    TableContext,
    TableField,
)
from rwa_analysis.extraction.temporal import TemporalDescriptor

DOCUMENT = "anz-2025-09-30-aps330"
BUNDLE = "au/anz/2025-09-30/aps330"
BOUNDS = ("0.00", "0.15", "0.25", "0.50", "0.75", "2.50", "10.00", "100.00")
LABELS = tuple(f"{a} to <{b}" for a, b in itertools.pairwise(BOUNDS)) + (
    "100.00 (Default)",
)
CR6 = (
    ("on_balance_exposure", "Original on-\nbalance\nsheet gross\nexposure", "$M", ()),
    ("off_balance_exposure", "Off-balance\nsheet\nexposures", "$M", ()),
    ("average_ccf", "Average\nCCF", "%", ()),
    ("ead", "EAD\npost CRM\nand post-\nCCF", "$M", ("ead-definition",)),
    ("average_pd", "Average\nPD", "%", ("pd-definition",)),
    ("reported_borrower_count", "Number of\nBorrowers", "", ("borrower-definition",)),
    ("average_lgd", "Average\nLGD", "%", ("lgd-definition",)),
    (
        "average_maturity",
        "Average\nmaturity",
        "Yr",
        ("maturity-definition", "maturity-modification"),
    ),
    ("rwa", "RWA", "$M", ("cms2-overlay-context",)),
    ("rwa_density", "RWA density", "%", ("cms2-overlay-context",)),
    ("regulatory_expected_loss", "EL", "$M", ()),
    ("provisions", "Provisions", "$M", ()),
)
CR9 = (
    ("weighted_average_pd", "Weighted\naverage PD", "%", ("pd-definition",)),
    (
        "arithmetic_average_pd",
        "Arithmetic\naverage PD by\nBorrowers",
        "%",
        ("pd-definition",),
    ),
    ("previous_year_borrower_count", "End of previous\nyear", "", ()),
    ("current_year_borrower_count", "End of the year", "", ()),
    ("defaulted_borrower_count", "Defaulted\nBorrowers in the\nyear", "", ()),
    (
        "new_defaulted_borrower_count",
        "of which: new\ndefaulted Borrowers\nin the year",
        "",
        (),
    ),
    (
        "historical_annual_default_rate",
        "Average historical\nannual default rate",
        "%",
        ("cr9-history", "cr9-history-exclusions", "cr9-corporate-history-context"),
    ),
)
SHARED = (
    "report-entity",
    "entity-hierarchy",
    "level-2",
    "suncorp-entity",
    "suncorp-exclusion",
    "currency-rounding",
)
PASSAGES = (
    (
        "report-entity",
        6,
        "Introduction: reporting entity",
        "This document is prepared for",
        "requirements.",
    ),
    (
        "entity-hierarchy",
        6,
        "Introduction: entity hierarchy",
        "Australia and New Zealand Banking Group Limited (ANZBGL) is",
        "as the ANZGHL Group.",
    ),
    (
        "level-2",
        6,
        "Introduction: Level 2",
        "The APS 330 disclosure has been prepared",
        "Any reference to ANZ / the Group refers to ANZ’s Level 2 Banking Group.",
    ),
    (
        "suncorp-entity",
        6,
        "Suncorp Bank Acquisition",
        "Suncorp Bank is the trading name",
        "Banking Group Limited (ANZBGL).",
    ),
    (
        "suncorp-exclusion",
        54,
        "CRE: Suncorp IRB exclusion",
        "On 31 July 2024 ANZ added",
        "IRB specific disclosure tables.",
    ),
    (
        "currency-rounding",
        7,
        "Currency statement",
        "Unless otherwise stated, all amounts",
        "AUD millions.",
    ),
    (
        "cr6-introduction",
        57,
        "CR6 introduction",
        "The table below provides",
        "under the IRB approach.",
    ),
    (
        "slotting-exclusion",
        57,
        "CR6 footnote 1",
        "Excludes Specialised Lending",
        "supervisory slotting.",
    ),
    (
        "maturity-definition",
        57,
        "CR6 footnote 2",
        "Average maturity has been excluded",
        "the RWA calculation.",
    ),
    (
        "borrower-definition",
        57,
        "CR6 footnote 3",
        "The definition of a “borrower”",
        "more than one PD band.",
    ),
    (
        "maturity-modification",
        116,
        "Appendix 1: CR6, column h, rationale",
        "Average maturity has been excluded",
        "information for users.",
    ),
    (
        "cms2-overlay-context",
        23,
        "CMS2 Sep 25 footnote 2 (cross-table context)",
        "Retail Residential Mortgages RWA include",
        "30 June 2024 reporting period.",
    ),
    (
        "cms2-suncorp-context",
        23,
        "CMS2: Suncorp standardised scope",
        "Suncorp Bank is a standardised ADI",
        "Residential Mortgages Asset Classes.",
    ),
    (
        "nz-separate",
        60,
        "CR6 separate NZ block heading",
        "RBNZ regulated entities",
        "RBNZ regulated entities",
    ),
    (
        "pd-definition",
        36,
        "CRA: PD definition",
        "Probability of Default (PD) is",
        "over a 12-month horizon;",
    ),
    (
        "ead-definition",
        36,
        "CRA: EAD definition",
        "Exposure at Default (EAD) represents",
        "under committed limits); and",
    ),
    (
        "lgd-definition",
        36,
        "CRA: LGD definition",
        "Loss Given Default (LGD) is",
        "percentage of the facility’s EAD.",
    ),
    (
        "cr9-introduction",
        66,
        "cr9-introduction",
        "The table below presents",
        "IRB approach.",
    ),
    ("cr9-ratings", 66, "cr9-ratings", "External Ratings have", "the External Rating."),
    (
        "cr9-history",
        66,
        "cr9-history",
        "The 5-year default rate history",
        "by September 2027.",
    ),
    (
        "cr9-slotting",
        66,
        "cr9-slotting",
        "Excludes Specialised Lending",
        "supervisory slotting.",
    ),
    (
        "cr9-history-exclusions",
        66,
        "cr9-history-exclusions",
        "The historical average default rate calculation",
        "from the denominator.",
    ),
    (
        "cr9-nz-separate",
        69,
        "CR9 separate RBNZ block heading",
        "RBNZ regulated entities",
        "RBNZ regulated entities",
    ),
)


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, "" if page == 1 else str(page), location, row, column
    )


def address(scope, kind, key):
    return OccurrenceRef(BUNDLE, scope, kind, key)


def build():
    physicals, occurrences, contexts, tables, domains = [], [], [], [], []
    comments, targets = {}, {}

    def physical(key, operation, evidence, **parameters):
        binding = PhysicalBinding(
            key + "@1",
            operation,
            tuple(PhysicalParameter(k, v) for k, v in parameters.items()),
            evidence,
        )
        physicals.append(binding)
        return FragmentRef(binding.revision_id, "text")

    def region(key, evidence, box, multiline=False, y_tolerance=3, **params):
        return physical(
            key,
            "region",
            evidence,
            box=tuple(map(str, box)),
            multiline=int(multiline),
            y_tolerance=y_tolerance,
            **params,
        )

    for key, page, location, start, end in PASSAGES:
        params = (
            {"box": ("612", "200", "786", "238")}
            if key == "maturity-modification"
            else {}
        )
        comments[key] = physical(
            key, "passage", ref(page, location), start=start, end=end, **params
        )
    comments["cr9-corporate-history-context"] = region(
        "cr9-corporate-history-context",
        ref(116, "Appendix 1: CR9 column h modification and rationale"),
        (535, 609, 245, 301),
        second_box=("612", "790", "245", "400"),
    )
    for domain, page, specs, edges, markers, label_box in (
        (
            "cr6",
            57,
            CR6,
            (218, 270, 322, 370, 418, 466, 518, 566, 614, 653, 706, 752, 796),
            (63, 66, 325, 430),
            (75, 218),
        ),
        (
            "cr9",
            66,
            CR9,
            (328, 389, 449, 510, 571, 635, 710, 780),
            (68, 70, 280, 390),
            (80, 206),
        ),
    ):
        cr9 = domain == "cr9"
        tid = domain + "-residential-mortgages"
        template = domain.upper()
        title = (
            "CR9: IRB – Back testing of probability of default (PD) per portfolio"
            if cr9
            else "CR6: IRB – Credit risk exposures by portfolio and PD range"
        )
        total = (
            "Sub-Total AIRB Residential\nMortgage"
            if cr9
            else "Sub-Total AIRB Residential Mortgages"
        )
        labels = LABELS + (total,)
        row_ids = tuple(f"band-{i}" for i in range(1, 9)) + ("portfolio-aggregate",)
        common = SHARED + (
            ("cr9-introduction", "cr9-slotting", "cr9-nz-separate")
            if cr9
            else (
                "cr6-introduction",
                "slotting-exclusion",
                "cms2-suncorp-context",
                "nz-separate",
            )
        )
        context = TableContext(
            "context",
            date(2025, 9, 30),
            "" if cr9 else "Sep 25",
            template,
            title,
            "Residential Mortgages",
            Knowledge(
                "ANZ BH Pty Ltd", "established", ("report-entity", "entity-hierarchy")
            ),
            Knowledge("Level 2", "established", ("level-2",)),
            Knowledge(
                "AIRB", "established", (domain + "-introduction", "suncorp-exclusion")
            ),
            Knowledge(
                "Australia",
                "provisional",
                ("cr9-nz-separate" if cr9 else "nz-separate", "suncorp-exclusion"),
            ),
            Knowledge("AUD", "established", ("currency-rounding",)),
            common,
            (
                ref(1, "Cover reporting date"),
                ref(6, "Introduction: entity and perimeter"),
                ref(
                    page,
                    "CR9 headings" if cr9 else "CR6 date, AIRB and portfolio headings",
                ),
            ),
        )
        cid = tid + "/context@1"
        descriptors = (
            (
                TemporalDescriptor(
                    "history",
                    "5-year default rate history",
                    duration_amount=Decimal(5),
                    duration_unit="years",
                    duration_status="established",
                    qualification_refs=CR9[-1][3],
                    evidence=(
                        ref(66, "cr9-history"),
                        ref(66, "cr9-history-exclusions"),
                    ),
                ),
                TemporalDescriptor(
                    "annual",
                    "in the year",
                    evidence=(ref(66, "CR9", column=CR9[4][1]),),
                ),
                TemporalDescriptor(
                    "previous-year",
                    "End of previous year",
                    evidence=(ref(66, "CR9", column=CR9[2][1]),),
                ),
                TemporalDescriptor(
                    "current-year",
                    "End of the year",
                    evidence=(ref(66, "CR9", column=CR9[3][1]),),
                ),
                TemporalDescriptor(
                    "unspecified", "", evidence=(ref(66, "CR9 headings"),)
                ),
            )
            if cr9
            else (
                TemporalDescriptor(
                    "measurement",
                    "Sep 25",
                    point="2025-09-30",
                    point_status="established",
                    evidence=(ref(57, "CR6 date, AIRB and portfolio headings"),),
                ),
            )
        )
        attrs = tuple(
            Assertion(
                k.value,
                k.status,
                evidence_refs=tuple(
                    EvidenceRef(BUNDLE, DOCUMENT, "", "comment", q)
                    for q in k.qualification_refs
                ),
                name=name,
            )
            for name in (
                "reporting_entity",
                "consolidation_scope",
                "regulatory_scope",
                "geography",
                "currency",
            )
            for k in (getattr(context, name),)
        )
        contexts.append(ContextDefinition(cid, attrs, descriptors, context.evidence))
        slot = physical(
            tid + "/title", "passage", ref(page, template), start=title, end=title
        )
        occurrences.append(
            OccurrenceBinding(address(tid, "table", tid), (slot,), (cid,))
        )
        axes, fields, temporal, bands, relationships, notes = [], [], [], [], [], []

        def axis(
            key,
            kind,
            label,
            order,
            parents=(),
            quals=(),
            location=None,
            row=None,
            column=None,
            slot=None,
            *,
            axes=axes,
            page=page,
            template=template,
            tid=tid,
            cid=cid,
        ):
            axes.append(
                SourceAxisItem(
                    key,
                    kind,
                    label,
                    order,
                    parents,
                    ("context",),
                    quals,
                    ref(page, location or template, row, column),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, kind, key), () if slot is None else (slot,), (cid,)
                )
            )

        structures = (
            (
                ("date", "header", "Sep 25", 0, (), (475, 510, 108, 118)),
                ("approach", "header", "AIRB", 1, (), (80, 110, 147, 157)),
                (
                    "pd-heading",
                    "header",
                    "Portfolio/\nPD scale",
                    2,
                    (),
                    (80, 140, 128, 146),
                ),
                (
                    "mortgage-block",
                    "block",
                    "Residential Mortgages",
                    3,
                    ("approach",),
                    (80, 200, 270, 280),
                ),
                (
                    "borrower-counts",
                    "header",
                    "Number of Borrowers",
                    4,
                    ("date",),
                    (449, 571, 119, 128),
                ),
            )
            if cr9
            else (
                ("date", "header", "Sep 25", 0, (), (490, 525, 125, 135)),
                ("approach", "header", "AIRB", 1, (), (75, 115, 190, 200)),
                (
                    "pd-heading",
                    "header",
                    "Portfolio/\nPD scale",
                    2,
                    (),
                    (75, 125, 172, 190),
                ),
                (
                    "mortgage-block",
                    "block",
                    "Residential Mortgages",
                    3,
                    ("approach",),
                    (75, 218, 314, 325),
                ),
            )
        )
        for key, kind, label, order, parents, box in structures:
            axis(
                key,
                kind,
                label,
                order,
                parents,
                slot=region(
                    tid + "/" + key,
                    ref(page, template),
                    box,
                    "\n" in label,
                    1 if cr9 else 3,
                ),
            )
        columns = (
            tuple(s[1] for s in specs)
            if cr9
            else tuple(f"column-{i}" for i in range(1, 13))
        )
        grid_ref = physical(
            tid + "/body",
            "grid",
            ref(page, "CR9" if cr9 else "CR6 Residential Mortgages"),
            edges=tuple(map(str, edges)),
            markers=tuple(map(str, markers)),
            labels=tuple(map(str, label_box)),
            columns=columns,
            multiline_rows=("8",) if cr9 else (),
            y_tolerance=1 if cr9 else 3,
        ).binding_ref
        for j, (key, label, unit, quals) in enumerate(specs):
            column = "column-" + key if cr9 else columns[j]
            parents = ("borrower-counts",) if cr9 and j in (2, 3) else ("date",)
            evidence = ref(
                page, "CR9" if cr9 else "CR6 header", column=label if cr9 else column
            )
            slot = region(
                tid + "/field/" + key,
                evidence,
                (
                    edges[j],
                    edges[j + 1],
                    (129 if j in (2, 3) else 119) if cr9 else 135,
                    146 if cr9 else 170,
                ),
                True,
                1 if cr9 else 3,
            )
            axis(
                column,
                "column",
                label,
                j + 2 if cr9 else j,
                parents,
                quals,
                location="CR9" if cr9 else "CR6 header",
                column=label if cr9 else column,
                slot=slot,
            )
            attributes = ()
            if (cr9 and key == "weighted_average_pd") or (
                not cr9 and key.startswith("average_")
            ):
                attributes = (SemanticAttribute("weighting", None, "unresolved", ()),)
            if cr9 and key == "arithmetic_average_pd":
                attributes = (
                    SemanticAttribute("weighting", "borrowers", "established", ()),
                )
            if key.endswith("count"):
                attributes = (
                    SemanticAttribute(
                        "counted_entity", None, "unresolved", () if cr9 else quals
                    ),
                )
                if not cr9:
                    attributes += (
                        SemanticAttribute("distinctness", None, "unresolved", quals),
                    )
            if key in ("rwa", "rwa_density"):
                attributes = (
                    SemanticAttribute("overlay_treatment", None, "unresolved", quals),
                )
            if key == "average_maturity":
                attributes += (
                    SemanticAttribute(
                        "missing_cell_presentation", "dash", "established", quals
                    ),
                )
            if key == "provisions":
                attributes = (
                    SemanticAttribute(
                        "band_cell_presentation", "blank", "established", ()
                    ),
                )
            fields.append(
                TableField(
                    key,
                    label,
                    parents + (column,),
                    unit,
                    Decimal(1000000 if unit == "$M" else 1),
                    quals,
                    attributes,
                    evidence,
                    "integer" if key.endswith("count") else "decimal",
                    "count"
                    if key.endswith("count")
                    else "money"
                    if unit == "$M"
                    else "scalar",
                )
            )
            occurrences.append(
                OccurrenceBinding(address(tid, "field", key), (slot,), (cid,))
            )
        if cr9:
            rating_ref = physical(
                tid + "/ratings",
                "grid",
                ref(66, "CR9"),
                edges=("206", "267", "328"),
                markers=tuple(map(str, markers)),
                labels=("80", "206"),
                columns=("S&P", "Moody’s"),
                multiline_rows=("8",),
                y_tolerance=1,
            ).binding_ref
            for j, (left, right, agency) in enumerate(
                ((206, 267, "S&P"), (267, 328, "Moody’s"))
            ):
                heading = f"external-ratings-{j}"
                axis(
                    heading,
                    "header",
                    "External rating\nequivalent",
                    j,
                    ("date",),
                    ("cr9-ratings",),
                    slot=region(
                        tid + "/" + heading,
                        ref(66, "CR9"),
                        (left, right, 115, 135),
                        True,
                        1,
                    ),
                )
                slot = region(
                    tid + f"/rating-{j}",
                    ref(66, "CR9", column=agency),
                    (left, right, 147, 157),
                    y_tolerance=1,
                )
                axis(
                    f"rating-{j}",
                    "column",
                    agency,
                    j,
                    (heading,),
                    ("cr9-ratings",),
                    column=agency,
                    slot=slot,
                )
                fields.append(
                    TableField(
                        f"rating-{j}",
                        agency,
                        (heading, f"rating-{j}"),
                        "",
                        Decimal(1),
                        ("cr9-ratings",),
                        (),
                        ref(66, "CR9", column=agency),
                        "text",
                        "text",
                    )
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "field", f"rating-{j}"), (slot,), (cid,)
                    )
                )
        roles = (
            (
                ("weighted_average_pd", "measurement", "unspecified"),
                ("weighted_average_pd", "weight_measurement", "unspecified"),
                ("arithmetic_average_pd", "measurement", "unspecified"),
                ("previous_year_borrower_count", "measurement", "previous-year"),
                ("current_year_borrower_count", "measurement", "current-year"),
                ("defaulted_borrower_count", "outcome_window", "annual"),
                ("defaulted_borrower_count", "cohort_anchor", "unspecified"),
                ("new_defaulted_borrower_count", "outcome_window", "annual"),
                ("historical_annual_default_rate", "history_window", "history"),
            )
            if cr9
            else tuple((s[0], "measurement", "measurement") for s in specs)
        )
        for i, (rid, label) in enumerate(zip(row_ids, labels)):
            source_row = str((11 + i if i < 8 else 20) if cr9 else 10 + i)
            axis(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                location="CR9" if cr9 else "CR6 Residential Mortgages",
                row=source_row,
                slot=FragmentRef(grid_ref, f"row/{i}"),
            )
            if i < 8:
                bands.append(
                    BandDefinition(
                        f"pd-band-{i + 1}",
                        label,
                        i,
                        "default" if i == 7 else "interval",
                        "%",
                        None if i == 7 else Decimal(BOUNDS[i]),
                        None if i == 7 else Decimal(BOUNDS[i + 1]),
                        None if i == 7 else True,
                        None if i == 7 else False,
                        "not_applicable" if i == 7 else "established",
                        "not_applicable" if i == 7 else "established",
                        label if i == 7 else None,
                        ref(
                            page,
                            "CR9" if cr9 else "CR6 Residential Mortgages",
                            row=source_row,
                        ),
                    )
                )
            for j, (key, _, _, quals) in enumerate(specs):
                cell_id = rid + "/" + key
                times = tuple((r, d) for f, r, d in roles if f == key)
                missing = (
                    "not_applicable"
                    if key == "average_maturity"
                    else "not_disclosed_at_this_grain"
                    if key == "provisions" and i < 8
                    else "dash_unresolved"
                    if cr9 and i == 6 and key == "new_defaulted_borrower_count"
                    else "blank_unresolved"
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "cell", cell_id),
                        (FragmentRef(grid_ref, f"{i}/{j}"),),
                        (cid,),
                        temporal_roles=tuple(TemporalRole(r, cid, d) for r, d in times),
                        cell=CellBinding(
                            key,
                            rid,
                            "column-" + key if cr9 else columns[j],
                            () if i == 8 else (f"pd-band-{i + 1}",),
                            quals,
                            "integer" if key.endswith("count") else "decimal",
                            missing,
                            source_row_role=total if i == 8 else "band",
                            source_aggregation_scope=("mortgage-block",),
                        ),
                    )
                )
                domains.append(
                    DomainFieldBinding(
                        address(tid, "cell", cell_id),
                        domain,
                        rid,
                        key,
                        "binding-" + key,
                    )
                )
                temporal.extend(CellTemporalBinding(cell_id, r, d) for r, d in times)
            if cr9:
                for j, agency in enumerate(("S&P", "Moody’s")):
                    slot = FragmentRef(rating_ref, f"{i}/{j}")
                    axis(
                        f"{rid}-rating-{j}",
                        "header",
                        "",
                        j,
                        (rid, f"rating-{j}"),
                        ("cr9-ratings",),
                        row=source_row,
                        column=agency,
                        slot=slot,
                    )
                    occurrences.append(
                        OccurrenceBinding(
                            address(tid, "cell", rid + f"/rating-{j}"),
                            (slot,),
                            (cid,),
                            cell=CellBinding(
                                f"rating-{j}",
                                rid,
                                f"rating-{j}",
                                () if i == 8 else (f"pd-band-{i + 1}",),
                                ("cr9-ratings",),
                                "text",
                                "blank_unresolved" if i == 8 else None,
                                source_row_role=total if i == 8 else "band",
                                source_aggregation_scope=("mortgage-block",),
                            ),
                        )
                    )
                if i != 7:
                    relationships.append(
                        SourceRelationship(
                            "new-defaults-" + rid,
                            "subset",
                            CR9[5][1],
                            SourceEndpoint("field", CR9[4][0]),
                            (SourceEndpoint("field", CR9[5][0]),),
                            (SourceEndpoint("row", rid),),
                            False,
                            None,
                            (ref(66, "CR9", source_row, CR9[5][1]),),
                        )
                    )
        evidence = (
            ref(
                page,
                "CR9 Residential Mortgages PD scale and Sub-Total"
                if cr9
                else "CR6 Residential Mortgages PD scale and Sub-Total",
                row="11–20" if cr9 else "10–18",
            ),
        )
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            "Portfolio/\nPD scale",
            tuple(bands),
            ("context",),
            Knowledge(
                "Displayed PD ranges and default category cover the subtotal",
                "established",
                (domain + "-introduction",),
            ),
            Knowledge(
                "Non-overlapping printed intervals and separate default category",
                "established",
                () if cr9 else ("cr6-introduction",),
            ),
            evidence,
        )
        relationships.append(
            SourceRelationship(
                "mortgage-subtotal",
                "total",
                total,
                SourceEndpoint("row", "portfolio-aggregate"),
                tuple(SourceEndpoint("row", r) for r in row_ids[:-1]),
                (SourceEndpoint("block", "mortgage-block"),),
                True,
                True,
                evidence,
            )
        )
        note_ids = (
            SHARED
            + (
                "pd-definition",
                "cr9-introduction",
                "cr9-ratings",
                "cr9-history",
                "cr9-slotting",
                "cr9-history-exclusions",
                "cr9-corporate-history-context",
                "cr9-nz-separate",
            )
            if cr9
            else tuple(p[0] for p in PASSAGES[:17])
        )
        for q in note_ids:
            scope = tuple(
                SourceEndpoint("field", key) for key, _, _, qs in specs if q in qs
            ) or (SourceEndpoint("dataset", tid),)
            slot = comments[q]
            source = next(
                p.source_reference
                for p in physicals
                if p.revision_id == slot.binding_ref
            )
            notes.append(Qualification(q, "", (source,), scope))
            targets.setdefault(q, []).extend(
                address(tid, "table" if e.kind == "dataset" else e.kind, e.id)
                for e in scope
            )
        tables.append(
            SourceTable(
                tid,
                SourceTableMetadata(
                    context,
                    tuple(axes),
                    tuple(fields),
                    (segmentation,),
                    tuple(notes),
                    tuple(relationships),
                    descriptors,
                    tuple(temporal),
                ),
                (),
            )
        )
    for q, refs in targets.items():
        occurrences.append(
            OccurrenceBinding(
                address(None, "comment", q),
                (comments[q],),
                links=tuple(OccurrenceLink("qualifies", r) for r in refs),
            )
        )
    document = SourceDocument(
        DOCUMENT,
        f"raw/{DOCUMENT}.pdf",
        "anz",
        "ANZ BH Pty Ltd",
        "2025 Basel III Pillar 3 Disclosure As at 30 September 2025 APS 330: Public Disclosure",
        date(2025, 9, 30),
        date(2025, 11, 10),
        "au",
        "https://www.anz.com/content/dam/anzcom/shareholder/full-year-results-announcement/2025-september-pillar-3-disclosure.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        f"extractions/{BUNDLE}/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "anz-2025-capture@1",
            tuple(physicals),
            tuple(contexts),
            tuple(occurrences),
            domain_bindings=tuple(domains),
        ),
    )


DEFINITION = run_path(str(Path(__file__).with_name("adjustments.py")))["extend"](build())
