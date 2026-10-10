"""Silver owns unit conversion and publication closure, not PDF extraction.

Real saved inputs catch numeric/metadata loss. Mutations exercise publication
faults that source goldens and catalogue resolution cannot detect.
"""

from dataclasses import replace
from decimal import Decimal, localcontext

import polars as pl
import pytest


@pytest.fixture(scope="module")
def saved_inputs(tmp_path_factory, cba_bundle, westpac_bundle, nab_bundle, anz_bundle):
    from rwa_analysis.storage.bronze import load_bronze, save_bronze

    root = tmp_path_factory.mktemp("silver-bronze")
    refs = tuple(
        save_bronze(b, "v1", root, "test-r1")
        for b in (cba_bundle, westpac_bundle, nab_bundle, anz_bundle)
    )
    return tuple(load_bronze(ref, root) for ref in refs), refs


@pytest.fixture
def saved_bundles(saved_inputs):
    return saved_inputs[0]


@pytest.fixture
def bronze_refs(saved_inputs):
    return saved_inputs[1]


@pytest.fixture
def catalogue(project_root):
    from rwa_analysis.catalogue.load import load_catalogue

    return load_catalogue(project_root / "catalogue/releases/cr6-v1.json")


def observation(org, record="band-1"):
    date = "2025-06-30" if org == "cba" else "2025-09-30"
    return f"au/{org}/{date}/aps330/cr6-residential-mortgages/{record}"


def test_source_values_and_partial_semantics_survive(
    saved_bundles, bronze_refs, catalogue
):
    from rwa_analysis.normalization.cr6 import conform_cr6
    from rwa_analysis.normalization.validate import validate_candidate

    candidate = conform_cr6(saved_bundles, bronze_refs, catalogue, "test-r1")
    validate_candidate(candidate, saved_bundles, bronze_refs, catalogue)
    rows = {r["observation_id"]: r for r in candidate.tables["observations"].to_dicts()}
    cba = rows[observation("cba")]
    assert cba["ead_amount"] == Decimal(281508000000)
    assert cba["mean_pd_fraction"] == Decimal("0.0008")
    assert cba["mean_lgd_fraction"] == Decimal("0.14")
    assert cba["reported_entity_count"] == 742470
    assert cba["mean_maturity_years"] is None
    assert rows[observation("nab", "portfolio-aggregate")]["rwa_amount"] == Decimal(
        112014000000
    )
    assert rows[observation("anz", "portfolio-aggregate")]["rwa_amount"] == Decimal(
        94135000000
    )
    assert len(rows) == 36
    assert len(candidate.tables["lineage"]) == 432
    assert sum(r["segment_id"] is None for r in rows.values()) == 4
    defaults = candidate.tables["segments"].filter(pl.col("category_kind") == "default")
    assert len(defaults) == 4
    assert (
        defaults["lower_fraction"].null_count()
        == defaults["upper_fraction"].null_count()
        == 4
    )
    contexts = {
        r["organisation_id"]: r for r in candidate.tables["contexts"].to_dicts()
    }
    assert str(contexts["cba"]["observation_date"]) == "2025-06-30"
    assert str(contexts["anz"]["document_date"]) == "2025-09-30"
    assert contexts["anz"]["geography"]["status"] == "provisional"
    interpretations = {
        (r["observation_id"], r["field_key"]): r
        for r in candidate.tables["interpretations"].to_dicts()
    }
    lgd = interpretations[observation("cba"), "mean_lgd_fraction"]
    assert lgd["value_state"] == "present"
    assert (
        next(a for a in lgd["attributes"] if a["name"] == "weighting")["status"]
        == "unresolved"
    )
    assert interpretations[observation("nab"), "ead_amount"]["currency_code"] == "AUD"
    assert interpretations[observation("cba"), "ead_amount"]["currency_code"] is None
    # Independent reviewed source contracts: nine maturity and eight provision
    # omissions per bank, plus Westpac's default CCF dash (69 positions).
    expected = {
        (observation(org, row), field)
        for org in ("cba", "westpac", "nab", "anz")
        for row in (*[f"band-{n}" for n in range(1, 9)], "portfolio-aggregate")
        for field in ("mean_maturity_years", "provision_amount")
        if field == "mean_maturity_years" or row != "portfolio-aggregate"
    }
    expected.add((observation("westpac", "band-8"), "mean_ccf_fraction"))
    assert {
        key
        for key, r in interpretations.items()
        if r["value_state"] == "source_missing"
    } == expected
    lineage = {
        (r["observation_id"], r["field_key"]): r
        for r in candidate.tables["lineage"].to_dicts()
    }
    nab_density = lineage[observation("nab"), "rwa_density_fraction"]
    assert nab_density["displayed_precision"] == 1
    assert Decimal(nab_density["source_value"]) == Decimal("6.0")
    assert rows[observation("nab")]["rwa_density_fraction"] == Decimal("0.060")
    maturity = lineage[observation("anz"), "mean_maturity_years"]
    assert maturity["missing_reason"] == "not_applicable"
    assert maturity["qualification_refs"]
    assert candidate.tables["observations"].schema["ead_amount"] == pl.Decimal(22, 8)
    assert candidate.tables["observations"].schema["reported_entity_count"] == pl.Int64


