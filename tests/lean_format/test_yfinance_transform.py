"""LEAN-format compliance tests for the yfinance pipeline transforms.

These guard the contract every project depends on: deci-cent price scaling,
'YYYYMMDD HH:MM' date format, expected column order, and sentinel rows on
factor/map files.
"""

from io import BytesIO
import zipfile

import pandas as pd
import pytest

from yfinance_lean import publish, transform


@pytest.fixture
def ohlcv_frame() -> pd.DataFrame:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    return pd.DataFrame(
        {
            "Open":   [100.12, 101.50, 102.75],
            "High":   [101.00, 102.30, 103.40],
            "Low":    [ 99.50, 101.10, 102.10],
            "Close":  [100.80, 102.10, 103.05],
            "Volume": [1_000_000, 1_500_000, 1_200_000],
        },
        index=idx,
    )


@pytest.fixture
def corporate_actions_frame() -> pd.DataFrame:
    """Three-day frame with a dividend on day 2 and a 2:1 split on day 3."""
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    return pd.DataFrame(
        {
            "Open":          [100.0, 100.0, 50.0],
            "High":          [101.0, 101.0, 51.0],
            "Low":           [ 99.0,  99.0, 49.0],
            "Close":         [100.0, 100.0, 50.0],
            "Volume":        [1_000_000, 1_000_000, 1_000_000],
            "Dividends":     [0.0, 1.0, 0.0],
            "Stock Splits":  [0.0, 0.0, 2.0],
        },
        index=idx,
    )


class TestDailyBarTransform:
    def test_column_order(self, ohlcv_frame):
        out = transform.transform_daily_bars(ohlcv_frame)
        assert list(out.columns) == ["date_str", "open", "high", "low", "close", "volume"]

    def test_date_format(self, ohlcv_frame):
        out = transform.transform_daily_bars(ohlcv_frame)
        assert out["date_str"].tolist() == [
            "20240102 00:00",
            "20240103 00:00",
            "20240104 00:00",
        ]

    def test_price_scaling_deci_cents(self, ohlcv_frame):
        out = transform.transform_daily_bars(ohlcv_frame)
        # 100.12 * 10_000 = 1_001_200. The transform preserves the input
        # DatetimeIndex, so we look up by position rather than label.
        assert out.iloc[0]["open"] == 1_001_200
        assert out.iloc[0]["close"] == 1_008_000

    def test_price_columns_are_integers(self, ohlcv_frame):
        out = transform.transform_daily_bars(ohlcv_frame)
        for col in ("open", "high", "low", "close", "volume"):
            assert pd.api.types.is_integer_dtype(out[col]), f"{col} must be integer"

    def test_volume_not_scaled(self, ohlcv_frame):
        out = transform.transform_daily_bars(ohlcv_frame)
        assert out["volume"].tolist() == [1_000_000, 1_500_000, 1_200_000]


class TestFactorFileTransform:
    def test_column_order(self, corporate_actions_frame):
        out = transform.transform_factor_file(corporate_actions_frame)
        assert list(out.columns) == ["date_str", "price_factor", "split_factor", "ref_price"]

    def test_sentinel_row_present(self, corporate_actions_frame):
        out = transform.transform_factor_file(corporate_actions_frame)
        last = out.iloc[-1]
        assert last["date_str"] == "20501231"
        assert last["price_factor"] == 1.0
        assert last["split_factor"] == 1.0
        assert last["ref_price"] == 0

    def test_factors_normalize_to_one_at_end(self, corporate_actions_frame):
        out = transform.transform_factor_file(corporate_actions_frame)
        # Last *real* row (before sentinel) should also be 1.0 — normalization point.
        real = out.iloc[-2]
        assert real["price_factor"] == 1.0
        assert real["split_factor"] == 1.0

    def test_split_ref_price_uses_prior_close_scaled(self, corporate_actions_frame):
        out = transform.transform_factor_file(corporate_actions_frame)
        # 2024-01-04 was the split; prior close = 100.0 → 1_000_000 deci-cents.
        split_row = out[out["date_str"] == "20240104"].iloc[0]
        assert split_row["ref_price"] == 1_000_000


class TestMapFileTransform:
    def test_columns_and_sentinel(self):
        df = transform.transform_map_file(
            ticker="AAPL",
            exchange="Q",
            start_date=pd.Timestamp("1980-12-12"),
            end_date=pd.Timestamp("2024-01-01"),
        )
        assert list(df.columns) == ["date_str", "ticker", "exchange"]
        assert df.iloc[0]["date_str"] == "19801212"
        assert df.iloc[-1]["date_str"] == "20501231"
        # Ticker is lowercased in LEAN map files.
        assert df["ticker"].unique().tolist() == ["aapl"]


class TestDailyBarPublish:
    def test_zip_layout(self, ohlcv_frame, tmp_path, monkeypatch):
        monkeypatch.setattr(publish, "DAILY_DIR", str(tmp_path))
        monkeypatch.setattr(publish, "_ensure_dirs", lambda: None)

        bars = transform.transform_daily_bars(ohlcv_frame)
        zip_path = publish.publish_daily_bar("AAPL", bars)

        assert zip_path.endswith("aapl.zip")
        with zipfile.ZipFile(zip_path) as zf:
            assert zf.namelist() == ["aapl.csv"]
            content = zf.read("aapl.csv").decode()

        # CSV has no header and uses comma separators.
        first_line = content.splitlines()[0]
        assert first_line.startswith("20240102 00:00,")
        assert first_line.count(",") == 5  # 6 columns → 5 commas
