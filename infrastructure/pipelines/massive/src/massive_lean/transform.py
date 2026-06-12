"""Convert raw Massive.com API responses to LEAN-format / alternative-data DataFrames.

This module is pure (no network calls, no filesystem access) so it can be
unit-tested with mocked API responses — see `tests/test_transform.py`.

Two output families:

1. Futures daily bars -> LEAN `future/<market>/daily/<symbol>.zip` rows
   (`Time,Open,High,Low,Close,Volume`, per
   https://github.com/QuantConnect/Lean/blob/master/Data/future/readme.md).
   Futures daily prices are NOT scaled by 10,000 (that convention is
   equities-only).

2. Options EOD data -> `lean-data/alternative/massive/options/...` CSVs
   (chain snapshots with greeks/IV/OI, and per-contract daily aggregate
   bars). Options data is written as alternative data rather than native
   LEAN `option/usa/daily` zips because the native format requires
   per-contract deci-cent-strike file naming
   (https://github.com/QuantConnect/Lean/blob/master/Data/option/readme.md)
   that has not been validated against real Massive.com responses yet.
"""
from __future__ import annotations

from typing import Any, Iterable

import pandas as pd


# ---------------------------------------------------------------------------
# Futures
# ---------------------------------------------------------------------------

def transform_futures_daily_bars(aggs: Iterable[Any]) -> pd.DataFrame:
    """Convert a list/iterator of futures aggregate-bar objects to LEAN daily rows.

    Input: items from `MassiveClient.list_futures_aggregates(...)` —
    `FuturesAgg` objects (per `massive==2.8.0`,
    `massive/rest/models/futures.py`) exposing `window_start` (int,
    nanoseconds since epoch UTC), `open`, `high`, `low`, `close`, `volume`,
    `dollar_volume`, `transactions`, `session_end_date`, `settlement_price`.
    `_extract_timestamp_ns` also falls back to a millisecond `timestamp`/`t`
    field defensively, in case a future API revision changes the field name.

    Output columns (no header, ready for `writer.write_futures_daily`):
        date_str (YYYYMMDD 00:00), open, high, low, close, volume

    Futures daily prices are written as-is (NOT multiplied by 10,000) per
    the LEAN futures daily example
    (`20160601 00:00,43.20,43.50,43.10,43.45,513`).
    """
    rows = []
    for item in aggs:
        data = _as_dict(item)
        ts_ns = _extract_timestamp_ns(data)
        rows.append({
            "date_str": pd.Timestamp(ts_ns, unit="ns", tz="UTC").strftime("%Y%m%d 00:00"),
            "open": _num(data.get("open")),
            "high": _num(data.get("high")),
            "low": _num(data.get("low")),
            "close": _num(data.get("close")),
            "volume": _num(data.get("volume")),
        })
    df = pd.DataFrame(rows, columns=["date_str", "open", "high", "low", "close", "volume"])
    if not df.empty:
        df = df.drop_duplicates(subset="date_str").sort_values("date_str").reset_index(drop=True)
    return df


