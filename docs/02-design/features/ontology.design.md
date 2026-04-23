# Ontology Implementation Design

**Document ID:** ontology.design.md  
**Version:** 2.0.0  
**Status:** Active (Phase I Complete, Phase II Planned)  
**Last Updated:** 2026-04-22  
**Layer:** L2.5 (Typed Concepts + Object/Link/Action)

---

## 1. Context

### Strategic Motivation

**RAPai (Research AI Platform)** is an AI-Native R&D Project Management system designed to autonomously manage research projects from ideation to commercialization. The ontology layer serves as the Single Source of Truth (SSOT) for all downstream systems:

- Pydantic v2 data models (runtime validation)
- PostgreSQL relational schemas (persistence)
- Neo4j graph constraints (relationship integrity)
- OpenAPI contracts (external APIs)
- LLM system prompts (automatic agent configuration)

### Problem Statement

Without a formal ontology:
- AI agents cannot reliably extract intent from unstructured input (work logs, directives)
- Cross-system data inconsistencies emerge (schema ≠ model ≠ database)
- Governance rules (SemVer, append-only) cannot be enforced
- Compliance and traceability requirements (PROV-O lineage, security tiers) remain ad-hoc

### Design Principles (from ADR-001 & 06-Design-Charter)

1. **JSON Schema is SSOT** — All downstream artifacts (Pydantic, migrations, OpenAPI) derive from schema
2. **Append-Only Core** — No field deletion; use deprecation + versioning
3. **SemVer Governance** — Breaking changes require MAJOR version bumps + migration scripts
4. **Object-Centric** — All real-world entities model as Objects; all state changes via Actions
5. **Kinetic Ontology** — Agents drive state transitions through explicit Actions (Write-back Discipline)
6. **Standard Reuse** — PROV-O, CloudEvents 1.0, FOAF, OWL-Time, BPMN 2.0 integration
7. **LLM-First Readability** — Semantic structure must be navigable by AI (no opaque foreign keys)

---

## 2. Overview

### Scope

**Phase I (Complete):** 5 Core Objects + 25+ Enums + JSON Schema SSOT + Roundtrip Tests
- Project (8 WBS types, conditional TRL/CRL, cross-cutting attributes)
- Task (WBS hierarchy, dependency tracking, no self-references)
- WorkLog (13 daily report tags, LLM parser input, PROV-O support)
- Person (FOAF compatible, security clearance levels)
- Event (CloudEvents 1.0 envelope, PROV-O lineage, LLM confidence)

**Phase II (Planned):** 10 Extended Objects + 8 Link types + Compliance validators
- WorkDirective (6-state machine: created→validated→dispatched→in_progress→completed/failed)
- Role, Milestone, Blocker, Decision, Gate, KPI, Artifact, Risk, IP
- Links.json (20+ cardinality rules)
- Compliance rules (WBS cycle detection, cross-reference integrity)

**Phase III (Future):** Neo4j + PostgreSQL migrations, Alembic versioning, Qdrant vector schema

### Key Deliverables

| Artifact | Location | Status |
|----------|----------|--------|
| **JSON Schemas** | `ontology/schemas/*.json` (21 files) | ✅ Phase I done, Phase II in progress |
| **Pydantic Models** | `ontology/models/core.py`, `extended.py` | ✅ Phase I done, Phase II 70% |
| **Enums** | `ontology/models/enums.py` | ✅ 25+ enums complete |
| **Governance Validator** | `ontology/validators/governance.py` | ✅ SemVer + append-only enforcer |
| **Rule Engine** | `ontology/rules/engine.py` + registry | ✅ 13 SBVR rules implemented |
| **Roundtrip Tests** | `ontology/tests/unit/test_roundtrip.py` | ✅ 13/13 passing |
| **Schema Validation Tests** | `ontology/tests/unit/test_schema_shape.py` | ⚠️ 20/21 passing (1 metadata fix needed) |
| **E2E Parsing Pipeline** | `ontology/parsing/`, `ontology/rules/` | ✅ 235 tests, 64% coverage |

