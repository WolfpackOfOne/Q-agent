"""Broad quarterly-fundamentals pipeline: every US company above a market-cap
floor, linked to CRSP through the CCM link table, plus daily prices for a
point-in-time top-N universe.

Three phases:

  1. comp.fundq for all USD-reporting companies with quarter-end market cap
     >= --min-mktcap ($M), joined to PERMNO via crsp_a_ccm.ccmxpf_lnkhist.
     -> lean-data/alternative/fundamentals/broad_quarterly_fundamentals.csv

  2. A point-in-time universe: at each calendar quarter-end, the --top-n
     largest companies by the most recently *reported* market cap (only
     filings whose rdq is already public). No survivorship bias — membership
     is decided with information available on the date.
     -> lean-data/alternative/fundamentals/broad_universe.csv

  3. CRSP daily prices for every PERMNO that was ever in that universe, in
     batches, published as LEAN daily zips + factor files + map files, plus
     a compact month-end total-return index for research.
     -> lean-data/equity/usa/{daily,factor_files,map_files}/{lean_ticker}.*
     -> lean-data/alternative/fundamentals/broad_permno_map.csv
     -> lean-data/alternative/fundamentals/broad_monthly_tri.csv

LEAN zips are named by ticker, and CRSP tickers are reused across companies
over time, so every PERMNO gets a unique ``lean_ticker`` (its latest CRSP
ticker; ``{ticker}{permno}`` on collision). Research code should key on
PERMNO and translate through broad_permno_map.csv.

Usage:
    export WRDS_USERNAME=<your-wrds-username>
    caffeinate -dims python scripts/run_broad_quarterly_pipeline.py
    python scripts/run_broad_quarterly_pipeline.py --fundamentals-only
    python scripts/run_broad_quarterly_pipeline.py --top-n 500 --min-mktcap 2000
"""

import argparse
import os
import re
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wrds_lean.connection import close_connection, set_connection_profile
from wrds_lean.extract import extract_daily_prices, extract_distributions, extract_name_history
from wrds_lean.publish import publish_daily_bar, publish_factor_file, publish_map_file
from wrds_lean.quarterly_fundamentals import (
    extract_all_quarterly_fundamentals,
    publish_quarterly_fundamentals,
    tidy_quarterly_fundamentals,
)
from wrds_lean.transform import transform_daily_bars, transform_factor_file, transform_map_file

LEAN_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lean-data'))
FUND_DIR = os.path.join(LEAN_DATA, 'alternative', 'fundamentals')
BATCH_SIZE = 500
STALE_DAYS = 200   # a filing older than this at the quarter-end no longer defines membership


def build_universe(fund, start, end, top_n):
    """Point-in-time top-N by reported market cap at each calendar quarter-end."""
    f = fund[['permno', 'gvkey', 'Ticker', 'AvailableDate', 'FiscalQuarterEnd', 'prccq', 'cshoq']].copy()
    f['mktcap'] = f['prccq'] * f['cshoq']
    f = f.dropna(subset=['mktcap']).sort_values('AvailableDate')
    rows = []
    for q in pd.date_range(start, end, freq='QE'):
        sub = f[(f['AvailableDate'] <= q) & (f['FiscalQuarterEnd'] >= q - pd.DateOffset(days=STALE_DAYS))]
        latest = sub.drop_duplicates('permno', keep='last')
        top = latest.nlargest(top_n, 'mktcap').copy()
        top['quarter_end'] = q
        top['rank'] = np.arange(1, len(top) + 1)
        rows.append(top[['quarter_end', 'permno', 'gvkey', 'Ticker', 'mktcap', 'rank']])
    return pd.concat(rows, ignore_index=True)


def lean_ticker_map(names_df, comp_ticker):
    """One unique, alphanumeric LEAN ticker per PERMNO."""
    names_df = names_df.copy()
    names_df['permno'] = names_df['permno'].astype(int)
    latest = (names_df.sort_values(['permno', 'namedt'])
                      .drop_duplicates('permno', keep='last')
                      .set_index('permno')['ticker'])
    out = {}
    for permno in names_df['permno'].unique():
        t = latest.get(permno)
        if not isinstance(t, str) or not t.strip():
            t = comp_ticker.get(permno, '')
        t = re.sub(r'[^A-Za-z0-9]', '', str(t)).upper() or f'P{permno}'
        out[int(permno)] = t
    seen = {}
    for permno, t in out.items():
        seen.setdefault(t, []).append(permno)
    for t, permnos in seen.items():
        if len(permnos) > 1:
            for permno in permnos:
                out[permno] = f'{t}{permno}'
    return out


def monthly_tri(prices_df):
    """Month-end total-return index per PERMNO from CRSP daily ``ret`` (dividends included)."""
    p = prices_df[['permno', 'date', 'ret', 'prc']].copy()
    p['date'] = pd.to_datetime(p['date'])
    p['ret'] = pd.to_numeric(p['ret'], errors='coerce').fillna(0.0)
    p = p.sort_values(['permno', 'date'])
    p['tri'] = (1.0 + p['ret']).groupby(p['permno']).cumprod()
    p['prc'] = p['prc'].abs()
    p['month'] = p['date'].dt.to_period('M')
    m = p.groupby(['permno', 'month']).tail(1)
    return m[['permno', 'date', 'tri', 'prc']].rename(columns={'prc': 'raw_close'})


