# region imports
from AlgorithmImports import *

from datetime import datetime, timedelta
from io import StringIO
import pandas as pd

from domain.config import (
    UNIVERSE, BENCHMARK, LOOKBACK, K,
    START_DATE, END_DATE, CASH,
    TRUMP_PROB_CSV,
)
from models import (
    ElectionBetaAlpha,
    ElectionBetaPortfolio,
    MarketOrderExecutor,
    PortfolioLogger,
)
# endregion


class ElectionIndustryBeta(QCAlgorithm):
    """
    Trades the Polymarket election-driven industry-beta signal from
    notebook `infrastructure/marimo/notebooks/election_industry_returns.py`.

    Each market day at +5 min from open:
      1. Pull LOOKBACK+5 days of daily history for the 19-ETF universe
      2. Compute each ETF's rolling beta to ΔP(Trump win probability)
      3. Long top-K, short bottom-K, weights ∝ β (gross exposure 100%)
      4. Apply targets with SetHoldings (market orders)

    Architecture: atomic structure
      - Composition root: this file
      - Organisms:        models/{alpha, portfolio, execution, logger}.py
      - Molecules+Atoms:  domain/{config, models, signals}.py

    The β math lives in `domain/signals/election_beta.py`, which is a
    symlink to `MyProjects/shared/signals/election_beta.py` (pure Python).
    """

    def Initialize(self) -> None:
        # === Backtest configuration ===
        self.SetStartDate(*START_DATE)
        self.SetEndDate(*END_DATE)
        self.SetCash(CASH)
        self.SetBenchmark(BENCHMARK)

        # === Universe — manual AddEquity per ticker (no coarse universe) ===
        self._symbols: dict[str, Symbol] = {}
        for ticker in UNIVERSE:
            self._symbols[ticker] = self.AddEquity(
                ticker, Resolution.Daily
            ).Symbol
        # Benchmark needs a subscription so scheduling on its calendar works.
        if BENCHMARK not in self._symbols:
            self.AddEquity(BENCHMARK, Resolution.Daily)

        # === Warmup — cover the longest lookback the strategy needs ===
        self.SetWarmUp(timedelta(days=LOOKBACK + 10))

        # === Load bundled Polymarket snapshot ===
        # data/trump_prob.csv is created by tools/refresh_trump_prob.py
        # and shipped with the project.
        self._trump_prob = self._load_trump_prob()

        # === Wire organisms ===
        self._alpha     = ElectionBetaAlpha(lookback=LOOKBACK)
        self._portfolio = ElectionBetaPortfolio(k=K)
        self._executor  = MarketOrderExecutor()
        self._logger    = PortfolioLogger(self)

        # === Daily scheduled rebalance ===
        self.Schedule.On(
            self.DateRules.EveryDay(BENCHMARK),
            self.TimeRules.AfterMarketOpen(BENCHMARK, 5),
            self._rebalance,
        )

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def OnData(self, data: Slice) -> None:
        pass

    def OnOrderEvent(self, order_event: OrderEvent) -> None:
        if order_event.Status != OrderStatus.Filled:
            return
        action = "BUY" if order_event.FillQuantity > 0 else "SELL"
        self._logger.log_trade(
            date=self.Time,
            symbol=order_event.Symbol,
            action=action,
            quantity=float(order_event.FillQuantity),
            price=float(order_event.FillPrice),
        )

    def OnEndOfAlgorithm(self) -> None:
        self._logger.save_all()

    # ------------------------------------------------------------------
    # Scheduled handler
    # ------------------------------------------------------------------

    def _rebalance(self) -> None:
        if self.IsWarmingUp:
            return

        # 1. Build returns DataFrame for the universe over the lookback.
        returns = self._recent_returns()
        if returns is None or returns.empty:
            return

        # 2. Compute signal — latest rolling β per ETF.
        betas = self._alpha.compute_signals(returns, self._trump_prob)
        if betas.dropna().empty:
            return

        # 3. Convert to portfolio targets.
        targets = self._portfolio.to_targets(betas)

        # 4. Execute.
        self._executor.execute(self, UNIVERSE, targets)

        # 5. Snapshot for ObjectStore analysis.
        prob_today, delta_today = self._latest_prob()
        gross = sum(abs(w) for w in targets.values())
        n_long  = sum(1 for w in targets.values() if w > 0)
        n_short = sum(1 for w in targets.values() if w < 0)
        self._logger.log_daily_snapshot(
            date=self.Time,
            nav=float(self.Portfolio.TotalPortfolioValue),
            gross_exposure=gross,
            n_long=n_long,
            n_short=n_short,
            p_trump=prob_today,
            delta_p=delta_today,
        )
        for ticker, weight in targets.items():
            if weight == 0.0:
                continue
            symbol = self._symbols[ticker]
            price = float(self.Securities[symbol].Price)
            qty = float(self.Portfolio[symbol].Quantity)
            self._logger.log_position(
                date=self.Time,
                symbol=ticker,
                quantity=qty,
                price=price,
                target_weight=weight,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_trump_prob(self) -> pd.Series:
        """Read the bundled Polymarket snapshot from disk.

        Tries the project working directory first (local backtest), then
        ObjectStore (cloud, if uploaded). Falls back to an empty Series so
        Initialize never raises — _rebalance will simply produce all-zero
        betas if the data is missing.
        """
        try:
            df = pd.read_csv(TRUMP_PROB_CSV, parse_dates=["date"], index_col="date")
            return df["prob_trump"].astype(float).sort_index()
        except FileNotFoundError:
            self.Debug(f"{TRUMP_PROB_CSV} not on disk; trying ObjectStore")
        try:
            blob = self.ObjectStore.Read(TRUMP_PROB_CSV)
            df = pd.read_csv(StringIO(blob), parse_dates=["date"], index_col="date")
            return df["prob_trump"].astype(float).sort_index()
        except Exception as e:
            self.Error(f"Trump-probability CSV unavailable: {e}")
            return pd.Series(dtype=float)

    def _recent_returns(self) -> pd.DataFrame | None:
        """Daily simple returns (percent) for the universe over LOOKBACK+5 days."""
        symbols = [self._symbols[t] for t in UNIVERSE]
        bars = self.History(symbols, LOOKBACK + 5, Resolution.Daily)
        if bars is None or bars.empty:
            return None
        # `History` returns a multi-index (symbol, time). Pivot to wide.
        try:
            closes = bars["close"].unstack(level=0)
        except Exception:
            return None
        closes.columns = [str(c).split()[0] for c in closes.columns]  # strip exchange
        # Reindex to the ticker order in UNIVERSE; drop any tickers without data.
        closes = closes.reindex(columns=[t for t in UNIVERSE if t in closes.columns])
        returns_pct = closes.pct_change().dropna(how="all") * 100.0
        return returns_pct

    def _latest_prob(self) -> tuple[float, float]:
        """Most recent Polymarket Trump probability and 1-day change at self.Time."""
        if self._trump_prob.empty:
            return (float("nan"), float("nan"))
        window = self._trump_prob[self._trump_prob.index <= pd.Timestamp(self.Time.date())]
        if len(window) < 2:
            return (float(window.iloc[-1]) if len(window) else float("nan"),
                    float("nan"))
        return (float(window.iloc[-1]), float(window.iloc[-1] - window.iloc[-2]))
