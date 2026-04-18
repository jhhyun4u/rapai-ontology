"""Rule Engine core classes: Rule, RuleEngine, RuleResult, RuleViolation.

Implements declarative rule evaluation and enforcement against ontology objects.
Rules are specified in SBVR format and evaluated against context dictionaries.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RuleSeverity(str, Enum):
    """Deontic modality for rules (RFC 2119 inspired)."""

    MUST = "must"        # Mandatory compliance
    SHOULD = "should"    # Strongly recommended
    MAY = "may"          # Optional


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    satisfied: bool
    reason: str | None = None
    constraint_value: Any | None = None

    def __bool__(self) -> bool:
        """Allow truthiness check."""
        return self.satisfied


@dataclass
class RuleViolation:
    """A rule violation (rule not satisfied)."""

    rule_id: str
    reason: str
    severity: RuleSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Rule:
    """A declarative business rule in SBVR format.

    SBVR (Semantic Business Vocabulary and Business Rules) provides
    natural-language-like specification of business logic.
    """

    rule_id: str
    """Unique rule identifier (e.g., 'R001')."""

    sbvr_statement: str
    """Human-readable SBVR rule statement."""

    severity: RuleSeverity = RuleSeverity.MUST
    """Deontic modality: MUST (mandatory), SHOULD (recommended), MAY (optional)."""

    affected_entities: list[str] = field(default_factory=list)
    """Entity types this rule applies to (e.g., ['Blocker', 'Task'])."""

    condition: Callable[[dict[str, Any]], bool] | None = None
    """Optional evaluation function; if None, rule is declarative-only."""

    neo4j_constraint: str | None = None
    """Optional Neo4j Cypher constraint (enforced at graph level)."""

    def evaluate(self, context: dict[str, Any]) -> RuleResult:
        """Evaluate this rule against a context dictionary.

        Args:
            context: Context dict with data for rule evaluation

        Returns:
            RuleResult with satisfied boolean and optional reason/constraint value
        """
        if self.condition is None:
            # Declarative-only rule; cannot evaluate
            return RuleResult(
                satisfied=True,
                reason="Declarative rule (no evaluation function)"
            )

        try:
            satisfied = self.condition(context)
            return RuleResult(satisfied=satisfied)
        except Exception as e:
            return RuleResult(
                satisfied=False,
                reason=f"Evaluation error: {e!s}"
            )


@dataclass
class DecisionTrace:
    """Complete audit trail linking a decision to triggering rules."""

    trace_id: str
    decision_id: str
    entity_id: str
    action_taken: str
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    explainability_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: str | None = None
    axioms: list[dict[str, str]] = field(default_factory=list)


class RuleEngine:
    """Constraint/Rule Engine: evaluates and enforces business rules.

    Responsibilities:
      1. Load rule registry
      2. Evaluate rules against object instances
      3. Enforce rules (detect violations)
      4. Audit decisions (link to triggering rules)
    """

    def __init__(self) -> None:
        """Initialize engine with rule registry."""
        from ontology.rules.registry import RuleRegistry

        self.registry: RuleRegistry = RuleRegistry()
        self._rule_cache: dict[str, Rule] = {}

    def evaluate(self, rule_id: str, context: dict[str, Any]) -> RuleResult:
        """Evaluate a single rule against context.

        Args:
            rule_id: Rule ID to evaluate (e.g., 'R001')
            context: Context dictionary for evaluation

        Returns:
            RuleResult with satisfied boolean
        """
        rule = self.registry.get(rule_id)
        return rule.evaluate(context)

    def enforce(
        self,
        obj: Any,
        rule_ids: list[str]
    ) -> list[RuleViolation]:
        """Enforce a list of rules against an object or context dict.

        Args:
            obj: Pydantic object instance, dict, or any object with attributes
            rule_ids: List of rule IDs to enforce

        Returns:
            List of RuleViolation objects (empty if all satisfied)
        """
        violations: list[RuleViolation] = []

        # Extract object fields as context
        if isinstance(obj, dict):
            context = obj
        elif hasattr(obj, '__pydantic_core__'):
            context = obj.model_dump()
        else:
            context = vars(obj)

        for rule_id in rule_ids:
            result = self.evaluate(rule_id, context)

            if not result.satisfied:
                rule = self.registry.get(rule_id)
                violation = RuleViolation(
                    rule_id=rule_id,
                    reason=result.reason or f"Rule {rule_id} not satisfied",
                    severity=rule.severity
                )
                violations.append(violation)

        return violations

    def audit_decision(
        self,
        decision: Any,
        triggered_rules: list[str],
        agent_id: str | None = None
    ) -> DecisionTrace:
        """Create audit trail linking decision to triggering rules.

        Args:
            decision: Decision object
            triggered_rules: List of rule IDs that enabled/constrained this decision
            agent_id: Agent that made the decision

        Returns:
            DecisionTrace with full audit information
        """
        # Extract SBVR statements
        axioms = []
        for rule_id in triggered_rules:
            try:
                rule = self.registry.get(rule_id)
                axioms.append({
                    'rule_id': rule_id,
                    'sbvr_statement': rule.sbvr_statement
                })
            except KeyError:
                pass

        # Calculate explainability score: ratio of rules backing decision
        # Normalize: 1 rule = 0.33, 2 rules = 0.67, 3+ = 1.0
        explainability_score = min(1.0, len(triggered_rules) / 3.0)

        # Generate trace ID (simplified)
        trace_id = f"trace-{datetime.utcnow().isoformat()}"

        decision_id = getattr(decision, 'decision_id', 'unknown')
        entity_id = getattr(decision, 'context', 'unknown')

        trace = DecisionTrace(
            trace_id=trace_id,
            decision_id=decision_id,
            entity_id=entity_id,
            action_taken="approve_decision",
            triggered_rules=[
                {
                    'rule_id': rid,
                    'sbvr_statement': axioms[i]['sbvr_statement'],
                    'satisfied': True,
                    'constraint_value': None
                }
                for i, rid in enumerate(triggered_rules)
            ],
            explainability_score=explainability_score,
            agent_id=agent_id,
            axioms=axioms
        )

        return trace

    def explain_violation(self, rule_id: str) -> str:
        """Get human-readable explanation of a rule.

        Args:
            rule_id: Rule ID

        Returns:
            SBVR statement
        """
        rule = self.registry.get(rule_id)
        return rule.sbvr_statement
