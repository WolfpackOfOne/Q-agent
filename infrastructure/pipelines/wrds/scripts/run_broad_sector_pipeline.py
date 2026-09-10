"""Point-in-time GICS classification for the broad universe.

Reads the gvkey/permno pairs from the broad quarterly-fundamentals extract, pulls
each company's GICS classification *history* from ``comp.co_hgic``, and publishes
a map that can be joined as-of any date.

Unlike ``run_sector_pipeline.py`` — which pulls the current classification for the
30-stock universe keyed on ticker — this keys on gvkey/permno and carries validity
windows, so a 2010 backtest sees a company's 2010 sector rather than today's.

Usage:
    export WRDS_USERNAME=<your-wrds-username>
    python scripts/run_broad_sector_pipeline.py
    python scripts/run_broad_sector_pipeline.py --profile <named-profile>
"""

import argparse
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wrds_lean.connection import close_connection, get_connection, set_connection_profile
from wrds_lean.sectors import (
    build_pit_sector_map,
    extract_historical_gics,
    publish_pit_sector_map,
)

LEAN_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lean-data'))
FUND_CSV = os.path.join(LEAN_DATA, 'alternative', 'fundamentals', 'broad_quarterly_fundamentals.csv')


def main():
    parser = argparse.ArgumentParser(description='Point-in-time GICS map for the broad universe')
    parser.add_argument('--profile', default=None, help='Named WRDS profile from .wrds_profiles.json')
    parser.add_argument('--fundamentals', default=FUND_CSV,
                        help='Broad quarterly fundamentals CSV providing gvkey/permno pairs')
    args = parser.parse_args()

    set_connection_profile(args.profile)
    t0 = time.time()

    if not os.path.exists(args.fundamentals):
        print(f"ERROR: {args.fundamentals} not found — run run_broad_quarterly_pipeline.py first.")
        sys.exit(1)

    fund = pd.read_csv(args.fundamentals, usecols=['gvkey', 'permno', 'Ticker'])
    pairs = fund.drop_duplicates(['gvkey', 'permno'])[['gvkey', 'permno', 'Ticker']]
    pairs['gvkey'] = pairs['gvkey'].astype(str).str.zfill(6)
    gvkeys = sorted(pairs['gvkey'].unique())
    print(f"{len(gvkeys):,} gvkeys / {pairs['permno'].nunique():,} permnos from {os.path.basename(args.fundamentals)}")

    print("\nPulling GICS history from comp.co_hgic ...")
    hist = extract_historical_gics(gvkeys)
    print(f"  {len(hist):,} classification periods for {hist['gvkey'].nunique():,} gvkeys "
          f"({hist['gvkey'].nunique()/len(gvkeys):.1%} of the universe)")

    conn = get_connection()
    company = conn.raw_sql(
        "SELECT gvkey, conm, sic FROM comp.company WHERE gvkey IN %(g)s",
        params={'g': tuple(gvkeys)},
    )

    sector_map = build_pit_sector_map(hist, pairs, company_df=company)
    path = publish_pit_sector_map(sector_map, LEAN_DATA)

    n_multi = (sector_map.groupby('permno').size() > 1).sum()
    print(f"\n  {len(sector_map):,} rows covering {sector_map['permno'].nunique():,} permnos")
    print(f"  {n_multi:,} permnos were reclassified at least once — point-in-time joins matter for these")
    print(f"  sectors present: {sector_map['MorningstarSectorName'].nunique()}")
    print(sector_map['MorningstarSectorName'].value_counts().to_string())
    print(f"\n  written to {path}")
    print(f"Done in {time.time() - t0:.0f}s")
    close_connection()


if __name__ == '__main__':
    main()
