# region imports
from AlgorithmImports import *
# endregion

from domain.models import PortfolioTargets


class MarketOrderExecutor:
    """Apply portfolio targets via SetHoldings (market orders)."""

    def execute(self, algorithm: QCAlgorithm, targets: PortfolioTargets, symbols: dict) -> None:
        for ticker, weight in targets.weights.items():
            if ticker in symbols:
                algorithm.SetHoldings(symbols[ticker], weight)
