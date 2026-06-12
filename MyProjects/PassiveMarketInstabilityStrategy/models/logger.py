# region imports
from AlgorithmImports import *
# endregion

from domain.models import PassivePressureSignal, PortfolioTargets


class PortfolioLogger:
    def __init__(self, algorithm: QCAlgorithm):
        self._algo = algorithm

    def log_rebalance(self, signal: PassivePressureSignal, targets: PortfolioTargets) -> None:
        self._algo.Log(
            f"REBALANCE | {signal.date.date()} | "
            f"p(t)={signal.passive_share:.3f} | "
            f"avg_quintile={signal.avg_pressure_quintile:.1f} | "
            f"overlay={'ON' if signal.overlay_active else 'OFF'} | "
            f"scale={signal.exposure_scale:.2f}"
        )
