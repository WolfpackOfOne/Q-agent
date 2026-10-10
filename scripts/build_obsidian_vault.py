#!/usr/bin/env python3
"""Generate the Obsidian code vault under ``obsidian/`` from the tracked source.

The vault mirrors every tracked Python module, shell script, research notebook,
CI workflow, and Claude agent/skill prompt as an Obsidian note, then layers
cross-linked hub notes on top:

* ``Code/``     one note per source file: docstrings, signatures, imports
                (as [[wikilinks]]), every embedded SQL / Cypher query, and the
                full source in a collapsed callout.
* ``SQL/``      a catalogue of every SQL query plus one note per database table
                (e.g. ``crsp.dsf``) linking back to the queries that read it.
* ``Hubs/``     one hub per strategy project, data pipeline, and workspace area.
* ``Indexes/``  flat indexes (all files, Cypher queries, external packages).

Hand-written notes at the vault root (``Home.md``, ``Architecture.md`` ...)
are never touched. Re-run after code changes:

    python scripts/build_obsidian_vault.py
"""

from __future__ import annotations

import ast
import itertools
import json
import re
import shutil
import subprocess
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VAULT = REPO_ROOT / "obsidian"
GENERATED_DIRS = ("Code", "SQL", "Hubs", "Indexes")
GITHUB_BLOB = "https://github.com/WolfpackOfOne/Q-agent/blob/main"

SQL_RE = re.compile(r"(?is)\bselect\b.+?\bfrom\b")
SQL_TABLE_RE = re.compile(r"(?i)\b(?:from|join)\s+([A-Za-z_]\w*\.[A-Za-z_]\w*|\{[^}]+\}(?:\.\{?[\w]+\}?)?)")
CYPHER_RE = re.compile(r"(?s)\b(MATCH|MERGE|UNWIND|CREATE)\b.*(\(\w*:\w+|\]->|RETURN)")

PROJECT_LAYERS = {
    "main.py": "Composition root",
    "models": "Organism",
    "domain": "Molecule / Atom",
    "tools": "Tool (offline refresh)",
    "research": "Research",
    "infrastructure": "Infrastructure adapter",
}


# --------------------------------------------------------------------------- #
# File discovery and classification
# --------------------------------------------------------------------------- #

def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO_ROOT)
    files = [f.decode() for f in out.split(b"\0") if f]
    return [f for f in files if not f.startswith(("Lean/", "obsidian/"))]


def wanted(rel: str) -> bool:
    p = Path(rel)
    if p.suffix in {".py", ".sh", ".ipynb"}:
        return True
    if rel.startswith(".github/workflows/") and p.suffix in {".yml", ".yaml"}:
        return True
    if rel == "Dockerfile":
        return True
    if rel.startswith(".claude/agents/") or rel.startswith("MyProjects/.claude/agents/"):
        return p.suffix == ".md"
    if rel.startswith(".claude/skills/") and p.name == "SKILL.md":
        return True
    return False


def area_of(rel: str) -> tuple[str, str]:
    """Return (hub folder, hub name) for a repository path."""
    parts = Path(rel).parts
    if parts[0] == "MyProjects" and len(parts) > 2 and parts[1] != ".claude":
        if parts[1] == "shared":
            return "Projects", "shared signals"
        return "Projects", parts[1]
    if parts[:2] == ("infrastructure", "pipelines") and len(parts) > 3:
        return "Pipelines", parts[2]
    if parts[:2] == ("infrastructure", "marimo"):
        return "Areas", "Marimo notebooks"
    if parts[0] == "agent_graph_system":
        return "Areas", "Agent Graph System"
    if parts[0] == "tests":
        return "Areas", "Tests"
    if parts[0] == "scripts":
        return "Areas", "Scripts"
    if parts[0] == ".github":
        return "Areas", "CI workflows"
    if parts[0] == ".claude" or rel.startswith("MyProjects/.claude/"):
        return "Areas", "Claude agents and skills"
    return "Areas", "Workspace root"


def layer_of(rel: str) -> str | None:
    parts = Path(rel).parts
    if parts[0] != "MyProjects" or len(parts) < 3 or parts[1] in {"shared", ".claude"}:
        return "Atom (shared signal)" if len(parts) > 2 and parts[1] == "shared" else None
    return PROJECT_LAYERS.get(parts[2])


def note_path(rel: str) -> str:
    """Vault-relative note path (without .md) for a repository file."""
    return f"Code/{rel}"


def link(rel: str, label: str | None = None) -> str:
    return f"[[{note_path(rel)}|{label or Path(rel).name}]]"


def hub_link(folder: str, name: str) -> str:
    return f"[[Hubs/{folder}/{name}|{name}]]"


def gh(rel: str, line: int | None = None) -> str:
    return f"{GITHUB_BLOB}/{rel}" + (f"#L{line}" if line else "")


