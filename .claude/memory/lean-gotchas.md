# LEAN Gotchas

Durable LEAN, LEAN CLI, QuantConnect cloud, Docker, and research-container gotchas.

Include symptoms and the confirmed fix. Do not store secrets or config values.

## Shared signals — `domain/signals/` is a symlink, edit the shared source

Workspace convention: pure-Python signal atoms live in `MyProjects/shared/signals/`. Projects consume them via relative symlinks inside `domain/signals/`. `lean cloud push` follows symlinks and uploads the file *content* — QC cloud never sees the link, so the cloud build behaves the same as a local clone.

Rules:
- Edit the file in `shared/signals/`, never the symlink copy inside a project. Edits to the link silently modify shared source.
- Symlink path from a project two levels deep (`<Project>/domain/signals/foo.py`) is `../../../shared/signals/foo.py`. The third `..` is necessary.
- Shared atoms must be importable without `from AlgorithmImports import *` — they should run under a plain venv with just `pandas` + `numpy`. Add a synthetic-data unit test before symlinking into a project.

First use: `MyProjects/ElectionIndustryBeta/domain/signals/election_beta.py → ../../../shared/signals/election_beta.py`.

## Polymarket Pipeline — Resolved Markets Need fidelity=1440

Symptom: `run_prices_pipeline.py` writes empty CSV files for closed/resolved markets.

Cause: Default `fidelity=60` (hourly) returns 0 points from the CLOB `/prices-history` endpoint for resolved markets. Only `interval=max, fidelity=1440` (daily) returns data.

Fix:
```bash
python scripts/run_prices_pipeline.py --fidelity 1440
```

## Polymarket Pipeline — Tag Filter Broken (May 2026)

Symptom: `run_markets_pipeline.py` with default filter returns 0 markets.

Cause: Polymarket events no longer expose tag slugs (`events[].tags[].slug` is empty). The `DEFAULT_TAG_FILTER` (`fed`, `macro`, `economics`, etc.) matches nothing.

Workaround: Paginate the events endpoint and filter client-side by event `title`:
```python
for page in range(50):
    r = requests.get('https://gamma-api.polymarket.com/events',
        params={'limit': 100, 'offset': offset}, timeout=30)
    for ev in r.json():
        if any(t in (ev.get('title') or '').lower() for t in FED_TERMS):
            # keep this event's markets
```

## Polymarket API — search= Parameter Ignores Keywords

Symptom: `GET /markets?search=fed+chair` returns unrelated trending markets (e.g. GTA VI).

Cause: The `search` param on both `/markets` and `/events` returns trending results, not keyword matches.

Workaround: Full pagination + client-side text filter on `question` or `title` fields.

## marimo — MultipleDefinitionError from ANY Shared Top-Level Variable

Symptom: Cells that define the same variable name at the top level get `MultipleDefinitionError`. This includes loop variables (`for ax in ...`), plot handles (`fig`, `ax`), temporary DataFrames (`df`), and any other assignment.

Cause: marimo treats EVERY top-level assignment as a cell export. Two cells that both assign `fig = ...` or `ax = ...` or `df = ...` will conflict, even if the variables are logically independent.

Fix: Use unique names in every cell. Common pattern for plots:
```python
# Cell A (histogram)
fig_hist, ax_hist = plt.subplots(1, 3, figsize=(15, 4))
h_hyg = df_results["HYG"].dropna()  # not h or hyg
ax_hist[0].hist(h_hyg, ...)
fig_hist  # display

# Cell B (3D scatter)
fig_3d = plt.figure(figsize=(12, 6))
ax_3d = fig_3d.add_subplot(111, projection="3d")
fig_3d  # display
```

For loop variables, prefix with `_`:
```python
for _col in poly_df.columns:   # _ prefix = not exported
    _valid = aligned[_col].dropna()
```

## marimo — Function Cells vs Statement Cells: When Code Doesn't Execute

Symptom: A cell contains valid plot code but nothing renders. The cell appears as just a function definition in the notebook.

Cause: If a cell's code is wrapped in `def _(params): ...`, marimo treats it as a function cell. The body only executes when marimo detects a downstream cell that consumes one of its returned variables. If nothing consumes the return value, the function body never runs.

