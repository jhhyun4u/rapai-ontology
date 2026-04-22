# Ontology User-Centric Gaps — Planning Document

> **Summary**: Address 5 critical gaps in the RAPai ontology identified through R&D end-user workflow analysis — budget/cost tracking, team/resource allocation, approval workflow, document management, and reporting support — to make the system usable for real Korean R&D project management contexts.
>
> **Project**: RAPai (Research AI Platform)
> **Version**: L2.5 Ontology — Phase II Enhancement
> **Author**: Product Manager Agent
> **Date**: 2026-04-22
> **Status**: Draft — Awaiting CTO Approval

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | Phase I ontology (5 core objects) is academically sound but lacks 5 critical capabilities that R&D practitioners need daily: budget tracking, team resource allocation, approval workflow, document management, and dashboard reporting. Contract research projects cannot be managed without these. |
| **Solution** | Introduce targeted schema extensions and 5 new Phase II objects (Budget, TeamAssignment, Approval, Document, and Dashboard Query spec) alongside clarifications to WorkDirective, Blocker, and governance mode. |
| **Function/UX Effect** | Research PMs can run a full 12-month government-funded contract project without switching to Excel for budget, resource allocation, or approval chains. Researchers get a lighter logging experience with guided tag selection rather than memorizing 13 codes. |
| **Core Value** | Transform the ontology from a technically correct schema into a system that practitioners voluntarily adopt because it reduces their coordination overhead rather than adding to it. |

---

## Context Anchor

> Auto-generated from Executive Summary. Propagated to Design/Do documents for context continuity.

| Key | Value |
|-----|-------|
| **WHY** | 5 core objects alone cannot support contract research or government-funded R&D project management — PMs resort to external tools, defeating the Digital Twin goal |
| **WHO** | Research project managers (PM), program directors, team leads, researchers in Korean public R&D institutions managing government-funded or contract research projects |
| **RISK** | Adding objects too aggressively creates ontology bloat; insufficient additions leave core use cases broken — must scope each gap to minimum viable schema additions |
| **SUCCESS** | A PM can run a 12-month contract research project (budget, team, approvals, milestones, gates) entirely within the system without an Excel workaround |
| **SCOPE** | Phase II-A (must-have): Budget fields + TeamAssignment + Approval objects; Phase II-B (should-have): Document object + Dashboard query spec; Phase III (defer): Full approval UI, notification engine |

---

## 1. Overview

### 1.1 Purpose

The RAPai ontology Phase I delivers a structurally rigorous foundation (JSON Schema SSOT, 5 core objects, 13 SBVR rules, 235 tests). However, an end-user workflow review against real Korean R&D project management patterns reveals that the system scores approximately 6/10 for user fit in its current state. This plan defines the requirements to close the 5 critical gaps before Phase II development proceeds, ensuring that the additional 10 planned objects actually address practitioner needs rather than only technical completeness.

### 1.2 Background

The review assessed three representative use cases:

- **Use Case A — Contract Research (Government-funded, 12 months):** PM cannot track budget, get approval signatures, or attach specification documents. The `contract_research` overlay in cross_cutting references an L2-C Client Acceptance Gate, but there is no Gate object, no budget object, and no approval object in Phase I. Rating: Phase I is insufficient; Phase II objects (Milestone, Gate, Decision) are the minimum, Budget/Approval are critical additions.

- **Use Case B — TRL Progression:** Project has `trl_target` and `current_trl` fields. However, there is no mechanism to validate that evidence is sufficient before advancing TRL. The `AdvanceTRL` Action in the charter requires `evidence.count >= 2`, but the Artifact/Document object to hold that evidence does not yet exist. Rating: Partial — schema supports intent but evidence linking is missing.

- **Use Case C — Team Coordination:** Task has a single `assignee` field. Five researchers on one task have no way to declare their individual roles or allocation percentages. Resource conflict detection (person assigned to 3 simultaneous tasks) is impossible without a TeamAssignment link. Rating: No — Phase II needs TeamAssignment.

### 1.3 Related Documents

- Design: `docs/02-design/features/ontology.design.md` (v2.0.0)
- Charter: `mindvault/ontology/06-ontology-design-charter.md`
- ADR-001: `mindvault/decisions/001-ontology-strategy.md`
- Project Type Classification: `mindvault/ontology/10-project-type-classification-v2.md`

---

## 2. Scope

### 2.1 In Scope

