"""Write-time policy enforcement for the ontology graph.

This is where ``rules.yaml`` stops being documentation and starts being
behaviour. The flagship rule is ``deployment_gate``: a Strategy may only be
written with a live ``DEPLOYS_TO`` edge when its latest completed Backtest
clears the Sharpe threshold. Enforcement is *fail-closed* — a missing or
failing backtest denies the write.

The supported graph API (``graph_models.strategy_deploys_to``) calls
:func:`check_deployment_gate` before writing, and raises
:class:`PolicyViolation` on denial.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from agent_graph_system.ontology.rules import Rule, get_rule

log = logging.getLogger(__name__)

DEFAULT_SHARPE_THRESHOLD = 0.5

# Above this bootstrap p-value a strategy's out-of-sample Sharpe cannot be
# distinguished from noise, so it is denied a live deployment.
BOOTSTRAP_P_VALUE_THRESHOLD = 0.10

# Environments treated as "live" for gating purposes. paper/staging are not
# gated — they are exactly where un-validated strategies are meant to run.
LIVE_ENVIRONMENTS = frozenset({"live"})

# Backtest statuses that must never satisfy the gate.
_INVALID_BACKTEST_STATUSES = frozenset({"failed", "running"})


@dataclass(frozen=True)
class PolicyDecision:
    """The result of a policy check.

    ``allowed`` is the only field callers must branch on; ``code`` and
    ``message`` explain why, and ``evidence`` carries the supporting facts.
    """

    allowed: bool
    code: str
    message: str
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:  # convenience: `if decision: ...`
        return self.allowed


class PolicyViolation(RuntimeError):
    """Raised when a fail-closed policy denies a graph write."""

    def __init__(self, decision: PolicyDecision):
        self.decision = decision
        super().__init__(f"[{decision.code}] {decision.message}")


def _threshold_from_rule(rule: Rule | None) -> float:
    """Parse a ``Backtest.sharpe >= 0.5``-style condition into a float."""
    if rule is None:
        return DEFAULT_SHARPE_THRESHOLD
    condition = str(rule.raw.get("condition", ""))
    match = re.search(r"sharpe\s*>=?\s*(-?\d+(?:\.\d+)?)", condition, re.IGNORECASE)
    return float(match.group(1)) if match else DEFAULT_SHARPE_THRESHOLD


def _backtest_sharpe(backtest: dict[str, Any]) -> float | None:
    value = backtest.get("sharpe")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_deployment_gate(
    strategy: str,
    environment: str,
    *,
    latest_backtest: dict[str, Any] | None = None,
    latest_walkforward: dict[str, Any] | None = None,
    threshold: float | None = None,
    p_value_threshold: float = BOOTSTRAP_P_VALUE_THRESHOLD,
) -> PolicyDecision:
    """Decide whether ``strategy`` may deploy to ``environment``.

    Enforcement only applies when the ``deployment_gate`` rule is
    ``status: enforced`` AND ``severity: blocking`` AND the environment is
    live. In every other case the write is allowed (and the reason is recorded
    in the decision ``code``), which keeps the YAML honest: a non-enforced rule
    never silently blocks.

    When the gate IS active it is fail-closed. A live deployment must clear two
    bars, in order:

    1. **Backtest** — a valid completed backtest whose Sharpe meets ``threshold``
       (a missing backtest, non-numeric Sharpe, or sub-threshold Sharpe denies).
    2. **Walk-forward** — a completed, genuine (``mode='walkforward'``) run must
       validate the *exact* backtest being gated, and its bootstrap p-value
       (when present) must be a finite number at or below ``p_value_threshold``.
       A ``rolling_holdout`` run, a run validating a different backtest, or a
       non-finite p-value all deny.

    ``latest_backtest`` / ``latest_walkforward`` may be injected (mainly for
    tests); otherwise they are fetched from the active graph backend.
    """
    env = (environment or "").strip().lower()
    rule = get_rule("deployment_gate")

    if rule is None or rule.is_disabled:
        return PolicyDecision(True, "GATE_DISABLED", "deployment_gate rule is disabled.")

    if env not in LIVE_ENVIRONMENTS:
        return PolicyDecision(
            True, "NOT_LIVE", f"Environment '{env or environment}' is not gated."
        )

    if not rule.is_hard_gate:
        # blocking-but-not-enforced (or enforced-but-not-blocking): documented
        # guidance only. Allow the write but say so plainly.
        return PolicyDecision(
            True,
            "GATE_NOT_ENFORCED",
            f"deployment_gate is status={rule.status.value}, severity="
            f"{rule.severity.value if rule.severity else 'none'}; not enforced.",
        )

    bt_threshold = threshold if threshold is not None else _threshold_from_rule(rule)

    if latest_backtest is None:
        from agent_graph_system.graph.backend import latest_backtest_for_strategy

        latest_backtest = latest_backtest_for_strategy(strategy)

    if not latest_backtest:
        return PolicyDecision(
            False,
            "MISSING_BACKTEST",
            f"Strategy '{strategy}' has no valid completed backtest; "
            "cannot deploy live (fail-closed).",
        )

    sharpe = _backtest_sharpe(latest_backtest)
    bt_id = latest_backtest.get("run_id") or latest_backtest.get("name") or "unknown"
    evidence = [{"node": f"Backtest:{bt_id}", "metric": "sharpe", "value": sharpe}]

    if sharpe is None:
        return PolicyDecision(
            False,
            "MISSING_BACKTEST",
            f"Latest backtest for '{strategy}' has no numeric Sharpe; "
            "cannot deploy live (fail-closed).",
            evidence,
        )

    if sharpe < bt_threshold:
        return PolicyDecision(
            False,
            "DEPLOYMENT_GATE_FAILED",
            f"Latest backtest Sharpe {sharpe} is below threshold {bt_threshold}.",
            evidence,
        )

    # Second bar: out-of-sample walk-forward validation of THIS backtest.
    # Look the run up by the exact backtest being gated (not merely the newest
    # run for the strategy), so a stale run that validated an older backtest
    # cannot green-light a newer one.
    if latest_walkforward is None:
        from agent_graph_system.graph.backend import latest_walkforward_for_backtest

        latest_walkforward = latest_walkforward_for_backtest(bt_id)

    if not latest_walkforward:
        return PolicyDecision(
            False,
            "NO_WALKFORWARD",
            f"Strategy '{strategy}' has a passing backtest but no completed "
            f"walk-forward run validating backtest {bt_id}; cannot deploy live "
            "(fail-closed).",
            evidence,
        )

    # If the run records which backtest it validated, it must be this one. (An
    # injected run without the field is treated as a caller assertion that it is
    # the relevant one.)
    validated_bt = latest_walkforward.get("validates_backtest")
    if validated_bt is not None and validated_bt != bt_id:
        return PolicyDecision(
            False,
            "NO_WALKFORWARD",
            f"Latest walk-forward run validates backtest {validated_bt}, not the "
            f"gated backtest {bt_id}; cannot deploy live (fail-closed).",
            evidence,
        )

    # The run must be genuine out-of-sample evaluation. A ``rolling_holdout`` run
    # (one precomputed series sliced into windows, no refit) is in-sample
    # reporting and cannot validate a live deploy. A run with no recorded mode is
    # treated as a caller/legacy assertion of a real run.
    wf_mode = latest_walkforward.get("mode") or "walkforward"
    if wf_mode != "walkforward":
        return PolicyDecision(
            False,
            "NOT_OUT_OF_SAMPLE",
            f"Walk-forward run for '{strategy}' is mode='{wf_mode}' (rolling "
            "holdout / in-sample slicing), not genuine out-of-sample evaluation; "
            "cannot validate a live deploy (fail-closed).",
            evidence,
        )

    p_value = latest_walkforward.get("bootstrap_p_value")
    wf_id = latest_walkforward.get("run_id") or "unknown"
    evidence.append({
        "node": f"WalkforwardRun:{wf_id}",
        "metric": "bootstrap_p_value",
        "value": p_value,
    })

    # When a p-value is present it must be a finite number. A non-numeric or NaN
    # value is malformed validation data and must fail closed rather than fall
    # through to PASSED (a NaN comparison is always False).
    if p_value is not None:
        import math

        try:
            p_value_f = float(p_value)
        except (TypeError, ValueError):
            p_value_f = math.nan
        if not math.isfinite(p_value_f):
            return PolicyDecision(
                False,
                "INVALID_PVALUE",
                f"Walk-forward bootstrap p-value {p_value!r} is not a finite "
                "number; cannot validate (fail-closed).",
                evidence,
            )
        if p_value_f > p_value_threshold:
            return PolicyDecision(
                False,
                "NOT_SIGNIFICANT",
                f"Bootstrap p-value {p_value_f:.3f} > {p_value_threshold}; "
                "out-of-sample Sharpe is not distinguishable from noise.",
                evidence,
            )

    return PolicyDecision(
        True,
        "DEPLOYMENT_GATE_PASSED",
        f"Latest backtest Sharpe {sharpe} meets threshold {bt_threshold} and a "
        "walk-forward run validates it out of sample.",
        evidence,
    )
