"""Reviewed Westpac 2023 metadata and physical bindings; no PDF processing."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from itertools import pairwise

from rwa_analysis.catalogue.models import EvidenceRef
from rwa_analysis.catalogue.models import SemanticAttribute as Assertion
from rwa_analysis.extraction.definitions import (
    CaptureDefinition,
    CaptureSnapshot,
    CellBinding,
    ContextDefinition,
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

DOCUMENT = "westpac-2023-09-30-aps330"
BUNDLE = "au/westpac/2023-09-30/aps330"
PORTFOLIO = "Residential mortgages"
PANELS = (
    ("2023-09-30", "30 September 2023"),
    ("2023-03-31", "31 March 2023"),
    ("2022-09-30", "30 September 2022"),
)
HISTORY_FIELDS = (
    "predicted_pd",
    "observed_pd",
    "predicted_lgd",
    "observed_lgd",
    "ead_variance",
)
BANDS = (
    "0.0 to 0.10",
    "0.10 to 0.25",
    "0.25 to 1.0",
    "1.0 to 2.5",
    "2.5 to 10.0",
    "10.0 to 99.99",
    "Subtotal",
    "Default",
    "Total",
)


def ref(page, location, row=None, column=None):
    return SourceReference(
        DOCUMENT, page, "" if page == 2 else str(page - 2), location, row, column
    )


def physical(key, operation, page, location, **parameters):
    return PhysicalBinding(
        key + "@1",
        operation,
        tuple(PhysicalParameter(k, v) for k, v in parameters.items()),
        ref(page, location),
    )


def note(physicals, key, page, start, end, targets, kind="field"):
    physicals[key, page] = physical(
        f"{key}-p{page}",
        "passage",
        page,
        key,
        start=start,
        end=end or "",
        **({"font_prefix": "WFANIQ+"} if page == 2 else {}),
    )
    return Qualification(
        key,
        "",
        (ref(page, key),),
        tuple(SourceEndpoint(kind, target) for target in targets),
    )


def common_notes(physicals, dataset):
    return [
        note(physicals, key, page, start, end, (dataset,), "dataset")
        for key, page, start, end in (
            ("report-entity", 2, "In this report references", "In this report, unless"),
            (
                "currency",
                2,
                "In this report, unless otherwise stated or the context otherwise requires",
                "References to ‘US$’",
            ),
            ("rounding", 2, "Any discrepancies", "In this report"),
            ("level-2", 13, "Unless otherwise specified", "The Westpac Group"),
            ("regulatory-basis", 6, "Westpac uses the Advanced", "In accordance"),
        )
    ]


def context(label, title, template, page, qualifications=()):
    return TableContext(
        "context",
        date(2023, 9, 30),
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
        ("report-entity", "currency", "rounding", "level-2", "regulatory-basis")
        + qualifications,
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


def measurement(day, label, page):
    return TemporalDescriptor(
        "measurement",
        label,
        point=day,
        point_status="established",
        evidence=(ref(page, "Panel heading"),),
    )


def exposure(physicals, day, label):
    dataset, page = "table9d-" + day, 44
    title = "Residential mortgages portfolio by PD band¹,²"
    specs = (
        ("outstandings", "Outstandings³", "$m", ("outstandings",)),
        ("undrawn", "Committed Undrawn⁴", "$m", ("undrawn",)),
        ("ead", "Exposure at Default", "$m", ("ead-definition",)),
        ("pd", "Probability of Default", "%", ("pd-bands", "pd-definition")),
        ("lgd", "Loss Given Default", "%", ("lgd-definition",)),
        (
            "expected_loss",
            "Regulatory Expected Loss",
            "$m",
            ("expected-loss-definition",),
        ),
        ("rwa", "Risk Weighted Assets", "$m", ("rwa-definition", "risk-weight-floor")),
        ("risk_weight", "Average Risk Weight", "%", ("risk-weight-floor",)),
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
    notes = common_notes(physicals, dataset)
    for key, source, start, end, targets in (
        ("outstandings", 44, "Outstandings are", "4. ", ("outstandings",)),
        ("undrawn", 44, "Committed undrawn balances", None, ("undrawn",)),
        (
            "risk-weight-floor",
            44,
            "The above table reflects",
            "3. ",
            ("rwa", "risk_weight")
            + (("risk_weight_floor",) if day == "2022-09-30" else ()),
        ),
        (
            "expected-loss-definition",
            41,
            "For both non-defaulted",
            "From 31 March",
            ("expected_loss",),
        ),
        ("ead-definition", 110, "EAD is calculated", "Expected credit loss", ("ead",)),
        ("lgd-definition", 111, "The LGD represents", "Maturity", ("lgd",)),
        ("rwa-definition", 112, "Assets (both", "Securitisation purchased", ("rwa",)),
    ):
        notes.append(note(physicals, key, source, start, end, targets))
    # PD defines both the numeric field and interval segmentation, not all fields.
    for key, source, start, end in (
        ("pd-bands", 41, "Westpac’s program-managed", "For both"),
        ("pd-definition", 112, "Probability of default is", "Resecuritisation"),
    ):
        q = note(physicals, key, source, start, end, ("pd",))
        notes.append(
            replace(
                q,
                scope=q.scope
                + tuple(SourceEndpoint("band", f"band-{i}") for i in range(6)),
            )
        )
    if day == "2022-09-30":
        default_quals = ("default-pre-2023",)
        notes.append(
            note(
                physicals,
                "default-pre-2023",
                110,
                "Pre – 1 January 2023:",
                "From 1 January 2023:",
                ("band-7",),
                "band",
            )
        )
    else:
        default_quals = ("default-from-2023", "npe-definition")
        notes.extend(
            (
                note(
                    physicals,
                    "default-from-2023",
                    110,
                    "From 1 January 2023:",
                    "Defaulted not impaired",
                    ("band-7",),
                    "band",
                ),
                note(
                    physicals,
                    "npe-definition",
                    112,
                    "Credit default exposures",
                    "Non-Performing Exposures –",
                    ("band-7",),
                    "band",
                ),
            )
        )
    context_quals = ()
    if day != "2022-09-30":
        context_quals = (
            "asset-class-transition",
            "mortgage-definition",
            "nz-perimeter",
        )
        for key, source, start, end in (
            ("asset-class-transition", 41, "From 31 March 2023", "Corporate portfolio"),
            (
                "mortgage-definition",
                22,
                "Residential Mortgages asset class",
                "Australian Credit Cards",
            ),
            (
                "nz-perimeter",
                22,
                "RBNZ regulated exposures",
                "Standardised and Securitised",
            ),
        ):
            notes.append(
                note(physicals, key, source, start, end, (dataset,), "dataset")
            )
    bands, cells = [], []
    for i, row_label in enumerate(BANDS):
        bid = f"band-{i}"
        bounds = row_label.split(" to ") if i < 6 else (None, None)
        qs = ("pd-bands", "pd-definition") if i < 6 else default_quals if i == 7 else ()
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
        cells.extend(bid + "/" + f.id for f in fields)
    if day == "2023-09-30":
        keys = ("irb_rwa", "standardised_rwa")
        q = note(
            physicals, "supplementary-rwa", 44, "As at 30 September 2023", "2. ", keys
        )
        notes.append(q)
        for key, name in zip(
            keys,
            (
                "Residential Mortgages risk weighted assets under the IRB approach",
                "standardised approach equivalent",
            ),
            strict=True,
        ):
            f = field(key, name, "$m", page, "Footnote 1", (), (q.id,), form="note")
            fields.append(f)
            cells.append(key)
    if day == "2022-09-30":
        q = next(q for q in notes if q.id == "risk-weight-floor")
        f = field(
            "risk_weight_floor",
            "floor of 25% to its residential mortgage risk weights",
            "%",
            page,
            "Footnote 2",
            (),
            (q.id,),
            form="note",
        )
        fields.append(f)
        cells.append(f.id)
    relationships = tuple(
        SourceRelationship(
            key,
            "total",
            name,
            SourceEndpoint("row", parent),
            tuple(SourceEndpoint("row", child) for child in children),
            (SourceEndpoint("dataset", dataset),),
            None,
            None,
            (ref(page, title, name),),
        )
        for key, name, parent, children in (
            ("subtotal", "Subtotal", "band-6", tuple(f"band-{i}" for i in range(6))),
            ("total", "Total", "band-8", ("band-6", "band-7")),
        )
    )
    return SourceTable(
        dataset,
        SourceTableMetadata(
            context(label, title, "Table 9(d)", page, context_quals),
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
            (measurement(day, label, page),),
            tuple(CellTemporalBinding(c, "measurement", "measurement") for c in cells),
        ),
        (),
    )


def backtesting(physicals, day, label):
    dataset = "table9f-" + day
    page = 56 if day == "2023-09-30" else 57
    title = "Regulatory loss estimates and actual losses" + (
        " (continued)" if page == 57 else ""
    )
    label = label.replace("September", "Sept")
    shared = ("backtesting-framework", "nz-history")
    specs = (
        (
            "expected_loss",
            "Regulatory Expected Loss¹",
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
            "Observed EAD variance to Predicted²",
            "%",
            None,
            shared + ("ead-variance-method", "negative-variance"),
        ),
    )
    notes = common_notes(physicals, dataset)
    for key, source, start, end, targets in (
        (
            "backtesting-framework",
            56,
            "The table below compares",
            "Default rates",
            HISTORY_FIELDS,
        ),
        (
            "default-rates",
            56,
            "At the start of each year",
            "Loss Given Default (LGD)",
            HISTORY_FIELDS[:2],
        ),
        (
            "lgd-workout",
            56,
            "The LGD analysis",
            "Exposure at Default (EAD)",
            HISTORY_FIELDS[2:4],
        ),
        (
            "ead-variance-method",
            56,
            "The EAD variance",
            "30 Sept 2023",
            ("ead_variance",),
        ),
        (
            "expected-loss-population",
            page,
            "Includes regulatory expected losses",
            "2. ",
            ("expected_loss",),
        ),
        ("negative-variance", page, "A negative outcome", "3. ", ("ead_variance",)),
        ("nz-history", page, "Historical Default Rate", None, HISTORY_FIELDS),
    ):
        notes.append(note(physicals, key, source, start, end, targets))
    axes = [
        axis("panel", "header", label, 0, page, title),
        axis("mortgage", "row", PORTFOLIO, 0, page, title, ("panel",)),
        axis("default-rate", "header", "Default rate", 0, page, title, ("panel",)),
        axis("lgd", "header", "Loss Given Default", 1, page, title, ("panel",)),
    ]
    fields = []
    for j, (key, name, unit, parent, qs) in enumerate(specs):
        parents = ("panel", parent) if parent else ("panel",)
        attrs = (
            (SemanticAttribute("weighting", None, "unresolved", ()),)
            if key in HISTORY_FIELDS
            else ()
        )
        f = field(key, name, unit, page, title, parents + (key,), qs, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, parents, qs))
    descriptors = [measurement(day, label, page)]
    for key, text, qs, location in (
        (
            "history",
            "since IRB accreditation; 2008 for most portfolios",
            ("backtesting-framework", "default-rates", "nz-history"),
            "Default rates",
        ),
        (
            "lgd-history",
            "since IRB accreditation, excluding recent defaults; two-year residential mortgage workout",
            ("backtesting-framework", "lgd-workout", "nz-history"),
            "Loss Given Default (LGD)",
        ),
        (
            "ead-history",
            "all obligors that defaulted over the observation period",
            ("backtesting-framework", "ead-variance-method", "nz-history"),
            "Exposure at Default (EAD)",
        ),
        (
            "annual-anchor",
            "At the start of each year",
            ("default-rates",),
            "Default rates",
        ),
        (
            "annual-outcome",
            "during the one-year period",
            ("default-rates",),
            "Default rates",
        ),
        (
            "ead-prediction",
            "up to one year prior to default",
            ("ead-variance-method",),
            "Exposure at Default (EAD)",
        ),
    ):
        descriptors.append(
            TemporalDescriptor(
                key,
                text,
                duration_amount=Decimal(1) if key == "annual-outcome" else None,
                duration_unit="year" if key == "annual-outcome" else None,
                duration_status="established"
                if key == "annual-outcome"
                else "unresolved",
                qualification_refs=qs,
                evidence=(ref(56, location),),
            )
        )
    bindings = [
        CellTemporalBinding("mortgage/expected_loss", "measurement", "measurement")
    ]
    for key in HISTORY_FIELDS:
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
        dataset,
        SourceTableMetadata(
            context(label, title, "Table 9(f)", page),
            tuple(axes),
            tuple(fields),
            (),
            tuple(notes),
            (),
            tuple(descriptors),
            tuple(bindings),
        ),
        (),
    )


def bindings(tables, notes):
    """Expand the reviewed grids into explicit, retained occurrence bindings."""
    physicals = list(notes.values())
    occurrences, contexts = [], []

    def address(scope, kind, key):
        return OccurrenceRef(BUNDLE, scope, kind, key)

    common = tables[0].metadata.context
    attributes = tuple(
        Assertion(
            value.value,
            value.status,
            evidence_refs=tuple(
                EvidenceRef(BUNDLE, DOCUMENT, "", "comment", q)
                for q in value.qualification_refs
            ),
            name=name,
        )
        for name, value in (
            ("reporting_entity", common.reporting_entity),
            ("consolidation_scope", common.consolidation_scope),
            ("regulatory_scope", common.regulatory_scope),
            ("geography", common.geography),
            ("currency", common.currency),
        )
    )
    common_id = "westpac-2023/common@1"
    contexts.append(ContextDefinition(common_id, attributes, evidence=common.evidence))
    comment_targets = {}
    for table_index, table in enumerate(tables):
        tid, meta = table.id, table.metadata
        backtest = table_index >= 3
        page = meta.context.evidence[0].pdf_page
        title, label = meta.context.source_title, meta.context.source_date_label
        time_id = tid + "/time@1"
        contexts.append(ContextDefinition(time_id, temporal=meta.temporal_descriptors))
        context_refs = (common_id, time_id)

        def bind(
            kind,
            key,
            reader,
            slot="text",
            *,
            links=(),
            cell=None,
            roles=(),
            tid=tid,
            context_refs=context_refs,
        ):
            occurrences.append(
                OccurrenceBinding(
                    address(tid, kind, key),
                    (FragmentRef(reader.revision_id, slot),),
                    context_refs,
                    links=links,
                    temporal_roles=roles,
                    cell=cell,
                )
            )

        heading = physical(
            tid + "/title",
            "passage",
            page,
            title,
            start="Regulatory loss estimates"
            if backtest
            else "Residential mortgages portfolio",
            end="\n",
        )
        physicals.append(heading)
        bind("table", tid, heading)
        reader = physical(
            tid + "/body",
            "rows",
            page,
            title,
            after=label,
            prefix=PORTFOLIO if backtest else BANDS[0],
            rows=1 if backtest else 9,
            columns=6 if backtest else 8,
            labels=tuple(
                f.source_label
                for f in meta.published_fields
                if f.source_form == "table_body"
            ),
        )
        physicals.append(reader)
        if backtest:
            top = (464, 116, 359)[table_index - 3]
            shift = 0 if page == 56 else 28.35
            boxes = (
                (214, top, 251, top + 28),
                (275, top + 19, 308, top + 28),
                (332, top + 19, 365, top + 28),
                (389, top + 19, 421, top + 28),
                (445, top + 19, 478, top + 28),
                (487, top, 535, top + 28),
            )
            boxes = tuple(
                (left + shift, y, right + shift, bottom)
                for left, y, right, bottom in boxes
            )
            axis_boxes = {
                "panel": (30 + shift, top, 110 + shift, top + 8),
                "default-rate": (298 + shift, top + 9, 337 + shift, top + 17),
                "lgd": (402 + shift, top + 9, 461 + shift, top + 17),
            }
        else:
            top = (116, 272, 428)[table_index]
            edges = (125, 185, 235, 285, 335, 385, 445, 495, 536)
            boxes = tuple(
                (left, top, right, top + 30) for left, right in pairwise(edges)
            )
            axis_boxes = {"panel": (30, top + 9, 110, top + 18)}
        for key, box in axis_boxes.items():
            region = physical(
                tid + "/" + key, "region", page, title, box=tuple(str(v) for v in box)
            )
            physicals.append(region)
            bind("header", key, region)
        if not backtest:
            band_header = physical(
                tid + "/pd-bands",
                "passage",
                page,
                title,
                start="PD band",
                end="\n",
                after="Residential mortgages portfolio by ",
            )
            physicals.append(band_header)
            bind("header", "pd-bands", band_header)
        for i, a in enumerate(a for a in meta.axes if a.axis == "row"):
            bind(
                "row",
                a.id,
                reader,
                f"row/{i}",
                links=tuple(
                    OccurrenceLink("header", address(tid, "header", p))
                    for p in a.header_path_refs
                ),
            )
        for j, f in enumerate(meta.published_fields):
            if f.source_form == "table_body":
                header = physical(
                    tid + "/" + f.id + "/header",
                    "region",
                    page,
                    title,
                    box=tuple(str(v) for v in boxes[j]),
                )
                physicals.append(header)
                path = tuple(
                    OccurrenceLink("header", address(tid, "header", p))
                    for p in f.header_path_refs[:-1]
                )
                bind("field", f.id, header, links=path)
                bind("column", f.id, header, links=path)
                rows = (
                    ("mortgage",) if backtest else tuple(f"band-{i}" for i in range(9))
                )
            else:
                q = f.qualification_refs[0]
                header = notes[q, page]
                bind("field", f.id, header)
                rows = (None,)
            for i, row in enumerate(rows):
                cid = row + "/" + f.id if row else f.id
                if row:
                    source, slot = reader, f"{i}/{j}"
                else:
                    q = f.qualification_refs[0]
                    pattern = (
                        r"floor of (\d+%)"
                        if f.id == "risk_weight_floor"
                        else r"\$([\d,]+) million"
                    )
                    index = 1 if f.id == "standardised_rwa" else 0
                    source = physical(
                        tid + "/" + f.id,
                        "token",
                        page,
                        f.source_reference.location,
                        start="The above table reflects"
                        if f.id == "risk_weight_floor"
                        else "As at 30 September 2023",
                        end="3. " if f.id == "risk_weight_floor" else "2. ",
                        pattern=pattern,
                        index=index,
                    )
                    physicals.append(source)
                    slot = "text"
                roles = tuple(
                    TemporalRole(b.role, time_id, b.descriptor_ref)
                    for b in meta.temporal_bindings
                    if b.cell_id == cid
                )
                missing = (
                    "not_applicable"
                    if tid == "table9d-2022-09-30" and cid == "band-7/pd"
                    else None
                )
                links = (OccurrenceLink("field", address(tid, "field", f.id)),)
                if row:
                    links += (
                        OccurrenceLink("row", address(tid, "row", row)),
                        OccurrenceLink("column", address(tid, "column", f.id)),
                    )
                else:
                    links += (OccurrenceLink("evidence", address(None, "comment", q)),)
                bind(
                    "cell",
                    cid,
                    source,
                    slot,
                    links=links,
                    roles=roles,
                    cell=CellBinding(
                        f.id,
                        row,
                        f.id if row else None,
                        (row,) if row and not backtest else (),
                        f.qualification_refs,
                        missing_reason=missing,
                        missing_tokens=("N/A",) if missing == "not_applicable" else (),
                    ),
                )
        for q in meta.qualifications:
            source_page = q.evidence[0].pdf_page
            # Page 57's printed notes serve both comparative panels. The separately
            # printed page 56 notes have their own table-scoped occurrences.
            scope = (
                tid
                if source_page == 56
                and q.id
                in ("expected-loss-population", "negative-variance", "nz-history")
                else None
            )
            comment_targets.setdefault((scope, q.id, source_page), []).extend(
                address(
                    tid, {"dataset": "table", "band": "row"}.get(e.kind, e.kind), e.id
                )
                for e in q.scope
            )
    for (scope, key, page), targets in comment_targets.items():
        occurrences.append(
            OccurrenceBinding(
                address(scope, "comment", key),
                (FragmentRef(notes[key, page].revision_id, "text"),),
                links=tuple(OccurrenceLink("qualifies", target) for target in targets),
            )
        )
    return CaptureSnapshot(
        "westpac-2023-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
    )


def build():
    notes = {}
    tables = tuple(exposure(notes, day, label) for day, label in PANELS)
    tables += tuple(backtesting(notes, day, label) for day, label in PANELS)
    snapshot = bindings(tables, notes)
    return CaptureDefinition(
        SourceDocument(
            DOCUMENT,
            "raw/westpac-2023-09-30-aps330.pdf",
            "westpac",
            "Westpac Banking Corporation",
            "September 2023 Pillar 3 Report",
            date(2023, 9, 30),
            None,
            "au",
            "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/september-2023-Pillar-3-report.pdf",
        ),
        BUNDLE,
        "extractions/au/westpac/2023-09-30/aps330/extract.py",
        tables,
        snapshot,
    )


DEFINITION = build()
