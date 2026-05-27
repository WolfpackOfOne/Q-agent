"""
Configuration constants for ElectionIndustryBeta.

Layer: ATOMS (pure constants, no dependencies except stdlib).

Usage:
    from domain.config import *
"""

# === ObjectStore ===
OBJECTSTORE_NAMESPACE = "electionbeta"

# === Universe ===
# 19 US sector & industry ETFs from the replication notebook
# (infrastructure/marimo/notebooks/election_industry_returns.py).
UNIVERSE = [
    # Broad SPDR Select Sector ETFs
    "XLE", "XLF", "XLV", "XLI", "XLK", "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC",
    # Trump-themed industry slices
    "XOP", "ITA", "KBE", "IBB", "ICLN", "TAN", "GDX", "ITB",
]
BENCHMARK = "SPY"

# === Signal ===
LOOKBACK = 60   # trading days of history used in the rolling beta regression
K = 3           # long top-K by beta, short bottom-K by beta

# === Polymarket ===
# Trump YES token from the 2024 Presidential Election Winner event.
TRUMP_TOKEN = "21742633143463906290569050155826241533067272736897614950488156847949938836455"
POLYMARKET_PRICES_URL = "https://clob.polymarket.com/prices-history"
TRUMP_PROB_CSV = "data/trump_prob.csv"

# === Backtest defaults ===
START_DATE = (2024, 3, 15)
END_DATE   = (2024, 11, 7)
CASH       = 100_000
