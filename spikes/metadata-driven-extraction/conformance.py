"""DISPOSABLE: saved metadata -> existing composer -> native relations/persistence.

No PDF operations, source configuration imports, dates or financial label rules.
The composer input is deliberately a lightweight structural view, not a new codec.
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

import mountainash as ma
from mountainash.core.dtypes import DecimalDtype
from mountainash_data import IbisBackend

from metadata import Definition, Link
from rwa_analysis.catalogue.models import EvidenceRef, RevisionRef, SemanticAttribute, UnitConversion
from rwa_analysis.catalogue.resolve import compose_field
from rwa_analysis.domains.cr6.contracts import model_spec


@dataclass(frozen=True)
class CapturedRow:
    id: str
    kind: str
    position: int
    original_text: str
    source_number: Decimal | None
    value_kind: str
    unit: str
    precision: int | None
    missing_reason: str | None
    physical_binding: str
    slot: str
    pdf_page: int
    printed_page: str


@dataclass(frozen=True)
class BindingRow:
    owner: str
    definition_revision: str


@dataclass(frozen=True)
class DefinitionRow:
    revision: str
    content: str


@dataclass(frozen=True)
class AttributeRow:
    owner: str
    name: str
    value: str | None
    status: str
    evidence: str
    alternatives: str


@dataclass(frozen=True)
class ResolvedRow:
    id: str
    unit_factor: Decimal | None


def relation(model, rows):
    decimals = {"source_number": DecimalDtype(16, 8), "unit_factor": DecimalDtype(16, 8)}
    return ma.relation(rows).conform(model_spec(model, decimals=decimals))


def conform(saved, refinements=()):
    snapshot = saved["definition_snapshot"]
    definitions = {d["revision"]: Definition(**d) for d in snapshot["definitions"]}
    bindings = [BindingRow(node["id"], ref) for node in snapshot["occurrences"]
                for ref in node["definitions"]]
    for definition, targets in refinements:
        definitions[definition.revision] = definition
        bindings.extend(BindingRow(target, definition.revision) for target in targets)

    # Reuse production composition, including evidence, conflicts and explicit overrides.
    # This structural adapter avoids claiming a production all-kind catalogue format.
    contributions = {}
    kinds = {item["id"]: item["kind"] for item in saved["occurrences"]}
    for d in definitions.values():
        evidence = tuple(EvidenceRef(snapshot["bundle_key"], snapshot["document_id"],
                                    "spike", "axis" if kinds[key] in ("row", "column", "header")
                                    else "qualification", key) for key in d.evidence)
        contributions[d.revision] = SimpleNamespace(
            revision_id=d.revision,
            attributes=tuple(SemanticAttribute(name=name, value=value, status=status,
                                               evidence_refs=evidence)
                             for name, value, status in d.assertions),
            concept_ref=None, measure_ref=None, evidence_refs=evidence, decision_refs=(),
            conversion=UnitConversion(d.unit, Decimal(1), Decimal(d.factor)) if d.factor else None,
            overrides_refs=tuple(RevisionRef("mapping", ref) for ref in d.overrides),
            supersedes_refs=(),
        )
    catalogue = SimpleNamespace(member=lambda ref: contributions[ref.revision_id])
    captured, attributes, resolved = [], [], []
    for item in saved["occurrences"]:
        captured.append(CapturedRow(**{**item, "source_number":
            Decimal(item["source_number"]) if item["source_number"] is not None else None}))
        selected = [contributions[b.definition_revision] for b in bindings if b.owner == item["id"]]
        meaning = compose_field(catalogue,
            SimpleNamespace(source_unit=item["unit"], source_scale=Decimal(1)), selected, lambda ref: True)
        resolved.append(ResolvedRow(item["id"], meaning.unit_factor))
        for attribute in meaning.attributes:
            attributes.append(AttributeRow(item["id"], attribute.name, attribute.value,
                attribute.status, json.dumps([r.ref_id for r in attribute.evidence_refs]),
                json.dumps([(a.value, a.status) for a in attribute.alternatives])))

    occurrences = relation(CapturedRow, captured)
    values = (occurrences.filter(ma.col("value_kind") == "decimal")
        .join(relation(ResolvedRow, resolved), on="id")
        .with_columns((ma.col("source_number") * ma.col("unit_factor"))
                      .cast(DecimalDtype(16, 8), rounding="to_zero").alias("normalised_value")))
    return {"occurrences": occurrences, "bindings": relation(BindingRow, bindings),
            "definitions": relation(DefinitionRow, [DefinitionRow(key, json.dumps(
                {"assertions": d.assertions, "evidence": d.evidence, "unit": d.unit,
                 "factor": d.factor, "overrides": d.overrides})) for key, d in definitions.items()]),
            "links": relation(Link, [Link(**link) for link in snapshot["links"]]),
            "attributes": relation(AttributeRow, attributes), "values": values}


def publish_and_read(relations, database):
    with IbisBackend(dialect="duckdb", database=str(database)) as db:
        with db.transaction():
            for name, value in relations.items():
                db.create_table(name, value.to_pyarrow(), overwrite=True)
    with IbisBackend(dialect="duckdb", database=str(database), read_only=True) as db:
        return {name: ma.relation(ma.relation(db.table(name)).to_pyarrow()) for name in relations}
