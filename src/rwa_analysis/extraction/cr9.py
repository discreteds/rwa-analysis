"""Typed CR9 source observations without a fabricated common snapshot date."""

from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal

from .datasets import DatasetMetadata
from .models import Knowledge, ReportedValue, SourceReference


@dataclass(frozen=True)
class Cr9Context:
    id: str
    document_date: date
    source_template: str
    source_title: str
    source_portfolio_label: str
    reporting_entity: Knowledge
    consolidation_scope: Knowledge
    regulatory_scope: Knowledge
    geography: Knowledge
    currency: Knowledge
    qualification_refs: tuple[str, ...]
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class Cr9BacktestingRow:
    record_id: str
    source_row_ref: str
    source_row_role: str
    source_segment_memberships: tuple[str, ...]
    source_aggregation_scope: tuple[str, ...]
    weighted_average_pd: ReportedValue[Decimal]
    arithmetic_average_pd: ReportedValue[Decimal]
    historical_annual_default_rate: ReportedValue[Decimal]
    previous_year_borrower_count: ReportedValue[int]
    current_year_borrower_count: ReportedValue[int]
    defaulted_borrower_count: ReportedValue[int]
    new_defaulted_borrower_count: ReportedValue[int]


CR9_FIELDS = tuple(f.name for f in fields(Cr9BacktestingRow)[5:])


@dataclass(frozen=True)
class Cr9Dataset:
    id: str
    metadata: DatasetMetadata[Cr9Context]
    backtesting_rows: tuple[Cr9BacktestingRow, ...]
