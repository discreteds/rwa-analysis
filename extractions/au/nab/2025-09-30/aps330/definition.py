"""NAB September 2025: reviewed agreements, source order and temporal bindings."""

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

DOCUMENT = "nab-2025-09-30-aps330"
BUNDLE = "au/nab/2025-09-30/aps330"
BOUNDS = ("0.00", "0.15", "0.25", "0.50", "0.75", "2.50", "10.00", "100.00")
LABELS = tuple(f"{a} to <{b}" for a, b in itertools.pairwise(BOUNDS)) + (
    "100.00 (Default)",
)
CR6 = (
    ("on_balance_exposure", "On-balance\nsheet EaD\npre-CRM", "$m", ()),
    ("off_balance_exposure", "Off-balance\nsheet EaD\npre-CCF and\npre-CRM", "$m", ()),
    ("average_ccf", "Average\nCCF", "%", ()),
    ("ead", "EaD\npost-CCF\nand\npost-CRM", "$m", ()),
    ("average_pd", "Weighted\naverage\nPD", "%", ()),
    ("reported_borrower_count", "Number\nof\nborrowers", "", ("borrower-definition",)),
    ("average_lgd", "Average\nloss given\ndefault\n(LGD)", "%", ()),
    ("average_maturity", "Average\nmaturity", "years", ("maturity-definition",)),
    ("rwa", "RWA", "$m", ("overlay-exclusion",)),
    ("rwa_density", "RWA\ndensity", "%", ("overlay-exclusion",)),
    ("regulatory_expected_loss", "Expected\nloss", "$m", ()),
    (
        "provisions",
        "Provision\nfor credit\nimpairment",
        "$m",
        ("provision-definition",),
    ),
)
CR9 = (
    ("weighted_average_pd", "Weighted\naverage\nPD", "%", ("cr9-weighting",)),
    (
        "arithmetic_average_pd",
        "Arithmetic\naverage\nPD by\nborrowers",
        "%",
        ("cr9-weighting", "borrower-definition"),
    ),
    (
        "current_year_borrower_count",
        "As at\n30 Sep 25",
        "",
        ("cr9-counting", "borrower-definition"),
    ),
    (
        "previous_year_borrower_count",
        "As at\n30 Sep 24",
        "",
        ("cr9-counting", "borrower-definition"),
    ),
    (
        "defaulted_borrower_count",
        "Number\nof\ndefaulted\nborrowers\nin the\nyear",
        "",
        ("cr9-counting", "borrower-definition", "cr9-defaults"),
    ),
    (
        "new_defaulted_borrower_count",
        "Of which:\nnew\ndefaulted\nborrowers\nin the\nyear",
        "",
        ("cr9-counting", "borrower-definition", "cr9-defaults", "cr9-new-defaults"),
    ),
    (
        "historical_annual_default_rate",
        "Average\nhistorical\nannual\ndefault\nrate",
        "%",
        ("cr9-history", "cr9-framework"),
    ),
)
SHARED = (
    "report-entity",
    "currency-rounding",
    "regulatory-basis",
    "level-2-definition",
    "level-2",
)
PASSAGES = (
    (
        "report-entity",
        4,
        "Introduction",
        "The Group, being NAB",
        "measure capital adequacy.",
    ),
    (
        "currency-rounding",
        4,
        "Introduction",
        "Amounts are presented",
        "except where indicated.",
    ),
    (
        "regulatory-basis",
        4,
        "Introduction",
        "National Australia Bank Limited (NAB)",
        "Attachment A of APS 330.",
    ),
    (
        "level-2-definition",
        4,
        "Scope of consolidation",
        "Level 2 comprises NAB",
        "leasing companies.",
    ),
    (
        "level-2",
        4,
        "Scope of consolidation",
        "This report applies",
        "unless otherwise stated.",
    ),
    (
        "cr6-introduction",
        48,
        "CR6 introduction",
        "The following tables provide",
        "band, where:",
    ),
    (
        "approach",
        48,
        "CR6 approach heading",
        "Credit risk exposures subject",
        "by asset class and PD band",
    ),
    (
        "borrower-definition",
        48,
        "CR6 column (f) definition",
        "The number of borrowers in column (f)",
        "subsidiary's underlying asset classes.",
    ),
    (
        "maturity-definition",
        48,
        "CR6 column (h) definition",
        "Average maturity in column (h)",
        "template prescribed by APS 330.",
    ),
    (
        "overlay-exclusion",
        48,
        "CR6 columns (i) and (j) definition",
        "RWA in column (i)",
        "exclude RWA overlay adjustments.",
    ),
    (
        "provision-definition",
        48,
        "CR6 column (l) definition",
        "The provision for credit impairment in column (l)",
        "template prescribed by APS 330.",
    ),
    (
        "cr9-introduction",
        60,
        "cr9-introduction",
        "The following tables provide results",
        "for each ECAI.",
    ),
    (
        "cr9-weighting",
        60,
        "cr9-weighting",
        "Weighted average PD in column (a)",
        "divided by the number of borrowers.",
    ),
    (
        "cr9-counting",
        60,
        "cr9-counting",
        "The approach to measure",
        "probability of default range.",
    ),
    ("cr9-defaults", 60, "cr9-defaults", "A borrower is included", "during the year."),
    (
        "cr9-new-defaults",
        60,
        "cr9-new-defaults",
        "The number of borrowers in column (e)",
        "during the financial year.",
    ),
    (
        "cr9-history",
        60,
        "cr9-history",
        "A 10-year observation period",
        "has been averaged.",
    ),
    (
        "cr9-framework",
        60,
        "cr9-framework",
        "Changes in asset class definitions",
        "best endeavours basis.",
    ),
    (
        "cr9-bnz-separation",
        60,
        "cr9-bnz-separation",
        "APS 330 requires information",
        "represents 91% of credit RWA.",
    ),
)
AGENCIES = ("S&P Global Ratings /\nFitch Ratings", "Moody's Investor Services")


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, "" if page == 1 else str(page - 2), location, row, column
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

    def region(key, evidence, box, multiline=False):
        return physical(
            key, "region", evidence, box=tuple(map(str, box)), multiline=int(multiline)
        )

    for key, page, location, start, end in PASSAGES:
        comments[key] = physical(
            key, "passage", ref(page, location), start=start, end=end
        )
    for domain, page, specs, edges, markers, label_box in (
        (
            "cr6",
            49,
            CR6,
            (166, 225, 286, 330, 384, 429, 480, 531, 582, 633, 684, 733, 786),
            (62, 63, 295, 410),
            (60, 165),
        ),
        (
            "cr9",
            61,
            CR9,
            (191, 240, 290, 340, 389, 439, 489, 539),
            (48, 49, 165, 260),
            (45, 190),
        ),
    ):
        cr9 = domain == "cr9"
        tid = domain + "-residential-mortgages"
        template = domain.upper()
        title = (
            "CR9: IRB - backtesting of probability of default per portfolio"
            if cr9
            else "CR6: IRB – credit risk exposures by portfolio and probability of default range"
        )
        common = SHARED + (
            ("cr9-introduction", "cr9-bnz-separation")
            if cr9
            else ("cr6-introduction", "approach")
        )
        labels = LABELS if cr9 else LABELS + ("Sub-total",)
        row_ids = tuple(f"band-{i}" for i in range(1, 9)) + (
            () if cr9 else ("portfolio-aggregate",)
        )
        context = TableContext(
            "context",
            date(2025, 9, 30),
            "" if cr9 else "As at 30 Sep 25",
            template,
            title,
            "Residential mortgage",
            Knowledge(
                "NAB and its controlled entities", "established", ("report-entity",)
            ),
            Knowledge("Level 2", "established", ("level-2-definition", "level-2")),
            Knowledge(
                "A-IRB",
                "established",
                ("cr9-introduction",) if cr9 else ("regulatory-basis", "approach"),
            ),
            Knowledge(),
            Knowledge("AUD", "established", ("currency-rounding",)),
            common,
            (ref(60, "CR9 introduction and A-IRB heading"), ref(61, "CR9 headings"))
            if cr9
            else (
                ref(1, "Cover"),
                ref(48, "CR6 title and approach"),
                ref(49, "CR6 date and portfolio headings"),
            ),
        )
        cid = tid + "/context@1"
        descriptors = (
            (
                TemporalDescriptor(
                    "current-year",
                    "As at 30 Sep 25",
                    point="2025-09-30",
                    point_status="established",
                    evidence=(ref(61, "CR9 count header"),),
                ),
                TemporalDescriptor(
                    "previous-year",
                    "As at 30 Sep 24",
                    point="2024-09-30",
                    point_status="established",
                    evidence=(ref(61, "CR9 count header"),),
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
                        ref(1, "Full Year report cover"),
                        ref(60, "cr9-defaults"),
                    ),
                ),
                TemporalDescriptor(
                    "history",
                    "10-year observation period",
                    duration_amount=Decimal(10),
                    duration_unit="years",
                    duration_status="established",
                    qualification_refs=("cr9-history", "cr9-framework"),
                    evidence=(ref(60, "cr9-history"),),
                ),
                TemporalDescriptor(
                    "unspecified", "", evidence=(ref(60, "CR9 definitions"),)
                ),
            )
            if cr9
            else (
                TemporalDescriptor(
                    "measurement",
                    "As at 30 Sep 25",
                    point="2025-09-30",
                    point_status="established",
                    evidence=(ref(49, "CR6 date and portfolio headings"),),
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
            tid + "/title", "passage", ref(page - 1, template), start=title, end=title
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
            source_page=None,
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
                    ref(source_page or page, location or template, row, column),
                )
            )
            occurrences.append(
                OccurrenceBinding(
                    address(tid, kind, key), () if slot is None else (slot,), (cid,)
                )
            )

        if cr9:
            structures = (
                (
                    "mortgage-block",
                    "block",
                    "Residential mortgage",
                    0,
                    (),
                    (45, 190, 153, 163),
                ),
                ("pd-heading", "header", "PD scale", 1, (), (45, 100, 139, 149)),
                (
                    "borrower-counts",
                    "header",
                    "Number of borrowers",
                    2,
                    (),
                    (290, 389, 94, 102),
                ),
            )
        else:
            structures = (
                ("date", "header", "As at 30 Sep 25", 0, (), (440, 520, 80, 90)),
                ("pd-heading", "header", "PD scale", 2, (), (60, 160, 142, 153)),
                (
                    "mortgage-block",
                    "block",
                    "Residential mortgage",
                    3,
                    ("approach",),
                    (60, 165, 282, 295),
                ),
            )
        for key, kind, label, order, parents, box in structures:
            axis(
                key,
                kind,
                label,
                order,
                parents,
                slot=region(tid + "/" + key, ref(page, template), box),
            )
            if not cr9 and key == "date":
                approach = "Credit risk exposures subject to the A-IRB approach by asset class and PD band"
                axis(
                    "approach",
                    "header",
                    approach,
                    1,
                    source_page=48,
                    slot=physical(
                        tid + "/approach",
                        "passage",
                        ref(48, "CR6"),
                        start=approach,
                        end=approach,
                    ),
                )
        columns = tuple(s[1] for s in specs) if cr9 else tuple("abcdefghijkl")
        grid_ref = physical(
            tid + "/body",
            "grid",
            ref(
                page, "CR9 Residential mortgage" if cr9 else "CR6 Residential mortgage"
            ),
            edges=tuple(map(str, edges)),
            markers=tuple(map(str, markers)),
            labels=tuple(map(str, label_box)),
            columns=columns,
        ).binding_ref
        for j, (key, label, unit, quals) in enumerate(specs):
            column = "column-" + key if cr9 else columns[j]
            parents = (
                (("borrower-counts",) if j in (2, 3) else ()) if cr9 else ("date",)
            )
            evidence = ref(
                page,
                "CR9 header" if cr9 else "CR6 header",
                column=label if cr9 else column,
            )
            slot = region(
                tid + "/field/" + key,
                evidence,
                (
                    edges[j],
                    edges[j + 1],
                    (128 if j in (2, 3) else 94) if cr9 else 105,
                    (145 if j in (2, 3) else 140) if cr9 else 141,
                ),
                True,
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
            if key.endswith("count"):
                attributes = (
                    SemanticAttribute(
                        "counted_entity",
                        "agreement",
                        "established",
                        ("cr9-counting", "borrower-definition") if cr9 else quals,
                    ),
                    SemanticAttribute("distinctness", None, "unresolved", ()),
                )
            elif cr9 and key == "weighted_average_pd":
                attributes = (
                    SemanticAttribute(
                        "weighting", "EAD", "established", ("cr9-weighting",)
                    ),
                )
            elif cr9 and key == "arithmetic_average_pd":
                attributes = (
                    SemanticAttribute(
                        "weighting", "arithmetic_by_agreements", "established", quals
                    ),
                )
            elif not cr9 and key.startswith("average_"):
                attributes = (SemanticAttribute("weighting", None, "unresolved", ()),)
            if cr9 and j >= 4:
                attributes += (
                    SemanticAttribute(
                        "default_cell_presentation", "shaded", "established", ()
                    ),
                )
            if key in ("rwa", "rwa_density"):
                attributes = (
                    SemanticAttribute(
                        "overlay_treatment", "excluded", "established", quals
                    ),
                )
            if key == "average_maturity":
                attributes += (
                    SemanticAttribute(
                        "missing_cell_presentation", "shaded", "established", quals
                    ),
                )
            if key == "provisions":
                attributes = (
                    SemanticAttribute(
                        "band_cell_presentation", "shaded", "established", quals
                    ),
                )
            fields.append(
                TableField(
                    key,
                    label,
                    parents + (column,),
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
                ref(46, "External ratings"),
                edges=("340", "440", "550"),
                markers=("255", "256", "159", "255"),
                labels=("250", "340"),
                columns=AGENCIES,
                row_labels=LABELS,
            ).binding_ref
            for j, agency in enumerate(AGENCIES):
                slot = region(
                    tid + f"/rating-{j}",
                    ref(46, "External ratings"),
                    ((340, 440)[j], (440, 550)[j], 139, 157),
                    True,
                )
                axis(
                    f"rating-{j}",
                    "column",
                    agency,
                    j,
                    quals=("cr9-introduction",),
                    location="External ratings",
                    source_page=46,
                    slot=slot,
                )
                fields.append(
                    TableField(
                        f"rating-{j}",
                        agency,
                        (f"rating-{j}",),
                        "",
                        Decimal(1),
                        ("cr9-introduction",),
                        (),
                        ref(46, "External ratings"),
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
                ("weighted_average_pd", "measurement", "current-year"),
                ("weighted_average_pd", "weight_measurement", "current-year"),
                ("arithmetic_average_pd", "measurement", "unspecified"),
                ("current_year_borrower_count", "measurement", "current-year"),
                ("previous_year_borrower_count", "measurement", "previous-year"),
                ("defaulted_borrower_count", "outcome_window", "annual"),
                ("new_defaulted_borrower_count", "outcome_window", "annual"),
                ("historical_annual_default_rate", "history_window", "history"),
            )
            if cr9
            else tuple((s[0], "measurement", "measurement") for s in specs)
        )
        for i, (rid, label) in enumerate(zip(row_ids, labels)):
            row_slot = FragmentRef(grid_ref, f"row/{i}")
            # The original CR9 row-axis reference is to CR9; values name its selected block.
            axis(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                location="CR9" if cr9 else "CR6 Residential mortgage",
                row=label,
                slot=row_slot,
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
                            "CR9" if cr9 else "CR6 Residential mortgage",
                            row=label,
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
                    if cr9 and i in (0, 6) and key == "new_defaulted_borrower_count"
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
                            source_row_role="Sub-total" if i == 8 else "band",
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
                for j, agency in enumerate(AGENCIES):
                    slot = FragmentRef(rating_ref, f"{i}/{j}")
                    axis(
                        f"{rid}-rating-{j}",
                        "header",
                        "",
                        j,
                        (rid, f"rating-{j}"),
                        ("cr9-introduction",),
                        "External ratings",
                        label,
                        agency,
                        slot,
                        46,
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
                                ("cr9-introduction",),
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
                            (
                                ref(60, "cr9-new-defaults"),
                                ref(61, "CR9", label, CR9[5][1]),
                            ),
                        )
                    )
        evidence = (
            ref(
                page,
                "CR9 PD scale"
                if cr9
                else "CR6 Residential mortgage PD scale and Sub-total",
            ),
        )
        segmentation = SegmentationDefinition(
            "pd-segmentation",
            "PD scale",
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
                () if cr9 else ("cr6-introduction",),
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
            SHARED + ("borrower-definition",) + tuple(p[0] for p in PASSAGES[11:])
            if cr9
            else tuple(p[0] for p in PASSAGES[:11])
        )
        for q in note_ids:
            scope = tuple(
                SourceEndpoint("field", key) for key, _, _, qs in specs if q in qs
            ) or (SourceEndpoint("dataset", tid),)
            if cr9 and q == "borrower-definition":
                scope = tuple(
                    SourceEndpoint("field", s[0]) for s in (*CR9[2:6], CR9[1])
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
        "nab",
        "National Australia Bank Limited",
        "Pillar 3 Report as at 30 September 2025 Incorporating the requirements of APS 330",
        date(2025, 9, 30),
        date(2025, 11, 6),
        "au",
        "https://www.nab.com.au/content/dam/nab/documents/notice/corporate/2025-full-year-pillar-3-report.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        f"extractions/{BUNDLE}/extract.py",
        tuple(tables),
        CaptureSnapshot(
            "nab-2025-capture@1",
            tuple(physicals),
            tuple(contexts),
            tuple(occurrences),
            domain_bindings=tuple(domains),
        ),
    )


DEFINITION = run_path(str(Path(__file__).with_name("adjustments.py")))["extend"](build())
