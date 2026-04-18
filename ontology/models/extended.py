"""Extended Objects (Phase II): 10 models for Phase II ontology expansion.

Auto-derivable from JSON Schemas (ontology/schemas/*.json) but with manual
business rule validators added below.

Source: ADR-001 R6, ontology/06-ontology-design-charter.md (governance).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology.models.enums import (
    ArtifactStatusExtended,
    ArtifactType,
    BlockerStatus,
    DecisionStatus,
    GateLevel,
    GateStatus,
    Intent,
    IPStatus,
    IPType,
    KPITier,
    Likelihood,
    ProjectStatus,
    RiskCategory,
    RoleType,
    SecurityTier,
    Severity,
    WorkDirectiveStatus,
)


class WorkDirective(BaseModel):
    """Work directive capturing work intent and entities (ontology/09).

    P0 enhancements (v0.3.0):
    - status: 6-state lifecycle (created → validated → dispatched → in_progress → completed/failed)
    - source_worklog_id, source_rule_ids, source_document: Provenance tracking (R020)
    """

    model_config = ConfigDict(extra="forbid")

    directive_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    parent_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    intent: Intent
    entities: list[dict[str, Any]] = Field(default_factory=list, description="Referenced entities")
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    status: WorkDirectiveStatus = WorkDirectiveStatus.CREATED
    source_worklog_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    source_rule_ids: list[str] = Field(default_factory=list, description="Rule IDs that triggered creation")
    source_document: str | None = Field(None, max_length=512)
    created_at: str | None = None
    updated_at: str | None = None

    @model_validator(mode="after")
    def validate_no_self_reference(self) -> WorkDirective:
        """Directives must not reference themselves."""
        if self.parent_id and self.parent_id == self.directive_id:
            raise ValueError("directive cannot reference itself as parent")
        return self


class Role(BaseModel):
    """Role definition (PI, Coordinator, Researcher, etc.)."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    name: RoleType
    description: str | None = Field(None, max_length=512)
    responsibilities: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Milestone(BaseModel):
    """Project milestone tied to deliverables."""

    model_config = ConfigDict(extra="forbid")

    milestone_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    project_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = Field(None, max_length=1024)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    deliverable_ids: list[str] = Field(default_factory=list)
    status: ProjectStatus | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Blocker(BaseModel):
    """Blocker impeding Task progress."""

    model_config = ConfigDict(extra="forbid")

    blocker_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    task_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    severity: Severity
    description: str = Field(..., min_length=1, max_length=2048)
    root_cause: str | None = Field(None, max_length=2048)
    mitigation: str | None = Field(None, max_length=2048)
    owner_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    status: BlockerStatus | None = None
    created_at: str | None = None
    resolved_at: str | None = None
    updated_at: str | None = None


class Decision(BaseModel):
    """Recorded decision with context, options, and chosen outcome."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    context: str = Field(..., min_length=1, max_length=2048)
    options: list[dict[str, Any]] = Field(default_factory=list, description="Evaluated options")
    chosen: str = Field(..., description="ID of chosen option")
    rationale: str = Field(..., min_length=1, max_length=2048)
    decision_maker_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    status: DecisionStatus | None = None
    prov_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    created_at: str | None = None
    updated_at: str | None = None

    @model_validator(mode="after")
    def validate_chosen_in_options(self) -> Decision:
        """Chosen option must exist in options."""
        option_ids = [opt.get("option_id") for opt in self.options if "option_id" in opt]
        if self.chosen not in option_ids:
            raise ValueError(f"chosen option '{self.chosen}' not found in options")
        return self


class Gate(BaseModel):
    """Stage-gate review (TRL, CRL, L2-C, Annual, Moving Target). Append-only."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    project_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    level: GateLevel
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    status: GateStatus
    signed_by: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    snapshot_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    decision_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    prov_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    created_at: str | None = None
    updated_at: str | None = None


class KPI(BaseModel):
    """Key Performance Indicator (Output, Outcome, Value 3-tier)."""

    model_config = ConfigDict(extra="forbid")

    kpi_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    project_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    task_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    tier: KPITier
    metric: str = Field(..., min_length=1, max_length=256)
    unit: str | None = Field(None, max_length=50)
    target: float | None = None
    actual: float | None = None
    measured_at: str | None = None
    baseline: float | None = None
    frequency: str | None = None
    owner_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    created_at: str | None = None
    updated_at: str | None = None


class Artifact(BaseModel):
    """Deliverable (document, code, data, report, etc.)."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    type: ArtifactType
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = Field(None, max_length=1024)
    uri: str = Field(..., description="Storage URI")
    hash: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")  # SHA256
    version: str | None = None
    created_by_task_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    created_by_person_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    security_tier: SecurityTier | None = None
    status: ArtifactStatusExtended | None = None
    related_ip_ids: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Risk(BaseModel):
    """Risk register entry."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    project_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    task_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    category: RiskCategory
    description: str = Field(..., min_length=1, max_length=2048)
    impact: str | None = Field(None, max_length=1024)
    likelihood: Likelihood | None = None
    risk_score: float | None = Field(None, ge=0, le=100)
    mitigation: str | None = Field(None, max_length=1024)
    contingency: str | None = Field(None, max_length=1024)
    owner_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    status: str | None = None
    blocker_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    created_at: str | None = None
    updated_at: str | None = None


class IP(BaseModel):
    """Intellectual Property record (patent, copyright, trademark, etc.)."""

    model_config = ConfigDict(extra="forbid")

    ip_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    project_id: str | None = Field(None, pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    type: IPType
    title: str = Field(..., min_length=1, max_length=512)
    description: str | None = Field(None, max_length=2048)
    status: IPStatus
    filing_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    publication_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    grant_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    filing_number: str | None = None
    registration_number: str | None = None
    jurisdiction: list[str] = Field(default_factory=list)
    inventors: list[str] = Field(default_factory=list)
    related_artifact_ids: list[str] = Field(default_factory=list)
    notes: str | None = Field(None, max_length=2048)
    created_at: str | None = None
    updated_at: str | None = None
