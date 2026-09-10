# Course Release Checklist

Use this checklist before publishing a version that students will share.

## Repository controls

- [ ] `main` requires a pull request, one approval, approval of the latest push,
      resolved conversations, and a current branch.
- [ ] `Tests`, `Docs`, `Security`, `Repository policy`, `Docker`, `CodeQL`, and
      `Dependency review` are required checks.
- [ ] Force pushes and deletion are blocked; there are no student bypass actors.
- [ ] Students use forks; only trusted instructors or TAs receive upstream write
      access.
- [ ] CODEOWNERS, issue forms, PR template, code of conduct, support, and private
      security reporting are present.
- [ ] GitHub Actions use immutable SHAs and least-privilege tokens.
- [ ] Dependency alerts, security updates, secret scanning, push protection, and
      code scanning are enabled.

## Content and documentation

- [ ] Onboarding commands were tested from a clean clone on each supported OS.
- [ ] `python scripts/create_strategy.py ReleaseSmokeTest` produces valid Python
      without unresolved tokens.
- [ ] README, Getting Started, Docker, contribution, testing, credential, and
      security guidance describe current behavior.
- [ ] Dataset sources and redistribution terms are documented.
- [ ] No credentials, personal paths, proprietary data, generated backtests, or
      unnecessary notebook output are tracked.

## Engineering validation

- [ ] `pytest -m "not integration"` passes on Python 3.11 and 3.12.
- [ ] `python scripts/check_repository_policy.py --all` passes.
- [ ] `mkdocs build --strict` and the GitHub link check pass.
- [ ] CodeQL and dependency review pass.
- [ ] The Docker image builds, imports its core packages, runs tests, contains the
      demo project, and has no secret references in its layers.
- [ ] Relevant LEAN cloud backtests and example notebooks were run manually.

## Publish

1. Merge the release PR after required review and checks.
2. Create a semantic version tag such as `v0.1.0` from the verified `main` commit.
3. Wait for the versioned multi-architecture GHCR image to publish.
4. Create GitHub release notes that identify the commit, image tag, supported
   Python versions, known limitations, and student upgrade instructions.
5. Pull the versioned image from a clean machine and run the quickstart.
6. Keep course material pinned to the version tag; use `latest` only for
   development.
