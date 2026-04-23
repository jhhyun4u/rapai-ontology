# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Summary

**RAPai (Research AI Platform) — L2.5 Ontology Implementation**

This repo implements the ontology layer for an AI-Native R&D Project Management platform. The focus is on enforcing a canonical JSON Schema (SSOT — Single Source of Truth) that all downstream systems (Pydantic models, databases, APIs) derive from. The design follows ADR-001 (Ontology Strategy) and ADR-002 (Operational Ontology) documented in `mindvault/` and is built with Python 3.11 + Pydantic v2.

**Current Status: TIER 0 (Foundation) ✅ COMPLETE — 2026-04-22**
- **TIER 0 Achievement:**
  - T0-1: Core 5 Objects (Project, Task, WorkLog, Person, Event) + 43 roundtrip tests ✓
  - T0-2: 8 Link types + 11 Action types + 30 model tests ✓
  - T0-4: WorkLog → WorkDirective → Action → Event parser pipeline + 16 parser tests ✓
  - **93 total tests passing | 81% code coverage**
  - JSON Schema SSOT (Draft 2020-12) + Pydantic v2 roundtrip enforcement active
  - SemVer governance + Append-only validator ready

**Next: TIER 1A (Compliance & Integration) — Weeks 8-14**
- Extended 10 Objects (WorkDirective, Milestone, Blocker, Decision, Gate, KPI, Artifact, Role, Risk, IP)
- 8 Compliance Validators (WBS A-H, cardinality, cross-reference, TRL/CRL gates, cascading blocks, role authority, decision provenance, rule append-only)
- 3DB Migration (PostgreSQL schema + Neo4j relationships + Qdrant embeddings)
- Observability Infrastructure (Prometheus metrics, Grafana dashboard, SLO definitions per performance analysis)

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

**Performance & Metrics**
```bash
# View performance metrics (Phase II+)
curl http://localhost:8000/metrics

# Profile validation latency
python -c "
from ontology.models.core import Project
import statistics
stats = Project.get_validation_stats()
print(f'P50: {stats.get(\"p50\", \"N/A\")}ms, P99: {stats.get(\"p99\", \"N/A\")}ms')
"
```

---

## TIER 1A Roadmap (Weeks 8-14) — Compliance & Integration Layer

### Strategic Context

TIER 0 established the **SSOT foundation**. TIER 1A builds the **governance layer** before agents come online in TIER 1B.

```
TIER 0 (Complete):     JSON Schema SSOT + Pydantic models + Parser
                       └─ 93 tests, 81% coverage ✓

TIER 1A (Next 7 weeks): Extended Objects + Compliance Rules + 3DB + Observability
                        ├─ 10 extended objects (WorkDirective, Milestone, Blocker, etc.)
                        ├─ 8 compliance validators (governance layer)
                        ├─ PostgreSQL + Neo4j + Qdrant schema deployment
                        └─ Prometheus/Grafana observability baseline

TIER 1B (Weeks 15-22): CoordinatorAI + 9 SpecialistAgents + Event-driven loop
                       └─ LogSubmitted → Task update operational loop
```

### Week-by-Week Breakdown

| Week | Focus | Deliverables | Parallelization |
|------|-------|---------------|-----------------|
| **8** | Extended Objects (10) + Compliance Validators (8) | 20 roundtrip tests + 8 validators | 3x Backend architects |
| **9-10** | 3DB Schema (PostgreSQL + Neo4j + Qdrant) | Migration scripts + integration tests | Backend-Arch-1 vs Backend-Arch-2 |
| **11** | Observability (Prometheus + Grafana + SLO) | Metrics, dashboard, alert rules | DevOps/Backend overlap |
| **12** | Integration Testing (3DB consistency) | 15+ end-to-end tests | Full team |
| **13** | Compliance Validators Deep Dive (8/8) | 16 validator tests + audit logging | Backend-Arch-1 solo |
| **14** | Documentation + TIER 1B Prep | Analysis report + handoff checklist | PM + Tech lead |

### Compliance Validators (Week 13 Focus)

The 8 validators enforce governance per `mindvault/06-ontology-design-charter.md`:

1. **WBS Classification A-H** — Map project_type to allowed WBS patterns
2. **Cardinality Constraints** — Max tasks, recursion depth limits
3. **Cross-reference Integrity** — FK validation (task.owner_id → Person)
4. **TRL/CRL Gates** — Type A requires trl_target, Type C requires crl_target
5. **Blocker Cascading** — If Task blocked → dependent tasks auto-flagged
6. **Role Authority Chain** — ProgramDirector > ProjectLead > SubprojectLead
7. **Decision Provenance** — Every Action auto-generates Decision with evidence link
8. **Rule Append-Only** — Rules versioned, never deleted (SemVer governance)

### Key Dependencies Between Tiers

```
TIER 0 → TIER 1A:
  Extended Objects depend on Core 5 Objects schemas ✓
  Validators depend on Pydantic models ✓
  3DB depends on JSON schema structure ✓

TIER 1A → TIER 1B:
  ❌ CoordinatorAI cannot dispatch until compliance layer locked
  ❌ Event routing requires validated ontology state
  → TIER 1A completion gates TIER 1B kickoff
```

---

## Performance & Responsiveness

### TIER 0 Baseline (Measured 2026-04-22)

Per `mindvault/11-performance-analysis.md`:

**Validation Performance:**
- Pydantic validation: 0.089ms/op ✓
- Full JSON roundtrip: 0.266ms/op ✓
- Rule engine (13 rules): 0.0005ms/op ✓
- **Ontology contribution to agent latency: 0.07%**

**Actual Agent Latency Breakdown:**

| Component | Duration | Agent Latency % |
|-----------|----------|-----------------|
| LLM inference (GPT-4 equiv) | 500-2000ms | **99%** ← Real bottleneck |
| Ontology validation | 0.35ms | <0.1% ← Noise level |
| DB query (w/o cache) | 1-10ms | <1% |
| Network I/O | 100-400ms | ~5% |

**Conclusion:** Ontology is NOT the performance constraint. Agent responsiveness is determined by LLM quality and network latency, not SSOT validation.

### Performance Design Principles (P1-P4)

1. **P1: Validation First** (non-negotiable)
   - Cost NOW: 0.089ms validation
   - Cost LATER if invalid data stored: 5000ms recovery (56,000× worse)
   - **Decision:** Strict typing is FREE compared to data corruption cost

2. **P2: Async-first for I/O-bound operations** (TIER 1A Week 11)
   - WorkLog parsing: Background batch (non-blocking agent response)
   - DB caching: Redis with 5min TTL for Project/Task hot data
   - Report generation: Queue async, notify when ready
   - ✓ **Improves concurrency 5-10×**

3. **P3: No over-optimization** (anti-pattern avoidance)
   - ❌ Lazy validation → data quality drops, 0.02% latency saved (useless)
   - ❌ Hot/Cold data split → architecture complexity, 0.005% latency saved (useless)
   - ✅ Focus instead on: DB indexing (10-50× speedup), Redis caching (100-1000× speedup)

4. **P4: Metrics-driven decisions** (TIER 1A Week 11)
   - Deploy Prometheus: `ontology_validation_latency_ms`, `rule_execution_time_ms`, `cache_hit_ratio`
   - Set SLO: Roundtrip P99 < 1.0ms (Phase II target)
   - Never optimize without measurement

### TIER 1A Performance Roadmap (Weeks 11-13)

| Week | Task | Expected Impact |
|------|------|-----------------|
| **W11** | Prometheus instrumentation | Visibility into latency distribution |
| **W11** | Grafana dashboard setup | Real-time monitoring |
| **W12** | Async WorkLog parsing | 5-10× throughput (batch processing) |
| **W13** | DB indexing (project_type, person_id) | 10-50× query speedup |
| **W13** | Redis cache (metadata, query results) | 100-1000× cache hit speedup |

**Do NOT attempt** lazy validation, hot/cold splits, or schema caching until metrics prove they're needed (Phase III+).

---

## Architecture & Design Principles

### 0. Operational Ontology: 5-Layer Model

The system is an **Event-Driven Agent Orchestration OS** (per `mindvault/07-operational-ontology-design.md`):

