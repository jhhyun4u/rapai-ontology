"""Constraint/Rule Engine (Phase III W1-W2).

Implements SBVR-based business rule enforcement with 13 core rules (R001-R013).
Enables:
  - Declarative rule specification (SBVR format)
  - Runtime rule evaluation against object instances
  - Violation detection and audit trails
  - Decision trace linking to triggering rules (explainability)
"""

from __future__ import annotations

from ontology.rules.engine import Rule, RuleEngine, RuleResult, RuleViolation
from ontology.rules.registry import RuleRegistry

__all__ = [
    "Rule",
    "RuleEngine",
    "RuleRegistry",
    "RuleResult",
    "RuleViolation",
]
