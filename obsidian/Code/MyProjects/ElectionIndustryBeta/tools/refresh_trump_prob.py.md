---
path: "MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py"
hub: "ElectionIndustryBeta"
layer: "Tool (offline refresh)"
lines: 68
tags:
  - "code/python"
  - "projects/ElectionIndustryBeta"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py"
---
# refresh_trump_prob.py

`MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py` · hub [[Hubs/Projects/ElectionIndustryBeta|ElectionIndustryBeta]] · layer **Tool (offline refresh)** · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py)

## Purpose

One-off refresher for the bundled Polymarket Trump-probability snapshot.

Run manually whenever you want a fresher CSV — the algorithm itself never
makes HTTP calls.

    cd ~/Documents/Q-agent/MyProjects/ElectionIndustryBeta
    python tools/refresh_trump_prob.py

Writes `data/trump_prob.csv` with columns: date, prob_trump.

Source: Polymarket CLOB API — "Will Donald Trump win the 2024 US Presidential
Election?" YES token. Same request signature as the marimo notebook at
infrastructure/marimo/notebooks/election_industry_returns.py:101.

## Dependencies

**Imports (workspace):** [[Code/MyProjects/ElectionIndustryBeta/domain/config.py|config.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#requests|requests]], [[Indexes/External packages#sys|sys]]

## Constants

| Name | Value | Line |
|---|---|---|
| `HERE` | `Path(__file__).resolve().parent` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py#L26) |
| `PROJECT_ROOT` | `HERE.parent` | [27](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py#L27) |

## Functions

### `fetch_trump_prob()`

```python
def fetch_trump_prob() -> pd.DataFrame
```
[line 32](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py#L32)

Pull daily Trump YES-token prices from Polymarket CLOB.

### `main()`

```python
def main() -> int
```
[line 54](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py#L54)

## Source

> [!example]- MyProjects/ElectionIndustryBeta/tools/refresh_trump_prob.py (68 lines)
> ```python
> """
> One-off refresher for the bundled Polymarket Trump-probability snapshot.
>
> Run manually whenever you want a fresher CSV — the algorithm itself never
> makes HTTP calls.
>
>     cd ~/Documents/Q-agent/MyProjects/ElectionIndustryBeta
>     python tools/refresh_trump_prob.py
>
> Writes `data/trump_prob.csv` with columns: date, prob_trump.
>
> Source: Polymarket CLOB API — "Will Donald Trump win the 2024 US Presidential
> Election?" YES token. Same request signature as the marimo notebook at
> infrastructure/marimo/notebooks/election_industry_returns.py:101.
> """
>
> from __future__ import annotations
>
> import sys
> from pathlib import Path
>
> import pandas as pd
> import requests
>
> # Token + endpoint live in domain.config so refresher and algorithm agree.
> HERE = Path(__file__).resolve().parent
> PROJECT_ROOT = HERE.parent
> sys.path.insert(0, str(PROJECT_ROOT))
> from domain.config import TRUMP_TOKEN, POLYMARKET_PRICES_URL, TRUMP_PROB_CSV  # noqa: E402
>
>
> def fetch_trump_prob() -> pd.DataFrame:
>     """Pull daily Trump YES-token prices from Polymarket CLOB."""
>     r = requests.get(
>         POLYMARKET_PRICES_URL,
>         params={"market": TRUMP_TOKEN, "interval": "max", "fidelity": 1440},
>         timeout=30,
>     )
>     r.raise_for_status()
>     history = r.json().get("history", [])
>     if not history:
>         raise RuntimeError("Polymarket returned an empty history payload")
>
>     df = pd.DataFrame(history)
>     df["date"] = pd.to_datetime(df["t"], unit="s").dt.normalize()
>     df["prob_trump"] = df["p"].astype(float)
>     df = df.set_index("date")[["prob_trump"]].sort_index()
>
>     # De-duplicate any same-day samples (Polymarket sometimes returns more than one).
>     df = df.groupby(level=0).last()
>     return df
>
>
> def main() -> int:
>     out_path = PROJECT_ROOT / TRUMP_PROB_CSV
>     out_path.parent.mkdir(parents=True, exist_ok=True)
>
>     df = fetch_trump_prob()
>     df.to_csv(out_path)
>     print(f"Wrote {len(df)} rows to {out_path.relative_to(PROJECT_ROOT)}")
>     print(f"  Date range : {df.index[0].date()} → {df.index[-1].date()}")
>     print(f"  Prob range : {df['prob_trump'].min():.3f} – {df['prob_trump'].max():.3f}")
>     return 0
>
>
> if __name__ == "__main__":
>     sys.exit(main())
> ```
