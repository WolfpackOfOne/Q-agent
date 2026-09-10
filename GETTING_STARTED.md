# Getting Started

This is the shortest supported path for a new Q-agent student.

## 1. Install prerequisites

- Git
- Python 3.11 or 3.12
- Docker Desktop if you will use the course image or run local LEAN backtests
- A QuantConnect account only for strategy and cloud-backtest work

## 2. Fork and clone

If you will contribute changes, fork `WolfpackOfOne/Q-agent` on GitHub, then:

```bash
git clone https://github.com/YOUR-USERNAME/Q-agent.git
cd Q-agent
git remote add upstream https://github.com/WolfpackOfOne/Q-agent.git
git fetch upstream
```

If you only want to run the examples, clone the upstream repository directly:

```bash
git clone https://github.com/WolfpackOfOne/Q-agent.git
cd Q-agent
```

All remaining commands assume the current directory is the repository root.

## 3. Choose an environment

### Course Docker image

Use the tagged course baseline for the most consistent setup:

```bash
docker pull ghcr.io/wolfpackofone/q-agent:v0.1.0
docker run --rm -it -v "$(pwd):/workspace" \
  ghcr.io/wolfpackofone/q-agent:v0.1.0
```

The image supports Intel/AMD and Apple Silicon. No `--platform` flag is needed.

### Host Python environment

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

On Windows PowerShell, activate with:

```powershell
venv\Scripts\Activate.ps1
```

`requirements-dev.txt` automatically applies the direct dependency versions in
`constraints-course.txt`. Install LEAN into this environment when you need
QuantConnect tooling:

```bash
python -m pip install lean==1.0.225
lean login
```

## 4. Run the research example

The notebook uses a committed Polymarket fixture and fetches public ETF prices
from yfinance:

```bash
python -m venv infrastructure/marimo/venv
source infrastructure/marimo/venv/bin/activate
python -m pip install -r infrastructure/marimo/requirements.txt
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

Open <http://localhost:2719>. On Windows, activate the notebook environment with
`infrastructure\marimo\venv\Scripts\Activate.ps1`.

## 5. Create a strategy repository

Do not copy `MyProjects/_template` directly; it contains rendering tokens. From
the Q-agent root, run:

```bash
python scripts/create_strategy.py MyFirstStrategy
cd MyProjects/MyFirstStrategy
git init
```

The generated directory is intentionally ignored by the Q-agent repository so
that each student can create an independent GitHub portfolio repository. Add it
to the central Q-agent repository only after the instructor approves it as a
shared example.

For a QuantConnect cloud backtest:

```bash
lean cloud push --project "MyFirstStrategy" --force
lean cloud backtest "MyFirstStrategy" --name "baseline"
```

## 6. Validate a Q-agent contribution

From the Q-agent repository root:

```bash
pytest -m "not integration"
python scripts/check_repository_policy.py --all
```

Then follow the complete fork and PR workflow in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Credentials and help

- [Credential setup](CREDENTIALS.md)
- [Docker and LEAN details](docs/docker.md)
- [Student support](SUPPORT.md)
- [Private security reporting](SECURITY.md)