---

## 3. Architecture

### 3.1 Layered Ontology Stack (08-Stack-Catalog)

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 8: Meta-Ontology (Governance)                         │
│   - SemVer enforcement, Append-only validation, Audit trail │
├──────────────────────────────────────────────────────────────┤
│ Layer 7: Agent Capability & Communication                   │
│   - Intent definitions, LLM prompt templates                 │
├──────────────────────────────────────────────────────────────┤
│ Layer 6: Event & Action Taxonomy (Phase II)                 │
│   - Intent: 13 ParsingIntent, 10 Action types               │
│   - Entity: 10 types (task, person, date, duration, ...)    │
│   - 4 Artifact types: WorkLog, WorkDirective, WorkPlan, ...  │
├──────────────────────────────────────────────────────────────┤
│ Layer 5: Work Activity Ontology (NL-First, 09-Activity)    │
│   - 4 primary artifacts + NLP 8-stage pipeline              │
│   - Feedback-loop learning (correction pairs → fine-tuning)  │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Actor/Role/Authority (Phase II)                    │
│   - Person (FOAF), Role (10 types), Team, Stakeholder       │
│   - Delegation matrix, ABAC attributes                      │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: R&D Project Domain (Phase I/II, 10-Classification) │
│   - Project (8 WBS types + cross-cutting attributes)        │
│   - Task, Milestone, Gate, KPI, Artifact, Blocker, ...      │
│   - contract_research: 6-phase workflow + L2-C gate         │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: Knowledge/Document (Phase II+)                     │
│   - Decision, Document, FAQ, Template, Rule Repository      │
│   - Dublin Core, SKOS for classification                    │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: Upper (Time, PROV-O, Foundational)                 │
│   - OWL-Time (temporal expressions)                         │
│   - W3C PROV-O (causality, attribution, delegation)         │
│   - DublinCore (metadata)                                   │
└──────────────────────────────────────────────────────────────┘
```

**Reuse vs Custom Development:**
- Layer 1-2: 95% reuse (standards)
- Layer 3: 40% reuse, 60% custom (R&D domain specifics)
- Layer 4: 50% reuse, 50% custom (role/governance)
- Layer 5: 20% reuse, 80% custom (work activity NLP)
- Layers 6-8: 40-60% reuse, balanced

### 3.2 JSON Schema SSOT Pattern

```
JSON Schema (Draft 2020-12)
    ↓ [definitive source]
    ├→ Pydantic v2 models (auto-derivable OR hand-validated)
    ├→ PostgreSQL migrations (Alembic + jsonschema_to_sql)
    ├→ Neo4j Cypher constraints (from neo4j_constraint field)
    ├→ OpenAPI/FastAPI schemas (@app.openapi())
    └→ LLM system prompts (auto-injected via LLM-Prompt-Binding R4)

