---
path: "MyProjects/PassiveMarketInstability/tests/test_flows.py"
hub: "PassiveMarketInstability"
lines: 41
tags:
  - "code/python"
  - "projects/PassiveMarketInstability"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py"
---
# test_flows.py

`MyProjects/PassiveMarketInstability/tests/test_flows.py` · hub [[Hubs/Projects/PassiveMarketInstability|PassiveMarketInstability]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#numpy|numpy]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#passive_market_instability|passive_market_instability]], [[Indexes/External packages#pytest|pytest]]

## Functions

### `_sample_flow_panel()`

```python
def _sample_flow_panel()
```
[line 12](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py#L12)

### `test_add_returns_creates_return_column()`

```python
def test_add_returns_creates_return_column()
```
[line 24](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py#L24)

### `test_flow_pressure_proxy_is_volume_times_return()`

```python
def test_flow_pressure_proxy_is_volume_times_return()
```
[line 30](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py#L30)

### `test_negative_volume_fails_validation()`

```python
def test_negative_volume_fails_validation()
```
[line 36](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_flows.py#L36)

## Source

> [!example]- MyProjects/PassiveMarketInstability/tests/test_flows.py (41 lines)
> ```python
> import numpy as np
> import pandas as pd
> import pytest
>
> from passive_market_instability.flows import (
>     add_returns,
>     estimate_flow_pressure_proxy,
>     validate_etf_flow_proxy,
> )
>
>
> def _sample_flow_panel():
>     return pd.DataFrame(
>         {
>             "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
>             "ticker": ["SPY", "SPY", "IVV", "IVV"],
>             "adj_close": [100.0, 101.0, 50.0, 49.0],
>             "close": [100.0, 101.0, 50.0, 49.0],
>             "volume": [10.0, 20.0, 30.0, 40.0],
>         }
>     )
>
>
> def test_add_returns_creates_return_column():
>     df = add_returns(_sample_flow_panel())
>     assert "return" in df.columns
>     assert np.isclose(df.loc[df["ticker"].eq("SPY"), "return"].iloc[-1], 0.01)
>
>
> def test_flow_pressure_proxy_is_volume_times_return():
>     df = estimate_flow_pressure_proxy(add_returns(_sample_flow_panel()))
>     spy_second = df[df["ticker"].eq("SPY")].iloc[-1]
>     assert np.isclose(spy_second["flow_pressure_proxy"], spy_second["volume"] * spy_second["return"])
>
>
> def test_negative_volume_fails_validation():
>     df = _sample_flow_panel()
>     df.loc[0, "volume"] = -1.0
>     with pytest.raises(ValueError, match="volume"):
>         validate_etf_flow_proxy(df)
> ```
