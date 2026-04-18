# R&D Agentic System — 온톨로지 설계 헌장 (Ontology Design Charter)

**설계 리드:** Palantir-style Chief Ontology Engineer  
**방식:** Object-Centric Ontology with Kinetic Layer  
**목표:** AI Agent가 R&D 프로젝트를 **조정하고 실행**할 수 있는 운영 온톨로지(Operational Ontology) 구축

---

## 🎖️ 핵심 설계 원칙 (Design Principles)

### Palantir 온톨로지의 3축

```
1. Objects (명사)    — "무엇이 존재하는가"
2. Links (동사)      — "어떻게 연결되는가"
3. Actions (동력학)  — "어떻게 변하는가" ★ AI Agent의 권능 영역
```

### 이 프로젝트의 7가지 원칙

| # | 원칙 | 의미 |
|---|------|------|
| 1 | **Object-Centric** | 모든 현실 개체는 Object. Relational 표가 아님. |
| 2 | **Kinetic Ontology** | Agent는 관찰만 하지 않고 **Action**으로 상태를 바꿈 |
| 3 | **Write-back Discipline** | 현실 변경은 반드시 정의된 Action을 경유 (raw mutation 금지) |
| 4 | **Semantic Integration** | 이질적 데이터 소스(HR, 예산, 문서)가 하나의 Object로 통합 |
| 5 | **Governance by Design** | 모든 Action은 Guard(조건) + Permission(권한) + Audit(증적) |
| 6 | **Digital Twin** | 온톨로지 = 프로젝트의 디지털 트윈 (실시간 미러) |
| 7 | **Agent-First Readability** | AI가 자체적으로 네비게이션 가능한 구조 (OpenAI Harness) |

---

## 🏛️ 최상위 설계 결정 (Architectural Decisions)

### AD-001: Object-Centric vs Relational
**결정:** Object-Centric  
**이유:** Agent는 "Project 85의 팀원 중 TRL 판단 경험 있는 사람"을 물어봄. SQL JOIN이 아니라 Object Navigation.

### AD-002: Static Ontology vs Temporal KG
**결정:** **Hybrid**. Core Schema는 정적(OWL-style). Instance Facts는 동적(Graphiti-style with `valid_from/to`).

### AD-003: Closed vs Open World
**결정:** **Closed World** for Rules (규칙은 명시된 것만). **Open World** for Facts (사실은 추가 가능).

### AD-004: Agent Authority Model
**결정:** **Tiered Autonomy** — Action마다 L0(읽기만)~L4(완전자율)로 분류.

### AD-005: Project Type Classification
**결정:** 5개 MVP 유형 + 서브타입. 신규 유형은 기존 상속.

---

## 📦 Part 1: Core Object Types (핵심 객체 12종)

### 1.1 Project Domain Objects

```yaml
# ─── 구조 객체 ───
Portfolio:
  description: "기관 전체 R&D 집합"
  properties: [name, institution, fiscal_year, total_budget]
  primary_key: portfolio_id
  
Program:
  description: "공통 목표의 Project 묶음 (사업단)"
  properties: [name, director, duration, total_budget, strategic_theme]
  primary_key: program_id
  
Project:
  description: "독립 목표를 가진 R&D 단위"
  properties:
    - project_id (PK)
    - name
    - project_type: ProjectTypeEnum  # ★ 라우팅 키
    - current_TRL: int (1-9)
    - current_CRL: int (1-9)
    - methodology: MethodologyEnum  # Stage-Gate, Agile, Hybrid
    - phase: PhaseEnum  # Planning, Execution, Monitoring, Closing
    - start_date, end_date
    - budget_total
    - sponsor: Stakeholder (link)
  
Subproject:
  description: "Project 내 세부과제"
  parent: Project
  
WorkPackage:
  description: "WBS의 작업 패키지 (중간 단위)"
  
Task:
  description: "실행 가능한 최소 작업"
  properties: [name, owner, effort_hours, status, due_date]
```

### 1.2 Outcome Objects

```yaml
Milestone:
  description: "검증 가능한 중간 목표"
  properties: [name, target_date, verification_criteria, status]
  
Deliverable:
  description: "계약상 납품물 또는 주요 산출물"
  properties: [name, type, acceptance_criteria, deadline, status]
  types: [Report, Paper, Patent, Prototype, Software, Dataset, PolicyBrief]
  
Gate:
  description: "Stage-Gate 의사결정 지점"
  properties: [gate_number, criteria, decision_date, decision: GateDecisionEnum]
  decisions: [Go, Kill, Hold, Recycle]
  
KPI:
  description: "성과지표"
  properties: [name, target_value, current_value, measurement_method, unit]
```

### 1.3 Actor Objects