Critical Rule: No reverse flow
- ❌ Never modify Pydantic without updating JSON Schema first
- ❌ Never update database without schema versioning
- ✅ Always: JSON Schema → Pydantic → Migrations → OpenAPI
```

### 3.3 Core Objects (Phase I - Complete)

#### **Project**
```json
{
  "properties": {
    "project_id": "ULID (26 chars)",
    "name": "string",
    "project_type": "A|B|C|D|E|F|G|H (WBS axis 1)",
    "cross_cutting": {
      "contract_modality": "internal_rd | public_grant | contract_research",
      "funding_source": "government | private | self | mixed",
      "security_tier": "PUBLIC | RESTRICTED | CONFIDENTIAL | SECRET",
      "scale_tier": "small | medium | large"
    },
    "status": "draft | active | on_hold | completed | cancelled",
    "start_date": "ISO8601",
    "trl_target": "1-9 (if type A/B)",
    "crl_target": "1-9 (if type C)",
    "current_trl": "integer (Phase III)",
    "trl_progression_history": "[{trl, date, evidence_worklog_id}] (Phase III)"
  },
  "required": ["project_id", "name", "project_type", "cross_cutting", "status"],
  "x-ontology-version": "0.3.0",
  "x-ontology-layer": "L2.5"
}
```

**Business Rules (Pydantic validators):**
- Type A/B → `trl_target` mandatory
- Type C → `crl_target` mandatory
- contract_research overlay → L2-C Client Acceptance gate (Rule Engine)
- TRL/CRL progression append-only (no regression in history)

#### **Task**
```json
{
  "properties": {
    "task_id": "ULID",
    "project_id": "ULID (foreign key)",
    "wbs_code": "regex: ^[0-9]+(\\.[0-9]+)*$",
    "title": "string",
    "status": "planned | in_progress | blocked | done | cancelled",
    "parent_task_id": "ULID | null",
    "depends_on_task_ids": "[ULID]",
    "deliverable_artifact_ids": "[ULID]"
  },
  "x-ontology-version": "0.3.0"
}
```

**Business Rules:**
- No self-reference: `task_id ≠ parent_task_id`
- No cycles: transitive closure check on `depends_on_task_ids`
- Unique WBS code per project

#### **WorkLog**
```json
{
  "properties": {
    "log_id": "ULID",
    "task_id": "ULID",
    "author_person_id": "ULID",
    "date": "ISO8601",
    "content": "string (≤32KB)",
    "tags": ["DONE", "ISSUE", "TRL_UP", "CRL_UP", "TIME", "COST", "IP", "ASSIGN", "DELIVERABLE", "EXPERIMENT", "MGT", "DO", "REV"],
    "trl_observed": "integer (optional)",
    "crl_observed": "integer (optional)",
    "prov_id": "W3C PROV-O URI (optional)"
  },
  "x-ontology-version": "0.1.0"
}
```

**Business Rules:**
- Tags must be unique within single log
- If `trl_observed` or `crl_observed` set, require evidence artifacts
- If `prov_id` set, link to originating decision/artifact

#### **Person**
```json
{
  "properties": {
    "person_id": "ULID",
    "name": "string",
    "security_clearance": "PUBLIC | RESTRICTED | CONFIDENTIAL | SECRET",
    "email": "RFC5321 email",
    "role_ids": "[ULID]",
    "foaf_uri": "URI (optional, interoperability)"
  },
  "x-ontology-version": "0.1.0"
}
```

**Business Rules:**
- security_clearance is rank-ordered (PUBLIC < RESTRICTED < ... < SECRET)
- Active person cannot have empty role_ids
- Email is unique per instance

#### **Event**
```json
{
  "properties": {
    "id": "ULID",
    "specversion": "1.0 (CloudEvents)",
    "type": "string (reverse-DNS: com.rapai.ontology.worklog.submitted)",
    "source": "URI",
    "subject": "string (optional)",
    "time": "ISO8601 with timezone",
    "data": "JSON object (event payload)",
    "datacontenttype": "application/json",
    "prov_id": "W3C PROV-O: prov:wasGeneratedBy URI",
    "actor_person_id": "ULID (optional, human actor)",
    "actor_agent_id": "AG-xxx (optional, AI agent actor, starts with AG-)",
    "model_id": "string (optional, LLM model name if AI-sourced)",
    "confidence": "float 0.0-1.0 (LLM confidence, if applicable)"
  },
  "x-ontology-version": "0.1.0"
}
```

**Business Rules:**
- If `actor_agent_id` starts with `AG-`, then `model_id` must be present (LLM provenance)
- PROV-O `prov_id` traces back to decision, artifact, or rule that generated event
- Events are immutable (append-only)

### 3.4 Extended Objects (Phase II - 70% Complete)

#### **WorkDirective** (6-state machine)
```python
class WorkDirective(_OntologyObject):
  directive_id: Identifier
  parent_id: Identifier | None  # Parent directive (delegation chain)
  intent: Intent  # create_task, update_status, log_work, validate_gate, ...
  entities: list[str]  # Task IDs, Person IDs affected
  due_date: datetime | None
  status: WorkDirectiveStatus  # created → validated → dispatched → in_progress → completed/failed
  
  source_worklog_id: Identifier | None  # Derived from WorkLog parsing
  source_rule_ids: list[str]  # Rule IDs that generated this directive
  created_at: datetime
  updated_at: datetime
