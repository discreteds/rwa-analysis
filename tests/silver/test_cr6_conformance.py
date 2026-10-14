"""Independent numerical and source-semantic proof at the CR6 domain boundary."""

from dataclasses import asdict, replace
from decimal import Decimal, localcontext

import mountainash as ma
import polars as pl
import pytest


@pytest.fixture(scope="module")
def inputs(tmp_path_factory, cba_bundle, westpac_bundle, nab_bundle, anz_bundle):
    from rwa_analysis.storage.bronze import BronzeStore

    store = BronzeStore(tmp_path_factory.mktemp("silver-bronze"))
    return tuple(
        store.load(store.save(bundle, "v1"))
        for bundle in (cba_bundle, westpac_bundle, nab_bundle, anz_bundle)
    )


@pytest.fixture
def catalogue(project_root):
    from rwa_analysis.catalogue.load import load_catalogue

    return load_catalogue(project_root / "catalogue/releases/cr6-v1.json")


def conform(inputs, catalogue):
    from rwa_analysis.domains.cr6.projection import project_cr6
    from rwa_analysis.domains.source_tables.legacy import domain_bindings
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline

    return project_cr6(
        SourceTablePipeline().conform(inputs, catalogue),
        tuple(b for loaded in inputs for b in domain_bindings(loaded.bundle)),
    )


def observation(org, record="band-1"):
    date = "2025-06-30" if org == "cba" else "2025-09-30"
    return f"au/{org}/{date}/aps330/cr6-residential-mortgages/{record}"


def test_source_values_and_partial_semantics_survive(inputs, catalogue):
    from rwa_analysis.domains.cr6.contracts import TABLES
    from rwa_analysis.domains.cr6.models import SilverObservation

    output = conform(inputs, catalogue)
    rows = {
        r.observation_id: asdict(r)
        for r in output.observations.to_dataclasses(
            SilverObservation, spec=TABLES[0].spec
        )
    }
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
    assert output.fields.count_rows() == 432
    assert sum(r["segment_id"] is None for r in rows.values()) == 4
    defaults = output.observations.filter(
        ma.col("category_kind") == "default"
    ).to_polars()
    assert len(defaults) == 4
    assert (
        defaults["lower_fraction"].null_count()
        == defaults["upper_fraction"].null_count()
        == 4
    )
    contexts = {r["organisation_id"]: r for r in output.contexts.to_dicts()}
    assert str(contexts["cba"]["observation_date"]) == "2025-06-30"
    assert str(contexts["anz"]["document_date"]) == "2025-09-30"
    assert contexts["anz"]["geography_status"] == "provisional"
    fields = {
        (r["observation_id"], r["field_key"]): r for r in output.fields.to_dicts()
    }
    lgd = fields[observation("cba"), "mean_lgd_fraction"]
    assert lgd["value_state"] == "present"
    assert (
        output.attributes.filter(
            (ma.col("observation_id") == observation("cba"))
            & (ma.col("field_key") == "mean_lgd_fraction")
            & (ma.col("name") == "weighting")
            & (ma.col("assertion_index") == 0)
        ).item("status")
        == "unresolved"
    )
    assert fields[observation("nab"), "ead_amount"]["currency_code"] == "AUD"
    assert fields[observation("cba"), "ead_amount"]["currency_code"] is None
    # Nine maturity and eight provision omissions per bank, plus WBC default CCF.
    expected = {
        (observation(org, row), field)
        for org in ("cba", "westpac", "nab", "anz")
        for row in (*[f"band-{n}" for n in range(1, 9)], "portfolio-aggregate")
        for field in ("mean_maturity_years", "provision_amount")
        if field == "mean_maturity_years" or row != "portfolio-aggregate"
    }
    expected.add((observation("westpac", "band-8"), "mean_ccf_fraction"))
    assert {
        key for key, r in fields.items() if r["value_state"] == "source_missing"
    } == expected
    density = fields[observation("nab"), "rwa_density_fraction"]
    assert density["displayed_precision"] == 1
    assert Decimal(density["source_value"]) == Decimal("6.0")
    assert rows[observation("nab")]["rwa_density_fraction"] == Decimal("0.060")
    maturity = fields[observation("anz"), "mean_maturity_years"]
    assert maturity["missing_reason"] == "not_applicable"
    assert (
        output.field_qualifications.filter(
            (ma.col("observation_id") == maturity["observation_id"])
            & (ma.col("field_key") == maturity["field_key"])
        ).count_rows()
        > 0
    )
    schema = output.observations.to_polars().schema
    assert schema["ead_amount"] == pl.Decimal(16, 2)
    assert schema["mean_pd_fraction"] == pl.Decimal(16, 8)
    assert schema["reported_entity_count"] == pl.Int64
    assert output.field_mappings.count_rows() == 1296
    assert output.relationships.count_rows() == 32


