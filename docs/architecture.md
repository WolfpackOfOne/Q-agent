# Architecture

Projects in this workspace follow an atomic architecture that keeps composition thin, orchestration isolated, and business logic testable.

## Strategy layer diagram

```mermaid
graph TD
    A["main.py<br/><small>Composition Root</small>"]
    B["models/<br/><small>Orchestration</small>"]
    C["domain/<br/><small>Business Logic</small>"]
    D["Pure Python<br/><small>DTOs · Signals · Metrics · Validation</small>"]

    A --> B
    B --> C
    C --> D

    style A fill:#3949ab,color:#fff,stroke:none
    style B fill:#5c6bc0,color:#fff,stroke:none
    style C fill:#7986cb,color:#fff,stroke:none
    style D fill:#9fa8da,color:#fff,stroke:none
```

## Full workspace flow

```mermaid
graph TD
    subgraph Pipelines["Data Pipelines"]
        P1[Crypto]
        P2[Polymarket]
        P3[WRDS / CRSP]
        P4[SEC EDGAR]
        P5[yfinance]
    end

    subgraph Local["Local Store"]
        D1["infrastructure/pipelines/\n*/data/"]
    end

    subgraph Research["Research"]
        N1[Marimo Notebooks]
    end

    subgraph Strategy["Strategy"]
        S1[LEAN Algorithm]
        S2[QuantConnect Cloud]
        OS[ObjectStore Results]
    end

    subgraph Agent["Agent Layer"]
        A1[Claude Code]
    end

    Pipelines --> Local
    Local --> N1
    Local --> S1
    S1 --> S2
    S2 --> OS
    OS --> N1
    A1 --> S1
    A1 --> Pipelines
```

## Pipeline flow

```mermaid
graph LR
    SRC["Data Source<br/>API / File"]
    PIPE["run_pipeline.py"]
    FMT["LEAN CSV Format"]
    DATA["data/"]
    NB["Research Notebook"]
    BT["LEAN Backtest"]

    SRC --> PIPE
    PIPE --> FMT
    FMT --> DATA
    DATA --> NB
    DATA --> BT
```

---

## Layers

### Composition Root — `main.py`

Wires the project together. Responsibilities:

- Scheduling
- Event routing
- Dependency construction
- Top-level orchestration

The composition root should be thin. If logic is drifting into `main.py`, it belongs in `models/`.

### Models Layer — `models/`

Orchestration and domain coordination. Responsibilities:

- Strategy coordination
- Signal orchestration
- Portfolio orchestration
- Risk orchestration

Models depend on domain. They do not depend on each other.

### Domain Layer — `domain/`

Reusable business logic. Responsibilities:

- Calculations
- Validation
- DTOs
- Metrics
- Pure functions

Domain modules have no LEAN imports. They are testable with plain `pytest` without instantiating an algorithm.

---

## Shared signals library

`MyProjects/shared/signals/` is the canonical source for reusable signal atoms. Projects consume them via symlinks — `lean cloud push` follows symlinks so QuantConnect cloud sees a normal file.

```
shared/signals/
├── momentum.py         ← pure Python
├── mean_reversion.py
└── volatility.py

MyFirstStrategy/
└── domain/
    └── signals/
        ├── momentum.py → ../../shared/signals/momentum.py
        └── mean_reversion.py → ../../shared/signals/mean_reversion.py
```

---

## Goals

- **Testability**: domain logic runs without LEAN
- **Reduced coupling**: layers depend only downward
- **Reusable research**: signals live in `shared/`, not inside projects
- **Readability for students**: each layer has a single clear responsibility
- **Safe AI-assisted development**: the structure gives agents a predictable target

---

## Runtime artifact: the workspace Docker image

The workspace publishes a single runtime image to GitHub Container Registry
on every push to `main`:

```
ghcr.io/wolfpackofone/q-agent:latest   # tracks main
ghcr.io/wolfpackofone/q-agent:sha-<x>  # per-commit
ghcr.io/wolfpackofone/q-agent:vX.Y.Z   # version tags
```

The image bundles three things that today require three separate host venvs:

- **LEAN CLI** (`lean`), pinned via the `LEAN_VERSION` build arg
- **Infrastructure pipelines** (crypto / Polymarket / EDGAR / WRDS / yfinance)
- **marimo** with its plotting stack

Build pipeline:

```mermaid
graph LR
    SRC["Dockerfile<br/>.dockerignore"]
    CI[".github/workflows/docker.yml"]
    BLD["Buildx build (linux/amd64)"]
    SMK["Smoke tests<br/>(in built image)"]
    GHCR["ghcr.io/wolfpackofone/q-agent"]

    SRC --> CI
    CI --> BLD
    BLD --> SMK
    SMK --> GHCR
```

`.dockerignore` mirrors `.gitignore` and additionally excludes the LEAN engine
checkout, `References/`, the rendered mkdocs site, all per-user data
directories, and every `MyProjects/*/` subtree except the
`ElectionIndustryBeta/` reference example. The image runs as non-root
`qagent` (uid 1000) and contains no credentials — `lean.json`, `.env`, and
`config.json` files are mounted in at runtime, never baked.

The image deliberately does **not** support `lean backtest` (local). That
command spawns a nested `quantconnect/lean` Docker container, which would
require either the Docker socket (privilege escalation) or Docker-in-Docker.
`lean cloud backtest` works inside the container; `lean backtest` runs on
the host. Tracked as issue #27.

For build commands, smoke-test recipe, GHCR pull verification, and the six
known gotchas, see [Docker](docker.md) and the `/docker-workflow` skill at
`.claude/skills/docker-workflow/SKILL.md`.
