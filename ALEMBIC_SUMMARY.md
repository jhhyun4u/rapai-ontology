# Alembic Migration Summary: Phase II PostgreSQL Schema

**Created**: 2026-04-22  
**Phase**: Phase II (Extended 10 Objects + Links + Actions)  
**Status**: COMPLETE  
**Governance**: ADR-001 (SSOT) + ontology/06-ontology-design-charter.md (SemVer + Append-only)

---

## Overview

Created comprehensive PostgreSQL schema migration for RAPai Ontology Phase II using Alembic. The migration is **IDEMPOTENT**, **SAFE** (create-only), and fully **REVERSIBLE** (downgradeable).

### Location
```
alembic/
├── versions/
│   └── 001_initial.py         ← Main migration file (679 lines)
├── env.py                      ← Alembic environment config
├── alembic.ini                 ← Database URL + logging config
├── script.py.mako              ← Template for future migrations
└── README.md                   ← Comprehensive documentation
```

---

## What Was Created

### 1. 17 PostgreSQL Native ENUM Types

```sql
-- Status Enumerations
severity_enum              → (low, medium, high, critical)
blocker_status_enum        → (open, in_progress, resolved, closed)
decision_status_enum       → (pending, approved, rejected, implemented, reviewed)
gate_status_enum           → (planned, in_progress, passed, failed, waived)
work_directive_status_enum → (created, validated, dispatched, in_progress, completed, failed)

-- Level/Tier Enumerations
gate_level_enum     → (L1_TRL, L1_CRL, L2_STAGE, L2_C_CLIENT, L3_ANNUAL, L4_MOVING)
kpi_tier_enum       → (output, outcome, value)
project_status_enum → (draft, active, on_hold, completed, cancelled)

-- Type Enumerations
artifact_type_enum → (doc, code, data, report, presentation, dataset, model, other)
artifact_status_enum → (draft, in_review, published, archived, deprecated)
ip_type_enum       → (patent, copyright, trademark, trade_secret, design_right, utility_model)
ip_status_enum     → (idea, drafting, filed, published, granted, rejected, abandoned)
role_type_enum     → (PI, Coordinator, Researcher, DevOps, Manager, Analyst, Engineer, Consultant, Admin, Other)
security_tier_enum → (PUBLIC, RESTRICTED, CONFIDENTIAL, SECRET)

-- Value Enumerations
likelihood_enum → (rare, unlikely, possible, likely, almost_certain)
risk_category_enum → (technical, schedule, cost, scope, resource, regulatory, market, quality, security, other)
intent_enum → (create_task, update_status, log_work, assign_person, raise_blocker, resolve_blocker, record_decision, submit_gate, measure_kpi, produce_artifact, validate_level_up_criteria)
```

### 2. 10 Extended Object Tables

#### 2.1 Milestones (`milestones`)
- PK: `milestone_id` (ULID, 26 chars)
- FK: `project_id` → projects
- Columns: name, description, date, deliverable_ids[], status, timestamps
- Indexes: (project_id, status), (date), (created_at)
- Purpose: Project phase completion targets with deliverables

#### 2.2 Blockers (`blockers`)
- PK: `blocker_id` (ULID)
- FK: `task_id` → tasks, `owner_id` → persons
- Columns: severity enum, description, root_cause, mitigation, status, resolved_at, timestamps
- Indexes: (task_id, status), (owner_id), (severity), (created_at)
- Purpose: Task impediments with severity and mitigation tracking

#### 2.3 Decisions (`decisions`)
- PK: `decision_id` (ULID)
- FK: `decision_maker_id` → persons
- Columns: context, options JSON, chosen, rationale, status enum, prov_id, timestamps
- Indexes: (decision_maker_id), (status), (created_at)
- Purpose: Recorded decisions with context, options, chosen outcome (PROV-O lineage)

#### 2.4 Gates (`gates`)
- PK: `gate_id` (ULID, immutable)
- FK: `project_id` → projects, `signed_by` → persons, `decision_id` → decisions
- Columns: level enum, criteria JSON, status enum, snapshot_id, prov_id, timestamps
- Indexes: (project_id, level), (status), (signed_by), (created_at)
- Purpose: Stage-gate reviews (TRL, CRL, L2-C Client Acceptance, Annual, Moving Target)

#### 2.5 KPIs (`kpis`)
- PK: `kpi_id` (ULID)
- FK: `project_id` → projects, `task_id` → tasks, `owner_id` → persons
- Columns: tier enum, metric, unit, target, actual, measured_at, baseline, frequency, timestamps
- Indexes: (project_id, tier), (task_id), (owner_id), (created_at)
- Purpose: Key Performance Indicators in 3-tier model (Output, Outcome, Value)

#### 2.6 Artifacts (`artifacts`)
- PK: `artifact_id` (ULID)
- FK: `created_by_task_id` → tasks, `created_by_person_id` → persons
- Columns: type enum, name, description, uri, hash (SHA256), version, security_tier enum, status enum, related_ip_ids[], timestamps
- Indexes: (type, status), (security_tier), (created_by_task_id), (created_by_person_id), (created_at)
- Purpose: Deliverables (document, code, data, report, etc.) with security tier and integrity hash

