"""Pydantic v2 models for RAPai Ontology.

Exports the Core 5 (Phase I) Objects and shared enum types.
Extended 10 Objects and Links/Actions arrive in Phase II.
"""

from __future__ import annotations

from ontology.models.core import Event, Person, Project, Task, WorkLog
from ontology.models.enums import (
    ContractModality,
    CrossCutting,
    DailyReportTag,
    FundingSource,
    GateLevel,
    GateStatus,
    Intent,
    KPITier,
    ProjectStatus,
    ProjectTypeCode,
    ScaleTier,
    SecurityTier,
    TaskStatus,
)

__all__ = [
    # Core objects
    "Project",
    "Task",
    "WorkLog",
    "Person",
    "Event",
    # Enums
    "ProjectTypeCode",
    "ContractModality",
    "FundingSource",
    "SecurityTier",
    "ScaleTier",
    "GateLevel",
    "GateStatus",
    "KPITier",
    "DailyReportTag",
    "TaskStatus",
    "ProjectStatus",
    "Intent",
    "CrossCutting",
]
