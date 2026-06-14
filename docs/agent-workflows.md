# Agent Workflows

## Overview

Q-agent is designed to support AI-assisted quantitative research and development workflows.

The repository emphasizes:

- reproducibility
- modularity
- safe AI-assisted development
- deterministic research workflows
- educational readability

---

## Recommended Agent Workflows

### Claude Code

Suggested use cases:

- notebook generation
- LEAN strategy refactoring
- diagnostics generation
- documentation drafting
- pipeline scaffolding

### Project-scoped skills

Reusable knowledge for this workspace lives in `.claude/skills/`. Skills are markdown playbooks with a frontmatter whitelist of tools; invoke one with a slash command from Claude Code.

| Skill | Purpose |
|---|---|
| `/docker-workflow` | Build, smoke-test, publish, and verify the Q-agent Docker image. Handles `LEAN_VERSION` bumps, GHCR pull verification, CI debugging. See [Docker](docker.md). |
| `/marimo-pair` | Pair-program inside a running marimo notebook. |
| `/push-git` | Wrap the canonical workspace push flow (branch → PR → merge). |
| `/push-lean` | Push the active project to QuantConnect with `lean cloud push --force`. |
| `/run-local-research-notebook` | Boot a research notebook against local pipeline data. |

---

## A safe agent session pattern

Use this pattern when asking an AI coding agent to change Q-agent:

```text
1. Inspect the issue, linked docs, and relevant files.
2. State the intended change and non-goals.
3. Create a feature branch.
4. Make the smallest useful change.
5. Run focused tests or docs checks.
6. Update docs if behavior changed.
7. Open a PR with known limitations and a test plan.
```

Example prompt:

```text
Review issue #73 and make the smallest PR that adds issue templates and strengthens the PR template. Do not change unrelated docs. Run or describe the docs checks needed before merge.
```

This keeps the agent from rewriting too much of the repo at once and makes PR review easier.

---

## Safe refactoring checklist

Before accepting agent-generated changes, confirm:

- the change stays on a feature branch
- the diff is focused
- no credentials, local paths, or generated datasets are committed
- tests or docs checks are included in the PR description
- architecture layering is preserved
- notebooks remain reproducible
- data-source limitations are documented

---

## Repository Philosophy

Q-agent encourages:

- thin orchestration layers
- pure domain logic
- reusable signals
- notebook-driven research
- deterministic outputs

---

## Safe Refactoring Patterns

Recommended practices:

- keep `main.py` thin
- isolate signal logic in `domain/`
- avoid giant orchestration files
- preserve notebook reproducibility
- avoid hidden state

---

## Notebook Workflows

Recommended notebook behavior:

- deterministic outputs
- explicit dependencies
- reproducible charts
- environment-independent paths
- structured exports

---

## Guardrails

Agents should:

- never commit credentials
- avoid hardcoded local paths
- preserve reproducibility
- preserve architecture layering
- avoid modifying generated datasets directly

---

## Future Directions

Potential future workflows:

- automated diagnostics notebooks
- AI-assisted signal engineering
- reproducible research templates
- agent evaluation workflows
- shared project memory standards
