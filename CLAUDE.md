# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Summary

**RAPai (Research AI Platform) — L2.5 Ontology Implementation**

This repo implements the ontology layer for an AI-Native R&D Project Management platform. The focus is on enforcing a canonical JSON Schema (SSOT — Single Source of Truth) that all downstream systems (Pydantic models, databases, APIs) derive from. The design follows ADR-001 (Ontology Strategy) and is built with Python 3.11 + Pydantic v2.

**Current Status:** Phase I (Foundation) ✅ COMPLETE
- Core 5 Objects (Project, Task, WorkLog, Person, Event) fully specified
- 27/27 tests passing (73% code coverage)
- JSON Schema SSOT + Pydantic roundtrip enforcement active
- SemVer + Append-only governance validator ready

**Next:** Phase II (W3–W5) — Extended 10 Objects + 8 Link types + Compliance validators

---

## Quick Start

### Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Common Commands

**Testing**
```bash
# All tests
pytest ontology/tests/ -v

# Single test file
pytest ontology/tests/unit/test_roundtrip.py -v

# Single test
pytest ontology/tests/unit/test_roundtrip.py::TestProjectRoundtrip::test_contract_research_project -v

# With coverage report
pytest ontology/tests/ --cov=ontology --cov-report=html
```

**Code Quality**
```bash
# Type checking
mypy --strict ontology/

# Linting
ruff check ontology/

# Code formatting
ruff format ontology/
```

**Development Databases**
```bash
# Start local PostgreSQL 16, Neo4j 5, Qdrant v1.11, Redis
docker-compose -f docker-compose.dev.yml up -d

# Stop
docker-compose -f docker-compose.dev.yml down
```

**Code Generation (Phase II+)**
```bash
# Regenerate Pydantic models from JSON Schema (after schema changes)
python -m datamodel_code_generator --input ontology/schemas/project.json \
  --output ontology/models/core.py
```

---

## Architecture & Design Principles

### 1. SSOT: JSON Schema is Canonical

```
JSON Schema (Draft 2020-12) ← CANONICAL
    ↓
    ├→ Pydantic v2 models (auto-derivable)
    ├→ PostgreSQL migrations (Alembic)
    ├→ Neo4j Cypher (graph constraints)
    └→ OpenAPI / Public APIs
```

- All Objects are defined first as JSON Schema in `ontology/schemas/*.json`
- `x-ontology-version` field in every schema gates SemVer bumps
- Pydantic models generated from schemas (or manually overridden with validators)
- **Roundtrip tests enforce JSON ↔ Pydantic ↔ JSON equivalence** (CI gate)

### 2. Governance: SemVer + Append-Only

Per `ontology/06-ontology-design-charter.md`:

**Breaking Changes** (require MAJOR bump):
- Field removal
- Required field addition
- Enum value removal
- Numeric constraint narrowing
- Pattern change

**Non-Breaking Changes** (MINOR/PATCH):
- Field addition → MINOR
- Enum value addition → MINOR
- Doc changes → PATCH

Validator: `ontology.validators.governance.validate_semver_bump()` — auto-checks schema diffs against SemVer.

### 3. Business Rules via Pydantic Validators

Type constraints are enforced at the *field level* (JSON Schema + Pydantic):

```python
@model_validator(mode='after')
def _enforce_trl_by_type(self):
    if self.project_type in ('A', 'B') and not hasattr(self, 'trl_target'):
        raise ValueError("Project types A/B require 'trl_target'")
```

**Key rules:**
- Project type A/B → require `trl_target` (TRL gate)
- Project type C → require `crl_target` (CRL gate)
- Contract research overlay (`contract_modality="contract_research"`) → L2-C gate
- Task: no self-references, valid WBS code `^[0-9]+(\.[0-9]+)*$`
- WorkLog: tags unique + non-empty, content ≤32KB
- Event (LLM-sourced): if `confidence` or `actor_agent_id` starts with `AG-`, require `model_id` (PROV-O lineage)

### 4. Identifier Format: ULID (26 chars)