```yaml
Person:
  description: "연구원, PM, 이해관계자 개인"
  properties: [name, role, institution, expertise_areas, availability]
  
Team:
  description: "작업 그룹"
  properties: [name, lead, members, institution]
  
Role:
  description: "프로젝트 내 역할 (Person과 분리)"
  types: [ProgramDirector, ProjectLead, Researcher, Coordinator, Advisor, Sponsor]
  
Stakeholder:
  description: "외부 이해관계자 (발주처, 협력기관, 규제기관)"
```

### 1.4 Knowledge Objects

```yaml
Decision:
  description: "기록된 의사결정"
  properties:
    - decision_id
    - what_was_decided
    - rationale
    - alternatives_considered
    - decided_by: Person
    - decided_at: timestamp
    - confidence: float (0-1)
    - evidence_links: [Document]
  
Risk:
  description: "식별된 리스크"
  properties: [description, probability, impact, mitigation_plan, owner, status]
  
Issue:
  description: "실제 발생한 문제"
  
Rule:
  description: "적용되는 규칙/제약"
  types: [GovernmentGuideline, ContractClause, InstitutionalPolicy, BestPractice]
  properties: [effective_from, effective_to, version, source_document]
  
Document:
  description: "참조 문서"
```

### 1.5 Coordination Objects (★ 이 시스템의 차별 객체)

```yaml
Handoff:
  description: "팀 간 작업 인계"
  properties: [from_team, to_team, artifact, handoff_criteria, scheduled_date]
  
Dependency:
  description: "작업 간 의존성"
  properties: [predecessor: Task, successor: Task, type, slack]
  types: [FS, SS, FF, SF]
  
SyncPoint:
  description: "정기 동기화 시점"
  types: [WeeklyStandup, MonthlyReview, GateMeeting, AdHoc]
  
Blocker:
  description: "진행 저해 요소"
  properties: [blocked_item, blocking_item, detected_at, resolution_plan]
  
Communication:
  description: "커뮤니케이션 기록"
  types: [Meeting, Email, Report, Escalation]
```

---

## 🔗 Part 2: Link Types (관계 모델)

Palantir의 핵심: **Link도 1급 객체** — 속성을 가질 수 있음.

```yaml
# 구조 관계
Portfolio --[contains]--> Program --[contains]--> Project
Project --[decomposes_into]--> Subproject --[decomposes_into]--> WorkPackage
WorkPackage --[decomposes_into]--> Task

# 책임 관계
Person --[plays]--> Role --[on]--> Project
  (link properties: allocation%, start_date, end_date)
Team --[responsible_for]--> WorkPackage

# 산출 관계
Task --[produces]--> Deliverable
Deliverable --[satisfies]--> Milestone
Milestone --[advances]--> Gate

# 의존 관계 (★ Coordinator 핵심)
Task --[depends_on]--> Task
  (link properties: dependency_type, lag_days, criticality)
Handoff --[transfers]--> Deliverable
  (link properties: transfer_date, acceptance_status)

# 측정 관계
Project --[measured_by]--> KPI
KPI --[derived_from]--> [Task, Deliverable, Milestone]

# 근거 관계 (★ Hallucination 방지)
Decision --[justified_by]--> Evidence (Document|Data|Precedent)
Decision --[applies]--> Rule
Decision --[affects]--> [Project|Task|Budget]

# 리스크 관계
Risk --[threatens]--> [Project|Milestone|Deliverable]
Risk --[mitigated_by]--> Task
Blocker --[blocks]--> Task --[blocks_downstream]--> Task
```

---

## ⚡ Part 3: Action Types — Kinetic Layer (★ AI Agent 권능)

**이 층이 Palantir Ontology의 핵심.** Agent는 여기 정의된 Action만 실행 가능.

### 3.1 Action 구조 (모든 Action 공통)

```yaml
Action Template:
  name: string
  parameters: {...}
  guards:         # 실행 전 조건 검증
    - condition_1
    - condition_2
  permissions:    # 누가 실행 가능?
    required_role: [...]
    autonomy_level: L0-L4
  effects:        # 어떤 Object가 어떻게 변하는가
    - create/update/delete
  audit:          # 자동 기록
    who, when, why, rollback_plan
  approval:       # 인간 승인 필요 여부
    required_if: condition
```

### 3.2 Project Lifecycle Actions

```yaml
CreateProject:
  parameters: [name, type, sponsor, budget, duration]
  guards: [type in ProjectTypeEnum, budget > 0]
  permissions: {role: [ProgramDirector], autonomy: L1}
  effects: [create Project, link to Program, initialize WBS template]

AdvanceTRL:
  parameters: [project, new_TRL, evidence]
  guards: 
    - new_TRL == current_TRL + 1  # 한 단계씩만
    - evidence.count >= 2          # 최소 근거 2개
  permissions: {role: [ProjectLead], autonomy: L2}
  effects: [update Project.current_TRL, create Decision, trigger GateReview if TRL in [4,7]]

CloseProject:
  parameters: [project, reason, final_report]
  guards: [all_deliverables.status in [Accepted, Waived]]
  permissions: {role: [ProgramDirector], autonomy: L0}  # 반드시 인간
  approval: {required: true}
```