def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "_", text)


# --------------------------------------------------------------------------- #
# Python module resolution
# --------------------------------------------------------------------------- #

def build_module_index(py_files: list[str]) -> dict[str, dict[str, str]]:
    """Map import roots -> {dotted module name: repo path}."""
    roots: set[str] = {""}
    for rel in py_files:
        parts = Path(rel).parts
        if "src" in parts:
            roots.add("/".join(parts[: parts.index("src") + 1]))
        if parts[0] == "MyProjects" and len(parts) > 2:
            roots.add("/".join(parts[:2]))
        if parts[:2] == ("infrastructure", "pipelines") and len(parts) > 3:
            roots.add("/".join(parts[:3]))
        roots.add(str(Path(rel).parent) if str(Path(rel).parent) != "." else "")
    index: dict[str, dict[str, str]] = {}
    for root in roots:
        table: dict[str, str] = {}
        prefix = f"{root}/" if root else ""
        for rel in py_files:
            if not rel.startswith(prefix):
                continue
            sub = Path(rel[len(prefix):])
            mod_parts = list(sub.with_suffix("").parts)
            if mod_parts and mod_parts[-1] == "__init__":
                mod_parts = mod_parts[:-1]
            if mod_parts and all(p.isidentifier() for p in mod_parts):
                table[".".join(mod_parts)] = rel
        index[root] = table
    return index


def candidate_roots(rel: str) -> list[str]:
    parts = Path(rel).parts
    roots = [str(Path(rel).parent) if str(Path(rel).parent) != "." else ""]
    if parts[0] == "MyProjects" and len(parts) > 2:
        roots.append("/".join(parts[:2]))
    if parts[:2] == ("infrastructure", "pipelines") and len(parts) > 3:
        roots.append("/".join(parts[:3]) + "/src")
        roots.append("/".join(parts[:3]))
    roots.append("")
    return roots


def resolve_import(rel: str, module: str, names: list[str], level: int,
                   index: dict[str, dict[str, str]]) -> list[str]:
    targets: list[str] = []
    if level:
        base = Path(rel).parent
        for _ in range(level - 1):
            base = base.parent
        pkg = ".".join(base.parts)
        dotted = ".".join(p for p in (pkg, module) if p)
        table = index.get("", {})
        for name in names:
            if f"{dotted}.{name}" in table:
                targets.append(table[f"{dotted}.{name}"])
        if dotted in table and not targets:
            targets.append(table[dotted])
        return targets
    for root in candidate_roots(rel):
        table = index.get(root, {})
        hits = [table[f"{module}.{n}"] for n in names if f"{module}.{n}" in table]
        if hits:
            return hits
        if module in table:
            return [table[module]]
    return targets


# --------------------------------------------------------------------------- #
# Python analysis
# --------------------------------------------------------------------------- #

@dataclass
class Query:
    kind: str            # "sql" | "cypher"
    text: str
    rel: str
    line: int
    owner: str           # enclosing def/class or "module"
    variable: str | None
    tables: list[str] = field(default_factory=list)
    placeholders: list[str] = field(default_factory=list)
    dynamic: dict[str, list[str]] = field(default_factory=dict)   # template -> resolved
    call_sites: list[tuple[int, str]] = field(default_factory=list)
    func: ast.AST | None = field(default=None, repr=False)


@dataclass
class PyInfo:
    docstring: str = ""
    classes: list[tuple] = field(default_factory=list)
    functions: list[tuple] = field(default_factory=list)
    constants: list[tuple] = field(default_factory=list)
    internal: set[str] = field(default_factory=set)
    external: set[str] = field(default_factory=set)
    queries: list[Query] = field(default_factory=list)
    error: str | None = None


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = ast.unparse(node.args)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({args}){ret}"


def literal_text(node: ast.AST, source: str) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        seg = ast.get_source_segment(source, node) or ""
        seg = re.sub(r"^[rRfFbBuU]{1,2}", "", seg)
        for q in ('"""', "'''", '"', "'"):
            if seg.startswith(q) and seg.endswith(q) and len(seg) >= 2 * len(q):
                return seg[len(q):-len(q)]
        return seg
    return None


def clean_query(text: str) -> str:
    return textwrap.dedent(text.strip("\n")).strip()


