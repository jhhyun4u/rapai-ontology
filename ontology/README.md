# Ontology — L2.5 SSOT Implementation

**Version:** 0.1.0 (Phase I Foundation)  
**Status:** MVP Core 5 Objects + SSOT Enforcement  
**Last Updated:** 2026-04-18

---

## Overview

This module implements the **L2.5 Ontology** for RAPai (Research AI Platform) per [ADR-001](../mindvault/decisions/001-ontology-strategy.md) and the [Ontology Design Charter](../mindvault/ontology/06-ontology-design-charter.md).

### Core Principle: JSON Schema = SSOT

Per ADR-001 R5, **JSON Schema is the single source of truth (SSOT)**. All representations (Pydantic models, databases, APIs) derive from schemas.

**Enforcement:**
- ✅ Roundtrip tests: `JSON → Pydantic → JSON` equivalence
- ✅ Schema-shape tests: Every schema is valid Draft 2020-12, declares `x-ontology-version`
- ✅ Enum matching: Python enums match JSON Schema `$defs` exactly
- ✅ Governance validator: SemVer + Append-only rules (breaking changes require MAJOR bump)

---

## Phase I — Core 5 Objects

| Object | Schema | Pydantic Model | Tests |
|--------|--------|---|---|
| **Project** | `schemas/project.json` | `models/core.Project` | ✅ roundtrip + shape |
| **Task** | `schemas/task.json` | `models/core.Task` | ✅ roundtrip + validators |
| **WorkLog** | `schemas/worklog.json` | `models/core.WorkLog` | ✅ roundtrip + tag validation |
| **Person** | `schemas/person.json` | `models/core.Person` | ✅ roundtrip |
| **Event** | `schemas/event.json` | `models/core.Event` | ✅ roundtrip + CloudEvents v1.0 |

**Shared Enums:** `schemas/enums.json`
- ProjectTypeCode (A–H WBS types)
- ContractModality, FundingSource, SecurityTier, ScaleTier
- GateLevel, GateStatus, KPITier, DailyReportTag (13 values)
- TaskStatus, ProjectStatus, TRLLevel, CRLLevel, Intent
- ArtifactType, IPType, IPStatus, RiskCategory, Severity, Likelihood

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install package in editable mode
pip install -e .
```

### 2. Run Tests

```bash
# All tests
pytest ontology/tests/ -v

# Unit tests only
pytest ontology/tests/unit/ -v

# Roundtrip tests (JSON↔Pydantic)
pytest ontology/tests/unit/test_roundtrip.py -v

# Schema shape tests (validity + enums)
pytest ontology/tests/unit/test_schema_shape.py -v

# With coverage
pytest ontology/tests/ --cov=ontology --cov-report=html
```

### 3. Docker Compose (Databases)

```bash
# Start PostgreSQL 16, Neo4j 5, Qdrant v1.11, Redis
docker-compose -f docker-compose.dev.yml up -d