def replace_dataset(inputs, dataset):
    return (
        replace(inputs[0], bundle=replace(inputs[0].bundle, datasets=(dataset,))),
        *inputs[1:],
    )


def test_missing_scale_blocks_only_its_conversion(inputs, catalogue):
    ds = inputs[0].bundle.datasets[0]
    binding = next(b for b in ds.metadata.bindings if b.typed_field_name == "ead")
    ds = replace(
        ds,
        metadata=replace(
            ds.metadata,
            published_fields=tuple(
                replace(f, source_scale=None)
                if f.id == binding.published_field_ref
                else f
                for f in ds.metadata.published_fields
            ),
        ),
    )
    output = conform(replace_dataset(inputs, ds), catalogue)
    row = output.observations.filter(
        ma.col("observation_id") == observation("cba")
    ).to_dicts()[0]
    assert row["ead_amount"] is None
    assert row["mean_lgd_fraction"] == Decimal("0.14")
    field = output.fields.filter(
        (ma.col("observation_id") == observation("cba"))
        & (ma.col("field_key") == "ead_amount")
    ).to_dicts()[0]
    assert field["value_state"] == "not_conformed"
    assert field["source_value"] == "281508"
    assert field["conversion_reason"]


@pytest.mark.parametrize(
    ("field", "target", "source", "expected"),
    [
        ("ead", "ead_amount", "-9999999.99999912345678", "-9999999999999.12"),
        ("ead", "ead_amount", "10000000", "10000000000000"),
        ("average_pd", "mean_pd_fraction", "0.123456", "0.00123456"),
    ],
)
def test_domain_amounts_and_rates_under_small_decimal_context(
    inputs, catalogue, field, target, source, expected
):
    ds = inputs[0].bundle.datasets[0]
    row = ds.exposure_rows[0]
    row = replace(row, **{field: replace(getattr(row, field), value=Decimal(source))})
    ds = replace(ds, exposure_rows=(row, *ds.exposure_rows[1:]))
    with localcontext() as ctx:
        ctx.prec = 10
        output = conform(replace_dataset(inputs, ds), catalogue)
    assert output.observations.filter(
        ma.col("observation_id") == observation("cba")
    ).item(target) == Decimal(expected)
    assert output.observations.to_polars().schema[target] == pl.Decimal(
        16, 2 if target == "ead_amount" else 8
    )


def test_empty_selection_has_explicit_schemas(catalogue):
    from rwa_analysis.domains.cr6.contracts import TABLES

    output = conform((), catalogue)
    assert all(
        frame.is_empty() and pl.Null not in frame.dtypes
        for frame in (getattr(output, table.member).to_polars() for table in TABLES)
    )


