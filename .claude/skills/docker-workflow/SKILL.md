---
name: docker-workflow
description: Build, smoke-test, publish, and verify the Q-agent Docker image (LEAN CLI + infrastructure pipelines + marimo). Handles LEAN_VERSION bumps, local iteration, GHCR pull verification, and CI debugging for the docker workflow.
argument-hint: "[task] — e.g. 'bump lean to 1.0.226', 'rebuild and smoke-test', 'verify ghcr pull', 'check docker CI'"
allowed-tools:
  - Bash(docker build:*)
  - Bash(docker run:*)
  - Bash(docker pull:*)
  - Bash(docker history:*)
  - Bash(docker logout:*)
  - Bash(docker rmi:*)
  - Bash(docker images:*)
  - Bash(docker buildx:*)
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git push:*)
  - Bash(git fetch:*)
  - Bash(git checkout:*)
  - Bash(git pull:*)
  - Bash(git branch:*)
  - Bash(gh pr:*)
  - Bash(gh run:*)
  - Bash(gh issue:*)
  - Bash(gh api:*)
  - Bash(grep:*)
  - Bash(test:*)
  - Read
  - Edit
  - Write
  - AskUserQuestion
---

# Docker Workflow Skill

Handle Q-agent's Docker image: build, smoke-test, push, verify. The image
bundles **LEAN CLI + infrastructure pipelines + marimo** in a single
`linux/amd64` image, published to `ghcr.io/wolfpackofone/q-agent` on every
push to `main` by `.github/workflows/docker.yml`.

## When to invoke

- "bump LEAN to X.Y.Z" / "bump lean version"
- "rebuild the docker image"
- "smoke-test the image locally"
- "verify the GHCR pull works"
- "the docker CI failed"
- "is the docker image up to date?"

## Canonical files

| Path | Purpose |
|---|---|
| `Dockerfile` | Multi-stage build, `LEAN_VERSION` build arg, single `/opt/venv`, non-root `qagent` user |
| `.dockerignore` | Mirrors `.gitignore`; re-includes `MyProjects/ElectionIndustryBeta/` as the shipped demo |
| `.github/workflows/docker.yml` | Build on PR, push `:latest` + `:sha-X` on `main`, push `:vX.Y.Z` on tag |
| `docs/docker.md` | User-facing docs (quickstart, mounted dev, credentials, bumping LEAN) |

## Task 1: Bump LEAN_VERSION

```bash
# Confirm current pin
grep '^ARG LEAN_VERSION=' Dockerfile

# Edit Dockerfile, change the default in the top-level ARG.
# Or build with --build-arg without editing.

# Build with the new version
docker build --build-arg LEAN_VERSION=<X.Y.Z> -t q-agent:dev .

# Run the full smoke suite (see Task 2)
```

After verifying locally, commit the Dockerfile change on a feature branch
and open a PR; `main` is branch-protected.

## Task 2: Build + smoke-test locally

```bash
docker build -t q-agent:dev .
```

Then run every assertion (these mirror `.github/workflows/docker.yml`'s
smoke-test stage):

```bash
docker run --rm q-agent:dev lean --help | head -5
docker run --rm q-agent:dev python -c \
  "import ccxt, pandas, numpy, yfinance, tenacity, tqdm, dotenv, requests; print('OK')"
docker run --rm q-agent:dev python -c "import marimo; print(marimo.__version__)"
docker run --rm q-agent:dev pytest -m "not integration" \
  --ignore=tests/hygiene -p no:cacheprovider -q
docker run --rm q-agent:dev test -d /workspace/MyProjects/ElectionIndustryBeta
docker run --rm -v "$(pwd):/workspace" q-agent:dev bash -lc 'ls MyProjects | head -5'
docker history q-agent:dev | grep -iE 'lean\.json|\.env|credentials|\.key' \
  && echo "FAIL: secrets in layers" || echo "OK: no secrets in history"
docker images q-agent:dev --format '{{.Size}}'
```

All must pass before pushing. Expected image size: ~1 GB.

## Task 3: Verify the published GHCR image (post-merge)

After a PR merges to `main`, the workflow pushes a new `:latest` + `:sha-X`.
Verify the image is pullable as an anonymous user:

```bash
# Watch the post-merge build first
gh run list --repo WolfpackOfOne/Q-agent --branch main --workflow docker --limit 1

# Once it's success, pull and run anonymously
docker logout ghcr.io
docker rmi ghcr.io/wolfpackofone/q-agent:latest 2>/dev/null || true
docker pull ghcr.io/wolfpackofone/q-agent:latest
docker run --rm ghcr.io/wolfpackofone/q-agent:latest lean --help
```

