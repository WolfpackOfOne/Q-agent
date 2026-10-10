---
path: "infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py"
hub: "news_events_sentiment"
lines: 37
tags:
  - "code/python"
  - "pipelines/news_events_sentiment"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py"
---
# publish.py

`infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py` · hub [[Hubs/Pipelines/news_events_sentiment|news_events_sentiment]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py)

## Purpose

Write news-sentiment alternative data as documented CSVs under lean-data/alternative/.

Not native LEAN price data -- this is a research/alternative-data CSV with a
header and a point-in-time-safe date column, per the "Alternative Data"
convention in infrastructure/pipelines (see docs/pipelines/index.md).

## Dependencies


**Imports (external):** [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/news_events_sentiment/scripts/run_pipeline.py|run_pipeline.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `LEAN_DATA_ROOT` | `os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')` | [12](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py#L12) |
| `SENTIMENT_DIR` | `os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment')` | [13](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py#L13) |
| `FINANCIAL_SENTIMENT_DIR` | `os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment_financial')` | [16](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py#L16) |

## Functions

### `publish_sentiment()`

```python
def publish_sentiment(ticker, df, out_dir=SENTIMENT_DIR)
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py#L19)

Write per-ticker sentiment CSV: date,ticker,avg_tone,volume_pct,tone_z.

### `publish_panel()`

```python
def publish_panel(df, out_dir=SENTIMENT_DIR)
```
[line 29](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py#L29)

Write the combined multi-ticker panel as sentiment_panel.csv.

## Source

> [!example]- infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/publish.py (37 lines)
> ```python
> """Write news-sentiment alternative data as documented CSVs under lean-data/alternative/.
>
> Not native LEAN price data -- this is a research/alternative-data CSV with a
> header and a point-in-time-safe date column, per the "Alternative Data"
> convention in infrastructure/pipelines (see docs/pipelines/index.md).
> """
>
> import os
>
> import pandas as pd
>
> LEAN_DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
> SENTIMENT_DIR = os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment')
> # --financial-only pulls (curated financial-media domain filter) write to a
> # separate directory so they never clobber the general-news pull.
> FINANCIAL_SENTIMENT_DIR = os.path.join(LEAN_DATA_ROOT, 'alternative', 'news_sentiment_financial')
>
>
> def publish_sentiment(ticker, df, out_dir=SENTIMENT_DIR):
>     """Write per-ticker sentiment CSV: date,ticker,avg_tone,volume_pct,tone_z."""
>     os.makedirs(out_dir, exist_ok=True)
>     path = os.path.join(out_dir, f'{ticker.lower()}.csv')
>     out = df.copy()
>     out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
>     out.to_csv(path, index=False)
>     return path
>
>
> def publish_panel(df, out_dir=SENTIMENT_DIR):
>     """Write the combined multi-ticker panel as sentiment_panel.csv."""
>     os.makedirs(out_dir, exist_ok=True)
>     path = os.path.join(out_dir, 'sentiment_panel.csv')
>     out = df.copy()
>     out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
>     out.to_csv(path, index=False)
>     return path
> ```
