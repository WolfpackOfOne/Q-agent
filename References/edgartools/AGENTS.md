# AGENTS.md - EdgarTools Usage Guide for QuantConnect Agents

## Purpose

This document tells AI agents how to use `edgartools` safely and consistently in this QuantConnect workspace.

Use this guide when a task involves SEC EDGAR filings, company fundamentals, XBRL facts, financial statements, insider trading filings, institutional holdings, proxy statements, fund filings, current filings, or research pipelines that pull public SEC data through the Python `edgartools` package.

This guide is intentionally verbose. It is meant to be a working playbook, not a short reference card.

Primary documentation source:

- <https://edgartools.readthedocs.io/en/latest/complete-guide/>

Related documentation to consult when needed:

- SEC compliance: <https://edgartools.readthedocs.io/en/latest/resources/sec-compliance/>
- Search and filter filings: <https://edgartools.readthedocs.io/en/latest/guides/searching-filings/>
- Filter by criteria: <https://edgartools.readthedocs.io/en/latest/guides/filtering-filings/>
- Company Facts: <https://edgartools.readthedocs.io/en/latest/guides/company-facts/>
- API reference: <https://edgartools.readthedocs.io/en/latest/api/company/>

The upstream complete guide was last observed as "Last updated: February 2026". If a task depends on exact current API behavior, re-check the live docs before implementing.

---

## Workspace Scope

This guide applies inside:

```text
/path/to/Q-agent
```

It does not replace the workspace-level `AGENTS.md`. It supplements it for EDGAR and `edgartools` work.

When working inside a project under `MyProjects/<ProjectName>`, project-level files still take precedence:

- `MyProjects/<ProjectName>/AGENTS.md`
- `MyProjects/<ProjectName>/claude.md`
- `MyProjects/<ProjectName>/README.md`
- `MyProjects/<ProjectName>/docs/`

Do not edit `Lean/`.

Do not modify shared LEAN config, project `config.json`, ObjectStore schemas, trading logic, live trading settings, risk limits, universe selection, or strategy parameters unless the user explicitly asks.

---

## What EdgarTools Is For

`edgartools` is a Python package for accessing SEC EDGAR data and converting filings into structured Python objects.

Use it for:

- Pulling company filings by ticker, CIK, form type, date, accession number, or exchange
- Reading clean filing text, markdown, or raw HTML
- Parsing typed filing objects through `filing.obj()`
- Extracting financial statements from 10-K and 10-Q filings
- Querying company facts and XBRL concepts
- Building pandas DataFrames from statements or filing collections
- Tracking insider trades from Form 4 filings
- Inspecting institutional holdings from 13F-HR filings
- Reviewing fund portfolios from N-PORT and N-MFP filings
- Parsing proxy statements such as DEF 14A
- Monitoring current filings through `get_current_filings()`
- Creating research datasets for notebooks, offline analysis, or later QuantConnect ingestion

Do not use `edgartools` for:

- Placing trades
- Replacing QuantConnect market data subscriptions
- Pulling non-SEC data
- Scraping pages outside SEC/EDGAR through ad hoc requests
- Real-time live-trading decisions unless the user has explicitly approved the operational design and latency assumptions
- Silent changes to algorithm behavior

---

## Core Safety Rule

`edgartools` should usually live in research, data preparation, or offline feature engineering code.

In this workspace, avoid adding `edgartools` imports directly to production QuantConnect algorithm runtime files unless the user explicitly asks and understands the consequences. LEAN cloud/runtime environments may not have the package installed, SEC network access may be unavailable or unsuitable, and live SEC requests can make backtests non-deterministic.

Preferred pattern:

1. Use `edgartools` in a research script or notebook.
2. Normalize and validate the resulting dataset.
3. Save a stable artifact into an approved project data location or ObjectStore workflow.
4. Consume the stable artifact from the algorithm.

For QuantConnect strategy work, keep the strategy deterministic and data-versioned.

---

## Installation

The package name to install is:

```bash
pip install edgartools
```

The Python import package is:

```python
from edgar import Company
```

The package name and import name differ. This matters.

If you see an import error such as:

```text
ImportError: cannot import name 'get_filings' from 'edgar'
```

then the wrong package may be installed. The intended package is `edgartools`, not an unrelated package named `edgar`.