def extract_queries(tree: ast.AST, source: str, rel: str) -> list[Query]:
    queries: list[Query] = []
    docstring_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr):
                docstring_ids.add(id(body[0].value))

    def visit(node: ast.AST, owner: str, variable: str | None, func=None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            owner = node.name if owner == "module" else f"{owner}.{node.name}"
            if not isinstance(node, ast.ClassDef):
                func = node
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            variable = ast.unparse(node.targets[0])
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            variable = ast.unparse(node.target)
        if id(node) not in docstring_ids:
            text = literal_text(node, source)
            if text and len(text) > 20:
                kind = None
                if SQL_RE.search(text) and re.search(r"(?i)\bselect\b", text.lstrip()[:400]):
                    kind = "sql"
                elif rel.startswith("agent_graph_system/") and CYPHER_RE.search(text):
                    kind = "cypher"
                if kind:
                    body = clean_query(text)
                    q = Query(kind, body, rel, node.lineno, owner, variable, func=func)
                    if kind == "sql":
                        q.tables = sorted({t for t in SQL_TABLE_RE.findall(body)})
                    if isinstance(node, ast.JoinedStr):
                        q.placeholders = sorted(set(re.findall(r"\{([^{}]+)\}", body)))
                    queries.append(q)
                    return
        for child in ast.iter_child_nodes(node):
            if isinstance(node, ast.JoinedStr):
                return
            visit(child, owner, variable, func)

    visit(tree, "module", None)
    resolve_dynamic_tables(tree, queries)
    return queries


# --------------------------------------------------------------------------- #
# Best-effort resolution of f-string table names ({schema}.{table})
# --------------------------------------------------------------------------- #

MAX_CANDIDATES = 12


def str_candidates(expr: ast.AST | None, env: dict[str, set[str]],
                   world: dict[str, bool] | None = None) -> set[str] | None:
    """Possible string values of a simple expression, or None if unknown."""
    if expr is None:
        return None
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}
    if isinstance(expr, ast.Name):
        return env.get(expr.id)
    if isinstance(expr, ast.IfExp):
        # Within one "world" every shared condition takes a single value, so
        # correlated choices (schema and table keyed on one flag) stay paired.
        test = ast.dump(expr.test)
        if world and test in world:
            return str_candidates(expr.body if world[test] else expr.orelse, env, world)
        a, b = str_candidates(expr.body, env, world), str_candidates(expr.orelse, env, world)
        return (a or set()) | (b or set()) or None
    if isinstance(expr, ast.JoinedStr):
        acc = {""}
        for part in expr.values:
            if isinstance(part, ast.Constant):
                opts = {str(part.value)}
            elif isinstance(part, ast.FormattedValue):
                opts = str_candidates(part.value, env, world)
            else:
                opts = None
            if not opts:
                return None
            acc = {x + y for x in acc for y in opts}
            if len(acc) > MAX_CANDIDATES:
                return None
        return acc
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        a, b = str_candidates(expr.left, env, world), str_candidates(expr.right, env, world)
        if a and b:
            return {x + y for x in a for y in b}
    return None


def local_env(func: ast.AST, seed: dict[str, set[str]],
              world: dict[str, bool] | None = None) -> dict[str, set[str]]:
    env = dict(seed)
    assigns = sorted((n for n in ast.walk(func) if isinstance(n, ast.Assign)),
                     key=lambda n: n.lineno)
    for node in assigns:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            vals = str_candidates(node.value, env, world)
            if vals:
                env[node.targets[0].id] = vals
    return env


def resolve_dynamic_tables(tree: ast.AST, queries: list[Query]) -> None:
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    parent_func: dict[int, ast.AST] = {}
    for f in funcs.values():
        for n in ast.walk(f):
            parent_func.setdefault(id(n), f)
    for q in queries:
        templates = [t for t in q.tables if "{" in t]
        if q.kind != "sql" or not templates or q.func is None:
            continue
        func = q.func
        params = [a.arg for a in func.args.args]
        defaults = dict(zip(params[len(params) - len(func.args.defaults):], func.args.defaults))
        base = {k: v for k, d in defaults.items() if (v := str_candidates(d, {}))}
        seeds: list[dict[str, set[str]]] = []
        for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
            if not (isinstance(call.func, ast.Name) and call.func.id == func.name):
                continue
            caller = parent_func.get(id(call))
            caller_env = local_env(caller, {}) if caller is not None else {}
            bound = dict(base)
            for name, arg in zip(params, call.args):
                if (v := str_candidates(arg, caller_env)):
                    bound[name] = v
            for kw in call.keywords:
                if kw.arg and (v := str_candidates(kw.value, caller_env)):
                    bound[kw.arg] = v
            q.call_sites.append((call.lineno, ast.unparse(call)))
            seeds.append(bound)
        tests = sorted({ast.dump(n.test) for n in ast.walk(func) if isinstance(n, ast.IfExp)})
        worlds = ([dict(zip(tests, combo)) for combo in itertools.product((True, False), repeat=len(tests))]
                  if len(tests) <= 4 else [{}])
        envs = [(local_env(func, seed, w), w) for seed in (seeds or [base]) for w in worlds]
        for template in templates:
            resolved: set[str] = set()
            try:
                expr = ast.parse(f"f{template!r}", mode="eval").body
            except SyntaxError:
                continue
            for env, w in envs:
                resolved |= str_candidates(expr, env, w) or set()
            q.dynamic[template] = sorted(r for r in resolved if "{" not in r)
        q.tables = sorted({t for t in q.tables if "{" not in t}
                          | {r for rs in q.dynamic.values() for r in rs})


