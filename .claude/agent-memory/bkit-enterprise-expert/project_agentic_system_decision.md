---
name: Agentic System Start Decision (2026-04-22)
description: Strategic decision on when to begin Agentic System planning-design relative to Ontology Phase II completion. Hybrid Option C recommended.
type: project
---

RAPai Agentic System design start point: Week 8, following Option C (Hybrid with Staged Gates), targeting 18-week total timeline vs. 24-week sequential.

**Why:** Ontology Phase I is complete in design but only 60% coded (5/19 objects). Phase II's 10 extended objects are critical dependencies for all 4 agent personas (Coordinator, Planner, Analyst, Evaluator). Sequential (Option A) wastes 8 weeks and risks Phase II missing agent needs. Fully parallel (Option B) risks design churn. Hybrid Option C uses Weeks 5-7 for Phase I hardening (parser MVP, Link/Action infrastructure, SSOT for 14 models), Weeks 8-10 for roadmapping + RFD, Weeks 11-14 for parallel Phase II + agent blueprints, Weeks 15-20 for implementation.

**How to apply:**
- At Week 8 go/no-go gate, require: (1) Phase I parser >=80% intent classification accuracy on 50 real Korean logs, (2) 14 extended object Pydantic models with SSOT enforcement, (3) Link + Action runtime contracts in place, (4) Governance CI/CD blocking schema violations.
- Hard no-go triggers reverting to Option A: parser <70% accuracy, Link types undefined, Action guards not formalized, PROV-O lineage unclear.
- Agent delivery priority: Tier 1 (Planner + Analyst) first for core value, Tier 2 (Coordinator), Tier 3 (Evaluator) last.
- Critical path objects to unblock all agents: Blocker, Gate, Milestone, Decision, Risk (5 of Phase II's 10).
- Daily 15-min sync between ontology and agent design tracks during Weeks 11-14 to prevent drift.
- Current phase status as of 2026-04-22: Phase I foundation complete (commit 6c92f70 added P0 Constraints/Provenance/WorkDirective State), Phase III W1-W2 Constraint/Rule Engine already merged (13 SBVR rules) — suggesting schedule may actually be ahead of the 18-week plan.
