"""Load and validate ontology rules from ``ontology/schema/rules.yaml``.

The point of this module is honesty: the YAML must never imply an enforced
safety guarantee that the code does not actually provide. Every rule carries
an explicit ``status``:

    proposed   - an idea only; never enforced by code.
    documented - describes current behaviour / guidance; not a hard gate.
    enforced   - code MUST enforce this rule (see ``ontology/policy.py``).
    disabled   - explicitly turned off; ignored everywhere.

A rule is a hard, write-blocking gate ONLY when ``status == enforced`` and
``severity == blocking`` (``Rule.is_hard_gate``). A ``blocking`` severity on a
non-enforced rule is a documentation/warning signal — never a silent
guarantee — and :func:`validate_rules` surfaces it as a warning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from agent_graph_system.config import cfg

log = logging.getLogger(__name__)


class RuleStatus(str, Enum):
    PROPOSED = "proposed"
    DOCUMENTED = "documented"
    ENFORCED = "enforced"
    DISABLED = "disabled"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"
    ERROR = "error"


# Rules predating explicit status semantics default to ``documented`` — the
# safe choice, because documented rules never enforce.
_DEFAULT_STATUS = RuleStatus.DOCUMENTED


@dataclass(frozen=True)
class Rule:
    """A single ontology rule with explicit enforcement status."""

    name: str
    status: RuleStatus
    severity: Severity | None = None
    description: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def is_enforced(self) -> bool:
        return self.status is RuleStatus.ENFORCED

    @property
    def is_disabled(self) -> bool:
        return self.status is RuleStatus.DISABLED

    @property
    def is_hard_gate(self) -> bool:
        """True only when code must block writes on violation.

        This is the single source of truth for "does this rule actually
        block something". It requires BOTH an enforced status and a blocking
        severity, so no amount of YAML alone can turn a rule into a gate.
        """
        return self.is_enforced and self.severity is Severity.BLOCKING


def _coerce_status(name: str, value: Any) -> RuleStatus:
    if value is None:
        log.warning(
            "Rule '%s' has no status; defaulting to '%s' (not enforced).",
            name,
            _DEFAULT_STATUS.value,
        )
        return _DEFAULT_STATUS
    try:
        return RuleStatus(str(value).strip().lower())
    except ValueError as exc:
        valid = ", ".join(s.value for s in RuleStatus)
        raise ValueError(
            f"Rule '{name}' has invalid status {value!r}. Valid: {valid}."
        ) from exc


def _coerce_severity(name: str, value: Any) -> Severity | None:
    if value is None:
        return None
    try:
        return Severity(str(value).strip().lower())
    except ValueError as exc:
        valid = ", ".join(s.value for s in Severity)
        raise ValueError(
            f"Rule '{name}' has invalid severity {value!r}. Valid: {valid}."
        ) from exc


def _rules_path(path: str | Path | None = None) -> Path:
    return Path(path) if path is not None else cfg.ontology_dir / "rules.yaml"


def load_rules(path: str | Path | None = None) -> dict[str, Rule]:
    """Parse ``rules.yaml`` into validated :class:`Rule` objects.

    Raises ``ValueError`` on unknown ``status``/``severity`` values. Soft
    inconsistencies (e.g. ``blocking`` + ``documented``) are returned as
    warnings by :func:`validate_rules`, not raised here.
    """
    rules_path = _rules_path(path)
    if not rules_path.exists():
        raise FileNotFoundError(f"Ontology rules file not found: {rules_path}")

    raw = yaml.safe_load(rules_path.read_text()) or {}
    rule_block = raw.get("rules", {})
    if not isinstance(rule_block, dict):
        raise ValueError(f"'rules' must be a mapping in {rules_path}")

    rules: dict[str, Rule] = {}
    for name, body in rule_block.items():
        body = body or {}
        rules[name] = Rule(
            name=name,
            status=_coerce_status(name, body.get("status")),
            severity=_coerce_severity(name, body.get("severity")),
            description=str(body.get("description", "")),
            raw=dict(body),
        )
    return rules


def validate_rules(rules: dict[str, Rule]) -> list[str]:
    """Return human-readable warnings for self-inconsistent rules.

    The key invariant: a ``blocking`` severity must not masquerade as
    enforcement. ``blocking`` + (``proposed`` | ``documented``) is reported so
    the metadata cannot quietly imply a guarantee the code does not provide.
    """
    warnings: list[str] = []
    for rule in rules.values():
        if rule.severity is Severity.BLOCKING and rule.status in (
            RuleStatus.PROPOSED,
            RuleStatus.DOCUMENTED,
        ):
            warnings.append(
                f"Rule '{rule.name}' is severity=blocking but status={rule.status.value}: "
                "it is NOT enforced by code. Set status=enforced to make it a real gate, "
                "or lower the severity to avoid implying a guarantee."
            )
    return warnings


@lru_cache(maxsize=1)
def _cached_rules() -> dict[str, Rule]:
    rules = load_rules()
    for warning in validate_rules(rules):
        log.warning("%s", warning)
    return rules


def get_rule(name: str, *, reload: bool = False) -> Rule | None:
    """Look up a single rule by name from the default rules file (cached)."""
    if reload:
        _cached_rules.cache_clear()
    return _cached_rules().get(name)
