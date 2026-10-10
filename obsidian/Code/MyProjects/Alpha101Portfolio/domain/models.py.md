---
path: "MyProjects/Alpha101Portfolio/domain/models.py"
hub: "Alpha101Portfolio"
layer: "Molecule / Atom"
lines: 45
tags:
  - "code/python"
  - "projects/Alpha101Portfolio"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py"
---
# models.py

`MyProjects/Alpha101Portfolio/domain/models.py` · hub [[Hubs/Projects/Alpha101Portfolio|Alpha101Portfolio]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py)

## Purpose

DTOs and enums for Alpha101Portfolio.

Layer: ATOMS (pure data structures — Python stdlib only, no LEAN imports).

## Dependencies


**Imports (external):** [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#enum|enum]]

## Classes

### class `Side`(Enum)

[line 11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py#L11)

Which side of the dollar-neutral book a position sits on.

- `def from_weight(cls, weight: float) -> 'Side'` — [L19](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py#L19)

### class `AlphaScore`

[line 28](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py#L28)

One stock's model score on one weekly scoring date.


### class `TargetPosition`

[line 36](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py#L36)

A target weight for one ticker on one rebalance.

- `def side(self) -> Side` — [L43](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/Alpha101Portfolio/domain/models.py#L43)

## Source

> [!example]- MyProjects/Alpha101Portfolio/domain/models.py (45 lines)
> ```python
> """
> DTOs and enums for Alpha101Portfolio.
>
> Layer: ATOMS (pure data structures — Python stdlib only, no LEAN imports).
> """
>
> from dataclasses import dataclass
> from enum import Enum
>
>
> class Side(Enum):
>     """Which side of the dollar-neutral book a position sits on."""
>
>     LONG = "long"
>     SHORT = "short"
>     FLAT = "flat"
>
>     @classmethod
>     def from_weight(cls, weight: float) -> "Side":
>         if weight > 0:
>             return cls.LONG
>         if weight < 0:
>             return cls.SHORT
>         return cls.FLAT
>
>
> @dataclass(frozen=True)
> class AlphaScore:
>     """One stock's model score on one weekly scoring date."""
>
>     ticker: str
>     score: float
>
>
> @dataclass(frozen=True)
> class TargetPosition:
>     """A target weight for one ticker on one rebalance."""
>
>     ticker: str
>     weight: float
>
>     @property
>     def side(self) -> Side:
>         return Side.from_weight(self.weight)
> ```
