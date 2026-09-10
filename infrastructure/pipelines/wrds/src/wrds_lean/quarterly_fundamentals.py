"""Quarterly financial-statement pipeline from Compustat (comp.fundq).

Extracts income statement, balance sheet, and cash-flow items per fiscal
quarter and publishes a flat CSV with a point-in-time availability date for
use in local backtests and research notebooks.

Output: lean-data/alternative/fundamentals/quarterly_fundamentals.csv

Point-in-time: ``AvailableDate`` uses ``rdq`` (the actual earnings release
date) when present. When ``rdq`` is null it falls back to ``datadate`` plus a
filing lag — 45 days for fiscal quarters 1–3 (10-Q deadline) and 90 days for
fiscal quarter 4 (10-K deadline). Use ``AvailableDate``, never ``datadate``,
to align features with prices.

Cash-flow items in ``comp.fundq`` are fiscal-year-to-date cumulative (the
``*y`` columns). They are published as-is here; convert to single-quarter
flows downstream by differencing within (gvkey, fyearq).
"""

import os

import pandas as pd

from .connection import get_connection

# --- Identity / timing ---
ID_COLS = ['gvkey', 'tic', 'conm', 'datadate', 'rdq', 'fyearq', 'fqtr', 'fyr']

# --- Income statement (quarterly flows) ---
INCOME_COLS = ['saleq', 'revtq', 'cogsq', 'xsgaq', 'xrdq', 'oibdpq', 'dpq',
               'xintq', 'piq', 'txtq', 'ibq', 'niq', 'epspxq', 'cshprq']

# --- Balance sheet (point-in-time levels) ---
BALANCE_COLS = ['atq', 'actq', 'cheq', 'rectq', 'invtq', 'ppentq', 'gdwlq',
                'intanq', 'ltq', 'lctq', 'apq', 'dlttq', 'dlcq', 'ceqq', 'seqq',
                'req', 'cshoq']

# --- Cash flow (fiscal-year-to-date cumulative) ---
CASHFLOW_COLS = ['oancfy', 'capxy', 'dvy', 'sstky', 'prstkcy', 'fincfy', 'ivncfy']

# --- Market ---
MARKET_COLS = ['prccq', 'mkvaltq']

FUNDQ_COLS = ID_COLS + INCOME_COLS + BALANCE_COLS + CASHFLOW_COLS + MARKET_COLS

STANDARD_FILTERS = """
    AND indfmt = 'INDL'
    AND datafmt = 'STD'
    AND popsrc = 'D'
    AND consol = 'C'
"""


def extract_quarterly_fundamentals(tickers, start_year=1997):
    """Pull quarterly fundamentals from comp.fundq for the given tickers.

    Args:
        tickers: List of ticker strings
        start_year: First fiscal year to include (default 1997)

    Returns:
        DataFrame sorted by (tic, datadate)
    """
    conn = get_connection()
    cols = ', '.join(FUNDQ_COLS)
    sql = f"""
        SELECT {cols}
        FROM comp.fundq
        WHERE tic IN %(tickers)s
          AND fyearq >= {start_year}
          {STANDARD_FILTERS}
        ORDER BY tic, datadate
    """
    return conn.raw_sql(sql, params={'tickers': tuple(tickers)})


