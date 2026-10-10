---
path: "MyProjects/ElectionIndustryBeta/domain/models.py"
hub: "ElectionIndustryBeta"
layer: "Molecule / Atom"
lines: 63
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py"
---
# models.py

`MyProjects/ElectionIndustryBeta/domain/models.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py)

## Purpose

Data models for ElectionIndustryBeta.

Layer: ATOMS (pure data types, no dependencies except stdlib).

## Dependencies


**Imports (external):** [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#enum|enum]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/domain/__init__.py|__init__.py]]

## Classes

### class `PositionState`(Enum)

[line 13](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L13)


### class `SignalDirection`(Enum)

[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L19)


### class `Signal`

[line 26](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L26)

Trading signal DTO.

- `def __post_init__(self)` — [L33](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L33)

### class `PositionInfo`

[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L39)


### class `TradeRecord`

[line 49](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L49)


### class `Logger`(Protocol)

[line 59](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L59)

- `def Debug(self, message: str) -> None` — [L60](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L60)
- `def Log(self, message: str) -> None` — [L61](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L61)
- `def Error(self, message: str) -> None` — [L62](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/domain/models.py#L62)

## Source

> [!example]- MyProjects/ElectionIndustryBeta/domain/models.py (63 lines)
> ```python
> """
> Data models for ElectionIndustryBeta.
>
> Layer: ATOMS (pure data types, no dependencies except stdlib).
> """
>
> from dataclasses import dataclass
> from datetime import datetime
> from enum import Enum
> from typing import Optional, Protocol, runtime_checkable
>
>
> class PositionState(Enum):
>     FLAT = "FLAT"
>     LONG = "LONG"
>     SHORT = "SHORT"
>
>
> class SignalDirection(Enum):
>     LONG = 1
>     FLAT = 0
>     SHORT = -1
>
>
> @dataclass
> class Signal:
>     """Trading signal DTO."""
>     symbol: str
>     direction: SignalDirection
>     strength: float
>     timestamp: datetime
>
>     def __post_init__(self):
>         if not 0.0 <= self.strength <= 1.0:
>             raise ValueError(f"Signal strength must be 0-1, got {self.strength}")
>
>
> @dataclass
> class PositionInfo:
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
>     date: datetime
>     symbol: str
>     action: str  # "BUY", "SELL", "CLOSE"
>     quantity: float
>     price: float
>     pnl: Optional[float] = None
>
>
> @runtime_checkable
> class Logger(Protocol):
>     def Debug(self, message: str) -> None: ...
>     def Log(self, message: str) -> None: ...
>     def Error(self, message: str) -> None: ...
> ```