- [ ] **Gap 1 — Budget/Cost fields:** Add `budget_allocated`, `budget_actual`, `effort_estimated_hours`, `effort_actual_hours` to Task; add `budget_total` and `budget_spent` to Project. Define COST_OVERRUN business rule (alert if actual > 110% of allocated).
- [ ] **Gap 2 — TeamAssignment object:** New Phase II object linking Task ↔ Person with `role_on_task` (Lead/Support/Advisor), `allocation_percent`, `start_date`, `end_date`. Task retains `assignee` as primary owner shorthand; TeamAssignment extends it.
- [ ] **Gap 3 — Approval object:** New Phase II object supporting approval chains for WorkLog, Decision, and Gate entities. Fields: `approves_entity_type`, `approves_entity_id`, `approver_person_id`, `status` (pending/approved/rejected), `comment`, `created_at`, `completed_at`.
- [ ] **Gap 4 — Document object:** New Phase II object for specifications, reports, patent drafts, design documents. Fields: `name`, `doc_type` (Specification/Report/Design/Patent Draft/Dataset), `relates_to` (task_id or project_id), `status` (draft/review/approved/published), `owner_person_id`, `storage_uri`. Enables TRL evidence linking (Use Case B).
- [ ] **Gap 5 — Dashboard query specification:** Define four standard query views (Project Health, Task Backlog, Team Capacity, Risk Register) as part of the ontology contract so downstream API and UI can be built without ad-hoc interpretation.
- [ ] **Blocker vs Task.status clarification:** Formalize the distinction in schema documentation and SBVR rules: Task.status = "blocked" is a work-item state; Blocker object = an external dependency blocking progress with a resolution plan and owner.
- [ ] **Governance mode field:** Add optional `governance_mode` field to Project (`relaxed | balanced | strict`) to accommodate both Agile and Stage-Gate teams within the same system.
- [ ] **WorkLog tag UX recommendation:** Document a tag-discovery UX recommendation (dropdown / autocomplete) so researchers are not required to memorize all 13 tags. Tags remain the same; the friction reduction is in the application layer.

### 2.2 Out of Scope

- Approval notification engine (email/SMS) — Phase III
- Approval UI workflow (multi-step form) — Phase III
- Full budget module (purchase orders, invoice matching) — out of RAPai scope; integrate with external ERP
- Resource capacity planning dashboard UI — Phase III
- NTIS (National Science and Technology Information Service) API integration for government cost reporting — Phase III
- Changing the 13 WorkLog tag set — tags are tested and stable; UX improvement only
- Neo4j graph schema for new objects — Phase III (Alembic + Cypher)
- Changing existing Phase I schemas in breaking ways — governance rules prohibit this; all additions must be non-breaking (MINOR version bumps)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | MoSCoW | Status |
|----|-------------|----------|--------|--------|
| FR-01 | Task schema gains `budget_allocated` (float, optional), `budget_actual` (float, optional), `effort_estimated_hours` (int, optional), `effort_actual_hours` (int, optional) | High | Must | Pending |
| FR-02 | Project schema gains `budget_total` (float, optional) and `budget_spent` (float, optional) | High | Must | Pending |
| FR-03 | Business rule COST_OVERRUN: if `budget_actual > budget_allocated * 1.1`, raise warning-level violation | High | Must | Pending |
| FR-04 | New `TeamAssignment` JSON Schema at `ontology/schemas/team_assignment.json` with fields: `assignment_id` (ULID), `task_id`, `person_id`, `role_on_task` enum (Lead/Support/Advisor), `allocation_percent` (int 1-100), `start_date`, `end_date` | High | Must | Pending |
| FR-05 | New `Approval` JSON Schema at `ontology/schemas/approval.json` with fields: `approval_id` (ULID), `approves_entity_type` enum (WorkLog/Decision/Gate/Document), `approves_entity_id` (ULID), `approver_person_id` (ULID), `status` enum (pending/approved/rejected), `comment` (optional string), `created_at`, `completed_at` | High | Must | Pending |
| FR-06 | New `Document` JSON Schema at `ontology/schemas/document.json` with fields: `document_id` (ULID), `name` (string), `doc_type` enum (Specification/Report/Design/Patent_Draft/Dataset/Other), `relates_to_type` enum (Task/Project), `relates_to_id` (ULID), `status` enum (draft/review/approved/published), `owner_person_id` (ULID), `storage_uri` (URI, optional) | High | Should | Pending |
| FR-07 | SBVR rule clarification: add `BLOCKER_REQUIRES_RESOLUTION_PLAN` rule — a Blocker object must have `resolution_plan` and `owner_person_id` set within 48 hours of creation | Medium | Should | Pending |
| FR-08 | Project schema gains optional `governance_mode` field: enum (relaxed/balanced/strict). Default = balanced. Influences which state transitions require an Approval object. | Medium | Should | Pending |
| FR-09 | Dashboard query spec document: define four standard aggregate views as JSON Schema annotated query contracts (Project Health, Task Backlog, Team Capacity, Risk Register) | Medium | Could | Pending |
| FR-10 | Pydantic models for all 3 new Must-have objects (TeamAssignment, Approval, Document) with roundtrip tests | High | Must | Pending |
| FR-11 | Existing Phase I schemas receive budget/effort field additions as MINOR version bumps (task.json: 0.3.0 → 0.4.0, project.json: 0.3.0 → 0.4.0) with governance validator confirmation | High | Must | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | Adding new fields must not increase roundtrip validation latency above 1ms/op (Phase II target) | pytest benchmark suite; CI regression gate |
| Governance | All schema changes must pass `validate_semver_bump()` check before merge | Pre-commit hook + CI |
| Test Coverage | New Pydantic models must achieve ≥80% line coverage | pytest-cov in CI |
| Backward Compatibility | No existing Phase I tests may break as a result of these additions | Full test suite must pass (235+ tests) |
| Usability | WorkLog tag documentation must include a guided reference card (dropdown order, example per tag) usable by research teams without training | Document review by 1 representative PM |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] FR-01 through FR-03: Budget fields on Task and Project pass roundtrip tests; COST_OVERRUN rule triggers correctly on boundary values
- [ ] FR-04: TeamAssignment schema + Pydantic model created; allocation_percent validated (1-100); duplicate assignment for same task+person rejected
- [ ] FR-05: Approval schema + Pydantic model created; entity_type/entity_id cross-validation enforced
- [ ] FR-06: Document schema + Pydantic model created; doc_type enum matches design charter Deliverable types
- [ ] FR-07: BLOCKER_REQUIRES_RESOLUTION_PLAN rule added to SBVR registry; test covers positive and negative case
- [ ] FR-08: governance_mode field added to Project schema; default = "balanced"; no existing tests broken
- [ ] FR-10: All new models have ≥80% test coverage
- [ ] FR-11: Task schema v0.4.0 and Project schema v0.4.0 validated by governance validator; MINOR bump confirmed