```
┌─────────────────────────────────────────────┐
│ Layer 5: INTENT      Human input (WorkLog,  │  ← Research team writes daily logs
│                      WorkDirective, Report) │     Agent parses intent + routes
├─────────────────────────────────────────────┤
│ Layer 4: EVENT       Parsed events          │  ← LogSubmitted, DirectiveIssued,
│                      (routing + dispatch)   │     DeadlineApproaching (system),
│                                             │     BlockerDetected (AI-detected)
├─────────────────────────────────────────────┤
│ Layer 3: ACTION      Agent execution        │  ← CoordinatorAI + 9 Specialist
│                      (coordinator +         │     agents (ScopeAgent,
│                      specialists)           │     ScheduleAgent, etc.)
├─────────────────────────────────────────────┤
│ Layer 2: STATE       Project state          │  ← 15 Objects (Project, Task,
│                      (Objects + Links)      │     WorkDirective, Milestone,
│                                             │     Blocker, Decision, etc.)
├─────────────────────────────────────────────┤
│ Layer 1: KNOWLEDGE   Rules + templates      │  ← WBS patterns, governance rules,
│                      (Static Ontology)      │     decision precedents
└─────────────────────────────────────────────┘
```

**Key Insight:** This is NOT a static data model—it's an **operational system** where Layer 5 (human intent) drives Layer 3 (agent actions) which mutate Layer 2 (state) in compliance with Layer 1 (rules).

### 1. SSOT: JSON Schema is Canonical

```
JSON Schema (Draft 2020-12) ← CANONICAL SOURCE OF TRUTH
    ↓
    ├→ Pydantic v2 models (auto-derivable, with validators for governance)
    ├→ PostgreSQL schema (Alembic migrations from JSON structure)
    ├→ Neo4j graph constraints (relationship cardinality from Links)
    ├→ Qdrant vector collections (embeddings for semantic search)
    └→ OpenAPI / Public APIs (auto-generated from schema)
```

- All Objects are defined first as JSON Schema in `ontology/schemas/*.json`
- `x-ontology-version` field in every schema gates SemVer bumps (governance)
- Pydantic models add **business rule validators** (TRL gates, WBS validation, role authority)
- **Roundtrip tests enforce JSON ↔ Pydantic ↔ JSON equivalence** (CI gate—TIER 0 ✓)
- Per `mindvault/11-performance-analysis.md`: Validation is 0.089ms (0.07% of agent latency)—**no performance penalty for strict typing**

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

## Multi-Team Coordination (TIER 1A Weeks 8-14)

### Team Structure for Parallel Work

**TIER 1A involves 3+ backend architects working in parallel:**

```
Backend-Arch-1:
  ├─ Week 8: Extended Objects 1-4 + roundtrip tests
  ├─ Week 9: PostgreSQL schema (Alembic)
  ├─ Week 13: Compliance validators (8/8) + audit logging

Backend-Arch-2:
  ├─ Week 8: Extended Objects 5-7 + roundtrip tests
  ├─ Week 9-10: Neo4j graph schema + Cypher constraints
  ├─ Week 10: Qdrant vector embeddings

DevOps/Backend-3:
  ├─ Week 11: Prometheus instrumentation
  ├─ Week 11: Grafana dashboard + SLO definitions
  └─ Week 11-12: CI/CD integration for metrics

QA + Full Team:
  ├─ Week 12: Integration testing (3DB consistency)
  └─ Week 14: Documentation + handoff
```

### Coordination Points (No Blocking)

| Week | Sync Point | Decision Required |
|------|-----------|------------------|
| **W8 Start** | Extended Objects naming finalized | Confirm 10 object names match schema intent |
| **W9 Mid** | PostgreSQL schema design review | FK relationships must match Neo4j Intent |
| **W10 End** | 3DB integration architecture | Qdrant embeddings must align with PostgreSQL text search |
| **W12 Mid** | Integration test results | Any cascading failures before Week 13 validators |
| **W14 Start** | TIER 1B handoff readiness | Compliance layer locked, governance rules enforced |

### Low-Dependency Sequencing

Extended Objects and 3DB schema development have **minimal blocking dependencies**:

```
✓ Extended Objects can be defined independently
✓ PostgreSQL schema can be written in parallel with Neo4j
✓ Qdrant embeddings can be defined independently
✗ Only Week 12 integration requires all pieces ready
```