Fix: For cells that produce visual output (plots, markdown), use statement cells (no function wrapper). A bare `fig_hist` at the end of a statement cell will display the figure. Only use function cells when you need to explicitly declare parameters and return values for the reactive graph.

Rule of thumb: **statement cells for display, function cells for data transformations that feed downstream cells**.

## marimo — Statement Cells Cannot Access Function Cell Returns

Symptom: A statement cell raises `NameError: name 'df_results' is not defined` even though an upstream function cell returns `(df_results,)`.

Cause: Statement cells (no `def _()`) can only see variables defined by other statement cells at module scope. They cannot receive values from function cells' return tuples — that mechanism only works between function cells.

Fix: Don't mix paradigms. Either make all cells functions (and ensure every return is consumed downstream) or make all cells statements (and ensure unique variable names). For simple analysis notebooks, all-statement is simpler.

## marimo — Kill Server Before Rewriting Notebook File

Symptom: `Write` tool fails with "file modified since read" or edits silently vanish.

Cause: The marimo kernel holds its own copy of the notebook in memory and periodically saves it to disk, overwriting external edits. The `Write` and `Edit` tools see a stale version.

Fix: Always `pkill -f "marimo edit.*filename"` before rewriting the `.py` file. Then restart the server. Alternative: use `ctx.edit_cell()` through `execute-code.sh` to mutate cells in the live kernel.

## marimo — Use Bash Heredoc to Write Notebook Files

Symptom: `Write` tool fails because the file was reformatted by marimo since last read.

Fix: Use `cat > file << 'EOF'` via the Bash tool instead of the Write tool. This bypasses the "must read before write" check and avoids exact-match issues from marimo's reformatting.

## Polymarket CLOB — Old Resolved Markets Return Flat Post-Resolution Prices

Symptom: Price CSVs for resolved markets (e.g. 2022 ETH Merge markets) contain only `price=0.5` from 2023 onward — no pre-event probability history.

Cause: The CLOB `/prices-history` endpoint only retains data from ~late 2022 onwards. Pre-resolution probability series are not accessible for old markets.

Fix: Check `s.std() > 0.01` before using any series. For event studies on pre-2023 events, the data simply is not available via the public CLOB API.

## Polymarket API — Pagination Cap is 100 Per Request

Symptom: Setting `limit=500` still returns exactly 100 markets. The `offset` param does work for pagination.

Fix: Always use `limit=100` and paginate with `offset += 100`. Break when `len(batch) == 0`, not `len(batch) < limit`.

## Binance API — HTTP 451 Geo-Block in the US

Symptom: `ccxt` raises `ExchangeNotAvailable: binance GET .../exchangeInfo 451 Service unavailable from a restricted location`.

Cause: Binance geo-blocks US IP addresses on its main API. Binance.US is a separate entity with a different ccxt exchange ID.

Fix: Use Coinbase or Kraken for US-based pulls. Do not include Binance in US pipelines without a VPN or proxy.

## marimo — Infrastructure Venv Does Not Contain marimo

Symptom: `infrastructure/.venv/bin/marimo: No such file or directory`

Cause: marimo has its own separate venv at `infrastructure/marimo/venv/`.

Fix: Always launch marimo with `~/Documents/Q-agent/infrastructure/marimo/venv/bin/marimo`.

## marimo — Formatter Silently Drops Variables from Cell Return Tuples on First Open

Symptom: Downstream cells get `NameError` for variables that were in the return tuple when the file was written, but are missing after the server starts.

Cause: marimo's autoformatter removes "unused" variables from the return tuple the first time it parses a cell. If `QC_ROOT`, `pathlib`, or `mdates` are returned but not referenced by any downstream cell at parse time, marimo strips them.

Fix: Re-run the affected cell once after the server starts. Downstream cells recover when the kernel re-exports the correct variables. To prevent recurrence, ensure every returned variable is actually consumed downstream.

## marimo — Discover Running Servers Before Starting a New One

Symptom: Multiple marimo servers on ports 2718, 2719, 2720, etc., making it unclear which notebook is active.

Cause: Starting a new marimo server without checking existing sessions.

