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

import logging
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Trading days per year — used to annualize Sharpe and CAGR.
TRADING_DAYS = 252

# Result modes. Only ``walkforward`` is genuine out-of-sample evaluation and is
# eligible to satisfy the live deployment gate (see ontology/policy.py). The
# single precomputed-series path is ``rolling_holdout``: it slices one already
# realized return series into calendar windows without refitting anything, so it
# is in-sample reporting, NOT validation, and the gate must refuse it.
MODE_WALKFORWARD = "walkforward"
MODE_ROLLING_HOLDOUT = "rolling_holdout"


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
    # How the per-window OOS returns were produced. ``rolling_holdout`` (the
    # default single-series path) is in-sample slicing and is NOT gate-eligible;
    # ``walkforward`` means each window's returns came from a model fit only on
    # its own train slice (refit callback or caller-supplied per-window OOS).
    mode: str = MODE_ROLLING_HOLDOUT
    # Provenance: how each window's OOS returns were generated —
    # ``rolling_holdout_slice`` | ``refit_callback`` | ``supplied_windows``.
    oos_source: str = "rolling_holdout_slice"
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
    returns: pd.Series | None = None,
    *,
    strategy: str = "",
    train_months: int = 12,
    test_months: int = 3,
    step_months: int = 3,
    min_windows: int = 4,
    anchored: bool = False,
    metric_fn: Callable[[np.ndarray], dict] | None = None,
    windows: "list | tuple | None" = None,
    refit: Callable[[pd.Series, pd.DatetimeIndex], object] | None = None,
) -> WalkforwardResult:
    """Run walk-forward analysis. Three input modes, two of them genuine OOS:

    - ``windows=[oos_0, oos_1, ...]`` — caller supplies the per-window
      out-of-sample returns directly (each a ``pd.Series`` with a
      ``DatetimeIndex``, or a bare array). Each was produced by a model trained
      only on its own train window. Result ``mode='walkforward'``.
    - ``returns=..., refit=fn`` — ``fn(train_returns, test_index)`` is called for
      each window to generate that window's OOS returns from a model fit on the
      train slice only. Result ``mode='walkforward'``.
    - ``returns=...`` alone — the convenience path: one precomputed series sliced
      into calendar windows with **no refit**. This is in-sample reporting, so
      the result is ``mode='rolling_holdout'`` and is NOT eligible to validate a
      live deployment (the gate refuses it).

    Train windows may overlap (or expand, with ``anchored=True``); test windows
    never do (enforced by ``step_months >= test_months``). Raises
    :class:`InsufficientDataError` if fewer than ``min_windows`` windows result.
    """
    if windows is not None and refit is not None:
        raise ValueError("pass either windows= or refit=, not both")
    if step_months < test_months:
        raise ValueError(
            f"step_months ({step_months}) < test_months ({test_months}) would "
            "overlap test windows; walk-forward requires step_months >= test_months."
        )

    if windows is not None:
        built = _windows_from_oos(windows, metric_fn=metric_fn)
        if len(built) < min_windows:
            raise InsufficientDataError(
                f"only {len(built)} OOS window(s) supplied; need at least {min_windows}."
            )
        return _assemble_result(
            strategy, built, train_months, test_months, step_months,
            mode=MODE_WALKFORWARD, oos_source="supplied_windows",
        )

    if returns is None:
        raise ValueError("run_walkforward requires one of returns=, windows=, or refit=")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns must be indexed by a DatetimeIndex")

    series = returns.sort_index().dropna()
    if series.empty:
        raise InsufficientDataError("return series is empty")

    bounds_kw = dict(train_months=train_months, test_months=test_months,
                     step_months=step_months, anchored=anchored)
    if refit is not None:
        built = _windows_with_refit(series, refit, metric_fn=metric_fn, **bounds_kw)
        if len(built) < min_windows:
            raise InsufficientDataError(
                f"only {len(built)} walk-forward window(s) produced by refit; "
                f"need at least {min_windows}."
            )
        return _assemble_result(
            strategy, built, train_months, test_months, step_months,
            mode=MODE_WALKFORWARD, oos_source="refit_callback",
        )

    built = _windows_from_slices(series, metric_fn=metric_fn, **bounds_kw)
    if len(built) < min_windows:
        raise InsufficientDataError(
            f"only {len(built)} walk-forward window(s) fit in the series; "
            f"need at least {min_windows} (train={train_months}m, "
            f"test={test_months}m, step={step_months}m)."
        )
    log.warning(
        "run_walkforward(returns=...) sliced one precomputed series into %d "
        "windows without refitting; result is mode='rolling_holdout' (in-sample "
        "reporting) and is NOT eligible to validate a live deployment.",
        len(built),
    )
    return _assemble_result(
        strategy, built, train_months, test_months, step_months,
        mode=MODE_ROLLING_HOLDOUT, oos_source="rolling_holdout_slice",
    )