def analyze_python(rel: str, source: str, index) -> PyInfo:
    info = PyInfo()
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        info.error = f"{exc.msg} (line {exc.lineno})"
        return info
    info.docstring = ast.get_docstring(tree) or ""
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                (signature(m), (ast.get_docstring(m) or "").strip(), m.lineno)
                for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            info.classes.append((node.name, bases, ast.get_docstring(node) or "", node.lineno, methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info.functions.append((signature(node), ast.get_docstring(node) or "", node.lineno))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper() and node.value is not None:
                    value = ast.unparse(node.value)
                    if len(value) > 160:
                        value = value[:157] + "..."
                    info.constants.append((t.id, value, node.lineno))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits = resolve_import(rel, alias.name, [], 0, index)
                if hits:
                    info.internal.update(hits)
                else:
                    info.external.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            names = [a.name for a in node.names]
            hits = resolve_import(rel, node.module or "", names, node.level, index)
            if hits:
                info.internal.update(hits)
            elif not node.level and node.module:
                info.external.add(node.module.split(".")[0])
    info.internal.discard(rel)
    info.queries = extract_queries(tree, source, rel)
    return info


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #

def callout(kind: str, title: str, body: str, folded: bool = True) -> str:
    fold = "-" if folded else ""
    lines = [f"> [!{kind}]{fold} {title}"]
    lines += [f"> {line}" if line else ">" for line in body.splitlines()]
    return "\n".join(lines)


def fence(lang: str, text: str) -> str:
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}"


def frontmatter(data: dict) -> str:
    out = ["---"]
    for key, value in data.items():
        if value is None or value == [] or value == "":
            continue
        if isinstance(value, list):
            out.append(f"{key}:")
            out += [f"  - {json.dumps(v)}" for v in value]
        else:
            out.append(f"{key}: {json.dumps(value)}")
    out.append("---")
    return "\n".join(out)


def tag_for(folder: str, name: str) -> str:
    return f"{folder.lower()}/{re.sub(r'[^A-Za-z0-9_-]+', '-', name).strip('-')}"


def demote_headings(markdown: str, by: int = 2) -> str:
    out, in_fence = [], False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"^#{1,6} ", line):
            line = "#" * by + line
            line = re.sub(r"^#{7,}", "######", line)
        out.append(line)
    return "\n".join(out)


def query_block(q: Query, with_source: bool) -> str:
    owner = "module level" if q.owner == "module" else f"`{q.owner}()`"
    parts = [f"**{owner}** — line [{q.line}]({gh(q.rel, q.line)})"]
    if with_source:
        parts[0] += f" in {link(q.rel, q.rel)}"
    if q.variable:
        parts[0] += f" · assigned to `{q.variable}`"
    if q.tables:
        parts.append("Tables: " + ", ".join(table_link(t) for t in q.tables))
    for template, resolved in q.dynamic.items():
        parts.append(f"Dynamic table `{template}` → " + (
            ", ".join(table_link(r) for r in resolved) + " *(resolved from assignments / call sites)*"
            if resolved else "*not statically resolvable*"))
    if q.call_sites:
        parts.append("Call sites:\n" + "\n".join(
            f"- [L{line}]({gh(q.rel, line)}) `{text}`" for line, text in q.call_sites))
    if q.placeholders:
        parts.append("f-string placeholders: " + ", ".join(f"`{{{p}}}`" for p in q.placeholders))
    parts.append(fence(q.kind, q.text))
    return "\n\n".join(parts)


def table_link(table: str) -> str:
    if table.startswith("{"):
        return f"`{table}` (dynamic)"
    return f"[[SQL/Tables/{table.lower()}|{table.lower()}]]"


