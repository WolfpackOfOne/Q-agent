---
path: "infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py"
hub: "polymarket"
lines: 187
tags:
  - "code/python"
  - "pipelines/polymarket"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py"
---
# run_crypto_event_search.py

`infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py` · hub [[Hubs/Pipelines/polymarket|polymarket]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py)

## Purpose

Targeted crypto-event market search using Gamma API search parameter.

Searches for BTC/ETH/SOL ETF approvals, Ethereum upgrades, and Solana outages
using the free-text search endpoint rather than tag filtering (tags no longer
returned by the API as of 2025).

Writes results to lean-data/alternative/polymarket/markets.csv (appends/merges
with any existing rows).

Usage:
    python scripts/run_crypto_event_search.py
    python scripts/run_crypto_event_search.py --active-only
    python scripts/run_crypto_event_search.py --dry-run

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#json|json]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#requests|requests]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]], [[Indexes/External packages#typing|typing]]

## Constants

| Name | Value | Line |
|---|---|---|
| `GAMMA_BASE` | `'https://gamma-api.polymarket.com'` | [27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L27) |
| `SEARCH_QUERIES` | `{'crypto_etf_approvals': ['bitcoin etf', 'spot bitcoin etf', 'ethereum etf', 'spot ethereum etf', 'solana etf', 'xrp etf', 'SEC approve crypto ETF', 'BlackRo...` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L29) |
| `HERE` | `pathlib.Path(__file__).resolve().parent` | [62](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L62) |
| `ROOT` | `HERE.parent` | [63](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L63) |
| `LEAN_ROOT` | `ROOT / 'lean-data' / 'alternative' / 'polymarket'` | [64](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L64) |

## Functions

### `_get()`

```python
def _get(session: requests.Session, url: str, params: dict) -> Any
```
[line 67](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L67)

### `_parse_token_ids()`

```python
def _parse_token_ids(raw: Any) -> tuple[str | None, str | None]
```
[line 74](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L74)

### `search_markets()`

```python
def search_markets(session: requests.Session, query: str, active: bool | None=None, closed: bool | None=None, limit: int=100) -> list[dict]
```
[line 89](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L89)

### `normalize()`

```python
def normalize(market: dict, theme: str, query: str) -> dict
```
[line 105](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L105)

### `main()`

