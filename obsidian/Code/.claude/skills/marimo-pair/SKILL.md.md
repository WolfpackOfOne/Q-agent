---
path: ".claude/skills/marimo-pair/SKILL.md"
hub: "Claude agents and skills"
tags:
  - "prompt"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/marimo-pair/SKILL.md"
---
# marimo-pair

`.claude/skills/marimo-pair/SKILL.md` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/marimo-pair/SKILL.md)

> [!abstract] Description
> >-

| Key | Value |
|---|---|
| allowed-tools | `` |

## Prompt

### marimo Pair Programming Protocol

This skill gives you full access to a running marimo notebook. You can read
cell code, create and edit cells, install packages, run cells, and inspect
the reactive graph — all programmatically. The user sees results live in their
browser while you work through bundled scripts or MCP.

#### Philosophy

marimo notebooks are a dataflow graph — cells are the fundamental unit of
computation, connected by the variables they define and reference. When a cell
runs, marimo automatically re-executes downstream cells. You have full access
to the running notebook.

- **Cells are your main lever.** Use them to break up work and choose how and
  when to bring the human into the loop. Not every cell needs rich output —
  sometimes the object itself is enough, sometimes a summary is better.
  Match the presentation to the intent.
- **Understand intent first.** When clear, act. When ambiguous, clarify.
- **Follow existing signal.** Check imports, `pyproject.toml`, existing cells,
  and `dir(ctx)` before reaching for external tools.
- **Stay focused.** Build first, polish later — cell names, layout, and styling
  can wait.

#### Prerequisites

##### How to invoke marimo

Only servers started with `--no-token` register in the local server registry
and are auto-discoverable — starting without a token makes discovery easier.
If a server has a token, set the `MARIMO_TOKEN` environment variable before
calling the execute script (avoids leaking the token in process listings). The
right way to invoke marimo depends on context (project
tooling, global install, sandbox mode). See
[finding-marimo.md](reference/finding-marimo.md) for the full decision tree.

**Do NOT use `--headless` unless the user asks for it.** Omitting it lets
marimo auto-open the browser, which is the expected pairing experience. If the
user explicitly requests headless, offer to open `http://localhost:<port>`
in their browser (`open` on macOS, `xdg-open` on Linux, `start` on Windows).

#### Troubleshooting

##### `SyntaxError` or `ImportError` from `execute-code.sh`

