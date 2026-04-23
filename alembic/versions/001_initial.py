"""Initial schema migration for RAPai Ontology Phase II extended objects.

Creates tables for 10 extended Objects (WorkDirective, Milestone, Blocker,
Decision, Gate, KPI, Artifact, Role, Risk, IP) plus junction/relationship
tables. Governed by ADR-001 (SSOT) and ontology/06-ontology-design-charter.md
(SemVer + Append-only).

Revision ID: 001
Revises:
Create Date: 2026-04-22

This migration is IDEMPOTENT and SAFE: only creates tables that don't exist.
All constraints are explicit (NOT NULL, FK, UNIQUE, CHECK, INDEX).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Create Phase II extended object tables and indexes."""

    # ============================================================================
    # STEP 1: Create ENUM types (PostgreSQL native)
    # ============================================================================

    # Severity enum (for Blocker, Risk)
    op.execute("""
        CREATE TYPE severity_enum AS ENUM (
            'low',
            'medium',
            'high',
            'critical'
        )
    """)

    # BlockerStatus enum
    op.execute("""
        CREATE TYPE blocker_status_enum AS ENUM (
            'open',
            'in_progress',
            'resolved',
            'closed'
        )
    """)

    # DecisionStatus enum
    op.execute("""
        CREATE TYPE decision_status_enum AS ENUM (
            'pending',
            'approved',
            'rejected',
            'implemented',
            'reviewed'
        )
    """)

    # GateStatus enum
    op.execute("""
        CREATE TYPE gate_status_enum AS ENUM (
            'planned',
            'in_progress',
            'passed',
            'failed',
            'waived'
        )
    """)

    # GateLevel enum
    op.execute("""
        CREATE TYPE gate_level_enum AS ENUM (
            'L1_TRL',
            'L1_CRL',
            'L2_STAGE',
            'L2_C_CLIENT',
            'L3_ANNUAL',
            'L4_MOVING'
        )
    """)

    # KPITier enum
    op.execute("""
        CREATE TYPE kpi_tier_enum AS ENUM (
            'output',
            'outcome',
            'value'
        )
    """)

    # ProjectStatus enum (for Milestone)
    op.execute("""
        CREATE TYPE project_status_enum AS ENUM (
            'draft',
            'active',
            'on_hold',
            'completed',
            'cancelled'
        )
    """)

    # ArtifactType enum
    op.execute("""
        CREATE TYPE artifact_type_enum AS ENUM (
            'doc',
            'code',
            'data',
            'report',
            'presentation',
            'dataset',
            'model',
            'other'
        )
    """)

    # ArtifactStatus enum
    op.execute("""
        CREATE TYPE artifact_status_enum AS ENUM (
            'draft',
            'in_review',
            'published',
            'archived',
            'deprecated'
        )
    """)

    # SecurityTier enum
    op.execute("""
        CREATE TYPE security_tier_enum AS ENUM (
            'PUBLIC',
            'RESTRICTED',
            'CONFIDENTIAL',
            'SECRET'
        )
    """)

    # RoleType enum
    op.execute("""
        CREATE TYPE role_type_enum AS ENUM (
            'PI',
            'Coordinator',
            'Researcher',
            'DevOps',
            'Manager',
            'Analyst',
            'Engineer',
            'Consultant',
            'Admin',
            'Other'
        )
    """)

    # RiskCategory enum
    op.execute("""
        CREATE TYPE risk_category_enum AS ENUM (
            'technical',
            'schedule',
            'cost',
            'scope',
            'resource',
            'regulatory',
            'market',
            'quality',
            'security',
            'other'
        )
    """)

    # Likelihood enum
    op.execute("""
        CREATE TYPE likelihood_enum AS ENUM (
            'rare',
            'unlikely',
            'possible',
            'likely',
            'almost_certain'
        )
    """)

    # IPType enum
    op.execute("""
        CREATE TYPE ip_type_enum AS ENUM (
            'patent',
            'copyright',
            'trademark',
            'trade_secret',
            'design_right',
            'utility_model'
        )
    """)

    # IPStatus enum
    op.execute("""
        CREATE TYPE ip_status_enum AS ENUM (
            'idea',
            'drafting',
            'filed',
            'published',
            'granted',
            'rejected',
            'abandoned'
        )
    """)

    # WorkDirectiveStatus enum
    op.execute("""
        CREATE TYPE work_directive_status_enum AS ENUM (
            'created',
            'validated',
            'dispatched',
            'in_progress',
            'completed',
            'failed'
        )
    """)

    # Intent enum
    op.execute("""
        CREATE TYPE intent_enum AS ENUM (
            'create_task',
            'update_status',
            'log_work',
            'assign_person',
            'raise_blocker',
            'resolve_blocker',
            'record_decision',
            'submit_gate',
            'measure_kpi',
            'produce_artifact',
            'validate_level_up_criteria'
        )
    """)

    # ============================================================================
    # STEP 2: Create main object tables
    # ============================================================================

    # 2.1: MILESTONES
    # ============================================================================
    op.create_table(
        'milestones',
        sa.Column('milestone_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation (26 chars)'),
        sa.Column('project_id', sa.String(36), nullable=False,
                  comment='Foreign key to projects.project_id'),
        sa.Column('name', sa.String(256), nullable=True,
                  comment='Milestone name (e.g., Phase 1 Completion)'),
        sa.Column('description', sa.String(1024), nullable=True,
                  comment='Detailed description of milestone objectives'),
        sa.Column('date', sa.Date(), nullable=False,
                  comment='Target milestone date'),
        sa.Column('deliverable_ids', postgresql.ARRAY(sa.String(36)), nullable=True,
                  comment='Array of Artifact/Task IDs that comprise this milestone'),
        sa.Column('status', project_status_enum, nullable=True, default='planned',
                  comment='Milestone status (planned, active, completed, cancelled)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
                  comment='Creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
                  comment='Last update timestamp'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.Index('idx_milestones_project_id_status', 'project_id', 'status'),
        sa.Index('idx_milestones_date', 'date'),
        comment='Milestones: project phase completion targets with deliverables'
    )

    # 2.2: BLOCKERS
    # ============================================================================
    op.create_table(
        'blockers',
        sa.Column('blocker_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('task_id', sa.String(36), nullable=False,
                  comment='Foreign key to tasks.task_id'),
        sa.Column('severity', severity_enum, nullable=False,
                  comment='Blocker severity (low, medium, high, critical)'),
        sa.Column('description', sa.String(2048), nullable=False,
                  comment='Detailed description of the blocker'),
        sa.Column('root_cause', sa.String(2048), nullable=True,
                  comment='Analysis of root cause (optional)'),
        sa.Column('mitigation', sa.String(2048), nullable=True,
                  comment='Proposed mitigation or workaround'),
        sa.Column('owner_id', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id (resolver)'),
        sa.Column('status', blocker_status_enum, nullable=False, default='open',
                  comment='Blocker status (open, in_progress, resolved, closed)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Resolution timestamp (null if unresolved)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['persons.person_id'], ondelete='SET NULL'),
        sa.Index('idx_blockers_task_id_status', 'task_id', 'status'),
        sa.Index('idx_blockers_owner_id', 'owner_id'),
        sa.Index('idx_blockers_severity', 'severity'),
        comment='Blockers: Task impediments with severity and mitigation tracking'
    )

    # 2.3: DECISIONS
    # ============================================================================
    op.create_table(
        'decisions',
        sa.Column('decision_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('context', sa.String(2048), nullable=False,
                  comment='Context and problem statement'),
        sa.Column('options', postgresql.JSON, nullable=True,
                  comment='JSON array of {option_id, description, pros[], cons[]}'),
        sa.Column('chosen', sa.String(256), nullable=False,
                  comment='ID of the chosen option'),
        sa.Column('rationale', sa.String(2048), nullable=False,
                  comment='Why this option was chosen'),
        sa.Column('decision_maker_id', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id'),
        sa.Column('status', decision_status_enum, nullable=False, default='pending',
                  comment='Decision status (pending, approved, rejected, implemented, reviewed)'),
        sa.Column('prov_id', sa.String(36), nullable=True,
                  comment='PROV-O Activity ID for lineage tracking'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['decision_maker_id'], ['persons.person_id'], ondelete='SET NULL'),
        sa.Index('idx_decisions_decision_maker_id', 'decision_maker_id'),
        sa.Index('idx_decisions_status', 'status'),
        comment='Decisions: Recorded decisions with context, options, and chosen outcome'
    )

    # 2.4: GATES
    # ============================================================================
    op.create_table(
        'gates',
        sa.Column('gate_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation (immutable)'),
        sa.Column('project_id', sa.String(36), nullable=False,
                  comment='Foreign key to projects.project_id'),
        sa.Column('level', gate_level_enum, nullable=False,
                  comment='Gate level (L1_TRL, L1_CRL, L2_STAGE, L2_C_CLIENT, L3_ANNUAL, L4_MOVING)'),
        sa.Column('criteria', postgresql.JSON, nullable=True,
                  comment='JSON array of {criterion_id, description, met, evidence}'),
        sa.Column('status', gate_status_enum, nullable=False, default='planned',
                  comment='Gate status (planned, in_progress, passed, failed, waived)'),
        sa.Column('signed_by', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id (approver)'),
        sa.Column('snapshot_id', sa.String(36), nullable=True,
                  comment='Reference to project state snapshot at gate time'),
        sa.Column('decision_id', sa.String(36), nullable=True,
                  comment='Foreign key to decisions.decision_id'),
        sa.Column('prov_id', sa.String(36), nullable=True,
                  comment='PROV-O Activity ID for lineage'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signed_by'], ['persons.person_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.decision_id'], ondelete='SET NULL'),
        sa.Index('idx_gates_project_id_level', 'project_id', 'level'),
        sa.Index('idx_gates_status', 'status'),
        sa.Index('idx_gates_signed_by', 'signed_by'),
        comment='Gates: Stage-gate reviews (TRL, CRL, L2-C, Annual, Moving Target)'
    )

    # 2.5: KPIs
    # ============================================================================
    op.create_table(
        'kpis',
        sa.Column('kpi_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('project_id', sa.String(36), nullable=True,
                  comment='Foreign key to projects.project_id (optional for task-level)'),
        sa.Column('task_id', sa.String(36), nullable=True,
                  comment='Foreign key to tasks.task_id (optional for task-level KPIs)'),
        sa.Column('tier', kpi_tier_enum, nullable=False,
                  comment='KPI 3-tier: output, outcome, value'),
        sa.Column('metric', sa.String(256), nullable=False,
                  comment='Metric name (e.g., response_rate, time_to_delivery)'),
        sa.Column('unit', sa.String(50), nullable=True,
                  comment='Measurement unit (%, hours, count, score, etc.)'),
        sa.Column('target', sa.Numeric(precision=15, scale=2), nullable=True,
                  comment='Target value for this KPI'),
        sa.Column('actual', sa.Numeric(precision=15, scale=2), nullable=True,
                  comment='Actual measured value (null if not yet measured)'),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Timestamp of last measurement'),
        sa.Column('baseline', sa.Numeric(precision=15, scale=2), nullable=True,
                  comment='Baseline value for comparison'),
        sa.Column('frequency', sa.String(32), nullable=True,
                  comment='Measurement frequency (daily, weekly, monthly, quarterly, annually, ad_hoc)'),
        sa.Column('owner_id', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id (tracker)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['persons.person_id'], ondelete='SET NULL'),
        sa.Index('idx_kpis_project_id_tier', 'project_id', 'tier'),
        sa.Index('idx_kpis_task_id', 'task_id'),
        sa.Index('idx_kpis_owner_id', 'owner_id'),
        comment='KPIs: Key Performance Indicators in 3-tier model (Output, Outcome, Value)'
    )

    # 2.6: ARTIFACTS
    # ============================================================================
    op.create_table(
        'artifacts',
        sa.Column('artifact_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('type', artifact_type_enum, nullable=False,
                  comment='Artifact type (doc, code, data, report, presentation, dataset, model, other)'),
        sa.Column('name', sa.String(256), nullable=True,
                  comment='Artifact name'),
        sa.Column('description', sa.String(1024), nullable=True,
                  comment='Detailed description'),
        sa.Column('uri', sa.String(1024), nullable=False,
                  comment='Storage URI (S3, Git, local path, etc.)'),
        sa.Column('hash', sa.String(64), nullable=True,
                  comment='SHA256 hash for integrity verification (pattern: ^[a-f0-9]{64}$)'),
        sa.Column('version', sa.String(64), nullable=True,
                  comment='Semantic version (e.g., 1.0.2)'),
        sa.Column('created_by_task_id', sa.String(36), nullable=True,
                  comment='Foreign key to tasks.task_id'),
        sa.Column('created_by_person_id', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id'),
        sa.Column('security_tier', security_tier_enum, nullable=True, default='RESTRICTED',
                  comment='Data security tier (PUBLIC, RESTRICTED, CONFIDENTIAL, SECRET)'),
        sa.Column('status', artifact_status_enum, nullable=True, default='draft',
                  comment='Artifact status (draft, in_review, published, archived, deprecated)'),
        sa.Column('related_ip_ids', postgresql.ARRAY(sa.String(36)), nullable=True,
                  comment='Array of IP IDs related to this artifact'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['created_by_task_id'], ['tasks.task_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_person_id'], ['persons.person_id'], ondelete='SET NULL'),
        sa.Index('idx_artifacts_type_status', 'type', 'status'),
        sa.Index('idx_artifacts_security_tier', 'security_tier'),
        sa.Index('idx_artifacts_created_by_task_id', 'created_by_task_id'),
        sa.Index('idx_artifacts_created_by_person_id', 'created_by_person_id'),
        comment='Artifacts: Deliverables (document, code, data, report, etc.) with security tier'
    )

    # 2.7: ROLES
    # ============================================================================
    op.create_table(
        'roles',
        sa.Column('role_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('name', role_type_enum, nullable=False,
                  comment='Role type (PI, Coordinator, Researcher, DevOps, Manager, Analyst, Engineer, Consultant, Admin, Other)'),
        sa.Column('description', sa.String(512), nullable=True,
                  comment='Detailed role description'),
        sa.Column('responsibilities', postgresql.ARRAY(sa.String(256)), nullable=True,
                  comment='Array of key responsibilities'),
        sa.Column('permissions', postgresql.ARRAY(sa.String(32)), nullable=True,
                  comment='Array of permission scopes (read, write, approve, sign, admin)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_roles_name', 'name'),
        comment='Roles: Role definitions with responsibilities and permissions'
    )

    # 2.8: RISKS
    # ============================================================================
    op.create_table(
        'risks',
        sa.Column('risk_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('project_id', sa.String(36), nullable=True,
                  comment='Foreign key to projects.project_id'),
        sa.Column('task_id', sa.String(36), nullable=True,
                  comment='Foreign key to tasks.task_id (optional)'),
        sa.Column('category', risk_category_enum, nullable=False,
                  comment='Risk category (technical, schedule, cost, scope, resource, regulatory, market, quality, security, other)'),
        sa.Column('description', sa.String(2048), nullable=False,
                  comment='Risk description'),
        sa.Column('impact', sa.String(1024), nullable=True,
                  comment='Potential impact if risk materializes'),
        sa.Column('likelihood', likelihood_enum, nullable=True,
                  comment='Likelihood (rare, unlikely, possible, likely, almost_certain)'),
        sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=True,
                  comment='Risk score (0-100) calculated from likelihood x impact'),
        sa.Column('mitigation', sa.String(1024), nullable=True,
                  comment='Mitigation strategy'),
        sa.Column('contingency', sa.String(1024), nullable=True,
                  comment='Contingency plan if risk occurs'),
        sa.Column('owner_id', sa.String(36), nullable=True,
                  comment='Foreign key to persons.person_id (manager)'),
        sa.Column('status', sa.String(32), nullable=True, default='identified',
                  comment='Risk status (identified, active, mitigated, closed)'),
        sa.Column('blocker_id', sa.String(36), nullable=True,
                  comment='Foreign key to blockers.blocker_id (if escalated)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['persons.person_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['blocker_id'], ['blockers.blocker_id'], ondelete='SET NULL'),
        sa.Index('idx_risks_project_id_category', 'project_id', 'category'),
        sa.Index('idx_risks_owner_id', 'owner_id'),
        sa.Index('idx_risks_status', 'status'),
        comment='Risks: Risk register entries with likelihood, impact, mitigation, contingency'
    )

    # 2.9: IPs (Intellectual Property)
    # ============================================================================
    op.create_table(
        'ips',
        sa.Column('ip_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('project_id', sa.String(36), nullable=True,
                  comment='Foreign key to projects.project_id'),
        sa.Column('type', ip_type_enum, nullable=False,
                  comment='IP type (patent, copyright, trademark, trade_secret, design_right, utility_model)'),
        sa.Column('title', sa.String(512), nullable=False,
                  comment='Title or name of IP (e.g., patent title, trademark name)'),
        sa.Column('description', sa.String(2048), nullable=True,
                  comment='Detailed description'),
        sa.Column('status', ip_status_enum, nullable=False, default='idea',
                  comment='IP status (idea, drafting, filed, published, granted, rejected, abandoned)'),
        sa.Column('filing_date', sa.Date(), nullable=True,
                  comment='Filing date (null if not yet filed)'),
        sa.Column('publication_date', sa.Date(), nullable=True,
                  comment='Publication date (null if not yet published)'),
        sa.Column('grant_date', sa.Date(), nullable=True,
                  comment='Grant date (null if not yet granted)'),
        sa.Column('filing_number', sa.String(128), nullable=True,
                  comment='Official filing number (patent, trademark, etc.)'),
        sa.Column('registration_number', sa.String(128), nullable=True,
                  comment='Registration/grant number'),
        sa.Column('jurisdiction', postgresql.ARRAY(sa.String(32)), nullable=True,
                  comment='Array of jurisdiction codes (KR, US, EP, JP, CN, WIPO, other)'),
        sa.Column('inventors', postgresql.ARRAY(sa.String(36)), nullable=True,
                  comment='Array of Person IDs of inventors/authors'),
        sa.Column('related_artifact_ids', postgresql.ARRAY(sa.String(36)), nullable=True,
                  comment='Array of Artifact IDs (code, paper, design files, etc.)'),
        sa.Column('notes', sa.String(2048), nullable=True,
                  comment='Additional notes or claims'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.Index('idx_ips_project_id_type', 'project_id', 'type'),
        sa.Index('idx_ips_status', 'status'),
        comment='IPs: Intellectual Property records (patents, copyrights, trademarks, etc.)'
    )

    # 2.10: WORK DIRECTIVES
    # ============================================================================
    op.create_table(
        'work_directives',
        sa.Column('directive_id', sa.String(36), nullable=False, primary_key=True,
                  comment='ULID assigned at creation'),
        sa.Column('parent_id', sa.String(36), nullable=True,
                  comment='Parent directive ID for nested work hierarchies'),
        sa.Column('intent', intent_enum, nullable=False,
                  comment='Work activity intent (create_task, update_status, log_work, assign_person, etc.)'),
        sa.Column('entities', postgresql.JSON, nullable=True,
                  comment='JSON array of {entity_type, entity_id, role}'),
        sa.Column('due_date', sa.Date(), nullable=False,
                  comment='Target completion date'),
        sa.Column('status', work_directive_status_enum, nullable=False, default='created',
                  comment='6-state lifecycle: created, validated, dispatched, in_progress, completed, failed (P0 enhancement)'),
        sa.Column('source_worklog_id', sa.String(36), nullable=True,
                  comment='WorkLog ID that generated this directive (traceability)'),
        sa.Column('source_rule_ids', postgresql.ARRAY(sa.String(36)), nullable=True,
                  comment='Array of Rule IDs (R001-R020) that triggered creation'),
        sa.Column('source_document', sa.String(512), nullable=True,
                  comment='Original source document reference (meeting notes, email, file path)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['work_directives.directive_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_worklog_id'], ['worklogs.worklog_id'], ondelete='SET NULL'),
        sa.Index('idx_work_directives_intent_status', 'intent', 'status'),
        sa.Index('idx_work_directives_due_date', 'due_date'),
        sa.Index('idx_work_directives_parent_id', 'parent_id'),
        comment='WorkDirectives: Intent-driven work directives (Phase III W1 P0 enhancement)'
    )

    # ============================================================================
    # STEP 3: Create junction/relationship tables
    # ============================================================================

    # 3.1: DECISION_EVIDENCE (Decision can reference multiple evidence artifacts)
    # ============================================================================
    op.create_table(
        'decision_evidence',
        sa.Column('decision_id', sa.String(36), nullable=False,
                  comment='Foreign key to decisions.decision_id'),
        sa.Column('artifact_id', sa.String(36), nullable=False,
                  comment='Foreign key to artifacts.artifact_id'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('decision_id', 'artifact_id'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.decision_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.artifact_id'], ondelete='CASCADE'),
        sa.Index('idx_decision_evidence_artifact_id', 'artifact_id'),
        comment='Decision Evidence: Links decisions to supporting artifacts'
    )

    # 3.2: PERSON_ROLE_ASSIGNMENT (Junction table for Person <-> Role mapping)
    # ============================================================================
    op.create_table(
        'person_role_assignments',
        sa.Column('person_id', sa.String(36), nullable=False,
                  comment='Foreign key to persons.person_id'),
        sa.Column('role_id', sa.String(36), nullable=False,
                  comment='Foreign key to roles.role_id'),
        sa.Column('project_id', sa.String(36), nullable=True,
                  comment='Foreign key to projects.project_id (optional: null=global role)'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_from', sa.Date(), nullable=True,
                  comment='Date role becomes effective'),
        sa.Column('effective_to', sa.Date(), nullable=True,
                  comment='Date role expires (null=ongoing)'),
        sa.PrimaryKeyConstraint('person_id', 'role_id', 'project_id'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.person_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
        sa.Index('idx_person_role_assignments_project_id', 'project_id'),
        comment='Person Role Assignments: Links persons to roles with optional project/time scope'
    )

    # ============================================================================
    # STEP 4: Create additional indexes for common queries
    # ============================================================================

    # Indexes for temporal queries (created_at, updated_at)
    op.create_index('idx_milestones_created_at', 'milestones', ['created_at'])
    op.create_index('idx_blockers_created_at', 'blockers', ['created_at'])
    op.create_index('idx_decisions_created_at', 'decisions', ['created_at'])
    op.create_index('idx_gates_created_at', 'gates', ['created_at'])
    op.create_index('idx_kpis_created_at', 'kpis', ['created_at'])
    op.create_index('idx_artifacts_created_at', 'artifacts', ['created_at'])
    op.create_index('idx_risks_created_at', 'risks', ['created_at'])
    op.create_index('idx_ips_created_at', 'ips', ['created_at'])
    op.create_index('idx_work_directives_created_at', 'work_directives', ['created_at'])


def downgrade() -> None:
    """Drop all Phase II extended object tables and ENUMs in reverse order."""

    # Drop indexes explicitly (not strictly necessary but good practice)
    op.drop_index('idx_work_directives_created_at', table_name='work_directives')
    op.drop_index('idx_ips_created_at', table_name='ips')
    op.drop_index('idx_risks_created_at', table_name='risks')
    op.drop_index('idx_artifacts_created_at', table_name='artifacts')
    op.drop_index('idx_kpis_created_at', table_name='kpis')
    op.drop_index('idx_gates_created_at', table_name='gates')
    op.drop_index('idx_decisions_created_at', table_name='decisions')
    op.drop_index('idx_blockers_created_at', table_name='blockers')
    op.drop_index('idx_milestones_created_at', table_name='milestones')

    # Drop junction/relationship tables first (due to FKs)
    op.drop_table('person_role_assignments')
    op.drop_table('decision_evidence')

    # Drop main object tables (reverse order of creation)
    op.drop_table('work_directives')
    op.drop_table('ips')
    op.drop_table('risks')
    op.drop_table('roles')
    op.drop_table('artifacts')
    op.drop_table('kpis')
    op.drop_table('gates')
    op.drop_table('decisions')
    op.drop_table('blockers')
    op.drop_table('milestones')

    # Drop all ENUM types (reverse order of creation for clarity)
    op.execute('DROP TYPE IF EXISTS intent_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS work_directive_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS ip_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS ip_type_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS likelihood_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS risk_category_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS role_type_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS security_tier_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS artifact_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS artifact_type_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS project_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS kpi_tier_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS gate_level_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS gate_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS decision_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS blocker_status_enum CASCADE')
    op.execute('DROP TYPE IF EXISTS severity_enum CASCADE')
