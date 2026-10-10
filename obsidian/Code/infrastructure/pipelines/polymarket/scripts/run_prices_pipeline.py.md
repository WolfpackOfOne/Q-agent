---
path: "infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py"
hub: "polymarket"
lines: 96
tags:
  - "code/python"
  - "pipelines/polymarket"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py"
---
# run_prices_pipeline.py

`infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py` · hub [[Hubs/Pipelines/polymarket|polymarket]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py)

## Purpose

Pull historical YES-token price series for each market in markets.csv.

Reads `lean-data/alternative/polymarket/markets.csv` (produced by
`run_markets_pipeline.py`) and writes one CSV per market into
`lean-data/alternative/polymarket/prices/<slug>.csv`.

Skip markets missing a YES token id. Heavy — uses `--limit` for quick runs.

Examples:

    python scripts/run_prices_pipeline.py --limit 10
    python scripts/run_prices_pipeline.py --interval 1m --fidelity 60

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/polymarket/src/polymarket_lean/__init__.py|__init__.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#dotenv|dotenv]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#tqdm|tqdm]]

## Constants

| Name | Value | Line |
|---|---|---|
| `HERE` | `pathlib.Path(__file__).resolve().parent` | [27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py#L27) |
| `ROOT` | `HERE.parent` | [28](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py#L28) |
| `LEAN_ROOT` | `ROOT / 'lean-data' / 'alternative' / 'polymarket'` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py#L29) |

## Functions

### `parse_args()`

```python
def parse_args() -> argparse.Namespace
```
[line 32](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py#L32)

### `main()`

```python
def main() -> int
```
[line 47](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py#L47)

## Source

> [!example]- infrastructure/pipelines/polymarket/scripts/run_prices_pipeline.py (96 lines)
> ```python
> """Pull historical YES-token price series for each market in markets.csv.
>
> Reads `lean-data/alternative/polymarket/markets.csv` (produced by
> `run_markets_pipeline.py`) and writes one CSV per market into
> `lean-data/alternative/polymarket/prices/<slug>.csv`.
>
> Skip markets missing a YES token id. Heavy — uses `--limit` for quick runs.
>
> Examples:
>
>     python scripts/run_prices_pipeline.py --limit 10
>     python scripts/run_prices_pipeline.py --interval 1m --fidelity 60
> """
> from __future__ import annotations
>
> import argparse
> import pathlib
> import sys
>
> import pandas as pd
> from dotenv import load_dotenv
> from tqdm import tqdm
>
> from polymarket_lean import ClobClient, write_market_prices_csv
>
>
> HERE = pathlib.Path(__file__).resolve().parent
> ROOT = HERE.parent
> LEAN_ROOT = ROOT / "lean-data" / "alternative" / "polymarket"
>
>
> def parse_args() -> argparse.Namespace:
>     p = argparse.ArgumentParser(description=__doc__)
>     p.add_argument("--markets-csv", default=str(LEAN_ROOT / "markets.csv"))
>     p.add_argument("--prices-dir", default=str(LEAN_ROOT / "prices"))
>     p.add_argument("--interval", default="max",
>                    choices=["1h", "6h", "1d", "1w", "1m", "max"])
>     p.add_argument("--fidelity", type=int, default=60,
>                    help="Bar width in minutes (60 = hourly).")
>     p.add_argument("--limit", type=int, default=None,
>                    help="Stop after N markets — for smoke tests.")
>     p.add_argument("--skip-existing", action="store_true",
>                    help="Skip markets whose price CSV already exists.")
>     return p.parse_args()
>
>
> def main() -> int:
>     load_dotenv(ROOT / ".env")
>     args = parse_args()
>
>     markets_csv = pathlib.Path(args.markets_csv)
>     prices_dir = pathlib.Path(args.prices_dir)
>
>     if not markets_csv.exists():
>         print(f"markets.csv not found at {markets_csv}; run run_markets_pipeline.py first.",
>               file=sys.stderr)
>         return 1
>
>     markets = pd.read_csv(markets_csv)
>     if args.limit:
>         markets = markets.head(args.limit)
>     markets = markets.dropna(subset=["YesTokenId", "Slug"])
>
>     client = ClobClient()
>     written = 0
>     empty = 0
>     skipped = 0
>     for _, row in tqdm(markets.iterrows(), total=len(markets), desc="prices"):
>         slug = str(row["Slug"])
>         out_path = prices_dir / f"{slug}.csv"
>         if args.skip_existing and out_path.exists():
>             skipped += 1
>             continue
>         try:
>             df = client.price_history(
>                 token_id=str(row["YesTokenId"]),
>                 interval=args.interval,
>                 fidelity_minutes=args.fidelity,
>             )
>         except Exception as exc:  # noqa: BLE001
>             tqdm.write(f"  {slug}: error — {exc}")
>             continue
>         if df.empty:
>             empty += 1
>             continue
>         write_market_prices_csv(df, slug, prices_dir)
>         written += 1
>
>     print(f"\nWrote {written} markets, {empty} empty, {skipped} skipped → {prices_dir}",
>           file=sys.stderr)
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
