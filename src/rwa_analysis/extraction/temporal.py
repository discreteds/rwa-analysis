"""Source-supported field timing; absent boundaries remain unresolved."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .models import SourceReference, Status


@dataclass(frozen=True)
class TemporalDescriptor:
    id: str
    source_label: str
    point: str | None = None
    start: str | None = None
    end: str | None = None
    point_status: Status = "unresolved"
    start_status: Status = "unresolved"
    end_status: Status = "unresolved"
    duration_amount: Decimal | None = None
    duration_unit: str | None = None
    duration_status: Status = "unresolved"
    qualification_refs: tuple[str, ...] = ()
    evidence: tuple[SourceReference, ...] = ()


@dataclass(frozen=True)
class TemporalBinding:
    record_id: str
    field_key: str
    role: Literal[
        "measurement",
        "cohort_anchor",
        "outcome_window",
        "history_window",
        "rating_assignment",
        "weight_measurement",
    ]
    descriptor_ref: str