Fix: Always run `bash .claude/skills/marimo-pair/scripts/discover-servers.sh` first. Identify the correct port by inspecting `ctx.cells[0].code` on each discovered server. Only start a new server if none of the existing sessions has the target notebook.

## Bash Background Tasks — Python stdout Not Captured in Task Output

Symptom: Background task "completed" but task output file is 0 bytes or empty.

Cause: `run_in_background=true` Bash tasks do not reliably pipe Python stdout to the task output buffer for long-running scripts.

Fix: Redirect explicitly when running scripts in background:
```bash
python my_script.py > /tmp/output.txt 2>&1
```
Then read the file after the script finishes instead of relying on task output capture.

## Polymarket Pipeline — Background Run Overwrites Manually Written markets.csv

Symptom: Manually curated `markets.csv` is replaced with 0 rows after a pipeline run in the background.

Cause: `run_markets_pipeline.py` unconditionally overwrites `markets.csv` on every run. A concurrent background run that finds 0 matching markets writes an empty file.

Fix: Never run the markets pipeline concurrently with manual CSV writes. Check for running background jobs before modifying `markets.csv`. Use `--snapshot` flag to preserve dated copies before overwriting.

## Polymarket — Use CLOB Cursor Pagination for Full Market Discovery

Symptom: Gamma API `/events` pagination returns only ~100 events, missing most Fed/macro markets.

Cause: Gamma events endpoint has low coverage. The CLOB endpoint (`https://clob.polymarket.com/markets`) indexes 200k+ markets with cursor pagination.

Fix: For complete market discovery, use the CLOB directly with cursor pagination:
```python
cursor = ''
while True:
    params = {'limit': 1000}
    if cursor:
        params['next_cursor'] = cursor
    r = requests.get('https://clob.polymarket.com/markets', params=params)
    payload = r.json()
    items = payload.get('data', [])
    cursor = payload.get('next_cursor', '')
    # ... filter items client-side by question text
    if not cursor or cursor == 'LTE=':
        break
```
Full scan is ~200 pages and takes a few minutes with 0.15 s pacing.

## Polymarket — Apply Exclusion Terms Before Bulk Price Download

Symptom: Price files downloaded for irrelevant markets (NBA player "Norman Powell", Bank of England, Turkish Central Bank) that matched Fed keyword terms.

Cause: Keyword terms like "powell" and "rate" match non-Fed markets. Filtering was applied after download, wasting bandwidth.

Fix: Build an exclusion list and apply it before calling the prices pipeline:
```python
EXCLUDE = ['bank of england', 'nba', 'norman powell', 'turkey', 'turkish']
keep = [m for m in matches if not any(x in m['question'].lower() for x in EXCLUDE)]
```
Filter before writing to `markets.csv`, not after.

## Polymarket Prices Pipeline — Fails Silently on YesTokenId Schema Mismatch

Symptom: `run_prices_pipeline.py` exits cleanly but downloads 0 files. No error in logs.

Cause: `markets.csv` written from a custom CLOB scan uses column name `yes_token` while the pipeline script expects `YesTokenId`. The script skips all rows where `YesTokenId` is NaN/missing.

Fix: When writing a custom `markets.csv`, match the expected column names exactly:
`MarketId, Slug, Question, EventSlug, EventTitle, Active, Closed, Archived, StartDate, EndDate, ResolvedOutcome, OutcomePrices, Volume, Liquidity, YesTokenId, NoTokenId, Tags`
Or inspect `polymarket_lean/writer.py` for the exact column the prices pipeline reads.

## LEAN Local Backtest — ObjectStore Empty, File Path Mismatch in Docker

Symptom: Algorithm tries to load data from ObjectStore or local file, gets `FileNotFoundError` or ObjectStore read fails with "Object not found". Works differently in Docker vs host filesystem.

Cause:
1. Local backtests run in Docker with empty ObjectStore (must be pre-populated by a previous run or manually)
2. File paths differ between host (`/Users/.../data/`) and Docker (`/LeanCLI/...` or similar — varies by LEAN version)
3. LEAN mounts only `data-folder` from lean.json; other paths are not accessible in Docker

