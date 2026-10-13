"""Immutable semantic catalogue contracts. References always pin a revision."""

from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from rwa_analysis.extraction.models import OccurrenceRef, Status

Kind = Literal["concept", "relationship", "measure", "decision", "mapping", "context"]


@dataclass(frozen=True)
class RevisionRef:
    kind: Kind
    revision_id: str


@dataclass(frozen=True)
class EvidenceRef:
    """An external occurrence; candidate validation binds it to selected Bronze."""

    bundle_key: str
    document_id: str
    dataset_id: str
    kind: Literal[
        "qualification",
        "field",
        "band",
        "axis",
        "context",
        "relationship",
        "comment",
        "table",
        "row",
        "column",
        "header",
        "block",
        "cell",
    ]
    ref_id: str


@dataclass(frozen=True)
class Assertion:
    value: str | int | bool | RevisionRef | EvidenceRef | None
    status: Status
    evidence_refs: tuple[EvidenceRef, ...] = ()
    decision_refs: tuple[RevisionRef, ...] = ()

    def __post_init__(self):
        if self.status in ("unresolved", "conflicting") and self.value is not None:
            raise ValueError("Unknown/conflicting assertion has a value")
        if self.status in ("established", "provisional") and self.value is None:
            raise ValueError("Known assertion requires a value")
        if any(ref.kind != "decision" for ref in self.decision_refs):
            raise ValueError("decision_refs require decision revisions")


