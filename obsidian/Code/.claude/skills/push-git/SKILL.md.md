---
path: ".claude/skills/push-git/SKILL.md"
hub: "Claude agents and skills"
tags:
  - "prompt"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/push-git/SKILL.md"
---
# push-git

`.claude/skills/push-git/SKILL.md` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/push-git/SKILL.md)

> [!abstract] Description
> Commit and push the QuantConnect repo to Git and GitHub. Handles staging, committing, marimo notebook rendering, and pushing. Use when the user wants to push to GitHub (not QuantConnect Cloud).

| Key | Value |
|---|---|
| argument-hint | `[commit message]` |
| disable-model-invocation | `true` |
| allowed-tools | `` |

## Prompt

### Push Git Skill

Commit all pending changes and push to Git/GitHub.

#### Usage

```text
/push-git [commit message]
```

Examples:

- `/push-git` — auto-generates commit message from changes
- `/push-git "Add yfinance pipeline"` — uses provided message

#### Workflow

##### 1. Inspect Current State

```bash
git status --short
git remote -v
git branch --show-current
git log --oneline -5
```

Review what will be committed. Summarize the changes for the user.

##### 2. Check for Marimo Notebooks

Scan all staged and modified `.py` files for marimo notebooks:

```bash
# For each changed .py file, check if it's a marimo notebook
head -20 "<file>" | grep -q 'marimo.App'
```

If any marimo notebooks are found among the changed files, **ask the user**:

> Found marimo notebooks in changed files:
> - `<path/to/notebook.py>`
>
> Would you like to render them to `.ipynb` for GitHub viewing? (This runs `marimo export` with outputs.)

If the user says yes, export each notebook:

```bash
infrastructure/marimo/venv/bin/marimo export ipynb "<notebook.py>" -o "<notebook.ipynb>" --include-outputs
```

Then stage the generated `.ipynb` files alongside the other changes.

If the user says no, skip rendering and proceed with the commit.

##### 3. Stage Changes

Stage all relevant files. Use specific file paths rather than `git add -A` when possible.

Do NOT stage:
- `.env`, credentials, secrets
- `config.json` files
- `backtests/`, `__pycache__/`, `.ipynb_checkpoints/`
- Files in `.gitignore`

If there are many files, group them logically and stage by directory or pattern.

##### 4. Commit

If a commit message was provided as an argument, use it. Otherwise, generate a concise commit message based on the changes.

For large changesets, consider asking the user whether to split into multiple commits or do one big commit.

##### 5. Push to GitHub

```bash
git push origin <current-branch>
```

Do not force-push unless the user explicitly asks.

##### 6. Report Results

```text
Commit: <short hash> <message>
Push: origin/<branch> — success / failed
Notebooks rendered: <list> / none
```

#### Safety Rules

- Always inspect `git status` before committing
- Never commit secrets, credentials, or `config.json`
- Never use `git push --force` unless explicitly requested
- Never stage files matching `.gitignore` patterns
- Ask before creating multiple commits (don't assume)
