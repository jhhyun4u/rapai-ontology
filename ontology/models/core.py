"""Pydantic v2 Core 5 models — Phase I Foundation.

Mirrors the JSON Schemas in ``ontology/schemas/*.json`` (SSOT per ADR-001 R5).
Roundtrip equivalence is asserted by ``ontology/tests/unit/test_roundtrip.py``.

Maintenance rule (from ontology/06-ontology-design-charter.md):
- Schema changes flow JSON Schema \u2192 model, NEVER the other way.
- Breaking change requires SemVer major bump + migration script.
- New fields default to optional to preserve Append-only semantics.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, model_validator

from ontology.models.enums import (
    PROJECT_TYPES_REQUIRING_CRL,
    PROJECT_TYPES_REQUIRING_TRL,
    CloudEventsSpecVersion,
    CrossCutting,
    DailyReportTag,
    ProjectStatus,
    ProjectTypeCode,
    SecurityTier,
    TaskStatus,
)

# ── Shared primitives ────────────────────────────────────────────────────

# ULID (26) or UUIDv7 canonical form (36) \u2014 mirrors enums.json/Identifier.
_IDENTIFIER_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
Identifier = Annotated[
    str,
    StringConstraints(min_length=26, max_length=36, pattern=_IDENTIFIER_PATTERN.pattern),
]

# Semantic shortcuts for "bounded string".
ShortStr = Annotated[str, StringConstraints(min_length=1, max_length=256)]
LongStr = Annotated[str, StringConstraints(min_length=1, max_length=32768)]


# ── TRL/CRL Progression (Phase III W2-W3) ────────────────────────────────
class TRLProgressionEntry(BaseModel):
    """Record of a single TRL level transition (audit trail)."""

    from_level: Annotated[int, Field(ge=1, le=9)]
    to_level: Annotated[int, Field(ge=1, le=9)]
    transitioned_at: datetime
    evidence_artifacts: list[Identifier] | None = None
    approved_by: Identifier | None = None
    gate_decision_trace_id: Identifier | None = None

    model_config = ConfigDict(extra="forbid")


class CRLProgressionEntry(BaseModel):
    """Record of a single CRL level transition (audit trail)."""

    from_level: Annotated[int, Field(ge=1, le=9)]
    to_level: Annotated[int, Field(ge=1, le=9)]
    transitioned_at: datetime
    evidence_artifacts: list[Identifier] | None = None
    approved_by: Identifier | None = None
    gate_decision_trace_id: Identifier | None = None

    model_config = ConfigDict(extra="forbid")


class _OntologyObject(BaseModel):
    """Common base for every Core Object.

    Enforces:
    - ``extra='forbid'`` \u2014 unknown fields rejected (Ontology compliance).
    - Datetime ISO-8601 serialization via default Pydantic v2 behavior.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=False,  # Objects are mutable in-process; persistence layer enforces append-only.
        populate_by_name=True,
        json_schema_extra={"x-ontology-version": "0.1.0", "x-ontology-layer": "L2.5"},
    )


# ── Project ───────────────────────────────────────────────────────────────
class Project(_OntologyObject):
    """A research project, the unit of governance in RAPai."""

    project_id: Identifier
    name: ShortStr
    project_type: ProjectTypeCode
    cross_cutting: CrossCutting
    status: ProjectStatus
    start_date: date
    end_date: date | None = None
    pi_person_id: Identifier | None = None
    sponsor: Annotated[str, StringConstraints(max_length=256)] | None = None
    trl_target: Annotated[int, Field(ge=1, le=9)] | None = None
    crl_target: Annotated[int, Field(ge=1, le=9)] | None = None
    current_trl: Annotated[int, Field(ge=1, le=9)] | None = None
    current_crl: Annotated[int, Field(ge=1, le=9)] | None = None
    trl_progression_history: list[TRLProgressionEntry] | None = None
    crl_progression_history: list[CRLProgressionEntry] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _enforce_trl_crl_by_type(self) -> Project:
        """Mirror the JSON Schema ``allOf`` conditionals in Pydantic space."""
        if self.project_type in PROJECT_TYPES_REQUIRING_TRL and self.trl_target is None:
            raise ValueError(
                f"project_type={self.project_type.value} requires 'trl_target' (decision 9)."
            )
        if self.project_type in PROJECT_TYPES_REQUIRING_CRL and self.crl_target is None:
            raise ValueError(
                f"project_type={self.project_type.value} requires 'crl_target' (decision 9)."
            )
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


