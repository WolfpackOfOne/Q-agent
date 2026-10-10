---
path: "tests/agent_graph_system/test_returns_loader.py"
hub: "Tests"
lines: 127
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py"
---
# test_returns_loader.py

`tests/agent_graph_system/test_returns_loader.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py)

## Purpose

Unit tests for the returns loader / discovery boundary module.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/analysis/returns.py|returns.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#json|json]], [[Indexes/External packages#numpy|numpy]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pytest|pytest]]

## Functions

### `_write_csv()`

```python
def _write_csv(path, *, level_col=False)
```
[line 14](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L14)

### `_write_lean_result()`

```python
def _write_lean_result(path, values)
```
[line 23](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L23)

### `test_load_returns_from_return_column()`

```python
def test_load_returns_from_return_column(tmp_path)
```
[line 34](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L34)

### `test_load_returns_derives_from_level_column()`

```python
def test_load_returns_derives_from_level_column(tmp_path)
```
[line 43](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L43)

### `test_load_returns_rejects_columnless_csv()`

```python
def test_load_returns_rejects_columnless_csv(tmp_path)
```
[line 52](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L52)

### `test_load_returns_preserves_zero_lean_equity_point()`

```python
def test_load_returns_preserves_zero_lean_equity_point(tmp_path, zero)
```
[line 60](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L60)

### `test_load_returns_reports_missing_lean_equity_value()`

```python
def test_load_returns_reports_missing_lean_equity_value(tmp_path)
```
[line 74](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L74)

### `test_discover_returns_finds_project_csv()`

```python
def test_discover_returns_finds_project_csv(tmp_path)
```
[line 82](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L82)

### `test_discover_returns_none_when_absent()`

```python
def test_discover_returns_none_when_absent(tmp_path)
```
[line 90](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L90)

### `test_discover_returns_swallows_bad_file()`

```python
def test_discover_returns_swallows_bad_file(tmp_path)
```
[line 94](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L94)

### `test_discover_returns_swallows_malformed_lean_result()`

```python
def test_discover_returns_swallows_malformed_lean_result(tmp_path, payload)
```
[line 116](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L116)

### `test_default_search_roots_honours_env()`

```python
def test_default_search_roots_honours_env(tmp_path, monkeypatch)
```
[line 124](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_returns_loader.py#L124)

## Source

> [!example]- tests/agent_graph_system/test_returns_loader.py (127 lines)
> ```python
> """Unit tests for the returns loader / discovery boundary module."""
>
> from __future__ import annotations
>
> import json
>
> import numpy as np
> import pandas as pd
> import pytest
>
> from agent_graph_system.analysis import returns as rl
>
>
> def _write_csv(path, *, level_col=False):
>     idx = pd.bdate_range("2020-01-01", periods=10)
>     if level_col:
>         df = pd.DataFrame({"date": idx, "close": np.linspace(100, 110, 10)})
>     else:
>         df = pd.DataFrame({"date": idx, "return": np.full(10, 0.001)})
>     path.write_text(df.to_csv(index=False))
>
>
> def _write_lean_result(path, values):
>     path.parent.mkdir(parents=True, exist_ok=True)
>     path.write_text(json.dumps({
>         "Charts": {
>             "Strategy Equity": {
>                 "Series": {"Equity": {"Values": values}},
>             },
>         },
>     }))
>
>
> def test_load_returns_from_return_column(tmp_path):
>     p = tmp_path / "r.csv"
>     _write_csv(p)
>     s = rl.load_returns(p)
>     assert isinstance(s, pd.Series)
>     assert len(s) == 10
>     assert np.allclose(s.values, 0.001)
>
>
> def test_load_returns_derives_from_level_column(tmp_path):
>     p = tmp_path / "r.csv"
>     _write_csv(p, level_col=True)
>     s = rl.load_returns(p)
>     # pct_change drops the first row.
>     assert len(s) == 9
>     assert (s > 0).all()
>
>
> def test_load_returns_rejects_columnless_csv(tmp_path):
>     p = tmp_path / "bad.csv"
>     p.write_text("a,b\n1,2\n")
>     with pytest.raises(ValueError):
>         rl.load_returns(p)
>
>
> @pytest.mark.parametrize("zero", [0, 0.0, "0"])
> def test_load_returns_preserves_zero_lean_equity_point(tmp_path, zero):
>     p = tmp_path / "result.json"
>     _write_lean_result(p, [
>         {"x": 0, "y": 100},
>         {"x": 86_400, "y": zero},
>         {"x": 172_800, "y": 10},
>     ])
>
>     returns = rl.load_returns(p)
>
>     assert returns.iloc[0] == -1.0
>     assert len(returns) == 2
>
>
> def test_load_returns_reports_missing_lean_equity_value(tmp_path):
>     p = tmp_path / "result.json"
>     _write_lean_result(p, [{"x": 1_577_836_800}])
>
>     with pytest.raises(ValueError, match="has no equity value"):
>         rl.load_returns(p)
>
>
> def test_discover_returns_finds_project_csv(tmp_path):
>     proj = tmp_path / "MyStrat" / "data"
>     proj.mkdir(parents=True)
>     _write_csv(proj / "returns.csv")
>     s = rl.discover_returns("MyStrat", roots=[tmp_path])
>     assert s is not None and len(s) == 10
>
>
> def test_discover_returns_none_when_absent(tmp_path):
>     assert rl.discover_returns("Ghost", roots=[tmp_path]) is None
>
>
> def test_discover_returns_swallows_bad_file(tmp_path):
>     proj = tmp_path / "Broken"
>     proj.mkdir()
>     (proj / "returns.csv").write_text("a,b\n1,2\n")
>     # A malformed artifact is treated as "unavailable", not an exception.
>     assert rl.discover_returns("Broken", roots=[tmp_path]) is None
>
>
> @pytest.mark.parametrize("payload", [
>     "{not valid json",
>     json.dumps({
>         "Charts": {
>             "Strategy Equity": {
>                 "Series": {
>                     "Equity": {
>                         "Values": [{"x": 1_577_836_800, "y": {"bad": "value"}}],
>                     },
>                 },
>             },
>         },
>     }),
> ])
> def test_discover_returns_swallows_malformed_lean_result(tmp_path, payload):
>     result = tmp_path / "BrokenLean" / "backtests" / "run" / "result.json"
>     result.parent.mkdir(parents=True)
>     result.write_text(payload)
>
>     assert rl.discover_returns("BrokenLean", roots=[tmp_path]) is None
>
>
> def test_default_search_roots_honours_env(tmp_path, monkeypatch):
>     monkeypatch.setenv("WALKFORWARD_RETURNS_ROOT", str(tmp_path))
>     assert rl.default_search_roots() == [tmp_path]
> ```