```

**Dispatch Rules (R010):**
- `intent` must be valid (13 enum values)
- `entities` must exist in ontology
- Circular parent chains prohibited
- Dispatched directives are immutable

#### **Role, Milestone, Blocker, Decision, Gate, KPI, Artifact, Risk, IP** (to be detailed in Phase II)

### 3.5 Enums (25+ Types)

| Category | Enums | Count |
|----------|-------|-------|
| **Project Axis** | ProjectTypeCode, ContractModality, FundingSource, SecurityTier, ScaleTier | 5 |
| **Workflow** | TaskStatus, ProjectStatus, BlockerStatus, DecisionStatus | 4 |
| **Intent & Action** | Intent, ParsingIntent | 2 |
| **Gate & KPI** | GateLevel, GateStatus, KPITier | 3 |
| **Daily Tags** | DailyReportTag | 1 |
| **Artifact & IP** | ArtifactType, ArtifactStatusExtended, IPType, IPStatus | 4 |
| **Risk & Severity** | RiskCategory, Severity, Likelihood | 3 |
| **Advanced** | WorkDirectiveStatus, RoleType | 2 |

**Enum Validation Rule (test_schema_shape.py):**
All Python enums in `ontology/models/enums.py` must match their corresponding JSON Schema definitions byte-for-byte.

### 3.6 Governance Enforcement

#### **SemVer + Append-Only Validator** (`validators/governance.py`)

```python
def compare_schemas(old: dict, new: dict) -> Diff:
  """
  Detect breaking changes:
  - Field removal
  - Enum value removal
  - Constraint narrowing (maxLength ↓, minLength ↑)
  - required field addition
  - additionalProperties: true → false
  
  Return: Diff(severity="major"|"minor"|"patch"|"none", changes=[...])
  """

def validate_semver_bump(old_version: str, new_version: str, diff: Diff):
  """
  Enforce version bump matches change severity:
  - Breaking (MAJOR) → requires MAJOR bump
  - Minor (non-breaking additions) → requires MINOR+ bump
  - Patch (docs only) → allows PATCH+ bump
  - Raises on non-monotonic version (e.g., 0.2.0 → 0.1.5)
  """
