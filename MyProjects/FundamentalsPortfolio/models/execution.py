# region imports
from AlgorithmImports import *
# endregion


class MarketOrderExecutor:
    """
    Execution organism for FundamentalsPortfolio.

    Applies target weights via SetHoldings — market orders only.
    Tickers in `universe` absent from `targets` (or with weight 0.0) are
    liquidated. Positive weights go long, negative weights go short —
    SetHoldings handles both sides identically.

    main.py passes only the *active* names (currently held or newly
    targeted), not all ~1,000 subscriptions, so a rebalance touches a few
    hundred securities rather than the whole universe.

    A ticker with no price data yet is skipped (with a log line if it had a
    non-zero target) — a company can enter the scored universe before its
    local price history begins.

    Layer: ORGANISM (orchestrates order execution).
    """

    def execute(
        self,
        algorithm: QCAlgorithm,
        universe: list[str],
        targets: dict[str, float],
    ) -> None:
        for ticker in universe:
            weight = targets.get(ticker, 0.0)
            security = algorithm.Securities[ticker]
            if not security.HasData or security.Price <= 0:
                if weight != 0.0:
                    algorithm.Log(f"[MarketOrderExecutor] {ticker}: no price data on {algorithm.Time.date()}, "
                                  f"skipping target {weight:+.3f}")
                continue
            algorithm.SetHoldings(ticker, weight)
