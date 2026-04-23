---
name: Agent-Ontology Dependency Matrix
description: Maps which ontology objects each of the 4 agent personas critically depends on — drives MVP ontology scope decisions.
type: project
---

Each of the 4 planned agent personas has distinct ontology dependencies that determine the minimum viable ontology for that agent to function.

**Why:** Without this mapping, ontology work risks building objects agents don't need yet, while leaving critical path objects incomplete. This matrix is the foundation for phased agent delivery.

**How to apply:**
- **Coordinator Agent** (blocker detection, handoffs, escalation): CRITICAL depends on Blocker, Handoff, Escalation Action (all Phase II). Cannot ship without Phase II.
- **Planner Agent** (WBS, scheduling, resource allocation): CRITICAL on Project + Task (Phase I, ready) + WorkPackage template (Phase II). Can ship first with minimal Phase II additions.
- **Analyst Agent** (TRL, risk, health scores): CRITICAL on Project.trl_target + WorkLog tags (Phase I). HIGH on Decision+Evidence, Risk, KPI (Phase II). Partially shippable.
- **Evaluator Agent** (gate reviews, milestone validation): CRITICAL on Gate + Milestone (both Phase II). Cannot ship until Phase II complete.
- Recommended delivery sequence based on this matrix: Planner first (lowest Phase II dependency), then Analyst, then Coordinator, then Evaluator.
- 5 Phase II objects are the critical path unblocking all agents: Blocker, Gate, Milestone, Decision, Risk. Prioritize these before the other 5 (WorkDirective, Role, KPI, Artifact, IP).
