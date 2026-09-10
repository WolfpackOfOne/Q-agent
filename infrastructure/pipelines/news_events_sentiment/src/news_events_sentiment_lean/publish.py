"""Write news-sentiment alternative data as documented CSVs under lean-data/alternative/.

Not native LEAN price data -- this is a research/alternative-data CSV with a
header and a point-in-time-safe date column, per the "Alternative Data"
convention in infrastructure/pipelines (see docs/pipelines/index.md).
"""

import os

import pandas as pd

LEAN_DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
SENTIMENT_DIR = os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment')
# --financial-only pulls (curated financial-media domain filter) write to a
# separate directory so they never clobber the general-news pull.
FINANCIAL_SENTIMENT_DIR = os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment_financial')


def publish_sentiment(ticker, df, out_dir=SENTIMENT_DIR):
    """Write per-ticker sentiment CSV: date,ticker,avg_tone,volume_pct,tone_z."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'{ticker.lower()}.csv')
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    return path


def publish_panel(df, out_dir=SENTIMENT_DIR):
    """Write the combined multi-ticker panel as sentiment_panel.csv."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'sentiment_panel.csv')
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    return path
