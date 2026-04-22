# Alembic Migrations for RAPai Ontology

This directory contains database schema migrations for RAPai ontology Phase II extended objects (Milestones, Blockers, Decisions, Gates, KPIs, Artifacts, Roles, Risks, IPs, WorkDirectives) and Phase III enhancements.

## Structure

```
alembic/
├── versions/              # Migration scripts (*.py files)
│   └── 001_initial.py     # Phase II initial schema (Milestones, Blockers, Decisions, etc.)
├── env.py                 # Alembic environment configuration
├── script.py.mako         # Template for auto-generating new migrations
├── alembic.ini            # Alembic configuration (DB URL, logging, etc.)
└── README.md              # This file
```

## Governance

All migrations are governed by:
- **ADR-001 (SSOT)**: JSON Schema is canonical; Alembic derives from JSON definitions
- **ontology/06-ontology-design-charter.md**: SemVer versioning + Append-only constraints
- **Design principle**: Migrations are **IDEMPOTENT** and **SAFE** (create-only, no drops in upgrade)

## Quick Start

### Prerequisites

```bash
# Install Alembic (usually included with poetry/pip)
pip install alembic sqlalchemy

# Set database URL (PostgreSQL 16+)
export DATABASE_URL="postgresql://user:pass@localhost:5432/rapai_dev"
```

### Initialize a New Migration

After adding a new table/field to JSON Schema:

```bash
# Auto-generate from SQLAlchemy models (if using declarative models)
alembic revision --autogenerate -m "Add new field to Project"

# OR manually create a skeleton
alembic revision -m "Add new field to Project"

# Edit alembic/versions/NNN_add_new_field_to_project.py with your changes
```

### Apply Migrations

```bash
# Apply all pending migrations to the database
alembic upgrade head

# Apply specific migration
alembic upgrade 001_initial

# Check current revision
alembic current

# Show history
alembic history
```

### Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001_initial

# Downgrade all (careful!)
alembic downgrade base
```

## Migration 001: Initial Phase II Schema

**Revision**: 001_initial.py  
**Objects Created**: 10 extended objects + 2 junction tables  
**ENUM Types**: 17 PostgreSQL native enums  

### Tables Created

| Table | Primary Key | Parent FK | Key Columns |
|-------|------------|-----------|------------|
| `milestones` | milestone_id | project_id | name, date, status, deliverable_ids[] |
| `blockers` | blocker_id | task_id | severity, description, status, owner_id |
| `decisions` | decision_id | - | context, options, chosen, status |
| `gates` | gate_id | project_id | level, status, signed_by, criteria[] |
| `kpis` | kpi_id | project_id, task_id | tier, metric, target, actual, frequency |
| `artifacts` | artifact_id | - | type, uri, hash, security_tier, status |
| `roles` | role_id | - | name, responsibilities[], permissions[] |
| `risks` | risk_id | project_id, task_id | category, likelihood, risk_score, status |
| `ips` | ip_id | project_id | type, status, filing_number, jurisdiction[] |
| `work_directives` | directive_id | - | intent, status, entities[], due_date |
| `decision_evidence` | (decision_id, artifact_id) | decisions, artifacts | - |
| `person_role_assignments` | (person_id, role_id, project_id) | persons, roles, projects | effective_from, effective_to |

### ENUM Types

- `severity_enum`: low, medium, high, critical
- `blocker_status_enum`: open, in_progress, resolved, closed
- `decision_status_enum`: pending, approved, rejected, implemented, reviewed
- `gate_status_enum`: planned, in_progress, passed, failed, waived
- `gate_level_enum`: L1_TRL, L1_CRL, L2_STAGE, L2_C_CLIENT, L3_ANNUAL, L4_MOVING
- `kpi_tier_enum`: output, outcome, value
- `project_status_enum`: draft, active, on_hold, completed, cancelled
- `artifact_type_enum`: doc, code, data, report, presentation, dataset, model, other
- `artifact_status_enum`: draft, in_review, published, archived, deprecated
- `security_tier_enum`: PUBLIC, RESTRICTED, CONFIDENTIAL, SECRET
- `role_type_enum`: PI, Coordinator, Researcher, DevOps, Manager, Analyst, Engineer, Consultant, Admin, Other
- `risk_category_enum`: technical, schedule, cost, scope, resource, regulatory, market, quality, security, other
- `likelihood_enum`: rare, unlikely, possible, likely, almost_certain
- `ip_type_enum`: patent, copyright, trademark, trade_secret, design_right, utility_model
- `ip_status_enum`: idea, drafting, filed, published, granted, rejected, abandoned
- `work_directive_status_enum`: created, validated, dispatched, in_progress, completed, failed
- `intent_enum`: create_task, update_status, log_work, assign_person, raise_blocker, resolve_blocker, record_decision, submit_gate, measure_kpi, produce_artifact, validate_level_up_criteria

### Indexes

All tables have:
- PK index (automatic)
- Compound indexes for filtering (e.g., `(project_id, status)`)
- Foreign key indexes for join performance
- Temporal indexes for created_at/updated_at queries

## Constraints

### Referential Integrity

- All FKs use `ON DELETE CASCADE` or `ON DELETE SET NULL` as appropriate
- Primary keys: 26-char ULID format (indexed)
- Date/DateTime: ISO 8601 format with timezone

### Business Rules (Enforced at Schema Level)

1. **Severity Enum**: Blockers must have valid severity (PostgreSQL CHECK)
2. **Status Enums**: All status fields are typed (no string drift)
3. **ULID Format**: IDs validated at application layer (schema accepts VARCHAR(36))
4. **Timestamps**: All tables have `created_at` (NOT NULL, default NOW()) and `updated_at`

## Integration with Phase III

Phase III migrations will extend this schema with:

- **Alembic Hooks** (pre/post upgrade): Auto-populate immutable reference tables
- **Migration Validation**: SemVer bump detection (if schema v0.2.0 → 0.3.0, must verify MINOR)
- **Rollback Safety**: Every downgrade must be idempotent (safe to re-run)
- **Audit Trail**: `alembic_version` table tracks applied migrations

## Configuration

### Database URL

Set via environment or `alembic.ini`:

```bash
# PostgreSQL 16 (recommended)
export DATABASE_URL="postgresql://user:password@localhost:5432/rapai_dev"

