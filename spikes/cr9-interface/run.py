"""DISPOSABLE shape spike. Run with an output directory, never production data roots."""

import json
import sys
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash.relations.core.relation_api.relation import Relation
from mountainash_data import IbisBackend

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.catalogue.models import (
    MappingScope,
    SourceMappingRevision,
    UnitConversion,
)
from rwa_analysis.catalogue.resolve import compose_field
from rwa_analysis.domains.cr6.contracts import SMALL, model_spec
from rwa_analysis.domains.cr6.contracts import TABLES as CR6_TABLES
from rwa_analysis.domains.cr6.models import Cr6Output
from rwa_analysis.domains.cr6.pipeline import Cr6Pipeline
from rwa_analysis.extraction.models import PublishedField, SourceReference
from rwa_analysis.extraction.runner import run_extractor
from rwa_analysis.storage.bronze import BronzeRef, BronzeStore

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("source.json")
BUNDLE = "au/westpac/2025-09-30/aps330"
RATES = ("weighted_average_pd", "arithmetic_average_pd", "historical_annual_default_rate")


@dataclass(frozen=True)
class Cr9Numbers:
    observation_id: str
    source_row: str
    context_id: str
    weighted_average_pd: Decimal
    arithmetic_average_pd: Decimal
    previous_year_borrower_count: int
    current_year_borrower_count: int
    defaulted_borrower_count: int
    new_defaulted_borrower_count: int
    historical_annual_default_rate: Decimal


@dataclass(frozen=True)
class TemporalDescriptor:
    descriptor_id: str
    document_id: str
    pdf_page: int
    source_text: str
    interpretation_note: str = ""
    point: str | None = None
    point_status: str = "unresolved"
    start: str | None = None
    start_status: str = "unresolved"
    end: str | None = None
    end_status: str = "unresolved"
    duration: int | None = None
    duration_unit: str | None = None
    duration_status: str = "unresolved"


@dataclass(frozen=True)
class TemporalBinding:
    observation_id: str
    field_key: str
    role: str
    descriptor_id: str


@dataclass(frozen=True)
class FieldOccurrence:
    observation_id: str
    field_key: str
    published: PublishedField
    temporal: tuple[TemporalBinding, ...]


@dataclass(frozen=True)
class FieldTag:
    observation_id: str
    field_key: str
    source_token: str
    source_unit: str
    unit_factor: Decimal
    mapping_ref: str
    semantic_status: str
    document_id: str
    pdf_page: int


@dataclass(frozen=True)
class FieldRelationship:
    parent_observation_id: str
    parent_field: str
    child_observation_id: str
    child_field: str
    kind: str
    document_id: str
    pdf_page: int
    source_text: str


@dataclass(frozen=True)
class Cr9Context:
    context_id: str
    document_id: str
    document_reporting_date: date
    publication_date: date | None
    source_version: str
    source_path: str


@dataclass(frozen=True)
class Cr9Output:
    observations: Relation
    descriptors: Relation
    bindings: Relation
    fields: Relation
    relationships: Relation
    contexts: Relation


@dataclass(frozen=True)
class Candidate:
    cr6: Cr6Output
    cr9: Cr9Output


# Same declared-inventory pattern as CR6, not a plugin mechanism.
CR9_MODELS = {
    "observations": Cr9Numbers,
    "descriptors": TemporalDescriptor,
    "bindings": TemporalBinding,
    "fields": FieldTag,
    "relationships": FieldRelationship,
    "contexts": Cr9Context,
}
CR9_SPECS = {
    name: model_spec(model, decimals={**dict.fromkeys(RATES, SMALL), "unit_factor": SMALL})
    for name, model in CR9_MODELS.items()
}
INVENTORY = tuple(("cr6", t.member, t.table) for t in CR6_TABLES) + tuple(
    ("cr9", name, f"cr9_{name}") for name in CR9_MODELS
)


def conform_cr9(source, catalogue):
    """One hand-reviewed row: explicit occurrence mappings, no financial inference."""
    oid = f"{BUNDLE}/{source['dataset_id']}/{source['record_id']}"
    descriptors = tuple(
        replace(TemporalDescriptor(document_id=source["document_id"], **item),
                descriptor_id=f"{BUNDLE}/{source['dataset_id']}/{item['descriptor_id']}")
        for item in source["temporal"]
    )
    bindings = tuple(TemporalBinding(oid, field, role, f"{BUNDLE}/{source['dataset_id']}/{ref}")
                     for field, role, ref in source["bindings"])
    tags, factors = [], {}
    for name, token in source["values"].items():
        unit = "%" if name in RATES else "#"
        published = PublishedField(
            name, source["labels"][name], (), unit, Decimal(1), (), (),
            SourceReference(source["document_id"], 55, "55", "CR9 mortgage first band", column=name),
        )
        occurrence = FieldOccurrence(oid, name, published, tuple(b for b in bindings if b.field_key == name))
        # Explicit source-unit mappings are local spike inputs, not approved catalogue assets.
        mapping = SourceMappingRevision(
            id=f"spike/{name}", revision_id=f"spike/{name}@v1",
            created_on=date(2026, 10, 12), effective_from=None, effective_to=None,
            scope=MappingScope(source["document_id"], date(2025, 9, 30),
                               source["dataset_id"], "CR9", "Residential Mortgages",
                               None, None, field_key=name, record_id=source["record_id"]),
            conversion=UnitConversion(unit, Decimal(1), Decimal("0.01") if name in RATES else Decimal(1)),
        )
        # No definition references are introduced here; date-restricted ones would not apply.
        def undated_definition(ref):
            member = catalogue.member(ref)
            return member.effective_from is None and member.effective_to is None

        meaning = compose_field(catalogue, occurrence.published, [mapping], undated_definition)
        factors[name] = meaning.unit_factor
        tags.append(FieldTag(oid, name, token, unit, meaning.unit_factor,
                             meaning.mapping_refs[0].revision_id,
                             meaning.attribute("measure").status, source["document_id"], 55))

    numeric = Cr9Numbers(oid, source["source_row"], f"{BUNDLE}/{source['dataset_id']}", **{
        name: Decimal(token) if name in RATES else int(token)
        for name, token in source["values"].items()
    })
    observations = ma.relation([numeric]).with_columns(*(
        (ma.col(name).cast(pl.Decimal(38, 8)) *
         ma.lit(factors[name]).cast(pl.Decimal(38, 8))).alias(name) for name in RATES
    )).conform(CR9_SPECS["observations"])
    relationship = FieldRelationship(
        oid, "defaulted_borrower_count", oid, "new_defaulted_borrower_count", "subset",
        source["document_id"], 56, source["qualifications"][1],
    )
    context = Cr9Context(f"{BUNDLE}/{source['dataset_id']}", source["document_id"],
                         date.fromisoformat(source["document_reporting_date"]), None,
                         "disposable-shape-v1", "cr9-source-shape.json")
    return Cr9Output(observations, *(
        ma.relation(list(rows)).conform(CR9_SPECS[name])
        for name, rows in (("descriptors", descriptors), ("bindings", bindings),
                           ("fields", tags), ("relationships", [relationship]), ("contexts", [context]))
    ))


