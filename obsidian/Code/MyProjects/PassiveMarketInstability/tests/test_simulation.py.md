---
path: "MyProjects/PassiveMarketInstability/tests/test_simulation.py"
hub: "PassiveMarketInstability"
lines: 37
tags:
  - "code/python"
  - "projects/PassiveMarketInstability"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py"
---
# test_simulation.py

`MyProjects/PassiveMarketInstability/tests/test_simulation.py` · hub [[Hubs/Projects/PassiveMarketInstability|PassiveMarketInstability]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py)

## Dependencies


**Imports (external):** [[Indexes/External packages#numpy|numpy]], [[Indexes/External packages#passive_market_instability|passive_market_instability]]

## Functions

### `test_simulate_market_paths_returns_expected_shape()`

```python
def test_simulate_market_paths_returns_expected_shape()
```
[line 11](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py#L11)

### `test_simulate_market_paths_has_no_negative_values_after_guards()`

```python
def test_simulate_market_paths_has_no_negative_values_after_guards()
```
[line 18](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py#L18)

### `test_hitting_times_are_nan_or_within_horizon()`

```python
def test_hitting_times_are_nan_or_within_horizon()
```
[line 25](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py#L25)

### `test_lyapunov_threshold_is_near_paper_value()`

```python
def test_lyapunov_threshold_is_near_paper_value()
```
[line 31](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py#L31)

### `test_feller_threshold_is_near_paper_value()`

```python
def test_feller_threshold_is_near_paper_value()
```
[line 35](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/tests/test_simulation.py#L35)

## Source

> [!example]- MyProjects/PassiveMarketInstability/tests/test_simulation.py (37 lines)
> ```python
> import numpy as np
>
> from passive_market_instability.config import PAPER_KAPPA, PAPER_SIGMA
> from passive_market_instability.simulation import (
>     feller_threshold,
>     lyapunov_threshold,
>     simulate_market_paths,
> )
>
>
> def test_simulate_market_paths_returns_expected_shape():
>     result = simulate_market_paths(n_paths=4, years=1, steps_per_year=12, random_seed=7)
>     paths = result["paths"]
>     assert paths.shape == (13, 6)
>     assert {"t", "year", "path_000", "path_003"}.issubset(paths.columns)
>
>
> def test_simulate_market_paths_has_no_negative_values_after_guards():
>     result = simulate_market_paths(n_paths=8, years=2, steps_per_year=12, random_seed=7)
>     paths = result["paths"]
>     path_cols = [col for col in paths.columns if col.startswith("path_")]
>     assert (paths[path_cols] >= 0.0).all().all()
>
>
> def test_hitting_times_are_nan_or_within_horizon():
>     result = simulate_market_paths(n_paths=8, years=2, steps_per_year=12, random_seed=7)
>     hits = result["hitting_times"]["hitting_time"]
>     assert hits.isna().all() or ((hits.dropna() >= 0.0) & (hits.dropna() <= 2.0)).all()
>
>
> def test_lyapunov_threshold_is_near_paper_value():
>     assert np.isclose(lyapunov_threshold(PAPER_KAPPA, PAPER_SIGMA), 0.87, atol=0.01)
>
>
> def test_feller_threshold_is_near_paper_value():
>     assert np.isclose(feller_threshold(PAPER_KAPPA, PAPER_SIGMA), 0.91, atol=0.01)
> ```
