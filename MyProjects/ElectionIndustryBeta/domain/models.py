"""
Data models for ElectionIndustryBeta.

Layer: ATOMS (pure data types, no dependencies except stdlib).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, runtime_checkable


class PositionState(Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalDirection(Enum):
    LONG = 1
    FLAT = 0
    SHORT = -1


@dataclass
class Signal:
    """Trading signal DTO."""
    symbol: str
    direction: SignalDirection
    strength: float
    timestamp: datetime

    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Signal strength must be 0-1, got {self.strength}")


@dataclass
class PositionInfo:
    symbol: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pnl: float
    state: PositionState = PositionState.FLAT


@dataclass
class TradeRecord:
    date: datetime
    symbol: str
    action: str  # "BUY", "SELL", "CLOSE"
    quantity: float
    price: float
    pnl: Optional[float] = None


@runtime_checkable
class Logger(Protocol):
    def Debug(self, message: str) -> None: ...
    def Log(self, message: str) -> None: ...
    def Error(self, message: str) -> None: ...
