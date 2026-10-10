---
path: ".claude/skills/run-local-research-notebook/SKILL.md"
hub: "Claude agents and skills"
tags:
  - "prompt"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/SKILL.md"
---
# run-local-research-notebook

`.claude/skills/run-local-research-notebook/SKILL.md` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/run-local-research-notebook/SKILL.md)

> [!abstract] Description
> Run a local QuantConnect research notebook in the correct LEAN Docker environment, inspect executed outputs, extract rendered charts, and interpret the results. Use when the user asks to run, debug, validate, or explain a notebook under MyProjects/*/research/*.ipynb.

| Key | Value |
|---|---|
| argument-hint | `[MyProjects/<Project>/research/<notebook>.ipynb]` |

## Prompt

### Run Local Research Notebook

Use this skill for QuantConnect research notebooks in this workspace. Follow `~/Documents/Q-agent/AGENTS.md` first. The key rule is: do not guess from the raw `.ipynb` file alone when a local LEAN research container already exists.

#### When To Use

- The user asks to run a notebook under `MyProjects/*/research/*.ipynb`
- The user wants to debug notebook execution in local LEAN research
- The user wants a plot, table, or notebook output interpreted

#### Inputs

`$ARGUMENTS` should be a notebook path such as:

```text
MyProjects/60_40 Test/research/plots.ipynb
```

If the user gives only a notebook name or a partial path, resolve it before running anything.

#### Workflow

##### 1. Resolve the notebook and project

- Confirm the notebook exists in the workspace.
- Derive:
  - `project_name`: parent directory above `research/`
  - `notebook_name`: basename, for example `plots.ipynb`
  - `notebook_stem`: basename without `.ipynb`

Read any project-level `AGENTS.md`, `claude.md`, or `docs/` files if they exist. If they do not exist, continue with the workspace-level `AGENTS.md`.

##### 2. Prefer an existing research container

List active research containers:

```bash
docker ps --format 'table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}'
```

Find the container that has the notebook mounted at `/LeanCLI/research/<notebook_name>`:

```bash
docker exec <container_id> sh -lc 'test -f "/LeanCLI/research/<notebook_name>" && echo NOTEBOOK_PRESENT || echo NOTEBOOK_MISSING'
```

Use the matching container. This matches the notebook-debugging workflow in `AGENTS.md`.

##### 3. If no matching container exists

Do not run the notebook with plain local Python.

Ask before launching a new research session because `lean research` is interactive:

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
lean research "<ProjectName>"
```

After the session starts, repeat container discovery and continue inside the container.

##### 4. Execute the notebook headlessly in the container

Run the notebook with `nbconvert` from `/LeanCLI`:

```bash
docker exec <container_id> sh -lc 'cd /LeanCLI && jupyter nbconvert --to notebook --execute "research/<notebook_name>" --output "/tmp/<notebook_stem>.executed.ipynb"'
```

This keeps the user notebook unchanged and produces an executed copy in `/tmp`.

If `nbconvert` fails earlier than the live Jupyter session, inspect the traceback and consider:

- `docker logs <container_id>`
- Running the failing code directly inside the same container
- Comparing saved notebook outputs with the headless run

##### 5. Copy the executed notebook back to the host

Workspace-level skills under `~/Documents/Q-agent/.claude/skills/` are not mounted inside `/LeanCLI`. Copy the executed notebook out of the container before using the bundled helper scripts:

```bash
docker cp <container_id>:/tmp/<notebook_stem>.executed.ipynb /tmp/<notebook_stem>.executed.ipynb
```

##### 6. Inspect the executed outputs

Use the bundled helper script from the workspace root:

```bash
python ~/Documents/Q-agent/.claude/skills/run-local-research-notebook/scripts/summarize_notebook_outputs.py "/tmp/<notebook_stem>.executed.ipynb"
```

Look for:

- `error` outputs and traceback details
- `stream` output with printed diagnostics
- `display_data` or `execute_result`
- `image/png` plots

##### 7. Extract the first rendered plot when present

If the executed notebook contains `image/png`, export it back into the project `research/` directory:

```bash
python ~/Documents/Q-agent/.claude/skills/run-local-research-notebook/scripts/extract_first_png.py "/tmp/<notebook_stem>.executed.ipynb" "~/Documents/Q-agent/MyProjects/<Project>/research/<notebook_stem>.executed.png"
```

This makes the image available in the workspace as:

```text
MyProjects/<Project>/research/<notebook_stem>.executed.png
```

##### 8. Interpret the notebook result

Never claim you visually inspected a plot unless you actually opened the rendered image. If direct image inspection is unavailable, interpret the chart from:

- The plotting code in the notebook
- The executed outputs
- Additional stats computed inside the same container

When a chart needs interpretation:

1. Read the plotting cell to identify:
   - chart type
   - series being plotted
   - date range
   - transformations such as raw price, normalized return, cumulative return, rolling window, or log scale
   - whether multiple y-axes are used
2. If the chart alone is not enough, create a temporary notebook copy in `/tmp`, append a diagnostic cell, execute that copy, and read the resulting stats. Do not edit the user's notebook just to inspect it.
3. Summarize what the image shows in plain terms:
   - trend direction
   - major turning points
   - approximate start/end levels
   - relative volatility
   - whether the picture supports the notebook's intended claim
4. Call out chart-design caveats when relevant:
   - dual-axis charts can exaggerate comparability
   - raw prices are not the same as normalized performance
   - price-only charts may omit dividends or total return
   - truncated axes can distort magnitude

##### 9. Response format

Report the result compactly:

- execution status
- container used
- executed notebook path
- extracted image path, if any
- key outputs or errors
- interpretation with caveats

#### Example Invocation

```text
/run-local-research-notebook MyProjects/60_40 Test/research/plots.ipynb
```

#### Constraints

- Do not edit `Lean/`
- Do not modify the source notebook unless the user asked for changes
- Prefer the active LEAN research container over ad hoc local execution
- Keep all notebook-specific diagnostics inside the same container so `QuantBook()`, mounted storage, and LEAN config stay consistent
