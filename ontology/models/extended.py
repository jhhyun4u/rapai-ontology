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

    @model_validator(mode="after")
    def validate_unique_responsibilities(self) -> Role:
        """Responsibilities must be unique (no duplicates)."""
        if len(self.responsibilities) != len(set(self.responsibilities)):
            raise ValueError("responsibilities must be unique (no duplicates)")
        return self

    @model_validator(mode="after")
    def validate_valid_permissions(self) -> Role:
        """Permissions must be from allowed set."""
        valid_perms = {"read", "write", "approve", "sign", "admin"}
        for perm in self.permissions:
            if perm not in valid_perms:
                raise ValueError(f"permission '{perm}' not in {valid_perms}")
        return self


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

    @model_validator(mode="after")
    def validate_deliverables_not_self_referencing(self) -> Milestone:
        """Deliverables must not reference the milestone itself."""
        if self.milestone_id in self.deliverable_ids:
            raise ValueError("deliverable_ids cannot include milestone_id")
        return self

    @model_validator(mode="after")
    def validate_unique_deliverables(self) -> Milestone:
        """Deliverable list must not have duplicates."""
        if len(self.deliverable_ids) != len(set(self.deliverable_ids)):
            raise ValueError("deliverable_ids must be unique (no duplicates)")
        return self


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

    @model_validator(mode="after")
    def validate_blocker_not_self_blocking(self) -> Blocker:
        """Blocker must not reference itself as the task."""
        if self.blocker_id == self.task_id:
            raise ValueError("blocker cannot block itself (blocker_id must differ from task_id)")
        return self

    @model_validator(mode="after")
    def validate_resolution_consistency(self) -> Blocker:
        """If resolved_at is set, status must be 'resolved' or 'closed'."""
        if self.resolved_at and self.status not in (BlockerStatus.RESOLVED, BlockerStatus.CLOSED):
            raise ValueError(
                f"resolved_at is set, but status is '{self.status}' "
                f"(must be 'resolved' or 'closed')"
            )
        return self


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

    @model_validator(mode="after")
    def validate_gate_approval_consistency(self) -> Gate:
        """If gate passed/failed, signed_by must be present."""
        if self.status in (GateStatus.PASSED, GateStatus.FAILED) and not self.signed_by:
            raise ValueError(
                f"gate status is '{self.status}', but signed_by is missing "
                "(required for passed/failed gates)"
            )
        return self

    @model_validator(mode="after")
    def validate_criteria_for_decision_gates(self) -> Gate:
        """Reviewed gates should have criteria with evidence."""
        if self.status in (GateStatus.PASSED, GateStatus.FAILED):
            if not self.criteria:
                raise ValueError(
                    f"gate status is '{self.status}', but criteria list is empty "
                    "(should have at least one criterion)"
                )
        return self


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

    @model_validator(mode="after")
    def validate_parent_reference(self) -> KPI:
        """KPI must reference either project_id or task_id (not both absent)."""
        if not self.project_id and not self.task_id:
            raise ValueError("KPI must reference either project_id or task_id (cannot be both absent)")
        return self

    @model_validator(mode="after")
    def validate_baseline_vs_target(self) -> KPI:
        """If both baseline and target are set, baseline should not exceed target."""
        if self.baseline is not None and self.target is not None:
            if self.baseline > self.target:
                raise ValueError(
                    f"baseline ({self.baseline}) cannot exceed target ({self.target})"
                )
        return self

    @model_validator(mode="after")
    def validate_measurement_coherence(self) -> KPI:
        """If actual is recorded, measured_at should be set."""
        if self.actual is not None and not self.measured_at:
            raise ValueError(
                "actual measurement is set, but measured_at timestamp is missing"
            )
        return self


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

    @model_validator(mode="after")
    def validate_creator_reference(self) -> Artifact:
        """Artifact must have either created_by_task_id or created_by_person_id."""
        if not self.created_by_task_id and not self.created_by_person_id:
            raise ValueError(
                "artifact must have either created_by_task_id or created_by_person_id"
            )
        return self

    @model_validator(mode="after")
    def validate_uri_format(self) -> Artifact:
        """URI must be non-empty and follow basic URI format."""
        if not self.uri or not self.uri.strip():
            raise ValueError("uri cannot be empty")
        if "://" not in self.uri and not self.uri.startswith("/"):
            raise ValueError(f"uri '{self.uri}' must be a valid path or full URI")
        return self

    @model_validator(mode="after")
    def validate_no_self_reference_in_related_ip(self) -> Artifact:
        """Related IP list must not reference the artifact itself."""
        if self.artifact_id in self.related_ip_ids:
            raise ValueError("related_ip_ids cannot include artifact_id")
        return self


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

    @model_validator(mode="after")
    def validate_parent_reference(self) -> Risk:
        """Risk must reference either project_id or task_id (not both absent)."""
        if not self.project_id and not self.task_id:
            raise ValueError("risk must reference either project_id or task_id (cannot be both absent)")
        return self

    @model_validator(mode="after")
    def validate_high_risk_has_mitigation(self) -> Risk:
        """High risk (score >= 70) should have mitigation and contingency plans."""
        if self.risk_score is not None and self.risk_score >= 70:
            if not self.mitigation:
                raise ValueError(
                    f"risk_score is {self.risk_score} (high risk), but mitigation plan is missing"
                )
            if not self.contingency:
                raise ValueError(
                    f"risk_score is {self.risk_score} (high risk), but contingency plan is missing"
                )
        return self

    @model_validator(mode="after")
    def validate_risk_not_self_blocking(self) -> Risk:
        """Risk must not reference itself as blocker (if blocker_id is set)."""
        if self.blocker_id and self.blocker_id == self.risk_id:
            raise ValueError("risk cannot reference itself as a blocker")
        return self


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

    @model_validator(mode="after")
    def validate_date_sequence(self) -> IP:
        """Date sequence must be logical: filing ≤ publication ≤ grant."""
        dates = {
            "filing_date": self.filing_date,
            "publication_date": self.publication_date,
            "grant_date": self.grant_date,
        }
        date_values = [d for d in dates.values() if d]
        if len(date_values) > 1:
            date_values.sort()
            if dates["filing_date"] and dates["publication_date"]:
                if dates["filing_date"] > dates["publication_date"]:
                    raise ValueError("filing_date must be ≤ publication_date")
            if dates["publication_date"] and dates["grant_date"]:
                if dates["publication_date"] > dates["grant_date"]:
                    raise ValueError("publication_date must be ≤ grant_date")
            if dates["filing_date"] and dates["grant_date"]:
                if dates["filing_date"] > dates["grant_date"]:
                    raise ValueError("filing_date must be ≤ grant_date")
        return self

    @model_validator(mode="after")
    def validate_unique_inventors(self) -> IP:
        """Inventors list must not have duplicates."""
        if len(self.inventors) != len(set(self.inventors)):
            raise ValueError("inventors must be unique (no duplicates)")
        return self

    @model_validator(mode="after")
    def validate_no_self_reference_in_artifacts(self) -> IP:
        """Related artifacts must not reference the IP record itself."""
        if self.ip_id in self.related_artifact_ids:
            raise ValueError("related_artifact_ids cannot include ip_id")
        return self
