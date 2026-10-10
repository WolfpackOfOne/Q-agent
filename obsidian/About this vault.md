---
tags:
  - meta
---
# About this vault

Back to [[Home]]

## Opening it

In Obsidian, choose **Open folder as vault** and select the `obsidian/` folder of your Q-agent checkout. Graph view looks best with the colour groups configured in `.obsidian/graph.json`.

Optional plugins: **Dataview**, which powers the tables in [[WRDS Pipeline Walkthrough]] and frontmatter queries such as `TABLE layer, lines FROM "Code/MyProjects"`. Mermaid diagrams render natively.

## What's generated and what's hand-written

| Folder / note | Source |
|---|---|
| `Code/` | **Generated.** One note per tracked `.py`, `.sh`, `.ipynb`, workflow, Dockerfile and agent/skill prompt, at the same path as in the repo |
| `SQL/` | **Generated.** [[SQL/SQL Catalog\|SQL Catalog]] plus one note per database table |
| `Hubs/` | **Generated.** One per project, pipeline and area, with a README summary, internal import graph, queries and file list |
| `Indexes/` | **Generated.** All files, external packages, Cypher queries |
| `Home`, `Architecture`, `Data Lineage`, `WRDS Pipeline Walkthrough`, this note | **Hand-written** |

Regenerate after code changes. This rewrites only the generated folders:

```bash
python scripts/build_obsidian_vault.py
```

## What a code note contains

1. **Frontmatter:** `path`, `hub`, `layer` (for strategy files), `lines`, `tags`, `github`
2. **Purpose:** the module docstring
3. **Dependencies:** workspace imports and *imported by* as links, plus external packages
4. **SQL / Cypher queries:** every query string, verbatim, with its enclosing function, line, tables, f-string placeholders and call sites
5. **Constants, classes (with methods), functions:** signatures, docstrings and GitHub line links
6. **Source:** the full file in a collapsed callout, so it's searchable in Obsidian

## How queries are found

A query is any string literal or f-string containing `SELECT … FROM` that isn't a docstring. Cypher is only searched for in `agent_graph_system/`. The tables come from the `FROM` and `JOIN` clauses. For placeholders such as `{schema}.{table}`, the generator works out the values from simple local assignments, `x if cond else y` expressions (keeping branches that share a condition paired), parameter defaults and same-file call sites. Anything it can't resolve is reported as *unresolved*. It does not guess.

## Tags

- `code/python`, `code/notebook`, `code/bash`, `code/yaml`, `code/symlink`, `prompt`
- `projects/<name>`, `pipelines/<name>`, `areas/<name>`
- `has/sql`, `has/cypher`
- `sql/table`, `sql/schema/<schema>`
