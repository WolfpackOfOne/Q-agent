# region imports
from AlgorithmImports import *
# endregion


class MarketOrderExecutor:
    """
    Execution organism for ElectionIndustryBeta.

    Applies target weights via SetHoldings — market orders only.
    Tickers absent from `targets` (or with weight 0.0) are liquidated.

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
            algorithm.SetHoldings(ticker, weight)
