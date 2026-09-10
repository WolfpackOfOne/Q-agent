# region imports
from AlgorithmImports import *

import os
from io import StringIO

import pandas as pd

from domain.config import FUNDAMENTAL_SCORES_CSV, MAX_SCORE_AGE_DAYS
# endregion


class FundamentalRankAlpha:
    """
    Alpha organism for FundamentalsPortfolio.

    Serves the most recent point-in-time cross-section of model scores from
    the bundled `data/fundamental_scores.csv` (columns: date, ticker, score).
    The scores were produced off-platform by the research notebook
    (`infrastructure/marimo/notebooks/fundamentals_portfolio.py`) from a
    model fit on 2005–2021 data only, applied to the held-out 2022–2023 test
    period, for the point-in-time top-1000 US companies each quarter. Each
    score row is dated the calendar quarter-end on which its inputs were
    already public (features are dated by `rdq`, the earnings release date),
    so a row is usable from its date forward.

    On each rebalance the newest score date <= today is taken as the active
    cross-section. If that batch is older than MAX_SCORE_AGE_DAYS the
    strategy goes flat rather than trade on a stale ranking.

    The file also defines the tradable universe: `tickers` is every ticker
    that appears in it, and main.py subscribes to exactly those.

    Layer: ORGANISM (orchestrates signal generation). Does no I/O after
    construction.
    """

    def __init__(self, algorithm: QCAlgorithm):
        self._scores = self._load(algorithm)
        self.tickers: list[str] = sorted(self._scores["ticker"].unique().tolist()) if not self._scores.empty else []

    def compute_signals(self, algorithm: QCAlgorithm) -> dict[str, float]:
        """Return {ticker: score} for the newest score batch dated <= today, or {} if none/stale."""
        if self._scores.empty:
            return {}
        now = pd.Timestamp(algorithm.Time.date())
        available = self._scores[self._scores["date"] <= now]
        if available.empty:
            return {}
        latest = available["date"].max()
        if (now - latest).days > MAX_SCORE_AGE_DAYS:
            algorithm.Log(f"[FundamentalRankAlpha] newest scores ({latest.date()}) are stale on {now.date()} — flat")
            return {}
        batch = available[available["date"] == latest]
        return {t: float(s) for t, s in zip(batch["ticker"], batch["score"])}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self, algorithm: QCAlgorithm) -> pd.DataFrame:
        """Read the bundled score file (__file__-relative path, plain relative path, then ObjectStore)."""
        candidates = []
        try:
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # models/ -> project root
            candidates.append(os.path.join(here, FUNDAMENTAL_SCORES_CSV))
        except NameError:
            pass
        candidates.append(FUNDAMENTAL_SCORES_CSV)

        for path in candidates:
            try:
                df = self._tidy(pd.read_csv(path, parse_dates=["date"]))
                algorithm.Log(f"[FundamentalRankAlpha] loaded {len(df)} score rows, {df['ticker'].nunique()} tickers from {path} "
                              f"({df['date'].min().date()} → {df['date'].max().date()})")
                return df
            except FileNotFoundError:
                continue
            except Exception as e:
                algorithm.Log(f"[FundamentalRankAlpha] error reading {path}: {type(e).__name__}: {e}")

        try:
            blob = algorithm.ObjectStore.Read(FUNDAMENTAL_SCORES_CSV)
            if blob:
                df = self._tidy(pd.read_csv(StringIO(blob), parse_dates=["date"]))
                algorithm.Log(f"[FundamentalRankAlpha] loaded {len(df)} score rows from ObjectStore")
                return df
        except Exception as e:
            algorithm.Error(f"[FundamentalRankAlpha] ObjectStore read failed: {type(e).__name__}: {e}")

        algorithm.Error("[FundamentalRankAlpha] all sources failed — no scores, strategy will stay flat")
        return pd.DataFrame(columns=["date", "ticker", "score"])

    @staticmethod
    def _tidy(df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(subset=["date", "ticker", "score"]).copy()
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df["ticker"] = df["ticker"].astype(str).str.upper()
        return df.sort_values(["date", "ticker"]).reset_index(drop=True)
