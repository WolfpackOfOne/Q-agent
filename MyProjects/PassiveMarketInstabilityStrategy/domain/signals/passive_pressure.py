"""Passive-pressure diagnostic signal — pure Python, no LEAN imports."""

from __future__ import annotations

import math
from typing import Dict, Optional


def logistic_passive_share(t: float, alpha: float = 0.106, t0: float = 30.0) -> float:
    """p(t) = 1 / (1 + exp(-alpha * (t - t0)))."""
    return 1.0 / (1.0 + math.exp(-alpha * (t - t0)))


def passive_share_at_date(date, ref_year: int = 1994, alpha: float = 0.106, t0: float = 30.0) -> float:
    """Return logistic passive share estimate for a given calendar date."""
    t = (date.year + date.month / 12.0) - ref_year
    return logistic_passive_share(t, alpha=alpha, t0=t0)


def lyapunov_threshold(kappa: float, sigma: float) -> float:
    """p_L = 1 - 3σ² / (4κ).  Above this, mean log growth turns negative."""
    return 1.0 - (3.0 * sigma ** 2) / (4.0 * kappa)


def feller_threshold(kappa: float, sigma: float) -> float:
    """p_F = 1 - σ² / (2κ).  Above this, the market can hit zero in finite time."""
    return 1.0 - sigma ** 2 / (2.0 * kappa)


def compute_flow_pressure_proxy(returns: Dict[str, float], volumes: Dict[str, float]) -> Dict[str, float]:
    """
    Proxy for passive-flow pressure per security: volume × return.

    This is a weak proxy, not true ETF creations or redemptions.
    Positive values indicate buying pressure; negative values indicate selling pressure.
    """
    result = {}
    for ticker in returns:
        if ticker in volumes:
            result[ticker] = returns[ticker] * volumes[ticker]
    return result


def passive_pressure_quintile(pressure: float, universe_pressures: list[float]) -> int:
    """Return quintile rank (1–5) of a single pressure value within the universe."""
    if not universe_pressures:
        return 3
    sorted_p = sorted(universe_pressures)
    n = len(sorted_p)
    rank = sum(1 for p in sorted_p if p <= pressure)
    quintile = min(5, max(1, math.ceil(rank / n * 5)))
    return quintile


def risk_overlay_scale(
    avg_quintile: float,
    threshold: int = 4,
    scale_when_high: float = 0.50,
) -> float:
    """
    Return gross-exposure scalar based on passive-pressure diagnostics.

    When average quintile >= threshold, reduce exposure to scale_when_high.
    Otherwise return 1.0 (no overlay).

    This is a research-only risk overlay.  Do not use for live trading
    without explicit review of the signal, sizing, and execution assumptions.
    """
    if avg_quintile >= threshold:
        return scale_when_high
    return 1.0
