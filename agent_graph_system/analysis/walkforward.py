"""Walk-forward analysis — rolling out-of-sample strategy evaluation.

A single full-period backtest reports the in-sample performance of a curve fit
on its own data. Walk-forward analysis enforces out-of-sample structure: train
on ``[t, t+train]``, test strictly on ``[t+train, t+train+test]``, slide forward
by ``step``, repeat. Only the aggregated out-of-sample returns count.

This module is pure Python (numpy + pandas, no graph/agent imports) so it is
unit-testable in isolation and callable from any layer. It takes a daily return
series in, and returns dataclass results out — the caller is responsible for
sourcing and preparing that series (from a LEAN equity curve, WRDS, etc.).

The hard invariant: **test windows never overlap**. Train windows may overlap
(and may expand, with ``anchored=True``), but each calendar day appears in at
most one test window, which is what prevents the subtle leakage of sliding
train/test with overlapping test periods. We enforce it by requiring
``step_months >= test_months``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

# Trading days per year — used to annualize Sharpe and CAGR.
TRADING_DAYS = 252


class InsufficientDataError(ValueError):
    """Raised when the return series is too short to form ``min_windows``.

    Surfaced (rather than silently returning a degenerate result) so the caller
    can record it as a risk — a strategy that cannot be walk-forward validated
    is a fact worth knowing, not one to paper over.
    """


@dataclass
class WalkforwardWindow:
    window_index: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    # Out-of-sample returns for this window's test slice.
    oos_returns: np.ndarray = field(repr=False)
    sharpe: float = 0.0
    cagr: float = 0.0
    max_drawdown: float = 0.0
    n_trades: int = 0


@dataclass
class WalkforwardResult:
    strategy: str
    windows: list[WalkforwardWindow]
    # Aggregated across the concatenation of every OOS window — the only
    # performance that counts.
    aggregate_sharpe: float
    aggregate_cagr: float
    aggregate_max_drawdown: float
    pct_windows_profitable: float
    pct_windows_positive_sharpe: float
    train_months: int
    test_months: int
    step_months: int
    # Set after a bootstrap significance test; None until then.
    bootstrap_p_value: float | None = None
    bootstrap_n_permutations: int | None = None


# ---------------------------------------------------------------------------
# Per-slice metrics (pure numpy)
# ---------------------------------------------------------------------------

def sharpe_ratio(returns: np.ndarray, periods: int = TRADING_DAYS) -> float:
    """Annualized Sharpe of a daily return array; 0.0 if undefined."""
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        return 0.0
    sd = r.std(ddof=1)
    if not np.isfinite(sd) or sd == 0.0:
        return 0.0
    return float(r.mean() / sd * np.sqrt(periods))


def cagr(returns: np.ndarray, periods: int = TRADING_DAYS) -> float:
    """Compound annual growth rate implied by a daily return array."""
    r = np.asarray(returns, dtype=float)
    if r.size == 0:
        return 0.0
    total = float(np.prod(1.0 + r))
    years = r.size / periods
    if years <= 0:
        return 0.0
    if total <= 0.0:
        # A blown-up equity curve has no real-valued growth rate; report a
        # total loss rather than returning a complex number.
        return -1.0
    return float(total ** (1.0 / years) - 1.0)


def max_drawdown(returns: np.ndarray) -> float:
    """Worst peak-to-trough decline of the equity curve, as a negative float.

    The curve is anchored at the initial capital (1.0) *before* the first return,
    so an immediate loss is measured from the start. Without the anchor a series
    like ``[-0.5, 0.1]`` would treat the post-first-return level as the peak and
    report 0.0, understating risk; with it, that series correctly reports -0.5.
    """
    r = np.asarray(returns, dtype=float)
    if r.size == 0:
        return 0.0
    equity = np.concatenate(([1.0], np.cumprod(1.0 + r)))
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    return float(drawdown.min())


def _n_trades(returns: np.ndarray) -> int:
    """Proxy trade count: number of non-zero daily returns."""
    r = np.asarray(returns, dtype=float)
    return int(np.count_nonzero(r))


# ---------------------------------------------------------------------------
# Window construction
# ---------------------------------------------------------------------------

def _iter_window_bounds(
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    train_months: int,
    test_months: int,
    step_months: int,
    anchored: bool,
):
    """Yield ``(train_start, train_end, test_start, test_end)`` timestamps.

    Test windows are contiguous and non-overlapping (guaranteed by the
    ``step_months >= test_months`` check in :func:`run_walkforward`). A window
    is only emitted when its full test slice fits inside ``[start, end]``.
    """
    i = 0
    while True:
        offset = pd.DateOffset(months=i * step_months)
        train_start = start if anchored else start + offset
        train_end = start + offset + pd.DateOffset(months=train_months)
        test_start = train_end
        test_end = test_start + pd.DateOffset(months=test_months)
        if test_start > end:
            break
        yield train_start, train_end, test_start, test_end, (test_end <= end)
        i += 1


def run_walkforward(
    returns: pd.Series,
    *,
    strategy: str = "",
    train_months: int = 12,
    test_months: int = 3,
    step_months: int = 3,
    min_windows: int = 4,
    anchored: bool = False,
    metric_fn: Callable[[np.ndarray], dict] | None = None,
) -> WalkforwardResult:
    """Run rolling walk-forward analysis over a daily return series.

    ``returns`` must be a :class:`pandas.Series` indexed by a ``DatetimeIndex``.
    Train windows may overlap (or expand, with ``anchored=True``); test windows
    never do. Raises :class:`InsufficientDataError` if fewer than
    ``min_windows`` complete test windows fit in the series, and ``ValueError``
    on a configuration that would overlap test windows.
    """
    if step_months < test_months:
        raise ValueError(
            f"step_months ({step_months}) < test_months ({test_months}) would "
            "overlap test windows; walk-forward requires step_months >= test_months."
        )
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns must be indexed by a DatetimeIndex")

    series = returns.sort_index().dropna()
    if series.empty:
        raise InsufficientDataError("return series is empty")

    idx = series.index
    start, end = idx[0], idx[-1]

    windows: list[WalkforwardWindow] = []
    for train_start, train_end, test_start, test_end, complete in _iter_window_bounds(
        start, end,
        train_months=train_months, test_months=test_months,
        step_months=step_months, anchored=anchored,
    ):
        if not complete:
            continue
        mask = (idx >= test_start) & (idx < test_end)
        oos = series.values[mask]
        if oos.size == 0:
            continue
        metrics = metric_fn(oos) if metric_fn else {}
        windows.append(WalkforwardWindow(
            window_index=len(windows),
            train_start=train_start.isoformat(),
            train_end=train_end.isoformat(),
            test_start=test_start.isoformat(),
            test_end=test_end.isoformat(),
            oos_returns=np.asarray(oos, dtype=float),
            sharpe=metrics.get("sharpe", sharpe_ratio(oos)),
            cagr=metrics.get("cagr", cagr(oos)),
            max_drawdown=metrics.get("max_drawdown", max_drawdown(oos)),
            n_trades=metrics.get("n_trades", _n_trades(oos)),
        ))

    if len(windows) < min_windows:
        raise InsufficientDataError(
            f"only {len(windows)} walk-forward window(s) fit in the series; "
            f"need at least {min_windows} (train={train_months}m, "
            f"test={test_months}m, step={step_months}m)."
        )

    all_oos = np.concatenate([w.oos_returns for w in windows])
    n = len(windows)
    return WalkforwardResult(
        strategy=strategy,
        windows=windows,
        aggregate_sharpe=sharpe_ratio(all_oos),
        aggregate_cagr=cagr(all_oos),
        aggregate_max_drawdown=max_drawdown(all_oos),
        pct_windows_profitable=sum(
            1 for w in windows if float(np.prod(1.0 + w.oos_returns)) > 1.0
        ) / n,
        pct_windows_positive_sharpe=sum(1 for w in windows if w.sharpe > 0) / n,
        train_months=train_months,
        test_months=test_months,
        step_months=step_months,
    )
