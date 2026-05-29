import numpy as np
import pandas as pd

from passive_market_instability.pressure import (
    assign_pressure_quintiles,
    compute_passive_pressure,
    estimate_index_weights_from_market_cap,
)


def _sample_pressure_panel():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"] * 5 + ["2024-01-02"] * 5),
            "ticker": ["A", "B", "C", "D", "E"] * 2,
            "market_cap": [50, 20, 15, 10, 5, 52, 19, 14, 10, 5],
            "rolling_adv_20d": [100, 50, 25, 20, 10, 100, 50, 25, 20, 10],
            "passive_share": [0.6] * 10,
        }
    )


def test_estimated_index_weights_sum_to_one_by_date():
    df = estimate_index_weights_from_market_cap(_sample_pressure_panel())
    sums = df.groupby("date")["index_weight_estimate"].sum()
    assert np.allclose(sums, 1.0)


def test_passive_pressure_is_finite_when_rolling_adv_is_positive():
    df = estimate_index_weights_from_market_cap(_sample_pressure_panel())
    df = compute_passive_pressure(df)
    assert np.isfinite(df["passive_pressure"]).all()


def test_pressure_quintiles_are_assigned_by_date():
    df = estimate_index_weights_from_market_cap(_sample_pressure_panel())
    df = compute_passive_pressure(df)
    df = assign_pressure_quintiles(df)
    counts = df.groupby("date")["pressure_quintile"].nunique()
    assert (counts == 5).all()
    assert set(df["pressure_quintile"].dropna().astype(int)) == {1, 2, 3, 4, 5}
