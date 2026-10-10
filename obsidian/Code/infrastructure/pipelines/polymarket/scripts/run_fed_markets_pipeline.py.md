---
path: "infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py"
hub: "polymarket"
lines: 213
tags:
  - "code/python"
  - "pipelines/polymarket"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py"
---
# run_fed_markets_pipeline.py

`infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py` · hub [[Hubs/Pipelines/polymarket|polymarket]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py)

## Purpose

Snapshot Fed/macro Polymarket markets via Gamma offset pagination.

Keyword-filters on `question` text (tags and search= are broken as of May 2026).
Captures volumeNum and liquidityNum from Gamma API response.

Output: lean-data/alternative/polymarket/markets.csv

Examples:

    python scripts/run_fed_markets_pipeline.py
    python scripts/run_fed_markets_pipeline.py --dry-run
    python scripts/run_fed_markets_pipeline.py --include-active-only
    python scripts/run_fed_markets_pipeline.py --snapshot

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#json|json]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#requests|requests]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]], [[Indexes/External packages#tqdm|tqdm]], [[Indexes/External packages#typing|typing]]

## Constants

| Name | Value | Line |
|---|---|---|
| `GAMMA_BASE` | `'https://gamma-api.polymarket.com'` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L29) |
| `PACING_S` | `0.2` | [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L30) |
| `FED_KEYWORDS` | `('federal reserve', 'fed rate', 'fomc', 'interest rate', 'jerome powell', 'fed chair', 'basis points', ' bps ', 'rate cut', 'rate hike', 'rate increase', 'ra...` | [33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L33) |
| `EXCLUDE_TERMS` | `('bank of england', 'bank of japan', 'ecb', 'european central', 'reserve bank of', 'nba', 'norman powell', 'turkey', 'turkish', 'canada', 'australian', 'rba ')` | [52](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L52) |
| `HERE` | `pathlib.Path(__file__).resolve().parent` | [67](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L67) |
| `ROOT` | `HERE.parent` | [68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L68) |
| `LEAN_ROOT` | `ROOT / 'lean-data' / 'alternative' / 'polymarket'` | [69](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L69) |

## Functions

### `_get()`

```python
def _get(session: requests.Session, url: str, params: dict[str, Any]) -> Any | None
```
[line 72](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L72)

Return parsed JSON or None on 422 (offset cap exceeded).

### `_parse_token_ids()`

```python
def _parse_token_ids(raw: Any) -> tuple[str | None, str | None]
```
[line 82](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L82)

### `_matches()`

```python
def _matches(question: str) -> bool
```
[line 97](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L97)

### `_normalize()`

```python
def _normalize(market: dict[str, Any]) -> dict[str, Any]
```
[line 106](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L106)

### `iter_gamma_markets()`

```python
def iter_gamma_markets(session: requests.Session, include_closed: bool=True) -> list[dict[str, Any]]
```
[line 133](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L133)

Paginate Gamma /markets, yield all raw market dicts.

### `main()`

