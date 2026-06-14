"""Unit tests for the pure walk-forward analysis module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agent_graph_system.analysis.walkforward import (
    InsufficientDataError,
    WalkforwardResult,
    cagr,
    max_drawdown,
    run_walkforward,
    sharpe_ratio,
)


def _series(years: float, mu: float = 0.0005, sigma: float = 0.01, seed: int = 0) -> pd.Series:
    n = int(round(years * 252))
    idx = pd.bdate_range("2018-01-01", periods=n)
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mu, sigma, n), index=idx)


def test_window_count_and_indices():
    # 4y of data, train 12m / test 3m / step 3m → windows every quarter after
    # the first training year, each needing a full 3m test slice ahead of it.
    result = run_walkforward(_series(4), train_months=12, test_months=3, step_months=3)
    assert isinstance(result, WalkforwardResult)
    assert len(result.windows) >= 4
    assert [w.window_index for w in result.windows] == list(range(len(result.windows)))


def test_test_windows_are_non_overlapping():
    result = run_walkforward(_series(5), train_months=12, test_months=3, step_months=3)
    bounds = [(w.test_start, w.test_end) for w in result.windows]
    for (_, end), (nxt_start, _) in zip(bounds, bounds[1:]):
        assert end <= nxt_start, f"test windows overlap: {end} > {nxt_start}"


def test_overlapping_step_is_rejected():
    with pytest.raises(ValueError, match="overlap"):
        run_walkforward(_series(4), train_months=12, test_months=3, step_months=1)


def test_insufficient_data_raises():
    with pytest.raises(InsufficientDataError):
        run_walkforward(_series(1.2), train_months=12, test_months=3, step_months=3, min_windows=4)


def test_requires_datetime_index():
    s = pd.Series(np.zeros(500))  # RangeIndex
    with pytest.raises(TypeError):
        run_walkforward(s)


def test_aggregate_metrics_on_constant_positive_series():
    # A constant small positive daily return: deterministic, easy to verify.
    # Zero variance means Sharpe is undefined and reported as 0.0 (not positive),
    # so positive-Sharpe windows are zero even though every window is profitable.
    idx = pd.bdate_range("2018-01-01", periods=252 * 4)
    s = pd.Series(np.full(len(idx), 0.001), index=idx)
    result = run_walkforward(s, train_months=12, test_months=3, step_months=3)
    assert result.pct_windows_profitable == 1.0
    assert result.pct_windows_positive_sharpe == 0.0
    assert result.aggregate_cagr > 0
    assert result.aggregate_max_drawdown == 0.0  # never declines


def test_positive_drift_series_has_positive_sharpe_windows():
    # With a positive drift dominating low vol, every window should be both
    # profitable and positive-Sharpe.
    idx = pd.bdate_range("2018-01-01", periods=252 * 4)
    rng = np.random.default_rng(11)
    s = pd.Series(rng.normal(0.002, 0.003, len(idx)), index=idx)
    result = run_walkforward(s, train_months=12, test_months=3, step_months=3)
    assert result.pct_windows_profitable == 1.0
    assert result.pct_windows_positive_sharpe == 1.0
    assert result.aggregate_sharpe > 0


def test_metric_helpers():
    r = np.array([0.01, -0.02, 0.03, 0.0, 0.01])
    assert sharpe_ratio(np.zeros(10)) == 0.0  # zero variance → 0
    assert max_drawdown(np.array([0.1, -0.5])) < 0
    # Drawdown is anchored at initial capital, so an immediate 50% loss is a
    # -0.5 drawdown rather than 0.0 (regression: PR #75 review item).
    assert max_drawdown(np.array([-0.5, 0.1])) == pytest.approx(-0.5)
    assert cagr(np.array([0.0, 0.0])) == 0.0
    # blown-up curve has no real growth rate → clamped to -1.0
    assert cagr(np.array([-1.5, 0.2])) == -1.0
    assert isinstance(sharpe_ratio(r), float)


def test_strategy_name_threaded_through():
    result = run_walkforward(_series(4), strategy="MyStrat")
    assert result.strategy == "MyStrat"


def test_single_series_path_is_rolling_holdout():
    # The precomputed-series path is in-sample slicing, not genuine walk-forward,
    # and must be tagged so the deployment gate can refuse it.
    result = run_walkforward(_series(4), strategy="MyStrat")
    assert result.mode == "rolling_holdout"
    assert result.oos_source == "rolling_holdout_slice"


def test_supplied_windows_path_is_walkforward():
    # Caller supplies per-window OOS returns (each trained out of sample).
    base = pd.Timestamp("2018-01-01")
    windows = [
        pd.Series(
            np.full(63, 0.001),
            index=pd.bdate_range(base + pd.DateOffset(months=4 * i), periods=63),
        )
        for i in range(5)
    ]
    result = run_walkforward(windows=windows, strategy="WF", min_windows=4)
    assert result.mode == "walkforward"
    assert result.oos_source == "supplied_windows"
    assert len(result.windows) == 5


def test_refit_path_is_walkforward_and_calls_back():
    calls = {"n": 0}

    def refit(train, test_index):
        # A real model would fit on `train`; here we just emit a fixed OOS series
        # of the right length and record that we were invoked per window.
        calls["n"] += 1
        return np.full(len(test_index), 0.0008)

    result = run_walkforward(
        _series(4), strategy="WF", refit=refit, train_months=12,
        test_months=3, step_months=3,
    )
    assert result.mode == "walkforward"
    assert result.oos_source == "refit_callback"
    assert calls["n"] == len(result.windows) >= 4


def test_windows_and_refit_are_mutually_exclusive():
    with pytest.raises(ValueError, match="not both"):
        run_walkforward(_series(4), windows=[np.array([0.01])], refit=lambda t, i: i)


def test_run_walkforward_requires_some_input():
    with pytest.raises(ValueError, match="requires one of"):
        run_walkforward()
