"""Tests for ontology rule loading and status semantics."""

from __future__ import annotations

import pytest

from agent_graph_system.ontology.rules import (
    Rule,
    RuleStatus,
    Severity,
    get_rule,
    load_rules,
    validate_rules,
)


def test_load_default_rules_parses_statuses():
    rules = load_rules()
    assert "deployment_gate" in rules
    for rule in rules.values():
        assert isinstance(rule.status, RuleStatus)


def test_deployment_gate_is_a_hard_gate():
    gate = load_rules()["deployment_gate"]
    assert gate.status is RuleStatus.ENFORCED
    assert gate.severity is Severity.BLOCKING
    assert gate.is_hard_gate is True


def test_documented_rule_is_not_a_hard_gate():
    rules = load_rules()
    staleness = rules["staleness"]
    assert staleness.status is RuleStatus.DOCUMENTED
    # warning severity + documented status must never block
    assert staleness.is_hard_gate is False
    assert staleness.is_enforced is False


def test_blocking_but_not_enforced_is_not_a_gate():
    # The core honesty invariant: blocking severity alone does not enforce.
    rule = Rule(name="x", status=RuleStatus.DOCUMENTED, severity=Severity.BLOCKING)
    assert rule.is_hard_gate is False
    rule_proposed = Rule(name="y", status=RuleStatus.PROPOSED, severity=Severity.BLOCKING)
    assert rule_proposed.is_hard_gate is False


def test_enforced_but_not_blocking_is_not_a_gate():
    rule = Rule(name="z", status=RuleStatus.ENFORCED, severity=Severity.WARNING)
    assert rule.is_enforced is True
    assert rule.is_hard_gate is False


def test_missing_status_defaults_to_documented(tmp_path):
    yaml_path = tmp_path / "rules.yaml"
    yaml_path.write_text(
        "rules:\n"
        "  legacy:\n"
        "    description: no status field\n"
        "    severity: warning\n"
    )
    rules = load_rules(yaml_path)
    assert rules["legacy"].status is RuleStatus.DOCUMENTED


def test_invalid_status_raises(tmp_path):
    yaml_path = tmp_path / "rules.yaml"
    yaml_path.write_text(
        "rules:\n"
        "  bad:\n"
        "    status: enforcedish\n"
    )
    with pytest.raises(ValueError, match="invalid status"):
        load_rules(yaml_path)


def test_invalid_severity_raises(tmp_path):
    yaml_path = tmp_path / "rules.yaml"
    yaml_path.write_text(
        "rules:\n"
        "  bad:\n"
        "    status: documented\n"
        "    severity: catastrophic\n"
    )
    with pytest.raises(ValueError, match="invalid severity"):
        load_rules(yaml_path)


def test_validate_rules_warns_on_blocking_non_enforced(tmp_path):
    yaml_path = tmp_path / "rules.yaml"
    yaml_path.write_text(
        "rules:\n"
        "  fake_gate:\n"
        "    status: documented\n"
        "    severity: blocking\n"
    )
    rules = load_rules(yaml_path)
    warnings = validate_rules(rules)
    assert any("fake_gate" in w for w in warnings)


def test_shipped_rules_have_no_dishonest_gates():
    # The committed rules.yaml must not advertise blocking severity without
    # backing it with enforcement.
    warnings = validate_rules(load_rules())
    assert warnings == [], f"Dishonest blocking rules: {warnings}"


def test_get_rule_returns_none_for_unknown():
    assert get_rule("does_not_exist") is None
