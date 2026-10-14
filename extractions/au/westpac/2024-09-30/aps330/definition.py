"""Reviewed Westpac 2024 metadata and physical bindings; no PDF processing."""

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

DOCUMENT = "westpac-2024-09-30-aps330"
BUNDLE = "au/westpac/2024-09-30/aps330"
PORTFOLIO = "Residential Mortgages"
PANELS = (
    ("2024-09-30", "30 September 2024"),
    ("2024-03-31", "31 March 2024"),
    ("2023-09-30", "30 September 2023"),
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
    return SourceReference(DOCUMENT, page, str(page), location, row, column)


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
        **({"remove": "assets (RWA) "} if key == "rwa-definition" else {}),
    )
    return Qualification(
        key, "", (ref(page, key),), tuple(SourceEndpoint(kind, t) for t in targets)
    )


def common_notes(physicals, id):
    return (
        note(
            physicals,
            "report-entity",
            2,
            "In this report references",
            "In this report, unless",
            (id,),
            "dataset",
        ),
        note(
            physicals,
            "currency",
            2,
            "In this report, unless otherwise stated or the context otherwise requires",
            "References to ‘US$’",
            (id,),
            "dataset",
        ),
        note(
            physicals,
            "level-2",
            14,
            "Unless otherwise specified",
            "The Westpac Group",
            (id,),
            "dataset",
        ),
        note(
            physicals,
            "regulatory-basis",
            7,
            "Westpac uses the Advanced",
            "In accordance",
            (id,),
            "dataset",
        ),
        note(
            physicals,
            "rounding",
            2,
            "Any discrepancies",
            "In this report",
            (id,),
            "dataset",
        ),
    )


