"""DISPOSABLE: reviewed source configuration, binding reusable metadata to ANZ."""

from metadata import Definition, Extraction, Link, Occurrence, Physical, PERCENT, RATIO, ROLES


PHYSICAL = (
    Physical("title", "line", 56, "55", {"prefix": "Table 9(f)"}),
    Physical("panel", "line", 56, "55", {"prefix": "Sep 23"}),
    Physical("mortgage", "numeric_row", 56, "55", {"prefix": "Residential Mortgage", "count": 5}),
    Physical("headers", "crops", 56, "55", {
        "boxes": ((235, 96, 295, 129), (295, 96, 353, 129), (353, 96, 414, 129),
                  (414, 96, 474, 129), (474, 96, 533, 129)),
    }),
    Physical("framework", "passage", 56, "55", {
        "after": "", "start": "APS 330 Table 9(f)", "end": "Estimated PD and LGD",
    }),
    Physical("pd", "passage", 56, "55", {
        "after": "Retail Portfolios", "start": "The estimated PD", "end": "The EAD ratio",
    }),
    Physical("ead", "passage", 56, "55", {
        "after": "Retail Portfolios", "start": "The EAD ratio", "end": "The estimated LGD",
    }),
    Physical("lgd", "passage", 56, "55", {
        "after": "Retail Portfolios", "start": "The estimated LGD", "end": "\n55",
    }),
    Physical("review", "passage", 56, "55", {
        "after": "", "start": "A review of historical", "end": "Retail Portfolios",
    }),
    Physical("matrix", "ruled_matrix", 45, "44", {
        "edges": (78.84, 175.98, 367.44, 449.76, 532.44),
        "rows": (("mortgage", "Residential Mortgages", "Remains post-January"),
                 ("nz", "Exposures of New", "New from January")),
    }),
)

DEFINITIONS = (*ROLES, PERCENT, RATIO,
    Definition("anz.pd-history@1", (("history_start", "2018", "established"),
        ("history_end", "2022", "established")), ("comment/pd",)),
    Definition("anz.ead-history@1", (("history_start", "2018", "established"),
        ("history_end", "2023", "established")), ("comment/ead",)),
    Definition("anz.lgd-history@1", (("history_start", "2017", "established"),
        ("history_end", "2021", "established")), ("comment/lgd",)),
    Definition("anz.pd-outcome@1", (("outcome_end", "2023-09", "established"),), ("comment/pd",)),
    Definition("anz.lgd-outcome@1", (("outcome_end", "2022-09", "established"),), ("comment/lgd",)),
    Definition("anz.portfolio@1", (("portfolio", "Residential Mortgage", "established"),), ("row/mortgage",)),
    Definition("anz.backtesting@1", (("purpose", "estimated versus realised credit risk", "established"),), ("comment/framework",)),
    Definition("anz.matrix@1", (("purpose", "pre/post January 2023 rating approach", "established"),)),
    Definition("anz.wholesale-review@1", (("mortgage_applicability", None, "unresolved"),), ("comment/review",)),
    # Deliberately partial interpretation for the later saved-Bronze refinement.
    Definition("anz.actual-lgd-loss@1", (("loss_basis", None, "unresolved"),), ("comment/lgd",)),
)

FIELDS = (
    ("estimated_pd", PERCENT, ("anz.pd-history@1",)),
    ("actual_pd", PERCENT, ("anz.pd-history@1", "anz.pd-outcome@1")),
    ("ead_ratio", RATIO, ("anz.ead-history@1",)),
    ("estimated_lgd", PERCENT, ("anz.lgd-history@1", "anz.lgd-outcome@1")),
    ("actual_lgd", PERCENT, ("anz.lgd-history@1", "anz.lgd-outcome@1",
                            "anz.actual-lgd-loss@1", "anz.wholesale-review@1")),
)


def node(id, kind, physical, slot="text", definitions=(), value_kind="text", unit=""):
    return Occurrence(id, kind, physical, slot, (f"role.{kind}@1", *definitions), value_kind, unit)


nodes = [node("table/backtesting", "table", "title", definitions=("anz.backtesting@1",)),
         node("header/panel", "header", "panel"),
         node("row/mortgage", "row", "mortgage", "label", ("anz.portfolio@1",))]
links = [Link("header/panel", "within", "table/backtesting"),
         Link("row/mortgage", "within", "table/backtesting")]
for name in ("framework", "pd", "ead", "lgd", "review"):
    nodes.append(node(f"comment/{name}", "comment", name,
                      definitions=("anz.wholesale-review@1",) if name == "review" else ()))
links.append(Link("comment/framework", "qualifies", "table/backtesting"))
for i, (key, conversion, context) in enumerate(FIELDS):
    for kind, physical, slot in (("field", "headers", str(i)), ("column", "headers", str(i)),
                                  ("cell", "mortgage", str(i))):
        nodes.append(node(f"{kind}/{key}", kind, physical, slot,
                          (conversion.revision, "anz.portfolio@1", *context),
                          "decimal" if kind == "cell" else "text", conversion.unit))
        links.append(Link(f"{kind}/{key}", "within", "table/backtesting"))
    links.extend((Link(f"cell/{key}", "field", f"field/{key}"),
                  Link(f"cell/{key}", "row", "row/mortgage"),
                  Link(f"cell/{key}", "column", f"column/{key}"),
                  Link(f"column/{key}", "header", "header/panel")))
    comment = "pd" if key.endswith("pd") else "ead" if key == "ead_ratio" else "lgd"
    links.append(Link(f"comment/{comment}", "qualifies", f"field/{key}"))

# The matrix is a structural slice, not additional mortgage exposure observations.
nodes.append(node("table/matrix", "table", "matrix", "title", ("anz.matrix@1",)))
for i in range(4):
    nodes.append(node(f"matrix/column/{i}", "column", "matrix", f"header/{i}"))
    links.append(Link(f"matrix/column/{i}", "within", "table/matrix"))
for row in ("mortgage", "nz"):
    nodes.extend((node(f"matrix/row/{row}", "row", "matrix", f"{row}/0"),
                  node(f"matrix/header/{row}", "header", "matrix", f"{row}/section"),
                  node(f"comment/matrix-{row}", "comment", "matrix", row)))
    links.extend((Link(f"matrix/row/{row}", "within", "table/matrix"),
                  Link(f"matrix/header/{row}", "within", "table/matrix"),
                  Link(f"comment/matrix-{row}", "describes", f"matrix/row/{row}")))
    for i in range(4):
        nodes.append(node(f"matrix/cell/{row}/{i}", "cell", "matrix", f"{row}/{i}"))
        links.extend((Link(f"matrix/cell/{row}/{i}", "row", f"matrix/row/{row}"),
                      Link(f"matrix/cell/{row}/{i}", "column", f"matrix/column/{i}"),
                      Link(f"matrix/cell/{row}/{i}", "header", f"matrix/header/{row}")))

EXTRACTION = Extraction("anz-2023-spike@1", "au/anz/2023-09-30/aps330",
    "anz-2023-09-30-aps330", "raw/anz-2023-09-30-aps330.pdf", PHYSICAL,
    tuple(nodes), DEFINITIONS, tuple(links))

# Source-supported enrichment, not a fabricated numerical change or production mapping.
REFINEMENT = Definition("anz.actual-lgd-loss@2",
    (("loss_basis", "average realised losses", "established"),),
    ("comment/lgd",), overrides=("anz.actual-lgd-loss@1",))
REFINEMENT_TARGETS = ("field/actual_lgd", "column/actual_lgd", "cell/actual_lgd")
