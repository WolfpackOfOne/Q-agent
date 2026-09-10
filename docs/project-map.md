# Project Map

## Core Workspace Files

| File | Purpose |
|---|---|
| README.md | Public project overview |
| AGENTS.md | AI coding workflow guidelines |
| claude.md | Claude Code and workspace setup |
| CONTRIBUTING.md | Contribution standards |
| SECURITY.md | Credential and security guidance |
| CODE_OF_CONDUCT.md | Participation and enforcement expectations |
| SUPPORT.md | Routing for questions, bugs, and private reports |
| Dockerfile | Multi-stage build for the workspace runtime image |
| .dockerignore | Files excluded from the Docker build context |
| .github/workflows/docker.yml | Builds + publishes the GHCR image |
| .github/CODEOWNERS | Instructor review ownership |
| scripts/create_strategy.py | Renders a valid strategy scaffold |
| scripts/check_repository_policy.py | Enforces contribution and data limits |
| .claude/skills/docker-workflow/SKILL.md | `/docker-workflow` playbook for Docker / GHCR tasks |

## MyProjects

This directory contains:

- Project templates
- Shared LEAN configuration
- Local research storage
- Individual strategy projects

New student strategies are generated here but are ignored by the workspace and
normally initialized as separate repositories. Only instructor-approved example
projects are tracked in Q-agent.

## References

The References directory contains:

- Academic papers
- Research notes
- Upstream open-source repositories
- Books and reference material

Before making the repository public, ensure that copyrighted or proprietary material is not redistributed improperly.

## Docs

The docs directory contains onboarding, architecture, and workflow documentation intended for students and contributors.
