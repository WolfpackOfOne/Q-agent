"""Transform yfinance DataFrames into LEAN daily bar, factor file, and map file formats."""

import pandas as pd


def transform_daily_bars(df):
    """Convert unadjusted OHLCV DataFrame to LEAN daily bar format.

    Input:  DataFrame with Open, High, Low, Close, Volume columns (unadjusted).
    Output: DataFrame with columns date_str, open, high, low, close, volume.

    Prices are scaled by 10,000 and stored as integers (deci-cents).
    Date format: 'YYYYMMDD 00:00'
    """
    result = pd.DataFrame({
        'date_str': df.index.strftime('%Y%m%d 00:00'),
        'open':     (df['Open']  * 10_000).round().astype(int),
        'high':     (df['High']  * 10_000).round().astype(int),
        'low':      (df['Low']   * 10_000).round().astype(int),
        'close':    (df['Close'] * 10_000).round().astype(int),
        'volume':   df['Volume'].round().astype(int),
    })
    return result


def transform_forex_bars(df):
    """Convert OHLC DataFrame to LEAN forex daily bar format.

    Unlike equity bars, LEAN forex bars store prices as plain decimals
    (no ×10000 scaling) and carry no volume column.

    Input:  DataFrame with Open, High, Low, Close columns.
    Output: DataFrame with columns date_str, open, high, low, close.
    Date format: 'YYYYMMDD 00:00'
    """
    result = pd.DataFrame({
        'date_str': df.index.strftime('%Y%m%d 00:00'),
        'open':     df['Open'].round(5),
        'high':     df['High'].round(5),
        'low':      df['Low'].round(5),
        'close':    df['Close'].round(5),
    })
    return result


def transform_factor_file(df):
    """Compute LEAN factor file rows from yfinance data.

    Computes:
      split_factor  = cfacshr(date) / cfacshr(latest), normalized to 1.0 at present.
                      Represents how many current shares one historical share becomes.
      price_factor  = cumulative (1 - div/prev_close) product, normalized to 1.0 at present.
                      Represents the dividend-adjustment multiplier relative to today.
      ref_price     = unadjusted close (×10000) on the day BEFORE a split; 0 otherwise.

    Only emits rows at the first date, each corporate-action date, and a sentinel (20501231).

    Returns DataFrame with columns: date_str, price_factor, split_factor, ref_price
    """
    splits    = df['Stock Splits']
    dividends = df['Dividends']
    closes    = df['Close']

    # ---- Split factor ------------------------------------------------
    # yfinance split ratios: 0 = no split, >0 = new/old shares
    split_ratios = splits.where(splits > 0, 1.0)
    cfacshr = split_ratios.cumprod()
    split_factor = cfacshr / cfacshr.iloc[-1]

    # ---- Price factor ------------------------------------------------
    # At each ex-div date, adjust factor *= (1 - div / prev_close).
    # Compute forward, then normalize to 1.0 at end.
    price_adj = pd.Series(1.0, index=df.index)
    div_dates = dividends[dividends > 0].index
    for date in div_dates:
        idx = df.index.get_loc(date)
        if idx == 0:
            continue
        prev_close = closes.iloc[idx - 1]
        div = dividends.at[date]
        if prev_close > 0:
            price_adj[date:] *= (1.0 - div / prev_close)
    price_factor = price_adj / price_adj.iloc[-1]

    # ---- Collect change-point dates ----------------------------------
    # Emit a row wherever either factor changes value.
    split_changed = (split_factor.diff().abs() > 1e-10).fillna(True)
    price_changed = (price_factor.diff().abs() > 1e-10).fillna(True)
    split_changed.iloc[0] = True  # always include first row
    price_changed.iloc[0] = True

    event_dates = df.index[split_changed | price_changed]

    rows = []
    for date in event_dates:
        pf = round(price_factor.at[date], 8)
        sf = round(split_factor.at[date], 8)

        # ref_price: close before a split event (so LEAN can map the price break)
        is_split = splits.at[date] > 0
        if is_split:
            idx = df.index.get_loc(date)
            ref = int(round(closes.iloc[idx - 1] * 10_000)) if idx > 0 else 0
        else:
            ref = 0

        rows.append({
            'date_str':     date.strftime('%Y%m%d'),
            'price_factor': pf,
            'split_factor': sf,
            'ref_price':    ref,
        })

    # Sentinel row (LEAN convention)
    rows.append({
        'date_str':     '20501231',
        'price_factor': 1.0,
        'split_factor': 1.0,
        'ref_price':    0,
    })

    return pd.DataFrame(rows)


def transform_map_file(ticker, exchange, start_date, end_date):
    """Build a simple LEAN map file for a ticker that was never renamed.

    Returns DataFrame with columns: date_str, ticker, exchange
    """
    ticker_lower = ticker.lower()
    rows = [
        {'date_str': start_date.strftime('%Y%m%d'), 'ticker': ticker_lower, 'exchange': exchange},
        {'date_str': '20501231',                     'ticker': ticker_lower, 'exchange': exchange},
    ]
    return pd.DataFrame(rows)
