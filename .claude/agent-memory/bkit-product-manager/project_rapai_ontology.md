---
name: RAPai Ontology Project Context
description: Core project context for RAPai R&D platform ontology — phase status, user profile, critical gaps, and planning decisions
type: project
---

RAPai (Research AI Platform) is an AI-Native R&D Project Management system targeting Korean public R&D institutions. The ontology layer is the SSOT for all downstream systems (Pydantic, PostgreSQL, Neo4j, OpenAPI, LLM prompts).

**Phase Status:**
- Phase I: COMPLETE — 5 core objects (Project, Task, WorkLog, Person, Event), 13 SBVR rules, 235 tests, 64% coverage
- Phase II: PLANNED — 10 extended objects + 8 Link types + compliance validators
- Phase III: FUTURE — Neo4j/PostgreSQL migrations, Alembic, Qdrant vector schema

**Key Architecture:**
- JSON Schema Draft 2020-12 is SSOT; Pydantic v2 derives from it
- ULID identifiers (26 chars, `^[0-9A-HJKMNP-TV-Z]{26}$`)
- SemVer governance: field additions = MINOR bump, field removal = MAJOR (blocked)
- Rule engine: SBVR rules in `ontology/rules/engine.py`

**Critical User-Centric Gaps (from end-user workflow assessment, 2026-04-22):**
1. Budget/Cost fields on Task and Project — essential for contract research (government R&D)
2. TeamAssignment object — Task has single assignee; real work is team-based
3. Approval object — no approval chain for WorkLog, Decision, Gate finalization
4. Document object — no place for specs, reports, patent drafts; TRL evidence linking broken
5. Dashboard query spec — users will build Excel workarounds without standard views

**Plan created:** `docs/01-plan/features/ontology-user-centric-gaps.plan.md` (2026-04-22)

**Why:** Gap analysis revealed Phase I scores ~6/10 for real practitioner use. Contract research projects (12-month government-funded) cannot run without budget tracking and approval chains. The Digital Twin goal fails if PMs use Excel in parallel.

**How to apply:** When reviewing ontology changes, verify they address one of the 5 gaps. New schema additions must be MINOR version bumps (optional fields only). Phase split: Must-have (Budget+TeamAssignment+Approval) in Phase II-A; Document+Dashboard in Phase II-B.