All object IDs use **ULID** (Crockford's base32, 26 chars):
```
01ARZ3NDEKTSV4RRFFQ69G5FAV  ← Valid ULID
Pattern: ^[0-9A-HJKMNP-TV-Z]{26}$
```

Fixtures use ULID format; any new fixture must comply. Pydantic validator enforces this via `StringConstraints`.

---

## File Structure (High-Level)

```
ontology/
├── schemas/              # JSON Schema SSOT (Draft 2020-12)
│   ├── enums.json       # Shared enums ($defs: ProjectTypeCode, CrossCutting, etc.)
│   ├── project.json     # Project with conditional TRL/CRL
│   ├── task.json        # Task with WBS + self-reference validators
│   ├── worklog.json     # WorkLog with tag uniqueness
│   ├── person.json      # Person with security_clearance
│   └── event.json       # CloudEvents 1.0 + PROV-O fields
│
├── models/              # Pydantic v2 models (derived from schemas)
│   ├── core.py         # Core 5 Objects + business rule validators
│   └── enums.py        # Python enums (must match JSON enums exactly)
│
├── validators/          # Custom validation logic
│   ├── governance.py   # SemVer + Append-only diff detector
│   └── compliance.py   # (Phase II) Ontology constraint checks
│
├── tests/
│   ├── unit/
│   │   ├── test_roundtrip.py    # JSON↔Pydantic↔JSON equivalence (10 tests)
│   │   └── test_schema_shape.py # Schema validity + x-ontology-version + enum match (13 tests)
│   ├── fixtures/                # Sample JSON data (all IDs = valid ULID)
│   └── conftest.py             # pytest fixtures + RefResolver
│
├── README.md            # Phase I setup/usage guide (1,265 lines)
└── prov/               # (Phase III) PROV-O Lineage + Outbox pattern

mindvault/
├── decisions/
│   ├── 001-ontology-strategy.md      # ADR-001: L2.5, SSOT, MVP 15 Objects
│   └── 002-ai-model-architecture.md  # ADR-002: AI model selection + decision 22
└── ontology/
    ├── 06-ontology-design-charter.md # Governance rules (SemVer, Append-only)
    ├── 07-operational-ontology-design.md  # Event-Driven Agentic OS
    ├── 08-ontology-stack-catalog.md      # Tech stack (Python, Pydantic, PostgreSQL, Neo4j, Qdrant)
    ├── 09-work-activity-ontology.md      # 10 Intent types
    └── 10-project-type-classification-v2.md  # WBS 8-type (A–H) + cross-cutting
```

---

## Development Workflow

### Adding a New Field to Project (Example)

1. **Update JSON Schema** (`ontology/schemas/project.json`)
   ```json
   {
     "properties": {
       "new_field": {
         "type": "string",
         "description": "..."
       }
     }
   }
   ```

2. **Bump `x-ontology-version`** (e.g., "0.1.0" → "0.1.1" if non-breaking)

3. **Update Python enum/model** (`ontology/models/enums.py`, `models/core.py`)
   - Add field to Pydantic dataclass
   - Add validator if needed
   - Ensure enum values match schema exactly

4. **Add roundtrip test** (`ontology/tests/unit/test_roundtrip.py`)
   - Create fixture JSON with new field
   - Test `model_validate()` + `model_dump_json()` roundtrip

5. **Run tests**
   ```bash
   pytest ontology/tests/ -v
   ```

6. **Commit** with SemVer-compliant message
   ```bash
   git commit -m "feat: Add new_field to Project (schema v0.1.1)"
   ```

### Schema Changes (Governance)

Use `ontology.validators.governance.compare_schemas()` to check diffs:

```python
from ontology.validators.governance import compare_schemas, validate_semver_bump

old = {...}  # Previous schema
new = {...}  # New schema

diff = compare_schemas(old, new)
print(f"Severity: {diff.severity}")  # "major", "minor", "patch", or "none"

validate_semver_bump("0.1.0", "0.1.1", diff)  # Raises if mismatch
```

---

## Phase II Checklist (W3–W5)

When starting Phase II:

- [ ] Add 10 extended Objects (WorkDirective, Role, Milestone, Blocker, Decision, Gate, KPI, Artifact, Risk, IP)
- [ ] Define 8 Link types (JSON Schema `links.json`)
- [ ] Define 10 Intent types (JSON Schema `actions.json`)
- [ ] Create Pydantic models for extended objects
- [ ] Write compliance validator (cardinality, cross-reference integrity)
- [ ] Write WBS classification validator
- [ ] Add integration tests (PostgreSQL CRUD, Neo4j relationships, Qdrant vectors)
- [ ] Start Phase III planning (Alembic migrations, Cypher scripts, Outbox)

---

## Important Files & References

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python dependencies, pytest config, ruff config |
| `docker-compose.dev.yml` | PostgreSQL + Neo4j + Qdrant + Redis dev setup |
| `ontology/README.md` | Detailed setup + testing guide for Phase I |
| `mindvault/decisions/001-ontology-strategy.md` | ADR-001: Strategic decisions 1–6 |
| `mindvault/ontology/06-ontology-design-charter.md` | Governance rules (SemVer, Append-only) |
| `ontology/tests/conftest.py` | pytest fixture definitions + RefResolver |
| `ontology/validators/governance.py` | SemVer + schema diff validator |

---

## Testing Best Practices

1. **Roundtrip is the SSOT sentinel**: If `test_roundtrip.py` passes, JSON ↔ Pydantic equivalence is guaranteed.
2. **Enum matching is enforced**: `test_schema_shape.py` ensures Python enums match JSON exactly.
3. **Schema validity is checked**: Every schema must be a valid Draft 2020-12 document.
4. **Negative tests matter**: Test both valid data (positive) and constraint violations (negative).

Example negative test pattern:
```python
with pytest.raises(ValueError, match="requires 'trl_target'"):
    Project.model_validate({...project_type: "A", no trl_target...})
```

---

## When in Doubt

- **Schema questions?** See `ontology/README.md` and `mindvault/decisions/001-ontology-strategy.md`
- **Governance rules?** See `mindvault/ontology/06-ontology-design-charter.md`
- **Test failures?** Check fixture ID format (must be 26-char ULID) and enum values
- **Phase II?** See "Phase II Checklist" above
- **Run tests locally:** `pytest ontology/tests/ -v` after `pip install -e ".[dev]"`