def persist_readback(candidate, database):
    with IbisBackend(dialect="duckdb", database=str(database)) as db:
        if "silver" not in db.list_namespaces():
            db.ibis_connection().create_database("silver")
        with db.transaction():
            for domain, member, table in INVENTORY:
                db.create_table(table, getattr(getattr(candidate, domain), member).to_pyarrow(),
                                namespace="silver", overwrite=True)
    with IbisBackend(dialect="duckdb", database=str(database), read_only=True) as db:
        values = {domain: {} for domain in ("cr6", "cr9")}
        for domain, member, table in INVENTORY:
            values[domain][member] = ma.relation(ma.relation(db.table(table, namespace="silver")).to_polars())
    return Candidate(Cr6Output(**values["cr6"]), Cr9Output(**values["cr9"]))


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    store = BronzeStore(output / "bronze")
    ref = BronzeRef(BUNDLE, "spike-input")
    if not (output / "bronze" / BUNDLE / "spike-input" / "bundle.json").exists():
        bundle = run_extractor(ROOT / "extractions" / BUNDLE / "extract.py",
                               ROOT / "raw/westpac-2025-09-30-aps330.pdf")
        store.save(bundle, "spike-input")
    # A saved CR9 shape input, explicitly separate from the retained cr6-v1 codec.
    saved_source = output / "cr9-source-shape.json"
    saved_source.write_text(SOURCE.read_text())
    source = json.loads(saved_source.read_text())
    catalogue = load_catalogue(ROOT / "catalogue/releases/cr6-v1.json")
    candidate = Candidate(Cr6Pipeline().conform((store.load(ref),), catalogue),
                          conform_cr9(source, catalogue))
    saved = persist_readback(candidate, output / "shape.duckdb")

    # Executable observations, not a test suite or a publication gate.
    print("Persisted/read back", len(INVENTORY), "relations")
    for table in CR6_TABLES:
        baseline = output / "baseline" / f"{table.table}.parquet"
        if baseline.exists():
            equal = getattr(saved.cr6, table.member).to_polars().equals(pl.read_parquet(baseline))
            print("CR6 baseline", table.member, equal)
    linked = saved.cr9.bindings.join(saved.cr9.descriptors, on="descriptor_id")
    print(linked.select("field_key", "role", "point", "start", "end", "duration", "end_status").to_polars())
    restored = saved.cr9.observations.with_columns(*(
        (ma.col(name).cast(pl.Decimal(38, 8)) *
         ma.lit(Decimal(100)).cast(pl.Decimal(38, 8))).alias(name) for name in RATES
    )).to_polars()
    print("Source-shaped values from DuckDB:", restored.to_dicts())
    print("Field subset:", saved.cr9.relationships.to_polars().to_dicts())

    # Small additional source shapes: no inferred end of CBA history; ANZ is an aggregate.
    cba = TemporalDescriptor("cba-history", "cba-2025-06-30-aps330", 60,
                             "calculated using data from 2014", start="2014", start_status="established")
    anz = TemporalDescriptor("anz-history", "anz-2025-09-30-aps330", 66,
                             "5-year default rate history", duration=5, duration_unit="years",
                             duration_status="established")
    print("Other temporal shapes:", ma.relation([cba, anz]).conform(CR9_SPECS["descriptors"]).to_polars())
    aggregate = Cr9Numbers("anz/cr9/subtotal", "Sub-Total AIRB Residential Mortgage", "anz/cr9",
                           Decimal("0.82"), Decimal("0.79"), 927798, 919180, 7840, 129, Decimal("0.62"))
    print("ANZ aggregate shape:", ma.relation([aggregate]).with_columns(*(
        (ma.col(name).cast(pl.Decimal(38, 8)) *
         ma.lit(Decimal("0.01")).cast(pl.Decimal(38, 8))).alias(name) for name in RATES
    )).conform(CR9_SPECS["observations"]).to_polars().to_dicts())
    summary = {"disposable": True, "database": str(output / "shape.duckdb"),
               "source_readback": restored.to_dicts(),
               "relations": len(INVENTORY), "cr9_semantics": "unresolved; unit conversion only"}
    (output / "result.json").write_text(json.dumps(summary, default=str, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
