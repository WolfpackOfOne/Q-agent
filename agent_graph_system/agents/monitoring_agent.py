"""Monitoring agent: watches datasets and pipelines for staleness."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from agent_graph_system.agents.base_agent import BaseAgent
from agent_graph_system.graph.neo4j import graph_models as gm
from agent_graph_system.graph.backend import query

log = logging.getLogger(__name__)

STALENESS_HOURS: dict[str, int] = {
    "WRDS": 24,
    "Bloomberg": 24,
    "Crypto": 1,
    "Polymarket": 4,
    "EDGAR": 168,  # 1 week
    "YFinance": 24,
}

# A strategy with a completed backtest but no completed walk-forward run (or one
# older than this) is flagged ``needs_walkforward`` for the research/walkforward
# pipeline to pick up.
WALKFORWARD_STALENESS_DAYS: int = 30


def _is_stale(created_at: str | None, cutoff: datetime) -> bool:
    """True if ``created_at`` is missing/unparseable or older than ``cutoff``."""
    if not created_at:
        return True
    try:
        ts = datetime.fromisoformat(created_at)
    except ValueError:
        return True
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)
    return ts < cutoff


class MonitoringAgent(BaseAgent):
    name = "MonitoringAgent"
    role = "monitoring"

    def run(self, **kwargs) -> Any:
        log.info("[MonitoringAgent] checking dataset freshness")
        results = {"stale_marked": [], "errors": [], "needs_walkforward": []}
        try:
            datasets = query("MATCH (d:Dataset) RETURN d.name AS name, d.source AS source, d.last_updated AS last_updated")
            for ds in datasets:
                source = ds.get("source", "")
                sla_hours = STALENESS_HOURS.get(source, 48)
                last_updated_str = ds.get("last_updated")
                if not last_updated_str:
                    continue
                try:
                    last_updated = datetime.fromisoformat(last_updated_str)
                    if datetime.utcnow() - last_updated > timedelta(hours=sla_hours):
                        gm.upsert_dataset(ds["name"], source=source, status="stale")
                        results["stale_marked"].append(ds["name"])
                        log.warning("[MonitoringAgent] marked stale: %s", ds["name"])
                except ValueError:
                    results["errors"].append(ds["name"])

            results["needs_walkforward"] = self._check_walkforward_coverage()

            gm.agent_monitors(self.name, "Dataset", "name", "*")
            self._mark_idle()
        except Exception as exc:
            self._mark_error(str(exc))
            raise
        return results

    def _check_walkforward_coverage(self) -> list[str]:
        """Flag strategies with a backtest but no recent completed walkforward.

        Returns the strategy names flagged. Each is marked
        ``status='needs_walkforward'`` so the deployment gate and a future
        WalkforwardAgent can act on it. A strategy whose latest completed
        walk-forward run is older than ``WALKFORWARD_STALENESS_DAYS`` is treated
        the same as one with no run at all.
        """
        from agent_graph_system.graph.backend import (
            latest_backtest_for_strategy,
            latest_walkforward_for_strategy,
        )

        flagged: list[str] = []
        strategies = query("MATCH (s:Strategy) RETURN s.name AS name")
        cutoff = datetime.utcnow() - timedelta(days=WALKFORWARD_STALENESS_DAYS)
        for s in strategies:
            name = s.get("name")
            if not name or latest_backtest_for_strategy(name) is None:
                continue
            wf = latest_walkforward_for_strategy(name)
            if wf is not None and not _is_stale(wf.get("created_at"), cutoff):
                continue
            gm.upsert_strategy(
                name,
                strategy_type=self._strategy_type(name),
                status="needs_walkforward",
            )
            flagged.append(name)
            log.warning("[MonitoringAgent] strategy needs walk-forward: %s", name)
        return flagged

    @staticmethod
    def _strategy_type(name: str) -> str:
        """Preserve an existing strategy's type when re-upserting its status."""
        from agent_graph_system.graph.local import engine
        node = engine.get_node(f"Strategy::{name}") or {}
        return node.get("strategy_type", "unknown")
