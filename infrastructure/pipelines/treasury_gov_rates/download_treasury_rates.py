import argparse
import datetime as dt
from pathlib import Path

import pandas as pd
import requests

BASE_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/"
    "accounting/od/avg_interest_rates"
)

TREASURY_COLUMNS = [
    "record_date",
    "security_desc",
    "avg_interest_rate_amt",
]


def fetch_rates(page_size: int = 10000) -> pd.DataFrame:
    """Download Treasury rate data from Treasury FiscalData API."""

    url = f"{BASE_URL}?page[size]={page_size}"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    payload = response.json()
    data = payload.get("data", [])

    if not data:
        raise ValueError("No Treasury rate data returned from API")

    df = pd.DataFrame(data)

    available_cols = [c for c in TREASURY_COLUMNS if c in df.columns]
    df = df[available_cols].copy()

    if "record_date" in df.columns:
        df["record_date"] = pd.to_datetime(df["record_date"])

    if "avg_interest_rate_amt" in df.columns:
        df["avg_interest_rate_amt"] = pd.to_numeric(
            df["avg_interest_rate_amt"],
            errors="coerce",
        )

    return df.sort_values("record_date")


def build_curve_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot Treasury data into a yield-curve style matrix."""

    if "security_desc" not in df.columns:
        return df

    curve = df.pivot_table(
        index="record_date",
        columns="security_desc",
        values="avg_interest_rate_amt",
        aggfunc="last",
    )

    curve = curve.sort_index()

    return curve


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Treasury.gov rates data",
    )

    parser.add_argument(
        "--output-dir",
        default="data/treasury_rates",
        help="Directory to write CSV outputs",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_df = fetch_rates()
    curve_df = build_curve_matrix(raw_df)

    today = dt.datetime.utcnow().strftime("%Y%m%d")

    raw_path = output_dir / f"treasury_rates_raw_{today}.csv"
    curve_path = output_dir / f"treasury_curve_matrix_{today}.csv"

    raw_df.to_csv(raw_path, index=False)
    curve_df.to_csv(curve_path)

    print(f"Wrote raw Treasury data to: {raw_path}")
    print(f"Wrote Treasury curve matrix to: {curve_path}")
    print(f"Rows downloaded: {len(raw_df):,}")


if __name__ == "__main__":
    main()
