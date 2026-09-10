# region imports
from AlgorithmImports import *
# endregion


class MarketOrderExecutor:
    """
    Execution organism for NewsSentimentAlpha.

    Applies target weights via SetHoldings — market orders only.
    Tickers absent from `targets` (or with weight 0.0) are liquidated.

    Skips re-issuing SetHoldings for a ticker whose target weight hasn't
    moved by more than `tol` since the last call. At the default
    `tol=1e-9` this only catches exact no-ops (price-drift
    micro-rebalancing of an unchanged target — see below). Set higher
    (e.g. `domain/config.py::REBALANCE_THRESHOLD`) to also skip small,
    immaterial weight adjustments on names that are staying in the
    portfolio but whose magnitude-weighted target drifted slightly —
    those cost a full order for little economic effect.

    Even at `tol=1e-9`: calling SetHoldings with the *same* weight every
    day still submits small orders to correct for price drift since the
    last call — a form of daily micro-rebalancing that isn't part of the
    strategy definition and materially adds to turnover/fees for names
    that are simply staying put. This changes nothing about *which*
    weights the strategy targets, only skips redundant order submission.

    Layer: ORGANISM (orchestrates order execution).
    """

    def __init__(self, tol: float = 1e-9):
        self.tol = tol
        self._last_issued: dict[str, float] = {}

    def execute(
        self,
        algorithm: QCAlgorithm,
        universe: list[str],
        targets: dict[str, float],
    ) -> None:
        for ticker in universe:
            weight = targets.get(ticker, 0.0)
            if abs(weight - self._last_issued.get(ticker, 0.0)) <= self.tol:
                continue
            algorithm.SetHoldings(ticker, weight)
            self._last_issued[ticker] = weight
