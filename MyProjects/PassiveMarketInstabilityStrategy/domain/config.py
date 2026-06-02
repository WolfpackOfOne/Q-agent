"""Strategy configuration for PassiveMarketInstabilityStrategy."""

# Backtest window
START_DATE = (2018, 1, 1)
END_DATE   = (2024, 1, 1)
CASH       = 1_000_000

BENCHMARK = "SPY"

# Universe — broad US equity ETFs (same as PMI notebook)
UNIVERSE = ["SPY", "QQQ", "IWM", "MDY", "VTI"]

# Risk-overlay parameters
# Passive-pressure quintile at or above which we apply the overlay
PRESSURE_QUINTILE_THRESHOLD = 4  # quintile 4 or 5 = high pressure

# When passive pressure is high, scale gross exposure by this factor (< 1 = reduce)
HIGH_PRESSURE_EXPOSURE_SCALE = 0.50

# Passive-share logistic calibration (Haddad et al.)
PASSIVE_SHARE_ALPHA = 0.106
PASSIVE_SHARE_T0    = 30.0       # midpoint year relative to 1994
PASSIVE_SHARE_REF   = 1994       # t=0 calendar year

# Rolling lookback for passive-pressure diagnostics (calendar days)
PRESSURE_LOOKBACK_DAYS = 63      # ~3 months

# Rebalance frequency
REBALANCE_DAYS = 21              # monthly