Fix: For small reference datasets (< 1 MB):
- Embed data directly in Python as constants or dictionaries instead of loading from files
- Use LEAN data-folder-relative paths if data must be external
- For cloud backtests: use ObjectStore after Initialize() pre-saves the data
- For local testing: hardcoded dicts avoid path resolution issues entirely

Example: Fed probability timeseries (31 rows)
```python
# In domain/config.py
FED_HIKE_PROBABILITIES = {
    date(2026, 4, 15): 0.145,
    date(2026, 4, 16): 0.145,
    # ... hardcode data
}

# In models/alpha.py on_initialize()
from domain.config import FED_HIKE_PROBABILITIES
self._fed_prob_lookup = FED_HIKE_PROBABILITIES
```

This pattern avoids Docker filesystem issues entirely and works across local, cloud, and live trading.

## yfinance — "Adj Close" No Longer Exists (v1.3+)

Symptom: `KeyError: 'Adj Close'` when indexing a multi-ticker yfinance download.

Cause: yfinance 1.3+ removed the `Adj Close` column. Multi-ticker downloads return a MultiIndex `(Price, Ticker)` where Price is one of: `Close`, `High`, `Low`, `Open`, `Volume`.

Fix:
```python
hy = yf.download(["HYG", "JNK"], start=s, end=e, progress=False)
# Access Close prices (not Adj Close)
if isinstance(hy.columns, pd.MultiIndex):
    prices = hy["Close"]  # DataFrame with HYG, JNK columns
```

Always inspect `hy.columns` and `hy.columns.levels` after download before indexing.

## yfinance — Multi-Ticker Column Structure

Symptom: Confusion about column structure when downloading 1 vs. multiple tickers.

Cause: Single-ticker download returns flat columns (`Close`, `High`, ...). Multi-ticker download returns `pd.MultiIndex` with levels `[Price, Ticker]`.

Fix: Always check `isinstance(result.columns, pd.MultiIndex)` and branch accordingly.

## WRDS Local Data — HY Bond ETFs (HYG, JNK) Not Available

Symptom: `FileNotFoundError` or missing zip when loading HY ETFs from WRDS LEAN-format data.

Cause: The local WRDS/CRSP pipeline only covers the configured 30-stock equity universe + SPY + SGOV. Bond ETFs like HYG and JNK are not included.

Fix: Use yfinance for HY ETF data: `yf.download(["HYG", "JNK"], ...)`. Or add them to the yfinance pipeline at `infrastructure/pipelines/yfinance/`.

## Event Window Analysis — Calendar Days ≠ Trading Days

Symptom: Event window matrix has 0 records despite having valid earnings dates and HY returns.

Cause: Using `pd.Timedelta(days=N)` counts calendar days, not trading days. A window of [-10, +5] calendar days around an earnings date rarely contains exactly 16 trading days, so strict `len(window) == WINDOW_SIZE` matching drops everything.

Fix: Use `.shift()` on the business-day index or `pd.bdate_range()`:
```python
# Instead of calendar-day offset:
trading_days = hyr.index
idx = trading_days.get_indexer([pd.Timestamp(earn_date)], method="nearest")[0]
window = hyr.iloc[max(0, idx - PRE_DAYS) : idx + POST_DAYS + 1]
```

## marimo code_mode — NotebookCell API

The `NotebookCell` object has these attributes (confirmed v0.23.5):
- `cell.id` — the cell ID (use this for `run_cell`, `edit_cell`, `delete_cell`)
- `cell.code` — the cell's source code as a string
- `cell.status` — `"idle"`, `"running"`, `"marimo-error"`, `"exception"`
- `cell.errors` — list of `CellError` objects with `.kind` and `.msg`
- `cell.name` — the cell's name (usually `"_"`)
- `cell.config` — cell configuration

NOT: `cell.cell_id`, `cell.__dict__`

## marimo — ctx.packages.add() for Runtime Installs

Symptom: `ModuleNotFoundError: No module named 'yfinance'` in notebook cell.

Fix: Use `ctx.packages.add("yfinance")` inside `code_mode` context — it installs into the marimo venv and handles kernel restart. Don't use `pip install` externally while the server is running.