If `docker pull` errors with `denied`, the package visibility hasn't been
flipped to public — see Task 4.

If the pull errors with `no matching manifest for linux/arm64/v8`, the host
is Apple Silicon and the image is amd64-only (see issue #26). Force the
platform:

```bash
docker pull --platform linux/amd64 ghcr.io/wolfpackofone/q-agent:latest
```

## Task 4: First-time GHCR visibility flip (manual, post-first-publish)

The package defaults to **private** when first published. The org admin
must flip it once:

1. Open <https://github.com/orgs/WolfpackOfOne/packages/container/q-agent/settings>
2. Scroll to **Danger Zone**
3. **Change visibility → Public** → confirm with the package name

This skill cannot do this step — it requires UI interaction.

## Task 5: Debug a failed `docker` CI run

```bash
# Find the latest failed run on the current branch
gh run list --repo WolfpackOfOne/Q-agent --branch "$(git branch --show-current)" \
  --workflow docker --limit 3

# View the failing step's log
gh run view --repo WolfpackOfOne/Q-agent <RUN_ID> --log-failed | tail -60
```

Cross-reference the failure mode against **Known gotchas** below before
rewriting code.

## Known gotchas (do not relearn these)

### 1. `lean` import fails as non-root with `FileNotFoundError: modules-1.14.json`

`lean.models/__init__.py` tries to download `modules-1.14.json` into its
package directory on first import. As `qagent` (non-root, uid 1000), the
write fails. The `Dockerfile` pre-caches the file at build time (as root):

```dockerfile
RUN python -c "import lean.models" \
    || python -c "import json, pathlib, lean; \
p = pathlib.Path(lean.__file__).parent / 'modules-1.14.json'; \
p.write_text(json.dumps({'modules': []}))"
```

If a new lean release changes the cache filename (e.g. `modules-1.15.json`),
the pre-cache might miss it. Symptom: `lean --help` raises `PermissionError`
or `FileNotFoundError` in the container.

### 2. Personal-paths CI scan flags `/home/qagent/`

`.github/workflows/secret-scan.yml` greps for `/home/<user>/` paths. The
`qagent` container user is a legitimate documented path, so `docs/docker.md`
is whitelisted via `:!docs/docker.md` in the `git grep` exclusion list.

**Never include `/home/qagent/` in any other tracked file** — including
comments inside the workflow YAML itself (a previous fix self-flagged this
way). If a new file needs to reference the path, either:

- Add it to the exclusion list (`:!<path>`), OR
- Phrase the path indirectly ("the qagent home directory")

### 3. Linkcheck 404s on `github.com/.../blob/main/<new-file>`

`docs/lychee` runs on every PR. A doc that links to a brand-new file via
`https://github.com/WolfpackOfOne/Q-agent/blob/main/<path>` will 404 until
the PR merges. Use a plain code span (`` `path/to/file` ``) for new files
introduced in the same PR.

### 4. `.dockerignore` re-include must keep `MyProjects/ElectionIndustryBeta/`

The image ships **one** demo project. The pattern is:

```
MyProjects/*/
!MyProjects/ElectionIndustryBeta/
```

Verify after any `.dockerignore` change:

```bash
docker build -t q-agent:dev . \
  && docker run --rm q-agent:dev test -d /workspace/MyProjects/ElectionIndustryBeta
```

### 5. `pytest -m "not integration"` plus hygiene tests

Inside the container, `tests/hygiene/` cannot run (they shell out to `git`
against the working tree; `.git/` is excluded). Always pass
`--ignore=tests/hygiene -p no:cacheprovider` in the in-image smoke test.
On a fresh checkout (the `tests.yml` workflow), `tests/hygiene/` runs
normally — no change needed there.

### 6. Image is `linux/amd64` only

Apple Silicon hosts must pull with `--platform linux/amd64` (Rosetta
emulation). Multi-arch tracked in issue #26.

## Open follow-ups

- #26 — multi-arch (add `linux/arm64`)
- #27 — support `lean backtest` (local) inside the container

## Reference

- PR that introduced the workflow: [#25](https://github.com/WolfpackOfOne/Q-agent/pull/25)
- Originating issue: [#20](https://github.com/WolfpackOfOne/Q-agent/issues/20) (closed)
- User docs: `docs/docker.md`