Do not uninstall or install packages in the shared environment without user approval. The shared venv is used by multiple projects.

Preferred environment in this workspace:

```bash
cd /path/to/Q-agent
source venv/bin/activate
python -c "import edgar; print(edgar.__file__)"
```

If `edgartools` is missing and the task requires it, ask for approval before installing into the shared `venv`.

---

## SEC Compliance Requirements

Automated EDGAR access must identify the user or organization. Always set an identity before making SEC requests.

Preferred pattern for scripts:

```python
from edgar import set_identity

set_identity("Your Name your.email@example.com")
```

More explicit pattern:

```python
from edgar import set_identity

set_identity(
    name="Your Name",
    email="your.email@example.com",
    organization="Your Organization",
)
```

Preferred pattern for reusable local workflows:

```bash
export EDGAR_IDENTITY="Your Name your.email@example.com"
```

or, when using the explicit identity fields supported by the library:

```bash
export EDGAR_NAME="Your Name"
export EDGAR_EMAIL="your.email@example.com"
```

Do not hard-code a real personal email address into committed project files unless the user explicitly asks. Prefer environment variables, `.env` files that are ignored, shell profiles, or local notebook setup cells excluded from commits.

When creating examples, use placeholders:

```python
set_identity("Your Name your.email@example.com")
```

Before running high-volume jobs, ensure identity is configured. If identity is missing, stop and ask the user what identity to use or explain how to set it.

---

## Rate Limits and Polite Access

The SEC expects automated clients to avoid excessive request rates. The edgartools docs describe a conservative default of up to 10 requests per second with built-in delays and retries for rate-limit responses.

Agent rules:

- Do not write tight loops that fetch hundreds or thousands of filings without caching, limits, and delays.
- For batch jobs, set a lower rate limit or add explicit sleeps.
- For production-style or repeated research jobs, enable local storage.
- Prefer company-level filing history calls when analyzing one company.
- Prefer filtered queries when criteria are known in advance.
- Avoid excessive concurrency against SEC endpoints.
- If HTTP 429 or 403 occurs, reduce request rate, back off, and do not keep retrying aggressively.
- For large historical jobs, prefer off-peak hours and resumable pipelines.

Conservative rate limit example:

```python
from edgar import set_rate_limit

set_rate_limit(5)
```

Batch delay example:

```python
import time

for filing in filings:
    process_filing(filing)
    time.sleep(0.2)
```

Use `head()`, `latest()`, or explicit date windows while developing:

```python
filings = Company("AAPL").get_filings(form="10-K").head(3)
```

Never test a new extraction routine by immediately running it across the entire market.

---

## Local Storage and Caching

Use local storage for repeated workflows so the same filings are not repeatedly fetched from SEC servers.

The compliance guide shows:

```python
from edgar import enable_local_storage

enable_local_storage("/path/to/storage")
```

Some edgartools configuration docs also refer to:

```python
from edgar import use_local_storage

use_local_storage(True)
```

Because the API can evolve, verify the installed version before relying on one name in durable code:

```bash
python - <<'PY'
import edgar
print(edgar.__file__)
print("enable_local_storage", hasattr(edgar, "enable_local_storage"))
print("use_local_storage", hasattr(edgar, "use_local_storage"))
PY
```

Workspace cache guidance:

- Use a project-specific cache path for repeatable research.
- Do not write caches into `Lean/`.
- Do not commit large downloaded SEC artifacts unless explicitly requested.
- Do not place bulky raw filings in algorithm source directories.
- Prefer `References/`, `research/`, or project `data/raw/` paths that are already ignored or documented.
- Confirm `.gitignore` before generating large data.

Example cache location for research:

```text
MyProjects/<ProjectName>/research/.edgar-cache/
```

Example cache location for shared reference experiments:

```text
References/edgartools/.cache/
```

If a cache contains personal information, raw filings, or large files, treat it as local generated data unless the user gives different instructions.

---

## Basic Imports

Common imports:

```python
from edgar import Company, get_filings, get_current_filings, set_identity
```

Use pandas only when needed:

```python
import pandas as pd
```

Do not import `AlgorithmImports` in pure edgartools research modules. Keep EDGAR extraction code independent from QuantConnect runtime code unless a project explicitly requires an adapter.