def _build_window(
    index: int,
    oos: np.ndarray,
    *,
    train_start: str = "",
    train_end: str = "",
    test_start: str = "",
    test_end: str = "",
    metric_fn: Callable[[np.ndarray], dict] | None = None,
) -> WalkforwardWindow:
    oos = np.asarray(oos, dtype=float)
    metrics = metric_fn(oos) if metric_fn else {}
    return WalkforwardWindow(
        window_index=index,
        train_start=train_start, train_end=train_end,
        test_start=test_start, test_end=test_end,
        oos_returns=oos,
        sharpe=metrics.get("sharpe", sharpe_ratio(oos)),
        cagr=metrics.get("cagr", cagr(oos)),
        max_drawdown=metrics.get("max_drawdown", max_drawdown(oos)),
        n_trades=metrics.get("n_trades", _n_trades(oos)),
    )


def _slice_bounds(idx, start, end, **bounds_kw):
    """Yield ``(train_start, train_end, test_start, test_end)`` for complete windows."""
    for ts, te, vs, ve, complete in _iter_window_bounds(start, end, **bounds_kw):
        if complete:
            yield ts, te, vs, ve


def _windows_from_slices(series, *, metric_fn, **bounds_kw) -> list[WalkforwardWindow]:
    idx = series.index
    out: list[WalkforwardWindow] = []
    for train_start, train_end, test_start, test_end in _slice_bounds(idx, idx[0], idx[-1], **bounds_kw):
        mask = (idx >= test_start) & (idx < test_end)
        oos = series.values[mask]
        if oos.size == 0:
            continue
        out.append(_build_window(
            len(out), oos,
            train_start=train_start.isoformat(), train_end=train_end.isoformat(),
            test_start=test_start.isoformat(), test_end=test_end.isoformat(),
            metric_fn=metric_fn,
        ))
    return out


def _windows_with_refit(series, refit, *, metric_fn, **bounds_kw) -> list[WalkforwardWindow]:
    idx = series.index
    out: list[WalkforwardWindow] = []
    for train_start, train_end, test_start, test_end in _slice_bounds(idx, idx[0], idx[-1], **bounds_kw):
        train = series[(idx >= train_start) & (idx < train_end)]
        test_index = idx[(idx >= test_start) & (idx < test_end)]
        if train.empty or len(test_index) == 0:
            continue
        oos = np.asarray(refit(train, test_index), dtype=float)
        if oos.size == 0:
            continue
        out.append(_build_window(
            len(out), oos,
            train_start=train_start.isoformat(), train_end=train_end.isoformat(),
            test_start=test_start.isoformat(), test_end=test_end.isoformat(),
            metric_fn=metric_fn,
        ))
    return out


def _windows_from_oos(windows, *, metric_fn) -> list[WalkforwardWindow]:
    out: list[WalkforwardWindow] = []
    for w in windows:
        if isinstance(w, pd.Series) and isinstance(w.index, pd.DatetimeIndex) and len(w):
            s = w.sort_index()
            test_start, test_end = s.index[0].isoformat(), s.index[-1].isoformat()
            oos = s.values
        else:
            test_start = test_end = ""
            oos = np.asarray(w, dtype=float)
        if np.asarray(oos, dtype=float).size == 0:
            continue
        out.append(_build_window(
            len(out), oos, test_start=test_start, test_end=test_end, metric_fn=metric_fn,
        ))
    return out


def _assemble_result(
    strategy: str,
    windows: list[WalkforwardWindow],
    train_months: int,
    test_months: int,
    step_months: int,
    *,
    mode: str,
    oos_source: str,
) -> WalkforwardResult:
    """Aggregate per-window OOS returns into a :class:`WalkforwardResult`."""
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
        mode=mode,
        oos_source=oos_source,
    )
