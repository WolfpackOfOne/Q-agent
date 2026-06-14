# region imports
from AlgorithmImports import *

from datetime import timedelta

from domain.config import (
    UNIVERSE, BENCHMARK,
    START_DATE, END_DATE, CASH,
    REBALANCE_DAYS,
)
from models import (
    PassivePressureAlpha,
    PassivePressurePortfolio,
    MarketOrderExecutor,
    PortfolioLogger,
)
# endregion


class PassiveMarketInstabilityStrategy(QCAlgorithm):
    """
    Research-only strategy: equal-weight broad equity ETFs with a
    passive-pressure risk overlay.

    The overlay reduces gross exposure when the flow-pressure proxy
    signals elevated passive-share fragility across the universe.
    It is derived from the model in Green, Krishnan, and Sturm (2022).

    This is a backtest scaffold, not a live-trading algorithm.
    Do not add brokerage credentials, live data subscriptions, or
    live execution logic without explicit review.

    Architecture: atomic structure
      - Composition root: this file
      - Organisms:        models/ (alpha, portfolio, execution, logger)
      - Molecules+Atoms:  domain/ (config, models, signals)
    """

    def Initialize(self) -> None:
        self.SetStartDate(*START_DATE)
        self.SetEndDate(*END_DATE)
        self.SetCash(CASH)
        self.SetBenchmark(BENCHMARK)

        self._symbols: dict[str, Symbol] = {}
        for ticker in UNIVERSE:
            self._symbols[ticker] = self.AddEquity(ticker, Resolution.Daily).Symbol
        if BENCHMARK not in self._symbols:
            self.AddEquity(BENCHMARK, Resolution.Daily)

        self.SetWarmUp(timedelta(days=30))

        self._alpha     = PassivePressureAlpha(universe=UNIVERSE)
        self._portfolio = PassivePressurePortfolio()
        self._executor  = MarketOrderExecutor()
        self._logger    = PortfolioLogger(self)

        self._day_counter = 0

        self.Schedule.On(
            self.DateRules.EveryDay(BENCHMARK),
            self.TimeRules.AfterMarketOpen(BENCHMARK, 5),
            self._rebalance,
        )

    def _rebalance(self) -> None:
        if self.IsWarmingUp:
            return

        self._day_counter += 1
        if self._day_counter % REBALANCE_DAYS != 0:
            return

        signal  = self._alpha.compute(self, self._symbols)
        targets = self._portfolio.compute(signal)

        self._executor.execute(self, targets, self._symbols)
        self._logger.log_rebalance(signal, targets)

        self.Plot("Passive Pressure", "passive_share", signal.passive_share)
        self.Plot("Passive Pressure", "avg_quintile", signal.avg_pressure_quintile)
        self.Plot("Passive Pressure", "exposure_scale", signal.exposure_scale)