# Or in alembic.ini
sqlalchemy.url = postgresql://user:password@localhost:5432/rapai_dev
```

### Logging

Default level: WARN. Change in `alembic.ini [logger_alembic] level = INFO` for verbose output.

## Testing Migrations

### Pre-apply Check

```bash
# Show SQL without applying
alembic upgrade head --sql

# Check what will be applied
alembic heads
```

### Test Roundtrip

```bash
# Apply migration
alembic upgrade head

# Verify schema
psql -U user -d rapai_dev -c "\dt"  # List tables

# Verify enums
psql -U user -d rapai_dev -c "\dT"  # List types

# Rollback
alembic downgrade -1

# Verify tables are gone
psql -U user -d rapai_dev -c "\dt"
```

### Test with Docker

```bash
# Start PostgreSQL 16 container
docker-compose -f docker-compose.dev.yml up -d postgres

# Run migrations
alembic upgrade head

# Verify (connect to container)
docker exec -it rapai-postgres psql -U rapai -d rapai_dev -c "\dt"

# Cleanup
docker-compose -f docker-compose.dev.yml down
```

## Troubleshooting

### Cannot connect to database

```bash
# Verify PostgreSQL is running
psql -U user -d rapai_dev -c "SELECT version();"

# Check alembic.ini sqlalchemy.url
grep "sqlalchemy.url" alembic.ini

# Or set DATABASE_URL explicitly
export DATABASE_URL="postgresql://user:pass@localhost:5432/rapai_dev"
```

### Foreign key constraint error

If downgrade fails with FK errors:
1. Check that `ON DELETE CASCADE` is set correctly
2. Manually drop dependent tables in downgrade (in correct order)
3. Example: drop `person_role_assignments` before `roles`

### Enum type already exists

If re-applying migration:
```bash
# Drop the conflicting enum
psql -U user -d rapai_dev -c "DROP TYPE IF EXISTS severity_enum CASCADE;"

# Re-apply migration
alembic upgrade 001_initial
```

## Best Practices

1. **Always test downgrade**: `alembic downgrade -1 && alembic upgrade head`
2. **Write idempotent migrations**: Use `CREATE TABLE IF NOT EXISTS`, `DROP TABLE IF EXISTS`
3. **Version your schemas**: Keep `x-ontology-version` in JSON schemas in sync with migration versions
4. **Document complex migrations**: Add comments explaining business logic
5. **Review SemVer**: Before applying, verify migration matches semantic versioning rules
6. **Backup before apply**: `pg_dump rapai_dev > backup.sql`

## References

- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **PostgreSQL ENUMs**: https://www.postgresql.org/docs/current/datatype-enum.html
- **RAPai Ontology**: `mindvault/ontology/06-ontology-design-charter.md`
- **ADR-001**: `mindvault/decisions/001-ontology-strategy.md`
