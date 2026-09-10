# region imports
from AlgorithmImports import *
# endregion


class MarketOrderExecutor:
    """
    Execution organism for Alpha101Portfolio.

    Applies target weights via SetHoldings — market orders only. Tickers in
    `universe` absent from `targets` (or with weight 0.0) are liquidated. Positive
    weights go long, negative weights go short — SetHoldings handles both sides
    identically.

    main.py passes only the *active* names (currently held or newly targeted), not
    all ~300 subscriptions, so a rebalance touches a few dozen securities rather
    than the whole universe.

    A ticker with no price data yet is skipped (with a log line if it had a
    non-zero target) — a company can enter the scored universe before its local
    price history begins.

    A rebalance dead-band (skip trades below some fraction of NAV, unless
    opening, closing, or flipping a position) was tried and dropped: at every
    width tested, order count converged to what unconditional SetHoldings
    already produces, meaning essentially every trade in this book is a
    genuine open/close/flip, not incidental drift correction. See
    docs/strategy.md for the numbers.

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