---

## Company Lookup

Use `Company` as the primary entry point for company-specific workflows.

By ticker:

```python
from edgar import Company

company = Company("AAPL")
```

By CIK:

```python
company = Company(320193)
```

Useful metadata:

```python
company.name
company.cik
company.sic_code
company.sic_description
company.shares_outstanding
company.public_float
```

Agent guidance:

- Prefer CIK for durable pipelines because tickers can change.
- Accept ticker input for interactive research because it is convenient.
- Persist both ticker and CIK in output datasets when possible.
- Do not assume every SEC filer has a current ticker.
- Do not assume all company metadata fields are present.
- Handle missing values explicitly.

---

## Filing Collections

Get a company's filing history:

```python
filings = Company("MSFT").get_filings()
```

Get only annual reports:

```python
tenks = Company("MSFT").get_filings(form="10-K")
```

Use collection operations to limit and select:

```python
recent = tenks.head(5)
latest = tenks[0]
```

Many examples use `filings[0]` for the latest filing. In production-style code, prefer clearer selection helpers if available in the installed version, and always handle empty results:

```python
filings = Company("MSFT").get_filings(form="10-K", amendments=False)

if len(filings) == 0:
    raise ValueError("No 10-K filings found for MSFT")

latest_10k = filings[0]
```

Agent guidance:

- Always decide whether amendments should be included.
- For historical financial modeling, usually start with `amendments=False` unless amended filings are part of the research question.
- For legal or restatement analysis, amendments may be essential.
- For broad market pulls, filter early.
- For one-company pulls, `Company(...).get_filings()` is usually clearer than global filing index searches.

---

## Global Filing Search

Use global `get_filings()` when the task is filing-centric across many companies.

Examples:

```python
from edgar import get_filings

recent_filings = get_filings()
annual_reports = get_filings(form="10-K").head(20)
financial_reports = get_filings(form=["10-K", "10-Q"])
```

By date:

```python
filings_on_date = get_filings(filing_date="2024-01-15")
q1_filings = get_filings(filing_date="2024-01-01:2024-03-31")
from_date = get_filings(filing_date="2024-01-01:")
through_date = get_filings(filing_date=":2024-12-31")
```

By year and quarter:

```python
filings_2024 = get_filings(2024)
q4_2024 = get_filings(2024, 4)
```

Important date distinction:

- `year` and `quarter` refer to filing submission date, not the fiscal period covered by the filing.
- A fiscal-year 10-K can be filed in the following calendar year.
- If the user asks for fiscal-year data, inspect XBRL facts or filing metadata, not just submission year.

---

## Filtering Strategy

There are two common filtering styles:

1. Filter while retrieving:

```python
filings = get_filings(
    year=2024,
    quarter=1,
    form="10-K",
    filing_date="2024-01-01:2024-01-31",
    amendments=False,
)
```

2. Filter an existing collection:

```python
filings = get_filings(2024, 1)
tenks = filings.filter(form="10-K")
```

Prefer filtering while retrieving when the criteria are known. It is more efficient and clearer.

Use post-filtering when:

- A collection has already been fetched
- The workflow is interactive
- You need multiple derived subsets from one base collection
- The criteria depend on fields inspected after retrieval

Common criteria:

- `form`
- `filing_date`
- `amendments`
- `cik`
- `ticker`
- `exchange`
- `accession_number`
- `file_number`
- `is_xbrl`

Always confirm exact parameter names against installed docs or API introspection when adding durable code.

---

## Opening and Reading Filings

Once you have a filing:

```python
filing = Company("AAPL").get_filings(form="10-K")[0]

text = filing.text()
markdown = filing.markdown()
html = filing.html()
```

Use cases:

- `text()` for NLP, search, keyword extraction, sentiment analysis, and simple RAG ingestion
- `markdown()` for LLM-readable document processing and chunking
- `html()` when layout, tables, or source markup matter

Avoid `filing.open()` in automated agent workflows unless the user explicitly asks to open a browser. It launches a browser and is not suitable for headless validation.

Agent guidance:

- For text analysis, store accession number, CIK, form, filing date, and source URL or accession metadata with extracted text.
- Do not strip metadata away from filing text artifacts.
- Do not rely on raw filing text alone for audited numeric facts when structured XBRL data is available.
- For table-heavy sections, inspect whether typed objects or XBRL statements are better than text parsing.