# --------------------------------------------------------------------------- #
# Note writers
# --------------------------------------------------------------------------- #

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def python_note(rel: str, source: str, info: PyInfo, imported_by: set[str]) -> str:
    folder, hub = area_of(rel)
    layer = layer_of(rel)
    tags = ["code/python", tag_for(folder, hub)]
    if info.queries:
        tags.append("has/" + "-".join(sorted({q.kind for q in info.queries})))
    fm = frontmatter({
        "path": rel,
        "hub": hub,
        "layer": layer,
        "lines": source.count("\n") + 1,
        "tags": tags,
        "github": gh(rel),
    })
    out = [fm, f"# {Path(rel).name}", ""]
    out.append(f"`{rel}` · hub {hub_link(folder, hub)}" + (f" · layer **{layer}**" if layer else "")
               + f" · [GitHub]({gh(rel)})")
    out.append("")
    if info.error:
        out.append(callout("warning", "Could not parse", info.error, folded=False))
    if info.docstring:
        out += ["## Purpose", "", info.docstring.strip(), ""]

    if info.internal or info.external or imported_by:
        out += ["## Dependencies", ""]
        if info.internal:
            out.append("**Imports (workspace):** " + ", ".join(link(t) for t in sorted(info.internal)))
        if info.external:
            out.append("")
            out.append("**Imports (external):** " + ", ".join(
                f"[[Indexes/External packages#{p}|{p}]]" for p in sorted(info.external)))
        if imported_by:
            out.append("")
            out.append("**Imported by:** " + ", ".join(link(t) for t in sorted(imported_by)))
        out.append("")

    if info.queries:
        kinds = sorted({q.kind.upper() for q in info.queries})
        out += [f"## {' & '.join(kinds)} queries ({len(info.queries)})", ""]
        for q in info.queries:
            out += [f"### {q.owner if q.owner != 'module' else 'module level'} · L{q.line}", "",
                    query_block(q, with_source=False), ""]

    if info.constants:
        out += ["## Constants", "", "| Name | Value | Line |", "|---|---|---|"]
        for name, value, line in info.constants:
            value = value.replace("|", "\\|").replace("\n", " ")
            out.append(f"| `{name}` | `{value}` | [{line}]({gh(rel, line)}) |")
        out.append("")

    if info.classes:
        out += ["## Classes", ""]
        for name, bases, doc, line, methods in info.classes:
            out.append(f"### class `{name}`" + (f"({bases})" if bases else ""))
            out += ["", f"[line {line}]({gh(rel, line)})", ""]
            if doc:
                out += [doc.strip(), ""]
            for sig, mdoc, mline in methods:
                first = mdoc.split("\n\n")[0].replace("\n", " ") if mdoc else ""
                out.append(f"- `{sig}` — [L{mline}]({gh(rel, mline)})" + (f"  \n  {first}" if first else ""))
            out.append("")

    if info.functions:
        out += ["## Functions", ""]
        for sig, doc, line in info.functions:
            name = sig.split("(")[0].split()[-1]
            out += [f"### `{name}()`", "", fence("python", sig),
                    f"[line {line}]({gh(rel, line)})", ""]
            if doc:
                out += [doc.strip(), ""]

    out += ["## Source", "", callout("example", f"{rel} ({source.count(chr(10)) + 1} lines)",
                                     fence("python", source))]
    return "\n".join(out)


def text_note(rel: str, source: str, lang: str, extra: str = "") -> str:
    folder, hub = area_of(rel)
    fm = frontmatter({"path": rel, "hub": hub, "tags": [f"code/{lang}", tag_for(folder, hub)],
                      "github": gh(rel)})
    out = [fm, f"# {Path(rel).name}", "",
           f"`{rel}` · hub {hub_link(folder, hub)} · [GitHub]({gh(rel)})", ""]
    if extra:
        out += [extra, ""]
    out += ["## Source", "", callout("example", rel, fence(lang, source),
                                     folded=len(source.splitlines()) > 40)]
    return "\n".join(out)


def prompt_note(rel: str, source: str) -> str:
    """Claude agent / skill prompt: surface frontmatter, embed the body."""
    folder, hub = area_of(rel)
    meta, body = {}, source
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", source, re.S)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
    title = meta.get("name") or Path(rel).stem
    if Path(rel).name == "SKILL.md":
        title = meta.get("name") or Path(rel).parent.name
    fm = frontmatter({"path": rel, "hub": hub, "tags": ["prompt", tag_for(folder, hub)],
                      "github": gh(rel)})
    out = [fm, f"# {title}", "", f"`{rel}` · hub {hub_link(folder, hub)} · [GitHub]({gh(rel)})", ""]
    if meta.get("description"):
        out += [callout("abstract", "Description", meta["description"].replace("\\n", "\n"),
                        folded=False), ""]
    extra = {k: v for k, v in meta.items() if k not in {"name", "description"}}
    if extra:
        out += ["| Key | Value |", "|---|---|"] + [f"| {k} | `{v}` |" for k, v in extra.items()] + [""]
    out += ["## Prompt", "", demote_headings(body.strip(), by=2)]
    return "\n".join(out)