Code runs **inside the running marimo kernel** — `execute-code.sh` POSTs it
over HTTP and never invokes a local Python. So errors here are not caused by
the local Python version, missing venv, or `uv` vs `pip` — they're problems
with the code being sent. Fix the code (use a heredoc for anything
multiline; don't try to one-line compound statements with `;`).

##### User keeps getting prompted to allow Bash commands

The skill declares `allowed-tools` in its frontmatter, but Claude Code may
still prompt for each Bash call. To fix this, the user should add the absolute
paths to the scripts to their `.claude/settings.json` (project-level) or
`~/.claude/settings.json` (global):

```json
{
  "permissions": {
    "allow": [
      "Bash(bash /absolute/path/to/skills/marimo-pair/scripts/discover-servers.sh *)",
      "Bash(bash /absolute/path/to/skills/marimo-pair/scripts/execute-code.sh *)"
    ]
  }
}
```

#### How to Discover Servers and Execute Code

Two operations: **discover servers** and **execute code**.

| Operation | Script | MCP |
|-----------|--------|-----|
| Discover servers | `bash scripts/discover-servers.sh` | `list_sessions()` tool |
| Execute code | `bash scripts/execute-code.sh -c "code"` | `execute_code(code=..., session_id=...)` tool |
| Execute code (multiline) | `bash scripts/execute-code.sh <<'EOF'` | same |
| Execute code (by URL) | `bash scripts/execute-code.sh --url http://localhost:2718 -c "code"` | same (with `url` param) |

Scripts auto-discover sessions from the local server registry. Use
`--port` to target a specific server when multiple are running,
`--session` to target a specific session when multiple notebooks are
open on the same server, or `--url` to skip discovery and connect to a
server by URL (e.g. `--url http://localhost:2718`). **On Windows, prefer
direct `--url` when registry discovery is empty** — see the next section
for why. Set the `MARIMO_TOKEN` env var to authenticate when the server
has token auth enabled (`--token` flag also works but exposes the token
in process listings). If the server was started with `--mcp`, you'll
have MCP tools available as an alternative.

##### Discovery finds nothing but the user has a server running?

Only `--no-token` servers are in the registry. If discovery comes up empty,
the server likely has token auth — ask the user for the token and set it as
the `MARIMO_TOKEN` environment variable.

On **Windows (Git Bash / MSYS2)**, discovery can also come up empty even for
a running `--no-token` server. If the user confirms marimo is reachable
locally, fall back to `--url http://127.0.0.1:<port>` (ask for the port).

##### No servers running?

**Always discover before starting.** Background task "completed" notifications
do not mean the server died — check the output or run discover first.

If no servers are found, read the user's intent — if they want a notebook,
start one. **Always start marimo as a background task** (using
`run_in_background` on the Bash tool) so the server automatically gets cleaned
up when the session ends and doesn't block the conversation. See
[finding-marimo.md](reference/finding-marimo.md).

If there's no `.py` file yet, pick a descriptive filename based on context
(e.g., `exploration.py`, `analysis.py`, `dashboard.py`). Don't ask — just
pick something reasonable.

**Avoid shell escaping issues.** `-c` works for simple one-liners, but for
multiline code or code with quotes/backticks/`${}`, use a heredoc or a file:

```bash
# heredoc (single-quoted delimiter prevents shell interpolation)
bash scripts/execute-code.sh <<'EOF'
import marimo._code_mode as cm

async with cm.get_context() as ctx:
    ctx.create_cell("x = 1")
EOF

# file
bash scripts/execute-code.sh /tmp/code.py

# target a specific port (skips auto-selection when multiple servers run)
bash scripts/execute-code.sh --port 2718 -c "1 + 1"
```

#### Executing Code

Every execute-code call runs inside the notebook's kernel. All cell variables
are in scope — `print(df.head())` just works. Nothing you define persists
between calls (variables, imports, side-effects all reset), but you can freely
introspect the notebook: inspect variables, test code snippets, check types
and shapes. Use this to explore, prototype, and validate before committing
anything to the notebook — then create cells to persist state and make results
visible to the user.

To mutate the notebook's dataflow graph — create, edit, and delete cells,
install packages, and run cells — use `marimo._code_mode`:

```python
import marimo._code_mode as cm

async with cm.get_context() as ctx:
    cid = ctx.create_cell("x = 1")
    ctx.packages.add("pandas")
    ctx.run_cell(cid)
```

You **must** use `async with` — without it, operations silently do nothing.
All `ctx.*` methods are **synchronous** — they queue operations and the
context manager flushes them on exit. Do **not** `await` them.

The kernel supports top-level `await`, so use `async with` directly. Do
**not** wrap calls in `async def main(): ...` + `asyncio.run(main())` — it's
unnecessary and easy to get wrong (compound statements like `async with`
can't follow `def name():` on the same line, so cramming it into a `-c`
one-liner produces a `SyntaxError`).

**Cells are not auto-executed.** `create_cell` and `edit_cell` are structural
changes only — use `run_cell` to queue execution.

`code_mode` is a tested, safe API for notebook mutations — prefer it for all
structural changes. You also have access to marimo internals from the kernel,
but treat that as a last resort and only with high confidence after exploration.

**Edit cells through `code_mode`, never the file system. Direct file writes
are silently lost.** It is tempting to reach for `Edit`/`Write` for a small
tweak since `edit_cell` requires the full new cell body. Don't — without
`--watch` (off by default) the kernel never sees those edits and overwrites
them on its next save, so the user sees nothing. (`Read` on the `.py` is
okay, but content may lag the live kernel; prefer `ctx.cells[target].code`.)

**UI state lives outside the reactive graph.** Anywidget traitlets can be read
or set directly (e.g., `slider.value = 5`). For `mo.ui.*` elements, use
`ctx.set_ui_value(element, new_value)` inside `code_mode`.

##### First Step: Explore the API

The `code_mode` API can change between marimo versions. Explore it at the
start of each session — dig deeper into anything you're unsure about.

```python
import marimo._code_mode as cm
help(cm)
```

#### Writing Cells That Actually Work

marimo's reactive graph is the #1 source of silent failures. Understand these
rules before writing any cell:

##### Every top-level assignment is a cell export

marimo treats every variable assigned at the top level of a cell as an export
into the reactive graph. If two cells both assign `fig`, `ax`, `df`, `h`, or
any other name — even if the variables are logically unrelated —
`MultipleDefinitionError` kills both cells. **This includes loop variables.**

```python
# WRONG — two cells both define fig, ax, h
# Cell A                           # Cell B
fig, ax = plt.subplots(...)        fig = plt.figure(...)
h = df["col"].dropna()             h = df["other"].dropna()

# RIGHT — unique names everywhere
# Cell A                           # Cell B
fig_hist, ax_hist = ...            fig_3d = plt.figure(...)
_h = df["col"].dropna()            _h2 = df["other"].dropna()
```

Rules:
- **Unique names across all cells** for any variable you assign at the top
  level. Use descriptive suffixes: `fig_hist`, `fig_3d`, `ax_eq`, `ax_scatter`.
- **Prefix throwaway variables with `_`**: `for _ticker in ...`,
  `_h = df["col"].dropna()`. Underscore-prefixed names are not exported.
- **Watch out for common collisions**: `fig`, `ax`, `df`, `data`, `result`,
  `x`, `y`, `i`, `j`, `h`, `s`, `e` — these cause conflicts constantly.

##### Function cells vs statement cells — know the difference

A cell whose body is `def _(params): ...` is a **function cell**. A cell with
bare statements is a **statement cell**. They behave differently:

| | Function cell | Statement cell |
|---|---|---|
| Body executes when... | marimo calls it (when a downstream cell consumes its return) | Immediately when the cell runs |
| Receives variables via... | Function parameters: `def _(df, plt):` | Reactive graph (must be defined by another cell) |
| Exports variables via... | `return (var1, var2)` tuple | Any top-level assignment |
| Plot displays when... | A downstream cell consumes the returned `fig` | The last expression is the fig object |

**Critical consequence**: If a function cell returns `fig` but no downstream
cell uses `fig`, **the function body never runs and the plot never renders.**
The user sees an empty cell with just a function definition.

**Recommendation for analysis notebooks**: Use **function cells** consistently.
They're the idiomatic marimo pattern — parameters declare dependencies
explicitly, return tuples declare outputs, and marimo handles the execution
order. Just make sure every returned variable is consumed by at least one
downstream cell.

##### Don't mix paradigms

Mixing function cells and statement cells in the same notebook causes confusing
failures. Statement cells can only see variables defined by other statement
cells. They cannot access values from function cells' return tuples.

Pick one style and stick with it. Function cells are the safer default.

##### Path resolution with `__file__`

`pathlib.Path(__file__).resolve()` points to the notebook `.py` file. Count
`.parents[]` carefully — verify the resolved path with a `print()` before
using it. A wrong parent index silently points to the wrong directory and
downstream cells fail with missing-file errors.

##### Kill the server before rewriting the file

If you need to rewrite the notebook `.py` file (not just edit cells via
`code_mode`), **kill the marimo process first**:

```bash
pkill -f "marimo edit.*my_notebook"
sleep 1
# Now safe to write the file
cat > path/to/notebook.py << 'EOF'
...
EOF
# Restart
marimo edit path/to/notebook.py --no-token &
```

The `Write` and `Edit` tools will often fail with "file modified since read"
because marimo reformats the file on open. Use `cat > file << 'EOF'` via Bash
to bypass this.

#### Guard Rails

Skip these and the UI breaks:

- **Install packages via `ctx.packages.add()`, not `uv add` or `pip`.**
  The code API handles kernel restarts and dependency resolution correctly.
  Only fall back to external CLIs if the API is unavailable or fails.
- **Custom widget = anywidget.** For bespoke visual components, use anywidget
  with HTML/CSS/JS. Composed `mo.ui` is fine for simple forms and controls.
  See [rich-representations.md](reference/rich-representations.md).
- **NEVER `Edit`, `Write`, or `NotebookEdit` the notebook `.py` file while a
  session is running. Direct writes are silently destroyed and never reach the
  user.** marimo only watches the file with `--watch`, which is off by
  default. Without it, the kernel doesn't pick up file edits — and on its
  next save, the kernel writes its own state and clobbers yours. The user sees
  no change, you think the work landed, and the bug is invisible. Always use
  `ctx.edit_cell(target, code=...)` with the full new cell body — even for a
  one-character change. (`Read` is allowed, but disk content may lag the live
  kernel; for the current truth prefer `ctx.cells[target].code`.)
- **No temp-file deps in cells.** `pathlib.Path("/tmp/...")` in cell code is a bug.
- **Avoid empty cells.** Prefer `edit_cell` into existing empty cells rather
  than creating new ones. Clean up any cells that end up empty after edits.
- **Don't worry about cell names.** Most cells don't need explicit names —
  see [notebook-improvements.md](reference/notebook-improvements.md#cell-names).

#### Widgets and Reactivity

Anywidget state (traitlets) lives outside marimo's reactive graph. To hook a
widget trait into the graph, pick one strategy per widget — never mix them:

- **`mo.state` + `.observe()`** — you pick specific traits to bridge. Default choice.
- **`mo.ui.anywidget()`** — wraps all synced traits into one reactive `.value`. Convenient but coarser.

Read [rich-representations.md](reference/rich-representations.md) before wiring either.

#### Keep in Mind

- **The user is editing too.** The notebook can change between your calls —
  re-inspect notebook state if it's been a while since you last looked.
- **Deletions are destructive.** Deleting a cell removes its variables from
  kernel memory — restoring means recreating the cell and re-running it and
  its dependents. If intent seems ambiguous, ask first.
- **Installing packages changes the project.** `ctx.packages.add()` adds
  real dependencies — confirm when it's not obvious from context.

#### References

- [finding-marimo.md](reference/finding-marimo.md) — how to find and invoke the right marimo
- [gotchas.md](reference/gotchas.md) — cached module proxies and other traps
- [rich-representations.md](reference/rich-representations.md) — custom widgets and visualizations
- [notebook-improvements.md](reference/notebook-improvements.md) — improving existing notebooks
