---
title: "101 Formulaic Alphas"
source: "arXiv (q-fin.PM)"
url: "https://arxiv.org/abs/1601.00991"
pdf_url: "https://arxiv.org/pdf/1601.00991"
local_pdf: "101-formulaic-alphas-kakushadze-2016.pdf"
author: "Zura Kakushadze"
date_fetched: "2026-09-03"
date_published: "2016-01-05"
journal_ref: "Wilmott Magazine, Vol. 84 (2016), pp. 72-80"
arxiv_id: "1601.00991"
tags: [alpha-factors, formulaic-alphas, quantitative-trading, cross-sectional, time-series-operators, signal-construction, equities]
---

# 101 Formulaic Alphas

> Source: [arXiv:1601.00991](https://arxiv.org/abs/1601.00991) (also [PDF](https://arxiv.org/pdf/1601.00991))
> Author: Zura Kakushadze
> Published: 2016-01-05 (v1); final v3: 2016-03-18. Also published in Wilmott Magazine, Vol. 84 (2016), pp. 72-80.
> Fetched: 2026-09-03

## About this entry

The full paper text (with all 101 alpha formulas, Alpha#1 through Alpha#101, and the
operator glossary) is preserved as-is in the bundled PDF in this same directory:

- `101-formulaic-alphas-kakushadze-2016.pdf` (22 pages, fetched directly from
  `https://arxiv.org/pdf/1601.00991`)

This markdown file is a metadata/summary wrapper for indexing and keyword search —
per the workspace convention of treating PDFs as opaque. **Do not treat this file as
a substitute for the PDF when implementing specific alpha formulas** — read the PDF
directly for exact expressions, since formula fidelity matters for implementation.

## Abstract

We present explicit formulas — that are also computer code — for 101 real-life
quantitative trading alphas. Their average holding period approximately ranges
between 0.6 and 6.4 days. The average pair-wise correlation of these alphas is
low, 15.9%. The returns are strongly correlated with volatility, but have no
significant dependence on turnover. We further discuss a method of increasing
the number of alphas, aimed at diversifying a trading portfolio, and thus
improving trading performance.

## Why this paper is here

Reference source for a new algorithmic trading project in this workspace that
will implement a subset of the 101 formulaic alphas as trading signals on
equities. The paper defines cross-sectional and time-series operators used
throughout the formulas: `rank`, `delay`, `correlation`, `covariance`, `scale`,
`ts_min`, `ts_max`, `ts_rank`, `ts_argmin`, `ts_argmax`, `decay_linear`,
`signedpower`, `indneutralize`, and others, built from price/volume/VWAP data.

## Notes for QC implementation (to be expanded)

- Formulas assume daily OHLCV + VWAP data across a cross-sectional universe.
- Several operators require a full-universe cross-section at each timestep
  (e.g. `rank`, `indneutralize`) — plan for a coarse/fine universe selection
  model or a precomputed universe snapshot in LEAN rather than per-symbol
  event-driven logic.
- `indneutralize` requires sector/industry classification data — check
  available LEAN fundamentals/classification datasets before assuming this is
  directly implementable for the full universe.
- No QC-specific implementation notes have been written yet; add them to
  `References/notes/` once implementation begins, and cross-link back here.
