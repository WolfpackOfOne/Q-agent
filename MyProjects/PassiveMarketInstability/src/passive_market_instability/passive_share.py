"""Passive-share curve helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from passive_market_instability.config import (
    PAPER_ALPHA_BRIGHTMAN_HARVEY,
    PAPER_ALPHA_HADDAD,
    PAPER_T0,
)


def logistic_passive_share(t, alpha, t0):
    """
    Return passive share p(t) = 1 / (1 + exp(-alpha * (t - t0))).
    Works with floats, lists, numpy arrays, or pandas Series.
    """
    is_scalar = np.isscalar(t)
    index = t.index if isinstance(t, pd.Series) else None
    values = np.asarray(t, dtype=float)
    exponent = np.clip(-alpha * (values - t0), -700, 700)
    result = 1.0 / (1.0 + np.exp(exponent))

    if is_scalar:
        return float(result)
    if index is not None:
        return pd.Series(result, index=index, name="passive_share")
    return result


def _coerce_time_frame(years_or_t: pd.Series | list | np.ndarray) -> pd.DataFrame:
    values = np.asarray(years_or_t, dtype=float)
    if values.size == 0:
        raise ValueError("years_or_t must contain at least one value")

    if np.nanmin(values) >= 1900:
        years = values
        t = years - np.nanmin(years)
    else:
        t = values
        years = 1994.0 + t

    return pd.DataFrame({"year": years, "t": t})


def build_passive_share_scenarios(years_or_t):
    """
    Build passive-share scenarios:
    - haddad_baseline using alpha = 0.106
    - brightman_harvey using alpha = 0.100
    - conservative using alpha below baseline
    - aggressive using alpha above baseline
    - no_passive using zero passive share
    """
    base = _coerce_time_frame(years_or_t)
    scenarios = {
        "no_passive": {
            "alpha": 0.0,
            "source": "zero-net-flow reference case",
        },
        "haddad_baseline": {
            "alpha": PAPER_ALPHA_HADDAD,
            "source": "Haddad, Huebner, and Loualiche 2025 fit",
        },
        "brightman_harvey": {
            "alpha": PAPER_ALPHA_BRIGHTMAN_HARVEY,
            "source": "Brightman and Harvey 2025 sensitivity fit",
        },
        "conservative": {
            "alpha": PAPER_ALPHA_HADDAD * 0.75,
            "source": "slower-than-baseline sensitivity",
        },
        "aggressive": {
            "alpha": PAPER_ALPHA_HADDAD * 1.25,
            "source": "faster-than-baseline sensitivity",
        },
    }

    frames = []
    for scenario, meta in scenarios.items():
        frame = base.copy()
        frame["scenario"] = scenario
        frame["alpha"] = meta["alpha"]
        frame["source"] = meta["source"]
        if scenario == "no_passive":
            frame["passive_share"] = 0.0
        else:
            frame["passive_share"] = logistic_passive_share(frame["t"], meta["alpha"], PAPER_T0)
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def threshold_crossing_year(df, threshold, scenario_col="scenario"):
    """
    For each scenario, find the first year or t where passive_share >= threshold.
    """
    required = {scenario_col, "passive_share"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    if "t" in df.columns:
        time_col = "t"
    elif "year" in df.columns:
        time_col = "year"
    else:
        raise ValueError("expected a 't' or 'year' column for sort order")

    records = []
    for scenario, group in df.sort_values(time_col).groupby(scenario_col):
        crossed = group[group["passive_share"] >= threshold]
        if crossed.empty:
            records.append(
                {
                    scenario_col: scenario,
                    "threshold": threshold,
                    "crossed": False,
                    "crossing_year": np.nan,
                    "crossing_t": np.nan,
                }
            )
            continue

        first = crossed.iloc[0]
        records.append(
            {
                scenario_col: scenario,
                "threshold": threshold,
                "crossed": True,
                "crossing_year": first["year"] if "year" in first.index else np.nan,
                "crossing_t": first["t"] if "t" in first.index else np.nan,
            }
        )

    return pd.DataFrame.from_records(records)


def validate_passive_share(df):
    """
    Sanity checks:
    - passive_share must be between 0 and 1
    - passive_share should generally be non-decreasing by scenario
    - no missing scenario labels
    - no missing year/t values
    """
    required = {"scenario", "passive_share"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    time_col = "t" if "t" in df.columns else "year" if "year" in df.columns else None
    if time_col is None:
        raise ValueError("expected a 't' or 'year' column")

    bounds_ok = df["passive_share"].between(0.0, 1.0).all()
    labels_ok = df["scenario"].notna().all()
    time_ok = df[time_col].notna().all()
    monotonic_ok = True

    for scenario, group in df.sort_values(time_col).groupby("scenario"):
        if scenario == "no_passive":
            monotonic_ok = monotonic_ok and (group["passive_share"].abs() < 1e-12).all()
        else:
            monotonic_ok = monotonic_ok and (group["passive_share"].diff().dropna() >= -1e-12).all()

    return {
        "passive_share_bounds": bool(bounds_ok),
        "passive_share_monotonic": bool(monotonic_ok),
        "scenario_labels_present": bool(labels_ok),
        "time_values_present": bool(time_ok),
    }
