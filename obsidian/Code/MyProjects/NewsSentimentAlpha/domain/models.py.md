---
path: "MyProjects/NewsSentimentAlpha/domain/models.py"
hub: "NewsSentimentAlpha"
layer: "Molecule / Atom"
lines: 93
tags:
  - "code/python"
  - "projects/NewsSentimentAlpha"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py"
---
# models.py

`MyProjects/NewsSentimentAlpha/domain/models.py` · hub [[Hubs/Projects/NewsSentimentAlpha|NewsSentimentAlpha]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py)

## Purpose

Data models for NewsSentimentAlpha.

Layer: ATOMS (pure data types, no dependencies except stdlib)

Contains:
- Enums for state tracking
- DTOs for data transfer
- Protocols for interfaces

## Dependencies


**Imports (external):** [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#enum|enum]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/MyProjects/NewsSentimentAlpha/domain/__init__.py|__init__.py]]

## Classes

### class `PositionState`(Enum)

[line 20](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L20)

Position lifecycle states.


### class `SignalDirection`(Enum)

[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L27)

Signal directions.


### class `Signal`

[line 37](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L37)

Trading signal DTO.

Not currently used — main.py passes plain `dict[ticker, tone_z]` /
`dict[ticker, weight]` between NewsToneAlpha and
NewsToneLongShortPortfolio instead. Kept for parity with the atomic
scaffold; wire it in if a richer per-signal record becomes useful.

- `def __post_init__(self)` — [L50](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L50)

### class `PositionInfo`

[line 56](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L56)

Position information DTO.


### class `TradeRecord`

[line 67](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L67)

Trade record DTO.


### class `Logger`(Protocol)

[line 80](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L80)

Logging interface.

- `def Debug(self, message: str) -> None` — [L82](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L82)
- `def Log(self, message: str) -> None` — [L83](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L83)
- `def Error(self, message: str) -> None` — [L84](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L84)

### class `PortfolioProvider`(Protocol)

[line 88](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L88)

Portfolio data interface.

- `def get_nav(self) -> float` — [L90](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L90)
- `def get_cash(self) -> float` — [L91](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L91)
- `def get_positions(self) -> dict` — [L92](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/NewsSentimentAlpha/domain/models.py#L92)

## Source

> [!example]- MyProjects/NewsSentimentAlpha/domain/models.py (93 lines)
> ```python
> """
> Data models for NewsSentimentAlpha.
>
> Layer: ATOMS (pure data types, no dependencies except stdlib)
>
> Contains:
> - Enums for state tracking
> - DTOs for data transfer
> - Protocols for interfaces
> """
>
> from dataclasses import dataclass
> from datetime import datetime
> from enum import Enum
> from typing import Optional, Protocol, runtime_checkable
>
>
> # === Enums ===
>
> class PositionState(Enum):
>     """Position lifecycle states."""
>     FLAT = "FLAT"
>     LONG = "LONG"
>     SHORT = "SHORT"
>
>
> class SignalDirection(Enum):
>     """Signal directions."""
>     LONG = 1
>     FLAT = 0
>     SHORT = -1
>
>
> # === Data Transfer Objects ===
>
> @dataclass
> class Signal:
>     """Trading signal DTO.
>
>     Not currently used — main.py passes plain `dict[ticker, tone_z]` /
>     `dict[ticker, weight]` between NewsToneAlpha and
>     NewsToneLongShortPortfolio instead. Kept for parity with the atomic
>     scaffold; wire it in if a richer per-signal record becomes useful.
>     """
>     symbol: str
>     direction: SignalDirection
>     strength: float  # 0.0 to 1.0
>     timestamp: datetime
>
>     def __post_init__(self):
>         if not 0.0 <= self.strength <= 1.0:
>             raise ValueError(f"Signal strength must be 0-1, got {self.strength}")
>
>
> @dataclass
> class PositionInfo:
>     """Position information DTO."""
>     symbol: str
>     quantity: float
>     avg_price: float
>     market_value: float
>     unrealized_pnl: float
>     state: PositionState = PositionState.FLAT
>
>
> @dataclass
> class TradeRecord:
>     """Trade record DTO."""
>     date: datetime
>     symbol: str
>     action: str  # "BUY", "SELL", "CLOSE"
>     quantity: float
>     price: float
>     pnl: Optional[float] = None
>
>
> # === Protocols (Interfaces) ===
>
> @runtime_checkable
> class Logger(Protocol):
>     """Logging interface."""
>     def Debug(self, message: str) -> None: ...
>     def Log(self, message: str) -> None: ...
>     def Error(self, message: str) -> None: ...
>
>
> @runtime_checkable
> class PortfolioProvider(Protocol):
>     """Portfolio data interface."""
>     def get_nav(self) -> float: ...
>     def get_cash(self) -> float: ...
>     def get_positions(self) -> dict: ...
> ```
