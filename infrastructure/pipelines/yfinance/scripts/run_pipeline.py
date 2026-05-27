"""yfinance-to-LEAN daily data pipeline (equity + forex).

Usage (equity):
    python scripts/run_pipeline.py --tickers AAPL MSFT SPY
    python scripts/run_pipeline.py --tickers AAPL --start 2010-01-01 --end 2024-12-31
    python scripts/run_pipeline.py --tickers AAPL --output /path/to/lean-data

Usage (forex — free daily FX from Yahoo, no API key):
    python scripts/run_pipeline.py --asset forex                 # defaults: EURUSD GBPUSD USDJPY
    python scripts/run_pipeline.py --asset forex --tickers GBP EUR JPY
    python scripts/run_pipeline.py --asset forex --tickers EURUSD GBPUSD --market oanda

Forex tickers accept either a 3-letter currency code (mapped to its major USD
pair) or a full 6-letter pair. Output goes to forex/<market>/daily/<pair>.zip.

Output goes to infrastructure/pipelines/yfinance/lean-data/ by default.
Point lean.json at that directory for local backtests:
    "data-folder": "~/Documents/Q-agent/infrastructure/pipelines/yfinance/lean-data"
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from yfinance_lean.download import download_history, get_exchange_code
from yfinance_lean.transform import (
    transform_daily_bars, transform_factor_file, transform_map_file, transform_forex_bars,
)
from yfinance_lean.publish import (
    publish_daily_bar, publish_factor_file, publish_map_file, publish_forex_bar, LEAN_DATA_ROOT,
)


# Major USD pairs for bare currency codes. JPY/CHF/CAD quote USD as the base.
CURRENCY_TO_PAIR = {
    'EUR': 'EURUSD', 'GBP': 'GBPUSD', 'JPY': 'USDJPY',
    'AUD': 'AUDUSD', 'NZD': 'NZDUSD', 'CAD': 'USDCAD', 'CHF': 'USDCHF',
}

DEFAULT_FX_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY']


def resolve_fx_pair(token):
    """Map a CLI token to a 6-letter LEAN pair. 'GBP' -> 'GBPUSD'; 'EURUSD' -> 'EURUSD'."""
    token = token.upper()
    if token in CURRENCY_TO_PAIR:
        return CURRENCY_TO_PAIR[token]
    if len(token) == 6:
        return token
    raise ValueError(f"Unrecognized FX token {token!r}; use a currency code (GBP) or pair (GBPUSD)")


def run_pipeline(tickers, start, end, output_root=None):
    if output_root:
        # Allow caller to redirect output
        import yfinance_lean.publish as _pub
        _pub.LEAN_DATA_ROOT = output_root
        _pub.DAILY_DIR  = os.path.join(output_root, 'equity', 'usa', 'daily')
        _pub.FACTOR_DIR = os.path.join(output_root, 'equity', 'usa', 'factor_files')
        _pub.MAP_DIR    = os.path.join(output_root, 'equity', 'usa', 'map_files')

    t0 = time.time()
    successes, failures = [], []

    for ticker in tickers:
        print(f"\n=== {ticker} ===")
        try:
            # 1. Download
            df = download_history(ticker, start=start, end=end)
            n_days = len(df)
            span = f"{df.index[0].date()} to {df.index[-1].date()}"
            n_splits = int((df['Stock Splits'] > 0).sum())
            n_divs   = int((df['Dividends']    > 0).sum())
            print(f"  {n_days} trading days ({span}), {n_splits} splits, {n_divs} dividends")

            # 2. Exchange code
            exchange = get_exchange_code(ticker)

            # 3. Transform
            bars_df   = transform_daily_bars(df)
            factor_df = transform_factor_file(df)
            map_df    = transform_map_file(ticker, exchange, df.index[0], df.index[-1])

            # 4. Publish
            zip_path    = publish_daily_bar(ticker, bars_df)
            factor_path = publish_factor_file(ticker, factor_df)
            map_path    = publish_map_file(ticker, map_df)

            print(f"  -> {zip_path}")
            print(f"  -> {factor_path}  ({len(factor_df)} rows)")
            print(f"  -> {map_path}")
            successes.append(ticker)

        except Exception as exc:
            print(f"  ERROR: {exc}")
            failures.append(ticker)

    elapsed = time.time() - t0
    print(f"\n=== Done in {elapsed:.1f}s — {len(successes)} ok, {len(failures)} failed ===")
    if failures:
        print(f"  Failed: {failures}")


def run_forex_pipeline(pairs, start, end, market='oanda', output_root=None):
    if output_root:
        import yfinance_lean.publish as _pub
        _pub.LEAN_DATA_ROOT = output_root

    t0 = time.time()
    successes, failures = [], []

    for pair in pairs:
        print(f"\n=== {pair} ({market}) ===")
        try:
            # Yahoo serves FX pairs via the '=X' suffix (e.g. EURUSD=X).
            df = download_history(f'{pair}=X', start=start, end=end)
            span = f"{df.index[0].date()} to {df.index[-1].date()}"
            print(f"  {len(df)} trading days ({span})")

            bars_df = transform_forex_bars(df)
            zip_path = publish_forex_bar(pair, bars_df, market=market)

            print(f"  -> {zip_path}")
            successes.append(pair)

        except Exception as exc:
            print(f"  ERROR: {exc}")
            failures.append(pair)

    elapsed = time.time() - t0
    print(f"\n=== Done in {elapsed:.1f}s — {len(successes)} ok, {len(failures)} failed ===")
    if failures:
        print(f"  Failed: {failures}")


def main():
    parser = argparse.ArgumentParser(description='yfinance-to-LEAN daily pipeline (equity + forex)')
    parser.add_argument('--asset', choices=['equity', 'forex'], default='equity',
                        help='Asset class to pull (default: equity)')
    parser.add_argument('--tickers', nargs='+', default=None,
                        help='Symbols to convert. Equity: tickers (AAPL SPY). '
                             'Forex: currency codes or pairs (GBP EUR JPY / EURUSD). '
                             'Forex defaults to EURUSD GBPUSD USDJPY if omitted.')
    parser.add_argument('--market', default='oanda',
                        help='Forex market folder under forex/ (default: oanda)')
    parser.add_argument('--start', default='1990-01-01',
                        help='Start date (default: 1990-01-01)')
    parser.add_argument('--end', default=None,
                        help='End date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--output', default=None,
                        help='Override output root directory (default: lean-data/ next to this package)')
    args = parser.parse_args()

    if args.asset == 'forex':
        tokens = args.tickers if args.tickers else DEFAULT_FX_PAIRS
        pairs = [resolve_fx_pair(t) for t in tokens]
        run_forex_pipeline(pairs, args.start, args.end, market=args.market, output_root=args.output)
    else:
        if not args.tickers:
            parser.error('--tickers is required for --asset equity')
        run_pipeline(args.tickers, args.start, args.end, output_root=args.output)


if __name__ == '__main__':
    main()