def context(id, label, title, template, page):
    return TableContext(
        "context",
        date(2024, 9, 30),
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
        ("report-entity", "level-2", "regulatory-basis", "currency", "rounding"),
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


def exposure(physicals, day, label):
    id, page = "table9d-" + day, 45
    title = "Residential Mortgages portfolio by PD band¹"
    specs = (
        ("outstandings", "Outstandingsᵃ", "$m", ("outstandings",)),
        ("undrawn", "Committed Undrawnᵇ", "$m", ("undrawn",)),
        ("ead", "Exposure at Default", "$m", ("ead-definition",)),
        ("pd", "Probability of Default", "%", ("pd-bands", "pd-definition")),
        ("lgd", "Loss Given Default", "%", ("lgd-definition",)),
        (
            "expected_loss",
            "Regulatory Expected Loss",
            "$m",
            ("expected-loss-definition",),
        ),
        ("rwa", "Risk Weighted Assets", "$m", ("rwa-definition",)),
        ("risk_weight", "Average Risk Weight", "%", ()),
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
    notes = list(common_notes(physicals, id))
    for key, start, end, targets in (
        ("outstandings", "Outstandings are", "b. ", ("outstandings",)),
        ("undrawn", "Committed undrawn balances", "1. ", ("undrawn",)),
    ):
        notes.append(note(physicals, key, 45, start, end, targets))
    notes.extend(
        (
            note(
                physicals,
                "expected-loss-definition",
                42,
                "For both non-defaulted",
                "Corporate portfolio",
                ("expected_loss",),
            ),
            note(
                physicals,
                "pd-bands",
                42,
                "Westpac’s program-",
                "For both",
                ("pd",),
            ),
        )
    )
    for key, source, start, end, targets in (
        ("ead-definition", 114, "EAD is calculated", "Geography", ("ead",)),
        (
            "pd-definition",
            114,
            "Probability of default is",
            "Substitution approach",
            ("pd",),
        ),
        (
            "lgd-definition",
            114,
            "The LGD represents",
            "Non-Performing exposures",
            ("lgd",),
        ),
        ("rwa-definition", 113, "Assets (both", "Tier 2 capital", ("rwa",)),
    ):
        notes.append(note(physicals, key, source, start, end, targets))
    notes.extend(
        (
            note(
                physicals,
                "default-definition",
                114,
                "From 1 January 2023:",
                "Defaulted but",
                ("band-7",),
                "band",
            ),
            note(
                physicals,
                "npe-definition",
                114,
                "Credit default exposures",
                "Non-Performing Exposures",
                ("band-7",),
                "band",
            ),
        )
    )
    notes = [
        replace(
            q,
            scope=q.scope
            + tuple(SourceEndpoint("band", f"band-{i}") for i in range(6)),
        )
        if q.id in ("pd-bands", "pd-definition")
        else q
        for q in notes
    ]
    bands, cells = [], []
    for i, row_label in enumerate(BANDS):
        bid = f"band-{i}"
        bounds = row_label.split(" to ") if i < 6 else (None, None)
        qs = (
            ("pd-bands", "pd-definition")
            if i < 6
            else ("default-definition", "npe-definition")
            if i == 7
            else ()
        )
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
    if day == "2024-09-30":
        keys = ("irb_rwa", "standardised_rwa")
        notes.append(
            note(
                physicals,
                "supplementary-rwa",
                page,
                "As at 30 September 2024",
                None,
                keys,
            )
        )
        for key, name in zip(
            keys,
            (
                "Residential Mortgages risk weighted assets under the IRB approach",
                "standardised approach equivalent",
            ),
            strict=True,
        ):
            f = field(
                key,
                name,
                "$m",
                page,
                "Footnote 1",
                (),
                ("supplementary-rwa",),
                form="note",
            )
            fields.append(f)
            cells.append(key)
    relationships = tuple(
        SourceRelationship(
            key,
            "total",
            name,
            SourceEndpoint("row", parent),
            tuple(SourceEndpoint("row", child) for child in children),
            (SourceEndpoint("dataset", id),),
            None,
            None,
            (ref(page, title, name),),
        )
        for key, name, parent, children in (
            ("subtotal", "Subtotal", "band-6", tuple(f"band-{i}" for i in range(6))),
            ("total", "Total", "band-8", ("band-6", "band-7")),
        )
    )
    descriptor = TemporalDescriptor(
        "measurement",
        label,
        point=day,
        point_status="established",
        evidence=(ref(page, "Panel heading"),),
    )
    return SourceTable(
        id,
        SourceTableMetadata(
            context(id, label, title, "Table 9(d)", page),
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
            (descriptor,),
            tuple(CellTemporalBinding(c, "measurement", "measurement") for c in cells),
        ),
        (),
    )


def backtesting(physicals, day, label):
    id = "table9f-" + day
    page = 58 if day == "2023-09-30" else 57
    title = "Regulatory loss estimates and actual losses"
    history_fields = (
        "predicted_pd",
        "observed_pd",
        "predicted_lgd",
        "observed_lgd",
        "ead_variance",
    )
    shared = ("backtesting-framework", "nz-history")
    specs = (
        (
            "expected_loss",
            "Regulatory Expected Lossᵃ",
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
            "Observed EAD variance to Predictedᵇ",
            "%",
            None,
            shared + ("ead-variance-method", "negative-variance"),
        ),
    )
    notes = list(common_notes(physicals, id))
    for key, source, start, end, targets in (
        (
            "backtesting-framework",
            56,
            "The table below compares",
            "Default rates",
            history_fields,
        ),
        (
            "default-rates",
            56,
            "At the start of each year",
            "Loss Given Default (LGD)",
            history_fields[:2],
        ),
        ("lgd-workout", 56, "LGD estimates are", None, history_fields[2:4]),
        (
            "ead-variance-method",
            57,
            "The EAD variance",
            "Regulatory Observed EAD",
            ("ead_variance",),
        ),
        (
            "expected-loss-population",
            page,
            "Includes regulatory expected losses",
            "b. ",
            ("expected_loss",),
        ),
        ("negative-variance", page, "A negative outcome", "c. ", ("ead_variance",)),
        ("nz-history", page, "Historical Default Rate", None, history_fields),
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
            if key in history_fields
            else ()
        )
        f = field(key, name, unit, page, title, parents + (key,), qs, attrs)
        fields.append(f)
        axes.append(axis(key, "column", name, j, page, title, parents, qs))
    descriptors = (
        TemporalDescriptor(
            "measurement",
            label,
            point=day,
            point_status="established",
            evidence=(ref(page, "Panel heading"),),
        ),
        TemporalDescriptor(
            "history",
            "since IRB accreditation; 2008 for most portfolios",
            qualification_refs=("backtesting-framework", "default-rates", "nz-history"),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "lgd-history",
            "since IRB accreditation, excluding recent defaults; two-year residential mortgage workout",
            qualification_refs=("backtesting-framework", "lgd-workout", "nz-history"),
            evidence=(ref(56, "Loss Given Default (LGD)"),),
        ),
        TemporalDescriptor(
            "ead-history",
            "all obligors that defaulted over the observation period",
            qualification_refs=(
                "backtesting-framework",
                "ead-variance-method",
                "nz-history",
            ),
            evidence=(ref(57, "Exposure at Default (EAD)"),),
        ),
        TemporalDescriptor(
            "annual-anchor",
            "At the start of each year",
            qualification_refs=("default-rates",),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "annual-outcome",
            "during the one-year period",
            duration_amount=Decimal(1),
            duration_unit="year",
            duration_status="established",
            qualification_refs=("default-rates",),
            evidence=(ref(56, "Default rates"),),
        ),
        TemporalDescriptor(
            "ead-prediction",
            "up to one year prior to default",
            qualification_refs=("ead-variance-method",),
            evidence=(ref(57, "Exposure at Default (EAD)"),),
        ),
    )
    bindings = [
        CellTemporalBinding("mortgage/expected_loss", "measurement", "measurement")
    ]
    for key in history_fields:
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
        id,
        SourceTableMetadata(
            context(id, label, title, "Table 9(f)", page),
            tuple(axes),
            tuple(fields),
            (),
            tuple(notes),
            (),
            descriptors,
            tuple(bindings),
        ),
        (),
    )


def bindings(tables, notes):
    """Bind selected 2024 panels, shared physical headers and printed notes."""
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
    common_id = "westpac-2024/common@1"
    contexts.append(ContextDefinition(common_id, attributes, evidence=common.evidence))
    comment_targets = {}
    headers = {}
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

        # The backtesting title is on page 56, preceding the continuation panels.
        title_page = 56 if backtest else page
        title_key = (title_page, "title")
        if title_key not in headers:
            heading = physical(
                f"p{title_page}/title",
                "passage",
                title_page,
                title,
                start="Regulatory loss estimates"
                if backtest
                else "Residential Mortgages portfolio",
                end="\n",
            )
            headers[title_key] = heading
            physicals.append(heading)
        bind("table", tid, headers[title_key])
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
            top = 184 if page == 57 else 124
            shift = 0 if page == 57 else -28.35
            boxes = (
                (197, top, 236, top + 31),
                (268, top + 23, 301, top + 31),
                (334, top + 23, 367, top + 31),
                (400, top + 23, 434, top + 31),
                (467, top + 23, 500, top + 31),
                (517, top, 568, top + 31),
            )
            boxes = tuple(
                (left + shift, y, right + shift, bottom)
                for left, y, right, bottom in boxes
            )
            axis_boxes = {
                "default-rate": (282 + shift, top + 12, 321 + shift, top + 20),
                "lgd": (405 + shift, top + 12, 464 + shift, top + 20),
            }
            panel_box = (
                (59, 220, 140, 229)
                if table_index == 3
                else (59, 431, 140, 440)
                if table_index == 4
                else (30, 124, 110, 132)
            )
        else:
            edges = (160, 215, 270, 315, 370, 414, 470, 525, 570)
            boxes = tuple((left, 145, right, 177) for left, right in pairwise(edges))
            axis_boxes = {}
            top = (181, 316, 452)[table_index]
            panel_box = (59, top, 140, top + 10)
        panel = physical(
            tid + "/panel", "region", page, title, box=tuple(str(v) for v in panel_box)
        )
        physicals.append(panel)
        bind("header", "panel", panel)
        for key, box in axis_boxes.items():
            header_key = (page, key)
            if header_key not in headers:
                region = physical(
                    f"p{page}/" + key,
                    "region",
                    page,
                    title,
                    box=tuple(str(v) for v in box),
                )
                headers[header_key] = region
                physicals.append(region)
            bind("header", key, headers[header_key])
        if not backtest:
            if (page, "pd-bands") not in headers:
                band_header = physical(
                    "p45/pd-bands",
                    "passage",
                    page,
                    title,
                    start="PD band",
                    end="\n",
                    after="Residential Mortgages portfolio by ",
                )
                headers[page, "pd-bands"] = band_header
                physicals.append(band_header)
            bind("header", "pd-bands", headers[page, "pd-bands"])
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
                header_key = (page, f.id + "/header")
                if header_key not in headers:
                    header = physical(
                        f"p{page}/" + f.id + "/header",
                        "region",
                        page,
                        title,
                        box=tuple(str(v) for v in boxes[j]),
                    )
                    headers[header_key] = header
                    physicals.append(header)
                path = tuple(
                    OccurrenceLink("header", address(tid, "header", p))
                    for p in f.header_path_refs[:-1]
                )
                bind("field", f.id, headers[header_key], links=path)
                bind("column", f.id, headers[header_key], links=path)
                rows = (
                    ("mortgage",) if backtest else tuple(f"band-{i}" for i in range(9))
                )
            else:
                q = f.qualification_refs[0]
                bind("field", f.id, notes[q, page])
                rows = (None,)
            for i, row in enumerate(rows):
                cid = row + "/" + f.id if row else f.id
                if row:
                    source, slot = reader, f"{i}/{j}"
                else:
                    source = physical(
                        tid + "/" + f.id,
                        "token",
                        page,
                        f.source_reference.location,
                        start="As at 30 September 2024",
                        end="",
                        pattern=r"\$([\d,]+) million",
                        index=1 if f.id == "standardised_rwa" else 0,
                    )
                    physicals.append(source)
                    slot = "text"
                roles = tuple(
                    TemporalRole(b.role, time_id, b.descriptor_ref)
                    for b in meta.temporal_bindings
                    if b.cell_id == cid
                )
                missing = (
                    "dash_unresolved"
                    if backtest and table_index in (3, 4) and f.id == "ead_variance"
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
                    ),
                )
        for q in meta.qualifications:
            source_page = q.evidence[0].pdf_page
            # Page 57 has one set of notes for both 2024 panels. The repeated
            # passage on page 58 remains its own physical comment occurrence.
            scope = tid if source_page == 58 else None
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
        "westpac-2024-capture@1", tuple(physicals), tuple(contexts), tuple(occurrences)
    )


def build():
    notes = {}
    tables = tuple(exposure(notes, day, label) for day, label in PANELS)
    tables += tuple(backtesting(notes, day, label) for day, label in PANELS)
    document = SourceDocument(
        DOCUMENT,
        "raw/westpac-2024-09-30-aps330.pdf",
        "westpac",
        "Westpac Banking Corporation",
        "September 2024 Pillar 3 Report",
        date(2024, 9, 30),
        None,
        "au",
        "https://www.westpac.com.au/content/dam/public/wbc/documents/pdf/aw/ic/wbc-pillar-3-report-september-2024.pdf",
    )
    return CaptureDefinition(
        document,
        BUNDLE,
        "extractions/au/westpac/2024-09-30/aps330/extract.py",
        tables,
        bindings(tables, notes),
    )


DEFINITION = build()