### 4.2 Use Case Acceptance Tests

- [ ] **Use Case A test:** A PM can create a Project with `contract_research` modality, create Tasks with budget fields, assign multiple people via TeamAssignment, attach a Document (specification), and record an Approval for the L2-C Gate — all via the ontology layer without external tools.
- [ ] **Use Case B test:** A researcher can submit a WorkLog with `trl_observed = 4` and link two Document objects as evidence. The AdvanceTRL Action guard (`evidence.count >= 2`) can be satisfied by Document IDs stored in `deliverable_artifact_ids`.
- [ ] **Use Case C test:** A PM assigns 3 TeamAssignment records to a Task (Lead + 2 Support). Query for total allocation per person returns correct value. An attempt to exceed 100% allocation for one person raises a validation error.

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Budget field additions inflate schema complexity, making Project/Task harder for LLMs to parse | Medium | Medium | Keep fields optional with clear `description` annotations; document in LLM-facing schema summary |
| TeamAssignment creates ambiguity with Task.assignee (two sources of truth for "who does this task") | High | High | Formalize in SBVR: Task.assignee = primary owner shorthand; TeamAssignment = full participation record. Validator: if TeamAssignment records exist, Task.assignee must match the Lead-role assignment. |
| Approval object becomes mandatory overhead and kills user adoption | High | Medium | Tie Approval requirement to governance_mode: "relaxed" mode skips Approval; "balanced" requires it for Gate only; "strict" requires it for WorkLog + Decision + Gate |
| Document object duplicates Artifact (planned Phase II) — creates twin-concept confusion | Medium | High | Pre-align: Document = human-authored reference material (specs, reports); Artifact = system-generated or experimental output (prototype, dataset, software). Distinct doc_type enums. Document in schema with `x-relates-to: Artifact` comment. |
| Schema MINOR bumps on Project and Task (v0.3.0 → v0.4.0) break undocumented consumer code downstream | Medium | Low | Enforce governance validator in CI; audit all test fixtures for hard-coded version strings before merging |
| 5 gaps + 3 schema additions + new SBVR rules exceed Phase II bandwidth in one sprint | High | Medium | Phase-split: Must-have (FR-01 to FR-05, FR-10, FR-11) in Phase II-A; Should/Could (FR-06 to FR-09) in Phase II-B |

---

## 6. Impact Analysis

### 6.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|--------------------|
| `ontology/schemas/task.json` | JSON Schema | Add 4 optional budget/effort fields; bump to v0.4.0 |
| `ontology/schemas/project.json` | JSON Schema | Add 2 optional budget fields + governance_mode field; bump to v0.4.0 |
| `ontology/models/core.py` | Pydantic Model | Add new optional fields to Task and Project dataclasses; add COST_OVERRUN validator |
| `ontology/rules/engine.py` | Rule Engine | Add COST_OVERRUN and BLOCKER_REQUIRES_RESOLUTION_PLAN rules |
| `ontology/tests/fixtures/` | Test Fixtures | Update project + task fixtures to include new optional fields in positive cases; add negative cases for COST_OVERRUN |

