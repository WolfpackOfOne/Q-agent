"""ETF flow-pressure proxy helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_returns(df, price_col="adj_close"):
    """
    Add simple returns by ticker.
    """
    required = {"date", "ticker", price_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values(["ticker", "date"])
    out["return"] = out.groupby("ticker", sort=False)[price_col].pct_change()
    return out


def estimate_flow_pressure_proxy(df):
    """
    Estimate weak ETF flow-pressure proxy using volume * return.
    Label clearly as proxy, not official flow.
    """
    if "return" not in df.columns:
        df = add_returns(df)
    required = {"volume", "return"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    out = df.copy()
    out["flow_pressure_proxy"] = out["volume"] * out["return"]
    out["flow_pressure_source"] = "proxy: volume times simple return, not official ETF flow"
    return out


def aggregate_etf_flow_pressure(df):
    """
    Aggregate ETF-level flow pressure by date.
    Include raw sum and z-scored rolling version.
    """
    if "flow_pressure_proxy" not in df.columns:
        df = estimate_flow_pressure_proxy(df)

    cleaned = df.dropna(subset=["flow_pressure_proxy"]).copy()
    agg = (
        cleaned.groupby("date", as_index=False)["flow_pressure_proxy"]
        .sum()
        .rename(columns={"flow_pressure_proxy": "aggregate_flow_pressure_proxy"})
        .sort_values("date")
    )
    rolling_mean = agg["aggregate_flow_pressure_proxy"].rolling(20, min_periods=5).mean()
    rolling_std = agg["aggregate_flow_pressure_proxy"].rolling(20, min_periods=5).std()
    agg["aggregate_flow_pressure_z"] = (
        (agg["aggregate_flow_pressure_proxy"] - rolling_mean) / rolling_std.replace(0.0, np.nan)
    )
    return agg


def validate_etf_flow_proxy(df):
    """
    Sanity checks:
    - date, ticker, price, volume columns exist
    - volume is non-negative
    - returns are finite except first observation per ticker
    - flow proxy is finite after dropping missing returns
    """
    price_cols = {"adj_close", "close"} & set(df.columns)
    required = {"date", "ticker", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if not price_cols:
        raise ValueError("missing required price column: expected 'adj_close' or 'close'")
    if (df["volume"] < 0).any():
        raise ValueError("volume must be non-negative")

    if "return" in df.columns:
        returns = df.sort_values(["ticker", "date"]).copy()
        invalid = returns["return"].notna() & ~np.isfinite(returns["return"])
        if invalid.any():
            raise ValueError("returns must be finite except missing first observations")

    if "flow_pressure_proxy" in df.columns:
        cleaned = df.dropna(subset=["return"]) if "return" in df.columns else df
        invalid_proxy = cleaned["flow_pressure_proxy"].notna() & ~np.isfinite(cleaned["flow_pressure_proxy"])
        if invalid_proxy.any():
            raise ValueError("flow_pressure_proxy must be finite after dropping missing returns")

    return True