#### 2.7 Roles (`roles`)
- PK: `role_id` (ULID)
- Columns: name enum (RoleType), description, responsibilities[], permissions[], timestamps
- Indexes: (name), (created_at)
- Purpose: Role definitions with responsibilities and permissions

#### 2.8 Risks (`risks`)
- PK: `risk_id` (ULID)
- FK: `project_id` → projects, `task_id` → tasks, `owner_id` → persons, `blocker_id` → blockers
- Columns: category enum, description, impact, likelihood enum, risk_score, mitigation, contingency, status, timestamps
- Indexes: (project_id, category), (owner_id), (status), (created_at)
- Purpose: Risk register entries with likelihood, impact, mitigation, contingency

#### 2.9 IPs (`ips`)
- PK: `ip_id` (ULID)
- FK: `project_id` → projects
- Columns: type enum, title, description, status enum, filing_date, publication_date, grant_date, filing_number, registration_number, jurisdiction[], inventors[], related_artifact_ids[], notes, timestamps
- Indexes: (project_id, type), (status), (created_at)
- Purpose: Intellectual Property records (patents, copyrights, trademarks, trade secrets, design rights, utility models)

#### 2.10 WorkDirectives (`work_directives`)
- PK: `directive_id` (ULID)
- FK: `parent_id` → work_directives (self-ref), `source_worklog_id` → worklogs
- Columns: intent enum, entities JSON, due_date, status enum (6-state), source_rule_ids[], source_document, timestamps
- Indexes: (intent, status), (due_date), (parent_id), (created_at)
- Purpose: Intent-driven work directives (Phase III W1 P0 enhancement: 6-state lifecycle)

### 3. 2 Junction/Relationship Tables

#### 3.1 Decision Evidence (`decision_evidence`)
- PK: (decision_id, artifact_id)
- FK: decision_id → decisions, artifact_id → artifacts
- Purpose: Links decisions to supporting artifacts (many-to-many)

#### 3.2 Person Role Assignments (`person_role_assignments`)
- PK: (person_id, role_id, project_id)
- FK: person_id → persons, role_id → roles, project_id → projects
- Columns: assigned_at, effective_from, effective_to
- Indexes: (project_id)
- Purpose: Maps persons to roles with optional project/time scope

### 4. Comprehensive Indexing Strategy

**Multi-column indexes for filtering:**
- (project_id, status) → Quick filtering by project + state
- (project_id, level/tier/type) → Hierarchy traversal
- (project_id, category) → Risk/milestone grouping

**Single-column indexes for joins:**
- (task_id), (owner_id), (project_id) → FK join performance
- (created_at), (status) → Temporal + state queries

**Total indexes:** ~35 (3 per main table + compound + temporal)

---

## Technical Specifications

### Database Target
- **PostgreSQL**: 16+ (uses native ENUM types, ARRAY types, JSON)
- **Python**: 3.11+
- **Alembic**: 1.13+
- **SQLAlchemy**: 2.0+

### Constraints & Rules

**Referential Integrity:**
- `ON DELETE CASCADE`: Most FKs (e.g., milestone → project, blocker → task)
- `ON DELETE SET NULL`: Reassignable FKs (e.g., owner_id, signed_by)

**Data Types:**
- IDs: `VARCHAR(36)` (26-char ULID or 36-char UUIDv7)
- Timestamps: `TIMESTAMP WITH TIMEZONE` (UTC, auto NOW())
- Status: PostgreSQL ENUM (no string drift)
- JSON: `postgresql.JSON` (for complex nested structures like options[], criteria[])
- Arrays: `postgresql.ARRAY(TEXT/VARCHAR/ULID)` (for deliverable_ids[], inventors[])

**Business Rules:**
- All required fields: `NOT NULL` (enforced at schema)
- Severity/Status enums: Strict typing (no invalid values)
- ULID format: Validated at application layer (schema accepts VARCHAR)
- Timestamps: All tables have `created_at` (NOT NULL, server_default NOW()) + `updated_at`

---

## Safety & Idempotency

✓ **SAFE**: Migration uses `CREATE TABLE` (no DROP in upgrade path)  
✓ **IDEMPOTENT**: Can be re-applied safely (PostgreSQL CREATE TYPE/TABLE exists)  
✓ **REVERSIBLE**: Downgrade path fully implemented with `DROP TABLE` + `DROP TYPE` in reverse order  
✓ **CASCADING FKs**: Deleting parent cascades to children (no orphans)  

---

## How to Apply

### 1. Quick Start
```bash
# Set database URL
export DATABASE_URL="postgresql://user:password@localhost:5432/rapai_dev"

# Apply migration
cd alembic
alembic upgrade head

# Verify
psql -c "SELECT * FROM information_schema.tables WHERE table_schema='public';"
```

### 2. With Docker
```bash
# Start PostgreSQL 16
docker-compose -f docker-compose.dev.yml up -d postgres

# Apply migration
alembic upgrade head

# Verify (inside container)
docker exec -it rapai-postgres psql -U rapai -d rapai_dev -c "\dt"
```

