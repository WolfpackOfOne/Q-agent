---
path: "tests/agent_graph_system/test_latest_backtest.py"
hub: "Tests"
lines: 60
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py"
---
# test_latest_backtest.py

`tests/agent_graph_system/test_latest_backtest.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py)

## Purpose

Standalone tests for latest-backtest selection (#53 sub-issue 3).

The deployment-gate tests exercise the gate with an injected backtest; these
pin down the selection logic itself: recency, validity, linkage, dedup.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/local/engine.py|engine.py]], [[Code/agent_graph_system/graph/neo4j/graph_models.py|graph_models.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]]

## Functions

### `_bt()`

```python
def _bt(run_id, sharpe=1.0, status='completed', **kw)
```
[line 13](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L13)

### `test_picks_most_recent_by_completed_at()`

```python
def test_picks_most_recent_by_completed_at()
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L19)

### `test_excludes_failed_and_running()`

```python
def test_excludes_failed_and_running()
```
[line 30](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L30)

### `test_links_via_strategy_property_without_edge()`

```python
def test_links_via_strategy_property_without_edge()
```
[line 43](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L43)

### `test_returns_none_when_no_valid_backtest()`

```python
def test_returns_none_when_no_valid_backtest()
```
[line 51](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L51)

### `test_returns_none_for_unknown_strategy()`

```python
def test_returns_none_for_unknown_strategy()
```
[line 58](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_latest_backtest.py#L58)

## Source

> [!example]- tests/agent_graph_system/test_latest_backtest.py (60 lines)
> ```python
> """Standalone tests for latest-backtest selection (#53 sub-issue 3).
>
> The deployment-gate tests exercise the gate with an injected backtest; these
> pin down the selection logic itself: recency, validity, linkage, dedup.
> """
>
> from __future__ import annotations
>
> from agent_graph_system.graph.local import engine
> from agent_graph_system.graph.neo4j import graph_models as gm
>
>
> def _bt(run_id, sharpe=1.0, status="completed", **kw):
>     gm.upsert_backtest(run_id, name=run_id, sharpe=sharpe, drawdown=-0.1, cagr=0.1)
>     if status != "completed" or kw:
>         engine.merge_node("Backtest", "run_id", run_id, {"status": status, **kw})
>
>
> def test_picks_most_recent_by_completed_at():
>     gm.upsert_strategy("S", strategy_type="factor")
>     _bt("old", completed_at="2026-01-01")
>     _bt("new", completed_at="2026-05-01")
>     gm.strategy_has_backtest("S", "old")
>     gm.strategy_has_backtest("S", "new")
>
>     latest = engine.latest_backtest_for_strategy("S")
>     assert latest is not None and latest["run_id"] == "new"
>
>
> def test_excludes_failed_and_running():
>     gm.upsert_strategy("S", strategy_type="factor")
>     _bt("good", completed_at="2026-01-01")
>     _bt("failed_recent", status="failed", completed_at="2026-09-01")
>     _bt("running_recent", status="running", completed_at="2026-09-02")
>     gm.strategy_has_backtest("S", "good")
>     gm.strategy_has_backtest("S", "failed_recent")
>     gm.strategy_has_backtest("S", "running_recent")
>
>     latest = engine.latest_backtest_for_strategy("S")
>     assert latest is not None and latest["run_id"] == "good"
>
>
> def test_links_via_strategy_property_without_edge():
>     # A backtest carrying a `strategy` property is found even with no edge.
>     _bt("orphan", completed_at="2026-03-01")
>     engine.merge_node("Backtest", "run_id", "orphan", {"strategy": "S"})
>     latest = engine.latest_backtest_for_strategy("S")
>     assert latest is not None and latest["run_id"] == "orphan"
>
>
> def test_returns_none_when_no_valid_backtest():
>     gm.upsert_strategy("S", strategy_type="factor")
>     _bt("nope", status="failed", completed_at="2026-01-01")
>     gm.strategy_has_backtest("S", "nope")
>     assert engine.latest_backtest_for_strategy("S") is None
>
>
> def test_returns_none_for_unknown_strategy():
>     assert engine.latest_backtest_for_strategy("Ghost") is None
> ```