### 6.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| `task.json` | READ | `ontology/tests/unit/test_roundtrip.py` | Needs verification — fixture updates may be needed |
| `task.json` | READ | `ontology/tests/unit/test_schema_shape.py` | Needs verification — version string check will fail without bump |
| `project.json` | READ | `ontology/tests/unit/test_roundtrip.py` | Needs verification — fixture updates |
| `project.json` | READ | `ontology/tests/unit/test_schema_shape.py` | Needs verification — version string check |
| `ontology/rules/engine.py` | EXECUTE | `ontology/tests/` (rule-related tests) | None — adding rules is append-only; existing rules unaffected |

### 6.3 Verification

- [ ] All 235+ existing tests pass with new schema versions
- [ ] `validate_semver_bump()` confirms task.json and project.json changes are MINOR (not MAJOR)
- [ ] No existing fixture IDs conflict with new ULID fields

---

## 7. Architecture Considerations

### 7.1 Phase II Object Classification

Following the bkit skeleton project principle: new objects should extend without replacing. The three Must-have objects fit into the existing Layer 3 (R&D Project Domain):

```
Layer 3 Extensions:
  TeamAssignment  — links Person ↔ Task with role/allocation context
  Approval        — cross-cutting governance object (touches WorkLog, Decision, Gate, Document)
  Document        — knowledge layer bridge (enables TRL evidence linking)
```

### 7.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Budget tracking granularity | Project-level only / Task-level / Both | Both (optional) | Government R&D requires both WBS-level and project-level cost visibility |
| TeamAssignment vs extending Task.assignee | Extend Task (add assignees array) / Separate object | Separate object | Preserves backward compatibility; separate object allows richer link attributes per Palantir Link model |
| Approval scope | All entities / Selected by governance_mode | governance_mode-gated | Reduces overhead for Agile teams while satisfying governance for Stage-Gate projects |
| Document vs Artifact | Merge / Keep separate | Keep separate | Different semantics: Document = human-authored; Artifact = produced output. Merge risks type confusion in LLM prompts |
| governance_mode default | relaxed / balanced / strict | balanced | Safe default: requires Approval for Gate decisions only, not every WorkLog |

### 7.3 Schema Addition Pattern (Non-Breaking)

All additions follow the established governance workflow:

```
1. Add fields as optional (no `required` array additions)
2. Bump x-ontology-version: MINOR
3. Run validate_semver_bump() — must return "minor"
4. Update Pydantic model with Optional[type] = None
5. Add roundtrip test with new field included
6. Add roundtrip test with new field absent (backward compat)
7. Commit: "feat: Add {field} to {Object} (schema v{N+1})"
```

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions (Confirmed)

- [x] `CLAUDE.md` has coding conventions section — Python 3.11 + Pydantic v2 + ULID identifiers
- [x] `pyproject.toml` — ruff linting + mypy strict type checking
- [x] JSON Schema Draft 2020-12 standard
- [x] ULID format for all primary keys: `^[0-9A-HJKMNP-TV-Z]{26}$`
- [x] SemVer governance via `ontology.validators.governance`

### 8.2 Conventions to Define

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| Budget field naming | Missing | `budget_allocated`, `budget_actual` (snake_case, float) | High |
| Effort field naming | Missing | `effort_estimated_hours`, `effort_actual_hours` (int) | High |
| Approval status enum | Missing | `pending / approved / rejected` — add to `ontology/models/enums.py` | High |
| Document type enum | Missing | Align with charter Deliverable types (Specification/Report/Design/Patent_Draft/Dataset/Other) | Medium |
| governance_mode enum | Missing | `relaxed / balanced / strict` — add to enums | Medium |

---

## 9. Next Steps

1. [ ] CTO (team lead) review and approval of this Plan
2. [ ] Stakeholder validation — confirm budget field granularity with one PM from target org (hyunjaeho@tenopa.co.kr)
3. [ ] Write Design document: `docs/02-design/features/ontology-user-centric-gaps.design.md`
   - Architecture for 3 new schemas (TeamAssignment, Approval, Document)
   - Schema additions to Task and Project
   - SBVR rule additions (COST_OVERRUN, BLOCKER_REQUIRES_RESOLUTION_PLAN)
   - governance_mode integration with existing rule engine
4. [ ] Phase split confirmation: Phase II-A (Must) vs Phase II-B (Should/Could)
5. [ ] TDD implementation starting with COST_OVERRUN rule (most testable first)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-22 | Initial draft — based on R&D end-user workflow assessment | Product Manager Agent |
