"""Validators enforce ontology invariants beyond what JSON Schema expresses.

Phase I ships the governance validator (SemVer + Append-only). Compliance
and WBS-classification validators arrive in Phase II.
"""

from __future__ import annotations

from ontology.validators.governance import (
    BreakingChangeError,
    GovernanceViolation,
    compare_enum_definitions,
    compare_schemas,
    validate_semver_bump,
)

__all__ = [
    "GovernanceViolation",
    "BreakingChangeError",
    "compare_schemas",
    "compare_enum_definitions",
    "validate_semver_bump",
]
