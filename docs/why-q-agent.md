# Why Q-agent Exists

## The problem with quantitative research tooling

Professional quantitative research is fragmented by design. Data comes from one vendor. It gets cleaned in Python scripts that live on someone's laptop. Analysis happens in notebooks that are never committed. Backtesting runs in a separate environment. Results live in email threads.

For practitioners, this fragmentation is an accepted cost of doing business. For students, it is a barrier that prevents them from ever seeing what the full workflow looks like.

Most academic quant courses teach theory well. The gap between "I understand a momentum factor" and "I ran a reproducible backtest of a momentum strategy on real data, validated it, and documented the result" is enormous — and almost no one teaches that gap explicitly.

Q-agent is an attempt to close it.

---

## Why pipelines, notebooks, strategies, and agents belong together

These are not separate concerns. They are a single workflow:

```
Raw data → Pipeline → Local store → Notebook research → Strategy → Backtest → Results → Notebook diagnostics
```

Every time they live in separate repos, separate environments, or separate documentation systems, something breaks. The pipeline output format doesn't match what the notebook expects. The strategy uses a different data source than the research notebook. The backtest results are never connected back to the hypothesis.

Q-agent treats the full workflow as a single coherent system. One repo. One set of conventions. One place to look.

---

## Why LEAN

QuantConnect's LEAN engine is the most mature open-source backtesting framework available. It handles the things that matter:

- **Survivorship bias**: uses point-in-time data, not backadjusted
- **Realistic fills**: configurable slippage and transaction cost models
- **Portfolio construction**: handles position sizing, cash management, and rebalancing correctly
- **Data quality**: cloud data is institutional grade

Most academic backtesting code does not handle these correctly. A strategy that looks good in a naive backtest often looks much worse in LEAN — and that difference is the signal. Building on LEAN means results are trustworthy enough to act on.

---

## Why reproducibility matters

A backtest you cannot reproduce is not a result. It is a claim.

Reproducibility in this context means:

- The exact data used in the analysis can be regenerated from the pipeline
- The notebook can be re-run and produce the same output
- The strategy code is version-controlled and the backtest is logged
- Another researcher (or you, six months later) can pick up where you left off

Q-agent enforces reproducibility by convention rather than by enforcement. Pipelines are version-controlled (data is gitignored but scripts are not). Notebooks read from declared sources. Workflows are documented.

---

## Why local matters

Cloud-dependent workflows have hidden costs:

- They fail when the API is down, rate-limited, or restricted
- They require credentials that can't be shared in a classroom
- They accumulate costs that are invisible until they aren't
- They don't work on a plane, in a classroom with poor wifi, or in regions with restricted access

Local pipelines — which pull data once and store it in LEAN-compatible format — eliminate most of these problems. Cloud (QuantConnect) is used for final validation and production backtesting, not daily iteration. Local is used for everything else.

---

## Why AI agents belong in the workflow

AI coding assistants change what is possible for a solo researcher or a small team. A single developer with Claude Code can:

- Maintain a large, well-structured codebase
- Catch API gotchas before they cause hard-to-debug errors
- Generate boilerplate that follows project conventions
- Document decisions in durable memory across sessions

But AI agents are also dangerous in a research context. An agent that doesn't know the LEAN API will introduce subtle bugs that only surface in live trading. An agent with no memory of past decisions will repeat the same mistakes.

Q-agent treats agent integration as a first-class concern. The `AGENTS.md` file documents architectural guardrails. The `claude.md` file documents LEAN-specific gotchas. The `.claude/memory/` system persists learned lessons across sessions. The result is an AI-assisted workflow that is safe enough to trust.

---

## Why education

Professional quantitative research codebases are not publicly available. The firms that build them have no reason to share them. Students learning systematic trading have no reference for what a real research infrastructure looks like — they learn theory without ever seeing how the pieces fit together in practice.

Q-agent is designed to be read, not just used. The architecture is explained. The conventions are documented. The code is written to be understood, not just to run. Every design decision that might surprise a reader has a documented reason.

---

## What Q-agent is not

Q-agent is not:

- A trading bot or automated execution system
- Investment advice or a signal service
- A black-box backtest runner
- A replacement for QuantConnect's cloud infrastructure
- A general-purpose AI agent framework

It is a workspace — an opinionated set of conventions, pipelines, and tools for doing quantitative research reproducibly, with AI assistance, in a way that can be taught and shared.

---

## The positioning

The closest adjacent projects are Qlib, Backtrader, various QuantConnect community repos, and generic AI coding agent frameworks. Q-agent differs from all of them in one important way: it explicitly integrates the educational and agentic concerns into the research infrastructure itself.

The goal is not to be the fastest backtester or the most powerful agent framework. The goal is to be the workspace that a student, researcher, or practitioner reaches for when they want to do serious quantitative work and have it be reproducible, teachable, and AI-assisted by default.