def replace_cell(bundles, field, value):
    bundle = bundles[0]
    ds = bundle.datasets[0]
    row = ds.records[0]
    changed = replace(row, **{field: replace(getattr(row, field), value=value)})
    return (
        replace(bundle, datasets=(replace(ds, records=(changed, *ds.records[1:])),)),
        *bundles[1:],
    )


def test_missing_scale_blocks_only_its_conversion(
    saved_bundles, bronze_refs, catalogue
):
    from rwa_analysis.normalization.cr6 import conform_cr6

    bundle = saved_bundles[0]
    ds = bundle.datasets[0]
    binding = next(b for b in ds.bindings if b.typed_field_name == "ead")
    ds = replace(
        ds,
        published_fields=tuple(
            replace(f, source_scale=None) if f.id == binding.published_field_ref else f
            for f in ds.published_fields
        ),
    )
    bundles = (replace(bundle, datasets=(ds,)), *saved_bundles[1:])
    candidate = conform_cr6(bundles, bronze_refs, catalogue, "r")
    row = (
        candidate.tables["observations"]
        .filter(pl.col("observation_id") == observation("cba"))
        .row(0, named=True)
    )
    assert row["ead_amount"] is None
    assert row["mean_lgd_fraction"] == Decimal("0.14")
    key = (pl.col("observation_id") == observation("cba")) & (
        pl.col("field_key") == "ead_amount"
    )
    assert (
        candidate.tables["interpretations"].filter(key)["value_state"][0]
        == "not_conformed"
    )
    lineage = candidate.tables["lineage"].filter(key).row(0, named=True)
    assert lineage["source_value"] == "281508"
    assert lineage["conversion_reason"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("average_pd", Decimal("0.123456789")),
        ("average_pd", Decimal("1e-1000100")),
        ("ead", Decimal(100000000)),  # Million scale exceeds 14 integer digits.
        ("reported_borrower_count", 2**63),
        ("ead", Decimal("9999999.123456789012345")),
    ],
)
def test_unrepresentable_values_rejected_before_cast(
    saved_bundles, bronze_refs, catalogue, field, value
):
    from rwa_analysis.normalization.cr6 import conform_cr6

    with pytest.raises(ValueError, match=field):
        conform_cr6(
            replace_cell(saved_bundles, field, value), bronze_refs, catalogue, "r"
        )


@pytest.mark.parametrize(
    ("field", "target", "source", "expected"),
    [
        (
            "ead",
            "ead_amount",
            "-9999999.99999912345678",
            "-9999999999999.12345678",
        ),
        (
            "ead",
            "ead_amount",
            "10000000",
            "10000000000000",
        ),
        (
            "average_pd",
            "mean_pd_fraction",
            "0.123456",
            "0.00123456",
        ),
    ],
)
def test_domain_amounts_and_rates_are_exact_under_small_decimal_context(
    saved_bundles, bronze_refs, catalogue, field, target, source, expected
):
    from rwa_analysis.normalization.cr6 import conform_cr6

    bundles = replace_cell(saved_bundles, field, Decimal(source))
    with localcontext() as ctx:
        ctx.prec = 10
        candidate = conform_cr6(bundles, bronze_refs, catalogue, "r")
    assert candidate.tables["observations"][target][0] == Decimal(expected)
    assert candidate.tables["observations"].schema[target] == pl.Decimal(22, 8)


