# Getting Started

This guide explains how to set up the Q-agent workspace locally.

> **Fast path:** the [Docker image](docker.md) bundles LEAN CLI, the
> infrastructure pipelines, and marimo into one container. If you don't need
> local `lean backtest` (host-only — see Docker page) and prefer not to
> manage host venvs, run:
>
> ```bash
> docker run --rm -it -v "$(pwd):/workspace" ghcr.io/wolfpackofone/q-agent:latest
> ```
>
> The host setup below is required only if you want to run `lean backtest`
> locally or develop without containers.

## Prerequisites

Install the following:

- Python 3.8+
- Git
- Docker Desktop
- QuantConnect account

## Clone the Repository

```bash
git clone https://github.com/WolfpackOfOne/Q-agent.git
cd Q-agent
```

## Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Install LEAN CLI

```bash
pip install --upgrade pip
pip install lean
```

## Configure QuantConnect

```bash
cd MyProjects
lean init
lean login
```

## Verify Installation

```bash
lean --version
```

![LEAN cloud backtest workflow](recordings/lean-backtest.gif)

## Recommended Workflow

- Keep strategy logic modular
- Use notebooks for research and diagnostics
- Keep reusable code in domain modules
- Avoid committing local data
- Use feature branches for experimental work
