"""Cross-bank cases that differ in timing, column order and aggregate grain."""

from decimal import Decimal

import polars as pl
import pytest

from rwa_analysis.catalogue.load import load_catalogue
from rwa_analysis.domains.cr9.pipeline import Cr9Pipeline
from rwa_analysis.domains.cr9.reconstruction import reconstruct_cr9
from rwa_analysis.storage.bronze import BronzeStore


@pytest.mark.parametrize("bank", ["cba", "nab", "anz"])
def test_bank_specific_cr9_meaning(bank, request, project_root, tmp_path):
    bundle = request.getfixturevalue(f"{bank}_bundle")
    datasets = [d for d in bundle.datasets if hasattr(d, "backtesting_rows")]
    assert len(datasets) == 1, f"{bank} must retain its selected CR9 block"
    ds = datasets[0]
    store = BronzeStore(tmp_path / "bronze")
    ref = store.save(bundle, "review")
    output = Cr9Pipeline().conform(
        (store.load(ref),),
        load_catalogue(project_root / "catalogue/releases/cr6-cr9-v1.json"),
    )
    observed = output.observations.to_polars()
    first = observed.filter(
        pl.col("source_record_id") == ds.backtesting_rows[0].record_id
    ).row(0, named=True)
    timing = output.temporal_bindings.join(
        output.temporal_descriptors, on="descriptor_id"
    ).to_polars()
    first_timing = timing.filter(pl.col("observation_id") == first["observation_id"])
    if bank == "cba":
        assert observed.height == 8
        assert first["historical_annual_default_rate"] == Decimal("0.0007")
        history = first_timing.filter(pl.col("role") == "history_window")
        assert history["start"].item() == "2014"
        assert history["end"].item() is None
        annual = first_timing.filter(
            (pl.col("field_key") == "defaulted_borrower_count")
            & (pl.col("role") == "outcome_window")
        )
        assert annual["start"].item() == "2024-04-01"
        assert annual["end"].item() == "2025-03-31"
    elif bank == "nab":
        assert observed.height == 8
        assert first["current_year_borrower_count"] == 198124
        assert first["previous_year_borrower_count"] == 215531
        for field, point in [
            ("current_year_borrower_count", "2025-09-30"),
            ("previous_year_borrower_count", "2024-09-30"),
        ]:
            assert (
                first_timing.filter(
                    (pl.col("field_key") == field) & (pl.col("role") == "measurement")
                )["point"].item()
                == point
            )
        table = next(iter(reconstruct_cr9(output, (bundle,)).values()))
        assert table.row(0)[3:5] == (198124, 215531)
    else:
        assert observed.height == 9
        subtotal = observed.filter(
            pl.col("source_record_id") == ds.backtesting_rows[-1].record_id
        ).row(0, named=True)
        assert subtotal["historical_annual_default_rate"] == Decimal("0.0062")
        history = timing.filter(
            (pl.col("observation_id") == subtotal["observation_id"])
            & (pl.col("role") == "history_window")
        )
        assert history["duration_amount"].item() == Decimal(5)
        assert history["end"].item() is None