```

**CI Gate:**
Every schema change triggers:
1. JSON Schema validity check (Draft 2020-12)
2. SemVer diff computation
3. Version bump validation (block if mismatch)
4. Roundtrip test (JSON → Pydantic → JSON equivalence)

---

## 4. Implementation Phases

### Phase I: Foundation (✅ Complete)

**Goals:** Establish SSOT, enforce roundtrip tests, achieve 64% coverage

**Deliverables:**
- ✅ 5 core objects + JSON schemas (v0.1-0.3)
- ✅ 25+ enums with Python equivalence
- ✅ Pydantic v2 models + strict validation
- ✅ 13/13 roundtrip tests passing
- ✅ SemVer + append-only validator
- ✅ 13 SBVR business rules in Rule Engine
- ✅ 235 unit + integration tests (64% coverage)

**Key Commits:**
- `feat(ontology): Add P0 enhancements (Constraints, Provenance, WorkDirective State)` — 0.3.0
- `feat(ontology): Add TRL/CRL state management infrastructure for Phase III W2-W3`
- `feat(ontology): Implement Phase III W1-W2 Constraint/Rule Engine with 13 core SBVR rules`
- `feat: Phase II complete - Extended 10 Objects + Links + Actions`

### Phase II: Extended Objects & Compliance (🔄 In Progress)

**Goals:** Add 10 extended objects, 8 link types, 13 compliance rules

**W1-W2:**
- [ ] Finalize 10 extended object schemas (WorkDirective, Role, Milestone, Blocker, Decision, Gate, KPI, Artifact, Risk, IP)
- [ ] Define 8 link types + cardinality rules (links.json)
- [ ] Create Pydantic models for extended objects (extended.py 100%)
- [ ] Add WBS cycle detection validator
- [ ] Fix `definitions_of_done.json` metadata (x-ontology-version)

**W3-W4:**
- [ ] Write 40+ compliance rule tests
- [ ] Implement cross-reference integrity checks
- [ ] Add E2E integration tests (PostgreSQL, Neo4j lookups)
- [ ] Document 6-phase contract_research workflow

**W5:**
- [ ] Achieve 80%+ overall test coverage
- [ ] SemVer bump to v1.0.0 (breaking: deprecated fields removed)
- [ ] Generate OpenAPI schema from ontology

### Phase III: Persistence & Knowledge (📅 Q2 2026)

**Goals:** Implement PostgreSQL + Neo4j + Qdrant persistence

**Components:**
- Alembic migrations (JSON Schema → PostgreSQL DDL)
- Neo4j Cypher schema + graph constraints
- Qdrant vector embeddings (semantic search)
- Outbox pattern for event-driven updates
- PROV-O lineage tracing (complete audit trail)

---

## 5. Design Decisions

### D1: JSON Schema as SSOT (ADR-001 R5)
**Decision:** All downstream artifacts derive from JSON Schema; reverse updates forbidden.  
**Rationale:** Single mutation point prevents schema/model/database drift.  
**Impact:** Pydantic models are code-generated (or hand-validated); schema changes trigger cascading migrations.

### D2: Append-Only Governance (ADR-001 R2)
**Decision:** Fields never deleted; deprecation + new versions instead.  
**Rationale:** Ensures backward compatibility for external systems consuming ontology.  
**Impact:** Schema size grows; migration burden falls on deletion → add-with-default.

### D3: Kinetic Layer: Actions Not Objects (06-Design-Charter)
**Decision:** State changes only via explicit Actions (WorkDirective, Rule evaluation); never direct object mutation.  
**Rationale:** Enables reversibility, audit trail, and permission enforcement.  
**Impact:** All mutations routed through WorkDirective → Rule Engine pipeline; requires state machine discipline.

### D4: contract_research as Cross-cutting (10-Classification v2.0, ADR-002 D22)
**Decision:** Academic research contracts modeled as cross-cutting overlay (Axis 2 attribute) not new WBS type.  
**Rationale:** Same WBS structure (A–H) applies; only gate rules (L2-C Client Acceptance) and KPI weights change.  
**Impact:** Reduces ontology explosion; enables single codebase for all project types.

### D5: 13-Tag WorkLog (09-Activity-Ontology)
**Decision:** 13 predefined daily report tags (DONE, ISSUE, TRL_UP, etc.) captured at parse time.  
**Rationale:** Structured tags enable Intent extraction without full NLP; tags are human-familiar.  
**Impact:** Reduces LLM hallucination risk; enables offline rule evaluation.

### D6: LLM Prompt Auto-Binding (ADR-001 R4)
**Decision:** Ontology enums + object names automatically injected into LLM system prompts.  
**Rationale:** Agents always have latest schema definition; no manual prompt updates needed.  
**Impact:** Semantic versioning of prompts tied to ontology version; drift detection trivial.

---

## 6. Validation & Testing

### 6.1 Test Coverage Target: 80%+

**Current Status:** 64% (235 tests)

**By Module:**
- `ontology/models/enums.py` — 100% ✓
- `ontology/parsing/intent_classifier.py` — 98% ✓
- `ontology/rules/engine.py` — 86% ✓
- `ontology/validators/governance.py` — **0% ⚠️** (needs integration tests)

### 6.2 Critical Test Gates

1. **Roundtrip (13 tests)**
   ```python
   for fixture in [project, task, worklog, person, event]:
       json_data = load_fixture(fixture)
       assert schema_validate(json_data, schema)
       model = Model.model_validate(json_data)
       assert model.model_dump_json() == json_data  # bit-exact equivalence
   ```

2. **Schema Validation (20 tests)**
   - Every schema is Draft 2020-12 valid
   - Every schema declares `x-ontology-version`
   - Python enums match JSON enums (12 checks)

3. **Rule Engine (27 tests)**
   ```python
   # Example: R010 WorkDirective intent validation
   assert engine.evaluate(WorkDirective(intent="invalid")) == RuleViolation(
       rule_id="R010", severity="MUST", reason="invalid intent type"
   )
   ```

4. **Governance (to implement)**
   ```python
   # Example: SemVer validation
   diff = compare_schemas(v0_1_0, v0_2_0)
   assert diff.severity == "minor"
   validate_semver_bump("0.1.0", "0.2.0", diff)  # passes
   validate_semver_bump("0.1.0", "0.1.1", diff)  # raises
   ```

### 6.3 E2E Validation

**Korean Corpus (35 samples):**
- 25 samples: 13 Intent types (2 per type)
- 10 edge cases: coreference, negation, ambiguity
- Target accuracy: ≥80%

```bash
pytest ontology/tests/e2e/test_pipeline_e2e.py -v
# Expected: 35 passed, intent classification F1≥0.80, entity extraction F1≥0.75
```

---

## 7. Critical Files & Paths

| File | Purpose | Status |
|------|---------|--------|
| `ontology/schemas/*.json` | JSON Schema SSOT (21 files) | ✅ Phase I, Phase II 70% |
| `ontology/models/core.py` | Pydantic core objects | ✅ |
| `ontology/models/extended.py` | Pydantic Phase II objects | ⚠️ 70% (Role, WorkDirective missing) |
| `ontology/models/enums.py` | 25+ Python enums | ✅ |
| `ontology/validators/governance.py` | SemVer + append-only enforcer | ✅ |
| `ontology/rules/engine.py` | Rule Engine + SBVR evaluator | ✅ |
| `ontology/parsing/intent_classifier.py` | Intent extraction (13 types) | ✅ |
| `ontology/parsing/entity_extractor.py` | Entity NER (10 types) | ✅ |
| `ontology/tests/unit/test_roundtrip.py` | Roundtrip validator (13 tests) | ✅ |
| `ontology/tests/unit/test_schema_shape.py` | Schema validation (20/21 tests) | ⚠️ |
| `ontology/tests/e2e/test_pipeline_e2e.py` | E2E parsing (35 samples) | ✅ |
| `mindvault/decisions/001-ontology-strategy.md` | ADR: SSOT + MVP scope | 📖 |
| `mindvault/ontology/06-ontology-design-charter.md` | Governance rules | 📖 |
| `mindvault/ontology/10-project-type-classification-v2.0.md` | WBS 8-type + cross-cutting | 📖 |

---

## 8. Migration Path (Phase I → Phase II)

### Breaking Changes to v1.0.0
Once Phase II is complete, SemVer MAJOR bump to v1.0.0 requires:
1. Removing deprecated fields (none yet, but planned for Phase III)
2. Finalizing enum lists (no more additions allowed)
3. Locking JSON Schema structure (no property reordering)

### Migration Script Template
```python
# ontology/migrations/v0_x_to_v1_0.py
def migrate_project_v0_to_v1(old_json: dict) -> dict:
    # Add any default values for new required fields
    # Remap enum values if changed
    # Validate new schema
    return new_json
```

---

## 9. Verification Checklist

Before marking Phase II complete:

- [ ] All 10 extended objects have JSON schemas + Pydantic models
- [ ] 8 link types defined + cardinality rules tested
- [ ] 40+ compliance rules written + tested (≥80% coverage on rules/*)
- [ ] definitions_of_done.json metadata fixed
- [ ] All roundtrip tests pass (13/13)
- [ ] All schema validation tests pass (21/21)
- [ ] E2E parsing accuracy ≥80%
- [ ] SemVer governance enforced in CI
- [ ] OpenAPI schema auto-generated from ontology
- [ ] LLM prompt auto-binding tested (system prompts include schema snapshot)
- [ ] Documentation complete (README + design doc)

---

## 10. Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Test Coverage | 80%+ | 64% | 🟡 On track |
| Roundtrip Pass Rate | 100% | 13/13 (100%) | ✅ |
| Schema Validity | 100% | 20/21 (95%) | 🟡 1 fix needed |
| Enum Match Accuracy | 100% | 12/12 (100%) | ✅ |
| Rule Engine Tests | 27+ | 27/27 (100%) | ✅ |
| SemVer Enforcement | Automated | Implemented | ✅ |
| E2E Parsing Accuracy | ≥80% | TBD (35 samples) | 🔄 |
| Phase II Schedule | 5 weeks | Week 3 | 🟡 On track |

---

## 11. Appendices

### A. JSON Schema Metadata Convention

Every schema declares:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Project",
  "description": "...",
  "type": "object",
  "x-ontology-version": "0.3.0",
  "x-ontology-layer": "L2.5",
  "x-ontology-status": "stable|experimental|deprecated"
}
```

### B. Pydantic Model Template (Phase II)

```python
from pydantic import BaseModel, Field, field_validator

class WorkDirective(_OntologyObject):
    directive_id: Identifier = Field(..., description="Unique identifier (ULID)")
    intent: Intent = Field(..., description="Action intent type (13 enum values)")
    
    @field_validator('directive_id')
    @classmethod
    def validate_ulid(cls, v: str) -> str:
        if not re.match(r'^[0-9A-HJKMNP-TV-Z]{26}$', v):
            raise ValueError("Invalid ULID format")
        return v
    
    @model_validator(mode='after')
    def validate_intent(self) -> 'WorkDirective':
        if self.intent not in Intent.__members__.values():
            raise ValueError(f"Invalid intent: {self.intent}")
        return self
```

### C. Ontology Version History

| Version | Date | Changes | Type |
|---------|------|---------|------|
| 0.1.0 | 2026-04-18 | Initial 5 core objects | Foundation |
| 0.2.0 | 2026-04-19 | Add TRL/CRL progression history | Minor |
| 0.3.0 | 2026-04-22 | Add Phase II schemas + Rule Engine | Minor |
| 1.0.0 | 2026-Q2 | Finalize extended objects, remove deprecated fields | **MAJOR** |

---

## 12. References

- **ADR-001:** Ontology Strategy (SSOT, MVP scope, standard reuse)
- **ADR-002:** AI Model Architecture (5-Tier Hybrid, LLM routing, contract_research first-class)
- **06-Design-Charter:** Governance rules (Object-Centric, Kinetic Layer, Write-back Discipline)
- **07-Operational-Design:** Event-Driven OS (5-Layer, Coordinator + Specialist agents)
- **08-Stack-Catalog:** Ontology stack layers (54% reuse, 46% custom, MVP 10 weeks)
- **09-Activity-Ontology:** Work activity design (13 tags, 10 intents, NL-first parsing)
- **10-Classification-v2.0:** Project type + contract_research cross-cutting
- **CLAUDE.md:** Quick start guide, Phase I/II checklists, troubleshooting

---

**Document Status:** APPROVED for Phase II implementation  
**Next Review:** 2026-04-29 (EOW Phase II W1-W2)
