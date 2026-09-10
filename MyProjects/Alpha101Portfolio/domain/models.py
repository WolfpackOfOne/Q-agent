"""
DTOs and enums for Alpha101Portfolio.

Layer: ATOMS (pure data structures — Python stdlib only, no LEAN imports).
"""

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    """Which side of the dollar-neutral book a position sits on."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

    @classmethod
    def from_weight(cls, weight: float) -> "Side":
        if weight > 0:
            return cls.LONG
        if weight < 0:
            return cls.SHORT
        return cls.FLAT


@dataclass(frozen=True)
class AlphaScore:
    """One stock's model score on one weekly scoring date."""

    ticker: str
    score: float


@dataclass(frozen=True)
class TargetPosition:
    """A target weight for one ticker on one rebalance."""

    ticker: str
    weight: float

    @property
    def side(self) -> Side:
        return Side.from_weight(self.weight)
