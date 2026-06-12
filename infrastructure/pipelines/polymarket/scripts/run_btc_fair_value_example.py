"""Build a committed data snapshot for the BTC Polymarket fair-value notebook.

This script reads Polymarket metadata and YES-token histories from the existing
Polymarket pipeline cache under ``lean-data/alternative/polymarket`` and writes
a small, curated snapshot under ``infrastructure/marimo/data``. The notebook can
then run without live Polymarket API calls, while the snapshot is still
reproducible from pipeline output.

Usage:
    python scripts/run_btc_fair_value_example.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import pandas as pd
import yfinance as yf


HERE = pathlib.Path(__file__).resolve()
PIPELINE_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[4]

DEFAULT_POLY_ROOT = PIPELINE_ROOT / "lean-data" / "alternative" / "polymarket"
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT / "infrastructure" / "marimo" / "data" / "btc_polymarket_fair_value"
)

BTC_MARKETS = [
    {
        "label": "Reach $90k",
        "event_type": "reach",
        "target": 90_000.0,
        "slug": "will-bitcoin-reach-90000-by-december-31-2026-113-862-581",
    },
    {
        "label": "Reach $100k",
        "event_type": "reach",
        "target": 100_000.0,
        "slug": "will-bitcoin-reach-100000-by-december-31-2026-571-361-361",
    },
    {
        "label": "Reach $110k",
        "event_type": "reach",
        "target": 110_000.0,
        "slug": "will-bitcoin-reach-110000-by-december-31-2026-658-339-969",
    },
    {
        "label": "Reach $120k",
        "event_type": "reach",
        "target": 120_000.0,
        "slug": "will-bitcoin-reach-120000-by-december-31-2026-625-425-562",
    },
    {
        "label": "Dip to $50k",
        "event_type": "dip",
        "target": 50_000.0,
        "slug": "will-bitcoin-dip-to-50000-by-december-31-2026-454-325-222-878-949-487-451",
    },
]

MONTH_CODES = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z",
}


def _btc_future_contract(as_of: pd.Timestamp, month_offset: int) -> dict[str, Any]:
    contract_month = as_of.to_period("M") + month_offset
    code = MONTH_CODES[int(contract_month.month)]
    yy = int(contract_month.year) % 100
    end = contract_month.to_timestamp(how="end").normalize()
    return {
        "label": f"{month_offset}M",
        "column": f"btc_{month_offset}m_future",
        "symbol": f"BTC{code}{yy:02d}.CME",
        "month_offset": month_offset,
        "contract_month_end": end.date().isoformat(),
    }


def _download_close(symbol: str, start: str, end: str | None = None) -> pd.Series:
    raw = yf.download(
        symbol,
        start=start,
        end=end,
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    if raw.empty or "Close" not in raw:
        raise ValueError(f"No Yahoo Finance close data for {symbol}")
    close = raw["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna().astype(float)
    close.index = pd.to_datetime(close.index).normalize()
    return close


def _load_daily_polymarket_price(path: pathlib.Path) -> pd.Series:
    raw = pd.read_csv(path, parse_dates=["datetime"])
    if raw.empty:
        return pd.Series(dtype=float)
    raw["datetime"] = pd.to_datetime(raw["datetime"], utc=True)
    daily = raw.set_index("datetime").sort_index()["price"].resample("D").last().dropna()
    daily.index = daily.index.tz_convert(None).normalize()
    return daily.astype(float)


def build_snapshot(
    polymarket_root: pathlib.Path,
    output_dir: pathlib.Path,
    start: str,
    end: str | None,
    as_of: str | None,
) -> None:
    markets_path = polymarket_root / "markets.csv"
    prices_dir = polymarket_root / "prices"
    if not markets_path.exists():
        raise FileNotFoundError(
            f"{markets_path} not found. Run the Polymarket markets pipeline first."
        )
    if not prices_dir.exists():
        raise FileNotFoundError(
            f"{prices_dir} not found. Run scripts/run_prices_pipeline.py first."
        )

    markets = pd.read_csv(markets_path)
    market_rows = []
    price_rows = []

    for cfg in BTC_MARKETS:
        slug = cfg["slug"]
        price_path = prices_dir / f"{slug}.csv"
        if not price_path.exists():
            raise FileNotFoundError(
                f"Missing price file for {slug}. Run the Polymarket prices pipeline."
            )
        daily = _load_daily_polymarket_price(price_path)
        meta_match = markets[markets["Slug"] == slug]
        meta = meta_match.iloc[0].to_dict() if not meta_match.empty else {}
        end_date = meta.get("EndDate") or "2027-01-01T05:00:00Z"

        market_rows.append(
            {
                "slug": slug,
                "label": cfg["label"],
                "event_type": cfg["event_type"],
                "target": cfg["target"],
                "question": meta.get("Question", ""),
                "end_date": end_date,
                "volume": meta.get("Volume"),
                "liquidity": meta.get("Liquidity"),
                "yes_token_id": meta.get("YesTokenId"),
                "no_token_id": meta.get("NoTokenId"),
                "latest_polymarket_prob": float(daily.iloc[-1]) if len(daily) else None,
            }
        )
        for dt, prob in daily.items():
            price_rows.append({"date": dt.date().isoformat(), "slug": slug, "prob": prob})

    as_of_ts = (
        pd.Timestamp(as_of).normalize()
        if as_of
        else pd.Timestamp.now("UTC").tz_localize(None).normalize()
    )
    contracts = [
        _btc_future_contract(as_of_ts, 1),
        _btc_future_contract(as_of_ts, 3),
    ]

    price_panel = pd.DataFrame({"btc_spot": _download_close("BTC-USD", start, end)})
    for contract in contracts:
        price_panel[contract["column"]] = _download_close(contract["symbol"], start, end)
    price_panel = price_panel.sort_index()

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(market_rows).to_csv(output_dir / "btc_polymarket_markets.csv", index=False)
    pd.DataFrame(price_rows).to_csv(output_dir / "btc_polymarket_prices.csv", index=False)
    price_panel.to_csv(output_dir / "btc_spot_futures.csv", index_label="date")
    pd.DataFrame(contracts).to_csv(output_dir / "btc_futures_contracts.csv", index=False)

    manifest = {
        "generated_at_utc": pd.Timestamp.now("UTC").isoformat(),
        "source_polymarket_root": str(polymarket_root),
        "start": start,
        "end": end,
        "as_of_for_contract_selection": as_of_ts.date().isoformat(),
        "markets": [m["slug"] for m in BTC_MARKETS],
        "files": [
            "btc_polymarket_markets.csv",
            "btc_polymarket_prices.csv",
            "btc_spot_futures.csv",
            "btc_futures_contracts.csv",
        ],
    }
    (output_dir / "snapshot.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"Wrote BTC fair-value example snapshot to {output_dir}", file=sys.stderr)
    print(f"Rows: markets={len(market_rows)}, poly_prices={len(price_rows)}, btc_prices={len(price_panel)}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--polymarket-root", type=pathlib.Path, default=DEFAULT_POLY_ROOT)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start", default="2026-04-01")
    parser.add_argument("--end", default=None)
    parser.add_argument(
        "--as-of",
        default=None,
        help="Date used to choose monthly BTC futures symbols. Defaults to today.",
    )
    args = parser.parse_args()

    build_snapshot(
        polymarket_root=args.polymarket_root,
        output_dir=args.output_dir,
        start=args.start,
        end=args.end,
        as_of=args.as_of,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
