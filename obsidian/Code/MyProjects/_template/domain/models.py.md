---
path: "MyProjects/_template/domain/models.py"
hub: "_template"
layer: "Molecule / Atom"
lines: 87
tags:
  - "code/python"
  - "projects/_template"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py"
---
# models.py

`MyProjects/_template/domain/models.py` · hub [[Hubs/Projects/_template|_template]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py)

## Purpose

Data models for {{STRATEGY_NAME}}.

Layer: ATOMS (pure data types, no dependencies except stdlib)

Contains:
- Enums for state tracking
- DTOs for data transfer
- Protocols for interfaces

## Dependencies


**Imports (external):** [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#enum|enum]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/MyProjects/_template/domain/__init__.py|__init__.py]]

## Classes

### class `PositionState`(Enum)

[line 20](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L20)

Position lifecycle states.


### class `SignalDirection`(Enum)

[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L27)

Signal directions.


### class `Signal`

[line 37](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L37)

Trading signal DTO.

- `def __post_init__(self)` — [L44](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L44)

### class `PositionInfo`

[line 50](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L50)

Position information DTO.


### class `TradeRecord`

[line 61](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L61)

Trade record DTO.


### class `Logger`(Protocol)

[line 74](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L74)

Logging interface.

- `def Debug(self, message: str) -> None` — [L76](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L76)
- `def Log(self, message: str) -> None` — [L77](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L77)
- `def Error(self, message: str) -> None` — [L78](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L78)

### class `PortfolioProvider`(Protocol)

[line 82](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L82)

Portfolio data interface.

- `def get_nav(self) -> float` — [L84](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L84)
- `def get_cash(self) -> float` — [L85](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L85)
- `def get_positions(self) -> dict` — [L86](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/models.py#L86)

## Source

> [!example]- MyProjects/_template/domain/models.py (87 lines)
> ```python
> """
> Data models for {{STRATEGY_NAME}}.
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
>     """Trading signal DTO."""
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