### 3.3 Planning Actions (Agent 주력 영역)

```yaml
GenerateWBS:
  parameters: [project]
  guards: [project.type != null, project.methodology != null]
  permissions: {role: [Coordinator_AI], autonomy: L3}  # AI 자율
  effects: 
    - create WorkPackage tree from template
    - link to Project
    - create initial Tasks
  audit: [template_used, rationale, alternatives_considered]

ScheduleTask:
  parameters: [task, start, end, assignee]
  guards: 
    - assignee.availability covers [start, end]
    - no dependency violation
  permissions: {autonomy: L3}
  
AssignResource:
  parameters: [person, task, allocation%]
  guards: [person.total_allocation + allocation <= 100]
  permissions: {autonomy: L2}

IdentifyRisk:
  parameters: [project, description, probability, impact]
  guards: [project.phase in [Planning, Execution]]
  permissions: {autonomy: L4}  # AI 완전 자율 식별
  effects: [create Risk, link to affected objects]
```

### 3.4 Coordination Actions (★ 차별 영역)

```yaml
DetectBlocker:
  parameters: [scope: Project|Program]
  permissions: {autonomy: L4}  # AI 자동 탐지
  triggered_by: [dependency_delay, resource_conflict, deliverable_miss]
  effects: [create Blocker, notify affected parties, propose ResolutionPlan]

InitiateHandoff:
  parameters: [from_team, to_team, deliverable, criteria]
  guards: [deliverable.status == Ready_for_Handoff]
  permissions: {autonomy: L3}
  effects: [create Handoff, schedule SyncPoint, notify teams]

EscalateIssue:
  parameters: [issue, to_role, urgency]
  guards: [issue.age > threshold OR issue.impact == High]
  permissions: {autonomy: L3}
  effects: [create Escalation, notify, log in Decision]

RecommendReallocation:
  parameters: [from_task, to_task, resource]
  permissions: {autonomy: L2}  # AI 제안, 인간 승인
  approval: {required_if: impact > 20%}
```

### 3.5 Governance Actions

```yaml
ConductGateReview:
  parameters: [gate, evidence_package]
  guards: [all_entry_criteria_met]
  permissions: {role: [ProgramDirector, Sponsor], autonomy: L0}
  effects: [record Decision: Go|Kill|Hold|Recycle, update Project.phase]
  approval: {required: true}

ApplyRule:
  parameters: [rule, scope]
  permissions: {autonomy: L4}
  effects: [validate scope against rule, create Issue if violation]

RecordDecision:
  parameters: [what, rationale, alternatives, evidence]
  permissions: {autonomy: L4}  # 모든 Action이 자동 호출
  effects: [create Decision object with provenance chain]
```

---

## 🎭 Part 4: Interfaces (다형성)

```yaml
Schedulable (interface):
  implemented_by: [Task, Milestone, Gate, SyncPoint]
  required: [start_date, end_date, dependencies]
  
Assignable (interface):
  implemented_by: [Task, Role, Responsibility]
  required: [assignee, allocation]
  
Measurable (interface):
  implemented_by: [KPI, Milestone, Deliverable]
  required: [target, actual, measure_method]
  
Auditable (interface):
  implemented_by: [Decision, Action, GateReview]
  required: [actor, timestamp, rationale]
```

**효과:** Agent가 "모든 Schedulable 객체의 지연 확인" 같은 **다형 질의** 가능.

---

## 🧮 Part 5: Logic Functions (파생 속성)

```yaml
Project.health_score:
  computed_from: [schedule_variance, budget_variance, risk_count, blocker_count]
  formula: weighted_average
  
Project.critical_path:
  computed_from: Task network
  algorithm: CPM
  
Person.overallocation_flag:
  computed_from: sum(allocation across tasks) > 100
  
Program.trl_distribution:
  computed_from: aggregate(projects.current_TRL)

Deliverable.at_risk:
  computed_from: [days_until_due, completion%, blocker_count]
```

---

## 🤖 Part 6: Agent Interaction Pattern

### 6.1 Agent는 온톨로지를 이렇게 씀

