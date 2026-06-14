# region imports
from AlgorithmImports import *
# endregion

from domain.models import PassivePressureSignal, PortfolioTargets
from domain.config import UNIVERSE


class PassivePressurePortfolio:
    """
    Equal-weight portfolio with passive-pressure risk overlay.

    Base position: equal weight across all universe members.
    Overlay: when passive pressure is elevated, scale gross exposure
    down by the factor provided in the signal.

    This is a research scaffold — the base allocation is intentionally
    naive so the overlay effect is isolated.
    """

    def compute(self, signal: PassivePressureSignal) -> PortfolioTargets:
        n = len(UNIVERSE)
        base_weight = 1.0 / n if n > 0 else 0.0
        scaled_weight = base_weight * signal.exposure_scale

        weights = {ticker: scaled_weight for ticker in UNIVERSE}

        return PortfolioTargets(
            weights=weights,
            exposure_scale=signal.exposure_scale,
            diagnostics={
                "passive_share": signal.passive_share,
                "avg_quintile": signal.avg_pressure_quintile,
                "high_pressure_fraction": signal.high_pressure_fraction,
                "overlay_active": float(signal.overlay_active),
            },
        )