---

## Typed Filing Objects

Use:

```python
obj = filing.obj()
```

This converts supported filings into structured Python objects.

Common 10-K style access:

```python
tenk = Company("AAPL").get_filings(form="10-K")[0].obj()

business = tenk.business_description
risk_factors = tenk.risk_factors
mda = tenk.mda
financials = tenk.financials
```

Financial statement access from a filing object:

```python
income = tenk.financials.income_statement()
balance = tenk.financials.balance_sheet()
cashflow = tenk.financials.cash_flow_statement()
```

Agent guidance:

- Prefer typed objects over regex or manual HTML parsing.
- Wrap `filing.obj()` in error handling for broad batch jobs because not every filing may parse cleanly.
- Log accession numbers for parse failures.
- Do not assume every form has the same object fields.
- For unsupported forms, fall back to `text()`, `markdown()`, attachments, or XBRL APIs as appropriate.

---

## Financial Statements

For a single filing:

```python
company = Company("AAPL")
tenk = company.get_filings(form="10-K", amendments=False)[0].obj()

income = tenk.financials.income_statement()
balance = tenk.financials.balance_sheet()
cashflow = tenk.financials.cash_flow_statement()
```

Convert a statement to pandas:

```python
income_df = income.to_dataframe()
```

For multi-period statements:

```python
company = Company("MSFT")
financials = company.get_financials()

income = financials.income_statement()
balance = financials.balance_sheet()
```

Company-level enhanced methods may also be available:

```python
company = Company("AAPL")

income_stmt = company.income_statement(periods=4, annual=True)
balance_sheet = company.balance_sheet(periods=4)
cash_flow = company.cashflow_statement(periods=5, annual=True)
```

DataFrame output:

```python
income_df = company.income_statement(periods=4, annual=True, as_dataframe=True)
```

Agent guidance:

- Use annual statements for long-term factor research unless the user asks for quarterly data.
- Use quarterly statements when modeling reporting cadence, surprises, short-horizon changes, or trailing metrics.
- Preserve period labels and filing dates.
- Store units and scaling assumptions.
- Do not mix concise display strings with numeric analysis.
- Use DataFrame output or `to_dataframe()` for calculations.
- Prefer full precision numeric fields over formatted values.
- Verify whether rows are indexed by labels or XBRL concepts before writing `.loc[...]` code.

---

## Company Facts and XBRL Concepts

Use company facts for historical XBRL data.

Basic:

```python
company = Company("GOOG")
facts = company.get_facts()

revenue = facts.get_revenue()
net_income = facts.get_net_income()
assets = facts.get_total_assets()
equity = facts.get_shareholders_equity()
```

Specific concept:

```python
accounts_payable = facts.get_concept("AccountsPayableCurrent")
revenue_series = facts.time_series("Revenues")
```

Company-level statement methods:

```python
income = company.income_statement(periods=4)
df = income.to_dataframe()
```

LLM context, when useful for summarization:

```python
context = income.to_llm_context()
```

Agent guidance:

- Use XBRL concepts for numeric research when possible.
- Do not assume every company reports the same concept.
- Handle taxonomy differences and missing values.
- Validate signs, units, dimensions, and period lengths.
- For ratios, explicitly document numerator, denominator, period, and whether values are annual or quarterly.
- Be careful with restatements and amended filings.
- When building factor datasets, retain enough metadata to reproduce each value.

Minimum metadata to preserve:

- ticker
- CIK
- company name
- concept
- label
- value
- unit
- fiscal year
- fiscal period
- period start
- period end
- filing date
- form
- accession number
- frame or dimension fields if present

---

## Insider Trading

Use Form 4 filings for insider transactions.

Example:

```python
from edgar import Company
import pandas as pd

form4s = Company("NVDA").get_filings(form="4").head(20)
transactions = pd.concat(
    [filing.obj().to_dataframe().fillna("") for filing in form4s],
    ignore_index=True,
)
```

Agent guidance:

- Treat Form 4 data as event data, not daily bar data.
- Preserve filing date, transaction date, reporting owner, issuer CIK, accession number, transaction code, direct/indirect ownership, share amount, price, and post-transaction holdings when available.
- Do not interpret all sales as bearish. Many sales are planned, tax-related, option-related, or compensation-related.
- Do not interpret all purchases as bullish without context.
- Be explicit about whether derivatives, option exercises, and non-open-market transactions are included.
- Avoid simplistic signals unless the user asks for exploratory work.

---

## Institutional Holdings: 13F

Use 13F-HR for institutional manager holdings.

Example:

```python
manager = Company(1423053)
thirteenf = manager.get_filings(form="13F-HR")[0].obj()

holdings = thirteenf.holdings
changes = thirteenf.compare_holdings()
history = thirteenf.holding_history(periods=4)
```

Agent guidance:

- 13F filings are delayed and do not represent real-time holdings.
- 13F reports long U.S. equity positions and certain securities; they omit many shorts, derivatives, cash, and non-reportable assets.
- Always preserve report period and filing date separately.
- Do not treat 13F as complete portfolio exposure.
- Use CUSIP/ticker mapping carefully; ticker symbols can be stale or ambiguous.
- For investment research, explain the delay and coverage limitations.

---

## Investment Funds

N-PORT example:

```python
fund = Company("VANGUARD INDEX FUNDS")
nport = fund.get_filings(form="NPORT-P")[0].obj()
investments = nport.investments
```

N-MFP example:

```python
mmf = fund.get_filings(form="N-MFP2")[0].obj()
```

Agent guidance:

- Fund filings can have complex issuer, series, and class structures.
- Preserve fund identifiers, series identifiers, period dates, and accession numbers.
- Do not assume fund names are unique.
- Inspect the typed object fields before normalizing.
- For fund holdings, preserve asset category, issuer, identifier, value, balance, currency, and maturity where available.

---

## Proxy Statements and Executive Compensation

DEF 14A example:

```python
proxy = Company("AAPL").get_filings(form="DEF 14A")[0].obj()

ceo_name = proxy.peo_name
ceo_total_comp = proxy.peo_total_comp
executive_compensation = proxy.executive_compensation
```

Agent guidance:

- Proxy data can be inconsistent across issuers and years.
- Validate compensation table columns before calculations.
- Preserve year, person name, role, total compensation, salary, stock awards, option awards, incentive compensation, pension changes, and all other compensation where available.
- Do not compare compensation across companies without documenting differences in fiscal years and table definitions.

---

## Current Filings

Use current filings for monitoring new SEC submissions.

Example:

```python
from edgar import get_current_filings

filings = get_current_filings()
eightks = filings.filter(form="8-K")
tenks = filings.filter(form="10-K")
```

Agent guidance:

- Current filings are useful for alerting and monitoring, not deterministic historical backtests.
- For a reproducible dataset, save the timestamp of retrieval and the filing metadata.
- Do not wire current filing pulls into live trading behavior without explicit user approval.
- For recurring monitors, implement caching, state tracking, idempotent processing, and rate limiting.

---

## AI and MCP Integration

The edgartools documentation describes an MCP server that can expose company research, filing search, financial analysis, ownership tracking, and comparison tools to AI clients.

Command examples from the docs:

```bash
edgartools-mcp
```

or:

```bash
uvx edgartools-mcp
```

Agent guidance:

- Do not add or configure MCP servers without explicit user approval.
- Do not run long-lived MCP services unless the user asks.
- If the user asks for natural-language SEC research integration, first determine whether they want local Python scripts, MCP, notebooks, or a web/API service.
- For this QuantConnect workspace, local Python scripts and notebooks are usually simpler and easier to reproduce.

---

## Data Engineering Patterns

Prefer explicit, reproducible extraction functions.

Recommended shape:

```python
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from edgar import Company


@dataclass(frozen=True)
class FilingRequest:
    ticker: str
    form: str
    limit: int = 5
    amendments: bool = False


def fetch_filing_metadata(request: FilingRequest) -> pd.DataFrame:
    company = Company(request.ticker)
    filings = company.get_filings(
        form=request.form,
        amendments=request.amendments,
    ).head(request.limit)

    rows = []
    for filing in filings:
        rows.append(
            {
                "ticker": request.ticker,
                "cik": company.cik,
                "company_name": company.name,
                "form": filing.form,
                "filing_date": filing.filing_date,
                "accession_number": filing.accession_number,
            }
        )

    return pd.DataFrame(rows)
```