```
[1. 관찰(Observe)]
   Agent.query("Project P85 상태")
   → Ontology는 Object + Links 네비게이션
   → 결과: {Project, Tasks, Risks, Blockers, KPIs, 최근 Decisions}

[2. 추론(Reason)]
   Agent.apply_rules(P85)
   → Rule Engine이 매칭되는 Rules 찾음
   → Logic Functions 실행 (health_score 등)
   → Anomaly 감지

[3. 계획(Plan)]
   Agent.propose_actions(P85)
   → 가능한 Action들 중 guards 통과하는 것 나열
   → 각 Action의 expected_effects 시뮬레이션

[4. 실행(Act)]
   Agent.execute(ActionX, parameters)
   → Guards 재확인
   → Permission 검증 (autonomy_level)
   → 필요시 인간 승인 대기
   → 실행 + Audit 로그
   → Ontology 상태 업데이트

[5. 학습(Learn)]
   Agent.record(Decision)
   → 근거 체인 저장
   → 성과 추적
```

### 6.2 Autonomy Levels (L0~L4)

| 레벨 | 의미 | 예시 Action |
|------|------|------------|
| L0 | AI 읽기만 | CloseProject, ConductGateReview |
| L1 | AI 제안, 인간 실행 | CreateProject |
| L2 | AI 실행, 인간 승인 | AssignResource, RecommendReallocation |
| L3 | AI 자율 실행, 통보 | GenerateWBS, InitiateHandoff |
| L4 | AI 완전 자율 | DetectBlocker, IdentifyRisk, ApplyRule |

---

## 🛡️ Part 7: Governance & Write-back Discipline

### 불변 조건 (Invariants)

1. **모든 상태 변경은 Action 경유** — raw mutation 금지
2. **모든 Action은 Decision 생성** — provenance chain 자동
3. **모든 Decision은 Evidence 링크** — hallucination 차단
4. **모든 Rule은 버전 관리** — 규칙 변경 시 소급 적용 명시
5. **모든 시간 민감 Fact는 valid_from/to** — 장기 프로젝트 무결성

### 감사 증적 (Audit Trail)

```yaml
Every Action execution creates:
  AuditRecord:
    action_name
    executor (Person|Agent)
    timestamp
    parameters
    guards_evaluated
    approvals_obtained
    effects_applied
    rollback_plan
    decision_link
```

---

## 🚀 Part 8: 구현 로드맵 (Phased Implementation)

### Phase 1: MVP Core (Month 1-2)
- **Object Types**: Project, Task, Person, Deliverable, Milestone, Decision, Risk
- **Links**: decomposes_into, plays, produces, depends_on, justified_by
- **Actions**: CreateProject, GenerateWBS, IdentifyRisk, RecordDecision
- **Project Types**: Scientific Research + Technology Development만

### Phase 2: Coordinator Layer (Month 3-4)
- **+ Objects**: Handoff, Dependency, SyncPoint, Blocker, Team
- **+ Actions**: DetectBlocker, InitiateHandoff, EscalateIssue
- **+ Logic**: critical_path, health_score
- **+ Project Types**: Commercialization

### Phase 3: Governance (Month 4-5)
- **+ Objects**: Rule, Gate, KPI
- **+ Actions**: ConductGateReview, ApplyRule, AdvanceTRL
- **+ Interfaces**: Auditable, Measurable
- **+ Project Types**: Policy Research, Academic Contract

### Phase 4: Portfolio & Optimization (Month 6+)
- **+ Objects**: Portfolio, Program
- **+ Cross-project optimization**: RecommendReallocation
- **+ Temporal layer**: 전면 도입

---

## 📋 설계 결정 요약 카드

| 질문 | 결정 |
|------|------|
| 어떤 온톨로지 스타일? | Palantir-style Object-Centric |
| 정적 vs 동적? | Hybrid (Schema 정적, Facts 동적) |
| Agent는 어떻게 상호작용? | Actions via Kinetic Layer |
| 어떻게 Hallucination 방지? | Write-back Discipline + Decision provenance |
| MVP 유형 개수? | 2개 시작(SR+TD), 점진 확장 |
| Autonomy Model? | L0-L4 tiered, Action별 지정 |
| 계층 구조? | Portfolio > Program > Project > Subproject > WP > Task |
| Coordinator 차별화? | Handoff/Dependency/Blocker를 1급 Object로 |

---

## 🎬 다음 실행 단계 (Lead's Decision)

**Phase 1 MVP 즉시 착수 권장.** 순서:

1. **Week 1**: Core Object Types 상세 스키마 (YAML/JSON Schema)
2. **Week 2**: Link Types + 다이어그램 (Mermaid)
3. **Week 3**: MVP 4개 Action 상세 명세 + Guards
4. **Week 4**: Decision/Evidence 객체로 근거 체인 구현
5. **Week 5**: Agent-Ontology 상호작용 프로토콜 정의
6. **Week 6**: Scientific Research 타입 인스턴스로 end-to-end 검증

**리드 결정 요청:**
- ✅ 이 헌장을 채택할 것인가?
- ⚙️ Phase 1 Week 1 — Core Object Schema 상세 작성 시작할까?
