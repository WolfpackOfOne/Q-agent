---
path: "agent_graph_system/ingestion/github/parser.py"
hub: "Agent Graph System"
lines: 105
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py"
---
# parser.py

`agent_graph_system/ingestion/github/parser.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py)

## Purpose

Parse a GitHub repository and extract notebook/pipeline/dependency relationships.

## Dependencies


**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#ast|ast]], [[Indexes/External packages#json|json]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#re|re]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/ingestion/github/graph_writer.py|graph_writer.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `KNOWN_DATASETS` | `{'wrds': 'WRDS', 'edgar': 'EDGAR', 'polymarket': 'Polymarket', 'crypto': 'Crypto', 'bloomberg': 'Bloomberg', 'yfinance': 'YFinance', 'quantconnect': 'QuantCo...` | [13](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py#L13) |

## Functions

### `_extract_imports()`

```python
def _extract_imports(source: str) -> list[str]
```
[line 25](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py#L25)

### `_infer_datasets()`

```python
def _infer_datasets(imports: list[str], path_str: str) -> list[str]
```
[line 39](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py#L39)

Guess which datasets a notebook depends on from its imports and path.

### `parse_notebook()`

```python
def parse_notebook(path: Path) -> dict[str, Any]
```
[line 49](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py#L49)

Extract metadata from a .py (marimo) or .ipynb notebook file.

### `scan_repo()`

```python
def scan_repo(repo_root: Path) -> dict[str, Any]
```
[line 88](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/ingestion/github/parser.py#L88)

Walk a local clone and extract all notebooks, pipelines, and their relationships.

## Source

> [!example]- agent_graph_system/ingestion/github/parser.py (105 lines)
> ```python
> """Parse a GitHub repository and extract notebook/pipeline/dependency relationships."""
>
> from __future__ import annotations
>
> import ast
> import logging
> import re
> from pathlib import Path
> from typing import Any
>
> log = logging.getLogger(__name__)
>
> KNOWN_DATASETS = {
>     "wrds": "WRDS",
>     "edgar": "EDGAR",
>     "polymarket": "Polymarket",
>     "crypto": "Crypto",
>     "bloomberg": "Bloomberg",
>     "yfinance": "YFinance",
>     "quantconnect": "QuantConnect",
>     "sql": "SQL",
> }
>
>
> def _extract_imports(source: str) -> list[str]:
>     try:
>         tree = ast.parse(source)
>     except SyntaxError:
>         return []
>     imports = []
>     for node in ast.walk(tree):
>         if isinstance(node, ast.Import):
>             imports.extend(alias.name for alias in node.names)
>         elif isinstance(node, ast.ImportFrom) and node.module:
>             imports.append(node.module)
>     return imports
>
>
> def _infer_datasets(imports: list[str], path_str: str) -> list[str]:
>     """Guess which datasets a notebook depends on from its imports and path."""
>     hits = set()
>     combined = " ".join(imports).lower() + " " + path_str.lower()
>     for keyword, source in KNOWN_DATASETS.items():
>         if keyword in combined:
>             hits.add(source)
>     return sorted(hits)
>
>
> def parse_notebook(path: Path) -> dict[str, Any]:
>     """Extract metadata from a .py (marimo) or .ipynb notebook file."""
>     result: dict[str, Any] = {
>         "name": path.stem,
>         "path": str(path),
>         "notebook_type": "research",
>         "datasets": [],
>         "imports": [],
>     }
>
>     if path.suffix == ".py":
>         try:
>             source = path.read_text(errors="replace")
>         except OSError:
>             return result
>         result["imports"] = _extract_imports(source)
>         # Detect notebook type from path or content
>         lower = source.lower()
>         if "backtest" in lower or "quantconnect" in lower:
>             result["notebook_type"] = "backtest"
>         elif "pipeline" in lower or "ingest" in lower:
>             result["notebook_type"] = "ingestion"
>     elif path.suffix == ".ipynb":
>         import json
>         try:
>             nb = json.loads(path.read_text(errors="replace"))
>         except (OSError, json.JSONDecodeError):
>             return result
>         code = "\n".join(
>             "".join(cell.get("source", []))
>             for cell in nb.get("cells", [])
>             if cell.get("cell_type") == "code"
>         )
>         result["imports"] = _extract_imports(code)
>
>     result["datasets"] = _infer_datasets(result["imports"], str(path))
>     return result
>
>
> def scan_repo(repo_root: Path) -> dict[str, Any]:
>     """Walk a local clone and extract all notebooks, pipelines, and their relationships."""
>     notebooks = []
>     for pattern in ("**/*.py", "**/*.ipynb"):
>         for p in repo_root.glob(pattern):
>             # Skip venv, .git, __pycache__
>             if any(part.startswith(".") or part in {"venv", "__pycache__", "node_modules"} for part in p.parts):
>                 continue
>             nb = parse_notebook(p)
>             if nb["imports"] or p.suffix == ".ipynb":
>                 notebooks.append(nb)
>
>     return {
>         "repo": repo_root.name,
>         "notebooks": notebooks,
>         "total": len(notebooks),
>     }
> ```