Agent guidance:

- Keep network access at the edges.
- Keep transformation logic pure when possible.
- Return DataFrames or dataclasses from extraction functions.
- Avoid burying SEC calls deep inside strategy logic.
- Make functions small enough to test with tiny samples.
- Add a `limit` parameter for development.
- Add idempotent output writes for batch jobs.
- Log enough metadata to resume failed runs.

---

## Error Handling

Expected failure modes:

- Missing package
- Wrong `edgar` package installed
- Missing SEC identity
- HTTP 429 rate limit responses
- HTTP 403 temporary block or forbidden response
- SEC maintenance or transient network errors
- Empty filing collections
- Unsupported filing object for `filing.obj()`
- Missing XBRL concepts
- DataFrame schema differences across filing types or versions
- Changed package API between installed version and online docs

Minimum handling for one-company scripts:

```python
from edgar import Company

company = Company("AAPL")
filings = company.get_filings(form="10-K", amendments=False)

if len(filings) == 0:
    raise ValueError("No original 10-K filings found for AAPL")

filing = filings[0]
```

Minimum handling for batch parse jobs:

```python
rows = []
errors = []

for filing in filings:
    try:
        obj = filing.obj()
        rows.append(extract_row(obj, filing))
    except Exception as exc:
        errors.append(
            {
                "form": getattr(filing, "form", None),
                "filing_date": getattr(filing, "filing_date", None),
                "accession_number": getattr(filing, "accession_number", None),
                "error": repr(exc),
            }
        )
```

Agent guidance:

- Do not swallow exceptions silently.
- Preserve accession numbers for failures.
- For research notebooks, display a compact failure summary.
- For scripts, write failure logs to a clear local artifact.
- For durable pipelines, make failures resumable.

---

## Validation

For code changes:

```bash
python -m py_compile path/to/script.py
```

For import and installed-version checks:

```bash
cd /path/to/Q-agent
source venv/bin/activate
python - <<'PY'
import edgar
print(edgar.__file__)
print(getattr(edgar, "__version__", "unknown"))
PY
```

For a minimal SEC access smoke test, use a tiny request:

```python
from edgar import Company, set_identity

set_identity("Your Name your.email@example.com")
company = Company("AAPL")
filings = company.get_filings(form="10-K", amendments=False).head(1)
print(filings)
```

Do not run broad historical pulls as a validation step.

For DataFrame-producing code, validate:

- row count is nonzero when expected
- required columns exist
- date columns parse correctly
- numeric columns are numeric, not formatted strings
- CIKs are preserved as strings or normalized consistently
- accession numbers are present
- duplicates are either expected or removed intentionally
- fiscal periods and filing dates are not confused

---

## QuantConnect Integration Guidance

When edgartools data is intended for a QuantConnect algorithm, build a boundary between data extraction and algorithm execution.

Preferred architecture:

```text
research or scripts/
    fetch SEC data with edgartools
    normalize to stable schema
    write versioned artifact

domain/ or data loader
    pure parsing and validation of artifact

models/
    consume already-normalized signals/features

main.py
    wire components only
```

For this workspace's atomic structure:

- EDGAR fetch code is infrastructure or research code.
- SEC parsing helpers can be molecules if pure and single-domain.
- DTOs and schema constants can be atoms.
- Strategy models should not make live SEC requests.
- `main.py` should not contain edgartools extraction logic.

Examples of acceptable locations:

```text
MyProjects/<ProjectName>/research/sec_fundamentals.ipynb
MyProjects/<ProjectName>/scripts/fetch_edgar_fundamentals.py
MyProjects/<ProjectName>/infrastructure/sec/edgar_client.py
MyProjects/<ProjectName>/domain/fundamentals/schema.py
```

Examples to avoid:

```text
MyProjects/<ProjectName>/main.py              # direct SEC fetch in algorithm runtime
MyProjects/<ProjectName>/models/alpha.py      # direct network requests inside signal generation
Lean/...                                      # never edit
```

If the user asks to add an EDGAR-derived signal:

