"""
One-off refresher for the bundled news-tone sentiment panel.

Run manually whenever the news_events_sentiment pipeline has produced a
fresher cut — the algorithm itself never makes HTTP calls or reads outside
its own `data/` directory.

    cd ~/Documents/Q-agent/MyProjects/NewsSentimentAlpha
    python tools/refresh_sentiment.py

Writes `data/sentiment_panel.csv` with columns: date, ticker, tone_z,
filtered to this project's UNIVERSE and [START_DATE, END_DATE].

Source: infrastructure/pipelines/news_events_sentiment (financial-media-only
GDELT panel, 4-domain restricted). To pull a fresher upstream cut first:

    cd ~/Documents/Q-agent/infrastructure/pipelines/news_events_sentiment
    python scripts/run_pipeline.py --financial-only

Same filter rule as the marimo notebook this strategy is derived from:
infrastructure/marimo/notebooks/news_sentiment_alpha.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))
from domain.config import UNIVERSE, START_DATE, END_DATE, SENTIMENT_PANEL_CSV  # noqa: E402

REPO_ROOT = PROJECT_ROOT.parents[1]
SOURCE_PANEL = (
    REPO_ROOT / "infrastructure" / "pipelines" / "news_events_sentiment"
    / "lean-data" / "alternative" / "news_sentiment_financial" / "sentiment_panel.csv"
)


def refresh() -> pd.DataFrame:
    """Filter the upstream financial-media sentiment panel to this project's scope."""
    if not SOURCE_PANEL.exists():
        raise FileNotFoundError(
            f"Upstream panel not found at {SOURCE_PANEL} — run "
            "`python scripts/run_pipeline.py --financial-only` from "
            "infrastructure/pipelines/news_events_sentiment/ first."
        )

    df = pd.read_csv(SOURCE_PANEL, parse_dates=["date"])
    start = f"{START_DATE[0]:04d}-{START_DATE[1]:02d}-{START_DATE[2]:02d}"
    end = f"{END_DATE[0]:04d}-{END_DATE[1]:02d}-{END_DATE[2]:02d}"
    sub = df[df["ticker"].isin(UNIVERSE) & df["date"].between(start, end)]
    sub = sub.dropna(subset=["tone_z"])[["date", "ticker", "tone_z"]]
    return sub.sort_values(["date", "ticker"]).reset_index(drop=True)


def main() -> int:
    out_path = PROJECT_ROOT / SENTIMENT_PANEL_CSV
    out_path.parent.mkdir(parents=True, exist_ok=True)

    panel = refresh()
    panel.to_csv(out_path, index=False)
    print(f"Wrote {len(panel)} rows to {out_path.relative_to(PROJECT_ROOT)}")
    print(panel["ticker"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
