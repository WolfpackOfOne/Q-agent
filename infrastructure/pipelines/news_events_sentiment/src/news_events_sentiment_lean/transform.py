"""Merge GDELT tone + volume timelines into a clean per-ticker DataFrame."""

import pandas as pd


def transform_sentiment(ticker, tone_points, volume_points):
    """Return DataFrame: date, ticker, avg_tone, volume_pct, tone_z.

    tone_z is a 90-day rolling z-score of avg_tone -- how surprising today's
    tone is relative to this ticker's own recent baseline, since raw tone
    has ticker- and regime-specific baselines that aren't comparable across
    names or time.

    GDELT returns avg_tone=0.0 on a day with zero matching articles (volume_pct
    also 0.0) -- that 0.0 is a "no data" placeholder, not a genuine neutral-tone
    reading. Days with volume_pct == 0 are treated as no-coverage and avg_tone
    is set to NaN so they don't silently pull the rolling baseline toward zero
    (this matters most for narrow, domain-filtered queries where true zero-
    coverage days are common).
    """
    empty = pd.DataFrame(columns=["date", "ticker", "avg_tone", "volume_pct", "tone_z"])
    if not tone_points or not volume_points:
        return empty

    tone_df = pd.DataFrame(tone_points).rename(columns={"value": "avg_tone"})
    vol_df = pd.DataFrame(volume_points).rename(columns={"value": "volume_pct"})

    for df in (tone_df, vol_df):
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%dT%H%M%SZ").dt.normalize()

    merged = tone_df.merge(vol_df, on="date", how="outer").sort_values("date").reset_index(drop=True)
    if merged.empty:
        return empty

    merged["ticker"] = ticker
    merged.loc[merged["volume_pct"] == 0, "avg_tone"] = pd.NA
    merged["avg_tone"] = merged["avg_tone"].astype("float64")

    roll = merged["avg_tone"].rolling(90, min_periods=20)
    merged["tone_z"] = (merged["avg_tone"] - roll.mean()) / roll.std()

    return merged[["date", "ticker", "avg_tone", "volume_pct", "tone_z"]]
