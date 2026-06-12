"""Cross-sectional passive-pressure diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_index_weights_from_market_cap(df):
    """
    If official index weights are unavailable, estimate index weight as:
        market_cap_i / sum(market_cap_i by date)

    Label as an estimate.
    """
    required = {"date", "ticker", "market_cap"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    total_market_cap = out.groupby("date")["market_cap"].transform("sum")
    out["index_weight_estimate"] = np.where(total_market_cap > 0, out["market_cap"] / total_market_cap, np.nan)
    out["index_weight_source"] = "estimated from market capitalization, not official index weights"
    return out


def compute_passive_pressure(df):
    """
    Simple score:
        passive_pressure = passive_share * index_weight / rolling_adv_20d

    Use safeguards for zero or missing rolling_adv_20d.
    """
    required = {"passive_share", "index_weight_estimate", "rolling_adv_20d"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    denom = out["rolling_adv_20d"].where(out["rolling_adv_20d"] > 0.0)
    out["passive_pressure"] = out["passive_share"] * out["index_weight_estimate"] / denom
    return out


def compute_passive_dollar_pressure(df):
    """
    Alternative interpretable score:
        passive_dollar_pressure =
            total_market_value * passive_share * index_weight / rolling_adv_20d
    """
    required = {"passive_share", "index_weight_estimate", "rolling_adv_20d"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    if "total_market_value" not in out.columns:
        if "market_cap" not in out.columns:
            raise ValueError("expected 'total_market_value' or 'market_cap'")
        out["total_market_value"] = out.groupby("date")["market_cap"].transform("sum")

    denom = out["rolling_adv_20d"].where(out["rolling_adv_20d"] > 0.0)
    out["passive_dollar_pressure"] = (
        out["total_market_value"] * out["passive_share"] * out["index_weight_estimate"] / denom
    )
    return out


def assign_pressure_quintiles(df):
    """
    Assign quintiles by date.
    Q1 = lowest pressure
    Q5 = highest pressure
    """
    if "date" not in df.columns or "passive_pressure" not in df.columns:
        raise ValueError("expected 'date' and 'passive_pressure' columns")

    out = df.copy()

    def _assign_one_date(series):
        result = pd.Series(pd.NA, index=series.index, dtype="Int64")
        valid = series.dropna()
        if valid.empty:
            return result
        q = min(5, len(valid))
        if q == 1:
            result.loc[valid.index] = 1
            return result
        ranked = valid.rank(method="first")
        result.loc[valid.index] = pd.qcut(ranked, q=q, labels=range(1, q + 1)).astype("Int64")
        return result

    out["pressure_quintile"] = out.groupby("date", group_keys=False)["passive_pressure"].apply(_assign_one_date)
    return out


def summarize_pressure_quintiles(df):
    """
    Summarize realized volatility, drawdown, forward returns, and liquidity by quintile.
    """
    if "pressure_quintile" not in df.columns:
        raise ValueError("expected 'pressure_quintile' column")

    columns = [
        "realized_vol_20d",
        "drawdown_63d",
        "forward_5d_return",
        "forward_20d_return",
        "rolling_adv_20d",
        "passive_pressure",
        "passive_dollar_pressure",
    ]
    available = [col for col in columns if col in df.columns]
    if not available:
        raise ValueError("no summary metric columns found")

    return (
        df.dropna(subset=["pressure_quintile"])
        .groupby("pressure_quintile", observed=True)[available]
        .mean()
        .reset_index()
        .sort_values("pressure_quintile")
    )
