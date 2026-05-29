# Docker

Q-agent ships a single workspace image bundling the LEAN CLI, the
infrastructure pipelines (crypto / Polymarket / EDGAR / WRDS / yfinance), and
marimo. The image is built and published to GitHub Container Registry by
`.github/workflows/docker.yml` on every push to `main`.

## Quickstart

```bash
docker pull ghcr.io/wolfpackofone/q-agent:latest

# Drop into an interactive shell with lean, marimo, python, and pytest ready.
docker run --rm -it ghcr.io/wolfpackofone/q-agent:latest

# Or run a specific tool one-off.
docker run --rm -it ghcr.io/wolfpackofone/q-agent:latest lean --help
docker run --rm -it ghcr.io/wolfpackofone/q-agent:latest marimo --help
```

The image is published as a multi-arch manifest for `linux/amd64` and
`linux/arm64`, so `docker pull` works natively on both x86 servers and Apple
Silicon Macs (no `--platform` flag needed). The `latest` tag tracks `main`;
short-SHA tags (`sha-abc1234`) and version tags (`v1.2.3`) are also published.

## What's inside

- Base: `python:3.12-slim`
- LEAN CLI pinned via build arg (`LEAN_VERSION`, defaults to the version that
  was current at the time the image was built — see image labels)
- A single venv at `/opt/venv` with: `lean`, infrastructure dependencies
  (`ccxt`, `pandas`, `numpy`, `yfinance`, `tenacity`, `tqdm`, `python-dotenv`,
  `requests`), marimo + its plotting stack (`matplotlib`, `plotly`, `seaborn`,
  `scipy`, `nbformat`), and dev tools (`pytest`, `pytest-cov`, `pytest-mock`)
- The repository copied into `/workspace` (everything in `.dockerignore` is
  excluded — no credentials, no per-user data, no `.git/`)
- The `MyProjects/ElectionIndustryBeta/` demo project as a worked example
- Runs as non-root user `qagent` (uid 1000)

## Mounted dev workflow

Mount your local checkout to keep edits in sync with the host:

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  ghcr.io/wolfpackofone/q-agent:latest
```

The bind mount overrides the baked-in `/workspace`, so you work against your
live files. This is the recommended workflow for contributors who want a
reproducible Python environment without managing three host venvs.

## Running a pipeline

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  ghcr.io/wolfpackofone/q-agent:latest \
  python infrastructure/pipelines/crypto/scripts/run_pipeline.py --help
```

Pipeline outputs land under `infrastructure/pipelines/<name>/lean-data/` —
because of the bind mount, they appear on the host too.

## Running marimo

```bash
docker run --rm -it \
  -p 2718:2718 \
  -v "$(pwd):/workspace" \
  ghcr.io/wolfpackofone/q-agent:latest \
  marimo edit --host 0.0.0.0 --port 2718 --no-token \
  infrastructure/marimo/notebooks/election_industry_returns.py
```

Then open <http://localhost:2718> on the host. `--host 0.0.0.0` is required so
the container's port is reachable from outside; `--no-token` skips the auth
prompt (only safe on a local-only port).

## LEAN: cloud backtest in the container, local backtest on the host

The image supports the **cloud** LEAN workflow out of the box:

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -v "$HOME/.lean:/home/qagent/.lean:ro" \
  ghcr.io/wolfpackofone/q-agent:latest \
  bash -c "cd MyProjects && lean cloud push --project ElectionIndustryBeta --force && lean cloud backtest ElectionIndustryBeta"
```

### Why local `lean backtest` is not run *inside* the container

`lean backtest` (local) does not run the engine in-process — it asks a Docker
daemon to spawn a separate `quantconnect/lean` container. From inside our
image there is no daemon to talk to, so you would have to either:

- **Bind-mount the host Docker socket** (`-v /var/run/docker.sock:...`) — a
  privilege escalation (the container can launch arbitrary host containers),
  *and* the spawned engine container's volume mounts are resolved by the
  **host** daemon against the **host** filesystem, not our container's
  `/workspace`. So the mounts only line up if your project sits at an
  identical path on the host, and the non-root `qagent` user also needs the
  host's `docker` group GID to read the socket. Fragile.
- **Docker-in-Docker** — run a second daemon inside the container. Heavier
  image, more moving parts.

Neither is enabled by default, so `:latest` stays minimal-privilege. Tracking
issue: [#27](https://github.com/WolfpackOfOne/Q-agent/issues/27) (deferred
until there is real demand).

### Recommended: run local backtests on the host

The host already has Docker set up (that is what runs this image), so run
local backtests there with the host's LEAN CLI — no socket gymnastics:

```bash
# On the host, with the lean CLI installed (pip install lean)
cd MyProjects/ElectionIndustryBeta
lean backtest "ElectionIndustryBeta"
```

`lean backtest` will pull and run the `quantconnect/lean` engine container via
the host daemon directly, and the volume paths resolve correctly because they
are already host paths. Use the container for `lean cloud backtest`, pipelines,
notebooks, and tests; use the host for local `lean backtest`.

## Credentials

The image is deliberately built **without** any credentials. Provide them at
runtime via read-only mounts or `--env-file`:

| Credential | Mount / env strategy |
|---|---|
| QuantConnect (`lean.json`) | `-v "$HOME/.lean:/home/qagent/.lean:ro"` (lean reads `~/.lean/credentials`) |
| Pipeline env (`infrastructure/.env`) | `--env-file infrastructure/.env` |
| Exchange API keys (CCXT) | `--env-file <your-secrets>.env` — never bake into the image |

Never `docker commit` a running container that has credentials mounted —
that's how secrets leak into a published image. If you need a credentialed
image for a closed environment, build it in that environment, don't push it
to a public registry.

## Building locally

```bash
docker build -t q-agent:dev .

# Bump LEAN to a different version:
docker build -t q-agent:dev --build-arg LEAN_VERSION=1.0.226 .
```

Local smoke tests (mirrors CI):

```bash
docker run --rm q-agent:dev lean --help
docker run --rm q-agent:dev pytest -m "not integration" --ignore=tests/hygiene -p no:cacheprovider -q
docker run --rm q-agent:dev python -c "import marimo, ccxt, pandas, numpy, yfinance"
docker run --rm q-agent:dev test -d /workspace/MyProjects/ElectionIndustryBeta
```

Hygiene tests (`tests/hygiene/`) are skipped inside the container because
they shell out to `git` against the working tree, and the image deliberately
excludes `.git/`. They still run in `.github/workflows/tests.yml` where a
fresh checkout is available.

## Image size

Around 1 GB compressed; ~3 GB on disk after pull. This is dominated by
SciPy, plotly, and the LEAN CLI's transitive deps. Slimming to per-tool tags
(`q-agent-lean`, `q-agent-marimo`) is a possible follow-up if size becomes a
pain point — open an issue on
[GitHub](https://github.com/WolfpackOfOne/Q-agent/issues).