1. Ask whether they want an offline dataset or live retrieval.
2. Explain that offline/versioned data is preferred for deterministic backtests.
3. Define the schema and update docs.
4. Add a small extraction script or notebook first.
5. Validate a tiny sample.
6. Only then wire the normalized artifact into strategy logic, with explicit approval if behavior changes.

---

## Output Schema Recommendations

For filing metadata:

```text
ticker
cik
company_name
form
filing_date
report_date
accession_number
file_number
is_xbrl
is_amendment
source_url
retrieved_at_utc
```

For financial statements:

```text
ticker
cik
company_name
statement_type
concept
label
value
unit
fiscal_year
fiscal_period
period_start
period_end
filing_date
form
accession_number
amended
retrieved_at_utc
```

For insider transactions:

```text
issuer_ticker
issuer_cik
issuer_name
owner_name
owner_cik
relationship
form
filing_date
transaction_date
transaction_code
security_title
shares
price
direct_or_indirect
shares_owned_after
accession_number
retrieved_at_utc
```

For 13F holdings:

```text
manager_name
manager_cik
report_period
filing_date
accession_number
issuer_name
cusip
ticker
class
value
shares_or_principal
put_call
investment_discretion
voting_sole
voting_shared
voting_none
retrieved_at_utc
```

Agent guidance:

- Add columns instead of renaming or removing when schemas are already used downstream.
- Document schema changes.
- Keep raw extracted values separate from derived factors.
- Store retrieval timestamp for reproducibility.
- Include source accession number in every derived dataset.

---

## Common Research Workflows

### Pull Latest 10-K Income Statement

```python
from edgar import Company, set_identity

set_identity("Your Name your.email@example.com")

tenk = Company("AAPL").get_filings(form="10-K", amendments=False)[0].obj()
income = tenk.financials.income_statement()
df = income.to_dataframe()
print(df.head())
```

### Pull Multi-Year Company Financials

```python
from edgar import Company, set_identity

set_identity("Your Name your.email@example.com")

company = Company("MSFT")
financials = company.get_financials()
income = financials.income_statement()
balance = financials.balance_sheet()

income_df = income.to_dataframe()
balance_df = balance.to_dataframe()
```

### Pull Recent 8-K Filings

```python
from edgar import get_current_filings, set_identity

set_identity("Your Name your.email@example.com")

filings = get_current_filings()
eightks = filings.filter(form="8-K")

for filing in eightks.head(10):
    print(filing.company_name, filing.filing_date, filing.accession_number)
```

### Pull Clean 10-K Text for NLP

```python
from edgar import Company, set_identity

set_identity("Your Name your.email@example.com")

filing = Company("JPM").get_filings(form="10-K", amendments=False)[0]
text = filing.text()
metadata = {
    "form": filing.form,
    "filing_date": filing.filing_date,
    "accession_number": filing.accession_number,
}
```

### Pull Form 4 Transactions

```python
from edgar import Company, set_identity
import pandas as pd

set_identity("Your Name your.email@example.com")

form4s = Company("TSLA").get_filings(form="4").head(10)
frames = []

for filing in form4s:
    ownership = filing.obj()
    df = ownership.to_dataframe()
    df["accession_number"] = filing.accession_number
    df["filing_date"] = filing.filing_date
    frames.append(df)

transactions = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
```

### Pull Latest 13F Holdings

```python
from edgar import Company, set_identity

set_identity("Your Name your.email@example.com")

manager = Company(1423053)
filing = manager.get_filings(form="13F-HR", amendments=False)[0]
thirteenf = filing.obj()
holdings = thirteenf.holdings
```

---

## Anti-Patterns

Do not do this:

```python
for ticker in all_tickers:
    filing = Company(ticker).get_filings(form="10-K")[0]
    text = filing.text()
```

without:

- identity
- rate limiting
- caching
- error handling
- limits during development
- accession metadata
- resumability

Do not do this:

```python
from edgar import Company

class MyAlgorithm(QCAlgorithm):
    def OnData(self, data):
        facts = Company("AAPL").get_facts()
```

Network-bound SEC data access inside `OnData` is inappropriate for deterministic QuantConnect algorithms.

Do not parse financial statement numbers from `filing.text()` with regex when XBRL facts or typed financial statements are available.

Do not assume:

- latest filing means latest fiscal period
- ticker means stable company identity
- all companies report the same XBRL concepts
- all statement rows are directly comparable across companies
- all filings parse successfully
- 13F holdings are real-time
- Form 4 transaction intent is obvious
- SEC data is adjusted for splits or restatements in the way your model expects

---

## When to Ask the User

Ask before:

- Installing or upgrading `edgartools` in the shared venv
- Running broad SEC pulls
- Creating large local caches
- Adding edgartools to a production algorithm dependency path
- Changing QuantConnect strategy behavior based on EDGAR data
- Writing derived EDGAR data into a project data directory that may be committed
- Changing ObjectStore keys or schemas
- Using a real name/email identity in committed code
- Running an MCP server

Do not ask before:

- Reading documentation
- Creating a small guide or example file
- Writing placeholder code with placeholder identity values
- Running a tiny local syntax check
- Inspecting installed package availability

---

## Documentation Expectations

When adding edgartools workflows to a project, update project docs with:

- Purpose of the SEC dataset
- Source forms used
- Extraction script or notebook path
- SEC identity configuration method
- Cache path
- Output artifact path
- Output schema
- Refresh cadence
- Known limitations
- How to validate
- Whether amendments are included
- How filing date and fiscal period are handled

For strategy-impacting datasets, document:

- How the feature is computed
- When the data would have been available historically
- Any lag applied to avoid lookahead bias
- Whether restatements are included
- How missing filings are handled
- How ticker changes and CIK mapping are handled

---

## Lookahead Bias and Research Integrity

SEC data can easily introduce lookahead bias.

Rules:

- Use filing date, not fiscal period end date, as the earliest availability date.
- Apply an additional conservative lag if the workflow assumes processing time.
- Do not use restated values before their filing date.
- Preserve accession number so the exact source filing is auditable.
- For point-in-time datasets, avoid replacing historical values with later restated values unless the research explicitly studies restatements.
- Do not join SEC facts to price data on fiscal period end date unless you intentionally lag by filing availability.

Example:

```text
Fiscal period end: 2024-12-31
Filing date:       2025-02-15
Usable from:       2025-02-16 or later, depending on the research rule
```

For QuantConnect backtests, build features keyed by the date they became available, not the fiscal date they describe.

---

## Minimal Agent Checklist

Before writing edgartools code:

- Read project docs if inside `MyProjects/<ProjectName>`.
- Confirm whether the task is research, data engineering, or algorithm runtime.
- Confirm whether SEC requests are needed or existing artifacts can be used.
- Check package availability in `venv` if execution is required.
- Set or require SEC identity.
- Limit request scope.
- Use caching for repeated pulls.
- Preserve accession metadata.
- Handle empty results and parse failures.
- Avoid strategy behavior changes without explicit approval.

Before finalizing:

- Run syntax validation for changed Python files.
- Run only a tiny smoke test if network access and identity are configured.
- Document any command that was not run.
- Report output paths and limitations.
- Do not claim broad data correctness from a tiny smoke test.

---

## Quick Decision Table

| Need | Preferred EdgarTools API |
|------|--------------------------|
| One company's filings | `Company("TICKER").get_filings(...)` |
| Many companies by form/date | `get_filings(...)` with filters |
| Latest submissions today | `get_current_filings()` |
| Clean filing text | `filing.text()` |
| LLM-readable filing document | `filing.markdown()` |
| Raw filing markup | `filing.html()` |
| Structured filing object | `filing.obj()` |
| Single-filing statements | `filing.obj().financials...` |
| Multi-period statements | `Company(...).get_financials()` or company statement methods |
| Historical XBRL concepts | `Company(...).get_facts()` |
| Insider transactions | Form `4`, then `filing.obj()` |
| Institutional holdings | Form `13F-HR`, then `filing.obj()` |
| Fund holdings | Forms such as `NPORT-P` or `N-MFP2` |
| Proxy compensation | Form `DEF 14A`, then `filing.obj()` |

---

## Final Notes

The most important implementation habit is to keep SEC retrieval separate from trading logic. Use `edgartools` to create transparent, versioned, reproducible research artifacts. Then consume those artifacts through the normal QuantConnect project architecture.

When in doubt, make the data boundary explicit, preserve accession-level provenance, and use filing dates to prevent lookahead bias.
