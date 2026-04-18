"""Enumerations mirroring ``ontology/schemas/enums.json``.

Every enum value MUST match the JSON Schema definition exactly; roundtrip tests
enforce equivalence. To extend (add a new value) bump ``x-ontology-version`` in
both the JSON Schema and this module, and update the governance log per
``ontology/06-ontology-design-charter.md``.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrEnum(str, Enum):
    """Backport-compatible string enum (``enum.StrEnum`` is 3.11+ only)."""

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


# ── Primary axis 1 ────────────────────────────────────────────────────────
class ProjectTypeCode(StrEnum):
    """WBS primary type (Axis 1, v2.0) — 8 codes A~H."""

    A = "A"  # Exploratory
    B = "B"  # Developmental
    C = "C"  # Commercialization
    D = "D"  # Investigative
    E = "E"  # Strategic Planning
    F = "F"  # Advisory
    G = "G"  # Hybrid
    H = "H"  # Event Operations


# ── Axis 2 cross-cutting ──────────────────────────────────────────────────
class ContractModality(StrEnum):
    INTERNAL_RD = "internal_rd"
    PUBLIC_GRANT = "public_grant"
    CONTRACT_RESEARCH = "contract_research"


class FundingSource(StrEnum):
    GOVERNMENT_NATIONAL = "government_national"
    PRIVATE_COMMISSIONED = "private_commissioned"
    SELF_INVESTMENT = "self_investment"
    MIXED = "mixed"


class SecurityTier(StrEnum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"

    @property
    def rank(self) -> int:
        """Monotonic rank (PUBLIC=0 ... SECRET=3). Used for ABAC comparisons."""
        return {"PUBLIC": 0, "RESTRICTED": 1, "CONFIDENTIAL": 2, "SECRET": 3}[self.value]


class ScaleTier(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# ── Governance / Gate ─────────────────────────────────────────────────────
class GateLevel(StrEnum):
    L1_TRL = "L1_TRL"
    L1_CRL = "L1_CRL"
    L2_STAGE = "L2_STAGE"
    L2_C_CLIENT = "L2_C_CLIENT"
    L3_ANNUAL = "L3_ANNUAL"
    L4_MOVING = "L4_MOVING"


class GateStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


class KPITier(StrEnum):
    OUTPUT = "output"
    OUTCOME = "outcome"
    VALUE = "value"


# ── Daily report 13 tags (v2.9) ───────────────────────────────────────────
class DailyReportTag(StrEnum):
    DONE = "DONE"
    ISSUE = "ISSUE"
    TRL_UP = "TRL_UP"
    CRL_UP = "CRL_UP"
    TIME = "TIME"
    COST = "COST"
    IP = "IP"
    ASSIGN = "ASSIGN"
    DELIVERABLE = "DELIVERABLE"
    EXPERIMENT = "EXPERIMENT"
    MGT = "MGT"
    DO = "DO"
    REV = "REV"


# ── Workflow status ───────────────────────────────────────────────────────
class TaskStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ── Work activity Intent (ontology/09) ──────────────────────────────────
class Intent(StrEnum):
    """Action intent for WorkDirective execution (10 + TRL/CRL)."""

    CREATE_TASK = "create_task"
    UPDATE_STATUS = "update_status"
    LOG_WORK = "log_work"
    ASSIGN_PERSON = "assign_person"
    RAISE_BLOCKER = "raise_blocker"
    RESOLVE_BLOCKER = "resolve_blocker"
    RECORD_DECISION = "record_decision"
    SUBMIT_GATE = "submit_gate"
    MEASURE_KPI = "measure_kpi"
    PRODUCE_ARTIFACT = "produce_artifact"
    VALIDATE_LEVEL_UP_CRITERIA = "validate_level_up_criteria"  # Phase III W2-W3: TRL/CRL


class ParsingIntent(StrEnum):
    """Natural language parsing intent extracted by LLM (10 + TRL/CRL).

    These intents represent the *meaning* of a WorkLog entry as interpreted by the parser.
    They map N:M to Action Intents (Intent) via `ontology/mapping/intent_mapper.py`.
    """

    COMPLETION = "completion"
    PROGRESS = "progress"
    PLAN = "plan"
    BLOCKER = "blocker"
    REQUEST = "request"
    DIRECTIVE = "directive"
    OBSERVATION = "observation"
    RISK_FLAG = "risk_flag"
    DECISION = "decision"
    QUERY = "query"
    # Phase III W2-W3 additions:
    LEVEL_UP_EVIDENCE = "level_up_evidence"  # Evidence that TRL/CRL criteria met
    LEVEL_UP_REQUEST = "level_up_request"  # Explicit request to level-up
    IMPLICIT_LEVEL_UP = "implicit_level_up"  # Implicit indication of level-up readiness


# ── Phase II enums (declared now so extended models can import) ───────────
class ArtifactType(StrEnum):
    DOC = "doc"
    CODE = "code"
    DATA = "data"
    REPORT = "report"
    PRESENTATION = "presentation"
    DATASET = "dataset"
    MODEL = "model"
    OTHER = "other"


class IPType(StrEnum):
    PATENT = "patent"
    COPYRIGHT = "copyright"
    TRADEMARK = "trademark"
    TRADE_SECRET = "trade_secret"
    DESIGN_RIGHT = "design_right"
    UTILITY_MODEL = "utility_model"


class IPStatus(StrEnum):
    IDEA = "idea"
    DRAFTING = "drafting"
    FILED = "filed"
    PUBLISHED = "published"
    GRANTED = "granted"
    REJECTED = "rejected"
    ABANDONED = "abandoned"


class RiskCategory(StrEnum):
    TECHNICAL = "technical"
    SCHEDULE = "schedule"
    COST = "cost"
    SCOPE = "scope"
    RESOURCE = "resource"
    REGULATORY = "regulatory"
    MARKET = "market"
    QUALITY = "quality"
    SECURITY = "security"
    OTHER = "other"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Likelihood(StrEnum):
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


# ── Extended Objects (Phase II) ────────────────────────────────────────────
class RoleType(StrEnum):
    """Role type (PI, Coordinator, Researcher, etc.)."""

    PI = "PI"
    COORDINATOR = "Coordinator"
    RESEARCHER = "Researcher"
    DEVOPS = "DevOps"
    MANAGER = "Manager"
    ANALYST = "Analyst"
    ENGINEER = "Engineer"
    CONSULTANT = "Consultant"
    ADMIN = "Admin"
    OTHER = "Other"


class BlockerStatus(StrEnum):
    """Blocker status lifecycle."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DecisionStatus(StrEnum):
    """Decision lifecycle status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    REVIEWED = "reviewed"


class ArtifactStatusExtended(StrEnum):
    """Artifact lifecycle status (extends ArtifactStatus for detailed phases)."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


