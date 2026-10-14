"""Reviewed CBA June 2025 mortgage selection, physical bindings and source context.

The ordinary Python loops expand the two reviewed grids. Financial interpretations
remain in the catalogue; passages are captured from their declared PDF locations.
"""

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

DOCUMENT = "cba-2025-06-30-aps330"
BUNDLE = "au/cba/2025-06-30/aps330"
BOUNDS = ("0.00", "0.15", "0.25", "0.50", "0.75", "2.50", "10.00", "100.00")
LABELS = tuple(f"{a} to <{b}" for a, b in itertools.pairwise(BOUNDS)) + (
    "100.00 (Default)",
)
CR6 = (
    ("on_balance_exposure", "Original\non-balance\nsheet\ngross\nexposure", "$M", ()),
    ("off_balance_exposure", "Off-\nbalance\nsheet\nexposures\npre CCF", "$M", ()),
    ("average_ccf", "Average\nCCF", "%", ("ccf-definition",)),
    ("ead", "EAD post\nCRM and\npost-CCF", "$M", ("ead-definition", "ccf-definition")),
    (
        "average_pd",
        "Average\nPD ¹",
        "%",
        ("pd-weighting", "pd-definition", "pd-long-run"),
    ),
    ("reported_borrower_count", "Number\nof\nborrowers", "", ()),
    ("average_lgd", "Average\nLGD", "%", ("lgd-definition", "lgd-downturn")),
    ("average_maturity", "Average\nmaturity", "Years", ()),
    ("rwa", "RWA ²", "$M", ("rwa-overlays",)),
    ("rwa_density", "RWA\ndensity ³", "%", ("density-rounding",)),
    (
        "regulatory_expected_loss",
        "Expected\nLoss",
        "$M",
        ("el-performing", "el-default"),
    ),
    ("provisions", "Provisions", "$M", ()),
)
CR9 = (
    (
        "weighted_average_pd",
        "Weighted\naverage\nPD",
        "%",
        ("pd-definition", "pd-long-run"),
    ),
    (
        "arithmetic_average_pd",
        "Arithmetic\naverage\nPD by\nborrowers",
        "%",
        ("pd-definition", "pd-long-run"),
    ),
    ("previous_year_borrower_count", "End of\nprevious\nyear", "#", ()),
    ("current_year_borrower_count", "End of the\nyear", "#", ()),
    (
        "defaulted_borrower_count",
        "Non-\nperforming\nborrowers\nin the year",
        "#",
        ("non-performing-definition", "retail-non-performing"),
    ),
    (
        "new_defaulted_borrower_count",
        "of which:\nnew non-\nperforming\nborrowers\nin the year",
        "#",
        ("non-performing-definition", "retail-non-performing"),
    ),
    (
        "historical_annual_default_rate",
        "Average\nhistorical\nannual\ndefault\nrate ²",
        "%",
        ("cr9-history",),
    ),
)
# Page, source location, inclusive prose anchors. Shared passages have one binding.
PASSAGES = (
    (
        "report-entity",
        6,
        "Introduction",
        "This document is prepared",
        "1 January 2025.",
    ),
    (
        "level-2",
        115,
        "Glossary: Level 2",
        "The level at which the Group reports",
        "this report has been produced.",
    ),
    (
        "portfolio-definition",
        116,
        "Glossary: Residential Mortgage",
        "Basel asset class – retail exposures secured",
        "residential mortgage property.",
    ),
    (
        "cr6-introduction",
        54,
        "CR6 introduction",
        "The table below shows the detailed",
        "asset class and PD range.",
    ),
    (
        "pd-definition",
        50,
        "Probability of Default (PD)",
        "The PD, expressed as a percentage,",
        "within a one year period.",
    ),
    (
        "pd-long-run",
        50,
        "Probability of Default (PD)",
        "PD estimates are based on a long-run",
        "external data where applicable.",
    ),
    (
        "lgd-definition",
        52,
        "Loss Given Default (LGD)",
        "LGD is estimated as the net present value",
        "percentage of the EAD.",
    ),
    (
        "lgd-downturn",
        52,
        "Loss Given Default (LGD)",
        "For calculating regulatory capital",
        "under stressed economic conditions.",
    ),
    (
        "ead-definition",
        52,
        "Exposure at Default (EAD)",
        "EAD is the estimate of the amount",
        "it is the actual amount outstanding.",
    ),
    (
        "ccf-definition",
        52,
        "Exposure at Default (EAD)",
        "EAD for loans and commitments",
        "as a facility enters default.",
    ),
    (
        "el-performing",
        52,
        "Expected Loss (EL)",
        "Regulatory EL is a hybrid",
        "EAD for non-defaulted exposures.",
    ),
    (
        "el-default",
        52,
        "Expected Loss (EL): defaulted exposures",
        "the Best Estimate of Expected Loss (BEEL)",
        "defaulted exposure; and",
    ),
    (
        "cr9-introduction",
        60,
        "cr9-introduction",
        "The table below provides a comparison",
        "RWA overlays and risk floors.",
    ),
    (
        "cr9-bands",
        60,
        "cr9-bands",
        "The Group’s internal PD grades",
        "sitting within the range.",
    ),
    (
        "cr9-history",
        60,
        "cr9-history",
        "The average historical default rate",
        "regulatory standards at the time.",
    ),
    (
        "non-performing-definition",
        116,
        "non-performing-definition",
        "An exposure that is in default.",
        "An exposure that is in default.",
    ),
    (
        "retail-non-performing",
        51,
        "retail-non-performing",
        "Retail exposures are classified as non-performing",
        "against the facility).",
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
    comment_slots, comment_targets = {}, {}

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

    for key, page, location, start, end in PASSAGES:
        comment_slots[key] = physical(
            key, "passage", ref(page, location), start=start, end=end
        )
    for key, number, top, bottom in (
        ("pd-weighting", 1, 507, 515),
        ("rwa-overlays", 2, 516, 524),
        ("density-rounding", 3, 524, 533),
    ):
        comment_slots[key] = region(
            key, ref(55, f"CR6 footnote {number}"), (80, 500, top, bottom)
        )

    shared = ("report-entity", "level-2", "portfolio-definition")
    for domain, page, specs, edges, markers, labels_box, height in (
        (
            "cr6",
            55,
            CR6,
            (232, 280, 325, 370, 416, 458, 506, 550, 595, 638, 682, 724, 770),
            (167, 169, 170, 278),
            (165, 230),
            8,
        ),
        (
            "cr9",
            60,
            CR9,
            (400, 450, 506, 560, 617, 673, 730, 777),
            (199, 201, 365, 440),
            (195, 275),
            7,
        ),
    ):
        cr9 = domain == "cr9"
        tid = domain + "-residential-mortgages"
        template = domain.upper()
        title = (
            "CR9: IRB - Backtesting of probability of default (PD) per portfolio"
            if cr9
            else "CR6: IRB – Credit risk exposures by portfolio and PD range"
        )
        labels = LABELS if cr9 else LABELS + ("Sub-total",)
        row_ids = tuple(f"band-{i}" for i in range(1, 9)) + (
            () if cr9 else ("portfolio-aggregate",)
        )
        common = shared + (
            ("cr9-introduction", "cr9-bands") if cr9 else ("cr6-introduction",)
        )
        context = TableContext(
            "context",
            date(2025, 6, 30),
            "" if cr9 else "30 June 2025",
            template,
            title,
            "Residential mortgage",
            Knowledge(
                "CBA and its subsidiaries (the Group)",
                "established",
                ("report-entity",),
            ),
            Knowledge("Level 2", "established", ("level-2",)),
            Knowledge(
                "Subject to AIRB approach", "established", (domain + "-introduction",)
            ),
            Knowledge(),
            Knowledge(),
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
        context_id = tid + "/context@1"
        descriptors = (
            (
                TemporalDescriptor(
                    "annual",
                    "1 April 2024 to 31 March 2025",
                    start="2024-04-01",
                    end="2025-03-31",
                    start_status="established",
                    end_status="established",
                    duration_amount=Decimal(12),
                    duration_unit="months",
                    duration_status="established",
                    qualification_refs=("cr9-introduction",),
                    evidence=(ref(60, "cr9-introduction"),),
                ),
                TemporalDescriptor(
                    "history",
                    "from 2014",
                    start="2014",
                    start_status="established",
                    qualification_refs=("cr9-history",),
                    evidence=(ref(60, "cr9-history"),),
                ),
                TemporalDescriptor(
                    "previous-year",
                    "End of previous year",
                    point="2024-03-31",
                    point_status="established",
                    qualification_refs=("cr9-introduction",),
                    evidence=(
                        ref(60, "cr9-introduction"),
                        ref(60, "CR9", column=CR9[2][1]),
                    ),
                ),
                TemporalDescriptor(
                    "current-year",
                    "End of the year",
                    point="2025-03-31",
                    point_status="established",
                    qualification_refs=("cr9-introduction",),
                    evidence=(
                        ref(60, "cr9-introduction"),
                        ref(60, "CR9", column=CR9[3][1]),
                    ),
                ),
                TemporalDescriptor(
                    "unspecified", "", evidence=(ref(60, "CR9 headings"),)
                ),
            )
            if cr9
            else (
                TemporalDescriptor(
                    "measurement",
                    "30 June 2025",
                    point="2025-06-30",
                    point_status="established",
                    evidence=(ref(55, "CR6 date, approach and portfolio headings"),),
                ),
            )
        )
        attributes = tuple(
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
        contexts.append(
            ContextDefinition(context_id, attributes, descriptors, context.evidence)
        )
        title_slot = physical(
            tid + "/title", "passage", ref(page, template), start=title, end=title
        )
        occurrences.append(
            OccurrenceBinding(address(tid, "table", tid), (title_slot,), (context_id,))
        )
        axes, fields, temporal, notes, relationships, bands = [], [], [], [], [], []

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
            context_id=context_id,
        ):
            evidence = ref(page, location or template, row, column)
            axes.append(
                SourceAxisItem(
                    key, kind, label, order, parents, ("context",), quals, evidence
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, kind, key),
                    () if slot is None else (slot,),
                    (context_id,),
                    links=tuple(
                        OccurrenceLink(
                            "header",
                            address(tid, next(a.axis for a in axes if a.id == p), p),
                        )
                        for p in parents
                    ),
                )
            )

        if cr9:
            structural = (
                (
                    "approach",
                    "header",
                    "Subject to AIRB approach",
                    0,
                    (),
                    (75, 195, 148, 160),
                ),
                (
                    "portfolio-heading",
                    "header",
                    "Portfolio Type",
                    1,
                    (),
                    (75, 160, 176, 185),
                ),
                ("pd-heading", "header", "PD Range ¹", 2, (), (195, 260, 176, 185)),
                (
                    "mortgage-block",
                    "block",
                    "Residential mortgage",
                    3,
                    ("approach", "portfolio-heading"),
                    (75, 190, 365, 375),
                ),
                (
                    "borrower-counts",
                    "header",
                    "Number of borrowers",
                    4,
                    (),
                    (510, 617, 125, 132),
                ),
            )
        else:
            structural = (
                ("date", "header", "30 June 2025", 0, (), (460, 530, 94, 103)),
                (
                    "approach",
                    "header",
                    "Subject to AIRB approach",
                    1,
                    (),
                    (65, 170, 124, 135),
                ),
                (
                    "portfolio-heading",
                    "header",
                    "Portfolio Type",
                    2,
                    (),
                    (65, 120, 157, 167),
                ),
                ("pd-heading", "header", "PD Range", 3, (), (165, 225, 157, 167)),
                (
                    "mortgage-block",
                    "block",
                    "Residential mortgage",
                    4,
                    ("approach", "portfolio-heading"),
                    (65, 155, 170, 180),
                ),
            )
        for key, kind, label, order, parents, box in structural:
            slot = region(
                tid + "/" + key, ref(page, template), box, y_tolerance=1 if cr9 else 3
            )
            axis(
                key,
                kind,
                label,
                order,
                parents,
                ("cr9-bands",) if cr9 and key == "pd-heading" else (),
                slot=slot,
            )
        grid_ref = physical(
            tid + "/body",
            "grid",
            ref(page, "CR9" if cr9 else "CR6 Residential mortgage"),
            markers=tuple(map(str, markers)),
            edges=tuple(map(str, edges)),
            labels=tuple(map(str, labels_box)),
            columns=tuple(s[1] for s in specs),
            height=height,
            y_tolerance=1 if cr9 else 3,
        ).binding_ref
        field_slots = {}
        for j, (key, label, unit, quals) in enumerate(specs):
            parents = (
                (("borrower-counts",) if j in (2, 3) else ()) if cr9 else ("date",)
            )
            evidence = ref(page, "CR9" if cr9 else "CR6 header", column=label)
            slot = region(
                tid + "/field/" + key,
                evidence,
                (edges[j], edges[j + 1], 132 if cr9 else 110, 173 if cr9 else 154),
                True,
                1 if cr9 else 3,
            )
            field_slots[key] = slot
            axis(
                "column-" + key,
                "column",
                label,
                j + 2 if cr9 else j,
                parents,
                quals,
                location="CR9" if cr9 else "CR6 header",
                column=label,
                slot=slot,
            )
            attrs = ()
            if cr9:
                if key == "weighted_average_pd":
                    attrs = (SemanticAttribute("weighting", None, "unresolved", ()),)
                elif key == "arithmetic_average_pd":
                    attrs = (
                        SemanticAttribute("weighting", "borrowers", "established", ()),
                        SemanticAttribute("counted_entity", None, "unresolved", ()),
                    )
                elif key.endswith("count"):
                    attrs = (
                        SemanticAttribute("counted_entity", None, "unresolved", ()),
                    )
            elif key.startswith("average_"):
                attrs = (
                    SemanticAttribute(
                        "weighting",
                        "EAD at the end of the period" if key == "average_pd" else None,
                        "established" if key == "average_pd" else "unresolved",
                        ("pd-weighting",) if key == "average_pd" else (),
                    ),
                )
            elif key == "reported_borrower_count":
                attrs = (SemanticAttribute("counted_entity", None, "unresolved", ()),)
            count = key.endswith("count")
            fields.append(
                TableField(
                    key,
                    label,
                    parents + ("column-" + key,),
                    unit,
                    Decimal(1000000 if unit == "$M" else 1),
                    quals,
                    attrs,
                    evidence,
                    "integer" if count else "decimal",
                    "count" if count else "money" if unit == "$M" else "scalar",
                )
            )
            occurrences.append(
                OccurrenceBinding(address(tid, "field", key), (slot,), (context_id,))
            )
        if cr9:
            rating_ref = physical(
                tid + "/ratings",
                "grid",
                ref(60, "CR9"),
                markers=tuple(map(str, markers)),
                edges=("275", "340", "400"),
                labels=("195", "275"),
                columns=("S&P", "Moodys"),
                height=7,
                y_tolerance=1,
            ).binding_ref
            for j, (left, right, agency) in enumerate(
                ((275, 340, "S&P"), (340, 400, "Moodys"))
            ):
                header_slot = region(
                    tid + f"/external-rating-{j}",
                    ref(60, "CR9"),
                    (left, right, 148, 173),
                    True,
                    1,
                )
                axis(
                    f"external-rating-{j}",
                    "header",
                    "External\nrating\nequivalent",
                    j,
                    slot=header_slot,
                )
                slot = region(
                    tid + f"/rating-{j}",
                    ref(60, "CR9", column=agency),
                    (left, right, 176, 185),
                    y_tolerance=1,
                )
                axis(
                    f"rating-{j}",
                    "column",
                    agency,
                    j,
                    (f"external-rating-{j}",),
                    column=agency,
                    slot=slot,
                )
                fields.append(
                    TableField(
                        f"rating-{j}",
                        agency,
                        (f"external-rating-{j}", f"rating-{j}"),
                        "",
                        Decimal(1),
                        (),
                        (),
                        ref(60, "CR9", column=agency),
                        "text",
                        "text",
                    )
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "field", f"rating-{j}"), (slot,), (context_id,)
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
                ("new_defaulted_borrower_count", "outcome_window", "annual"),
                ("historical_annual_default_rate", "history_window", "history"),
            )
            if cr9
            else tuple((s[0], "measurement", "measurement") for s in specs)
        )
        for i, (rid, label) in enumerate(zip(row_ids, labels)):
            aggregate = i == 8
            axis(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                ("cr9-bands",) if cr9 else (),
                location="CR9" if cr9 else "CR6 Residential mortgage",
                row=label,
                slot=FragmentRef(grid_ref, f"row/{i}"),
            )
            if not aggregate:
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
                            "CR9" if cr9 else "CR6 Residential mortgage",
                            row=label,
                        ),
                    )
                )
            for j, (key, _, _, quals) in enumerate(specs):
                cid = rid + "/" + key
                times = tuple(
                    (role, desc) for field, role, desc in roles if field == key
                )
                missing = (
                    "dash_unresolved"
                    if cr9 and i == 6 and key == "new_defaulted_borrower_count"
                    else "not_disclosed_at_this_grain"
                    if not cr9 and key == "provisions" and not aggregate
                    else "blank_unresolved"
                )
                occurrences.append(
                    OccurrenceBinding(
                        address(tid, "cell", cid),
                        (FragmentRef(grid_ref, f"{i}/{j}"),),
                        (context_id,),
                        temporal_roles=tuple(
                            TemporalRole(role, context_id, desc) for role, desc in times
                        ),
                        cell=CellBinding(
                            key,
                            rid,
                            "column-" + key,
                            () if aggregate else (f"pd-band-{i + 1}",),
                            quals,
                            "integer" if key.endswith("count") else "decimal",
                            missing,
                            source_row_role="Sub-total" if aggregate else "band",
                            source_aggregation_scope=("mortgage-block",),
                        ),
                    )
                )
                domains.append(
                    DomainFieldBinding(
                        address(tid, "cell", cid), domain, rid, key, "binding-" + key
                    )
                )
                temporal.extend(
                    CellTemporalBinding(cid, role, desc) for role, desc in times
                )
            if cr9:
                for j, agency in enumerate(("S&P", "Moodys")):
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
                            (context_id,),
                            cell=CellBinding(
                                f"rating-{j}",
                                rid,
                                f"rating-{j}",
                                (f"pd-band-{i + 1}",),
                                (),
                                "text",
                                None,
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
                            (ref(60, "CR9", label, CR9[5][1]),),
                        )
                    )
        evidence = (
            ref(
                page,
                "CR9 PD Range"
                if cr9
                else "CR6 Residential mortgage PD Range and Sub-total",
            ),
        )
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            "PD Range ¹" if cr9 else "PD Range",
            tuple(bands),
            ("context",),
            Knowledge()
            if cr9
            else Knowledge(
                "Displayed PD ranges and default category cover the subtotal",
                "established",
                ("cr6-introduction",),
            ),
            Knowledge(
                "Non-overlapping printed intervals and separate default category",
                "established",
                ("cr9-bands",) if cr9 else ("cr6-introduction",),
            ),
            evidence,
        )
        if not cr9:
            relationships.append(
                SourceRelationship(
                    "mortgage-subtotal",
                    "total",
                    "Sub-total",
                    SourceEndpoint("row", "portfolio-aggregate"),
                    tuple(SourceEndpoint("row", r) for r in row_ids[:-1]),
                    (SourceEndpoint("block", "mortgage-block"),),
                    True,
                    True,
                    evidence,
                )
            )
        note_ids = (
            (
                shared
                + (
                    "pd-definition",
                    "pd-long-run",
                    "cr9-introduction",
                    "cr9-bands",
                    "cr9-history",
                    "non-performing-definition",
                    "retail-non-performing",
                )
            )
            if cr9
            else (
                shared
                + (
                    "cr6-introduction",
                    "pd-weighting",
                    "rwa-overlays",
                    "density-rounding",
                    "pd-definition",
                    "pd-long-run",
                    "lgd-definition",
                    "lgd-downturn",
                    "ead-definition",
                    "ccf-definition",
                    "el-performing",
                    "el-default",
                )
            )
        )
        for q in note_ids:
            scope = tuple(
                SourceEndpoint("field", key) for key, _, _, qs in specs if q in qs
            )
            if q == "ccf-definition":
                scope = (
                    SourceEndpoint("field", "ead"),
                    SourceEndpoint("field", "average_ccf"),
                )
            if not scope:
                scope = (SourceEndpoint("dataset", tid),)
            if q == "el-default":
                scope += (SourceEndpoint("row", "band-8"),)
            slot = comment_slots[q]
            source = next(
                p.source_reference
                for p in physicals
                if p.revision_id == slot.binding_ref
            )
            notes.append(Qualification(q, "", (source,), scope))
            comment_targets.setdefault(q, []).extend(
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
    for q, targets in comment_targets.items():
        occurrences.append(
            OccurrenceBinding(
                address(None, "comment", q),
                (comment_slots[q],),
                links=tuple(OccurrenceLink("qualifies", t) for t in targets),
            )
        )
    document = SourceDocument(
        DOCUMENT,
        f"raw/{DOCUMENT}.pdf",
        "cba",
        "Commonwealth Bank of Australia",
        "Basel III Pillar 3 Capital Adequacy and Risk Disclosures as at 30 June 2025",
        date(2025, 6, 30),
        date(2025, 8, 13),
        "au",
        "https://www.commbank.com.au/content/dam/commbank-assets/investors/docs/results/fy25/basel-iii-pillar-3%E2%80%93capital-adequacy-risk-disclosures-30-june-2025.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        f"extractions/{BUNDLE}/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "cba-2025-capture@1",
            tuple(physicals),
            tuple(contexts),
            tuple(occurrences),
            domain_bindings=tuple(domains),
        ),
    )


DEFINITION = build()
