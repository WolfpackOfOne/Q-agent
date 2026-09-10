# region imports
from AlgorithmImports import *

from datetime import timedelta
from io import StringIO
import pandas as pd

from domain.config import (
    UNIVERSE, BENCHMARK, START_DATE, END_DATE, CASH, SENTIMENT_PANEL_CSV,
    SIGNAL_MAX_STALE_DAYS, REBALANCE_THRESHOLD,
)
from models import (
    NewsToneAlpha,
    NewsToneLongShortPortfolio,
    MarketOrderExecutor,
    PortfolioLogger,
)
# endregion


class NewsSentimentAlphaAlgorithm(QCAlgorithm):
    """
    NewsSentimentAlpha — daily long/short news-tone strategy.

    Each day, among whichever of the 10-stock universe have a valid
    financial-media (GDELT) news-tone z-score as of *yesterday*, ranks
    them and trades a selective top/bottom slice — long the top, short
    the bottom, weighted by signal magnitude, with a minimum-names-per-
    side floor to avoid single-stock concentration. Sits flat on days
    with fewer than MIN_NAMES scored tickers.

    Data sources:
      - WRDS/CRSP daily equity prices (already local):
        infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip
      - Bundled GDELT financial-media news-tone z-score CSV
        (data/sentiment_panel.csv) — filtered cut of the news_events_sentiment
        pipeline's financial-only panel; refreshed via tools/refresh_sentiment.py.
        The algorithm never makes HTTP calls or reads the pipeline directly.

    Architecture: Atomic Structure
    - Composition Root: This file (main.py)
    - Organisms: models/ (alpha, portfolio, execution, logger)
    - Molecules + Atoms: domain/ (business logic, DTOs, config, signals)

    Pattern: teaching/direct SetHoldings (not the QC AlphaModel framework
    lifecycle) — see AGENTS.md "Pattern Choice" and
    MyProjects/ElectionIndustryBeta/ for the worked example this mirrors.
    """

    def Initialize(self):
        # === Backtest Configuration ===
        self.SetStartDate(*START_DATE)
        self.SetEndDate(*END_DATE)
        self.SetCash(CASH)
        self.SetBenchmark(BENCHMARK)
        # Explicit margin account — the strategy holds short positions.
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # === Universe — manual AddEquity per ticker (static universe) ===
        self._symbols: dict[str, Symbol] = {}
        for ticker in UNIVERSE:
            security = self.AddEquity(ticker, Resolution.Daily)
            # IB's per-share commission model was calibrated for its legacy
            # tiered pricing; the modern $0-commission tier (IBKR Lite, and
            # every major US retail broker as of 2019+) is how this
            # strategy would actually be traded. Margin/short mechanics
            # from the brokerage model above are unaffected — only the
            # commission is overridden. Fill price still reflects the
            # market price at execution, so this isn't zero-cost trading,
            # just zero*commission*.
            security.SetFeeModel(ConstantFeeModel(0))
            self._symbols[ticker] = security.Symbol
        # Benchmark needs its own subscription so scheduling on its
        # calendar works even though it isn't traded.
        if BENCHMARK not in self._symbols:
            self.AddEquity(BENCHMARK, Resolution.Daily)

        # === Warmup ===
        self.SetWarmUp(timedelta(days=5))

        # === Load bundled news-tone panel ===
        # data/sentiment_panel.csv is created by tools/refresh_sentiment.py
        # and shipped with the project.
        tone_wide = self._load_sentiment_panel()

        # === Wire organisms ===
        self._alpha = NewsToneAlpha(tone_wide)
        self._portfolio = NewsToneLongShortPortfolio()
        self._executor = MarketOrderExecutor(tol=REBALANCE_THRESHOLD)
        self._logger = PortfolioLogger(self)


        # === Scheduled Events — daily rebalance ===
        # Scheduling near the close instead was tried (to better match a
        # close-to-close return window) but LEAN rejects every order:
        # for Resolution.Daily securities, there's no tradable price yet
        # at an intraday timestamp before that day's single bar closes,
        # so BrokerageModel.CanSubmitOrder fails for all of them. Daily
        # resolution can only be traded via a schedule that fires once
        # the bar is actually available — AfterMarketOpen is what works.
        self.Schedule.On(
            self.DateRules.EveryDay(BENCHMARK),
            self.TimeRules.AfterMarketOpen(BENCHMARK, 5),
            self._rebalance,
        )

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def OnData(self, data: Slice):
        """Process incoming data. Rebalancing is schedule-driven; nothing
        to do here."""
        pass

    def OnOrderEvent(self, orderEvent: OrderEvent):
        """Log fills to the ObjectStore trade record."""
        if orderEvent.Status != OrderStatus.Filled:
            return
        action = "BUY" if orderEvent.FillQuantity > 0 else "SELL"
        self._logger.log_trade(
            date=self.Time,
            symbol=orderEvent.Symbol,
            action=action,
            quantity=float(orderEvent.FillQuantity),
            price=float(orderEvent.FillPrice),
        )

    def OnEndOfAlgorithm(self):
        """Finalize and save data to ObjectStore."""
        self._logger.save_all()

    # ------------------------------------------------------------------
    # Scheduled handler
    # ------------------------------------------------------------------

    def _rebalance(self) -> None:
        if self.IsWarmingUp:
            return

        # 1. Trade on readings captured as of YESTERDAY — never today's, so
        #    the strategy never looks ahead. `record()` is called at the
        #    end of this method (step 4), so at this point the cache still
        #    reflects state as of the *previous* call. Readings stay
        #    eligible for up to SIGNAL_MAX_STALE_DAYS trading days after
        #    they were last seen (0 = yesterday's own exact reading only,
        #    matching the notebook; see domain/config.py).
        signals = self._alpha.eligible_signals(SIGNAL_MAX_STALE_DAYS)
        targets = self._portfolio.to_targets(signals)

        # 2. Execute. Empty dict (too few scored tickers, or no signal yet)
        #    means flat — the executor liquidates everyone.
        self._executor.execute(self, UNIVERSE, targets)

        # 3. Snapshot for ObjectStore analysis.
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
            price = float(self.Securities[symbol].Price)
            qty = float(self.Portfolio[symbol].Quantity)
            self._logger.log_position(
                date=self.Time,
                symbol=ticker,
                quantity=qty,
                price=price,
                target_weight=weight,
            )

        # 4. Capture TODAY's own exact-date reading (no ffill) into the
        #    staleness cache for use on the *next* rebalance — this is what
        #    makes step 1 always trade on readings from strictly before
        #    today.
        as_of = pd.Timestamp(self.Time.date())
        self._alpha.record(self._alpha.raw_reading(as_of), SIGNAL_MAX_STALE_DAYS)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_sentiment_panel(self) -> pd.DataFrame:
        """Read the bundled news-tone panel, pivoted wide (date x ticker).

        Tries three sources in order, since LEAN's runtime working directory
        differs between local Docker (cwd = /LeanCLI) and cloud (cwd varies):
          1. Path resolved from __file__ — most reliable in both environments.
          2. Plain relative path from config — works locally if cwd is project root.
          3. Organisation cloud ObjectStore — populated via
             `lean cloud object-store set "data/sentiment_panel.csv" <path>`.

        Returns an empty DataFrame if every source fails so Initialize never
        raises; _rebalance then no-ops gracefully and the failure is visible
        in the log.
        """
        import os

        candidates = []
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            candidates.append(os.path.join(here, SENTIMENT_PANEL_CSV))
        except NameError:
            pass  # __file__ undefined in some research notebook contexts
        candidates.append(SENTIMENT_PANEL_CSV)

        for path in candidates:
            try:
                df = pd.read_csv(path, parse_dates=["date"])
                wide = self._pivot_tone_panel(df)
                self.Log(f"[_load_sentiment_panel] loaded {len(df)} rows from {path}")
                return wide
            except FileNotFoundError:
                continue
            except Exception as e:
                self.Log(f"[_load_sentiment_panel] error reading {path}: {type(e).__name__}: {e}")

        try:
            blob = self.ObjectStore.Read(SENTIMENT_PANEL_CSV)
            if blob:
                df = pd.read_csv(StringIO(blob), parse_dates=["date"])
                wide = self._pivot_tone_panel(df)
                self.Log(f"[_load_sentiment_panel] loaded {len(df)} rows from ObjectStore")
                return wide
        except Exception as e:
            self.Error(f"[_load_sentiment_panel] ObjectStore read failed: {type(e).__name__}: {e}")

        self.Error("[_load_sentiment_panel] all sources failed — news-tone panel unavailable")
        return pd.DataFrame()

    @staticmethod
    def _pivot_tone_panel(df: pd.DataFrame) -> pd.DataFrame:
        """Long (date, ticker, tone_z) rows -> wide (index=date, columns=ticker)."""
        df = df[df["ticker"].isin(UNIVERSE)]
        wide = df.pivot(index="date", columns="ticker", values="tone_z")
        wide.index = pd.to_datetime(wide.index).normalize()
        return wide.sort_index()
