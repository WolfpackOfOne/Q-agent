---
path: "infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py"
hub: "polymarket"
lines: 67
tags:
  - "code/python"
  - "pipelines/polymarket"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py"
---
# clob.py

`infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py` · hub [[Hubs/Pipelines/polymarket|polymarket]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py)

## Purpose

Polymarket CLOB API client — historical price/probability per token.

Endpoint:
    GET https://clob.polymarket.com/prices-history?market=<token_id>&interval=...&fidelity=...

Each Polymarket market has two outcome tokens (YES / NO). We pull price history
for one token (typically YES); NO is `1 - YES` for binary markets.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#requests|requests]], [[Indexes/External packages#tenacity|tenacity]], [[Indexes/External packages#time|time]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py|__init__.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `CLOB_BASE` | `'https://clob.polymarket.com'` | [19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py#L19) |

## Classes

### class `ClobClient`

[line 23](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py#L23)

- `def __post_init__(self) -> None` — [L28](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py#L28)
- `def _get(self, path: str, params: dict[str, Any] | None=None) -> Any` — [L37](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py#L37)
- `def price_history(self, token_id: str, interval: str='max', fidelity_minutes: int=60) -> pd.DataFrame` — [L44](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py#L44)  
  Return a DataFrame indexed by UTC timestamp with a single `price` column.

## Source

> [!example]- infrastructure/pipelines/polymarket/src/polymarket_lean/clob.py (67 lines)
> ```python
> """Polymarket CLOB API client — historical price/probability per token.
>
> Endpoint:
>     GET https://clob.polymarket.com/prices-history?market=<token_id>&interval=...&fidelity=...
>
> Each Polymarket market has two outcome tokens (YES / NO). We pull price history
> for one token (typically YES); NO is `1 - YES` for binary markets.
> """
> from __future__ import annotations
>
> import time
> from dataclasses import dataclass
> from typing import Any
>
> import pandas as pd
> import requests
> from tenacity import retry, stop_after_attempt, wait_exponential
>
> CLOB_BASE = "https://clob.polymarket.com"
>
>
> @dataclass
> class ClobClient:
>     base_url: str = CLOB_BASE
>     pacing_s: float = 0.20
>     timeout_s: float = 30.0
>
>     def __post_init__(self) -> None:
>         self._session = requests.Session()
>         self._session.headers.update({"User-Agent": "polymarket-lean/0.1"})
>
>     @retry(
>         stop=stop_after_attempt(5),
>         wait=wait_exponential(multiplier=1, min=2, max=30),
>         reraise=True,
>     )
>     def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
>         time.sleep(self.pacing_s)
>         r = self._session.get(f"{self.base_url}{path}", params=params,
>                               timeout=self.timeout_s)
>         r.raise_for_status()
>         return r.json()
>
>     def price_history(
>         self,
>         token_id: str,
>         interval: str = "max",
>         fidelity_minutes: int = 60,
>     ) -> pd.DataFrame:
>         """Return a DataFrame indexed by UTC timestamp with a single `price` column.
>
>         `interval` controls the lookback window: `1h`, `6h`, `1d`, `1w`, `1m`, `max`.
>         `fidelity_minutes` is the minimum bar width; 60 gives hourly.
>         """
>         payload = self._get("/prices-history", params={
>             "market": token_id,
>             "interval": interval,
>             "fidelity": fidelity_minutes,
>         })
>         history = payload.get("history", []) if isinstance(payload, dict) else []
>         if not history:
>             return pd.DataFrame(columns=["price"])
>         df = pd.DataFrame(history)
>         df["datetime"] = pd.to_datetime(df["t"], unit="s", utc=True)
>         df = df.set_index("datetime")[["p"]].rename(columns={"p": "price"})
>         return df.sort_index()
> ```
