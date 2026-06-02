"""Domain data-transfer objects for PassiveMarketInstabilityStrategy."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PassivePressureSignal:
    """Snapshot of passive-pressure diagnostics at a single rebalance date."""
    date: object                           # datetime
    passive_share: float                   # logistic p(t) estimate
    avg_pressure_quintile: float           # mean pressure quintile across universe
    high_pressure_fraction: float          # fraction of universe in top two quintiles
    overlay_active: bool                   # True when risk overlay is triggered
    exposure_scale: float                  # target gross exposure scalar (0.0–1.0)


@dataclass
class PortfolioTargets:
    """Target weights produced by the portfolio model."""
    weights: Dict[str, float] = field(default_factory=dict)
    exposure_scale: float = 1.0
    diagnostics: Dict[str, float] = field(default_factory=dict)