def test_projection_consumes_resolved_results_without_recomputing(inputs, catalogue):
    from rwa_analysis.domains.cr6.projection import project_cr6
    from rwa_analysis.domains.source_tables.legacy import domain_bindings
    from rwa_analysis.domains.source_tables.pipeline import SourceTablePipeline

    source = SourceTablePipeline().conform(inputs[:1], catalogue)
    ead = ma.col("cell_id") == "band-1/ead"
    count = ma.col("cell_id") == "band-1/reported_borrower_count"
    changed = replace(
        source,
        meanings=source.meanings.with_columns(
            ma.when(ead)
            .then(ma.lit(Decimal("123.45")))
            .otherwise(ma.col("normalised_amount"))
            .alias("normalised_amount"),
            ma.when(count)
            .then(9007199254740993)
            .otherwise(ma.col("normalised_count"))
            .alias("normalised_count"),
            ma.when(ead | count)
            .then(ma.lit(Decimal(2)))
            .otherwise(ma.col("unit_factor"))
            .alias("unit_factor"),
        ),
    )
    output = project_cr6(changed, domain_bindings(inputs[0].bundle))
    row = output.observations.filter(ma.col("source_record_id") == "band-1")
    assert row.item("ead_amount") == Decimal("123.45")
    assert row.item("reported_entity_count") == 9007199254740993
    field = output.fields.filter(
        (ma.col("source_record_id") == "band-1") & (ma.col("field_key") == "ead_amount")
    )
    assert field.item("source_value") == "281508"
    assert Decimal(field.item("unit_factor")) == 2


def test_conflicts_retain_alternatives_without_erasing_values(inputs, catalogue):
    from rwa_analysis.catalogue.models import (
        InterpretationDecisionRevision,
        MemberSelection,
        RevisionRef,
        SemanticAttribute,
    )

    original = next(
        m for m in catalogue.members if m.revision_id == "cba.cr6.average_lgd@v1"
    )
    decision = replace(
        next(
            m
            for m in catalogue.members
            if isinstance(m, InterpretationDecisionRevision)
        ),
        id="synthetic-storage-decision",
        revision_id="synthetic-storage-decision@v1",
        effective_from=None,
        effective_to=None,
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
                    decision_refs=(RevisionRef("decision", decision.revision_id),),
                ),
                SemanticAttribute(
                    name="calculation_precision", value=8, status="established"
                ),
                SemanticAttribute(
                    name="distinctness", value=False, status="established"
                ),
            ),
        )
        for n, value in enumerate(("ead", "arrangement"))
    )
    cat = replace(
        catalogue,
        members=(*catalogue.members, decision, *additions),
        selection=(
            *catalogue.selection,
            MemberSelection("synthetic", "decision", decision.revision_id),
            *(
                MemberSelection("synthetic", "mapping", m.revision_id)
                for m in additions
            ),
        ),
    )
    output = conform(inputs, cat)
    field = output.fields.filter(
        (ma.col("observation_id") == observation("cba"))
        & (ma.col("field_key") == "mean_lgd_fraction")
    ).to_dicts()[0]
    key = (
        (ma.col("observation_id") == observation("cba"))
        & (ma.col("field_key") == "mean_lgd_fraction")
        & (ma.col("name") == "weighting")
    )
    weighting = output.attributes.filter(key)
    assert field["value_state"] == "present"
    assert (
        weighting.filter(ma.col("assertion_index") == 0).item("status") == "conflicting"
    )
    assert {
        a["value_text"]
        for a in weighting.filter(ma.col("assertion_index") > 0).to_dicts()
    } >= {
        "ead",
        "arrangement",
    }
    assert output.attribute_evidence.filter(key).count_rows() > 0
    assert {
        r["decision_revision_id"]
        for r in output.attribute_decisions.filter(key).to_dicts()
    } == {decision.revision_id}
    typed = output.attributes.filter(
        (ma.col("observation_id") == observation("cba"))
        & (ma.col("field_key") == "mean_lgd_fraction")
        & (ma.col("assertion_index") == 0)
    )
    assert (
        typed.filter(ma.col("name") == "calculation_precision").item("value_integer")
        == 8
    )
    assert typed.filter(ma.col("name") == "distinctness").item("value_boolean") is False
    assert output.observations.filter(
        ma.col("observation_id") == observation("cba")
    ).item("mean_lgd_fraction") == Decimal("0.14")