```python
def main() -> int
```
[line 160](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py#L160)

## Source

> [!example]- infrastructure/pipelines/polymarket/scripts/run_fed_markets_pipeline.py (213 lines)
> ```python
> """Snapshot Fed/macro Polymarket markets via Gamma offset pagination.
>
> Keyword-filters on `question` text (tags and search= are broken as of May 2026).
> Captures volumeNum and liquidityNum from Gamma API response.
>
> Output: lean-data/alternative/polymarket/markets.csv
>
> Examples:
>
>     python scripts/run_fed_markets_pipeline.py
>     python scripts/run_fed_markets_pipeline.py --dry-run
>     python scripts/run_fed_markets_pipeline.py --include-active-only
>     python scripts/run_fed_markets_pipeline.py --snapshot
> """
> from __future__ import annotations
>
> import argparse
> import json
> import pathlib
> import sys
> import time
> from datetime import datetime, timezone
> from typing import Any
>
> import pandas as pd
> import requests
> from tqdm import tqdm
>
> GAMMA_BASE = "https://gamma-api.polymarket.com"
> PACING_S = 0.20
>
> # Client-side keyword filter on market `question` text.
> FED_KEYWORDS: tuple[str, ...] = (
>     "federal reserve",
>     "fed rate",
>     "fomc",
>     "interest rate",
>     "jerome powell",
>     "fed chair",
>     "basis points",
>     " bps ",
>     "rate cut",
>     "rate hike",
>     "rate increase",
>     "rate decrease",
>     "quantitative",
>     "federal funds",
>     "fed meeting",
>     "fed decision",
> )
>
> EXCLUDE_TERMS: tuple[str, ...] = (
>     "bank of england",
>     "bank of japan",
>     "ecb",
>     "european central",
>     "reserve bank of",
>     "nba",
>     "norman powell",
>     "turkey",
>     "turkish",
>     "canada",
>     "australian",
>     "rba ",
> )
>
> HERE = pathlib.Path(__file__).resolve().parent
> ROOT = HERE.parent
> LEAN_ROOT = ROOT / "lean-data" / "alternative" / "polymarket"
>
>
> def _get(session: requests.Session, url: str, params: dict[str, Any]) -> Any | None:
>     """Return parsed JSON or None on 422 (offset cap exceeded)."""
>     time.sleep(PACING_S)
>     r = session.get(url, params=params, timeout=30)
>     if r.status_code == 422:
>         return None
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
> def _matches(question: str) -> bool:
>     q = question.lower()
>     if not any(kw in q for kw in FED_KEYWORDS):
>         return False
>     if any(ex in q for ex in EXCLUDE_TERMS):
>         return False
>     return True
>
>
> def _normalize(market: dict[str, Any]) -> dict[str, Any]:
>     yes_id, no_id = _parse_token_ids(market.get("clobTokenIds"))
>     end_date = market.get("endDate") or market.get("end_date_iso") or ""
>     year = None
>     if end_date:
>         try:
>             year = int(end_date[:4])
>         except (ValueError, TypeError):
>             pass
>     return {
>         "MarketId": market.get("id"),
>         "Slug": market.get("slug"),
>         "Question": market.get("question"),
>         "EndDate": end_date,
>         "Active": market.get("active"),
>         "Closed": market.get("closed"),
>         "Archived": market.get("archived"),
>         "ResolvedOutcome": market.get("resolvedOutcome"),
>         "Volume": market.get("volumeNum") or market.get("volume"),
>         "Liquidity": market.get("liquidityNum") or market.get("liquidity"),
>         "Volume24hr": market.get("volume24hr"),
>         "Year": year,
>         "YesTokenId": yes_id,
>         "NoTokenId": no_id,
>     }
>
>
> def iter_gamma_markets(
>     session: requests.Session,
>     include_closed: bool = True,
> ) -> list[dict[str, Any]]:
>     """Paginate Gamma /markets, yield all raw market dicts."""
>     offset = 0
>     limit = 100
>     all_markets: list[dict[str, Any]] = []
>     with tqdm(desc="fetching pages", unit="page") as pbar:
>         while True:
>             params: dict[str, Any] = {"limit": limit, "offset": offset}
>             if not include_closed:
>                 params["closed"] = "false"
>             batch = _get(session, f"{GAMMA_BASE}/markets", params=params)
>             if batch is None:  # 422 offset cap hit
>                 break
>             if not batch:
>                 break
>             all_markets.extend(batch)
>             pbar.update(1)
>             pbar.set_postfix(total=len(all_markets))
>             if len(batch) < limit:
>                 break
>             offset += limit
>     return all_markets
>
>
> def main() -> int:
>     p = argparse.ArgumentParser(description=__doc__)
>     p.add_argument("--include-active-only", action="store_true",
>                    help="Skip closed/resolved markets.")
>     p.add_argument("--snapshot", action="store_true",
>                    help="Also write a dated snapshot under markets_history/<YYYYMMDD>.csv.")
>     p.add_argument("--dry-run", action="store_true",
>                    help="Print matches, don't write.")
>     args = p.parse_args()
>
>     session = requests.Session()
>     session.headers["User-Agent"] = "polymarket-lean-fed/0.1"
>
>     print("Paginating Gamma API...", file=sys.stderr)
>     all_markets = iter_gamma_markets(session, include_closed=not args.include_active_only)
>     print(f"Total markets fetched: {len(all_markets)}", file=sys.stderr)
>
>     matched = [m for m in all_markets if _matches(m.get("question") or "")]
>     print(f"Matched {len(matched)} Fed/macro markets after keyword filter.", file=sys.stderr)
>
>     if args.dry_run:
>         for m in matched[:20]:
>             vol = m.get("volumeNum", 0)
>             liq = m.get("liquidityNum", 0)
>             print(f"  vol={vol:>12,.0f}  liq={liq:>10,.0f}  {m.get('question', '')[:80]}")
>         return 0
>
>     rows = [_normalize(m) for m in matched]
>     df = pd.DataFrame(rows)
>
>     out_path = LEAN_ROOT / "markets.csv"
>     LEAN_ROOT.mkdir(parents=True, exist_ok=True)
>     df.to_csv(out_path, index=False)
>     print(f"Wrote {len(df)} rows → {out_path}", file=sys.stderr)
>
>     if args.snapshot:
>         stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
>         snap_path = LEAN_ROOT / "markets_history" / f"{stamp}.csv"
>         snap_path.parent.mkdir(parents=True, exist_ok=True)
>         df.to_csv(snap_path, index=False)
>         print(f"Wrote snapshot → {snap_path}", file=sys.stderr)
>
>     # Summary stats
>     vol_nonzero = (df["Volume"].fillna(0) > 0).sum()
>     liq_nonzero = (df["Liquidity"].fillna(0) > 0).sum()
>     print(f"Volume non-zero: {vol_nonzero}/{len(df)}", file=sys.stderr)
>     print(f"Liquidity non-zero: {liq_nonzero}/{len(df)}", file=sys.stderr)
>
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