# Stop
docker-compose -f docker-compose.dev.yml down
```

**Services:**
- PostgreSQL: `localhost:5432` (user: `rapai`, db: `rapai_dev`)
- Neo4j: `localhost:7687` (HTTP: `localhost:7474`, user: `neo4j`, password: `rapai`)
- Qdrant: `localhost:6333`
- Redis: `localhost:6379`

---

## Directory Structure

```
ontology/
├── __init__.py                 # Package init (version, layer constant)
├── README.md                   # This file
│
├── schemas/                    # JSON Schema SSOT (Draft 2020-12)
│   ├── enums.json             # Shared enum definitions ($defs)
│   ├── project.json           # Project Object
│   ├── task.json              # Task Object
│   ├── worklog.json           # WorkLog Object
│   ├── person.json            # Person Object
│   └── event.json             # CloudEvents + PROV-O envelope
│
├── models/                     # Pydantic v2 models (derived from schemas)
│   ├── __init__.py            # Public API exports
│   ├── core.py                # Core 5 Objects (Project, Task, WorkLog, Person, Event)
│   ├── enums.py               # Python enums + CrossCutting dataclass
│   ├── links.py               # (Phase II) Relation types
│   └── actions.py             # (Phase II) Intent types
│
├── validators/                 # Custom validators
│   ├── __init__.py            # Public API (governance module)
│   ├── governance.py          # SemVer + Append-only enforcement
│   ├── compliance.py          # (Phase II) Ontology constraint checks
│   └── wbs_classification.py  # (Phase II) WBS type validation
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures (schemas, fixtures)
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_roundtrip.py  # JSON↔Pydantic roundtrip tests
│   │   ├── test_schema_shape.py # Schema validity + enum matching
│   │   └── test_validators.py # (Phase II) Validator tests
│   │
│   ├── integration/           # (Phase II) DB + Outbox tests
│   ├── e2e/                   # (Phase III) End-to-end scenarios
│   │
│   └── fixtures/              # Sample JSON data
│       ├── sample_project.json
│       ├── sample_project_developmental.json
│       ├── sample_task.json
│       ├── sample_worklog.json
│       ├── sample_person.json
│       └── sample_event.json
│
├── prov/                      # (Phase III) PROV-O Lineage
│   ├── writer.py             # CloudEvents → PROV-O JSON-LD
│   └── schemas/
│       └── prov-o.context.jsonld
│
├── migrations/                # (Phase III) Database migrations
│   ├── postgres/
│   │   ├── env.py            # Alembic config
│   │   └── versions/
│   ├── neo4j/
│   │   ├── 001_schema_constraints.cypher
│   │   └── 002_relationship_types.cypher
│   └── qdrant/
│       └── 001_init_collections.py
│
└── outbox/                    # (Phase III) Outbox Pattern
    ├── publisher.py          # PG outbox → Neo4j/Redis
    └── schemas/
        └── outbox.sql
```

---

## Key Rules & Governance

### SemVer + Append-Only (ontology/06)

1. **Breaking Changes** require MAJOR version bump:
   - Property removal
   - Required field addition
   - Enum value removal
   - Numeric constraint narrowing
   - Pattern change
   - `additionalProperties: true → false`

2. **Non-Breaking Changes** allow MINOR bump:
   - Property addition
   - Enum value addition
   - Documentation changes → PATCH

3. **Validator:** `ontology.validators.governance.validate_semver_bump()`

### Business Rules (Pydantic Validators)

- **Project type A/B**: Require `trl_target` (TRL gate)
- **Project type C**: Require `crl_target` (CRL gate)
- **Contract research** (`contract_modality="contract_research"`): Overlay L2-C gate (client acceptance)
- **Task**: No self-references, parent ≠ self, valid WBS code `^[0-9]+(\.[0-9]+)*$`
- **WorkLog**: Tags must be unique, ≥1 tag, content ≤32,768 chars
- **Event** (LLM-sourced): If `confidence` or `actor_agent_id` starts with `AG-`, require `model_id` (PROV-O lineage)

---

## Example Usage

### Load & Validate a Project

```python
import json
from ontology.models.core import Project
from jsonschema import Draft202012Validator

# Load fixture
with open("ontology/tests/fixtures/sample_project.json") as f:
    payload = json.load(f)

# Validate against schema
with open("ontology/schemas/project.json") as f:
    schema = json.load(f)
Draft202012Validator(schema).validate(payload)

# Parse into Pydantic model
project = Project.model_validate(payload)

# Serialize back to JSON
serialized = json.loads(project.model_dump_json(exclude_none=True))
print(f"Project: {project.name} (type {project.project_type})")
```

### Check Enum Matching

```python
from ontology.models.enums import ProjectTypeCode
import json

# Load schema enums
with open("ontology/schemas/enums.json") as f:
    enums_schema = json.load(f)

schema_values = enums_schema["$defs"]["ProjectTypeCode"]["enum"]
python_values = [member.value for member in ProjectTypeCode]

assert sorted(schema_values) == sorted(python_values), "Enum mismatch!"
```

### Validate Schema Changes

```python
from ontology.validators.governance import compare_schemas, validate_semver_bump

old_schema = {...}
new_schema = {...}

diff = compare_schemas(old_schema, new_schema)
print(f"Severity: {diff.severity}")  # "major", "minor", "patch", or "none"

