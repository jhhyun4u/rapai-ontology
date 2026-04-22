# Alembic Migration Validation Checklist

Use this checklist to verify the migration is working correctly.

## Pre-Deployment

- [ ] Database URL is set correctly in `alembic.ini` or `DATABASE_URL` env var
- [ ] PostgreSQL 16+ is running and accessible
- [ ] Python 3.11+ environment with Alembic installed
- [ ] No existing tables conflict with migration (check `\dt` in psql)

## Deployment

```bash
# Run these commands in order
```

### Step 1: Check Current State
```bash
alembic current
# Expected output: empty (no version), or existing version if upgrading
```
- [ ] Output matches expectation

### Step 2: Show Pending Migrations
```bash
alembic heads
# Expected output: 001_initial
```
- [ ] Shows `001_initial` as pending

### Step 3: Preview SQL (Optional)
```bash
alembic upgrade head --sql
# Should show CREATE TYPE and CREATE TABLE statements
```
- [ ] SQL output looks reasonable (no errors)

### Step 4: Apply Migration
```bash
alembic upgrade head
# Expected: "Running upgrade ... -> 001_initial, add 10 extended objects"
```
- [ ] No errors
- [ ] Output shows successful migration

### Step 5: Verify in Database

#### Check Tables
```bash
psql -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
"
```
- [ ] All 12 tables present:
  - [ ] milestones
  - [ ] blockers
  - [ ] decisions
  - [ ] gates
  - [ ] kpis
  - [ ] artifacts
  - [ ] roles
  - [ ] risks
  - [ ] ips
  - [ ] work_directives
  - [ ] decision_evidence
  - [ ] person_role_assignments

#### Check Enum Types
```bash
psql -c "
SELECT typname FROM pg_type 
WHERE typtype = 'e' 
ORDER BY typname;
"
```
- [ ] All 17 enums present:
  - [ ] severity_enum
  - [ ] blocker_status_enum
  - [ ] decision_status_enum
  - [ ] gate_status_enum
  - [ ] gate_level_enum
  - [ ] kpi_tier_enum
  - [ ] project_status_enum
  - [ ] artifact_type_enum
  - [ ] artifact_status_enum
  - [ ] security_tier_enum
  - [ ] role_type_enum
  - [ ] risk_category_enum
  - [ ] likelihood_enum
  - [ ] ip_type_enum
  - [ ] ip_status_enum
  - [ ] work_directive_status_enum
  - [ ] intent_enum

#### Check Indexes
```bash
psql -c "
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename;
"
```
- [ ] ~35+ indexes created (at least 2-3 per main table)

#### Check Foreign Keys
```bash
psql -c "
SELECT constraint_name, table_name, column_name 
FROM information_schema.key_column_usage 
WHERE constraint_name LIKE '%fk%' OR constraint_name LIKE '%FK%'
ORDER BY table_name;
"
```
- [ ] Foreign keys for all references:
  - [ ] milestones.project_id → projects
  - [ ] blockers.task_id → tasks
  - [ ] blockers.owner_id → persons
  - [ ] gates.project_id → projects
  - [ ] gates.signed_by → persons
  - [ ] gates.decision_id → decisions
  - [ ] kpis → projects, tasks, persons
  - [ ] artifacts → tasks, persons
  - [ ] risks → projects, tasks, persons, blockers
  - [ ] ips → projects
  - [ ] work_directives.parent_id → work_directives
  - [ ] work_directives.source_worklog_id → worklogs
  - [ ] decision_evidence → decisions, artifacts
  - [ ] person_role_assignments → persons, roles, projects

#### Inspect Sample Table Schema
```bash
psql -c "\d milestones"
psql -c "\d blockers"
```
- [ ] Columns match migration definition
- [ ] Constraints are in place (NOT NULL, FK, etc.)
- [ ] Timestamps exist (created_at, updated_at)

## Post-Deployment

### Test Roundtrip (Sample)

```sql
-- Insert test data
INSERT INTO roles (role_id, name, description) 
VALUES ('01ARZ3NDEKTSV4RRFFQ69G5FA', 'PI', 'Principal Investigator');

-- Query back
SELECT * FROM roles WHERE role_id = '01ARZ3NDEKTSV4RRFFQ69G5FA';

-- Verify enum constraint
INSERT INTO roles (role_id, name, description) 
VALUES ('01ARZ3NDEKTSV4RRFFQ70G5FB', 'INVALID', 'Test');
-- Expected: ERROR invalid input value for enum role_type_enum: "INVALID"
```
- [ ] Insert succeeds
- [ ] Query returns correct data
- [ ] Enum constraint enforced

### Rollback Test (Safety Verification)

```bash
# Rollback
alembic downgrade -1
# Expected: "Downgrading from 001_initial..."

# Verify tables gone
psql -c "\dt"
# Expected: No rapai tables

# Upgrade again
alembic upgrade head
# Expected: "Running upgrade ... -> 001_initial..."

# Verify tables restored
psql -c "\dt"
# Expected: All 12 tables present
```
- [ ] Downgrade succeeds
- [ ] Tables/enums removed
- [ ] Re-upgrade succeeds
- [ ] All tables/enums restored
- [ ] Data preserved (if tests were run with --transact flag)

## Final Verification

- [ ] Schema hash/signature matches expected (document below)
- [ ] No warnings in alembic logs
- [ ] No permission errors
- [ ] No connection issues

## Schema Signature (for reference)

Run after successful deployment:
```bash
psql -c "
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
"
```
Expected: **12 tables**

```bash
psql -c "
SELECT COUNT(*) FROM pg_type WHERE typtype = 'e';
"
```
Expected: **17 enums**

```bash
psql -c "
SELECT COUNT(*) FROM information_schema.table_constraints 
WHERE table_schema = 'public' AND constraint_type = 'FOREIGN KEY';
"
```
Expected: **14+ foreign key constraints**

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "Cannot connect to database" | Check `DATABASE_URL`, ensure PostgreSQL running |
| "Enum type already exists" | Drop with `DROP TYPE IF EXISTS xxx CASCADE;` before retry |
| "Foreign key constraint fails" | Check cascade settings in migration, verify FK order |
| "Permission denied on schema" | Ensure user has CREATE TABLE/TYPE privileges |
| "Rollback fails" | Check downgrade() function, may need CASCADE deletes |

## Sign-Off

- [ ] All checks passed
- [ ] Migration verified in development
- [ ] Ready for staging/production deployment
- [ ] Date deployed: _______________
- [ ] Deployed by: _______________
- [ ] Notes: _______________

