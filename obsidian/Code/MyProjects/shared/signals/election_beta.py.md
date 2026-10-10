---
path: "MyProjects/shared/signals/election_beta.py"
hub: "shared signals"
layer: "Atom (shared signal)"
lines: 91
tags:
  - "code/python"
  - "projects/shared-signals"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared/signals/election_beta.py"
---
# election_beta.py

`MyProjects/shared/signals/election_beta.py` · hub [[Hubs/Projects/shared signals|shared signals]] · layer **Atom (shared signal)** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared/signals/election_beta.py)

## Purpose

Election-driven industry-beta signal.

Pure pandas/numpy. No LEAN imports — must remain importable from a plain
Python environment so it can be symlinked into any QuantConnect project and
unit-tested locally.

Replicates the rolling-beta helper from
infrastructure/marimo/notebooks/election_industry_returns.py.

Functions:
    rolling_beta(returns, delta_prob, lookback)
        For each column of `returns`, compute the OLS slope of that column
        regressed on `delta_prob` over the trailing `lookback` rows.
        Returns the latest beta per column.

    top_bottom_k_betaweighted(betas, k)
        Build a long/short weight dict from the K largest and K smallest
        betas, with weights proportional to beta and normalised so that
        the sum of absolute weights equals 1 (gross exposure 100%).

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#numpy|numpy]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/MyProjects/ElectionIndustryBeta/domain/signals/election_beta.py|election_beta.py]], [[Code/MyProjects/ElectionIndustryBeta/models/alpha.py|alpha.py]], [[Code/MyProjects/ElectionIndustryBeta/models/portfolio.py|portfolio.py]]

## Functions

### `rolling_beta()`

```python
def rolling_beta(returns: pd.DataFrame, delta_prob: pd.Series, lookback: int) -> pd.Series
```
[line 29](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared/signals/election_beta.py#L29)

Latest-window OLS beta of each return column on delta_prob.

Args:
    returns:    DataFrame indexed by date, one column per ticker.
    delta_prob: Series indexed by date, daily change in the driver
                (e.g. Polymarket Trump win probability).
    lookback:   Number of trailing rows to use in the regression.

Returns:
    Series indexed by ticker with the most-recent rolling beta.
    Tickers with insufficient non-NaN observations get NaN.

### `top_bottom_k_betaweighted()`

```python
def top_bottom_k_betaweighted(betas: pd.Series, k: int) -> dict[str, float]
```
[line 63](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/shared/signals/election_beta.py#L63)

Long top-K (largest beta), short bottom-K (smallest beta), weighted by beta.

Weights are proportional to each selected beta and then normalised so the
sum of absolute weights equals 1.0 (gross exposure 100%). Non-selected
tickers receive weight 0.0.

Args:
    betas: Series of beta values, one per ticker. NaNs are dropped.
    k:     Number of tickers to long and short.

Returns:
    Dict mapping every ticker in `betas.index` to a weight in [-1, 1].
    Empty/insufficient input returns all zeros.

## Source

> [!example]- MyProjects/shared/signals/election_beta.py (91 lines)
> ```python
> """
> Election-driven industry-beta signal.
>
> Pure pandas/numpy. No LEAN imports — must remain importable from a plain
> Python environment so it can be symlinked into any QuantConnect project and
> unit-tested locally.
>
> Replicates the rolling-beta helper from
> infrastructure/marimo/notebooks/election_industry_returns.py.
>
> Functions:
>     rolling_beta(returns, delta_prob, lookback)
>         For each column of `returns`, compute the OLS slope of that column
>         regressed on `delta_prob` over the trailing `lookback` rows.
>         Returns the latest beta per column.
>
>     top_bottom_k_betaweighted(betas, k)
>         Build a long/short weight dict from the K largest and K smallest
>         betas, with weights proportional to beta and normalised so that
>         the sum of absolute weights equals 1 (gross exposure 100%).
> """
>
> from __future__ import annotations
>
> import numpy as np
> import pandas as pd
>
>
> def rolling_beta(
>     returns: pd.DataFrame,
>     delta_prob: pd.Series,
>     lookback: int,
> ) -> pd.Series:
>     """Latest-window OLS beta of each return column on delta_prob.
>
>     Args:
>         returns:    DataFrame indexed by date, one column per ticker.
>         delta_prob: Series indexed by date, daily change in the driver
>                     (e.g. Polymarket Trump win probability).
>         lookback:   Number of trailing rows to use in the regression.
>
>     Returns:
>         Series indexed by ticker with the most-recent rolling beta.
>         Tickers with insufficient non-NaN observations get NaN.
>     """
>     aligned = returns.join(delta_prob.rename("__driver__"), how="inner").tail(lookback)
>     if len(aligned) < max(20, lookback // 2):
>         return pd.Series(np.nan, index=returns.columns)
>
>     x = aligned["__driver__"].to_numpy()
>     betas: dict[str, float] = {}
>     for col in returns.columns:
>         y = aligned[col].to_numpy()
>         mask = ~(np.isnan(y) | np.isnan(x))
>         if mask.sum() < 20:
>             betas[col] = float("nan")
>             continue
>         cov = np.cov(x[mask], y[mask])
>         betas[col] = float(cov[0, 1] / cov[0, 0]) if cov[0, 0] > 0 else float("nan")
>     return pd.Series(betas)
>
>
> def top_bottom_k_betaweighted(betas: pd.Series, k: int) -> dict[str, float]:
>     """Long top-K (largest beta), short bottom-K (smallest beta), weighted by beta.
>
>     Weights are proportional to each selected beta and then normalised so the
>     sum of absolute weights equals 1.0 (gross exposure 100%). Non-selected
>     tickers receive weight 0.0.
>
>     Args:
>         betas: Series of beta values, one per ticker. NaNs are dropped.
>         k:     Number of tickers to long and short.
>
>     Returns:
>         Dict mapping every ticker in `betas.index` to a weight in [-1, 1].
>         Empty/insufficient input returns all zeros.
>     """
>     weights: dict[str, float] = {str(t): 0.0 for t in betas.index}
>     clean = betas.dropna().sort_values(ascending=False)
>     if len(clean) < 2 * k or k <= 0:
>         return weights
>
>     selected = pd.concat([clean.head(k), clean.tail(k)])
>     abs_sum = float(selected.abs().sum())
>     if abs_sum == 0.0:
>         return weights
>
>     for ticker, beta in selected.items():
>         weights[str(ticker)] = float(beta) / abs_sum
>     return weights
> ```
