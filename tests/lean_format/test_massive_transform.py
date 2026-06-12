"""LEAN-format compliance tests for the Massive.com futures/options pipeline transforms.

These are pure unit tests against mocked API response shapes (dicts and
SimpleNamespace objects mimicking `massive` SDK model objects) — no network
access and no MASSIVE_API_KEY required.

Field shapes are cross-checked against `massive==2.8.0`
(`massive/rest/models/futures.py`, `massive/rest/models/aggs.py`,
`massive/rest/models/snapshot.py`) — see
infrastructure/pipelines/massive/src/massive_lean/transform.py for details
and any remaining "ASSUMPTION" notes.
"""

import zipfile
from types import SimpleNamespace

import pandas as pd
import pytest

from massive_lean.transform import (
    transform_futures_contracts,
    transform_futures_daily_bars,
    transform_option_daily_bars,
    transform_options_chain_snapshot,
)
from massive_lean.writer import (
    write_futures_daily,
    write_option_daily_aggregates,
    write_options_chain_snapshot,
)


def _chain_item(**overrides):
    base = {
        "details": {
            "ticker": "O:SPY251219C00650000",
            "strike_price": 650.0,
            "expiration_date": "2025-12-19",
            "contract_type": "call",
        },
        "greeks": {"delta": 0.55, "gamma": 0.01, "theta": -0.12, "vega": 0.30},
        "implied_volatility": 0.18,
        "open_interest": 12345,
        "day": {"close": 12.5, "volume": 4321},
        "last_quote": {"bid": 12.4, "ask": 12.6},
        "last_trade": {"price": 12.5},
    }
    base.update(overrides)
    return base


