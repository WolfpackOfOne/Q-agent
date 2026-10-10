---
path: "tests/agent_graph_system/test_batch.py"
hub: "Tests"
lines: 122
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py"
---
# test_batch.py

`tests/agent_graph_system/test_batch.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py)

## Purpose

Tests for agent_graph_system.utils.batch.batch_run.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/utils/batch.py|batch.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#asyncio|asyncio]], [[Indexes/External packages#pytest|pytest]]

## Functions

### `test_all_succeed()`

```python
def test_all_succeed()
```
[line 12](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L12)

### `test_mixed_success_and_failure_with_skip()`

```python
def test_mixed_success_and_failure_with_skip()
```
[line 25](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L25)

### `test_none_result_counts_as_success()`

```python
def test_none_result_counts_as_success()
```
[line 44](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L44)

### `test_on_error_raise_propagates_first_failure()`

```python
def test_on_error_raise_propagates_first_failure()
```
[line 57](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L57)

### `test_concurrency_bound_respected()`

```python
def test_concurrency_bound_respected()
```
[line 67](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L67)

### `test_on_progress_called_for_every_input()`

```python
def test_on_progress_called_for_every_input()
```
[line 86](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L86)

### `test_concurrency_must_be_positive()`

```python
def test_concurrency_must_be_positive()
```
[line 102](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L102)

### `test_empty_inputs_returns_empty_result_immediately()`

```python
def test_empty_inputs_returns_empty_result_immediately()
```
[line 110](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_batch.py#L110)

## Source

> [!example]- tests/agent_graph_system/test_batch.py (122 lines)
> ```python
> """Tests for agent_graph_system.utils.batch.batch_run."""
>
> from __future__ import annotations
>
> import asyncio
>
> import pytest
>
> from agent_graph_system.utils.batch import batch_run
>
>
> def test_all_succeed():
>     async def ok(x: int) -> int:
>         return x * 2
>
>     result = asyncio.run(batch_run(ok, [1, 2, 3]))
>
>     assert result.results == [2, 4, 6]
>     assert result.total == 3
>     assert result.success_count == 3
>     assert result.failure_count == 0
>     assert result.errors == []
>
>
> def test_mixed_success_and_failure_with_skip():
>     async def maybe_fail(x: int) -> int:
>         if x == 2:
>             raise ValueError("bad input")
>         return x * 10
>
>     result = asyncio.run(batch_run(maybe_fail, [1, 2, 3]))
>
>     assert result.results == [10, None, 30]
>     assert result.success_count == 2
>     assert result.failure_count == 1
>     assert len(result.errors) == 1
>     index, exc = result.errors[0]
>     assert index == 1
>     assert isinstance(exc, ValueError)
>     assert result.successes == [(0, 10), (2, 30)]
>     assert result.failures == result.errors
>
>
> def test_none_result_counts_as_success():
>     async def returns_none(_x: int) -> None:
>         return None
>
>     result = asyncio.run(batch_run(returns_none, [1, 2, 3]))
>
>     assert result.results == [None, None, None]
>     assert result.succeeded == [True, True, True]
>     assert result.success_count == 3
>     assert result.failure_count == 0
>     assert result.successes == [(0, None), (1, None), (2, None)]
>
>
> def test_on_error_raise_propagates_first_failure():
>     async def maybe_fail(x: int) -> int:
>         if x == 2:
>             raise ValueError("boom")
>         return x
>
>     with pytest.raises(ValueError, match="boom"):
>         asyncio.run(batch_run(maybe_fail, [1, 2, 3], on_error="raise"))
>
>
> def test_concurrency_bound_respected():
>     current = 0
>     max_seen = 0
>
>     async def track(_x: int) -> int:
>         nonlocal current, max_seen
>         current += 1
>         max_seen = max(max_seen, current)
>         await asyncio.sleep(0.01)
>         current -= 1
>         return _x
>
>     concurrency = 2
>     result = asyncio.run(batch_run(track, list(range(6)), concurrency=concurrency))
>
>     assert max_seen <= concurrency
>     assert result.success_count == 6
>
>
> def test_on_progress_called_for_every_input():
>     progress_calls: list[tuple[int, int]] = []
>
>     async def ok(x: int) -> int:
>         return x
>
>     def on_progress(done: int, total: int) -> None:
>         progress_calls.append((done, total))
>
>     asyncio.run(batch_run(ok, [1, 2, 3], on_progress=on_progress))
>
>     assert len(progress_calls) == 3
>     assert all(total == 3 for _done, total in progress_calls)
>     assert sorted(done for done, _total in progress_calls) == [1, 2, 3]
>
>
> def test_concurrency_must_be_positive():
>     async def ok(x: int) -> int:
>         return x
>
>     with pytest.raises(ValueError):
>         asyncio.run(batch_run(ok, [1, 2, 3], concurrency=0))
>
>
> def test_empty_inputs_returns_empty_result_immediately():
>     async def ok(x: int) -> int:
>         return x
>
>     result = asyncio.run(batch_run(ok, []))
>
>     assert result.total == 0
>     assert result.success_count == 0
>     assert result.failure_count == 0
>     assert result.results == []
>     assert result.errors == []
>     assert result.duration_seconds == 0.0
> ```
