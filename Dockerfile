# syntax=docker/dockerfile:1.7
#
# Q-agent — workspace runtime image.
# Bundles LEAN CLI, infrastructure pipelines, and marimo into one image.
# Local `lean backtest` (which spawns its own Docker container) is intentionally
# unsupported here — use `lean cloud backtest` inside the container, or run
# `lean backtest` on the host. See docs/docker.md.

ARG PYTHON_VERSION=3.12
ARG LEAN_VERSION=1.0.225

# ---------- builder stage: install everything into /opt/venv ----------
FROM python:${PYTHON_VERSION}-slim AS builder

ARG LEAN_VERSION

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Build tools needed by some scientific-stack wheels (scipy, numpy, ccxt, etc.)
# Kept in the builder stage only — runtime image stays slim.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        gfortran \
        libffi-dev \
        libssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

# Install LEAN CLI first (pinned via build arg).
RUN pip install "lean==${LEAN_VERSION}"

# Pre-cache lean's modules-1.14.json so the runtime (non-root user) doesn't try
# to write into site-packages on first import. Falls back to an empty modules
# stub if the build environment can't reach cdn.quantconnect.com.
RUN python -c "import lean.models" \
    || python -c "import json, pathlib, lean; \
p = pathlib.Path(lean.__file__).parent / 'modules-1.14.json'; \
p.write_text(json.dumps({'modules': []}))"

# Copy only requirements files first to maximise layer caching.
COPY requirements-dev.txt constraints-course.txt /tmp/q-agent/
COPY infrastructure/requirements.txt /tmp/q-agent/infrastructure/requirements.txt
COPY infrastructure/marimo/requirements.txt /tmp/q-agent/infrastructure/marimo/requirements.txt

RUN pip install \
        -r /tmp/q-agent/requirements-dev.txt \
        -r /tmp/q-agent/infrastructure/requirements.txt \
        -r /tmp/q-agent/infrastructure/marimo/requirements.txt

# ---------- runtime stage: slim image with venv + repo ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG LEAN_VERSION
LABEL org.opencontainers.image.source="https://github.com/WolfpackOfOne/Q-agent" \
      org.opencontainers.image.description="Q-agent workspace: LEAN CLI + infrastructure pipelines + marimo." \
      org.opencontainers.image.licenses="MIT" \
      org.q-agent.lean-version="${LEAN_VERSION}"

# Runtime needs: git (used by some pipelines / lean cloud workflows), curl
# (debug + health checks), CA certs (for HTTPS to QC / data sources).
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 qagent \
    && useradd --uid 1000 --gid qagent --create-home --shell /bin/bash qagent

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /workspace
COPY --chown=qagent:qagent . /workspace

USER qagent

# No ENTRYPOINT — users invoke `lean`, `marimo`, `pytest`, `python`, or pipeline
# scripts as the first argument. Default `bash` gives an interactive shell.
CMD ["bash"]