def pull_prices(permnos, permno_to_ticker, start, end):
    """One CRSP batch -> LEAN zips / factor files / map files. Returns (published, monthly_tri_df)."""
    prices_df = extract_daily_prices(permnos, start, end)
    if prices_df.empty:
        return 0, pd.DataFrame()
    dist_df = extract_distributions(permnos)
    names_df = extract_name_history(permnos)
    bars = transform_daily_bars(prices_df, permno_to_ticker)
    ticker_to_permno = {t.lower(): p for p, t in permno_to_ticker.items()}
    published = 0
    for ticker_lower, bars_df in bars.items():
        permno = ticker_to_permno.get(ticker_lower)
        if permno is None:
            continue
        publish_daily_bar(ticker_lower, bars_df)
        publish_factor_file(ticker_lower, transform_factor_file(prices_df, dist_df, permno))
        publish_map_file(ticker_lower, transform_map_file(names_df, permno, ticker_lower.upper()))
        published += 1
    return published, monthly_tri(prices_df)


def main():
    parser = argparse.ArgumentParser(description='Broad quarterly fundamentals + point-in-time top-N universe')
    parser.add_argument('--profile', default=None, help='Named WRDS profile from .wrds_profiles.json')
    parser.add_argument('--start-year', type=int, default=2003, help='First fiscal year of fundamentals (default 2003)')
    parser.add_argument('--min-mktcap', type=float, default=1000.0, help='Market-cap floor in $M for the extract (default 1000)')
    parser.add_argument('--top-n', type=int, default=1000, help='Universe size at each quarter-end (default 1000)')
    parser.add_argument('--start', default='2004-01-01', help='First universe quarter-end')
    parser.add_argument('--end', default='2024-12-31', help='Last universe quarter-end / price end date')
    parser.add_argument('--price-start', default='1998-01-01',
                        help='Price history start (default 1998-01-01, same as the 30-stock pipeline, so '
                             'existing zips are regenerated as identical supersets rather than truncated)')
    parser.add_argument('--fundamentals-only', action='store_true', help='Phases 1-2 only; skip the CRSP price pull')
    args = parser.parse_args()

    set_connection_profile(args.profile)
    os.makedirs(FUND_DIR, exist_ok=True)
    t0 = time.time()

    print('=' * 70)
    print(f'PHASE 1: comp.fundq, fiscal {args.start_year}+, mktcap >= ${args.min_mktcap:,.0f}M, CCM-linked')
    print('=' * 70)
    raw = extract_all_quarterly_fundamentals(start_year=args.start_year, min_mktcap_musd=args.min_mktcap)
    print(f'  {len(raw):,} rows, {raw["gvkey"].nunique():,} gvkeys, {raw["permno"].nunique():,} permnos  ({time.time() - t0:.0f}s)')
    fund = tidy_quarterly_fundamentals(raw, key='gvkey')
    path = publish_quarterly_fundamentals(fund, LEAN_DATA, filename='broad_quarterly_fundamentals.csv')
    print(f'  {len(fund):,} rows after de-dup -> {path}')

    print('\n' + '=' * 70)
    print(f'PHASE 2: point-in-time top-{args.top_n} universe, {args.start} -> {args.end}')
    print('=' * 70)
    universe = build_universe(fund, args.start, args.end, args.top_n)
    upath = os.path.join(FUND_DIR, 'broad_universe.csv')
    universe.to_csv(upath, index=False, date_format='%Y-%m-%d')
    per_q = universe.groupby('quarter_end')['permno'].count()
    print(f'  {universe["quarter_end"].nunique()} quarter-ends, {per_q.min()}-{per_q.max()} names each, '
          f'{universe["permno"].nunique():,} distinct permnos ever -> {upath}')

    if args.fundamentals_only:
        close_connection()
        print(f'\nDone (fundamentals only) in {(time.time() - t0) / 60:.1f} min')
        return

    print('\n' + '=' * 70)
    print('PHASE 3: CRSP daily prices for every universe member, in batches')
    print('=' * 70)
    permnos = sorted(universe['permno'].unique().tolist())
    names_all = extract_name_history(permnos)
    comp_ticker = (fund.sort_values('AvailableDate').drop_duplicates('permno', keep='last')
                       .set_index('permno')['Ticker'].to_dict())
    p2t = lean_ticker_map(names_all, comp_ticker)
    for permno in permnos:                      # permnos with no CRSP name row at all
        p2t.setdefault(permno, comp_ticker.get(permno) or f'P{permno}')
    mpath = os.path.join(FUND_DIR, 'broad_permno_map.csv')
    pd.DataFrame({'permno': list(p2t), 'lean_ticker': list(p2t.values())}).assign(
        comp_ticker=lambda d: d['permno'].map(comp_ticker)).to_csv(mpath, index=False)
    print(f'  {len(p2t):,} permno -> lean_ticker rows -> {mpath}')

    total, tri_parts = 0, []
    n_batches = (len(permnos) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(permnos), BATCH_SIZE):
        batch = permnos[i:i + BATCH_SIZE]
        tb = time.time()
        try:
            n, tri = pull_prices(batch, {p: p2t[p] for p in batch}, args.price_start, args.end)
        except Exception as e:                  # keep going; report at the end
            print(f'  batch {i // BATCH_SIZE + 1}/{n_batches}: ERROR {e}')
            continue
        total += n
        tri_parts.append(tri)
        print(f'  batch {i // BATCH_SIZE + 1}/{n_batches}: {n} tickers published ({time.time() - tb:.0f}s)')

    tri_all = pd.concat(tri_parts, ignore_index=True) if tri_parts else pd.DataFrame()
    tpath = os.path.join(FUND_DIR, 'broad_monthly_tri.csv')
    tri_all.to_csv(tpath, index=False, date_format='%Y-%m-%d')
    print(f'\n  {total:,} tickers published; monthly TRI {len(tri_all):,} rows -> {tpath}')
    print(f'Done in {(time.time() - t0) / 60:.1f} min')
    close_connection()


if __name__ == '__main__':
    main()
