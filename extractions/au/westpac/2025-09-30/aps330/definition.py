"""Westpac September 2025 selected mortgage declarations and source-backed timing."""

import itertools
from datetime import date
from decimal import Decimal

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

DOCUMENT = "westpac-2025-09-30-aps330"
BUNDLE = "au/westpac/2025-09-30/aps330"
BOUNDS = ("0.00", "0.15", "0.25", "0.50", "0.75", "2.50", "10.00", "100.00")
LABELS = tuple(f"{a} to <{b}" for a, b in itertools.pairwise(BOUNDS)) + (
    "100.00 (Default)",
)
CR6 = (
    (
        "on_balance_exposure",
        "Original on-\nbalance sheet\ngross\nexposure",
        "$m",
        ("on-balance-definition",),
    ),
    (
        "off_balance_exposure",
        "Off-balance\nsheet\nexposure pre\nCCF",
        "$m",
        ("off-balance-definition",),
    ),
    ("average_ccf", "Average CCF\n(%)", "%", ("ccf-definition",)),
    ("ead", "EAD post\nCRM and\npost-CCF", "$m", ("ead-definition",)),
    ("average_pd", "Average PD\n(%)", "%", ("pd-definition", "pd-long-run")),
    ("reported_borrower_count", "Number of\nborrowers", "", ()),
    ("average_lgd", "Average LGD\n(%)", "%", ("lgd-downturn",)),
    ("average_maturity", "Average\nmaturity\n(years)", "years", ()),
    ("rwa", "RWA", "$m", ()),
    ("rwa_density", "RWA density\n(%)a", "%", ("density-rounding",)),
    ("regulatory_expected_loss", "EL", "$m", ("el-definition",)),
    ("provisions", "Provisions", "$m", ("provision-definition",)),
)
CR9 = (
    (
        "weighted_average_pd",
        "Weighted\naverage PDb",
        "%",
        ("pd-definition", "pd-long-run", "cr9-weighting"),
    ),
    (
        "arithmetic_average_pd",
        "Arithmetic\naverage PD\nby borrowers",
        "%",
        ("pd-definition", "pd-long-run"),
    ),
    ("previous_year_borrower_count", "End of\nprevious year", "", ()),
    ("current_year_borrower_count", "End of the year", "", ()),
    (
        "defaulted_borrower_count",
        "Non-performing\nborrowers in\nthe yearc",
        "",
        ("default-definition", "cr9-defaults"),
    ),
    (
        "new_defaulted_borrower_count",
        "of which: new\nNon-performing\nborrowers in\nthe year",
        "",
        ("default-definition", "cr9-defaults"),
    ),
    (
        "historical_annual_default_rate",
        "Average\nhistorical annual\ndefault rated",
        "%",
        ("cr9-history",),
    ),
)
SHARED = (
    "report-entity",
    "currency",
    "rounding",
    "regulatory-basis",
    "level-2-definition",
    "level-2",
    "portfolio-definition",
)
PASSAGES = (
    (
        "report-entity",
        2,
        "Report conventions",
        "In this report references",
        "just Westpac Banking Corporation.",
        0,
    ),
    (
        "currency",
        2,
        "Report conventions",
        "In this report, unless otherwise stated or the context",
        "are to Australian dollars.",
        0,
    ),
    (
        "rounding",
        2,
        "Report conventions",
        "Any discrepancies between totals",
        "are due to rounding.",
        0,
    ),
    (
        "regulatory-basis",
        2,
        "Report conventions",
        "In this report, unless otherwise stated, disclosures",
        "implementation of Basel III.",
        0,
    ),
    (
        "level-2-definition",
        8,
        "Group Structure",
        "Level 2, the consolidation",
        "Westpac Banking Corporation; and",
        0,
    ),
    (
        "level-2",
        8,
        "Group Structure",
        "Unless otherwise specified, all quantitative",
        "on a Level 2 basis2.",
        0,
    ),
    (
        "portfolio-definition",
        33,
        "CRA: Residential Mortgages",
        "Residential Mortgages asset class covers",
        "internally-modelled Retail IRB approach).",
        164,
    ),
    (
        "cr6-introduction",
        48,
        "CR6 A-IRB introduction",
        "The following table provides the key parameters",
        "APRA supervisory estimates for EAD).",
        0,
    ),
    (
        "density-rounding",
        49,
        "CR6 footnote a",
        "RWA density is calculated",
        "based on unrounded numbers.",
        0,
    ),
    (
        "pd-definition",
        98,
        "Glossary: Probability of default (PD)",
        "Probability of default is a through-the-cycle",
        "obligations within one year.",
        133,
    ),
    (
        "pd-long-run",
        47,
        "CRE: Program-managed approach",
        "PD models are calibrated",
        "long-run average default risk.",
        0,
    ),
    (
        "lgd-downturn",
        47,
        "CRE: Program-managed approach",
        "LGD estimates are",
        "during a downturn period.",
        0,
    ),
    (
        "ccf-definition",
        98,
        "Glossary: Credit conversion factor (CCF)",
        "Represents the proportion of undrawn limit",
        "when a facility enters default.",
        133,
    ),
    (
        "ead-definition",
        98,
        "Glossary: Exposure at default (EAD)",
        "EAD is calculated at facility level",
        "in the event of a future default.",
        133,
    ),
    (
        "on-balance-definition",
        98,
        "Glossary: On-balance sheet exposure",
        "Credit exposures arising from facilities that are recorded",
        "accounting methodology).",
        133,
    ),
    (
        "off-balance-definition",
        98,
        "Glossary: Off-balance sheet exposure",
        "Credit exposures arising from facilities that are not recorded",
        "included in off-balance sheet exposure.",
        133,
    ),
    (
        "default-definition",
        34,
        "CRB: Non-performing exposures",
        "Default occurs",
        "on a credit obligation to Westpac.",
        0,
    ),
    (
        "el-definition",
        97,
        "Appendix III footnote b",
        "Regulatory expected loss is calculated",
        "for defaulted and non-defaulted exposures.",
        0,
    ),
    (
        "provision-definition",
        44,
        "CRE: Provisioning",
        "Credit provisions are held by Westpac",
        "present value of future cashflows.",
        0,
    ),
    (
        "cr9-introduction",
        55,
        "cr9-introduction",
        "The following table provides a comparison",
        "for all portfolio types.",
        0,
    ),
    (
        "cr9-weighting",
        56,
        "cr9-weighting",
        "Observation point is June 2024",
        "is as at June 2024.",
        0,
    ),
    (
        "cr9-defaults",
        56,
        "cr9-defaults",
        "Defaulted borrowers in the year include:",
        "(new defaulted borrowers).",
        0,
    ),
    (
        "cr9-history",
        56,
        "cr9-history",
        "Average historical default rate is calculated",
        "over 10 years.",
        0,
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

    def region(key, evidence, box, multiline=False, y_tolerance=3):
        return physical(
            key,
            "region",
            evidence,
            box=tuple(map(str, box)),
            multiline=int(multiline),
            y_tolerance=y_tolerance,
        )

    for key, page, location, start, end, left in PASSAGES:
        comments[key] = physical(
            key, "passage", ref(page, location), start=start, end=end, left=left
        )
    for domain, page, specs, edges, markers, label_box in (
        (
            "cr6",
            48,
            CR6,
            (190, 245, 295, 345, 395, 445, 493, 542, 590, 640, 689, 738, 787),
            (114, 115, 398, 474),
            (114, 185),
        ),
        (
            "cr9",
            55,
            CR9,
            (400, 455, 515, 577, 636, 699, 754, 815),
            (135, 136, 270, 347),
            (130, 260),
        ),
    ):
        cr9 = domain == "cr9"
        tid = domain + "-residential-mortgages"
        template = domain.upper()
        title = (
            "CR9: IRB - Backtesting of probability of default (PD) per portfolio"
            if cr9
            else "CR6: IRB - Credit risk exposures by portfolio and PD ranges"
        )
        common = SHARED + (domain + "-introduction",)
        labels = LABELS if cr9 else LABELS + ("Total Residential Mortgages",)
        row_ids = tuple(f"band-{i}" for i in range(1, 9)) + (
            () if cr9 else ("portfolio-aggregate",)
        )
        context = TableContext(
            "context",
            date(2025, 9, 30),
            "" if cr9 else "As at 30 September 2025",
            template,
            title,
            "Residential\nMortgages",
            Knowledge(
                "Westpac Banking Corporation and its subsidiaries",
                "established",
                ("report-entity",),
            ),
            Knowledge("Level 2", "established", ("level-2-definition", "level-2")),
            Knowledge(
                "A-IRB", "established", ("regulatory-basis", domain + "-introduction")
            ),
            Knowledge(),
            Knowledge("AUD", "established", ("currency",)),
            common,
            (
                ref(1, "Cover"),
                ref(
                    page,
                    "CR9 headings"
                    if cr9
                    else "CR6 date, approach and portfolio headings",
                ),
            ),
        )
        cid = tid + "/context@1"
        descriptors = (
            (
                TemporalDescriptor(
                    "pd-measurement",
                    "June 2024",
                    point="2024-06",
                    point_status="established",
                    qualification_refs=("cr9-weighting",),
                    evidence=(ref(56, "cr9-weighting"),),
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
                    evidence=(ref(55, "cr9-introduction"), ref(56, "cr9-defaults")),
                ),
                TemporalDescriptor(
                    "history",
                    "10 years",
                    duration_amount=Decimal(10),
                    duration_unit="years",
                    duration_status="established",
                    qualification_refs=("cr9-history",),
                    evidence=(ref(56, "cr9-history"),),
                ),
                TemporalDescriptor(
                    "previous-year",
                    "End of previous year",
                    point="2024-06-30",
                    point_status="established",
                    qualification_refs=("cr9-introduction",),
                    evidence=(
                        ref(55, "cr9-introduction"),
                        ref(55, "CR9", column=CR9[2][1]),
                    ),
                ),
                TemporalDescriptor(
                    "current-year",
                    "End of the year",
                    point="2025-06-30",
                    point_status="established",
                    qualification_refs=("cr9-introduction",),
                    evidence=(
                        ref(55, "cr9-introduction"),
                        ref(55, "CR9", column=CR9[3][1]),
                    ),
                ),
                TemporalDescriptor(
                    "unspecified", "", evidence=(ref(55, "CR9 headings"),)
                ),
            )
            if cr9
            else (
                TemporalDescriptor(
                    "measurement",
                    "As at 30 September 2025",
                    point="2025-09-30",
                    point_status="established",
                    evidence=(ref(48, "CR6 date, approach and portfolio headings"),),
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
                ("approach", "header", "A-IRB", 0, (), (55, 100, 154, 163)),
                ("pd-heading", "header", "PD Range", 1, (), (130, 200, 184, 193)),
                (
                    "mortgage-block",
                    "block",
                    "Residential\nMortgages",
                    2,
                    ("approach",),
                    (65, 125, 300, 318),
                ),
                (
                    "external-ratings",
                    "header",
                    "External rating equivalent",
                    3,
                    (),
                    (280, 400, 163, 171),
                ),
                (
                    "borrower-counts",
                    "header",
                    "Number of borrowers",
                    4,
                    (),
                    (530, 635, 163, 171),
                ),
            )
            if cr9
            else (
                (
                    "date",
                    "header",
                    "As at 30 September 2025",
                    0,
                    (),
                    (30, 150, 201, 208),
                ),
                ("approach", "header", "A-IRB", 1, (), (30, 90, 194, 201)),
                ("monetary-unit", "header", "$m", 2, (), (30, 90, 215, 223)),
                ("pd-heading", "header", "PD scale", 3, (), (114, 185, 215, 223)),
                (
                    "mortgage-block",
                    "block",
                    "Residential\nMortgages",
                    4,
                    ("approach",),
                    (30, 110, 428, 445),
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
        tail = (
            {}
            if cr9
            else {
                "last_marker": ("30", "32", "474", "484"),
                "last_prefix": "Total",
                "last_labels": ("30", "190"),
            }
        )
        grid_ref = physical(
            tid + "/body",
            "grid",
            ref(page, "CR9" if cr9 else "CR6 Residential Mortgages"),
            edges=tuple(map(str, edges)),
            markers=tuple(map(str, markers)),
            labels=tuple(map(str, label_box)),
            columns=tuple(s[1] for s in specs),
            y_tolerance=1 if cr9 else 3,
            **tail,
        ).binding_ref
        for j, (key, label, unit, quals) in enumerate(specs):
            column = "column-" + key
            parents = (
                (("borrower-counts",) if j in (2, 3) else ()) if cr9 else ("date",)
            )
            evidence = ref(page, "CR9" if cr9 else "CR6 header", column=label)
            slot = region(
                tid + "/field/" + key,
                evidence,
                (
                    edges[j],
                    edges[j + 1],
                    (175, 166, 173, 173, 166, 163, 166)[j] if cr9 else 194,
                    193 if cr9 else 223,
                ),
                True,
                1 if cr9 else 3,
            )
            axis(
                column,
                "column",
                label,
                j,
                parents,
                quals,
                location="CR9" if cr9 else "CR6 header",
                column=label,
                slot=slot,
            )
            attributes = ()
            if cr9 and key == "weighted_average_pd":
                attributes = (
                    SemanticAttribute(
                        "weighting", "EAD", "established", ("cr9-weighting",)
                    ),
                )
            elif cr9 and key == "arithmetic_average_pd":
                attributes = (
                    SemanticAttribute("weighting", "borrowers", "established", ()),
                )
            elif not cr9 and key.startswith("average_"):
                attributes = (SemanticAttribute("weighting", None, "unresolved", ()),)
            if key.endswith("count"):
                attributes = (
                    SemanticAttribute("counted_entity", None, "unresolved", ()),
                )
            path = parents + (column,) + (("monetary-unit",) if unit == "$m" else ())
            fields.append(
                TableField(
                    key,
                    label,
                    path,
                    unit,
                    Decimal(1000000 if unit == "$m" else 1),
                    quals,
                    attributes,
                    evidence,
                    "integer" if key.endswith("count") else "decimal",
                    "count"
                    if key.endswith("count")
                    else "money"
                    if unit == "$m"
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
                ref(55, "CR9"),
                edges=("260", "330", "400"),
                markers=tuple(map(str, markers)),
                labels=("130", "260"),
                columns=("Moody's", "S&P"),
                y_tolerance=1,
            ).binding_ref
            for j, agency in enumerate(("Moody's", "S&P")):
                slot = region(
                    tid + f"/rating-{j}",
                    ref(55, "CR9", column=agency),
                    ((290, 365)[j], (330, 400)[j], 184, 193),
                    y_tolerance=1,
                )
                axis(
                    f"rating-{j}",
                    "column",
                    agency,
                    j,
                    ("external-ratings",),
                    column=agency,
                    slot=slot,
                )
                fields.append(
                    TableField(
                        f"rating-{j}",
                        agency,
                        ("external-ratings", f"rating-{j}"),
                        "",
                        Decimal(1),
                        (),
                        (),
                        ref(55, "CR9", column=agency),
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
                ("weighted_average_pd", "measurement", "pd-measurement"),
                ("weighted_average_pd", "weight_measurement", "pd-measurement"),
                ("arithmetic_average_pd", "measurement", "unspecified"),
                ("previous_year_borrower_count", "measurement", "previous-year"),
                ("current_year_borrower_count", "measurement", "current-year"),
                ("defaulted_borrower_count", "outcome_window", "annual"),
                ("new_defaulted_borrower_count", "outcome_window", "annual"),
                ("historical_annual_default_rate", "history_window", "history"),
            )
            if cr9
            else tuple((s[0], "measurement", "measurement") for s in specs)
        )
        for i, (rid, label) in enumerate(zip(row_ids, labels)):
            axis(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                ("default-definition",) if i == 7 else (),
                location="CR9" if cr9 else "CR6 Residential Mortgages",
                row=label,
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
                            row=label,
                        ),
                    )
                )
            for j, (key, _, _, quals) in enumerate(specs):
                cell_id = rid + "/" + key
                cell_quals = quals + (
                    ("default-definition",)
                    if i == 7 and "default-definition" not in quals
                    else ()
                )
                times = tuple((r, d) for f, r, d in roles if f == key)
                missing = (
                    "not_disclosed_at_this_grain"
                    if key == "provisions" and i < 8
                    else "dash_unresolved"
                    if (cr9 and i == 6 and key == "new_defaulted_borrower_count")
                    or (not cr9 and i == 7 and key == "average_ccf")
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
                            "column-" + key,
                            () if i == 8 else (f"pd-band-{i + 1}",),
                            cell_quals,
                            "integer" if key.endswith("count") else "decimal",
                            missing,
                            source_row_role="Total Residential Mortgages"
                            if i == 8
                            else "band",
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
                for j, agency in enumerate(("Moody's", "S&P")):
                    slot = FragmentRef(rating_ref, f"{i}/{j}")
                    axis(
                        f"{rid}-rating-{j}",
                        "header",
                        "",
                        j,
                        (rid, f"rating-{j}"),
                        row=label,
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
                                (f"pd-band-{i + 1}",),
                                (),
                                "text",
                                "blank_unresolved" if i == 7 else None,
                                source_row_role="band",
                                source_aggregation_scope=("mortgage-block",),
                            ),
                        )
                    )
                if i < 7:
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
                            (ref(55, "CR9", label, CR9[5][1]), ref(56, "cr9-defaults")),
                        )
                    )
        evidence = (
            ref(
                page,
                "CR9 PD Range"
                if cr9
                else "CR6 Residential Mortgages PD scale and Total",
            ),
        )
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            "PD Range" if cr9 else "PD scale",
            tuple(bands),
            ("context",),
            Knowledge()
            if cr9
            else Knowledge(
                "Displayed PD ranges and default category cover the total",
                "established",
                ("cr6-introduction",),
            ),
            Knowledge(
                "Non-overlapping printed intervals and separate default category",
                "established",
                () if cr9 else ("cr6-introduction",),
            ),
            evidence,
        )
        if not cr9:
            relationships.append(
                SourceRelationship(
                    "mortgage-total",
                    "total",
                    "Total Residential Mortgages",
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
            + ("pd-definition", "pd-long-run", "default-definition")
            + tuple(p[0] for p in PASSAGES[19:])
            if cr9
            else tuple(p[0] for p in PASSAGES[:19])
        )
        for q in note_ids:
            scope = tuple(
                SourceEndpoint("field", key) for key, _, _, qs in specs if q in qs
            ) or (SourceEndpoint("dataset", tid),)
            if q == "default-definition":
                scope = (SourceEndpoint("row", "band-8"),) + (
                    (
                        SourceEndpoint("field", CR9[4][0]),
                        SourceEndpoint("field", CR9[5][0]),
                    )
                    if cr9
                    else ()
                )
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
        "westpac",
        "WESTPAC BANKING CORPORATION",
        "PILLAR 3 REPORT WESTPAC SEPTEMBER 2025 INCORPORATING THE REQUIREMENTS OF APS 330",
        date(2025, 9, 30),
        date(2025, 11, 3),
        "au",
        "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-September-2025-Pillar-3-Report-2025.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        f"extractions/{BUNDLE}/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "westpac-2025-capture@1",
            tuple(physicals),
            tuple(contexts),
            tuple(occurrences),
            domain_bindings=tuple(domains),
        ),
    )


DEFINITION = build()
