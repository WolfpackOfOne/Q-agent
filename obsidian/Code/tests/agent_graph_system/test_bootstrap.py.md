---
path: "tests/agent_graph_system/test_bootstrap.py"
hub: "Tests"
lines: 59
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py"
---
# test_bootstrap.py

`tests/agent_graph_system/test_bootstrap.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py)

## Purpose

Unit tests for the bootstrap Sharpe significance test.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/analysis/bootstrap.py|bootstrap.py]], [[Code/agent_graph_system/analysis/walkforward.py|walkforward.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#numpy|numpy]]

## Functions

### `test_zero_mean_series_is_not_significant()`

```python
def test_zero_mean_series_is_not_significant()
```
[line 11](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L11)

### `test_zero_mean_pvalue_centers_near_half_on_average()`

```python
def test_zero_mean_pvalue_centers_near_half_on_average()
```
[line 20](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L20)

### `test_strong_positive_series_is_significant()`

```python
def test_strong_positive_series_is_significant()
```
[line 30](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L30)

### `test_block_bootstrap_runs_and_is_bounded()`

```python
def test_block_bootstrap_runs_and_is_bounded()
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L39)

### `test_deterministic_with_fixed_seed()`

```python
def test_deterministic_with_fixed_seed()
```
[line 48](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L48)

### `test_degenerate_input_returns_one()`

```python
def test_degenerate_input_returns_one()
```
[line 57](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/test_bootstrap.py#L57)

## Source

> [!example]- tests/agent_graph_system/test_bootstrap.py (59 lines)
> ```python
> """Unit tests for the bootstrap Sharpe significance test."""
>
> from __future__ import annotations
>
> import numpy as np
>
> from agent_graph_system.analysis.bootstrap import bootstrap_sharpe_pvalue
> from agent_graph_system.analysis.walkforward import sharpe_ratio
>
>
> def test_zero_mean_series_is_not_significant():
>     # A single zero-mean iid draw must never look significant (one-sided p well
>     # above the 0.05 bar), whichever way its sample mean happened to land.
>     rng = np.random.default_rng(1)
>     r = rng.normal(0.0, 0.01, 1000)
>     p = bootstrap_sharpe_pvalue(r, sharpe_ratio(r), n_permutations=3000, seed=7)
>     assert p > 0.05
>
>
> def test_zero_mean_pvalue_centers_near_half_on_average():
>     # Averaged over many zero-mean draws, the one-sided p-value is ~uniform and
>     # so averages near 0.5 — the calibration property of the test.
>     ps = []
>     for seed in range(24):
>         r = np.random.default_rng(seed).normal(0.0, 0.01, 600)
>         ps.append(bootstrap_sharpe_pvalue(r, sharpe_ratio(r), n_permutations=1500, seed=7))
>     assert 0.4 < float(np.mean(ps)) < 0.6
>
>
> def test_strong_positive_series_is_significant():
>     # A consistently positive series with a strong drift should be clearly
>     # distinguishable from the zero-mean null.
>     rng = np.random.default_rng(2)
>     r = rng.normal(0.0015, 0.008, 1000)
>     p = bootstrap_sharpe_pvalue(r, sharpe_ratio(r), n_permutations=3000, seed=7)
>     assert p < 0.05
>
>
> def test_block_bootstrap_runs_and_is_bounded():
>     rng = np.random.default_rng(3)
>     r = rng.normal(0.0010, 0.01, 800)
>     p = bootstrap_sharpe_pvalue(
>         r, sharpe_ratio(r), n_permutations=2000, seed=7, block_size=10
>     )
>     assert 0.0 <= p <= 1.0
>
>
> def test_deterministic_with_fixed_seed():
>     rng = np.random.default_rng(4)
>     r = rng.normal(0.0008, 0.01, 600)
>     obs = sharpe_ratio(r)
>     p1 = bootstrap_sharpe_pvalue(r, obs, n_permutations=1500, seed=123)
>     p2 = bootstrap_sharpe_pvalue(r, obs, n_permutations=1500, seed=123)
>     assert p1 == p2
>
>
> def test_degenerate_input_returns_one():
>     assert bootstrap_sharpe_pvalue(np.array([0.01]), 0.5) == 1.0
> ```
