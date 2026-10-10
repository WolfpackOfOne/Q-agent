---
path: "infrastructure/pipelines/wrds/src/wrds_lean/transform.py"
hub: "wrds"
lines: 337
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py"
---
# transform.py

`infrastructure/pipelines/wrds/src/wrds_lean/transform.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py)

## Purpose

Transform CRSP data into LEAN format (daily bars, factor files, map files).

## Dependencies


**Imports (external):** [[Indexes/External packages#numpy|numpy]], [[Indexes/External packages#pandas|pandas]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py|run_broad_quarterly_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py|run_pipeline.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `EXCHANGE_MAP` | `{'N': 'N', 'A': 'A', 'Q': 'Q', 'P': 'P'}` | [288](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py#L288) |

## Functions

### `transform_daily_bars()`

```python
def transform_daily_bars(prices_df, permno_to_ticker)
```
[line 11](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py#L11)

Convert CRSP daily prices to LEAN daily bar format.

Args:
    prices_df: DataFrame from extract_daily_prices()
    permno_to_ticker: dict mapping permno -> ticker (lowercase)

Returns:
    dict of {ticker: DataFrame} where DataFrame has columns:
        date_str, open, high, low, close, volume
    Ready to write as CSV (no header).

### `transform_factor_file()`

```python
def transform_factor_file(prices_df, dist_df, permno)
```
[line 76](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py#L76)

Build a LEAN factor file from CRSP cumulative adjustment factors and dividends.

LEAN factor file format (no header):
    Date,PriceFactor,SplitFactor,ReferencePrice

- SplitFactor: derived from cfacshr. Normalized so current = 1.0.
  SplitFactor(date) = cfacshr(date) / cfacshr(latest)
- PriceFactor: accounts for cash dividends. For each ex-date with a cash
  dividend (distcd 12xx), PriceFactor adjusts by (1 - divamt/price_before_ex).
  Cumulative product working backwards from 1.0.
- ReferencePrice: closing price on the day before the ex-date.
- Sentinel row: 20501231,1,1,0

Returns DataFrame ready to write as CSV (no header).

### `_sentinel_only()`

```python
def _sentinel_only()
```
[line 275](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py#L275)

### `transform_map_file()`

```python
def transform_map_file(names_df, permno, current_ticker)
```
[line 296](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/transform.py#L296)

Build a LEAN map file from CRSP name history.

LEAN map file format (no header):
    Date,MappedSymbol,PrimaryExchange

One row per name period. Sentinel row at end: 20501231,ticker,exchange

Returns DataFrame ready to write as CSV (no header).

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/transform.py (337 lines)
> ```python
> """Transform CRSP data into LEAN format (daily bars, factor files, map files)."""
>
> import pandas as pd
> import numpy as np
>
>
> # ---------------------------------------------------------------------------
> # Daily bars
> # ---------------------------------------------------------------------------
>
> def transform_daily_bars(prices_df, permno_to_ticker):
>     """Convert CRSP daily prices to LEAN daily bar format.
>
>     Args:
>         prices_df: DataFrame from extract_daily_prices()
>         permno_to_ticker: dict mapping permno -> ticker (lowercase)
>
>     Returns:
>         dict of {ticker: DataFrame} where DataFrame has columns:
>             date_str, open, high, low, close, volume
>         Ready to write as CSV (no header).
>     """
>     result = {}
>     for permno, ticker in permno_to_ticker.items():
>         df = prices_df[prices_df['permno'] == permno].copy()
>         if df.empty:
>             print(f"  WARNING: No price data for {ticker} (permno={permno})")
>             continue
>
>         df = df.sort_values('date').reset_index(drop=True)
>
>         # Close: abs(prc) — negative prc in CRSP means bid/ask midpoint
>         close = df['prc'].abs()
>
>         # Drop rows where close is missing (no usable price)
>         valid = close.notna()
>         if valid.sum() == 0:
>             print(f"  WARNING: No valid prices for {ticker} (permno={permno})")
>             continue
>         df = df[valid].reset_index(drop=True)
>         close = close[valid].reset_index(drop=True)
>
>         # Open: openprc, fallback to close
>         open_ = df['openprc'].copy()
>         open_ = open_.where(open_.notna() & (open_ > 0), close)
>
>         # High: askhi proxy, fallback to close, clamp >= max(open, close)
>         high = df['askhi'].copy()
>         high = high.where(high.notna() & (high > 0), close)
>         high = high.clip(lower=pd.concat([open_, close], axis=1).max(axis=1))
>
>         # Low: bidlo proxy, fallback to close, clamp <= min(open, close)
>         low = df['bidlo'].copy()
>         low = low.where(low.notna() & (low > 0), close)
>         low = low.clip(upper=pd.concat([open_, close], axis=1).min(axis=1))
>
>         # Scale to deci-cents (multiply by 10000, round to int)
>         bars = pd.DataFrame({
>             'date_str': df['date'].dt.strftime('%Y%m%d') + ' 00:00',
>             'open': (open_ * 10000).round().astype(int),
>             'high': (high * 10000).round().astype(int),
>             'low': (low * 10000).round().astype(int),
>             'close': (close * 10000).round().astype(int),
>             'volume': df['vol'].fillna(0).astype(int),
>         })
>
>         result[ticker.lower()] = bars
>
>     return result
>
>
> # ---------------------------------------------------------------------------
> # Factor files
> # ---------------------------------------------------------------------------
>
> def transform_factor_file(prices_df, dist_df, permno):
>     """Build a LEAN factor file from CRSP cumulative adjustment factors and dividends.
>
>     LEAN factor file format (no header):
>         Date,PriceFactor,SplitFactor,ReferencePrice
>
>     - SplitFactor: derived from cfacshr. Normalized so current = 1.0.
>       SplitFactor(date) = cfacshr(date) / cfacshr(latest)
>     - PriceFactor: accounts for cash dividends. For each ex-date with a cash
>       dividend (distcd 12xx), PriceFactor adjusts by (1 - divamt/price_before_ex).
>       Cumulative product working backwards from 1.0.
>     - ReferencePrice: closing price on the day before the ex-date.
>     - Sentinel row: 20501231,1,1,0
>
>     Returns DataFrame ready to write as CSV (no header).
>     """
>     pdf = prices_df[prices_df['permno'] == permno].copy()
>     pdf = pdf.sort_values('date').reset_index(drop=True)
>     pdf['close'] = pdf['prc'].abs()
>
>     # Drop rows with missing price or zero/missing adjustment factors
>     pdf = pdf.dropna(subset=['prc']).reset_index(drop=True)
>     pdf['close'] = pdf['close'].astype(float)
>     pdf['cfacshr'] = pd.to_numeric(pdf['cfacshr'], errors='coerce').astype(float)
>     pdf = pdf[(pdf['cfacshr'].notna()) & (pdf['cfacshr'] != 0)].reset_index(drop=True)
>
>     if pdf.empty:
>         return _sentinel_only()
>
>     # --- Split factor from cfacshr ---
>     # cfacshr is the cumulative shares adjustment factor.
>     # LEAN SplitFactor = latest_cfacshr / cfacshr(date), so that historical
>     # prices are deflated by <1 and the current date is 1.0.
>     # e.g. AAPL 1998 cfacshr=112, latest=1 → SplitFactor = 1/112 = 0.00892857
>     latest_cfacshr = pdf['cfacshr'].iloc[-1]
>     if pd.isna(latest_cfacshr) or latest_cfacshr == 0:
>         latest_cfacshr = 1.0
>
>     # --- Cash dividends from dsedist ---
>     # distcd 12xx = cash dividends on common stock
>     ddf = dist_df[dist_df['permno'] == permno].copy()
>     ddf = ddf.dropna(subset=['distcd', 'exdt', 'divamt'])
>     cash_divs = ddf[ddf['distcd'].astype(str).str.startswith('12')].copy()
>     cash_divs = cash_divs.sort_values('exdt').reset_index(drop=True)
>     cash_divs['divamt'] = cash_divs['divamt'].astype(float)
>
>     # --- Split events: detect changes in cfacshr ---
>     pdf['cfacshr_prev'] = pdf['cfacshr'].shift(1)
>     split_changes = pdf[
>         (pdf['cfacshr'] != pdf['cfacshr_prev']) & pdf['cfacshr_prev'].notna()
>     ].copy()
>
>     # Build event rows
>     rows = []
>
>     # Add split change events
>     for _, row in split_changes.iterrows():
>         split_factor = float(latest_cfacshr / row['cfacshr'])
>         # Get the price before this date for reference
>         prev_rows = pdf[pdf['date'] < row['date']]
>         ref_price = float(prev_rows['close'].iloc[-1] if len(prev_rows) > 0 else row['close'])
>         rows.append({
>             'date': row['date'],
>             'split_factor': split_factor,
>             'ref_price': ref_price,
>             'is_div': False,
>         })
>
>     # Add dividend events
>     for _, div_row in cash_divs.iterrows():
>         ex_date = div_row['exdt']
>         divamt = div_row['divamt']
>
>         # Find price on the day before ex-date
>         prev_rows = pdf[pdf['date'] < ex_date]
>         if len(prev_rows) == 0:
>             continue
>         ref_price = float(prev_rows['close'].iloc[-1])
>
>         # Get split factor at ex-date
>         at_or_before = pdf[pdf['date'] <= ex_date]
>         if len(at_or_before) == 0:
>             continue
>         cfacshr_at = at_or_before['cfacshr'].iloc[-1]
>         if pd.isna(cfacshr_at):
>             cfacshr_at = latest_cfacshr
>         split_factor = float(latest_cfacshr / cfacshr_at)
>
>         rows.append({
>             'date': ex_date,
>             'split_factor': split_factor,
>             'ref_price': ref_price,
>             'divamt': float(divamt),
>             'is_div': True,
>         })
>
>     if not rows:
>         # No corporate actions — just first date + sentinel
>         first_cfacshr = float(pdf['cfacshr'].iloc[0])
>         if pd.isna(first_cfacshr):
>             first_cfacshr = float(latest_cfacshr)
>         sf = float(latest_cfacshr) / first_cfacshr
>         return pd.DataFrame([
>             {
>                 'date_str': pdf['date'].iloc[0].strftime('%Y%m%d'),
>                 'price_factor': 1.0,
>                 'split_factor': round(sf, 8),
>                 'ref_price': round(float(pdf['close'].iloc[0]), 2),
>             },
>             {
>                 'date_str': '20501231',
>                 'price_factor': 1.0,
>                 'split_factor': 1.0,
>                 'ref_price': 0,
>             },
>         ])
>
>     # Sort by date, merge overlapping events on same date
>     events = pd.DataFrame(rows)
>     # Group by date — take max split_factor, sum divamt
>     grouped = []
>     for dt, grp in events.groupby('date'):
>         sf = grp['split_factor'].iloc[-1]  # last split factor at this date
>         ref = grp['ref_price'].iloc[0]
>         divamt = grp.loc[grp['is_div'], 'divamt'].sum() if grp['is_div'].any() else 0
>         grouped.append({
>             'date': dt,
>             'split_factor': sf,
>             'ref_price': ref,
>             'divamt': divamt,
>         })
>     events = pd.DataFrame(grouped).sort_values('date').reset_index(drop=True)
>
>     # Compute cumulative PriceFactor working backwards from 1.0
>     # For each cash dividend: price_adj = 1 - divamt / ref_price
>     # PriceFactor = cumulative product from latest to earliest
>     events['price_adj'] = 1.0
>     div_mask = events['divamt'] > 0
>     events.loc[div_mask, 'price_adj'] = (
>         1.0 - events.loc[div_mask, 'divamt'] / events.loc[div_mask, 'ref_price']
>     )
>
>     # Cumulative product from bottom to top
>     # At the latest event, PriceFactor = 1.0
>     # Going backwards, multiply by each price_adj
>     events['price_factor'] = events['price_adj'][::-1].cumprod()[::-1].values
>     # Normalize so the last event's PriceFactor = the adjustment between last event and sentinel
>     # Actually: the sentinel has PriceFactor=1, so the last event should have
>     # PriceFactor = price_adj of last event (if it was a dividend)
>     # Let's recalculate: PriceFactor at event i = product of price_adj from i to end
>     price_adjs = events['price_adj'].values
>     pf = np.ones(len(price_adjs))
>     cumulative = 1.0
>     for i in range(len(price_adjs) - 1, -1, -1):
>         cumulative *= price_adjs[i]
>         pf[i] = cumulative
>     events['price_factor'] = pf
>
>     # Also need initial row for the first date of data
>     first_date = pdf['date'].iloc[0]
>     first_cfacshr = float(pdf['cfacshr'].iloc[0])
>     if pd.isna(first_cfacshr):
>         first_cfacshr = float(latest_cfacshr)
>     first_sf = float(latest_cfacshr) / first_cfacshr
>
>     # If first event is after first data date, prepend a row
>     if events['date'].iloc[0] > first_date:
>         first_row = {
>             'date': first_date,
>             'split_factor': first_sf,
>             'ref_price': float(pdf['close'].iloc[0]),
>             'divamt': 0,
>             'price_adj': 1.0,
>             'price_factor': pf[0],  # same as first event's cumulative
>         }
>         events = pd.concat([pd.DataFrame([first_row]), events], ignore_index=True)
>
>     # Build output
>     out = pd.DataFrame({
>         'date_str': events['date'].apply(
>             lambda d: d.strftime('%Y%m%d') if hasattr(d, 'strftime') else str(d)[:10].replace('-', '')
>         ),
>         'price_factor': events['price_factor'].round(7),
>         'split_factor': events['split_factor'].round(8),
>         'ref_price': events['ref_price'].round(2),
>     })
>
>     # Append sentinel
>     sentinel = pd.DataFrame([{
>         'date_str': '20501231',
>         'price_factor': 1.0,
>         'split_factor': 1.0,
>         'ref_price': 0,
>     }])
>     out = pd.concat([out, sentinel], ignore_index=True)
>
>     return out
>
>
> def _sentinel_only():
>     return pd.DataFrame([{
>         'date_str': '20501231',
>         'price_factor': 1.0,
>         'split_factor': 1.0,
>         'ref_price': 0,
>     }])
>
>
> # ---------------------------------------------------------------------------
> # Map files
> # ---------------------------------------------------------------------------
>
> EXCHANGE_MAP = {
>     'N': 'N',   # NYSE
>     'A': 'A',   # AMEX
>     'Q': 'Q',   # NASDAQ
>     'P': 'P',   # NYSE Arca
> }
>
>
> def transform_map_file(names_df, permno, current_ticker):
>     """Build a LEAN map file from CRSP name history.
>
>     LEAN map file format (no header):
>         Date,MappedSymbol,PrimaryExchange
>
>     One row per name period. Sentinel row at end: 20501231,ticker,exchange
>
>     Returns DataFrame ready to write as CSV (no header).
>     """
>     ndf = names_df[names_df['permno'] == permno].copy()
>     ndf = ndf.sort_values('namedt').reset_index(drop=True)
>     # Filter out rows with null ticker values
>     ndf = ndf[ndf['ticker'].notna()].copy()
>
>     if ndf.empty:
>         return pd.DataFrame([{
>             'date_str': '20501231',
>             'ticker': current_ticker.lower(),
>             'exchange': 'N',
>         }])
>
>     rows = []
>     for _, row in ndf.iterrows():
>         exchange = EXCHANGE_MAP.get(row['primexch'], 'N')
>         rows.append({
>             'date_str': row['namedt'].strftime('%Y%m%d'),
>             'ticker': row['ticker'].lower(),
>             'exchange': exchange,
>         })
>
>     # Sentinel
>     last_row = ndf.iloc[-1]
>     exchange = EXCHANGE_MAP.get(last_row['primexch'], 'N')
>     rows.append({
>         'date_str': '20501231',
>         'ticker': current_ticker.lower(),
>         'exchange': exchange,
>     })
>
>     return pd.DataFrame(rows)
> ```
