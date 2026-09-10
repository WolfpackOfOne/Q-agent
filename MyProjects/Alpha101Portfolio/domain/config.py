"""
Configuration constants for Alpha101Portfolio.

Layer: ATOMS (pure constants, no dependencies except stdlib).

Usage:
    from domain.config import *
"""

# === ObjectStore ===
OBJECTSTORE_NAMESPACE = "alpha101_portfolio"

# === Universe ===
# There is no hard-coded ticker list. The tradable universe is every ticker that
# appears in data/alpha_scores.csv — the point-in-time largest 300 US companies
# by market cap at each quarter-end, scored by the research notebook
# (infrastructure/marimo/notebooks/alpha101_portfolio.py). main.py subscribes to
# those tickers at Initialize. Tickers are the names assigned by the WRDS broad
# pipeline and have local daily bars at
# infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip.
BENCHMARK = "SPY"

# === Rebalance schedule ===
# Daily. The formulaic alphas are built from one-day price and volume changes and
# their predictive power is concentrated at a one-day horizon: measured on the
# training period, the average absolute information coefficient falls from 0.0090
# at a 1-day horizon to 0.0065 at 5 days. DateRules.EveryDay(BENCHMARK) fires
# once per trading session on the benchmark's calendar, matching the notebook's
# scoring dates.

# === Alpha scores (bundled, point-in-time) ===
# Schema: date,ticker,score — one row per stock per trading day. Scores are
# produced by the notebook from a model fit on 2015-2021 only and exported for
# the held-out 2021-2024 test window. The algorithm only ever uses the newest
# batch with date <= today — see models/alpha.py.
ALPHA_SCORES_CSV = "data/alpha_scores.csv"

# A score batch older than this on a rebalance day means the notebook produced
# nothing for that session -> go flat rather than trade a stale ranking.
MAX_SCORE_AGE_DAYS = 4

# === Portfolio construction ===
# Dollar-neutral long/short: long the top LONG_SHORT_FRACTION of scored names,
# short the bottom LONG_SHORT_FRACTION, equal-weighted within each side,
# GROSS_EXPOSURE total (half long / half short). Quintile buckets hold roughly 60
# names per side out of a 300-name universe, which diversifies single-stock risk
# better than a decile at the same signal strength. Rank/weight math lives in
# domain/signals/cross_sectional_rank.py (symlink to
# ../../../shared/signals/cross_sectional_rank.py).
LONG_SHORT_FRACTION = 0.2         # top/bottom quintile (entry threshold)
GROSS_EXPOSURE = 1.0              # 50% long + 50% short
MIN_SCORED_NAMES = 50             # thinner cross-section than this -> flat

# === Turnover hysteresis ===
# A name already held stays in the book as long as it remains within the wider
# HOLD_FRACTION band, even after its rank drifts out of the top/bottom
# LONG_SHORT_FRACTION entry band; it is only removed once its rank exits
# HOLD_FRACTION entirely. Plain daily re-ranking (no buffer) was rebuilding most
# of the book every session on score noise with no persistence, at ~130% daily
# turnover, and that turnover cost consumed nearly all of the gross edge in LEAN.
# Validated on 2017-2020 (not touching the 2021-2024 test window): at the 2 bps
# cost assumption, hysteresis cut turnover 130% -> 109%/session and raised
# Sharpe 1.33 -> 1.80 versus the plain quintile rule, entry threshold unchanged.
HOLD_FRACTION = 0.3

# === Transaction costs ===
# The book turns over roughly 150% of gross per session, so the result is highly
# sensitive to execution cost. The backtest charges a flat per-trade fee of
# COST_BPS_PER_SIDE basis points of notional instead of LEAN's default per-share
# commission, so the engine's cost assumption is explicit and matches the
# notebook's. 2 bps is representative of institutional execution in the most
# liquid US large caps; retail-level costs are several times higher.
COST_BPS_PER_SIDE = 2.0

# === Backtest defaults ===
# Held-out test window. The research split is 60/20/20 on calendar years:
# train 2005-2016, validate 2017-2020, test 2021-2024.
START_DATE = (2021, 1, 1)
END_DATE = (2024, 12, 31)
CASH = 1_000_000