validate_semver_bump("0.1.0", "0.2.0", diff)  # Raises BreakingChangeError if mismatch
```

---

## Testing Strategy

### Unit Tests (Phase I)

| Test | Coverage | Purpose |
|------|----------|---------|
| `test_roundtrip.py` | 5 Objects × 5 scenarios | JSON↔Pydantic equivalence |
| `test_schema_shape.py` | All schemas | Validity (Draft 2020-12) + `x-ontology-version` + enum matching |

**Run:**
```bash
pytest ontology/tests/unit/ -v --tb=short
```

**Expected:** 20+ tests, all PASS

### Integration Tests (Phase II)

- PostgreSQL CRUD (Alembic migrations)
- Neo4j graph operations (relationships, constraints)
- Qdrant vector indexing
- Outbox propagation (PG → Neo4j)

### E2E Tests (Phase III)

- Journal input → Parser mock → WorkLog → Database roundtrip → PROV-O lineage

---

## Next Steps (Phase II & III)

### Phase II (W3–W5): Extended Objects + Relations + Compliance
- 10 additional Objects (WorkDirective, Role, Milestone, Blocker, Decision, Gate, KPI, Artifact, Risk, IP)
- 8 Link types (depends_on, produces, blocks, assigned_to, governed_by, measured_by, raised_from, related_ip)
- 10 Intent types (from ontology/09-work-activity-ontology.md)
- Compliance validator (cardinality, cross-reference integrity)
- WBS classification validator

### Phase III (W6–W8): Storage + Events
- PostgreSQL Alembic migrations (15 tables + audit)
- Neo4j Cypher (15 nodes + 8 relationships + Append-only constraints)
- Qdrant initialization (2 collections: main_corpus, contract_research_corpus)
- Outbox Pattern (PG → Neo4j/Redis propagation)
- PROV-O Lineage writer (CloudEvents → JSON-LD)
- E2E tests (journal input → lineage)

---

## References

| Document | Purpose |
|----------|---------|
| [ADR-001: Ontology Strategy](../mindvault/decisions/001-ontology-strategy.md) | Strategic decisions 1–6 (L2.5, SSOT, MVP scope) |
| [Ontology Design Charter (06)](../mindvault/ontology/06-ontology-design-charter.md) | SemVer + Append-only governance rules |
| [Operational Ontology (07)](../mindvault/ontology/07-operational-ontology-design.md) | Event-Driven Agentic OS (CloudEvents) |
| [Ontology Stack Catalog (08)](../mindvault/ontology/08-ontology-stack-catalog.md) | Tech stack rationale (Python, Pydantic v2, PostgreSQL, Neo4j, Qdrant) |
| [Work Activity Ontology (09)](../mindvault/ontology/09-work-activity-ontology.md) | 10 Intent types (create_task, update_status, log_work, etc.) |
| [Project Type Classification v2.0 (10)](../mindvault/ontology/10-project-type-classification-v2.md) | WBS 8-type (A–H) + cross-cutting axes |
| [ADR-002: AI Model Architecture](../mindvault/decisions/002-ai-model-architecture.md) | Decision 22 (contract_research L2-C gate) |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'ontology'`

**Solution:** Install in editable mode:
```bash
pip install -e .
```

### `pytest: command not found`

**Solution:** Install dev dependencies:
```bash
pip install pytest pytest-cov hypothesis jsonschema
```

### Schema validation fails

1. Ensure all schemas in `ontology/schemas/` are valid Draft 2020-12
2. Check `$id` and `$defs` structure
3. Verify enum values match Python enums exactly

### Test fixtures fail to load

1. Check fixture paths in `conftest.py`
2. Ensure `ontology/tests/fixtures/*.json` exist
3. Verify JSON is syntactically valid: `python -m json.tool <file.json>`

---

## Contributing

When modifying schemas:

1. **Update schema** in `ontology/schemas/`
2. **Regenerate model** (if using datamodel-code-generator):
   ```bash
   python -m datamodel_code_generator --input ontology/schemas/project.json \
     --output ontology/models/core.py
   ```
3. **Update Python enums** in `ontology/models/enums.py` to match `enums.json`
4. **Add roundtrip test** in `ontology/tests/unit/test_roundtrip.py`
5. **Bump version** in schema's `x-ontology-version` if breaking
6. **Run tests:** `pytest ontology/tests/ -v`
7. **Commit:** `git commit -m "feat: Update schema (project v0.2.0)"`

---

**Questions?** See [ADR-001](../mindvault/decisions/001-ontology-strategy.md) or the [Ontology Design Charter](../mindvault/ontology/06-ontology-design-charter.md).