@dataclass(frozen=True)
class SemanticAttribute(Assertion):
    name: str = ""
    alternatives: tuple[Assertion, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        if not self.name:
            raise ValueError("Empty semantic attribute name")

    def assertions(self) -> tuple[Assertion, ...]:
        return (self, *self.alternatives)


@dataclass(frozen=True, kw_only=True)
class Revision:
    id: str
    revision_id: str
    created_on: date
    effective_from: date | None
    effective_to: date | None
    evidence_refs: tuple[EvidenceRef, ...] = ()
    decision_refs: tuple[RevisionRef, ...] = ()
    supersedes_refs: tuple[RevisionRef, ...] = ()

    def __post_init__(self):
        if not self.id or not self.revision_id:
            raise ValueError("Empty revision identity")
        if (
            self.effective_from
            and self.effective_to
            and self.effective_from > self.effective_to
        ):
            raise ValueError(f"{self.revision_id}: reversed effective interval")
        if any(ref.kind != "decision" for ref in self.decision_refs):
            raise ValueError("decision_refs require decision revisions")


@dataclass(frozen=True, kw_only=True)
class ConceptRevision(Revision):
    name: str
    definition: str
    category: Literal["quantity", "unit", "population", "role", "segmentation"]


@dataclass(frozen=True, kw_only=True)
class ConceptRelationshipRevision(Revision):
    parent_ref: RevisionRef
    child_ref: RevisionRef
    relationship: Literal["specializes", "replaces", "split_from", "merged_from"]
    rationale: str


# Finite composition vocabulary. Values remain partial and source-scoped.
ATTRIBUTE_NAMES = frozenset(
    {
        "concept",
        "measure",
        "result_unit",
        "population",
        "weighting",
        "weight_measure",
        "weight_timing",
        "counted_entity",
        "distinctness",
        "exposure_basis",
        "overlay_treatment",
        "calculation_precision",
        "missingness",
        "reporting_entity",
        "consolidation_scope",
        "regulatory_scope",
        "geography",
        "currency",
        "row_role",
        "pd_band",
        "default_state",
        "population_exclusion",
        "aggregation",
        "loss_basis",
        "cohort_eligibility",
        "event_definition",
        "denominator",
        "structural_role",
        "qualification_meaning",
        "historical_review_applicability",
    }
)


def validate_attributes(attributes):
    names = [a.name for a in attributes]
    if len(names) != len(set(names)) or set(names) - ATTRIBUTE_NAMES:
        raise ValueError(f"Duplicate or unsupported semantic attributes: {names}")
    reference_kinds = {
        "weight_measure": "measure",
        "result_unit": "concept",
        "concept": "concept",
        "measure": "measure",
        "population": "concept",
    }
    for attribute in attributes:
        for a in attribute.assertions():
            if (
                attribute.name in reference_kinds
                and a.value is not None
                and (
                    not isinstance(a.value, RevisionRef)
                    or a.value.kind != reference_kinds[attribute.name]
                )
            ):
                raise ValueError(
                    f"{attribute.name} requires a {reference_kinds[attribute.name]} reference"
                )
            if (
                attribute.name == "pd_band"
                and a.value is not None
                and (not isinstance(a.value, EvidenceRef) or a.value.kind != "band")
            ):
                raise ValueError("pd_band requires a source band reference")


def revision_references(value, *, include_history=True):
    """Walk typed dependencies; historical links prove closure, not applicability."""
    if isinstance(value, RevisionRef):
        yield value
    elif is_dataclass(value):
        for field in fields(value):
            if include_history or field.name not in (
                "supersedes_refs",
                "overrides_refs",
            ):
                yield from revision_references(
                    getattr(value, field.name), include_history=include_history
                )
    elif isinstance(value, tuple):
        for item in value:
            yield from revision_references(item, include_history=include_history)


@dataclass(frozen=True, kw_only=True)
class MeasureRevision(Revision):
    concept_ref: RevisionRef
    result_unit_ref: RevisionRef
    attributes: tuple[SemanticAttribute, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        validate_attributes(self.attributes)
        if self.concept_ref.kind != "concept" or self.result_unit_ref.kind != "concept":
            raise ValueError(
                "Measure concept and result unit require concept references"
            )


@dataclass(frozen=True, kw_only=True)
class InterpretationDecisionRevision(Revision):
    interpretation: str
    rationale: str
    decision_context: str
    authority_refs: tuple[str, ...]
    decision_date: date | None = None


@dataclass(frozen=True)
class MappingScope:
    document_id: str
    document_date: date
    dataset_id: str
    template: str
    portfolio: str
    observation_from: date | None = None
    observation_to: date | None = None
    field_key: str | None = None
    published_field_ref: str | None = None
    record_id: str | None = None
    row_role: str | None = None
    band_ref: str | None = None
    reporting_entity: str | None = None
    regulatory_scope: str | None = None

    def __post_init__(self):
        if (
            self.observation_from is not None
            and self.observation_to is not None
            and self.observation_from > self.observation_to
        ):
            raise ValueError("Reversed mapping observation interval")

    def narrows(self, other: "MappingScope") -> bool:
        """Strict scope containment, never a specificity score."""
        if self == other:
            return False
        if (
            other.observation_from is not None
            and (
                self.observation_from is None
                or self.observation_from < other.observation_from
            )
        ) or (
            other.observation_to is not None
            and (
                self.observation_to is None
                or self.observation_to > other.observation_to
            )
        ):
            return False
        return all(
            getattr(other, f.name) is None
            or getattr(self, f.name) == getattr(other, f.name)
            for f in fields(self)
            if f.name not in ("observation_from", "observation_to")
        )


@dataclass(frozen=True)
class OccurrenceScope:
    targets: tuple[OccurrenceRef, ...]
    temporal_role: str = "measurement"


@dataclass(frozen=True)
class UnitConversion:
    source_unit: str
    source_scale: Decimal
    unit_factor: Decimal

    def __post_init__(self):
        if self.source_scale <= 0 or self.unit_factor <= 0:
            raise ValueError("Unit scales/factors must be positive")


@dataclass(frozen=True, kw_only=True)
class SourceMappingRevision(Revision):
    scope: MappingScope | OccurrenceScope
    concept_ref: RevisionRef | None = None
    measure_ref: RevisionRef | None = None
    attributes: tuple[SemanticAttribute, ...] = ()
    conversion: UnitConversion | None = None
    overrides_refs: tuple[RevisionRef, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        validate_attributes(self.attributes)
        for ref, kind in ((self.concept_ref, "concept"), (self.measure_ref, "measure")):
            if ref is not None and ref.kind != kind:
                raise ValueError(f"Mapping requires {kind} reference: {ref}")
        if any(r.kind not in ("mapping", "context") for r in self.overrides_refs):
            raise ValueError("Overrides require mapping references")


Member = (
    ConceptRevision
    | ConceptRelationshipRevision
    | MeasureRevision
    | InterpretationDecisionRevision
    | SourceMappingRevision
)


@dataclass(frozen=True)
class MemberSelection:
    path: str
    kind: Kind
    revision_id: str


@dataclass(frozen=True)
class CatalogueRelease:
    id: str
    schema_version: Literal["cr6-v1"]
    created_on: date
    selection: tuple[MemberSelection, ...]
    members: tuple[Member, ...]

    def member(self, ref: RevisionRef) -> Member:
        for selected, member in zip(self.selection, self.members, strict=True):
            if selected.kind == ref.kind and selected.revision_id == ref.revision_id:
                return member
        raise ValueError(f"Unresolved {ref.kind} revision: {ref.revision_id}")


@dataclass(frozen=True)
class FieldMeaning:
    concept_ref: RevisionRef | None
    measure_ref: RevisionRef | None
    mapping_refs: tuple[RevisionRef, ...]
    attributes: tuple[SemanticAttribute, ...]
    unit_factor: Decimal | None

    def attribute(self, name: str) -> SemanticAttribute:
        return next(
            (a for a in self.attributes if a.name == name),
            SemanticAttribute(name=name, value=None, status="unresolved"),
        )
