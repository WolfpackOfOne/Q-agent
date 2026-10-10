---
path: "MyProjects/_template/domain/config.py"
hub: "_template"
layer: "Molecule / Atom"
lines: 33
tags:
  - "code/python"
  - "projects/_template"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py"
---
# config.py

`MyProjects/_template/domain/config.py` · hub [[Hubs/Projects/_template|_template]] · layer **Molecule / Atom** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py)

## Purpose

Configuration constants for {{STRATEGY_NAME}}.

Layer: ATOMS (pure constants, no dependencies)

Usage:
    from domain.config import *

## Dependencies


**Imported by:** [[Code/MyProjects/_template/domain/__init__.py|__init__.py]], [[Code/MyProjects/_template/models/logger.py|logger.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `OBJECTSTORE_NAMESPACE` | `'{{objectstore_namespace}}'` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py#L11) |
| `DEFAULT_START_DATE` | `(2022, 1, 1)` | [14](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py#L14) |
| `DEFAULT_END_DATE` | `(2024, 1, 1)` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py#L15) |
| `DEFAULT_CASH` | `100000` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py#L16) |
| `DEFAULT_BENCHMARK` | `'SPY'` | [17](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/_template/domain/config.py#L17) |

## Source

> [!example]- MyProjects/_template/domain/config.py (33 lines)
> ```python
> """
> Configuration constants for {{STRATEGY_NAME}}.
>
> Layer: ATOMS (pure constants, no dependencies)
>
> Usage:
>     from domain.config import *
> """
>
> # === ObjectStore ===
> OBJECTSTORE_NAMESPACE = "{{objectstore_namespace}}"
>
> # === Backtest Defaults ===
> DEFAULT_START_DATE = (2022, 1, 1)
> DEFAULT_END_DATE = (2024, 1, 1)
> DEFAULT_CASH = 100_000
> DEFAULT_BENCHMARK = "SPY"
>
> # === Strategy Parameters ===
> # TODO: Add strategy-specific parameters
>
> # Example: Signal parameters
> # SIGNAL_LOOKBACK = 20
> # SIGNAL_THRESHOLD = 0.05
>
> # Example: Portfolio parameters
> # MAX_POSITION_SIZE = 0.10  # 10% max per position
> # TARGET_VOLATILITY = 0.10  # 10% annual volatility target
> # MAX_GROSS_EXPOSURE = 1.0  # 100% max gross exposure
>
> # Example: Execution parameters
> # LIMIT_ORDER_OFFSET = 0.005  # 0.5% limit order offset
> ```
