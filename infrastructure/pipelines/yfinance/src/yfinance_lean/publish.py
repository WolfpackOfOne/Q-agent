"""Write LEAN-format files: daily bar zips, factor files, map files."""

import os
import zipfile


LEAN_DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
DAILY_DIR  = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'daily')
FACTOR_DIR = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'factor_files')
MAP_DIR    = os.path.join(LEAN_DATA_ROOT, 'equity', 'usa', 'map_files')


def _ensure_dirs():
    for d in [DAILY_DIR, FACTOR_DIR, MAP_DIR]:
        os.makedirs(d, exist_ok=True)


def publish_daily_bar(ticker, df):
    """Write daily bar DataFrame as {ticker}.zip containing {ticker}.csv (no header).

    DataFrame must have columns: date_str, open, high, low, close, volume
    """
    _ensure_dirs()
    ticker = ticker.lower()
    lines = [
        f"{r['date_str']},{r['open']},{r['high']},{r['low']},{r['close']},{r['volume']}"
        for _, r in df.iterrows()
    ]
    csv_content = '\n'.join(lines) + '\n'
    zip_path = os.path.join(DAILY_DIR, f'{ticker}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'{ticker}.csv', csv_content)
    return zip_path


def publish_forex_bar(symbol, df, market='oanda'):
    """Write forex daily bars as forex/<market>/daily/{symbol}.zip → {symbol}.csv.

    DataFrame must have columns: date_str, open, high, low, close (no volume).
    Forex has no factor/map files, so only the bar zip is written.
    """
    symbol = symbol.lower()
    daily_dir = os.path.join(LEAN_DATA_ROOT, 'forex', market, 'daily')
    os.makedirs(daily_dir, exist_ok=True)
    lines = [
        f"{r['date_str']},{r['open']},{r['high']},{r['low']},{r['close']}"
        for _, r in df.iterrows()
    ]
    csv_content = '\n'.join(lines) + '\n'
    zip_path = os.path.join(daily_dir, f'{symbol}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'{symbol}.csv', csv_content)
    return zip_path


def publish_factor_file(ticker, df):
    """Write factor file DataFrame as {ticker}.csv (no header).

    DataFrame must have columns: date_str, price_factor, split_factor, ref_price
    """
    _ensure_dirs()
    ticker = ticker.lower()
    lines = [
        f"{r['date_str']},{r['price_factor']},{r['split_factor']},{r['ref_price']}"
        for _, r in df.iterrows()
    ]
    csv_content = '\n'.join(lines) + '\n'
    path = os.path.join(FACTOR_DIR, f'{ticker}.csv')
    with open(path, 'w') as f:
        f.write(csv_content)
    return path


def publish_map_file(ticker, df):
    """Write map file DataFrame as {ticker}.csv (no header).

    DataFrame must have columns: date_str, ticker, exchange
    """
    _ensure_dirs()
    ticker = ticker.lower()
    lines = [
        f"{r['date_str']},{r['ticker']},{r['exchange']}"
        for _, r in df.iterrows()
    ]
    csv_content = '\n'.join(lines) + '\n'
    path = os.path.join(MAP_DIR, f'{ticker}.csv')
    with open(path, 'w') as f:
        f.write(csv_content)
    return path
