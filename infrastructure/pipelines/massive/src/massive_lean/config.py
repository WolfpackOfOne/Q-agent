"""Default configuration for the Massive.com EOD pipeline.

These are intentionally small, liquid defaults — override via CLI flags
(`--roots`, `--underlyings`, etc.) or pass a custom list.
"""
from __future__ import annotations

# --- Futures -----------------------------------------------------------
#
# Root symbols for a small set of liquid US futures contracts.
# Massive (Polygon-lineage) futures tickers are typically of the form
# "<ROOT><MONTH_CODE><YEAR>" e.g. "ESZ24" for the Dec-2024 E-mini S&P 500
# contract, or a continuous/front-month alias depending on the endpoint.
#
# ASSUMPTION (unverified — confirm against `list_futures_contracts` /
# `list_futures_aggregates` once an API key is available): the contracts
# reference endpoint accepts a bare root symbol (e.g. "ES") and returns the
# list of tradable contract tickers for that root.
DEFAULT_FUTURES_ROOTS: list[str] = [
    "ES",  # E-mini S&P 500 (CME)
    "NQ",  # E-mini Nasdaq 100 (CME)
    "CL",  # Crude Oil WTI (NYMEX)
    "GC",  # Gold (COMEX)
    "ZN",  # 10-Year T-Note (CBOT)
]

# LEAN futures market (exchange) folder names — `future/<market>/daily/...`.
# LEAN's AlgoSeek-derived futures data uses lowercase exchange names: cme,
# nymex, comex, cbot, cboe, ice. Map each root symbol to its home exchange so
# the writer can place daily zips under the correct `lean-data/future/<market>/`
# directory. Extend this map if you add roots from other exchanges.
FUTURES_ROOT_MARKET: dict[str, str] = {
    "ES": "cme",     # E-mini S&P 500
    "NQ": "cme",     # E-mini Nasdaq 100
    "CL": "nymex",   # Crude Oil WTI
    "GC": "comex",   # Gold
    "ZN": "cbot",    # 10-Year T-Note
}

# --- Options -------------------------------------------------------------
#
# Underlyings for daily EOD options chain snapshots / aggregates.
DEFAULT_OPTIONS_UNDERLYINGS: list[str] = [
    "SPY",
    "QQQ",
]

# Massive (Polygon-style) options ticker prefix.
OPTION_TICKER_PREFIX = "O:"

# Massive (Polygon-style) futures ticker prefix used by some endpoints.
FUTURES_TICKER_PREFIX = "F:"
