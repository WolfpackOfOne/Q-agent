"""Sector classification from Compustat.

Extracts GICS sector codes from Compustat, maps to Morningstar sector codes
(as used by QuantConnect fundamentals), and publishes a static sector map.

Output: lean-data/alternative/sectors/sector_map.csv
Format: Ticker,GICSSector,GICSIndustryGroup,GICSIndustry,GICSSubIndustry,MorningstarSectorCode,MorningstarSectorName,SIC
"""

import os

import pandas as pd

from .connection import get_connection

# GICS sector code -> Morningstar sector code mapping
# GICS: https://www.msci.com/our-solutions/indexes/gics
# Morningstar: https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/us-equity/requesting-data/fundamentals
GICS_TO_MORNINGSTAR = {
    10: (309, "Energy"),
    15: (101, "Basic Materials"),
    20: (310, "Industrials"),
    25: (102, "Consumer Cyclical"),
    30: (205, "Consumer Defensive"),
    35: (206, "Healthcare"),
    40: (103, "Financial Services"),
    45: (311, "Technology"),
    50: (308, "Communication Services"),
    55: (207, "Utilities"),
    60: (104, "Real Estate"),
}


def extract_sectors(tickers):
    """Extract GICS sector classifications from Compustat.

    Args:
        tickers: List of ticker strings

    Returns:
        DataFrame with columns: ticker, gvkey, gsector, gind, gsubind, sic, conm
    """
    conn = get_connection()

    sql = """
        SELECT s.tic AS ticker, c.gvkey, c.gsector, c.gind, c.gsubind, c.sic, c.conm
        FROM comp.security s
        JOIN comp.company c ON s.gvkey = c.gvkey
        WHERE s.tic IN %(tickers)s
          AND s.iid = '01'
        ORDER BY s.tic
    """
    df = conn.raw_sql(sql, params={'tickers': tuple(tickers)})
    return df


def extract_historical_gics(gvkeys):
    """Extract point-in-time GICS classifications from Compustat's history table.

    ``comp.company`` carries only a company's *current* classification. Roughly
    39% of companies have been reclassified at least once (the 2018 creation of
    the Communication Services sector moved a large block of names out of
    Information Technology and Consumer Discretionary), so using the current
    code for a historical date is a look-ahead. ``comp.co_hgic`` carries each
    classification with the window it applied to.

    Args:
        gvkeys: iterable of gvkey strings (6-character, zero-padded)

    Returns:
        DataFrame with columns: gvkey, indfrom, indthru, gsector, ggroup, gind, gsubind
        ``indthru`` is null for the currently-effective row.
    """
    conn = get_connection()
    sql = """
        SELECT gvkey, indfrom, indthru, gsector, ggroup, gind, gsubind
        FROM comp.co_hgic
        WHERE gvkey IN %(gvkeys)s
        ORDER BY gvkey, indfrom
    """
    return conn.raw_sql(sql, params={'gvkeys': tuple(gvkeys)})