def transform_futures_contracts(contracts: Iterable[Any]) -> pd.DataFrame:
    """Convert futures contract reference objects to a flat metadata DataFrame.

    Used to discover tradable contract tickers for a root symbol (e.g. all
    "ES*" contracts) before pulling per-contract aggregates. Input items are
    `FuturesContract` objects (per `massive==2.8.0`,
    `massive/rest/models/futures.py`) with fields `ticker`, `product_code`,
    `trading_venue`, `name`, `type`, `date`, `active`, `first_trade_date`,
    `last_trade_date`, `settlement_date`, `days_to_maturity`, etc.

    NOTE: `FuturesContract` has NO `expiration_date` field. We use
    `last_trade_date` (falling back to `settlement_date`, then `date`) as
    the expiration proxy embedded in the LEAN daily zip's inner CSV filename
    (`writer.write_futures_daily`).
    """
    rows = []
    for item in contracts:
        data = _as_dict(item)
        rows.append({
            "ticker": data.get("ticker"),
            "product_code": data.get("product_code"),
            "exchange": data.get("trading_venue"),
            "first_trade_date": data.get("first_trade_date"),
            "last_trade_date": data.get("last_trade_date"),
            "expiration_date": (
                data.get("last_trade_date")
                or data.get("settlement_date")
                or data.get("date")
            ),
            "name": data.get("name"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

def transform_options_chain_snapshot(
    underlying_ticker: str,
    snapshot_date: str,
    chain: Iterable[Any],
) -> pd.DataFrame:
    """Convert an options-chain snapshot into a point-in-time alternative-data row set.

    Input: items from `MassiveClient.list_snapshot_options_chain(...)`. Each
    item is expected to expose (per
    https://massive.com/docs/rest/options/snapshots/option-chain-snapshot):
      - `details`: {ticker, strike_price, expiration_date, contract_type}
      - `greeks`: {delta, gamma, theta, vega}
      - `implied_volatility`
      - `open_interest`
      - `day` / `last_quote` / `last_trade`: price fields

    `snapshot_date` is the as-of date (YYYY-MM-DD) this snapshot represents
    — pass the date the pipeline was run, since `list_snapshot_options_chain`
    returns the *current* chain (not historical). This makes the output
    point-in-time safe: a row's `snapshot_date` is always <= when it was
    written.

    Output columns:
        snapshot_date, underlying_ticker, contract_ticker, expiration_date,
        strike_price, contract_type, bid, ask, last_price, volume,
        open_interest, implied_volatility, delta, gamma, theta, vega
    """
    rows = []
    for item in chain:
        data = _as_dict(item)
        details = _as_dict(data.get("details"))
        greeks = _as_dict(data.get("greeks"))
        day = _as_dict(data.get("day"))
        last_quote = _as_dict(data.get("last_quote"))
        last_trade = _as_dict(data.get("last_trade"))

        rows.append({
            "snapshot_date": snapshot_date,
            "underlying_ticker": underlying_ticker,
            "contract_ticker": details.get("ticker"),
            "expiration_date": details.get("expiration_date"),
            "strike_price": details.get("strike_price"),
            "contract_type": details.get("contract_type"),
            "bid": last_quote.get("bid") or last_quote.get("bid_price"),
            "ask": last_quote.get("ask") or last_quote.get("ask_price"),
            "last_price": last_trade.get("price") or day.get("close"),
            "volume": day.get("volume"),
            "open_interest": data.get("open_interest"),
            "implied_volatility": data.get("implied_volatility"),
            "delta": greeks.get("delta"),
            "gamma": greeks.get("gamma"),
            "theta": greeks.get("theta"),
            "vega": greeks.get("vega"),
        })

    columns = [
        "snapshot_date", "underlying_ticker", "contract_ticker", "expiration_date",
        "strike_price", "contract_type", "bid", "ask", "last_price", "volume",
        "open_interest", "implied_volatility", "delta", "gamma", "theta", "vega",
    ]
    return pd.DataFrame(rows, columns=columns)


def transform_option_daily_bars(contract_ticker: str, aggs: Iterable[Any]) -> pd.DataFrame:
    """Convert per-contract daily aggregate bars (`O:`-ticker `list_aggs`) to a flat frame.

    Input: items from `MassiveClient.list_aggs("O:...", 1, "day", ...)`. Each
    item exposes `timestamp` (ms since epoch UTC), `open`, `high`, `low`,
    `close`, `volume`, `vwap`, `transactions` — confirmed shape from the
    `Agg` model used across Massive's stocks/options aggregates.

    Output columns:
        date, contract_ticker, open, high, low, close, volume, vwap, transactions
    """
    rows = []
    for item in aggs:
        data = _as_dict(item)
        ts_ms = data.get("timestamp")
        date_str = (
            pd.Timestamp(ts_ms, unit="ms", tz="UTC").strftime("%Y-%m-%d")
            if ts_ms is not None else None
        )
        rows.append({
            "date": date_str,
            "contract_ticker": contract_ticker,
            "open": _num(data.get("open")),
            "high": _num(data.get("high")),
            "low": _num(data.get("low")),
            "close": _num(data.get("close")),
            "volume": _num(data.get("volume")),
            "vwap": _num(data.get("vwap")),
            "transactions": data.get("transactions"),
        })
    columns = ["date", "contract_ticker", "open", "high", "low", "close", "volume", "vwap", "transactions"]
    df = pd.DataFrame(rows, columns=columns)
    if not df.empty:
        df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_dict(obj: Any) -> dict[str, Any]:
    """Normalize a response item to a dict, handling SDK model objects, dicts, and None."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    if hasattr(obj, "_asdict"):  # namedtuple
        return obj._asdict()
    return {}


def _num(value: Any) -> float | int | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_timestamp_ns(data: dict[str, Any]) -> int:
    """Best-effort extraction of a UTC timestamp in nanoseconds from an aggregate row.

    Handles either:
      - `window_start` in nanoseconds (Polygon/Massive futures convention), or
      - `timestamp` / `t` in milliseconds (equities/options `Agg` convention).
    """
    if "window_start" in data and data["window_start"] is not None:
        return int(data["window_start"])
    for key in ("timestamp", "t"):
        if key in data and data[key] is not None:
            return int(data[key]) * 1_000_000  # ms -> ns
    raise KeyError(
        f"Could not find a timestamp field in aggregate row: {sorted(data.keys())}"
    )
