---
path: "infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py"
hub: "wrds"
lines: 54
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py"
---
# run_finratio_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py)

## Purpose

CLI for WRDS financial ratio exports.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py|ratios.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [14](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py#L14) |

## Functions

### `main()`

```python
def main()
```
[line 17](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py#L17)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py (54 lines)
> ```python
> """CLI for WRDS financial ratio exports."""
>
> import argparse
> import os
> import sys
> import time
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.ratios import extract_financial_ratios, publish_financial_ratios
> from wrds_lean.symbols import UNIVERSE
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
>
>
> def main():
>     parser = argparse.ArgumentParser(description='WRDS financial ratios pipeline')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Tickers to pull (default: 30-stock universe)')
>     parser.add_argument('--start', default=None, help='Start public date YYYY-MM-DD')
>     parser.add_argument('--end', default=None, help='End public date YYYY-MM-DD')
>     parser.add_argument('--columns', nargs='+', default=None,
>                         help='Override output columns from firm_ratio plus ticker')
>     args = parser.parse_args()
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     tickers = args.tickers or list(UNIVERSE)
>     t0 = time.time()
>
>     print(f"=== Extracting financial ratios for {len(tickers)} tickers ===")
>     ratios = extract_financial_ratios(
>         tickers=tickers,
>         start=args.start,
>         end=args.end,
>         columns=args.columns,
>     )
>     print(f"  {len(ratios):,} rows")
>
>     path = publish_financial_ratios(ratios, LEAN_DATA)
>     print(f"  Written to {path}")
>
>     close_connection()
>     print(f"\n=== Financial ratios pipeline complete in {time.time() - t0:.1f}s ===")
>
>
> if __name__ == '__main__':
>     main()
> ```