**If Backend-Arch-2 is blocked (Neo4j design):** Arch-1 can advance to Week 9 PostgreSQL work immediately. No wait.

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

## TIER 1A Completion Checklist (Weeks 8-14)

### Week 8: Extended Objects & Compliance
- [ ] WorkDirective schema + Pydantic model + 3 roundtrip tests
- [ ] Milestone, Blocker, Decision, Gate, KPI, Artifact, Role, Risk, IP (10 total)
- [ ] Each object: JSON schema + roundtrip test + fixture
- [ ] Compliance validators module created: `ontology/validators/compliance.py` (8/8)
  - [ ] WBS Classification A-H
  - [ ] Cardinality Constraints
  - [ ] Cross-reference Integrity
  - [ ] TRL/CRL Gates (Type A, Type C)
  - [ ] Blocker Cascading
  - [ ] Role Authority Chain
  - [ ] Decision Provenance
  - [ ] Rule Append-Only

### Weeks 9-10: 3DB Schema Deployment
- [ ] PostgreSQL migrations (Alembic): `alembic/versions/001_initial.sql`
  - [ ] Create projects, tasks, work_logs, decisions, blockers, kpis tables
  - [ ] Foreign keys for all relationships
  - [ ] Indexes on (project_type), (owner_id), (due_date), ULID unique
  - [ ] Roundtrip tests: PostgreSQL ↔ Pydantic equivalence
  
- [ ] Neo4j graph schema: `ontology/migrations/graph/001_relationships.cypher`
  - [ ] Node labels (:Project, :Task, :Person, :Milestone, :Blocker, :Decision, :KPI)
  - [ ] Relationships: DECOMPOSES_INTO, ASSIGNED_TO, BLOCKED_BY, MEASURED_BY, PRODUCES, APPLIES_TO
  - [ ] UNIQUE constraints on node IDs
  - [ ] Relationship cardinality constraints
  - [ ] Integration tests: Cypher query validation
  
- [ ] Qdrant vector schema: `ontology/migrations/vector/001_embeddings.py`
  - [ ] Collections: project_embeddings, task_embeddings, decision_embeddings
  - [ ] Vector size 1536 (OpenAI text-embedding-3-small)
  - [ ] Similarity search tests

### Week 11: Observability Infrastructure
- [ ] Prometheus metrics: `ontology/metrics.py`
  - [ ] `ontology_validation_latency_ms` (Histogram)
  - [ ] `ontology_rule_execution_ms` (Histogram)
  - [ ] `ontology_cache_hit_ratio` (Gauge)
  - [ ] `worklog_parse_total` (Counter)
  - [ ] `action_execution_time_ms` (Histogram, by action_type)
  
- [ ] Grafana dashboard: `observability/grafana/ontology-dashboard.json`
  - [ ] 10 panels (latency, success rate, throughput, cache, errors)
  - [ ] SLO thresholds (P99 <1.0ms, cache >70%, error <0.1%)
  
- [ ] SLO definitions: `observability/slo.yaml`
  - [ ] Availability: 99.9%
  - [ ] Latency: P99 < 1.0ms
  - [ ] Error rate: < 0.1%

### Week 12: Integration Testing
- [ ] PostgreSQL ↔ Pydantic roundtrip (5+ tests)
- [ ] Neo4j relationship validation (3+ tests)
- [ ] Qdrant embedding search (2+ tests)
- [ ] End-to-end: WorkLog → Parser → Decision → 3DB (3+ tests)
- [ ] Data consistency validation (cardinality, FK integrity, cascading deletes)
- [ ] **Target: 15+ integration tests passing**

### Week 13: Compliance Validators Deep Dive
- [ ] Implement all 8 validators in `ontology/validators/compliance.py` (~450 lines)
- [ ] 16+ validator unit tests (positive + negative cases)
- [ ] Audit logging for each violation
- [ ] Integration with Pydantic @model_validator decorators

### Week 14: Documentation & Handoff
- [ ] TIER 1A Completion Report: `docs/03-analysis/ontology-tier1a.analysis.md`
- [ ] TIER 1B Scope Definition: `mindvault/ontology/12-tier1b-agent-orchestration.md`
- [ ] Updated CLAUDE.md with TIER 1A metrics
- [ ] Handoff checklist to TIER 1B team (9 items)