```python
def main() -> int
```
[line 131](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py#L131)

## Source

> [!example]- infrastructure/pipelines/polymarket/scripts/run_crypto_event_search.py (187 lines)
> ```python
> """Targeted crypto-event market search using Gamma API search parameter.
>
> Searches for BTC/ETH/SOL ETF approvals, Ethereum upgrades, and Solana outages
> using the free-text search endpoint rather than tag filtering (tags no longer
> returned by the API as of 2025).
>
> Writes results to lean-data/alternative/polymarket/markets.csv (appends/merges
> with any existing rows).
>
> Usage:
>     python scripts/run_crypto_event_search.py
>     python scripts/run_crypto_event_search.py --active-only
>     python scripts/run_crypto_event_search.py --dry-run
> """
> from __future__ import annotations
>
> import argparse
> import json
> import pathlib
> import sys
> import time
> from typing import Any
>
> import pandas as pd
> import requests
>
> GAMMA_BASE = "https://gamma-api.polymarket.com"
>
> SEARCH_QUERIES: dict[str, list[str]] = {
>     "crypto_etf_approvals": [
>         "bitcoin etf",
>         "spot bitcoin etf",
>         "ethereum etf",
>         "spot ethereum etf",
>         "solana etf",
>         "xrp etf",
>         "SEC approve crypto ETF",
>         "BlackRock bitcoin ETF",
>         "Grayscale ETF",
>     ],
>     "ethereum_upgrades": [
>         "ethereum upgrade",
>         "ethereum hard fork",
>         "ethereum pectra",
>         "ethereum dencun",
>         "ethereum fusaka",
>         "ethereum merge",
>         "ethereum shanghai",
>         "ethereum cancun",
>         "ETH upgrade",
>     ],
>     "solana_outages": [
>         "solana outage",
>         "solana halt",
>         "solana network down",
>         "solana downtime",
>         "solana restart",
>         "SOL outage",
>     ],
> }
>
> HERE = pathlib.Path(__file__).resolve().parent
> ROOT = HERE.parent
> LEAN_ROOT = ROOT / "lean-data" / "alternative" / "polymarket"
>
>
> def _get(session: requests.Session, url: str, params: dict) -> Any:
>     time.sleep(0.25)
>     r = session.get(url, params=params, timeout=30)
>     r.raise_for_status()
>     return r.json()
>
>
> def _parse_token_ids(raw: Any) -> tuple[str | None, str | None]:
>     if not raw:
>         return None, None
>     if isinstance(raw, str):
>         try:
>             ids = json.loads(raw)
>         except json.JSONDecodeError:
>             return None, None
>     else:
>         ids = raw
>     if not isinstance(ids, list) or len(ids) < 2:
>         return None, None
>     return str(ids[0]), str(ids[1])
>
>
> def search_markets(
>     session: requests.Session,
>     query: str,
>     active: bool | None = None,
>     closed: bool | None = None,
>     limit: int = 100,
> ) -> list[dict]:
>     params: dict[str, Any] = {"search": query, "limit": limit}
>     if active is not None:
>         params["active"] = str(active).lower()
>     if closed is not None:
>         params["closed"] = str(closed).lower()
>     data = _get(session, f"{GAMMA_BASE}/markets", params=params)
>     return data if isinstance(data, list) else []
>
>
> def normalize(market: dict, theme: str, query: str) -> dict:
>     yes_id, no_id = _parse_token_ids(market.get("clobTokenIds"))
>     events = market.get("events") or []
>     ev = events[0] if events else {}
>     return {
>         "MarketId": market.get("id"),
>         "Theme": theme,
>         "SearchQuery": query,
>         "Slug": market.get("slug"),
>         "Question": market.get("question"),
>         "EventSlug": ev.get("slug"),
>         "EventTitle": ev.get("title"),
>         "Active": market.get("active"),
>         "Closed": market.get("closed"),
>         "Archived": market.get("archived"),
>         "StartDate": market.get("startDate"),
>         "EndDate": market.get("endDate"),
>         "ResolvedOutcome": market.get("resolvedOutcome"),
>         "OutcomePrices": market.get("outcomePrices"),
>         "Volume": market.get("volumeNum") or market.get("volume"),
>         "Liquidity": market.get("liquidityNum") or market.get("liquidity"),
>         "YesTokenId": yes_id,
>         "NoTokenId": no_id,
>     }
>
>
> def main() -> int:
>     p = argparse.ArgumentParser(description=__doc__)
>     p.add_argument("--active-only", action="store_true",
>                    help="Skip closed/resolved markets.")
>     p.add_argument("--dry-run", action="store_true",
>                    help="Print what would be fetched, don't write.")
>     args = p.parse_args()
>
>     session = requests.Session()
>     session.headers["User-Agent"] = "polymarket-lean-crypto/0.1"
>
>     rows: list[dict] = []
>     seen_slugs: set[str] = set()
>
>     for theme, queries in SEARCH_QUERIES.items():
>         print(f"\n[{theme}]", file=sys.stderr)
>         for query in queries:
>             for active, closed in (
>                 [(True, False)] if args.active_only else [(True, False), (False, True)]
>             ):
>                 label = "active" if active else "closed"
>                 try:
>                     markets = search_markets(session, query, active=active, closed=closed)
>                 except Exception as exc:
>                     print(f"  WARN: {query!r} ({label}): {exc}", file=sys.stderr)
>                     continue
>
>                 new = 0
>                 for m in markets:
>                     slug = m.get("slug") or m.get("id")
>                     if slug in seen_slugs:
>                         continue
>                     seen_slugs.add(slug)
>                     rows.append(normalize(m, theme, query))
>                     new += 1
>
>                 print(f"  {query!r} ({label}): +{new}", file=sys.stderr)
>
>     print(f"\nTotal unique markets: {len(rows)}", file=sys.stderr)
>
>     if args.dry_run:
>         print("--dry-run: not writing.", file=sys.stderr)
>         for r in rows[:5]:
>             print(r["Slug"], "|", r["Question"])
>         return 0
>
>     df = pd.DataFrame(rows)
>     out_path = LEAN_ROOT / "markets.csv"
>     LEAN_ROOT.mkdir(parents=True, exist_ok=True)
>     df.to_csv(out_path, index=False)
>     print(f"Wrote {len(df)} rows → {out_path}", file=sys.stderr)
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
