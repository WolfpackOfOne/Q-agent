---
path: "infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py"
hub: "news_events_sentiment"
lines: 62
tags:
  - "code/python"
  - "pipelines/news_events_sentiment"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py"
---
# download.py

`infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py` · hub [[Hubs/Pipelines/news_events_sentiment|news_events_sentiment]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py)

## Purpose

Fetch daily news tone and volume timelines from the GDELT DOC 2.0 API.

Free, no API key. Coverage: 2017-01-01 to present (GDELT's full-text news
archive start date). Query is free-text (company name), not a structured
ticker lookup, so results can include false positives from unrelated
entities that share a name fragment -- spot-check a ticker's output before
trusting it at face value.

## Dependencies


**Imports (external):** [[Indexes/External packages#requests|requests]], [[Indexes/External packages#time|time]]

**Imported by:** [[Code/infrastructure/pipelines/news_events_sentiment/scripts/run_pipeline.py|run_pipeline.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `BASE_URL` | `'https://api.gdeltproject.org/api/v2/doc/doc'` | [14](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L14) |
| `GDELT_ARCHIVE_START` | `'2017-01-01'` | [15](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L15) |
| `FINANCIAL_DOMAINS` | `['reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com']` | [21](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L21) |

## Functions

### `build_query()`

```python
def build_query(company, domains=None)
```
[line 24](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L24)

Build a GDELT query string, optionally restricted to a domain allowlist.

### `_timeline()`

```python
def _timeline(query, start, end, mode, timeout=60, retries=3)
```
[line 32](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L32)

### `fetch_tone()`

```python
def fetch_tone(query, start, end, timeout=60, retries=3)
```
[line 54](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L54)

Return [{date, value}] -- daily average article tone (roughly -10..+10).

### `fetch_volume()`

```python
def fetch_volume(query, start, end, timeout=60, retries=3)
```
[line 59](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py#L59)

Return [{date, value}] -- daily share (%) of global monitored news mentioning query.

## Source

> [!example]- infrastructure/pipelines/news_events_sentiment/src/news_events_sentiment_lean/download.py (62 lines)
> ```python
> """Fetch daily news tone and volume timelines from the GDELT DOC 2.0 API.
>
> Free, no API key. Coverage: 2017-01-01 to present (GDELT's full-text news
> archive start date). Query is free-text (company name), not a structured
> ticker lookup, so results can include false positives from unrelated
> entities that share a name fragment -- spot-check a ticker's output before
> trusting it at face value.
> """
>
> import time
>
> import requests
>
> BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
> GDELT_ARCHIVE_START = "2017-01-01"
>
> # Curated financial-media outlets for the --financial-only query mode. Kept short
> # (4 domains) deliberately: each additional domainis: clause measurably slows the
> # GDELT query -- 4 domains already took ~50s for a 3-month window in testing, vs.
> # ~1-2s for an unfiltered company-name query over 5 years.
> FINANCIAL_DOMAINS = ["reuters.com", "bloomberg.com", "cnbc.com", "wsj.com"]
>
>
> def build_query(company, domains=None):
>     """Build a GDELT query string, optionally restricted to a domain allowlist."""
>     if not domains:
>         return company
>     clause = " OR ".join(f"domainis:{d}" for d in domains)
>     return f"{company} ({clause})"
>
>
> def _timeline(query, start, end, mode, timeout=60, retries=3):
>     params = {
>         "query": query,
>         "mode": mode,
>         "format": "json",
>         "startdatetime": f"{start.replace('-', '')}000000",
>         "enddatetime": f"{end.replace('-', '')}000000",
>     }
>     last_exc = None
>     for attempt in range(retries):
>         try:
>             resp = requests.get(BASE_URL, params=params, timeout=timeout)
>             resp.raise_for_status()
>             payload = resp.json()
>             series = payload.get("timeline", [])
>             return series[0]["data"] if series else []
>         except (requests.RequestException, ValueError) as exc:
>             last_exc = exc
>             time.sleep(2 * (attempt + 1))
>     raise RuntimeError(f"GDELT request failed after {retries} attempts: {last_exc}")
>
>
> def fetch_tone(query, start, end, timeout=60, retries=3):
>     """Return [{date, value}] -- daily average article tone (roughly -10..+10)."""
>     return _timeline(query, start, end, mode="timelinetone", timeout=timeout, retries=retries)
>
>
> def fetch_volume(query, start, end, timeout=60, retries=3):
>     """Return [{date, value}] -- daily share (%) of global monitored news mentioning query."""
>     return _timeline(query, start, end, mode="timelinevol", timeout=timeout, retries=retries)
> ```
