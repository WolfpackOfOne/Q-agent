"""GDELT news-tone/volume sentiment pipeline.

Usage:
    python scripts/run_pipeline.py                          # full 30-ticker universe, general news
    python scripts/run_pipeline.py --tickers AAPL MSFT
    python scripts/run_pipeline.py --start 2020-01-01 --end 2024-12-31
    python scripts/run_pipeline.py --financial-only --tickers AAPL MSFT   # curated financial-media domains

Output: lean-data/alternative/news_sentiment/<ticker>.csv (+ sentiment_panel.csv)
        lean-data/alternative/news_sentiment_financial/<ticker>.csv (--financial-only)
Source: GDELT DOC 2.0 API (free, no key). Coverage: 2017-01-01 to present.
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from news_events_sentiment_lean.download import (
    build_query, fetch_tone, fetch_volume, GDELT_ARCHIVE_START, FINANCIAL_DOMAINS,
)
from news_events_sentiment_lean.transform import transform_sentiment
from news_events_sentiment_lean.publish import (
    publish_sentiment, publish_panel, SENTIMENT_DIR, FINANCIAL_SENTIMENT_DIR,
)
from news_events_sentiment_lean.symbols import COMPANY_NAMES, UNIVERSE

# GDELT is a free public service with no documented per-key rate limit -- keep
# concurrency modest so this stays a good citizen of the API. Domain-filtered
# (--financial-only) queries are measurably more expensive server-side (~50s for
# a 3-month/4-domain window vs. ~1-2s unfiltered over 5 years in testing), so
# they run strictly sequentially with a longer timeout and a pause between
# tickers instead of thread-pool concurrency.
MAX_WORKERS = 2
FINANCIAL_TIMEOUT = 240
FINANCIAL_PAUSE_SECONDS = 15


def _fetch_one(tk, company, start, end, domains=None, timeout=60, retries=3):
    query = build_query(company, domains)
    tone_pts = fetch_tone(query, start, end, timeout=timeout, retries=retries)
    volume_pts = fetch_volume(query, start, end, timeout=timeout, retries=retries)
    return transform_sentiment(tk, tone_pts, volume_pts)


def run_pipeline(tickers, start, end, financial_only=False):
    t0 = time.time()
    panels = []
    ok, failed = [], []

    out_dir = FINANCIAL_SENTIMENT_DIR if financial_only else SENTIMENT_DIR
    domains = FINANCIAL_DOMAINS if financial_only else None

    valid = [(tk, COMPANY_NAMES[tk]) for tk in tickers if tk in COMPANY_NAMES]
    for tk in tickers:
        if tk not in COMPANY_NAMES:
            print(f"  {tk}: no company-name mapping, skipping")
            failed.append(tk)

    def _handle_result(tk, company, df):
        if df.empty:
            print(f"  {tk} ({company}): no data returned")
            failed.append(tk)
            return
        path = publish_sentiment(tk, df, out_dir=out_dir)
        panels.append(df)
        print(f"  {tk} ({company}): {len(df)} days -> {os.path.basename(path)}")
        ok.append(tk)

    if financial_only:
        print(f"Financial-only mode: domains={FINANCIAL_DOMAINS}, sequential, timeout={FINANCIAL_TIMEOUT}s")
        for tk, company in valid:
            try:
                df = _fetch_one(tk, company, start, end, domains=domains, timeout=FINANCIAL_TIMEOUT, retries=2)
                _handle_result(tk, company, df)
            except Exception as exc:
                print(f"  {tk} ({company}): FAILED -- {exc}")
                failed.append(tk)
            time.sleep(FINANCIAL_PAUSE_SECONDS)
    else:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(_fetch_one, tk, company, start, end): (tk, company)
                for tk, company in valid
            }
            for future in as_completed(futures):
                tk, company = futures[future]
                try:
                    df = future.result()
                    _handle_result(tk, company, df)
                except Exception as exc:
                    print(f"  {tk} ({company}): FAILED -- {exc}")
                    failed.append(tk)

    if panels:
        combined = pd.concat(panels, ignore_index=True)
        panel_path = publish_panel(combined, out_dir=out_dir)
        print(f"\nCombined panel -> {panel_path} ({len(combined)} rows)")

    print(f"\n=== Done in {time.time() - t0:.1f}s -- {len(ok)} ok, {len(failed)} failed ===")
    if failed:
        print(f"Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(description="GDELT news-tone/volume sentiment pipeline")
    parser.add_argument("--tickers", nargs="+", default=UNIVERSE)
    parser.add_argument("--start", default=GDELT_ARCHIVE_START)
    parser.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    parser.add_argument(
        "--financial-only", action="store_true",
        help=f"Restrict to curated financial-media domains: {FINANCIAL_DOMAINS}. "
             "Slower and sequential; writes to a separate output directory.",
    )
    args = parser.parse_args()

    run_pipeline(args.tickers, args.start, args.end, financial_only=args.financial_only)


if __name__ == "__main__":
    main()