@pytest.mark.parametrize(
    ("table", "mutation", "error"),
    [
        ("lineage", "source_record_id", "lineage.*source_record_id"),
        ("segments", "silver_revision_id", "segments.*revision"),
        ("interpretations", "delete", "interpretations.*coverage"),
        ("interpretations", "value_state", "interpretations.*value_state"),
        (
            "interpretations",
            "measure_revision_ref",
            "interpretations.*measure_revision_ref",
        ),
        ("lineage", "source_value", "lineage.*source_value"),
        ("observations", "duplicate", "observations"),
        ("lineage", "output_version", "lineage.*output_version"),
        ("lineage", "qualification_refs", "lineage.*qualification"),
        ("applied_mappings", "mapping_revision_ref", "applied_mappings"),
        ("relationships", "child_observation_id", "relationships"),
        ("observations", "ead_amount", "observations.*ead_amount"),
    ],
)
def test_publication_rejects_broken_references_and_values(
    saved_bundles, bronze_refs, catalogue, table, mutation, error
):
    from rwa_analysis.normalization.cr6 import conform_cr6
    from rwa_analysis.normalization.validate import validate_candidate

    candidate = conform_cr6(saved_bundles, bronze_refs, catalogue, "r")
    frame = candidate.tables[table]
    if mutation == "delete":
        frame = frame.slice(1)
    elif mutation == "duplicate":
        frame = pl.concat([frame, frame.head(1)])
    else:
        rows = frame.to_dicts()
        rows[0][mutation] = (
            ["absent"]
            if mutation == "qualification_refs"
            else None
            if mutation == "ead_amount"
            else "absent"
        )
        frame = pl.DataFrame(rows, schema=frame.schema)
    candidate = replace(candidate, tables=candidate.tables | {table: frame})
    with pytest.raises(ValueError, match=error):
        validate_candidate(candidate, saved_bundles, bronze_refs, catalogue)


def test_empty_selection_has_explicit_schemas(catalogue):
    from rwa_analysis.normalization.cr6 import conform_cr6

    candidate = conform_cr6((), (), catalogue, "empty")
    assert len(candidate.tables) == 7
    assert all(
        frame.is_empty() and pl.Null not in frame.dtypes
        for frame in candidate.tables.values()
    )


def test_conflicts_retain_alternatives_and_support_without_erasing_values(
    saved_bundles, bronze_refs, catalogue
):
    from rwa_analysis.catalogue.models import MemberSelection, SemanticAttribute
    from rwa_analysis.normalization.cr6 import conform_cr6

    original = next(
        m for m in catalogue.members if m.revision_id == "cba.cr6.average_lgd@v1"
    )
    additions = tuple(
        replace(
            original,
            id=f"synthetic-{n}",
            revision_id=f"synthetic-{n}@v1",
            attributes=(
                SemanticAttribute(
                    name="weighting",
                    value=value,
                    status="established",
                    evidence_refs=original.evidence_refs,
                ),
            ),
        )
        for n, value in enumerate(("ead", "arrangement"))
    )
    cat = replace(
        catalogue,
        members=(*catalogue.members, *additions),
        selection=(
            *catalogue.selection,
            *(
                MemberSelection("synthetic", "mapping", m.revision_id)
                for m in additions
            ),
        ),
    )
    candidate = conform_cr6(saved_bundles, bronze_refs, cat, "r")
    rows = candidate.tables["interpretations"].filter(
        (pl.col("observation_id") == observation("cba"))
        & (pl.col("field_key") == "mean_lgd_fraction")
    )
    field = rows.row(0, named=True)
    weighting = next(a for a in field["attributes"] if a["name"] == "weighting")
    assert field["value_state"] == "present"
    assert weighting["status"] == "conflicting"
    assert {a["value"]["text"] for a in weighting["alternatives"]} >= {
        "ead",
        "arrangement",
    }
    assert weighting["evidence_refs"]
    assert candidate.tables["observations"]["mean_lgd_fraction"][0] == Decimal("0.14")


@pytest.mark.parametrize("broken", ["qualification", "bundle", "definition"])
def test_selected_catalogue_evidence_must_resolve_in_selected_bronze(
    saved_bundles, bronze_refs, catalogue, broken
):
    from rwa_analysis.normalization.cr6 import conform_cr6

    # Load-time closure cannot check external occurrences. Mutate support on a
    # used mapping or its referenced definition and exercise actual conformance.
    revision = (
        "cba.cr6.average_lgd@v1"
        if broken != "definition"
        else "risk.loss-given-default@v1"
    )
    member = next(m for m in catalogue.members if m.revision_id == revision)
    support = next(
        m for m in catalogue.members if m.revision_id == "cba.cr6.average_lgd@v1"
    ).evidence_refs[0]
    bad = (
        replace(support, bundle_key="au/absent/2025-06-30/aps330")
        if broken == "bundle"
        else replace(support, kind="qualification", ref_id="absent")
    )
    cat = replace(
        catalogue,
        members=tuple(
            replace(m, evidence_refs=(bad,)) if m is member else m
            for m in catalogue.members
        ),
    )
    with pytest.raises(ValueError, match="interpretations.*absent source evidence"):
        conform_cr6(saved_bundles, bronze_refs, cat, "r")
