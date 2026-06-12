"""Liquidity and realized-risk features for equity panels."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _sorted_panel(df):
    required = {"date", "ticker"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    return out.sort_values(["ticker", "date"])


def add_dollar_volume(df):
    """
    dollar_volume = close * volume
    """
    required = {"close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    out = _sorted_panel(df)
    out["dollar_volume"] = out["close"] * out["volume"]
    return out


def add_rolling_adv(df, window=20):
    """
    rolling average dollar volume by ticker.
    """
    out = add_dollar_volume(df) if "dollar_volume" not in df.columns else _sorted_panel(df)
    out["rolling_adv_20d"] = out.groupby("ticker", sort=False)["dollar_volume"].transform(
        lambda s: s.rolling(window, min_periods=1).mean()
    )
    return out


def add_realized_volatility(df, window=20):
    """
    rolling realized volatility by ticker.
    Annualize using sqrt(252).
    """
    out = _sorted_panel(df)
    price_col = "adj_close" if "adj_close" in out.columns else "close"
    out["return"] = out.groupby("ticker", sort=False)[price_col].pct_change()
    out["realized_vol_20d"] = out.groupby("ticker", sort=False)["return"].transform(
        lambda s: s.rolling(window, min_periods=max(2, min(window, 5))).std() * np.sqrt(252.0)
    )
    return out


def add_drawdown(df, window=63):
    """
    rolling drawdown by ticker.
    """
    out = _sorted_panel(df)
    price_col = "adj_close" if "adj_close" in out.columns else "close"
    rolling_high = out.groupby("ticker", sort=False)[price_col].transform(
        lambda s: s.rolling(window, min_periods=1).max()
    )
    out["drawdown_63d"] = out[price_col] / rolling_high - 1.0
    return out
