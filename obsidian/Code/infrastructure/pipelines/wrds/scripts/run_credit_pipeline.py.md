---
path: "infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py"
hub: "wrds"
lines: 88
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py"
---
# run_credit_pipeline.py

`infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py)

## Purpose

CLI for Markit CDS and TRACE credit-market exports.

## Dependencies

**Imports (workspace):** [[Code/infrastructure/pipelines/wrds/src/wrds_lean/connection.py|connection.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|credit.py]]

**Imports (external):** [[Indexes/External packages#argparse|argparse]], [[Indexes/External packages#os|os]], [[Indexes/External packages#sys|sys]], [[Indexes/External packages#time|time]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA` | `os.path.join(os.path.dirname(__file__), '..', 'lean-data')` | [18](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py#L18) |

## Functions

### `main()`

```python
def main()
```
[line 21](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py#L21)

## Source

> [!example]- infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py (88 lines)
> ```python
> """CLI for Markit CDS and TRACE credit-market exports."""
>
> import argparse
> import os
> import sys
> import time
>
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
>
> from wrds_lean.connection import close_connection, set_connection_profile
> from wrds_lean.credit import (
>     extract_cds,
>     extract_trace_trades,
>     publish_cds,
>     publish_trace,
> )
>
> LEAN_DATA = os.path.join(os.path.dirname(__file__), '..', 'lean-data')
>
>
> def main():
>     parser = argparse.ArgumentParser(description='WRDS credit data pipeline')
>     parser.add_argument('--profile', default=None,
>                         help='Named WRDS profile from .wrds_profiles.json')
>     parser.add_argument('--start', default=None, help='Start date YYYY-MM-DD')
>     parser.add_argument('--end', default=None, help='End date YYYY-MM-DD')
>     parser.add_argument('--cds', action='store_true', help='Export Markit CDS')
>     parser.add_argument('--trace', action='store_true', help='Export TRACE trades')
>     parser.add_argument('--enhanced-trace', action='store_true',
>                         help='Use trace_enhanced.trace_enhanced for TRACE')
>     parser.add_argument('--tickers', nargs='+', default=None,
>                         help='Company tickers/symbols to filter')
>     parser.add_argument('--cusips', nargs='+', default=None,
>                         help='TRACE CUSIPs to filter')
>     parser.add_argument('--tenors', nargs='+', default=['5Y'],
>                         help='CDS tenors (default: 5Y)')
>     parser.add_argument('--grades', nargs='+', default=None,
>                         help='TRACE bond grades: I/IG/investment_grade, H/HY/high_yield, N/NR/not_rated')
>     parser.add_argument('--years', nargs='+', type=int, default=None,
>                         help='Explicit CDS yearly tables to scan')
>     parser.add_argument('--limit', type=int, default=None,
>                         help='Limit TRACE rows for exploration')
>     args = parser.parse_args()
>
>     if not args.cds and not args.trace:
>         args.cds = True
>
>     set_connection_profile(args.profile)
>     if args.profile:
>         print(f"Using WRDS profile: {args.profile}")
>
>     t0 = time.time()
>
>     if args.cds:
>         print("=== Extracting Markit CDS ===")
>         cds = extract_cds(
>             tickers=args.tickers,
>             start=args.start,
>             end=args.end,
>             tenors=args.tenors,
>             years=args.years,
>         )
>         print(f"  {len(cds):,} rows")
>         path = publish_cds(cds, LEAN_DATA)
>         print(f"  Written to {path}")
>
>     if args.trace:
>         print("\n=== Extracting TRACE trades ===")
>         trace = extract_trace_trades(
>             tickers=args.tickers,
>             cusips=args.cusips,
>             start=args.start,
>             end=args.end,
>             enhanced=args.enhanced_trace,
>             grades=args.grades,
>             limit=args.limit,
>         )
>         print(f"  {len(trace):,} rows")
>         path = publish_trace(trace, LEAN_DATA, enhanced=args.enhanced_trace)
>         print(f"  Written to {path}")
>
>     close_connection()
>     print(f"\n=== Credit pipeline complete in {time.time() - t0:.1f}s ===")
>
>
> if __name__ == '__main__':
>     main()
> ```
