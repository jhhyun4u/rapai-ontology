# Alembic Quick Start Guide

## Apply Migration (5 minutes)

### 1. Set Database URL
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/rapai_dev"
```

### 2. Run Migration
```bash
cd alembic
alembic upgrade head
```

### 3. Verify
```bash
psql -c "\dt"    # See tables
psql -c "\dT"    # See enums
```

## What Gets Created

10 tables + 2 junction tables + 17 enums:
- **milestones**: Phase completion targets
- **blockers**: Task impediments
- **decisions**: Recorded decisions with options
- **gates**: Stage-gate reviews (TRL, CRL, L2-C, etc.)
- **kpis**: Output/Outcome/Value metrics
- **artifacts**: Deliverables (docs, code, data, reports)
- **roles**: Role definitions with permissions
- **risks**: Risk register with likelihood/impact
- **ips**: Intellectual property (patents, copyrights, etc.)
- **work_directives**: Intent-driven work (Phase III W1 enhancement)
- **decision_evidence**: Links decisions to artifacts
- **person_role_assignments**: Person ↔ Role mapping

## Rollback (if needed)

```bash
alembic downgrade -1    # Undo last migration
alembic downgrade base  # Undo all migrations
```

## With Docker

```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Apply migration
alembic upgrade head

# Verify (inside container)
docker exec -it rapai-postgres psql -U rapai -d rapai_dev -c "\dt"
```

## Troubleshooting

**Cannot connect?**
```bash
psql -c "SELECT version();"  # Check PostgreSQL running
grep sqlalchemy.url alembic.ini  # Check config
```

**Enum type exists error?**
```bash
psql -c "DROP TYPE IF EXISTS severity_enum CASCADE;"
alembic upgrade 001_initial
```

## More Help

- Full docs: `README.md`
- Migration source: `versions/001_initial.py`
- Governance: `ontology/06-ontology-design-charter.md`
