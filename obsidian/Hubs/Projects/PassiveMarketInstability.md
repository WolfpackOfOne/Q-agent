---
hub: "PassiveMarketInstability"
tags:
  - "hub"
  - "projects/PassiveMarketInstability"
---
# PassiveMarketInstability

`MyProjects/PassiveMarketInstability/` · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability)

> [!abstract] Summary
> This is a notebook-first research package for extending "A Model for Passive That Breaks the Market" by Michael Green, Hari P. Krishnan, and Stephan Sturm. It is not a production QuantConnect strategy and it does not place trades.
>
> The paper models market value `S(t)` as mean reverting toward a smooth fundamental value `F(t)`, with mean reversion weakening as passive share `p(t)` rises:
>
> — from `MyProjects/PassiveMarketInstability/README.md`

## Files

**`MyProjects/PassiveMarketInstability/src/passive_market_instability/`**

- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/__init__.py|__init__.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/config.py|config.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/flows.py|flows.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/liquidity.py|liquidity.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/passive_share.py|passive_share.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/plots.py|plots.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/pressure.py|pressure.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/simulation.py|simulation.py]]
- [[Code/MyProjects/PassiveMarketInstability/src/passive_market_instability/validation.py|validation.py]]

**`MyProjects/PassiveMarketInstability/tests/`**

- [[Code/MyProjects/PassiveMarketInstability/tests/test_flows.py|test_flows.py]]
- [[Code/MyProjects/PassiveMarketInstability/tests/test_passive_share.py|test_passive_share.py]]
- [[Code/MyProjects/PassiveMarketInstability/tests/test_pressure.py|test_pressure.py]]
- [[Code/MyProjects/PassiveMarketInstability/tests/test_simulation.py|test_simulation.py]]

## Other tracked files (on GitHub)

- [MyProjects/PassiveMarketInstability/README.md](https://github.com/WolfpackOfOne/Q-agent/blob/main/MyProjects/PassiveMarketInstability/README.md)
