---
path: "infrastructure/pipelines/crypto/scripts/run_pipeline.py"
hub: "crypto"
lines: 90
tags:
  - "code/python"
  - "pipelines/crypto"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py"
---
# run_pipeline.py

`infrastructure/pipelines/crypto/scripts/run_pipeline.py` · hub [[Hubs/Pipelines/crypto|crypto]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py)

## Purpose

Pull crypto OHLCV from a chosen exchange and write LEAN zips.

Examples:

    python scripts/run_pipeline.py --exchange coinbase --pairs BTC/USD ETH/USD
    python scripts/run_pipeline.py --exchange kraken --resolution daily \
        --start 2018-01-01 --end 2024-12-31

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/crypto/src/crypto_lean/__init__.py|__init__.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#dotenv|dotenv]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#tqdm|tqdm]]

## Constants

| Name | Value | Line |
|---|---|---|
| `HERE` | `pathlib.Path(__file__).resolve().parent` | [29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py#L29) |
| `ROOT` | `HERE.parent` | [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py#L30) |
| `LEAN_ROOT` | `ROOT / 'lean-data'` | [31](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py#L31) |

## Functions

### `parse_args()`

```python
def parse_args() -> argparse.Namespace
```
[line 34](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py#L34)

### `main()`

```python
def main() -> int
```
[line 52](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/scripts/run_pipeline.py#L52)

## Source

> [!example]- infrastructure/pipelines/crypto/scripts/run_pipeline.py (90 lines)
> ```python
> """Pull crypto OHLCV from a chosen exchange and write LEAN zips.
>
> Examples:
>
>     python scripts/run_pipeline.py --exchange coinbase --pairs BTC/USD ETH/USD
>     python scripts/run_pipeline.py --exchange kraken --resolution daily \\
>         --start 2018-01-01 --end 2024-12-31
> """
> from __future__ import annotations
>
> import argparse
> import pathlib
> import sys
> from datetime import datetime
>
> import pandas as pd
> from dotenv import load_dotenv
> from tqdm import tqdm
>
> from crypto_lean import (
>     DEFAULT_PAIRS,
>     ExchangeClient,
>     to_lean_daily,
>     to_lean_minute,
>     write_lean_zip,
> )
>
>
> HERE = pathlib.Path(__file__).resolve().parent
> ROOT = HERE.parent
> LEAN_ROOT = ROOT / "lean-data"
>
>
> def parse_args() -> argparse.Namespace:
>     p = argparse.ArgumentParser(description=__doc__)
>     p.add_argument(
>         "--exchange", required=True, choices=["coinbase", "kraken"]
>     )
>     p.add_argument(
>         "--pairs", nargs="+", default=DEFAULT_PAIRS,
>         help="Pairs in ccxt format (BTC/USDT). Defaults to BTC/ETH/SOL × USD/USDT/USDC.",
>     )
>     p.add_argument("--resolution", default="daily", choices=["daily", "minute"])
>     p.add_argument("--start", default="2017-01-01")
>     p.add_argument("--end", default=None,
>                    help="UTC end date (default: today)")
>     p.add_argument("--lean-root", default=str(LEAN_ROOT),
>                    help="Output root (default: infrastructure/crypto/lean-data)")
>     return p.parse_args()
>
>
> def main() -> int:
>     load_dotenv(ROOT / ".env")
>     args = parse_args()
>
>     start = pd.Timestamp(args.start, tz="UTC")
>     end = pd.Timestamp(args.end, tz="UTC") if args.end else pd.Timestamp.utcnow()
>     lean_root = pathlib.Path(args.lean_root)
>
>     print(f"Connecting to {args.exchange}…", file=sys.stderr)
>     client = ExchangeClient(exchange=args.exchange)
>
>     pairs = client.supported_pairs(args.pairs)
>     skipped = sorted(set(args.pairs) - set(pairs))
>     if skipped:
>         print(f"  Skipping unlisted pairs: {', '.join(skipped)}", file=sys.stderr)
>     if not pairs:
>         print("  No listed pairs to fetch — exiting.", file=sys.stderr)
>         return 1
>
>     tf = "1d" if args.resolution == "daily" else "1m"
>     written = 0
>     for pair in tqdm(pairs, desc=f"{args.exchange} {args.resolution}"):
>         df = client.fetch_ohlcv(pair, timeframe=tf, start=start, end=end)
>         if df.empty:
>             tqdm.write(f"  {pair}: no data")
>             continue
>         payload = to_lean_daily(df) if args.resolution == "daily" else to_lean_minute(df)
>         path = write_lean_zip(lean_root, args.exchange, pair, args.resolution, payload)
>         tqdm.write(f"  {pair}: {len(df)} bars → {path}")
>         written += 1
>
>     print(f"\nDone. Wrote {written}/{len(pairs)} pairs at {datetime.utcnow()}Z.",
>           file=sys.stderr)
>     return 0
>
>
> if __name__ == "__main__":
>     raise SystemExit(main())
> ```