def notebook_note(rel: str, raw: str, index) -> tuple[str, list[Query]]:
    folder, hub = area_of(rel)
    nb = json.loads(raw)
    cells = nb.get("cells", [])
    queries: list[Query] = []
    body: list[str] = []
    for i, cell in enumerate(cells):
        src = "".join(cell.get("source", []))
        if not src.strip():
            continue
        if cell.get("cell_type") == "markdown":
            body += [demote_headings(src, by=2), ""]
        elif cell.get("cell_type") == "code":
            body += [fence("python", src), ""]
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for q in extract_queries(tree, src, rel):
                q.owner = f"cell {i}"
                queries.append(q)
    fm = frontmatter({"path": rel, "hub": hub, "cells": len(cells),
                      "tags": ["code/notebook", tag_for(folder, hub)], "github": gh(rel)})
    out = [fm, f"# {Path(rel).name}", "",
           f"`{rel}` · hub {hub_link(folder, hub)} · {len(cells)} cells · [GitHub]({gh(rel)})",
           "", "Outputs are omitted; code and markdown cells are reproduced in order.", ""]
    if queries:
        out += [f"## SQL queries ({len(queries)})", ""]
        for q in queries:
            out += [query_block(q, with_source=False), ""]
    out += ["## Cells", ""] + body
    return "\n".join(out), queries


