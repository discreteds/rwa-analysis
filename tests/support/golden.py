"""Complete ordered source-payload comparison with precise mismatch paths."""


def assert_golden(actual: dict, expected: dict) -> None:
    def compare(actual, expected, path):
        assert type(actual) is type(expected), (
            f"{path}: type {type(actual)} != {type(expected)}"
        )
        if isinstance(expected, dict):
            for key in expected.keys() - actual.keys():
                raise AssertionError(f"{path + '.' if path else ''}{key}: missing key")
            for key in actual.keys() - expected.keys():
                raise AssertionError(f"{path + '.' if path else ''}{key}: unknown key")
            for key in expected:
                compare(actual[key], expected[key], f"{path}.{key}" if path else key)
        elif isinstance(expected, (list, tuple)):
            assert len(actual) == len(expected), (
                f"{path}: length {len(actual)} != {len(expected)}"
            )
            for i, (a, e) in enumerate(zip(actual, expected)):
                compare(a, e, f"{path}[{i}]")
        else:
            assert actual == expected, f"{path}: {actual!r} != {expected!r}"

    compare(actual, expected, "")


def assert_westpac_cr9(dataset, golden, cr6_golden):
    """Expand independently transcribed source expectations, not extractor output."""
    from copy import deepcopy
    from dataclasses import asdict
    from decimal import Decimal

    dataset_id = "cr9-residential-mortgages"
    expected_context = deepcopy(cr6_golden["context"])
    del expected_context["observation_date"], expected_context["source_date_label"]
    expected_context.update(
        source_template="CR9",
        source_title=golden["title"],
        source_portfolio_label=golden["portfolio"],
    )
    expected_context["regulatory_scope"]["qualification_refs"] = [
        "regulatory-basis",
        "cr9-introduction",
    ]
    expected_context["qualification_refs"] = [
        q if q != "cr6-introduction" else "cr9-introduction"
        for q in expected_context["qualification_refs"]
    ]
    expected_context["evidence"] = [ref(1, "Cover"), ref(55, "CR9 headings")]

    # JSON-like conversion here belongs to test support; it never calls the codec.
    def plain(value):
        from datetime import date

        if isinstance(value, dict):
            return {k: plain(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [plain(v) for v in value]
        if isinstance(value, (Decimal, date)):
            return str(value)
        return value

    field_notes = {
        "weighted_average_pd": ("pd-definition", "pd-long-run", "cr9-weighting"),
        "arithmetic_average_pd": ("pd-definition", "pd-long-run"),
        "defaulted_borrower_count": ("default-definition", "cr9-defaults"),
        "new_defaulted_borrower_count": ("default-definition", "cr9-defaults"),
        "historical_annual_default_rate": ("cr9-history",),
    }
    expected_axes = [
        ax("approach", "header", "A-IRB", 0),
        ax("pd-heading", "header", "PD Range", 1),
        ax("mortgage-block", "block", golden["portfolio"], 2, ("approach",)),
        ax("external-ratings", "header", "External rating equivalent", 3),
        ax("borrower-counts", "header", "Number of borrowers", 4),
    ]
    expected_fields, expected_bindings = [], []
    for i, (name, header) in enumerate(zip(golden["fields"], golden["headers"])):
        notes = field_notes.get(name, ())
        parents = (
            ("borrower-counts",)
            if name in ("previous_year_borrower_count", "current_year_borrower_count")
            else ()
        )
        expected_axes.append(
            # PDF55 places Moody's and S&P before all seven numeric columns.
            ax("column-" + name, "column", header, i + 2, parents, notes, column=header)
        )
        attrs = []
        if name == "weighted_average_pd":
            attrs = [
                {
                    "name": "weighting",
                    "value": "EAD",
                    "status": "established",
                    "qualification_refs": ["cr9-weighting"],
                }
            ]
        elif name == "arithmetic_average_pd":
            attrs = [
                {
                    "name": "weighting",
                    "value": "borrowers",
                    "status": "established",
                    "qualification_refs": [],
                }
            ]
        elif name.endswith("count"):
            attrs = [
                {
                    "name": "counted_entity",
                    "value": None,
                    "status": "unresolved",
                    "qualification_refs": [],
                }
            ]
        expected_fields.append(
            {
                "id": name,
                "source_label": header,
                "header_path_refs": [*parents, "column-" + name],
                "source_unit": "" if name.endswith("count") else "%",
                "source_scale": "1",
                "qualification_refs": list(notes),
                "attributes": attrs,
                "source_reference": ref(55, "CR9", column=header),
            }
        )
        expected_bindings.append(
            {
                "id": "binding-" + name,
                "typed_field_name": name,
                "published_field_ref": name,
                "row_refs": [f"band-{n}" for n in range(1, 9)],
                "column_refs": ["column-" + name],
                "context_refs": ["context"],
                "qualification_refs": list(notes),
            }
        )
    for i, agency in enumerate(("Moody's", "S&P")):
        expected_axes.append(
            ax(
                "rating-" + str(i),
                "column",
                agency,
                i,
                ("external-ratings",),
                column=agency,
            )
        )
    bands = []
    expected_rows = []
    for i, (label, tokens, ratings) in enumerate(
        zip(golden["bands"], golden["tokens"], golden["ratings"])
    ):
        rid = f"band-{i + 1}"
        expected_axes.append(
            ax(
                rid,
                "row",
                label,
                i,
                ("mortgage-block", "pd-heading"),
                ("default-definition",) if i == 7 else (),
                row=label,
            )
        )
        for j, rating in enumerate(ratings):
            expected_axes.append(
                ax(
                    f"{rid}-rating-{j}",
                    "header",
                    rating,
                    j,
                    (rid, f"rating-{j}"),
                    row=label,
                    column=("Moody's", "S&P")[j],
                )
            )
        bounds = label.split(" to <") if i < 7 else (None, None)
        bands.append(
            {
                "id": f"pd-band-{i + 1}",
                "source_label": label,
                "order": i,
                "kind": "interval" if i < 7 else "default",
                "unit": "%",
                "lower": bounds[0],
                "upper": bounds[1],
                "lower_inclusive": True if i < 7 else None,
                "upper_inclusive": False if i < 7 else None,
                "lower_status": "established" if i < 7 else "not_applicable",
                "upper_status": "established" if i < 7 else "not_applicable",
                "category": None if i < 7 else label,
                "source_reference": ref(55, "CR9", row=label),
            }
        )
        expected_row = {
            "record_id": rid,
            "source_row_ref": rid,
            "source_row_role": "band",
            "source_segment_memberships": [f"pd-band-{i + 1}"],
            "source_aggregation_scope": ["mortgage-block"],
        }
        for name, header, token in zip(golden["fields"], golden["headers"], tokens):
            count = name.endswith("count")
            missing = token in ("", "-")
            value = (
                None
                if missing
                else int(token.replace(",", ""))
                if count
                else token[:-1]
            )
            expected_row[name] = {
                "value": value,
                "original_text": token,
                "displayed_precision": None if missing else 0 if count else 2,
                "missing_reason": (
                    "dash_unresolved" if token == "-" else "blank_unresolved"
                )
                if missing
                else None,
                "source_reference": ref(55, "CR9", row=label, column=header),
            }
        expected_rows.append(expected_row)
    expected_segmentations = [
        {
            "id": "pd-segmentation",
            "source_dimension": "PD Range",
            "bands": bands,
            "context_refs": ["context"],
            "completeness": {
                "value": None,
                "status": "unresolved",
                "qualification_refs": [],
            },
            "disjointness": {
                "value": "Non-overlapping printed intervals and separate default category",
                "status": "established",
                "qualification_refs": [],
            },
            "evidence": [ref(55, "CR9 PD Range")],
        }
    ]
    expected_notes = []
    shared = (
        "report-entity",
        "currency",
        "rounding",
        "regulatory-basis",
        "level-2-definition",
        "level-2",
        "portfolio-definition",
        "pd-definition",
        "pd-long-run",
        "default-definition",
    )
    for q in cr6_golden["qualifications"]:
        if q["id"] not in shared:
            continue
        q = dict(q)
        if q["id"] in ("pd-definition", "pd-long-run"):
            q["scope"] = [
                {"kind": "field", "id": f}
                for f in ("weighted_average_pd", "arithmetic_average_pd")
            ]
        elif q["id"] == "default-definition":
            q["scope"] = [
                {"kind": "row", "id": "band-8"},
                {"kind": "field", "id": "defaulted_borrower_count"},
                {"kind": "field", "id": "new_defaulted_borrower_count"},
            ]
        else:
            q["scope"] = [{"kind": "dataset", "id": dataset_id}]
        expected_notes.append(q)
    for name, text in golden["notes"].items():
        scope = (
            [{"kind": "dataset", "id": dataset_id}]
            if name == "cr9-introduction"
            else [
                {"kind": "field", "id": f}
                for f, ns in field_notes.items()
                if name in ns
            ]
        )
        expected_notes.append(
            {
                "id": name,
                "source_text": text,
                "evidence": [ref(55 if name == "cr9-introduction" else 56, name)],
                "scope": scope,
            }
        )
    expected_relationships = [
        {
            "id": f"new-defaults-band-{i}",
            "kind": "subset",
            "source_label": golden["headers"][5],
            "parent": {"kind": "field", "id": "defaulted_borrower_count"},
            "children": [{"kind": "field", "id": "new_defaulted_borrower_count"}],
            "scope": [{"kind": "row", "id": f"band-{i}"}],
            "exhaustive": False,
            "mutually_exclusive": None,
            "evidence": [
                ref(55, "CR9", row=golden["bands"][i - 1], column=golden["headers"][5]),
                ref(56, "cr9-defaults"),
            ],
        }
        for i in range(1, 8)
    ]
    descriptors = []
    for id, label, changes in (
        (
            "pd-measurement",
            "June 2024",
            {
                "point": "2024-06",
                "point_status": "established",
                "qualification_refs": ["cr9-weighting"],
                "evidence": [ref(56, "cr9-weighting")],
            },
        ),
        (
            "annual",
            "1 July 2024 to 30 June 2025",
            {
                "start": "2024-07-01",
                "end": "2025-06-30",
                "start_status": "established",
                "end_status": "established",
                "duration_amount": "12",
                "duration_unit": "months",
                "duration_status": "established",
                "qualification_refs": ["cr9-introduction", "cr9-defaults"],
                "evidence": [ref(55, "cr9-introduction"), ref(56, "cr9-defaults")],
            },
        ),
        (
            "history",
            "10 years",
            {
                "duration_amount": "10",
                "duration_unit": "years",
                "duration_status": "established",
                "qualification_refs": ["cr9-history"],
                "evidence": [ref(56, "cr9-history")],
            },
        ),
        (
            "previous-year",
            "End of previous year",
            {
                "point": "2024-06-30",
                "point_status": "established",
                "qualification_refs": ["cr9-introduction"],
                "evidence": [
                    ref(55, "cr9-introduction"),
                    ref(55, "CR9", column=golden["headers"][2]),
                ],
            },
        ),
        (
            "current-year",
            "End of the year",
            {
                "point": "2025-06-30",
                "point_status": "established",
                "qualification_refs": ["cr9-introduction"],
                "evidence": [
                    ref(55, "cr9-introduction"),
                    ref(55, "CR9", column=golden["headers"][3]),
                ],
            },
        ),
        ("unspecified", "", {"evidence": [ref(55, "CR9 headings")]}),
    ):
        descriptor = {
            "id": id,
            "source_label": label,
            "point": None,
            "start": None,
            "end": None,
            "point_status": "unresolved",
            "start_status": "unresolved",
            "end_status": "unresolved",
            "duration_amount": None,
            "duration_unit": None,
            "duration_status": "unresolved",
            "qualification_refs": [],
            "evidence": [],
        }
        descriptor.update(changes)
        descriptors.append(descriptor)
    roles = (
        ("weighted_average_pd", "measurement", "pd-measurement"),
        ("weighted_average_pd", "weight_measurement", "pd-measurement"),
        ("arithmetic_average_pd", "measurement", "unspecified"),
        ("previous_year_borrower_count", "measurement", "previous-year"),
        ("current_year_borrower_count", "measurement", "current-year"),
        ("defaulted_borrower_count", "outcome_window", "annual"),
        ("new_defaulted_borrower_count", "outcome_window", "annual"),
        ("historical_annual_default_rate", "history_window", "history"),
    )
    expected_temporal_bindings = [
        {"record_id": f"band-{i}", "field_key": f, "role": r, "descriptor_ref": d}
        for i in range(1, 9)
        for f, r, d in roles
    ]
    assert_golden(
        plain(asdict(dataset)),
        {
            "id": dataset_id,
            "metadata": {
                "context": expected_context,
                "axes": expected_axes,
                "published_fields": expected_fields,
                "bindings": expected_bindings,
                "segmentations": expected_segmentations,
                "qualifications": expected_notes,
                "relationships": expected_relationships,
                "temporal_descriptors": descriptors,
                "temporal_bindings": expected_temporal_bindings,
            },
            "backtesting_rows": expected_rows,
        },
    )


def ref(page, location, row=None, column=None):
    return {
        "document_id": "westpac-2025-09-30-aps330",
        "pdf_page": page,
        "printed_page": "" if page == 1 else str(page),
        "location": location,
        "row": row,
        "column": column,
    }


def ax(id, kind, label, order, parents=(), notes=(), row=None, column=None):
    return {
        "id": id,
        "axis": kind,
        "source_label": label,
        "order": order,
        "header_path_refs": list(parents),
        "context_refs": ["context"],
        "qualification_refs": list(notes),
        "source_reference": ref(55, "CR9", row, column),
    }
