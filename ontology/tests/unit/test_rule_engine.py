"""Unit tests for Rule Engine (W1-W2 Phase III).

Tests core Rule, RuleEngine, and RuleRegistry functionality.
Validates: rule evaluation, enforcement, violation detection, and decision tracing.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from ontology.rules.engine import Rule, RuleEngine, RuleResult, RuleViolation
from ontology.rules.registry import RuleRegistry
from ontology.models.core import Task, Project
from ontology.models.extended import Blocker, Decision, Gate
from ontology.models.enums import (
    TaskStatus, BlockerStatus, ProjectStatus, Severity, ProjectTypeCode,
    GateLevel, GateStatus
)


class TestRuleBasics:
    """Test basic Rule class functionality."""

    def test_rule_creation(self):
        """Rule can be created with all required fields."""
        rule = Rule(
            rule_id="R001",
            sbvr_statement="If a Blocker is resolved, Task must transition from blocked within 24h",
            severity="must",
            affected_entities=["Blocker", "Task"]
        )

        assert rule.rule_id == "R001"
        assert rule.sbvr_statement is not None
        assert rule.severity == "must"
        assert len(rule.affected_entities) == 2

    def test_rule_result_satisfied(self):
        """RuleResult can represent satisfied rules."""
        result = RuleResult(satisfied=True, reason=None)
        assert result.satisfied is True
        assert result.reason is None

    def test_rule_result_violated(self):
        """RuleResult can represent violated rules with reason."""
        result = RuleResult(
            satisfied=False,
            reason="Project type A requires TRL gate, but none found"
        )
        assert result.satisfied is False
        assert "TRL gate" in result.reason


class TestRuleRegistry:
    """Test Rule Registry (SSOT for all rules)."""

    def test_registry_loads_builtin_rules(self):
        """Registry loads all 10 builtin rules (R001-R010)."""
        registry = RuleRegistry()
        rules = registry.list_all()

        assert len(rules) >= 10
        rule_ids = {r.rule_id for r in rules}
        assert "R001" in rule_ids
        assert "R010" in rule_ids

    def test_registry_fetch_by_id(self):
        """Registry can fetch rule by ID."""
        registry = RuleRegistry()
        rule = registry.get("R001")

        assert rule is not None
        assert rule.rule_id == "R001"
        assert "Blocker" in rule.affected_entities

    def test_registry_unknown_rule_raises(self):
        """Registry raises on unknown rule ID."""
        registry = RuleRegistry()

        with pytest.raises(KeyError):
            registry.get("R999")


class TestRuleEngine:
    """Test Rule Engine (evaluation and enforcement)."""

    @pytest.fixture
    def engine(self):
        """Create Rule Engine instance."""
        return RuleEngine()

    def test_engine_creation(self, engine):
        """RuleEngine initializes with registry."""
        assert engine is not None
        assert engine.registry is not None
        assert len(engine.registry.list_all()) >= 10

    def test_evaluate_rule_satisfied(self, engine):
        """Engine evaluates satisfied rule correctly."""
        # R001 context: Blocker resolved, Task was blocked, elapsed < 24h
        result = engine.evaluate(
            "R001",
            context={
                'status': 'resolved',
                'severity': 'critical',
                'task_status': 'blocked',
                'elapsed_hours': 12  # < 24h = satisfied
            }
        )

        assert result.satisfied is True

    def test_evaluate_rule_violated(self, engine):
        """Engine detects rule violation."""
        # R001 context: Blocker resolved >24h ago, Task still blocked
        result = engine.evaluate(
            "R001",
            context={
                'status': 'resolved',
                'severity': 'critical',
                'task_status': 'blocked',
                'elapsed_hours': 26  # > 24h = violated
            }
        )

        assert result.satisfied is False


class TestConstraintEnforcement:
    """Test Rule Engine enforcement (detecting violations)."""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_enforce_no_violations(self, engine):
        """Enforce returns empty list when all rules satisfied."""
        # Create a dict-based context (R002: Type C has no gate requirement)
        context = {
            'project_type': 'C',
            'gates': []  # Type C doesn't require gates
        }

        violations = engine.enforce(context, ["R002"])

        assert isinstance(violations, list)
        assert len(violations) == 0

    def test_enforce_returns_violations(self, engine):
        """Enforce returns violation when rule broken."""
        # Project type A with no gates (R002 violation)
        context = {
            'project_type': 'A',  # Requires TRL gate
            'gates': []  # No gates = violation
        }

        violations = engine.enforce(context, ["R002"])

        assert len(violations) > 0
        assert violations[0].rule_id == "R002"


class TestDecisionTracing:
    """Test Decision Trace linking to rules."""

    @pytest.fixture
    def engine(self):
        return RuleEngine()

    def test_audit_decision_traces_rules(self, engine):
        """audit_decision links decision to triggering rules."""
        # Create a minimal decision-like object
        class SimpleDecision:
            decision_id = "dec-001"
            context = "Task status transition"

        decision = SimpleDecision()
        triggered_rules = ["R001", "R004"]

        trace = engine.audit_decision(
            decision,
            triggered_rules=triggered_rules,
            agent_id="ag-pi-001"
        )

        assert trace.decision_id == "dec-001"
        assert len(trace.axioms) == len(triggered_rules)
        assert trace.axioms[0]['rule_id'] == "R001"
        assert trace.axioms[1]['rule_id'] == "R004"
        assert trace.explainability_score > 0.5  # 2 rules → ~0.67


class TestRuleR001BlockerResolution:
    """Test R001: Blocker resolution → Task progress (24h window)."""

    def test_r001_within_24h_satisfied(self):
        """R001 satisfied: Blocker resolved, task transitioned within 24h."""
        engine = RuleEngine()

        blocker_resolved_at = datetime.utcnow() - timedelta(hours=12)
        task_status_changed_at = datetime.utcnow()

        result = engine.evaluate(
            "R001",
            context={
                'blocker_severity': 'critical',
                'blocker_resolved_at': blocker_resolved_at,
                'task_status_changed_at': task_status_changed_at,
                'task_status': TaskStatus.IN_PROGRESS
            }
        )

        assert result.satisfied is True

    def test_r001_after_24h_violated(self):
        """R001 violated: Blocker resolved >24h, task still blocked."""
        engine = RuleEngine()

        result = engine.evaluate(
            "R001",
            context={
                'status': 'resolved',
                'severity': 'critical',
                'task_status': 'blocked',
                'elapsed_hours': 30  # > 24h = violated
            }
        )

        assert result.satisfied is False


class TestRuleR002TRLGate:
    """Test R002: Project type A/B require TRL gate."""

    def test_r002_type_a_no_gate_violated(self):
        """R002 violated: Type A project without TRL gate."""
        engine = RuleEngine()

        result = engine.evaluate(
            "R002",
            context={
                'project_type': 'A',
                'gates': []  # No gates = violation
            }
        )

        assert result.satisfied is False

    def test_r002_type_c_no_requirement(self):
        """R002 satisfied: Type C has no TRL gate requirement."""
        engine = RuleEngine()

        result = engine.evaluate(
            "R002",
            context={
                'project_type': 'C',
                'gates': []  # Type C doesn't require TRL
            }
        )

        assert result.satisfied is True


class TestRuleR004DependencyAcyclicity:
    """Test R004: No cycles in Task dependencies."""

    def test_r004_acyclic_satisfied(self):
        """R004 satisfied: Task dependencies form valid DAG."""
        engine = RuleEngine()

        # Task graph: T1 → T2 → T3 (acyclic)
        dependencies = {
            "T1": [],
            "T2": ["T1"],
            "T3": ["T2"]
        }

        result = engine.evaluate(
            "R004",
            context={
                'dependencies': dependencies
            }
        )

        assert result.satisfied is True

    def test_r004_cycle_violated(self):
        """R004 violated: Task has circular dependency."""
        engine = RuleEngine()

        # Task graph: T1 → T2 → T1 (cycle!)
        dependencies = {
            "T1": ["T2"],
            "T2": ["T1"]
        }

        result = engine.evaluate(
            "R004",
            context={
                'dependencies': dependencies
            }
        )

        assert result.satisfied is False


class TestRuleR010IntentMapping:
    """Test R010: WorkDirective intent must map to valid Action."""

    def test_r010_valid_intent_satisfied(self):
        """R010 satisfied: Intent is valid enum value."""
        engine = RuleEngine()

        valid_intents = [
            "create_task", "update_status", "log_work", "assign_person",
            "raise_blocker", "resolve_blocker", "record_decision",
            "submit_gate", "measure_kpi", "produce_artifact"
        ]

        for intent in valid_intents:
            result = engine.evaluate(
                "R010",
                context={'intent': intent}
            )
            assert result.satisfied is True

    def test_r010_invalid_intent_violated(self):
        """R010 violated: Invalid intent value."""
        engine = RuleEngine()

        result = engine.evaluate(
            "R010",
            context={'intent': 'invalid_intent_xyz'}
        )

        assert result.satisfied is False
