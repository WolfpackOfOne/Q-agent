---
path: "infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py"
hub: "wrds"
lines: 67
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py"
---
# run_13f_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py)

## Purpose

CLI for Thomson Reuters 13F institutional ownership exports.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py|ownership.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py#L19) |

## Functions

### `main()`

```python
def main()
```
[line 22](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py#L22)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py (67 lines)
> ```python
> """CLI for Thomson Reuters 13F institutional ownership exports."""
>
> import argparse
> import os
> import sys
> import time
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.ownership import (
>     build_13f_summary,
>     extract_13f_holdings,
>     publish_13f_holdings,
>     publish_13f_summary,
> )
> from wrds_lean.symbols import UNIVERSE
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
>
>
> def main():
>     parser = argparse.ArgumentParser(description='WRDS 13F ownership pipeline')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Tickers to pull (default: 30-stock universe)')
>     parser.add_argument('--start', default=None, help='Start report date YYYY-MM-DD')
>     parser.add_argument('--end', default=None, help='End report date YYYY-MM-DD')
>     parser.add_argument('--min-shares', type=float, default=None,
>                         help='Optional minimum manager holding size')
>     parser.add_argument('--summary-only', action='store_true',
>                         help='Only publish ticker-date aggregates')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     tickers = args.tickers or list(UNIVERSE)
>     t0 = time.time()
>
>     print(f"=== Extracting 13F holdings for {len(tickers)} tickers ===")
>     holdings = extract_13f_holdings(
>         tickers=tickers,
>         start=args.start,
>         end=args.end,
>         min_shares=args.min_shares,
>     )
>     print(f"  {len(holdings):,} manager-position rows")
>
>     summary = build_13f_summary(holdings)
>     print(f"  {len(summary):,} ticker-date summary rows")
>     summary_path = publish_13f_summary(summary, LEAN_DATA)
>     print(f"  Summary: {summary_path}")
>
>     if not args.summary_only:
>         holdings_path = publish_13f_holdings(holdings, LEAN_DATA)
>         print(f"  Holdings: {holdings_path}")
>
>     close_connection()
>     print(f"\n=== 13F pipeline complete in {time.time() - t0:.1f}s ===")
>
>
> if __name__ == '__main__':
>     main()
> ```
