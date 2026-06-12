# Project Memory

## Key Files
- `lean-gotchas.md` — LEAN, Polymarket API, marimo, and exchange gotchas
- `decisions.md` — Architecture decisions with rationale
- `data-pipelines.md` — Data pipeline patterns and lessons
- `objectstore.md` — ObjectStore keys and schema notes
- `commands.md` — Durable shell commands
- `teaching-style.md` — Course/teaching preferences

## Infrastructure Venvs
- **Main LEAN/QC venv**: `~/Documents/Q-agent/venv/`
- **Infrastructure pipelines venv**: `~/Documents/Q-agent/infrastructure/.venv/` (crypto + polymarket packages)
- **marimo venv**: `~/Documents/Q-agent/infrastructure/marimo/venv/` — marimo binary lives here, NOT in `.venv`

## Crypto Data (infrastructure/pipelines/crypto)
- Exchanges: Coinbase (coinbasepro), Kraken — **Binance geo-blocked (451) in the US**
- Coinbase: BTC/ETH back to 2013 (3422+ daily bars); no SOL
- Kraken: BTC/ETH/SOL all quote currencies, ~721 daily bars
- LEAN format zips under `lean-data/crypto/<market>/daily/<symbol>.zip`

## Polymarket Data (infrastructure/pipelines/polymarket)
- `markets.csv`: 505 crypto markets (paginated + keyword-filtered — tag/search params broken as of May 2026)
- `prices/`: 163 price CSVs (129 with real data; 375 resolved markets returned empty from CLOB)
- Old resolved markets (pre-2023) return flat post-resolution prices — no historical probability series
- See `lean-gotchas.md` for full API change details

## Workflow Lessons (from May 2026 session)
See `data-pipelines.md` for full list. Short version:
1. Always probe a live API with one raw request before building pipelines against it
2. Verify exchange accessibility before queuing long pulls (Binance = 451 in US)
3. Stabilize output files before starting dependent pipelines
4. Check data availability before building analysis sections around it
