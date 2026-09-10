# region imports
from AlgorithmImports import *
import pandas as pd
# endregion


class NewsToneAlpha:
    """
    Alpha organism for NewsSentimentAlpha.

    Surfaces each ticker's financial-media news-tone z-score. GDELT
    coverage of any one ticker is sparse (each name only has a real
    reading on ~40-55% of days in this bundled panel), which is the
    dominant driver of this strategy's turnover — a ticker isn't
    "borderline ranked", it simply has no reading at all on most days, so
    the ranked long/short membership changes almost completely day to
    day. Two lookup modes trade off signal freshness against turnover:

    - `raw_reading(date)`: this EXACT calendar date's own reading, no
      forward-fill. Used at `max_stale_days=0`.
    - `record()` / `eligible_signals()`: a bounded-staleness cache — a
      reading stays usable for up to `max_stale_days` trading days after
      it was last seen, instead of vanishing the instant a ticker goes
      quiet. `main.py` chooses which mode via
      `domain/config.py::SIGNAL_MAX_STALE_DAYS`.

    One-day lag (yesterday's reading only, never today's) is applied by
    the caller (main.py): it consumes `eligible_signals()` (state as of
    the *previous* call) before capturing today's own reading via
    `record()` — this is the actual mechanism, not calendar-day
    arithmetic, so it lags by exactly one trading day regardless of
    weekends/holidays.

    Layer: ORGANISM (orchestrates signal generation). The bundled CSV is
    loaded once by main.py and handed to this class as a wide DataFrame
    (index=date, columns=ticker, values=tone_z) — this class does no I/O
    itself.
    """

    def __init__(self, tone_wide: pd.DataFrame):
        self.name = "NewsToneAlpha"
        self._tone_wide = tone_wide.sort_index()
        # ticker -> (tone_z, age_in_trading_days_since_last_seen)
        self._last_seen: dict[str, tuple[float, int]] = {}

    def raw_reading(self, date: pd.Timestamp) -> dict[str, float]:
        """This exact date's own tone-z per ticker — no ffill, no lag.

        Args:
            date: calendar date to read (normalised to midnight).

        Returns:
            dict[ticker, tone_z]: only tickers with a non-null reading on
            this exact date. Empty dict if the date isn't in the panel at
            all, or every ticker was null that day.
        """
        d = date.normalize()
        if d not in self._tone_wide.index:
            return {}
        return self._tone_wide.loc[d].dropna().to_dict()

    def record(self, reading: dict[str, float], max_stale_days: int) -> None:
        """Age the staleness cache by one trading day, then overlay `reading`.

        Call once per rebalance with that day's `raw_reading(today)`.
        Entries older than `max_stale_days` are dropped so
        `eligible_signals` never has to filter unbounded history.
        """
        aged = {t: (z, age + 1) for t, (z, age) in self._last_seen.items()}
        for ticker, z in reading.items():
            aged[ticker] = (z, 0)
        self._last_seen = {t: v for t, v in aged.items() if v[1] <= max_stale_days}

    def eligible_signals(self, max_stale_days: int) -> dict[str, float]:
        """Every ticker whose last-seen reading is within `max_stale_days`.

        At `max_stale_days=0` this only returns tickers seen on the most
        recent `record()` call — equivalent to `raw_reading` with no
        staleness at all.
        """
        return {t: z for t, (z, age) in self._last_seen.items() if age <= max_stale_days}
