---
path: "infrastructure/pipelines/crypto/src/crypto_lean/client.py"
hub: "crypto"
lines: 127
tags:
  - "code/python"
  - "pipelines/crypto"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py"
---
# client.py

`infrastructure/pipelines/crypto/src/crypto_lean/client.py` · hub [[Hubs/Pipelines/crypto|crypto]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py)

## Purpose

Thin ccxt wrapper for pulling OHLCV across Binance, Coinbase, Kraken.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#ccxt|ccxt]], [[Indexes/External packages#dataclasses|dataclasses]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pandas|pandas]], [[Indexes/External packages#tenacity|tenacity]], [[Indexes/External packages#time|time]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/infrastructure/pipelines/crypto/scripts/list_symbols.py|list_symbols.py]], [[Code/infrastructure/pipelines/crypto/src/crypto_lean/__init__.py|__init__.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `DEFAULT_PAIRS` | `['BTC/USD', 'BTC/USDT', 'BTC/USDC', 'ETH/USD', 'ETH/USDT', 'ETH/USDC', 'SOL/USD', 'SOL/USDT', 'SOL/USDC']` | [13](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L13) |
| `EXCHANGE_IDS` | `{'coinbase': 'coinbase', 'kraken': 'kraken'}` | [20](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L20) |
| `REQUEST_PACING` | `{'coinbase': 0.2, 'kraken': 1.1}` | [26](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L26) |

## Classes

### class `ExchangeClient`

[line 33](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L33)

Single-exchange OHLCV fetcher.

- `def __post_init__(self) -> None` — [L40](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L40)
- `def supported_pairs(self, pairs: Iterable[str]) -> list[str]` — [L58](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L58)  
  Filter `pairs` down to the ones this exchange actually lists.
- `def fetch_ohlcv_page(self, symbol: str, timeframe: str, since_ms: int, limit: int=1000) -> list[list]` — [L68](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L68)
- `def fetch_ohlcv(self, symbol: str, timeframe: str='1d', start: pd.Timestamp | None=None, end: pd.Timestamp | None=None) -> pd.DataFrame` — [L79](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/crypto/src/crypto_lean/client.py#L79)  
  Paginated OHLCV fetch. Returns a UTC-indexed DataFrame.

## Source

> [!example]- infrastructure/pipelines/crypto/src/crypto_lean/client.py (127 lines)
> ```python
> """Thin ccxt wrapper for pulling OHLCV across Binance, Coinbase, Kraken."""
> from __future__ import annotations
>
> import os
> import time
> from dataclasses import dataclass
> from typing import Iterable
>
> import ccxt
> import pandas as pd
> from tenacity import retry, stop_after_attempt, wait_exponential
>
> DEFAULT_PAIRS: list[str] = [
>     "BTC/USD", "BTC/USDT", "BTC/USDC",
>     "ETH/USD", "ETH/USDT", "ETH/USDC",
>     "SOL/USD", "SOL/USDT", "SOL/USDC",
> ]
>
> # ccxt exchange IDs per the user-facing names.
> EXCHANGE_IDS: dict[str, str] = {
>     "coinbase": "coinbase",
>     "kraken": "kraken",
> }
>
> # Conservative per-exchange request pacing (seconds between requests).
> REQUEST_PACING: dict[str, float] = {
>     "coinbase": 0.20,
>     "kraken": 1.10,
> }
>
>
> @dataclass
> class ExchangeClient:
>     """Single-exchange OHLCV fetcher."""
>
>     exchange: str
>     api_key: str | None = None
>     api_secret: str | None = None
>
>     def __post_init__(self) -> None:
>         if self.exchange not in EXCHANGE_IDS:
>             raise ValueError(
>                 f"Unknown exchange {self.exchange!r}. "
>                 f"Expected one of: {sorted(EXCHANGE_IDS)}"
>             )
>         ccxt_id = EXCHANGE_IDS[self.exchange]
>         cfg: dict = {"enableRateLimit": True}
>         env_prefix = self.exchange.upper()
>         key = self.api_key or os.getenv(f"{env_prefix}_API_KEY")
>         secret = self.api_secret or os.getenv(f"{env_prefix}_API_SECRET")
>         if key and secret:
>             cfg["apiKey"] = key
>             cfg["secret"] = secret
>         self._client: ccxt.Exchange = getattr(ccxt, ccxt_id)(cfg)
>         self._client.load_markets()
>         self._pacing = REQUEST_PACING.get(self.exchange, 1.0)
>
>     def supported_pairs(self, pairs: Iterable[str]) -> list[str]:
>         """Filter `pairs` down to the ones this exchange actually lists."""
>         listed = set(self._client.symbols or [])
>         return [p for p in pairs if p in listed]
>
>     @retry(
>         stop=stop_after_attempt(5),
>         wait=wait_exponential(multiplier=1, min=2, max=30),
>         reraise=True,
>     )
>     def fetch_ohlcv_page(
>         self,
>         symbol: str,
>         timeframe: str,
>         since_ms: int,
>         limit: int = 1000,
>     ) -> list[list]:
>         time.sleep(self._pacing)
>         return self._client.fetch_ohlcv(symbol, timeframe=timeframe,
>                                         since=since_ms, limit=limit)
>
>     def fetch_ohlcv(
>         self,
>         symbol: str,
>         timeframe: str = "1d",
>         start: pd.Timestamp | None = None,
>         end: pd.Timestamp | None = None,
>     ) -> pd.DataFrame:
>         """Paginated OHLCV fetch. Returns a UTC-indexed DataFrame.
>
>         Columns: open, high, low, close, volume.
>         """
>         if symbol not in (self._client.symbols or []):
>             raise ValueError(f"{self.exchange} does not list {symbol}")
>
>         start = start or pd.Timestamp("2017-01-01", tz="UTC")
>         end = end or pd.Timestamp.utcnow()
>         if start.tz is None:
>             start = start.tz_localize("UTC")
>         if end.tz is None:
>             end = end.tz_localize("UTC")
>
>         timeframe_ms = self._client.parse_timeframe(timeframe) * 1000
>         since_ms = int(start.timestamp() * 1000)
>         end_ms = int(end.timestamp() * 1000)
>         rows: list[list] = []
>
>         while since_ms < end_ms:
>             batch = self.fetch_ohlcv_page(symbol, timeframe, since_ms)
>             if not batch:
>                 break
>             rows.extend(batch)
>             last_ts = batch[-1][0]
>             next_since = last_ts + timeframe_ms
>             if next_since <= since_ms:
>                 break
>             since_ms = next_since
>             if len(batch) < 100:
>                 break
>
>         if not rows:
>             return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
>
>         df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
>         df = df.drop_duplicates(subset="ts").sort_values("ts")
>         df["datetime"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
>         df = df[(df["datetime"] >= start) & (df["datetime"] <= end)]
>         df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]
>         return df
> ```