### Success Criteria (Definition of Done)
- [x] 93 tests passing (TIER 0 baseline)
- [ ] 42 new integration tests (TIER 1A target)
- [ ] 100% data flow coverage (WorkLog → PostgreSQL → Neo4j → Qdrant)
- [ ] Prometheus metrics live in CI/CD
- [ ] Grafana dashboard operational
- [ ] All 8 compliance validators active
- [ ] Zero regression in validation latency (<1.0ms P99)

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

## Ontology State Machine & Event Dispatch (TIER 1B Preview)

**Context:** TIER 1A locks the ontology state; TIER 1B adds agent-driven state transitions.

### Object Lifecycle States

```
Project:
  NEW → PLANNING → APPROVED → ACTIVE → PAUSED → CLOSED
  
Task:
  NEW → SCHEDULED → IN_PROGRESS → BLOCKED* → COMPLETED
  (* blocked = Blocker exists)
  
WorkDirective:
  ISSUED → IN_PROGRESS → COMPLETED | DEFERRED
  
Decision:
  PROPOSED → APPROVED → IMPLEMENTED | ARCHIVED
```

### Event → Action Routing (TIER 1B Implementation)

Per `mindvault/07-operational-ontology-design.md`, these dispatch rules must be enforced:

```yaml
LogSubmitted Event Handler:
  1. Parse natural language (Parser.extract_intent + Parser.extract_entities)
  2. Link to existing Objects (Tasks, Milestones)
  3. IF blockers mentioned → DetectBlocker Action
  4. IF new risks → IdentifyRisk Action
  5. IF plan_tomorrow exists → ScheduleTasks Action
  6. IF deliverable mentioned → UpdateDeliverable Action
  7. Always → RecordDecision (auto-provenance)

DirectiveIssued Event Handler:
  1. Validate authority chain (Role → hierarchy check)
  2. Parse directive content
  3. Create WorkDirective object + link
  4. Decompose into Tasks
  5. Assign to addressees
  6. Notify recipient

DeadlineApproaching Event Handler (system-triggered):
  1. Check progress of target
  2. IF at-risk → alert owner + propose mitigation
  3. IF critical → EscalateIssue
```

### Integration Point: TIER 1A ↔ TIER 1B

TIER 1A must ensure:
- [x] Object state enums are complete (NEW, ACTIVE, COMPLETED, etc.)
- [x] All relationships are defined (DECOMPOSES_INTO, BLOCKED_BY, APPLIES_TO, etc.)
- [x] Validators enforce state machine transitions (no invalid state combos)
- [x] Decision provenance chain works (every action → auto decision)
- [x] Role authority is validated (authority chain enforced)

TIER 1B will add:
- [ ] Event dispatcher (route LogSubmitted → ScopeAgent, etc.)
- [ ] Specialist agents (9 agents parallel dispatch)
- [ ] State machine transitions (Task: SCHEDULED → IN_PROGRESS)
- [ ] Feedback loop (completed action → next event)

---

## Testing Best Practices (TIER 0 & Beyond)

1. **Roundtrip is the SSOT sentinel**: If `test_roundtrip.py` passes, JSON ↔ Pydantic equivalence is guaranteed.
2. **Enum matching is enforced**: `test_schema_shape.py` ensures Python enums match JSON exactly.
3. **Schema validity is checked**: Every schema must be a valid Draft 2020-12 document.
4. **Negative tests matter**: Test both valid data (positive) and constraint violations (negative).
5. **Integration tests validate cascading**: Block detection, role authority, cross-references.

Example negative test pattern:
```python
with pytest.raises(ValueError, match="requires 'trl_target'"):
    Project.model_validate({...project_type: "A", no trl_target...})
```

Example integration test pattern (TIER 1A):
```python
def test_blocker_cascading_to_dependent_tasks():
    # Create Task A → Task B → Task C chain
    # Block Task A
    # Verify Task B, C receive blocker cascade notification
    # Verify decision auto-created
```

---

## Quick Reference: Key Files by Purpose