class TestFuturesDailyBarTransform:
    """`window_start` is nanoseconds since epoch UTC (FuturesAgg, massive==2.8.0)."""

    def test_column_order(self):
        out = transform_futures_daily_bars([
            {"window_start": 1704153600000000000, "open": 4780.0, "high": 4805.5,
             "low": 4775.25, "close": 4800.0, "volume": 1_500_000},
        ])
        assert list(out.columns) == ["date_str", "open", "high", "low", "close", "volume"]

    def test_date_format(self):
        out = transform_futures_daily_bars([
            {"window_start": 1704153600000000000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"window_start": 1704240000000000000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        ])
        assert out["date_str"].tolist() == ["20240102 00:00", "20240103 00:00"]

    def test_prices_not_scaled(self):
        """Unlike equities, futures daily prices are NOT multiplied by 10,000."""
        out = transform_futures_daily_bars([
            {"window_start": 1704153600000000000, "open": 4780.0, "high": 4805.5,
             "low": 4775.25, "close": 4800.0, "volume": 1_500_000},
        ])
        assert out.iloc[0]["open"] == 4780.0
        assert out.iloc[0]["close"] == 4800.0

    def test_handles_sdk_model_objects(self):
        """SDK responses may be model objects exposing attributes, not dicts."""
        raw = [SimpleNamespace(window_start=1704153600000000000, open=4780.0, high=4805.5,
                                low=4775.25, close=4800.0, volume=1_500_000)]
        out = transform_futures_daily_bars(raw)
        assert out.iloc[0]["close"] == 4800.0

    def test_falls_back_to_millisecond_timestamp(self):
        out = transform_futures_daily_bars([
            {"timestamp": 1704153600000, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10},
        ])
        assert out.iloc[0]["date_str"] == "20240102 00:00"

    def test_empty(self):
        out = transform_futures_daily_bars([])
        assert out.empty
        assert list(out.columns) == ["date_str", "open", "high", "low", "close", "volume"]

    def test_dedupes_by_date_sorted_ascending(self):
        out = transform_futures_daily_bars([
            {"window_start": 1704240000000000000, "open": 2, "high": 2, "low": 2, "close": 2, "volume": 2},
            {"window_start": 1704153600000000000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"window_start": 1704153600000000000, "open": 1, "high": 1, "low": 1, "close": 9, "volume": 9},
        ])
        assert len(out) == 2
        assert out["date_str"].is_monotonic_increasing
        assert out.iloc[0]["close"] == 1  # first occurrence wins


class TestFuturesContractsTransform:
    """FuturesContract has `trading_venue` (not `exchange`) and no `expiration_date`
    field — `last_trade_date` / `settlement_date` / `date` are used as the proxy."""

    def test_maps_trading_venue_to_exchange(self):
        out = transform_futures_contracts([
            {"ticker": "ESZ24", "product_code": "ES", "trading_venue": "CME",
             "first_trade_date": "2022-01-03", "last_trade_date": "2024-12-20",
             "name": "E-mini S&P 500 Future Dec 2024"},
        ])
        assert out.iloc[0]["ticker"] == "ESZ24"
        assert out.iloc[0]["exchange"] == "CME"
        assert out.iloc[0]["expiration_date"] == "2024-12-20"

    def test_expiration_falls_back_to_settlement_date(self):
        out = transform_futures_contracts([
            {"ticker": "ESZ24", "product_code": "ES", "trading_venue": "CME",
             "settlement_date": "2024-12-20"},
        ])
        assert out.iloc[0]["expiration_date"] == "2024-12-20"

    def test_empty(self):
        assert transform_futures_contracts([]).empty


class TestOptionsChainSnapshotTransform:
    """Field shapes from OptionContractSnapshot (massive==2.8.0,
    massive/rest/models/snapshot.py): details/greeks/day/last_quote/last_trade
    are nested objects; implied_volatility and open_interest are top-level."""

    def test_column_order(self):
        out = transform_options_chain_snapshot("SPY", "2024-06-10", [_chain_item()])
        assert list(out.columns) == [
            "snapshot_date", "underlying_ticker", "contract_ticker", "expiration_date",
            "strike_price", "contract_type", "bid", "ask", "last_price", "volume",
            "open_interest", "implied_volatility", "delta", "gamma", "theta", "vega",
        ]

    def test_extracts_nested_fields(self):
        out = transform_options_chain_snapshot("SPY", "2024-06-10", [_chain_item()])
        row = out.iloc[0]
        assert row["snapshot_date"] == "2024-06-10"
        assert row["underlying_ticker"] == "SPY"
        assert row["contract_ticker"] == "O:SPY251219C00650000"
        assert row["strike_price"] == 650.0
        assert row["contract_type"] == "call"
        assert row["bid"] == 12.4
        assert row["ask"] == 12.6
        assert row["open_interest"] == 12345
        assert row["implied_volatility"] == 0.18
        assert row["delta"] == 0.55
        assert row["gamma"] == 0.01
        assert row["theta"] == -0.12
        assert row["vega"] == 0.30

    def test_falls_back_to_day_close_when_no_quote_or_trade(self):
        item = _chain_item(last_trade={}, last_quote={})
        out = transform_options_chain_snapshot("SPY", "2024-06-10", [item])
        assert out.iloc[0]["last_price"] == 12.5  # from day.close
        assert pd.isna(out.iloc[0]["bid"])
        assert pd.isna(out.iloc[0]["ask"])

    def test_empty(self):
        out = transform_options_chain_snapshot("SPY", "2024-06-10", [])
        assert out.empty
        assert "snapshot_date" in out.columns


class TestOptionDailyBarTransform:
    """Agg.timestamp is milliseconds since epoch UTC (massive==2.8.0, massive/rest/models/aggs.py)."""

    def test_column_order(self):
        out = transform_option_daily_bars("O:SPY251219C00650000", [
            {"timestamp": 1704153600000, "open": 10.0, "high": 11.0, "low": 9.5,
             "close": 10.5, "volume": 100, "vwap": 10.2, "transactions": 50},
        ])
        assert list(out.columns) == [
            "date", "contract_ticker", "open", "high", "low", "close", "volume", "vwap", "transactions",
        ]

    def test_date_format_and_sort(self):
        out = transform_option_daily_bars("O:SPY251219C00650000", [
            {"timestamp": 1704240000000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "vwap": 1, "transactions": 1},
            {"timestamp": 1704153600000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "vwap": 1, "transactions": 1},
        ])
        assert out["date"].tolist() == ["2024-01-02", "2024-01-03"]
        assert (out["contract_ticker"] == "O:SPY251219C00650000").all()

    def test_empty(self):
        assert transform_option_daily_bars("O:SPY251219C00650000", []).empty


class TestFuturesDailyWriter:
    def test_zip_layout_and_csv_format(self, tmp_path):
        df = transform_futures_daily_bars([
            {"window_start": 1704153600000000000, "open": 4780.0, "high": 4805.5,
             "low": 4775.25, "close": 4800.0, "volume": 1_500_000},
        ])
        zip_path = write_futures_daily("ESZ24", "cme", "20241220", df, output_root=tmp_path)

        assert zip_path == tmp_path / "future" / "cme" / "daily" / "esz24_trade.zip"
        with zipfile.ZipFile(zip_path) as zf:
            assert zf.namelist() == ["esz24_trade_20241220.csv"]
            content = zf.read("esz24_trade_20241220.csv").decode()

        # No header; "Time,Open,High,Low,Close,Volume" per
        # https://github.com/QuantConnect/Lean/blob/master/Data/future/readme.md
        line = content.strip().split("\n")[0]
        fields = line.split(",")
        assert fields[0] == "20240102 00:00"
        assert len(fields) == 6


class TestOptionsAlternativeDataWriters:
    def test_chain_snapshot_csv_has_header(self, tmp_path):
        df = transform_options_chain_snapshot("SPY", "2024-06-10", [_chain_item()])
        path = write_options_chain_snapshot("SPY", "2024-06-10", df, output_root=tmp_path)

        assert path == tmp_path / "alternative" / "massive" / "options" / "chains" / "spy_20240610.csv"
        loaded = pd.read_csv(path)
        assert loaded.iloc[0]["contract_ticker"] == "O:SPY251219C00650000"

    def test_option_aggregates_merge_on_rerun(self, tmp_path):
        ticker = "O:SPY251219C00650000"
        df1 = transform_option_daily_bars(ticker, [
            {"timestamp": 1704153600000, "open": 10.0, "high": 11.0, "low": 9.5,
             "close": 10.5, "volume": 100, "vwap": 10.2, "transactions": 50},
        ])
        path = write_option_daily_aggregates(ticker, df1, output_root=tmp_path)
        assert path.name == "SPY251219C00650000.csv"

        df2 = transform_option_daily_bars(ticker, [
            {"timestamp": 1704153600000, "open": 10.0, "high": 11.0, "low": 9.5,
             "close": 10.6, "volume": 110, "vwap": 10.3, "transactions": 55},  # updated
            {"timestamp": 1704240000000, "open": 10.6, "high": 12.0, "low": 10.0,
             "close": 11.5, "volume": 150, "vwap": 11.0, "transactions": 70},  # new
        ])
        write_option_daily_aggregates(ticker, df2, output_root=tmp_path)

        loaded = pd.read_csv(path)
        assert len(loaded) == 2
        row = loaded[loaded["date"] == "2024-01-02"].iloc[0]
        assert row["close"] == 10.6  # new data wins on re-run