def extract_all_quarterly_fundamentals(start_year=2003, min_mktcap_musd=1000.0):
    """Pull quarterly fundamentals for EVERY US-dollar-reporting company above a
    market-cap floor, joined to CRSP PERMNOs through the CCM link table.

    No ticker filter. The link (``crsp_a_ccm.ccmxpf_lnkhist``, primary
    LU/LC links valid on ``datadate``) is what lets the fundamentals be
    matched to CRSP prices; rows without a valid link are dropped.

    Args:
        start_year: First fiscal year to include (default 2003 — one year of
            history before a 2004 research start for TTM / YoY features)
        min_mktcap_musd: Quarter-end ``prccq * cshoq`` floor in $ millions
            (default 1000 = $1B). Keeps the extract to ~2-3k firms per year.

    Returns:
        DataFrame with FUNDQ_COLS plus ``permno``, sorted by (gvkey, datadate)
    """
    conn = get_connection()
    cols = ', '.join(f'f.{c}' for c in FUNDQ_COLS)
    sql = f"""
        SELECT {cols}, l.lpermno AS permno
        FROM comp.fundq f
        JOIN crsp_a_ccm.ccmxpf_lnkhist l
          ON f.gvkey = l.gvkey
         AND l.linktype IN ('LU', 'LC')
         AND l.linkprim IN ('P', 'C')
         AND l.linkdt <= f.datadate
         AND (l.linkenddt IS NULL OR l.linkenddt >= f.datadate)
        WHERE f.fyearq >= {start_year}
          AND f.curcdq = 'USD'
          AND f.prccq IS NOT NULL AND f.cshoq IS NOT NULL
          AND f.prccq * f.cshoq >= {float(min_mktcap_musd)}
          {STANDARD_FILTERS}
        ORDER BY f.gvkey, f.datadate
    """
    df = conn.raw_sql(sql)
    df['permno'] = df['permno'].astype(int)
    return df


def _availability_date(row):
    """Point-in-time date a fiscal quarter's figures became public."""
    if pd.notna(row['rdq']):
        return pd.Timestamp(row['rdq'])
    lag_days = 90 if row['fqtr'] == 4 else 45
    return pd.Timestamp(row['datadate']) + pd.DateOffset(days=lag_days)


def tidy_quarterly_fundamentals(df, key='tic'):
    """Attach AvailableDate, drop duplicate (key, datadate) rows, sort.

    Compustat occasionally carries more than one row per (gvkey, datadate)
    when a filing is restated; the row with the latest ``rdq`` is kept so
    the published value is the one the market actually saw first-and-final.

    Args:
        key: identity column for de-duplication — ``'tic'`` for the
            ticker-filtered extract, ``'gvkey'`` for the broad extract (a
            ticker can be reused by different companies over time; a gvkey
            cannot). When a ``permno`` column is present, one row per
            (permno, datadate) is also enforced.
    """
    df = df.copy()
    df['datadate'] = pd.to_datetime(df['datadate'])
    df['rdq'] = pd.to_datetime(df['rdq'], errors='coerce')
    df['AvailableDate'] = df.apply(_availability_date, axis=1)

    df = (df.sort_values([key, 'datadate', 'rdq'])
            .drop_duplicates(subset=[key, 'datadate'], keep='last'))
    if 'permno' in df.columns:
        df = (df.sort_values(['permno', 'datadate', 'rdq'])
                .drop_duplicates(subset=['permno', 'datadate'], keep='last'))
    df = df.reset_index(drop=True)

    df = df.rename(columns={'tic': 'Ticker', 'conm': 'CompanyName',
                            'datadate': 'FiscalQuarterEnd',
                            'fyearq': 'FiscalYear', 'fqtr': 'FiscalQuarter',
                            'fyr': 'FiscalYearEndMonth', 'rdq': 'ReportDate'})

    lead = ['Ticker', 'CompanyName', 'gvkey', 'AvailableDate', 'ReportDate',
            'FiscalQuarterEnd', 'FiscalYear', 'FiscalQuarter', 'FiscalYearEndMonth']
    if 'permno' in df.columns:
        lead.insert(3, 'permno')
    rest = [c for c in df.columns if c not in lead]
    return df[lead + rest].sort_values(['Ticker', 'AvailableDate']).reset_index(drop=True)


def publish_quarterly_fundamentals(df, lean_data_dir=None, filename='quarterly_fundamentals.csv'):
    """Write a quarterly fundamentals CSV to lean-data/alternative/fundamentals/.

    Returns:
        Path to the written file
    """
    if lean_data_dir is None:
        lean_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'lean-data')

    out_dir = os.path.join(lean_data_dir, 'alternative', 'fundamentals')
    os.makedirs(out_dir, exist_ok=True)

    filepath = os.path.join(out_dir, filename)
    df.to_csv(filepath, index=False, date_format='%Y-%m-%d')
    return filepath