# ── Cross-cutting attribute bundle ───────────────────────────────────────
class CrossCutting(BaseModel):
    """Axis 2 attributes attached to every Project.

    ``contract_modality == CONTRACT_RESEARCH`` activates the First-class
    academic research overlay (decision 22): L2-C Gate, 6-phase WBS addon,
    dedicated KPIs, AG weight upshift.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_modality: ContractModality
    funding_source: FundingSource
    security_tier: SecurityTier
    scale_tier: ScaleTier

    @property
    def is_contract_research(self) -> bool:
        """True when the contract_research overlay must be activated."""
        return self.contract_modality is ContractModality.CONTRACT_RESEARCH


# Strict type alias for CloudEvents spec version (Phase III use).
CloudEventsSpecVersion = Literal["1.0"]

# Re-export helper for validators and tests.
PROJECT_TYPES_REQUIRING_TRL: frozenset[ProjectTypeCode] = frozenset(
    {ProjectTypeCode.A, ProjectTypeCode.B}
)
PROJECT_TYPES_REQUIRING_CRL: frozenset[ProjectTypeCode] = frozenset({ProjectTypeCode.C})


# Placeholder for Field to keep ``pydantic`` import used in this module
# (enums don't depend on Field, but downstream generators may).
_unused_field = Field  # pragma: no cover
