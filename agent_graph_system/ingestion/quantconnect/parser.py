"""Parse a QuantConnect / LEAN project under ``MyProjects/`` into a structured
inventory the graph writer can turn into nodes and edges.

This is deliberately a *pure* parser: it walks the filesystem and Python ASTs
and returns plain dicts. No graph imports, no I/O beyond reading files — so it
is fast and unit-testable against a fixture project.

What it recognises (atomic-architecture aware):

    files            every .py / .ipynb / .md / .csv under the project
    docs             AGENTS.md, claude.md, README.md, and anything under docs/
    modules          top-level classes in each .py file (File DEFINES Module)
    signals          top-level functions in domain/signals/*.py (Signal atoms)
    config_params    top-level UPPER_CASE assignments (domain/config.py et al.)
    subscriptions    AddEquity/AddCrypto/... data subscriptions (-> Dataset)
    data_files       bundled data/*.csv files (-> Dataset)
    objectstore      ObjectStore.Save/Read call sites (write/read keys)
    notebooks        research/*.ipynb and *.py

Heuristic facts (ObjectStore keys, subscription tickers resolved from
constants) are reported with a sub-1.0 ``confidence`` so the graph writer can
stamp honest provenance — see :mod:`agent_graph_system.ontology.provenance`.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Files that are project documentation regardless of location.
_DOC_NAMES = {"agents.md", "claude.md", "readme.md", "contributing.md"}

# QCAlgorithm data-subscription methods.
_SUBSCRIPTION_METHODS = {
    "AddEquity", "AddCrypto", "AddData", "AddForex",
    "AddFuture", "AddOption", "AddIndex", "AddCfd",
}

_OBJECTSTORE_METHODS = {"Save": "write", "Read": "read", "SaveBytes": "write", "ReadBytes": "read"}

# Confidence scores by how directly a fact is observed.
_CONF_AST = 0.95          # classes / functions / config params — direct from AST
_CONF_HEURISTIC = 0.8     # ObjectStore keys / tickers resolved from constants
_CONF_DYNAMIC = 0.5       # call site found but the key/ticker is computed


def _classify(rel_path: str) -> str:
    p = rel_path.lower()
    name = rel_path.rsplit("/", 1)[-1].lower()
    if name in _DOC_NAMES or p.startswith("docs/") or "/docs/" in p:
        if p.endswith(".md"):
            return "doc"
    if p.endswith(".ipynb"):
        return "notebook"
    if p.endswith(".py"):
        # research/*.py marimo notebooks count as notebooks too
        if "research/" in p or p.startswith("research/"):
            return "notebook"
        return "python"
    if p.endswith(".csv"):
        return "data"
    if p.endswith(".md"):
        return "doc"
    return "other"


def _iter_files(project_root: Path) -> list[tuple[str, str]]:
    """Return ``(relative_path, kind)`` for every interesting file."""
    out: list[tuple[str, str]] = []
    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or any(part.startswith(".") for part in path.parts):
            continue
        rel = path.relative_to(project_root).as_posix()
        kind = _classify(rel)
        if kind != "other":
            out.append((rel, kind))
    return out


def _str_arg(node: ast.AST) -> str | None:
    """The literal string value of an arg node, if it is a string constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _attr_chain_has_objectstore(func: ast.expr) -> bool:
    """True if the attribute chain of a call references ObjectStore."""
    cur: ast.AST | None = func
    while isinstance(cur, ast.Attribute):
        if cur.attr == "ObjectStore":
            return True
        cur = cur.value
    # also catch `self.ObjectStore.Save(...)` where value is Attribute(attr=ObjectStore)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
        return func.value.attr == "ObjectStore"
    return False


