# Passive Market Instability Extension

This notebook studies the passive-market-instability model from Michael Green, Hari P. Krishnan, and Stephan Sturm by comparing passive-share paths, simulating the market-level SDE, and adding flow and cross-sectional diagnostics.
It extends the paper by asking whether the instability story changes when the passive-share curve source, ETF flow-pressure proxy, and stock-level liquidity exposure are varied together.
Haddad, Huebner, and Loualiche 2025 is used as the baseline passive-share curve with the paper's approximate logistic growth parameter of alpha = 0.106.
Brightman and Harvey 2025 is used as an alternative passive-share curve sensitivity with alpha = 0.100.
The David Dredge / Yahoo Finance active-passive chart is treated only as a visual benchmark unless manually digitized and clearly labeled.
ETF volume times return is introduced as a weak flow-pressure proxy to make positive and negative broad-market ETF pressure more intuitive, not as official creations or redemptions.
The cross-sectional extension asks whether high index-weight, low-liquidity stocks look more exposed to passive pressure than other names in a small demo universe.
