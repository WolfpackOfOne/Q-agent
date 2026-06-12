# Public Release Checklist

## Repository Hygiene

- Review commit history
- Remove sensitive files
- Remove credentials
- Remove local machine paths
- Remove proprietary datasets

## Documentation

- README updated
- Architecture documented
- Setup instructions verified
- Contribution rules added
- Security guidance added

## Open Source Standards

- License added
- Pull request template added
- Issue templates added
- CI workflows added

## Student Experience

- Reproducible examples available
- Notebook workflows documented
- Clear project structure
- Research examples documented

## Engineering Validation

These map to the CI workflows under `.github/workflows/` — confirm each is
green on the release commit:

- Tests pass — `tests.yml` (`pytest -m "not integration"`, plus the
  `tests/hygiene/` checks that shell out to git)
- Docs build clean — `docs.yml` runs `mkdocs build --strict` (fails on missing
  nav pages or broken internal refs)
- Docs links resolve — `docs.yml` runs the `lychee` link-checker (`fail: true`)
  over `docs/**/*.md` and root markdown
- Docker image builds and smoke-tests pass — `docker.yml` (lean CLI loads,
  infrastructure/marimo imports, in-image pytest, demo project present,
  no secrets in layers)
- No secrets committed — `secret-scan.yml`
- Dependencies resolve from a clean environment — `pip install` of
  `requirements-dev.txt`, `infrastructure/requirements.txt`, and
  `infrastructure/marimo/requirements.txt`
- LEAN compatibility — `LEAN_VERSION` build arg pins the CLI; confirm the
  pinned version still pushes/backtests in the cloud
- Example notebook executes headless — run the marimo `.py` as a script and
  confirm no cell raises

## Final Review

- Test clone from a clean machine
- Verify onboarding steps
- Verify links
- Verify ignored files