### Core Ontology (TIER 0 — Complete)
| File | Purpose |
|------|---------|
| `ontology/schemas/project.json`, `task.json`, `worklog.json`, `person.json`, `event.json` | SSOT (JSON Schema Draft 2020-12) |
| `ontology/models/core.py` | Core 5 objects + business rule validators |
| `ontology/models/actions.py` | 11 Action types (CreateTask, UpdateStatus, LogWork, etc.) |
| `ontology/models/links.py` | 8 Link types (DependsOn, Produces, Blocks, etc.) |
| `ontology/parser.py` | WorkLog → WorkDirective → Action → Event pipeline (T0-4) |

### Extended Ontology (TIER 1A — In Progress)
| File | Purpose |
|------|---------|
| `ontology/schemas/workdirective.json`, `milestone.json`, `blocker.json`, etc. | 10 extended object schemas (Weeks 8) |
| `ontology/models/extended.py` | 10 extended Pydantic models (Week 8) |
| `ontology/validators/compliance.py` | 8 compliance validators (Week 13) |
| `ontology/migrations/001_initial.sql` | PostgreSQL schema (Week 9) |
| `ontology/migrations/graph/001_relationships.cypher` | Neo4j relationships (Week 9-10) |
| `ontology/migrations/vector/001_embeddings.py` | Qdrant vectors (Week 10) |
| `ontology/metrics.py` | Prometheus instrumentation (Week 11) |
| `observability/grafana/ontology-dashboard.json` | Grafana dashboard (Week 11) |

### Testing (TIER 0 & 1A)
| File | Purpose |
|------|---------|
| `ontology/tests/unit/test_roundtrip.py` | JSON ↔ Pydantic equivalence tests (TIER 0: 43 tests) |
| `ontology/tests/unit/test_parser.py` | Parser pipeline tests (TIER 0: 16 tests) |
| `ontology/tests/integration/test_postgres_roundtrip.py` | PostgreSQL integration (TIER 1A: 5+ tests) |
| `ontology/tests/integration/test_neo4j_consistency.py` | Neo4j integration (TIER 1A: 3+ tests) |
| `ontology/tests/integration/test_e2e_ontology.py` | End-to-end flow (TIER 1A: 3+ tests) |

### Strategy & Architecture (Mindvault)
| File | Purpose |
|------|---------|
| `mindvault/decisions/001-ontology-strategy.md` | ADR-001: Ontology vision + MVP scope |
| `mindvault/ontology/06-ontology-design-charter.md` | Design principles + governance rules (7 principles + P1-P4) |
| `mindvault/ontology/07-operational-ontology-design.md` | 5-layer event-driven OS + agent orchestration |
| `mindvault/ontology/10-project-type-classification-v2.md` | WBS classification (A-H types) for compliance validation |
| `mindvault/ontology/11-performance-analysis.md` | Benchmarks + anti-patterns (validation is 0.07% of latency) |

### Configuration
| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies (Pydantic, pytest, mypy, ruff), test config |
| `docker-compose.dev.yml` | Local PostgreSQL 16 + Neo4j 5 + Qdrant + Redis setup |
| `.claude/rules/python/testing.md` | pytest conventions for this project |
| `.claude/rules/python/patterns.md` | Python-specific design patterns |

---

## When in Doubt

- **Schema questions?** See `ontology/README.md` and `mindvault/decisions/001-ontology-strategy.md`
- **Governance + compliance?** See `mindvault/ontology/06-ontology-design-charter.md` (7 principles + 4 performance principles)
- **Event dispatch + agent design?** See `mindvault/ontology/07-operational-ontology-design.md` (5-layer model + event routing)
- **Performance optimization decisions?** See `mindvault/ontology/11-performance-analysis.md` (validation is 0.07% latency—don't over-optimize)
- **WBS validation rules?** See `mindvault/ontology/10-project-type-classification-v2.md`
- **Test failures?** Check:
  - ULID format: must be 26 chars, pattern `^[0-9A-HJKMNP-TV-Z]{26}$`
  - Enum values: Python enum must match JSON schema exactly
  - Roundtrip: JSON → Pydantic → JSON must be identical
- **Multi-team coordination (TIER 1A)?** See "Multi-Team Coordination" section above
- **Run tests locally:** `pytest ontology/tests/ -v` after `pip install -e ".[dev]"`

