"""Simulation utilities for the passive market instability model."""

from __future__ import annotations

import numpy as np
import pandas as pd

from passive_market_instability.config import F0, PAPER_R, S0
from passive_market_instability.passive_share import logistic_passive_share


def fundamental_value(t, f0=100.0, r=0.0917):
    """
    F(t) = F0 * exp(r * t)
    """
    values = np.asarray(t, dtype=float)
    result = f0 * np.exp(r * values)
    if np.isscalar(t):
        return float(result)
    if isinstance(t, pd.Series):
        return pd.Series(result, index=t.index, name="fundamental_value")
    return result


def _coerce_flow_pressure(flow_pressure, t_grid):
    if flow_pressure is None:
        return np.zeros_like(t_grid, dtype=float)
    if callable(flow_pressure):
        values = np.asarray(flow_pressure(t_grid), dtype=float)
    else:
        values = np.asarray(flow_pressure, dtype=float)
    if values.ndim != 1:
        raise ValueError("flow_pressure must be one-dimensional")
    if len(values) == len(t_grid):
        return values
    source_x = np.linspace(t_grid[0], t_grid[-1], len(values))
    return np.interp(t_grid, source_x, values)


def simulate_market_paths(
    n_paths=100,
    years=60,
    steps_per_year=252,
    s0=100.0,
    f0=100.0,
    r=0.0917,
    kappa=0.0909,
    sigma=0.1247,
    alpha=0.106,
    t0=30.0,
    passive_mode="logistic",
    random_seed=42,
    flow_pressure=None,
    lambda_flow=0.0,
):
    """
    Simulate the paper's passive market instability model.

    Base model:
        dS = kappa * (1 - p_t) * (F_t - S_t) * dt
             + sigma * sqrt(F_t * S_t) * dW

    Optional extension:
        + lambda_flow * flow_pressure_t * dt

    Use Euler-Maruyama.

    Numerical guards:
    - if S becomes negative, set S to 0 for that path
    - sqrt term should use max(F_t * S_t, 0)
    - record hitting time if S first hits 0
    """
    if n_paths <= 0:
        raise ValueError("n_paths must be positive")
    if years <= 0:
        raise ValueError("years must be positive")
    if steps_per_year <= 0:
        raise ValueError("steps_per_year must be positive")

    n_steps = int(years * steps_per_year)
    dt = 1.0 / steps_per_year
    t_grid = np.linspace(0.0, float(years), n_steps + 1)
    year_grid = 1994.0 + t_grid
    f_grid = fundamental_value(t_grid, f0=f0, r=r)

    if passive_mode == "none" or passive_mode == "no_passive":
        p_grid = np.zeros_like(t_grid)
    elif passive_mode == "logistic":
        p_grid = logistic_passive_share(t_grid, alpha=alpha, t0=t0)
    else:
        raise ValueError("passive_mode must be 'logistic', 'none', or 'no_passive'")

    flow_grid = _coerce_flow_pressure(flow_pressure, t_grid)

    rng = np.random.default_rng(random_seed)
    s = np.empty((n_steps + 1, n_paths), dtype=float)
    s[0, :] = s0
    hitting_times = np.full(n_paths, np.nan, dtype=float)

    for i in range(n_steps):
        current = s[i, :]
        drift = kappa * (1.0 - p_grid[i]) * (f_grid[i] - current)
        flow_drift = lambda_flow * flow_grid[i]
        diffusion_scale = sigma * np.sqrt(np.maximum(f_grid[i] * current, 0.0))
        shocks = rng.normal(0.0, np.sqrt(dt), size=n_paths)
        next_s = current + (drift + flow_drift) * dt + diffusion_scale * shocks
        hit_now = (next_s <= 0.0) & np.isnan(hitting_times)
        hitting_times[hit_now] = t_grid[i + 1]
        s[i + 1, :] = np.maximum(next_s, 0.0)

    path_cols = [f"path_{idx:03d}" for idx in range(n_paths)]
    paths_df = pd.DataFrame(s, columns=path_cols)
    paths_df.insert(0, "year", year_grid)
    paths_df.insert(0, "t", t_grid)

    state_df = pd.DataFrame(
        {
            "t": t_grid,
            "year": year_grid,
            "fundamental_value": f_grid,
            "passive_share": p_grid,
            "flow_pressure": flow_grid,
        }
    )
    hitting_times_df = pd.DataFrame({"path": path_cols, "hitting_time": hitting_times})

    return {
        "paths": paths_df,
        "state": state_df,
        "hitting_times": hitting_times_df,
    }


def compute_instantaneous_volatility(s, f, sigma):
    """
    V(t) = sigma * sqrt(F(t) / S(t))
    Use NaN or inf-safe handling when S <= 0.
    """
    s_values = np.asarray(s, dtype=float)
    f_values = np.asarray(f, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        vol = sigma * np.sqrt(np.where(s_values > 0.0, f_values / s_values, np.nan))
    vol = np.where(np.isfinite(vol), vol, np.nan)
    if np.isscalar(s) and np.isscalar(f):
        return float(vol)
    return vol


def lyapunov_threshold(kappa, sigma):
    """
    Paper's baseline Lyapunov-style threshold:
    p_L = 1 - (3 * sigma**2) / (4 * kappa)

    With kappa = 0.0909 and sigma = 0.1247, this should be around 0.87.
    """
    return 1.0 - (3.0 * sigma**2) / (4.0 * kappa)


def feller_threshold(kappa, sigma):
    """
    Paper's baseline Feller-style threshold:
    p_F = 1 - (sigma**2) / (2 * kappa)

    With kappa = 0.0909 and sigma = 0.1247, this should be around 0.91.
    """
    return 1.0 - sigma**2 / (2.0 * kappa)
