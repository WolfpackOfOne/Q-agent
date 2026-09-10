"""
Data models for FundamentalRankLS.

Layer: ATOMS (pure data types, no dependencies except stdlib)

Contains:
- Enums for state tracking
- DTOs for data transfer
- Protocols for interfaces
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, runtime_checkable


# === Enums ===

class PositionState(Enum):
    """Position lifecycle states."""
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalDirection(Enum):
    """Signal directions."""
    LONG = 1
    FLAT = 0
    SHORT = -1


# === Data Transfer Objects ===

@dataclass
class Signal:
    """Trading signal DTO."""
    symbol: str
    direction: SignalDirection
    strength: float  # 0.0 to 1.0
    timestamp: datetime

    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Signal strength must be 0-1, got {self.strength}")


@dataclass
class PositionInfo:
    """Position information DTO."""
    symbol: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pnl: float
    state: PositionState = PositionState.FLAT


@dataclass
class TradeRecord:
    """Trade record DTO."""
    date: datetime
    symbol: str
    action: str  # "BUY", "SELL", "CLOSE"
    quantity: float
    price: float
    pnl: Optional[float] = None


# === Protocols (Interfaces) ===

@runtime_checkable
class Logger(Protocol):
    """Logging interface."""
    def Debug(self, message: str) -> None: ...
    def Log(self, message: str) -> None: ...
    def Error(self, message: str) -> None: ...


@runtime_checkable
class PortfolioProvider(Protocol):
    """Portfolio data interface."""
    def get_nav(self) -> float: ...
    def get_cash(self) -> float: ...
    def get_positions(self) -> dict: ...