def workflow_extra(source: str) -> str:
    jobs = re.findall(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", source.split("\njobs:", 1)[-1])
    trig = re.search(r"(?ms)^on:\s*(.*?)^\S", source)
    lines = []
    if trig:
        lines.append("**Triggers:**\n\n" + fence("yaml", trig.group(1).rstrip()))
    if jobs:
        lines.append("**Jobs:** " + ", ".join(f"`{j}`" for j in jobs))
    return "\n\n".join(lines)


# --------------------------------------------------------------------------- #
# Hubs
# --------------------------------------------------------------------------- #

def readme_summary(directory: Path) -> str:
    for name in ("README.md", "claude.md", "CLAUDE.md"):
        path = directory / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = re.sub(r"(?s)```.*?```", "", text)
            paras = [p.strip() for p in text.split("\n\n") if p.strip()
                     and not p.strip().startswith(("#", "[!", "!["))]
            if paras:
                summary = "\n\n".join(paras[:2])
                summary = re.sub(r"\]\((?!https?:)[^)]*\)", "]", summary)  # drop relative links
                return summary + f"\n\n— from `{path.relative_to(REPO_ROOT)}`"
    return ""


def hub_dir(folder: str, name: str) -> Path | None:
    if folder == "Projects":
        d = REPO_ROOT / "MyProjects" / ("shared" if name == "shared signals" else name)
    elif folder == "Pipelines":
        d = REPO_ROOT / "infrastructure" / "pipelines" / name
    else:
        d = {
            "Marimo notebooks": REPO_ROOT / "infrastructure" / "marimo",
            "Agent Graph System": REPO_ROOT / "agent_graph_system",
        }.get(name)
    return d if d and d.exists() else None


def mermaid_graph(files: list[str], edges: dict[str, set[str]]) -> str:
    member = set(files)
    ids = {rel: f"n{i}" for i, rel in enumerate(sorted(member))}
    lines = []
    for rel in sorted(member):
        for target in sorted(edges.get(rel, ())):
            if target in member:
                lines.append(f"    {ids[rel]} --> {ids[target]}")
    if not lines:
        return ""
    used = {x for line in lines for x in re.findall(r"n\d+", line)}
    common = Path(*Path(sorted(member)[0]).parts[:2]) if member else Path()

    def label(r: str) -> str:
        p = Path(r)
        try:
            return str(p.relative_to(common))
        except ValueError:
            return p.name

    nodes = [f'    {ids[r]}["{label(r)}"]' for r in sorted(member) if ids[r] in used]
    return fence("mermaid", "graph LR\n" + "\n".join(nodes + lines))


def write_hub(folder: str, name: str, files: list[str], edges, queries: list[Query],
              non_code: list[str]) -> None:
    d = hub_dir(folder, name)
    fm = frontmatter({"hub": name, "tags": ["hub", tag_for(folder, name)]})
    out = [fm, f"# {name}", ""]
    if d:
        out.append(f"`{d.relative_to(REPO_ROOT)}/` · [GitHub]({GITHUB_BLOB}/{d.relative_to(REPO_ROOT)})")
        out.append("")
        summary = readme_summary(d)
        if summary:
            out += [callout("abstract", "Summary", summary, folded=False), ""]

    graph = mermaid_graph(files, edges)
    if graph:
        out += ["## Internal import graph", "", graph, ""]

    if queries:
        out += [f"## Queries in this {folder[:-1].lower()} ({len(queries)})", ""]
        tables = sorted({t for q in queries for t in q.tables if not t.startswith("{")})
        if tables:
            out += ["Tables touched: " + ", ".join(table_link(t) for t in tables), ""]
        for q in queries:
            out.append(f"- {link(q.rel)} → `{q.owner}` (L{q.line})"
                       + (" — " + ", ".join(table_link(t) for t in q.tables) if q.tables else ""))
        out.append("")

    out += ["## Files", ""]
    by_dir: dict[str, list[str]] = defaultdict(list)
    for rel in sorted(files):
        by_dir[str(Path(rel).parent)].append(rel)
    for directory, members in sorted(by_dir.items()):
        out.append(f"**`{directory}/`**")
        out.append("")
        for rel in members:
            layer = layer_of(rel)
            out.append(f"- {link(rel)}" + (f" · *{layer}*" if layer else ""))
        out.append("")
    if non_code:
        out += ["## Other tracked files (on GitHub)", ""]
        out += [f"- [{rel}]({gh(rel)})" for rel in sorted(non_code)]
    write(VAULT / "Hubs" / folder / f"{name}.md", "\n".join(out))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    for d in GENERATED_DIRS:
        shutil.rmtree(VAULT / d, ignore_errors=True)

    all_files = tracked_files()
    files = [f for f in all_files if wanted(f)]
    py_real = [f for f in files if f.endswith(".py") and not (REPO_ROOT / f).is_symlink()]
    index = build_module_index(py_real + [f for f in files if f.endswith(".py")])

    infos: dict[str, PyInfo] = {}
    sources: dict[str, str] = {}
    for rel in files:
        path = REPO_ROOT / rel
        if path.is_symlink() or not path.exists():
            continue
        sources[rel] = path.read_text(encoding="utf-8", errors="replace")
        if rel.endswith(".py"):
            infos[rel] = analyze_python(rel, sources[rel], index)

    # Symlinked shared signals: point the consumer note at the real file.
    symlinks: dict[str, str] = {}
    for rel in files:
        path = REPO_ROOT / rel
        if path.is_symlink():
            target = (path.parent / path.readlink()).resolve()
            symlinks[rel] = str(target.relative_to(REPO_ROOT))

    edges: dict[str, set[str]] = {rel: set(i.internal) for rel, i in infos.items()}
    for rel, target in symlinks.items():
        edges[rel] = {target}
    for rel, deps in edges.items():
        for i, dep in enumerate(list(deps)):
            if dep in symlinks:  # import of a symlink path → link the real file too
                deps.add(symlinks[dep])
    imported_by: dict[str, set[str]] = defaultdict(set)
    for rel, deps in edges.items():
        for dep in deps:
            imported_by[dep].add(rel)

    all_queries: list[Query] = []
    hub_members: dict[tuple[str, str], list[str]] = defaultdict(list)
    hub_queries: dict[tuple[str, str], list[Query]] = defaultdict(list)
    paired_exports = {f for f in files if f.endswith(".ipynb")
                      and f[: -len(".ipynb")] + ".py" in files}

    for rel in files:
        key = area_of(rel)
        hub_members[key].append(rel)
        out_path = VAULT / f"{note_path(rel)}.md"
        if rel in symlinks:
            target = symlinks[rel]
            write(out_path, "\n".join([
                frontmatter({"path": rel, "symlink_to": target,
                             "tags": ["code/symlink", tag_for(*key)]}),
                f"# {Path(rel).name}", "",
                f"`{rel}` is a **symlink** to the shared signal {link(target, target)}.",
                "", "`lean cloud push` follows the link and uploads the real file's content.",
            ]))
            continue
        src = sources.get(rel)
        if src is None:
            continue
        if rel.endswith(".py"):
            info = infos[rel]
            for q in info.queries:
                all_queries.append(q)
                hub_queries[key].append(q)
            write(out_path, python_note(rel, src, info, imported_by.get(rel, set())))
        elif rel.endswith(".ipynb"):
            if rel in paired_exports:
                twin = rel[: -len(".ipynb")] + ".py"
                write(out_path, "\n".join([
                    frontmatter({"path": rel, "tags": ["code/notebook", tag_for(*key)]}),
                    f"# {Path(rel).name}", "",
                    f"Rendered export of {link(twin, twin)} (kept so GitHub shows outputs). "
                    f"See the `.py` note for the code. [GitHub]({gh(rel)})",
                ]))
                continue
            note, qs = notebook_note(rel, src, index)
            all_queries += qs
            hub_queries[key] += qs
            write(out_path, note)
        elif rel.endswith(".sh"):
            write(out_path, text_note(rel, src, "bash"))
        elif rel.endswith((".yml", ".yaml")):
            write(out_path, text_note(rel, src, "yaml", workflow_extra(src)))
        elif rel == "Dockerfile":
            write(out_path, text_note(rel, src, "dockerfile"))
        else:
            write(out_path, prompt_note(rel, src))

    # Hubs ------------------------------------------------------------------
    hub_non_code: dict[tuple[str, str], list[str]] = defaultdict(list)
    for rel in all_files:
        if not wanted(rel):
            key = area_of(rel)
            if key in hub_members and not rel.endswith((".csv", ".zip", ".png", ".gif")):
                hub_non_code[key].append(rel)
    for key, members in hub_members.items():
        write_hub(*key, members, edges, hub_queries.get(key, []), hub_non_code.get(key, []))

    # SQL catalogue and table notes -----------------------------------------
    sql = [q for q in all_queries if q.kind == "sql"]
    cypher = [q for q in all_queries if q.kind == "cypher"]
    by_table: dict[str, list[Query]] = defaultdict(list)
    for q in sql:
        for t in q.tables:
            if not t.startswith("{"):
                by_table[t.lower()].append(q)
    dynamic = [q for q in sql if q.dynamic]

    for table, qs in by_table.items():
        schema = table.split(".")[0]
        fm = frontmatter({"table": table, "schema": schema, "queries": len(qs),
                          "tags": ["sql/table", f"sql/schema/{schema}"]})
        files_using = sorted({q.rel for q in qs})
        out = [fm, f"# {table}", "",
               f"Schema **{schema}** · read by {len(qs)} quer{'y' if len(qs) == 1 else 'ies'} in "
               + ", ".join(link(f) for f in files_using), "",
               "Back to [[SQL/SQL Catalog|SQL Catalog]]", ""]
        for q in qs:
            out += [f"## {Path(q.rel).name} → {q.owner}", "", query_block(q, with_source=True), ""]
        write(VAULT / "SQL" / "Tables" / f"{safe_name(table)}.md", "\n".join(out))

    schemas: dict[str, list[str]] = defaultdict(list)
    for t in sorted(by_table):
        schemas[t.split(".")[0]].append(t)
    out = [frontmatter({"tags": ["sql", "index"]}), "# SQL Catalog", "",
           f"Every SQL statement found in the workspace: **{len(sql)} queries** over "
           f"**{len(by_table)} tables** in **{len(schemas)} schemas**. "
           "Each query is reproduced verbatim (f-string placeholders kept as `{...}`).", "",
           "## Tables by schema", ""]
    for schema, tables in sorted(schemas.items()):
        out.append(f"- **{schema}**: " + ", ".join(
            f"{table_link(t)} ({len(by_table[t])})" for t in tables))
    out += ["", "## Queries by file", ""]
    by_file: dict[str, list[Query]] = defaultdict(list)
    for q in sql:
        by_file[q.rel].append(q)
    for rel, qs in sorted(by_file.items()):
        out += [f"### {link(rel, rel)}", ""]
        for q in qs:
            out += [query_block(q, with_source=False), ""]
    if dynamic:
        out += ["## Queries with dynamic table names", "",
                "These build the table name from an f-string placeholder; resolved "
                "values come from local assignments and same-file call sites.", ""]
        out += [f"- {link(q.rel)} → `{q.owner}` (L{q.line}): " + "; ".join(
                    f"`{t}` → " + (", ".join(table_link(r) for r in rs) or "unresolved")
                    for t, rs in q.dynamic.items()) for q in dynamic]
    write(VAULT / "SQL" / "SQL Catalog.md", "\n".join(out))

    # Indexes ---------------------------------------------------------------
    out = [frontmatter({"tags": ["cypher", "index"]}), "# Cypher Queries", "",
           f"{len(cypher)} Neo4j Cypher statements in [[Hubs/Areas/Agent Graph System|Agent Graph System]].", ""]
    for q in cypher:
        out += [f"## {Path(q.rel).name} → {q.owner}", "", query_block(q, with_source=True), ""]
    write(VAULT / "Indexes" / "Cypher Queries.md", "\n".join(out))

    externals: dict[str, set[str]] = defaultdict(set)
    for rel, info in infos.items():
        for pkg in info.external:
            externals[pkg].add(rel)
    out = [frontmatter({"tags": ["index"]}), "# External packages", "",
           "Third-party and standard-library modules imported across the workspace.", ""]
    for pkg in sorted(externals, key=str.lower):
        users = sorted(externals[pkg])
        out += [f"## {pkg}", "", f"{len(users)} file(s): " + ", ".join(link(u) for u in users), ""]
    write(VAULT / "Indexes" / "External packages.md", "\n".join(out))

    out = [frontmatter({"tags": ["index"]}), "# All files", "",
           f"{len(files)} source files mirrored into `Code/`.", ""]
    for key in sorted(hub_members):
        out += [f"## {hub_link(*key)}", ""] + [f"- {link(r, r)}" for r in sorted(hub_members[key])] + [""]
    write(VAULT / "Indexes" / "All files.md", "\n".join(out))

    print(f"Vault written to {VAULT.relative_to(REPO_ROOT)}/: {len(files)} file notes, "
          f"{len(hub_members)} hubs, {len(sql)} SQL queries over {len(by_table)} tables, "
          f"{len(cypher)} Cypher queries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
