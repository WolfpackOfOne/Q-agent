# News Events & Sentiment Pipeline (GDELT)

Pulls daily news-tone and news-volume timelines from the [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) and writes them as alternative-data CSVs for research notebooks and LEAN custom readers.

## What it produces

| Output | Source | Coverage |
|---|---|---|
| Daily average news tone per ticker | GDELT DOC 2.0 API, `mode=timelinetone` | 2017-01-01 to present |
| Daily news-volume intensity per ticker | GDELT DOC 2.0 API, `mode=timelinevol` | 2017-01-01 to present |
| 90-day rolling tone z-score | Derived | Same as above, first ~20 days per ticker are `NaN` (warm-up) |

No API key or account required. GDELT's DOC 2.0 API is free and rate-limit-friendly but not officially documented as unlimited — this pipeline caps concurrency at 5 workers (`MAX_WORKERS` in `scripts/run_pipeline.py`) to stay a good citizen.

## Quick start

```bash
cd infrastructure/pipelines/news_events_sentiment
python3 -m venv venv && source venv/bin/activate
pip install -e .

python scripts/run_pipeline.py                          # full 30-ticker universe, 2017-present
python scripts/run_pipeline.py --tickers AAPL MSFT       # specific tickers
python scripts/run_pipeline.py --start 2020-01-01 --end 2024-12-31
```

## Universe

Ticker → company-name mapping in `src/news_events_sentiment_lean/symbols.py` mirrors the WRDS 30-stock equity universe (`infrastructure/pipelines/wrds/src/wrds_lean/symbols.py`), so sentiment data lines up with an existing price universe out of the box.

## Output format

`lean-data/alternative/news_sentiment/<ticker>.csv` (header row, point-in-time date column):

```
date,ticker,avg_tone,volume_pct,tone_z
2024-01-01,AAPL,0.9127,0.009,0.4123
```

- `avg_tone`: GDELT's average article tone for that day's coverage, roughly on a -10..+10 scale. Positive = more positive language.
- `volume_pct`: share (%) of all monitored global news that day mentioning the query.
- `tone_z`: `avg_tone` z-scored against a trailing 90-day window (`min_periods=20`) — a ticker- and regime-relative "surprise" measure, since raw tone has ticker-specific baselines that aren't comparable across names.

`lean-data/alternative/news_sentiment/sentiment_panel.csv` is the same schema with every pulled ticker concatenated — the convenient entry point for a research notebook.

Per the workspace's [alternative-data convention](../../../docs/pipelines/index.md), this is **not native LEAN price data** — a custom `PythonData` reader is needed to use it directly inside a LEAN algorithm.

## Known limitations

- **Free-text query, not entity resolution.** GDELT matches the company-name string across global news; a generic name (e.g. a ticker whose company name overlaps a common phrase) can pick up false-positive mentions. Spot-check any ticker before trusting it.
- **No look-ahead by construction**, but GDELT aggregates by article *publish* date in UTC, which can straddle the US trading day (e.g. a 4pm ET earnings release publishes as the next UTC day). Treat same-day tone as same-day-or-next-session information, not intraday-precise.
- **Coverage starts 2017-01-01.** GDELT's DOC 2.0 full-text archive doesn't go earlier; the older GDELT 1.0 GKG format is out of scope here.
- **Two API calls per ticker** (tone + volume), each covering the full requested date range in one request (tested up to 5 years / 1,825 daily points with no truncation). Requests are slow (~1-2 min per ticker observed) — this is GDELT-side latency, not something the pipeline controls.
- **`tone_z` needs 20 warm-up days** per ticker before it's non-`NaN` (rolling window `min_periods=20`).
