---
path: "MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py"
hub: "PassiveMarketInstability"
lines: 25
tags:
  - "code/python"
  - "projects/PassiveMarketInstability"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py"
---
# validation.py

`MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py` · hub [[Hubs/Projects/PassiveMarketInstability|PassiveMarketInstability]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py)

## Purpose

Small validation helpers used by the notebook.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pandas|pandas]]

## Functions

### `check_status()`

```python
def check_status(condition)
```
[line 8](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py#L8)

Return the notebook's pass/fail status string.

### `make_check()`

```python
def make_check(check_name, condition, details)
```
[line 13](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py#L13)

Build one row for the notebook sanity-check summary table.

### `checks_to_frame()`

```python
def checks_to_frame(checks)
```
[line 22](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py#L22)

Convert a list of sanity-check dictionaries to a DataFrame.

## Source

> [!example]- MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py (25 lines)
> ```python
> """Small validation helpers used by the notebook."""
>
> from __future__ import annotations
>
> import pandas as pd
>
>
> def check_status(condition):
>     """Return the notebook's pass/fail status string."""
>     return "pass" if bool(condition) else "fail"
>
>
> def make_check(check_name, condition, details):
>     """Build one row for the notebook sanity-check summary table."""
>     return {
>         "check_name": check_name,
>         "status": check_status(condition),
>         "details": details,
>     }
>
>
> def checks_to_frame(checks):
>     """Convert a list of sanity-check dictionaries to a DataFrame."""
>     return pd.DataFrame(checks, columns=["check_name", "status", "details"])
> ```
