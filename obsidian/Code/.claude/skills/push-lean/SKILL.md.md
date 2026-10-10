---
path: ".claude/skills/push-lean/SKILL.md"
hub: "Claude agents and skills"
tags:
  - "prompt"
  - "areas/Claude-agents-and-skills"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/push-lean/SKILL.md"
---
# push-lean

`.claude/skills/push-lean/SKILL.md` · hub [[Hubs/Areas/Claude agents and skills|Claude agents and skills]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/.claude/skills/push-lean/SKILL.md)

> [!abstract] Description
> Push a QuantConnect project to QuantConnect Cloud via lean cloud push. Use when the user wants to deploy a LEAN algorithm to the cloud.

| Key | Value |
|---|---|
| argument-hint | `[project-name]` |
| disable-model-invocation | `true` |
| allowed-tools | `` |

## Prompt

### Push LEAN Skill

Push a QuantConnect project to its configured Git remote and to QuantConnect Cloud.

#### Usage

```text
/push-lean [project-name]
```

Examples:

- `/push-lean`
- `/push-lean MomentumETF`
- `/push-lean "My Strategy"`

#### Purpose

Use this skill when the user wants to:

- push or sync a project to QuantConnect Cloud
- deploy the latest changes to QC
- send changes to GitHub and QuantConnect Cloud

This skill is generic and should work for any project under:

```text
~/Documents/Q-agent/MyProjects/<ProjectName>
```

#### Project Resolution

Determine the target project in this order:

1. If the command includes a project name, use it.
2. If the current working directory is inside `MyProjects/<ProjectName>`, use that project.
3. Otherwise, ask the user which project to push.

#### Preconditions

Before pushing, verify:

- project directory exists under `MyProjects/`
- project is a Git repository
- shared LEAN CLI exists at `~/Documents/Q-agent/venv/bin/lean`
- `MyProjects/lean.json` exists

If Git remote configuration is missing, stop and tell the user the project needs to be connected first.

If QuantConnect Cloud push is not configured or fails because the project is not connected, report that clearly and tell the user the project needs to be connected to QuantConnect Cloud before this skill can complete.

#### Workflow

##### 1. Inspect Current State

From the project directory:

```bash
git status --short
git status -sb
git remote -v
git branch --show-current
```

Review what is about to be pushed before staging or committing.

##### 2. Validate Changed Python Files

If there are changed `.py` files, run syntax validation before committing.

Prefer validating only changed files. For example:

```bash
python -m py_compile main.py
python -m py_compile models/*.py domain/*.py
```

If validation fails, stop and fix the issue before pushing.

##### 3. Commit Local Changes

If there are uncommitted changes:

1. Stage the relevant project files
2. Create a clear commit message
3. Do not create a commit if there are no changes

Ask the user for a commit message only when the intent is unclear. Otherwise, use a concise imperative message based on the actual change.

##### 4. Push to Git Remote

From the project directory:

```bash
git push
```

Do not force-push unless the user explicitly asks.

##### 5. Push to QuantConnect Cloud

Use the shared workspace environment and run from `MyProjects`:

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
lean cloud push --project "<ProjectName>" --force
```

Use `--force` for the LEAN cloud push to avoid collaboration lock issues.

##### 6. Report Results

Report separately:

- Git commit result
- Git push result
- LEAN cloud push result
- any blockers or follow-up needed

#### Safety Rules

- Always inspect `git status` before committing
- Never commit ignored artifacts or generated outputs
- Never commit `config.json`
- Never commit `backtests/`, `__pycache__/`, `.ipynb_checkpoints/`, or secrets
- Never use `git push --force` unless explicitly requested
- Stop if syntax validation fails

#### If the Project Is Not Connected Yet

If the project has no Git remote or no working QuantConnect Cloud connection, do not guess. Tell the user what is missing and stop before pushing.

#### Recommended Output Format

When reporting completion, include:

```text
Project: <ProjectName>
Commit: created / not needed / failed
Git push: success / failed
LEAN cloud push: success / failed
Next step: <only if needed>
```