def build_pit_sector_map(hist_df, gvkey_permno, company_df=None):
    """Attach PERMNOs and Morningstar codes to the point-in-time GICS history.

    Args:
        hist_df: DataFrame from extract_historical_gics()
        gvkey_permno: DataFrame with columns gvkey, permno (and optionally Ticker)
        company_df: optional DataFrame from extract_sectors()-style pull, used to
            fill SIC and company name

    Returns:
        DataFrame keyed on (gvkey, permno, ValidFrom) with GICS levels, the
        Morningstar sector code, and ValidThrough (null = still in effect).
    """
    df = hist_df.copy()
    df['gvkey'] = df['gvkey'].astype(str).str.zfill(6)
    df['indfrom'] = pd.to_datetime(df['indfrom'], errors='coerce')
    df['indthru'] = pd.to_datetime(df['indthru'], errors='coerce')

    link = gvkey_permno.copy()
    link['gvkey'] = link['gvkey'].astype(str).str.zfill(6)
    df = df.merge(link.drop_duplicates(['gvkey', 'permno']), on='gvkey', how='inner')

    df['gsector_int'] = pd.to_numeric(df['gsector'], errors='coerce').astype('Int64')
    df['MorningstarSectorCode'] = df['gsector_int'].map(
        lambda x: GICS_TO_MORNINGSTAR.get(x, (None, None))[0] if pd.notna(x) else None
    ).astype('Int64')
    df['MorningstarSectorName'] = df['gsector_int'].map(
        lambda x: GICS_TO_MORNINGSTAR.get(x, (None, None))[1] if pd.notna(x) else None
    )

    if company_df is not None:
        extra = company_df.copy()
        extra['gvkey'] = extra['gvkey'].astype(str).str.zfill(6)
        df = df.merge(extra[['gvkey', 'conm', 'sic']].drop_duplicates('gvkey'), on='gvkey', how='left')
    else:
        df['conm'] = pd.NA
        df['sic'] = pd.NA

    out = df.rename(columns={
        'indfrom': 'ValidFrom', 'indthru': 'ValidThrough', 'conm': 'CompanyName',
        'gsector': 'GICSSector', 'ggroup': 'GICSIndustryGroup',
        'gind': 'GICSIndustry', 'gsubind': 'GICSSubIndustry', 'sic': 'SIC',
    })
    cols = ['gvkey', 'permno', 'CompanyName', 'ValidFrom', 'ValidThrough',
            'GICSSector', 'GICSIndustryGroup', 'GICSIndustry', 'GICSSubIndustry',
            'SIC', 'MorningstarSectorCode', 'MorningstarSectorName']
    if 'Ticker' in out.columns:
        cols.insert(2, 'Ticker')
    return out[cols].sort_values(['permno', 'ValidFrom']).reset_index(drop=True)


def publish_pit_sector_map(df, lean_data_dir=None, filename='broad_sector_map.csv'):
    """Write the point-in-time sector map to lean-data/alternative/sectors/."""
    if lean_data_dir is None:
        lean_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')
    sector_dir = os.path.join(lean_data_dir, 'alternative', 'sectors')
    os.makedirs(sector_dir, exist_ok=True)
    filepath = os.path.join(sector_dir, filename)
    df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
    return filepath


def transform_sector_map(sectors_df):
    """Transform Compustat GICS data to include Morningstar sector codes.

    Args:
        sectors_df: DataFrame from extract_sectors()

    Returns:
        DataFrame with added MorningstarSectorCode and MorningstarSectorName columns
    """
    df = sectors_df.copy()

    # Parse GICS sector (first 2 digits of gsector)
    df['gsector_int'] = pd.to_numeric(df['gsector'], errors='coerce').astype('Int64')

    # Map to Morningstar
    df['MorningstarSectorCode'] = df['gsector_int'].map(
        lambda x: GICS_TO_MORNINGSTAR.get(x, (None, None))[0] if pd.notna(x) else None
    ).astype('Int64')

    df['MorningstarSectorName'] = df['gsector_int'].map(
        lambda x: GICS_TO_MORNINGSTAR.get(x, (None, None))[1] if pd.notna(x) else None
    )

    # Clean up output columns
    result = df[[
        'ticker', 'conm', 'gsector', 'gind', 'gsubind', 'sic',
        'MorningstarSectorCode', 'MorningstarSectorName'
    ]].copy()
    result.columns = [
        'Ticker', 'CompanyName', 'GICSSector', 'GICSIndustryGroup',
        'GICSSubIndustry', 'SIC', 'MorningstarSectorCode', 'MorningstarSectorName'
    ]

    return result


def publish_sector_map(sector_df, lean_data_dir=None):
    """Write sector map CSV to lean-data.

    Args:
        sector_df: DataFrame from transform_sector_map()
        lean_data_dir: Base lean-data directory

    Returns:
        Path to the written file
    """
    if lean_data_dir is None:
        lean_data_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', 'lean-data'
        )

    sector_dir = os.path.join(lean_data_dir, 'alternative', 'sectors')
    os.makedirs(sector_dir, exist_ok=True)

    filepath = os.path.join(sector_dir, 'sector_map.csv')
    sector_df.to_csv(filepath, index=False)

    return filepath