# ── Task ──────────────────────────────────────────────────────────────────
class Task(_OntologyObject):
    """A WBS unit of work."""

    task_id: Identifier
    project_id: Identifier
    parent_task_id: Identifier | None = None
    wbs_code: Annotated[str, StringConstraints(max_length=64, pattern=r"^[0-9]+(\.[0-9]+)*$")]
    title: ShortStr
    description: Annotated[str, StringConstraints(max_length=4096)] | None = None
    status: TaskStatus
    deadline: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    assigned_person_ids: list[Identifier] = Field(default_factory=list)
    deliverable_artifact_ids: list[Identifier] = Field(default_factory=list)
    depends_on_task_ids: list[Identifier] = Field(default_factory=list)
    estimated_hours: Annotated[float, Field(ge=0)] | None = None
    actual_hours: Annotated[float, Field(ge=0)] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _no_self_reference(self) -> Task:
        if self.parent_task_id == self.task_id:
            raise ValueError("parent_task_id must differ from task_id.")
        if self.task_id in self.depends_on_task_ids:
            raise ValueError("A task cannot depend on itself.")
        if self.end_date is not None and self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        # Uniqueness in id lists.
        for field_name, values in (
            ("assigned_person_ids", self.assigned_person_ids),
            ("deliverable_artifact_ids", self.deliverable_artifact_ids),
            ("depends_on_task_ids", self.depends_on_task_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must contain unique identifiers.")
        return self


# ── WorkLog ───────────────────────────────────────────────────────────────
class WorkLog(_OntologyObject):
    """A daily/event-triggered work log, input to Parser LLM."""

    log_id: Identifier
    task_id: Identifier
    project_id: Identifier | None = None
    author_person_id: Identifier
    date: date
    content: LongStr
    tags: Annotated[list[DailyReportTag], Field(min_length=1)]
    trl_observed: Annotated[int, Field(ge=1, le=9)] | None = None
    crl_observed: Annotated[int, Field(ge=1, le=9)] | None = None
    hours_spent: Annotated[float, Field(ge=0, le=24)] | None = None
    linked_artifact_ids: list[Identifier] = Field(default_factory=list)
    linked_blocker_ids: list[Identifier] = Field(default_factory=list)
    prov_id: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _tags_unique(self) -> WorkLog:
        if len(self.tags) != len(set(self.tags)):
            raise ValueError("tags must be unique.")
        for field_name, values in (
            ("linked_artifact_ids", self.linked_artifact_ids),
            ("linked_blocker_ids", self.linked_blocker_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must contain unique identifiers.")
        return self


# ── Person ────────────────────────────────────────────────────────────────
class Person(_OntologyObject):
    """A human actor. FOAF-aligned (ADR-001 R4)."""

    person_id: Identifier
    name: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    email: EmailStr | None = None
    role_ids: list[Identifier] = Field(default_factory=list)
    security_clearance: SecurityTier
    organization: Annotated[str, StringConstraints(max_length=256)] | None = None
    foaf_uri: str | None = None
    active: bool = True
    created_at: datetime | None = None

    @model_validator(mode="after")
    def _roles_unique(self) -> Person:
        if len(self.role_ids) != len(set(self.role_ids)):
            raise ValueError("role_ids must be unique.")
        return self


# ── Event (CloudEvents 1.0) ───────────────────────────────────────────────
_CE_TYPE_PATTERN = r"^[a-z][a-z0-9._-]*\.v[0-9]+$"


class Event(_OntologyObject):
    """CloudEvents 1.0 compatible envelope for Outbox + PROV-O (patent CP5)."""

    id: str
    source: str  # CloudEvents uri-reference; validated loosely.
    type: Annotated[str, StringConstraints(pattern=_CE_TYPE_PATTERN)]
    specversion: CloudEventsSpecVersion = "1.0"
    time: datetime
    subject: str | None = None
    datacontenttype: str = "application/json"
    dataschema: str | None = None
    data: Any | None = None

    prov_id: str | None = None
    actor_person_id: Identifier | None = None
    actor_agent_id: str | None = None
    security_tier: SecurityTier | None = None
    model_id: str | None = None
    confidence: Annotated[float, Field(ge=0, le=1)] | None = None

    @model_validator(mode="after")
    def _llm_sourced_events_require_model_id(self) -> Event:
        """If ``actor_agent_id`` looks like an LLM agent and confidence is set,
        a ``model_id`` must accompany the event for PROV-O lineage integrity.
        """
        has_llm_signal = self.confidence is not None or (
            self.actor_agent_id is not None and self.actor_agent_id.startswith("AG-")
        )
        if has_llm_signal and self.model_id is None and self.actor_agent_id != "AG-INT":
            # AG-INT (Coordinator) is exempt because it delegates; others that report
            # confidence must attribute the model producing it.
            raise ValueError(
                "model_id is required when an LLM-backed agent reports 'confidence' "
                "(PROV-O lineage / patent CP5)."
            )
        return self


__all__ = ["Event", "Identifier", "Person", "Project", "Task", "WorkLog"]
