"""Write LEAN-format and alternative-data files for the Massive.com pipeline.

Output layout under `lean-data/`:

    future/<market>/daily/<symbol>_trade.zip
        -> contains <symbol>_trade_<expiration YYYYMMDD>.csv
        -> "Time,Open,High,Low,Close,Volume" rows (no header), per
           https://github.com/QuantConnect/Lean/blob/master/Data/future/readme.md

    alternative/massive/options/chains/<underlying>_<YYYYMMDD>.csv
        -> point-in-time options chain snapshot (greeks/IV/OI), header row

    alternative/massive/options/aggregates/<contract_ticker>.csv
        -> per-contract daily OHLCV bars, header row

    alternative/massive/futures/contracts/<root>.csv
        -> futures contract reference metadata, header row

NOTE on the futures daily writer: this follows the documented LEAN format
(`future/<market>/daily/<symbol>_trade.zip`) but has not been validated by
loading the output into a running LEAN engine, since no Massive.com API key
was available while building this pipeline. Verify the zip/CSV naming and
the `<symbol>` value (contract ticker vs. continuous symbol) once real data
is available — see `claude.md` "Known limitations / unverified assumptions".
"""
from __future__ import annotations

import io
import os
import pathlib
import zipfile

import pandas as pd


def _lean_data_root(output_root: str | os.PathLike | None = None) -> pathlib.Path:
    if output_root is not None:
        return pathlib.Path(output_root)
    here = pathlib.Path(__file__).resolve().parent
    return here.parent.parent / "lean-data"


# ---------------------------------------------------------------------------
# Futures — lean-data/future/<market>/daily/<symbol>_trade.zip
# ---------------------------------------------------------------------------

def write_futures_daily(
    symbol: str,
    market: str,
    expiration_date: str,
    df: pd.DataFrame,
    output_root: str | os.PathLike | None = None,
) -> pathlib.Path:
    """Write a futures daily-bar DataFrame as a LEAN-format zip.

    `df` must have columns: date_str, open, high, low, close, volume
    (see `transform.transform_futures_daily_bars`).

    `expiration_date` should be `YYYYMMDD` and is embedded in the inner CSV
    filename per the LEAN futures daily naming convention
    (`<symbol>_trade_<expiration>.csv`).

    Returns the path to the written zip.
    """
    lean_root = _lean_data_root(output_root)
    symbol_lower = symbol.lower()
    out_dir = lean_root / "future" / market.lower() / "daily"
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"{r['date_str']},{r['open']},{r['high']},{r['low']},{r['close']},{r['volume']}"
        for _, r in df.iterrows()
    ]
    csv_content = "\n".join(lines) + "\n"

    zip_path = out_dir / f"{symbol_lower}_trade.zip"
    inner_name = f"{symbol_lower}_trade_{expiration_date}.csv"
    _atomic_write_zip(zip_path, inner_name, csv_content)
    return zip_path


# ---------------------------------------------------------------------------
# Options — alternative data
# ---------------------------------------------------------------------------

def write_options_chain_snapshot(
    underlying_ticker: str,
    snapshot_date: str,
    df: pd.DataFrame,
    output_root: str | os.PathLike | None = None,
) -> pathlib.Path:
    """Write a point-in-time options chain snapshot CSV (header row included).

    Path: alternative/massive/options/chains/<underlying>_<YYYYMMDD>.csv
    """
    lean_root = _lean_data_root(output_root)
    out_dir = lean_root / "alternative" / "massive" / "options" / "chains"
    out_dir.mkdir(parents=True, exist_ok=True)

    date_compact = snapshot_date.replace("-", "")
    path = out_dir / f"{underlying_ticker.lower()}_{date_compact}.csv"
    df.to_csv(path, index=False)
    return path


def write_option_daily_aggregates(
    contract_ticker: str,
    df: pd.DataFrame,
    output_root: str | os.PathLike | None = None,
) -> pathlib.Path:
    """Write per-contract daily OHLCV aggregates CSV (header row included).

    Path: alternative/massive/options/aggregates/<contract_ticker>.csv

    Merge-on-write by `date`: re-running the pipeline for an overlapping
    date range updates existing rows (new data wins) instead of duplicating.
    """
    lean_root = _lean_data_root(output_root)
    out_dir = lean_root / "alternative" / "massive" / "options" / "aggregates"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Massive option tickers look like "O:SPY251219C00650000" — strip the
    # "O:" prefix for a friendlier filename.
    safe_name = contract_ticker.replace("O:", "").replace(":", "_")
    path = out_dir / f"{safe_name}.csv"

    if path.exists() and not df.empty:
        existing = pd.read_csv(path)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset="date", keep="last").sort_values("date")
        combined.to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

def write_futures_contracts(
    root_symbol: str,
    df: pd.DataFrame,
    output_root: str | os.PathLike | None = None,
) -> pathlib.Path:
    """Write futures contract reference metadata CSV (header row included).

    Path: alternative/massive/futures/contracts/<root>.csv
    """
    lean_root = _lean_data_root(output_root)
    out_dir = lean_root / "alternative" / "massive" / "futures" / "contracts"
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / f"{root_symbol.lower()}.csv"
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atomic_write_zip(zip_path: pathlib.Path, inner_name: str, csv_text: str) -> None:
    """Write csv_text into a zip at zip_path via an atomic temp-file swap."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_name, csv_text)
    tmp = zip_path.with_suffix(".tmp")
    tmp.write_bytes(buf.getvalue())
    os.replace(tmp, zip_path)