def _parse_python(rel_path: str, source: str) -> dict[str, Any]:
    """Extract classes, functions, config params, subscriptions, ObjectStore ops."""
    result: dict[str, Any] = {
        "classes": [], "functions": [], "config_params": [],
        "subscriptions": [], "objectstore": [],
    }
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        log.warning("Skipping unparseable file %s: %s", rel_path, exc)
        return result

    # Top-level classes and (for signal files) top-level functions + config params.
    is_signal_file = "signals/" in rel_path or rel_path.startswith("signals/")
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            result["classes"].append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.FunctionDef):
            if is_signal_file:
                result["functions"].append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    result["config_params"].append(
                        {"name": tgt.id, "line": node.lineno, "value": _literal_repr(node.value)}
                    )

    # Calls anywhere in the file: subscriptions + ObjectStore ops.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr in _SUBSCRIPTION_METHODS:
            ticker = _str_arg(node.args[0]) if node.args else None
            result["subscriptions"].append({
                "method": attr,
                "ticker": ticker,
                "ref": _name_ref(node.args[0]) if node.args and ticker is None else None,
                "line": node.lineno,
            })
        elif attr in _OBJECTSTORE_METHODS and _attr_chain_has_objectstore(node.func):
            key = _str_arg(node.args[0]) if node.args else None
            result["objectstore"].append({
                "op": _OBJECTSTORE_METHODS[attr],
                "key": key,
                "ref": _name_ref(node.args[0]) if node.args and key is None else None,
                "line": node.lineno,
            })
    return result


def _literal_repr(node: ast.AST) -> str:
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return f"<{type(node).__name__}>"


def _name_ref(node: ast.AST) -> str | None:
    """Name of a variable used as an argument (e.g. a config constant)."""
    if isinstance(node, ast.Name):
        return node.id
    return None


def parse_project(project_root: str | Path) -> dict[str, Any]:
    """Parse a single project directory into a structured inventory."""
    root = Path(project_root)
    if not root.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {root}")

    name = root.name
    files = _iter_files(root)

    inventory: dict[str, Any] = {
        "project": name,
        "root": str(root),
        "files": [{"path": rel, "kind": kind} for rel, kind in files],
        "docs": [rel for rel, kind in files if kind == "doc"],
        "notebooks": [rel for rel, kind in files if kind == "notebook"],
        "data_files": [rel for rel, kind in files if kind == "data"],
        "modules": [],      # {file, name, line}
        "signals": [],      # {file, name, line}
        "config_params": [],  # {name, value, file, line}
        "subscriptions": [],  # {ticker|ref, method, file, line, confidence}
        "objectstore": [],    # {op, key, file, line, confidence}
    }

    # First pass: parse python files, collect config params so we can resolve refs.
    parsed: dict[str, dict[str, Any]] = {}
    const_values: dict[str, str] = {}
    for rel, kind in files:
        if kind not in ("python", "notebook") or not rel.endswith(".py"):
            continue
        try:
            source = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            log.warning("Could not read %s: %s", rel, exc)
            continue
        pp = _parse_python(rel, source)
        parsed[rel] = pp
        for cp in pp["config_params"]:
            inventory["config_params"].append({"file": rel, **cp})
            # Capture string-literal constants for ObjectStore/ticker resolution.
            val = cp["value"]
            if val.startswith("'") or val.startswith('"'):
                const_values[cp["name"]] = val.strip("'\"")

    # Second pass: assemble modules/signals/subscriptions/objectstore with refs resolved.
    for rel, pp in parsed.items():
        for cls in pp["classes"]:
            inventory["modules"].append({"file": rel, "name": cls["name"], "line": cls["line"]})
        for fn in pp["functions"]:
            inventory["signals"].append({"file": rel, "name": fn["name"], "line": fn["line"]})
        for sub in pp["subscriptions"]:
            ticker = sub["ticker"] or const_values.get(sub["ref"] or "", None)
            inventory["subscriptions"].append({
                "file": rel, "method": sub["method"], "line": sub["line"],
                "ticker": ticker, "ref": sub["ref"],
                "confidence": _CONF_HEURISTIC if ticker else _CONF_DYNAMIC,
            })
        for op in pp["objectstore"]:
            key = op["key"] or const_values.get(op["ref"] or "", None)
            inventory["objectstore"].append({
                "file": rel, "op": op["op"], "line": op["line"],
                "key": key, "ref": op["ref"],
                "confidence": _CONF_HEURISTIC if key else _CONF_DYNAMIC,
            })

    return inventory


# Confidence constants exposed for the graph writer.
CONF_AST = _CONF_AST
CONF_HEURISTIC = _CONF_HEURISTIC
CONF_DYNAMIC = _CONF_DYNAMIC
