# region imports
from AlgorithmImports import *

from datetime import timedelta

from domain.config import (
    BENCHMARK, REBALANCE_MONTHS,
    START_DATE, END_DATE, CASH,
)
from models import (
    FundamentalRankAlpha,
    FundamentalRankPortfolio,
    MarketOrderExecutor,
    PortfolioLogger,
)
# endregion


class FundamentalsPortfolioAlgorithm(QCAlgorithm):
    """
    Quarterly-rebalanced, dollar-neutral long/short on a fundamental score
    across the point-in-time top-1000 US companies by market cap.

    Each rebalance (first trading day of Jan / Apr / Jul / Oct):
      1. Take the newest point-in-time cross-section of scores from
         data/fundamental_scores.csv (columns: date,ticker,score), produced
         by infrastructure/marimo/notebooks/fundamentals_portfolio.py from
         a model fit on 2005–2021 and exported for this held-out 2022–2023
         window. The file also defines the tradable universe.
      2. Long the top LONG_SHORT_FRACTION of scored names, short the bottom
         LONG_SHORT_FRACTION, equal-weighted within each side, 50% long /
         50% short (100% total gross exposure).
      3. Apply with market orders; hold until the next quarterly rebalance.

    The algorithm never sees the model or the raw fundamentals — only the
    score file — and never makes HTTP calls.

    Architecture: Atomic Structure
    - Composition Root: This file (main.py)
    - Organisms: models/ (alpha, portfolio, execution, logger)
    - Molecules + Atoms: domain/ (business logic, DTOs, config, signals)

    The ranking/weighting math lives in domain/signals/cross_sectional_rank.py
    — a symlink to ../../../shared/signals/cross_sectional_rank.py — so the
    LEAN book matches the notebook's backtested construction exactly.
    """

    def Initialize(self) -> None:
        # === Backtest configuration ===
        self.SetStartDate(*START_DATE)
        self.SetEndDate(*END_DATE)
        self.SetCash(CASH)
        self.SetBenchmark(BENCHMARK)

        # Strategy shorts — needs a margin brokerage model.
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # === Alpha first: the score file defines the universe ===
        self._alpha = FundamentalRankAlpha(self)
        self._universe: list[str] = list(self._alpha.tickers)

        # === Universe — manual AddEquity per scored ticker (no coarse universe) ===
        self._symbols: dict[str, Symbol] = {}
        for ticker in self._universe:
            try:
                self._symbols[ticker] = self.AddEquity(ticker, Resolution.Daily).Symbol
            except Exception as e:  # a ticker with no local data must not abort Initialize
                self.Log(f"[Initialize] could not subscribe {ticker}: {type(e).__name__}: {e}")
        self._universe = [t for t in self._universe if t in self._symbols]
        self.Log(f"[Initialize] subscribed {len(self._universe)} tickers from the score file")
        if BENCHMARK not in self._symbols:
            self.AddEquity(BENCHMARK, Resolution.Daily)

        # === Warmup ===
        self.SetWarmUp(timedelta(days=10))

        # === Wire remaining organisms ===
        self._portfolio = FundamentalRankPortfolio()
        self._executor = MarketOrderExecutor()
        self._logger = PortfolioLogger(self)

        # === Scheduled rebalance ===
        # DateRules.MonthStart(BENCHMARK) fires on the first trading day of
        # every month; _rebalance filters down to REBALANCE_MONTHS itself.
        self.Schedule.On(
            self.DateRules.MonthStart(BENCHMARK),
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
        if self.Time.month not in REBALANCE_MONTHS:
            return

        scores = self._alpha.compute_signals(self)
        scores = {t: s for t, s in scores.items() if t in self._symbols}
        if not scores:
            return

        targets = self._portfolio.to_targets(scores)
        # Only touch names that are held or targeted — not all ~1,300 subscriptions.
        active = sorted({t for t in self._universe if targets.get(t, 0.0) != 0.0 or self.Portfolio[self._symbols[t]].Invested})
        self._executor.execute(self, active, targets)

        gross = sum(abs(w) for w in targets.values())
        n_long = sum(1 for w in targets.values() if w > 0)
        n_short = sum(1 for w in targets.values() if w < 0)
        self._logger.log_daily_snapshot(
            date=self.Time,
            nav=float(self.Portfolio.TotalPortfolioValue),
            gross_exposure=gross,
            n_long=n_long,
            n_short=n_short,
        )
        for ticker, weight in targets.items():
            if weight == 0.0:
                continue
            symbol = self._symbols[ticker]
            self._logger.log_position(
                date=self.Time,
                symbol=ticker,
                quantity=float(self.Portfolio[symbol].Quantity),
                price=float(self.Securities[symbol].Price),
                target_weight=weight,
            )
