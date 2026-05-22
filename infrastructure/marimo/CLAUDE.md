# Marimo (shared tool environment)

## Purpose

Shared marimo environment for signal research. The venv here is used by any notebook in the workspace — typically this directory's `notebooks/`, `infrastructure/notebooks/`, or `MyProjects/<Project>/research/*.py`.

Data sources live under `infrastructure/pipelines/`.

## Workflow

Start a marimo session, then use `/marimo-pair` to collaborate:

```bash
cd ~/Documents/Q-agent/infrastructure/marimo
source venv/bin/activate
marimo edit notebooks/election_industry_returns.py --no-token
```

Then invoke the skill:
```
/marimo-pair pair with me on election_industry_returns.py
```

## Rules

- Editing `.py` notebook files directly while a marimo session is running is fine — marimo picks up the changes. `ctx.edit_cell()` / `ctx.create_cell()` via code_mode is the preferred path when you're already in a `/marimo-pair` session, but a direct file Edit is acceptable.
- Install packages via `ctx.packages.add()`, not `pip` or `uv add`.
- Keep signal logic pure Python (no LEAN imports) so it can graduate to `shared/signals/`.
- Data paths should reference `../pipelines/...` (from `infrastructure/marimo/`) or use `pathlib` — no hardcoded absolute paths in cells.
- No temp-file dependencies in cells (`/tmp/...` in cell code is a bug).
- **Always pass `timeout=` to network calls** (`requests.get/post`, `urllib`, etc.). `requests` has no default timeout, so a slow or unreachable endpoint will hang the cell — and the whole marimo kernel — indefinitely. Reasonable defaults: `timeout=30` for typical JSON APIs (Polymarket, Coingecko), `timeout=60` for slower academic / file-download hosts (Ken French / Dartmouth, SEC EDGAR bulk files).

## Plot Styling

Always use this dark theme for all matplotlib charts. Include this in the imports cell of every notebook:

```python
import matplotlib as mpl

plt.style.use('dark_background')
mpl.rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor': '#161b22',
    'axes.edgecolor': '#30363d',
    'axes.labelcolor': '#c9d1d9',
    'axes.grid': True,
    'grid.color': '#21262d',
    'grid.alpha': 0.6,
    'text.color': '#c9d1d9',
    'xtick.color': '#8b949e',
    'ytick.color': '#8b949e',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.dpi': 150,
    'savefig.facecolor': '#0d1117',
    'savefig.edgecolor': '#0d1117',
})
```

Additional styling rules:
- Use `RdYlGn` colormap for ranked/signal data (red=weak, green=strong)
- Use `mpl.colors.Normalize` + `ScalarMappable` for colorbars on ranked charts
- Bar edges: `edgecolor='#30363d'`, `linewidth=0.5`
- Reference lines: `color='#f85149'`, `alpha=0.7`
- Figure size: `(14, 5)` for bar charts, `(14, 6)` for time series
- Rotated x-labels: `rotation=45, ha='right', fontsize=9`
- Always call `plt.tight_layout()` before `plt.show()`

## GitHub Rendering

Marimo notebooks are plain `.py` files — GitHub shows only source code. To preserve rendered outputs for review:

```bash
# Export as Jupyter notebook with executed outputs (GitHub renders these natively)
marimo export ipynb my_notebook.py -o my_notebook.ipynb --include-outputs
```

A pre-commit hook auto-exports any staged marimo `.py` to `.ipynb` with `--include-outputs`.

## Shared venv

This directory hosts the shared marimo venv used by all marimo notebooks in the workspace. Activate it before starting marimo:

```bash
source venv/bin/activate
```
