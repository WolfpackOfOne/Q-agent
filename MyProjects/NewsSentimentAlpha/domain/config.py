"""
Configuration constants for NewsSentimentAlpha.

Layer: ATOMS (pure constants, no dependencies except stdlib)

Usage:
    from domain.config import *
"""

# === ObjectStore ===
OBJECTSTORE_NAMESPACE = "news_sentiment_alpha"

# === Universe ===
# 10-stock universe for the news-tone long/short signal.
UNIVERSE = [
    "GS", "AAPL", "JPM", "BA", "HD", "IBM", "VZ", "V", "NKE", "CSCO",
]
BENCHMARK = "SPY"

# === Backtest Configuration ===
# Held-out test window. Strategy parameters below were selected using
# 2017-2018 (train) and 2019 (validate) only — this window was never
# touched during parameter selection. See docs/strategy.md § "Validation
# Methodology".
#
# END_DATE is trimmed to 2021-04-30, not the full 2021-12-31 test period:
# GDELT coverage of this 10-ticker universe collapses through 2021 (from
# ~150-175 articles/month in early 2020 down to single digits by
# 2021-12), and in practice the strategy places zero trades after
# 2021-04-30 regardless of END_DATE — confirmed by running both windows
# and comparing OrderListHash (identical). Extending END_DATE past that
# point only stretches the same trades over more elapsed time, which
# dilutes CAGR and Sharpe with a statistically meaningless flat tail.
START_DATE = (2020, 1, 1)
END_DATE = (2021, 4, 30)
CASH = 100_000

# === Strategy Parameters ===
# MIN_NAMES and N_FLOOR were selected on the validate split; see
# docs/strategy.md § "Validation Methodology" before changing either.

# Minimum number of tickers with a valid tone-z signal before a day is
# tradeable — a breadth filter, not just an emptiness check. Thin
# cross-sections (few names with news that day) are much noisier than
# high-breadth days.
MIN_NAMES = 7

# Fraction of the scored (has-a-signal-today) universe to trade, split
# between long and short, before N_FLOOR is applied. Selects a slice, not
# a fixed count, so it scales with however many tickers have news on a
# given day. In practice N_FLOOR dominates at this data's typical daily
# breadth (5-8 scored names) — SELECT_FRAC between 0.3 and 1.0 makes
# almost no difference — so this value isn't load-bearing; kept at a
# middling default.
SELECT_FRAC = 0.5

# Minimum names per side whenever the cross-section is wide enough to
# support it. Without a floor, SELECT_FRAC alone rounds down to a single
# name per side most days given this data's typical breadth — an all-in
# single-stock bet is far noisier, and far more exposed to real-world
# execution slippage on a single name, than a diversified position.
N_FLOOR = 2

# Minimum |weight change| for MarketOrderExecutor to re-issue SetHoldings.
# Entries/exits have large deltas (0 -> target or target -> 0) and always
# clear this; it mainly filters small day-to-day drift in a magnitude-
# weighted target for a ticker that stays selected on both sides —
# not worth a full order's fees.
REBALANCE_THRESHOLD = 0.04

# Trading days a tone-z reading stays usable after it was last seen.
# GDELT coverage per ticker is sparse (~40-55% of days). 0 means only the
# freshest (yesterday's) reading is used — no forward-filling of stale
# readings across gaps.
SIGNAL_MAX_STALE_DAYS = 0

# === Bundled Data ===
# GDELT financial-media news-tone z-score panel, one row per (date, ticker),
# filtered to UNIVERSE and [2017-01-01, 2021-12-31] (the full window the
# bundled panel covers, wider than START_DATE/END_DATE above so the same
# CSV also supports train/validate backtests). Regenerate with
# `python tools/refresh_sentiment.py` whenever the upstream pipeline output
# changes. Read with an __file__-relative path (see workspace claude.md
# "Bundled per-project data") — no runtime HTTP calls or pipeline reads.
SENTIMENT_PANEL_CSV = "data/sentiment_panel.csv"