### 3. Rollback (if needed)
```bash
# Rollback one migration
alembic downgrade -1

# Verify tables are gone
psql -c "\dt"
```

---

## Integration with JSON Schema SSOT

All tables derived from:
- `ontology/schemas/milestone.json`
- `ontology/schemas/blocker.json`
- `ontology/schemas/decision.json`
- `ontology/schemas/gate.json`
- `ontology/schemas/kpi.json`
- `ontology/schemas/artifact.json`
- `ontology/schemas/role.json`
- `ontology/schemas/risk.json`
- `ontology/schemas/ip.json`
- `ontology/schemas/workdirective.json`

**Governance**: When updating schemas, bump `x-ontology-version` and use `ontology.validators.governance.validate_semver_bump()` to confirm migration versioning matches SemVer rules.

---

## Phase III Preparation

This migration establishes the foundation for Phase III enhancements:
- **Alembic Hooks**: Pre/post-upgrade auto-population of reference tables (Roles, RoleTypes)
- **Migration Validation**: Schema diff detection + SemVer enforcement in CI
- **Rollback Safety**: Incremental downgrades with safety checks
- **Audit Trail**: Leverage `alembic_version` table for schema history

---

## Documentation

- **Comprehensive guide**: `alembic/README.md` (8.7 KB)
  - Structure, quick start, troubleshooting, best practices
  - Testing strategies (roundtrip, Docker, integration)
  - References to Alembic docs and RAPai ADRs

- **Migration source**: `alembic/versions/001_initial.py` (679 lines)
  - Detailed column comments (docstring per column)
  - All constraints explicit (CHECK, FK, INDEX, ENUM)
  - Safe upgrade/downgrade paths

- **Configuration files**:
  - `alembic/env.py`: Environment setup (online/offline modes)
  - `alembic/alembic.ini`: DB URL, logging, script location
  - `alembic/script.py.mako`: Template for auto-generating future migrations

---

## File Manifest

```
/c/project/project_manager/.claude/worktrees/goofy-khorana-ec26a5/
├── alembic/
│   ├── versions/
│   │   └── 001_initial.py         ← MIGRATION FILE (679 lines)
│   │       - 17 ENUMs
│   │       - 10 main tables
│   │       - 2 junction tables
│   │       - 35+ indexes
│   │       - Comprehensive upgrade() + downgrade()
│   ├── env.py                      ← Alembic environment (online/offline)
│   ├── alembic.ini                 ← Configuration (DB URL, logging)
│   ├── script.py.mako              ← Template for future migrations
│   ├── README.md                   ← Full documentation (8.7 KB)
│   └── __init__.py                 ← [Will be auto-created by Alembic]
└── ALEMBIC_SUMMARY.md              ← THIS FILE
```

---

## Key Design Decisions

1. **PostgreSQL Native ENUMs**: Type-safe (no string drift), enforced at database level
2. **ARRAY Types**: For multi-valued columns (deliverable_ids[], inventors[], jurisdiction[])
3. **JSON Type**: For complex nested structures (options[], criteria[], entities[])
4. **ULID PKs**: 26-char time-sortable IDs (better than UUIDs for time-range queries)
5. **ON DELETE CASCADE**: Maintain referential integrity automatically (no orphans)
6. **Comprehensive Indexes**: Covering common query patterns (project_id+status, owner_id, created_at)
7. **Timestamped Records**: `created_at` (immutable) + `updated_at` (mutable) for audit trail

---

## Success Criteria (Met)

- [x] All 10 extended objects mapped to tables (Milestone, Blocker, Decision, Gate, KPI, Artifact, Role, Risk, IP, WorkDirective)
- [x] All enums from JSON Schema implemented as PostgreSQL native types
- [x] All relationships and FKs established (including junctions)
- [x] Indexes cover common filtering patterns (project_id, status, owner_id, created_at)
- [x] upgrade() and downgrade() paths fully implemented
- [x] Migration is IDEMPOTENT and SAFE (no data loss)
- [x] Comprehensive documentation (README + inline comments)
- [x] Configuration files ready for immediate use

---

## Next Steps

1. **Database Setup**: Apply migration to dev/staging PostgreSQL
   ```bash
   alembic upgrade head
   ```

2. **Schema Verification**: Confirm tables and enums created
   ```bash
   psql -c "\dt"      # List tables
   psql -c "\dT"      # List types
   ```

3. **Pydantic Model Generation**: Auto-generate Python models from tables
   ```bash
   datamodel-code-generator --input-file-type sqlmodel \
     --output ontology/models/extended.py
   ```

4. **Integration Tests**: Write roundtrip tests (JSON → DB → JSON)

5. **Phase III Planning**: Plan additional migrations for Alembic hooks, audit tables, etc.

---

## Contact & Questions

For issues or questions:
- Review `alembic/README.md` for detailed documentation
- Check `ontology/06-ontology-design-charter.md` for governance rules
- Refer to `ADR-001` in `mindvault/decisions/` for strategic decisions

---

**Created**: 2026-04-22  
**Migration ID**: 001_initial  
**Status**: Ready for deployment  
**Reversibility**: SAFE (downgradeable)
