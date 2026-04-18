# R&D Agentic OS — 운영 온톨로지 설계 (v2.0)

**리드:** Palantir-style Chief Ontology Engineer  
**핵심 재인식:** 이 시스템은 **Event-Driven Agent Orchestration OS**. 정적 온톨로지(X) → 운영 온톨로지(O)

---

## 🎯 시스템의 실체 (Re-framed)

### 사용자의 비전 = "연구관리 자율운영 OS"

```
[입력]     연구계획서
   ↓
[기획]     연구관리계획문서 자동 생성
   ↓
[실행 루프] 
   ┌──────────────────────────────────────────────┐
   │  인간(4계층): 일지/계획/지시/보고 입력      │
   │      ↓                                        │
   │  [Coordinator AI]: 이벤트 감지 + 의도 해석  │
   │      ↓                                        │
   │  [Specialist Agents]: 업무 배분 + 실행       │
   │      ↓                                        │
   │  결과 기록 → 다음 이벤트 유발                │
   │      ↓ (loop)                                 │
   └──────────────────────────────────────────────┘
   ↓
[산출]     자율 관리된 프로젝트 + 완전한 감사 증적
```

**핵심 통찰:**
- 인간은 **"의도"**(계획/지시/보고)만 제공 → AI가 **"실행"**
- 업무일지가 **1차 이벤트 소스** (trigger)
- Coordinator AI = 라우터, Specialist Agent = 실행기
- 모든 데이터는 자동 기록

---

## 🏛️ 5-Layer 운영 온톨로지 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ Layer 5: INTENT    인간의 의도 (일지/지시/계획)     │
├─────────────────────────────────────────────────────┤
│ Layer 4: EVENT     이벤트 감지 & 라우팅              │
├─────────────────────────────────────────────────────┤
│ Layer 3: ACTION    Agent 실행 (Coordinator+Specialist)│
├─────────────────────────────────────────────────────┤
│ Layer 2: STATE     프로젝트 상태 (Objects+Links)     │
├─────────────────────────────────────────────────────┤
│ Layer 1: KNOWLEDGE 규칙/템플릿/근거 (Static Ontology)│
└─────────────────────────────────────────────────────┘
```

각 층은 **Ontology Object로 1급 시민**. 층간 통신은 정의된 프로토콜.

---

## 📦 Part 1: INTENT Layer — 인간 의도 객체

### 1.1 네 가지 핵심 인간 입력

```yaml
WorkLog (업무일지):
  description: "가장 중요한 이벤트 소스. 모든 연구원이 매일 작성"
  properties:
    - log_id
    - author: Person
    - date
    - done_today: [WorkItem]        # 오늘 한 일
    - plan_tomorrow: [WorkItem]     # 내일 계획  ★ WorkPlan 임베디드
    - blockers: [Blocker]           # 막힌 것
    - observations: [Observation]   # 특이사항
    - requests: [Request]           # 요청
  raw_input_format: "자연어 텍스트 (Korean)"
  emits_events: [LogSubmitted]

WorkPlan (업무계획):
  description: "선제적 작업 계획 (일/주/월 단위)"
  properties:
    - horizon: [Daily, Weekly, Monthly, MilestoneSpan]
    - items: [PlannedItem]
    - author
    - target_entities: [Task|Milestone|Deliverable]
  embedded_in: WorkLog.plan_tomorrow OR standalone

WorkDirective (업무지시):
  description: "상급자 → 하급자 지시"
  properties:
    - directive_id
    - from: Person (상급 Role)
    - to: Person | Team
    - content: 자연어
    - urgency: [Low, Medium, High, Critical]
    - deadline
    - expected_output
    - related_to: [Project|Task|Issue]
  authority_chain: enforced (총괄→프로젝트→서브→연구원)
  emits_events: [DirectiveIssued]

WorkReport (업무보고):
  description: "업무 완료/진행 보고 (지시에 대한 응답 또는 자발적)"
  properties:
    - report_id
    - author
    - addresses: WorkDirective | Milestone | self_initiated
    - status: [Completed, InProgress, Blocked, Deferred]
    - output: [Deliverable|Document|Data]
    - issues_encountered
  emits_events: [ReportSubmitted]
```

### 1.2 왜 이 4가지가 온톨로지의 중심인가

**이것들이 AI의 "감각기관"**. 시스템은 인간의 자연어 의도를 구조화된 이벤트로 변환하여 작동.

---

## 🌊 Part 2: EVENT Layer — 이벤트 모델

### 2.1 Event Type 분류

```yaml
HumanEvent (인간 유발):
  - LogSubmitted        # 일지 제출
  - DirectiveIssued     # 지시 발령
  - ReportSubmitted     # 보고 제출
  - PlanCreated         # 계획 수립
  - ApprovalGranted     # 승인
  - EscalationRaised    # 에스컬레이션

SystemEvent (시스템 유발):
  - DeadlineApproaching # 마감 임박
  - DependencyResolved  # 선행 완료
  - BudgetThresholdHit  # 예산 임계
  - KPIOutOfRange       # KPI 이탈
  - RuleViolation       # 규칙 위반

AgentEvent (AI 유발):
  - BlockerDetected     # 블로커 자동 감지
  - RiskIdentified      # 리스크 식별
  - AnomalyDetected     # 이상 탐지
  - TaskCompleted       # Agent 작업 완료
  - QueryRequested      # 정보 요청

TemporalEvent (시간 유발):
  - DailyCycle          # 일일 점검
  - WeeklyReview        # 주간 검토
  - MilestoneCheck      # 마일스톤 점검
```

### 2.2 Event 구조 (모든 Event 공통)

```yaml
Event:
  event_id: uuid
  type: EventType
  source: [Human|System|Agent|Temporal]
  timestamp
  payload: {...}                  # type별 상이
  context:
    project: Project
    actors: [Person]
    related_objects: [Object]
  routing:
    target_coordinator: CoordinatorAI
    priority: [P0, P1, P2, P3]
  lifecycle:
    detected_at
    dispatched_at
    handled_by: [Agent]
    closed_at
```

### 2.3 이벤트 → 액션 라우팅 (Dispatch Table 예시)

```yaml
EventDispatchRules:
  
  LogSubmitted:
    steps:
      1. Parse natural language → extract intents
      2. Link to existing Objects (Tasks, Milestones)
      3. IF blockers mentioned → DetectBlocker Action
      4. IF new risks → IdentifyRisk Action
      5. IF plan_tomorrow exists → ScheduleTasks Action
      6. IF deliverable mentioned → UpdateDeliverable Action
      7. Always → UpdateDailyProgress + RecordDecision

  DirectiveIssued:
    steps:
      1. Validate authority chain
      2. Parse directive content
      3. Create WorkDirective object + link
      4. Decompose into Tasks (GenerateTasks Action)
      5. Assign to addressees
      6. Schedule tracking
      7. Notify recipient

  ReportSubmitted:
    steps:
      1. Link to addressed Directive/Milestone
      2. Update status
      3. IF completed → CloseDirective + check downstream
      4. IF blocked → trigger EscalateIssue
      5. Update KPIs

  DeadlineApproaching:
    steps:
      1. Check progress of target
      2. IF at-risk → alert owner + propose mitigation
      3. IF critical → EscalateIssue

  BlockerDetected:
    steps:
      1. Identify affected downstream
      2. ProposeResolution
      3. Notify owner of blocker + affected
      4. IF >1 day unresolved → EscalateIssue
```

---

## 🎭 Part 3: ACTOR Layer — 인간 & AI Agent 모델

### 3.1 인간 역할 계층 (권한 계층)

```yaml
Role Hierarchy:
  ProgramDirector (최고책임자/총괄):
    can_delegate_to_AI: [Planning, Reporting, Monitoring, Coordination]
    must_approve: [Budget>10%, Scope change, Personnel change, Gate decisions]
    issues_directives_to: [ProjectLead, SubprojectLead]
    default_delegation_level: L3
    
  ProjectLead (프로젝트 책임자):
    can_delegate_to_AI: [WBS generation, Schedule, Task assignment, Risk tracking]
    must_approve: [Task priority change, Resource reallocation>20%]
    issues_directives_to: [SubprojectLead, Researcher]
    default_delegation_level: L3
    
  SubprojectLead (서브프로젝트 책임자):
    can_delegate_to_AI: [Task-level scheduling, Daily coordination, Progress tracking]
    must_approve: [Deliverable acceptance, Subcontract]
    issues_directives_to: [Researcher]
    default_delegation_level: L2
    
  Researcher (참여연구원):
    can_delegate_to_AI: [Schedule suggestion, Data logging, Report drafting]
    must_approve: [Final work product]
    issues_directives_to: []
    default_delegation_level: L2
```

### 3.2 AI Agent 구조 (Coordinator + 9 Specialists)

```yaml
CoordinatorAI:
  role: "모든 이벤트 수신 → 분류 → 라우팅"
  capabilities:
    - event_parsing (NLP)
    - intent_classification
    - agent_dispatch
    - conflict_resolution
    - escalation_decision
  delegations_held: aggregated from all humans

SpecialistAgents (PMBOK + NPD aligned):
  
  1. ScopeAgent:
     owns: [WBS, WorkPackage, Task decomposition]
     actions: [GenerateWBS, RefineTaskStructure, ScopeChangeImpact]
  
  2. ScheduleAgent:
     owns: [Task scheduling, Critical path, Milestone tracking]
     actions: [ScheduleTask, RecomputeCP, DetectScheduleRisk]
  
  3. ResourceAgent:
     owns: [Person allocation, Team composition]
     actions: [AssignResource, DetectOverallocation, RecommendReallocation]
  
  4. RiskAgent:
     owns: [Risk register, Mitigation plans]
     actions: [IdentifyRisk, AssessRisk, RecommendMitigation]
  
  5. KPIAgent:
     owns: [KPI definition, Measurement, Dashboard]
     actions: [DefineKPI, MeasureKPI, FlagAnomaly]
  
  6. IPAgent:
     owns: [Patents, Publications, Trade secrets]
     actions: [TrackIPDeliverable, AdvisePatentTiming]
  
  7. KnowledgeAgent:
     owns: [Document repository, Knowledge graph, Search]
     actions: [IngestDocument, LinkKnowledge, AnswerQuery]
  
  8. CommunicationAgent:
     owns: [Meetings, Reports, Stakeholder updates]
     actions: [DraftReport, ScheduleMeeting, NotifyStakeholders]
  
  9. BudgetAgent:
     owns: [Cost tracking, Budget variance]
     actions: [RecordExpense, ProjectBurn, AlertOverrun]
```

### 3.3 Delegation Object (권한 위임)

```yaml
Delegation:
  description: "인간 → AI 권한 위임 명세"
  properties:
    - delegator: Person
    - delegate: AgentType
    - scope: [Project|Task|Domain]
    - action_types: [ActionType list]
    - autonomy_level: L0-L4
    - valid_from, valid_to
    - revocable: true
    - conditions: [...]
  
  default_delegations:
    ProgramDirector → Coordinator: [MonitorAllProjects@L4, RouteEvents@L4]
    ProjectLead → ScopeAgent: [GenerateWBS@L3, TrackProgress@L4]
    ProjectLead → ScheduleAgent: [ScheduleTasks@L3, DetectDelay@L4]
    Researcher → KnowledgeAgent: [LogExperimentData@L4, SearchLiterature@L4]
```

---

## 📄 Part 4: ARTIFACT Layer — 문서 객체

### 4.1 문서 생명주기

```yaml
ResearchProposal (연구계획서):
  description: "시스템 입력. 외부에서 제출"
  format: [PDF, DOCX, TXT]
  parsed_into: Project object + initial metadata
  
ResearchManagementPlan (연구관리계획문서):
  description: "시스템이 자동 생성하는 마스터 문서"
  sections:
    - Project_Charter
    - WBS_with_Schedule
    - ResourcePlan
    - RiskRegister
    - KPI_Definitions
    - Communication_Plan
    - Budget_Plan
    - Governance_Model (Gate criteria)
    - Delegation_Matrix
  generated_by: CoordinatorAI orchestrating all SpecialistAgents
  updated_on: major_change_events
  version_controlled: true
  
DailyWorkLog (일일 업무일지):
  scope: per-person-per-day
  
WorkDirective (업무지시서):
  scope: per-directive
  
WorkReport (업무보고서):
  scope: per-report
  
Decision (의사결정 기록):
  description: "모든 주요 선택의 자동 기록"
  
Deliverable (산출물):
  types: [Paper, Patent, Report, Prototype, Dataset, Brief]
```

### 4.2 연구계획서 → 연구관리계획 변환 파이프라인

```
[연구계획서 입력]
    ↓
[ProposalParser Agent]
  - 프로젝트 유형 분류 (5개 중)
  - 기간/예산/팀 추출
  - 목표/산출물 추출
    ↓
[Project Object 생성]
    ↓
[병렬 Agent 호출]:
  ├─ ScopeAgent.GenerateWBS
  ├─ ScheduleAgent.InitialSchedule
  ├─ ResourceAgent.TeamStructure
  ├─ RiskAgent.InitialRiskScan
  ├─ KPIAgent.DefineKPIs
  ├─ BudgetAgent.BudgetBreakdown
  └─ CommunicationAgent.CommPlan
    ↓
[Coordinator 통합 + 충돌 해결]
    ↓
[ResearchManagementPlan 문서 생성]
    ↓
[ProgramDirector 승인 대기]
    ↓
[승인 시 → 실행 모드 전환]
```

---

## 🔄 Part 5: 운영 루프 (Day-in-the-Life 구체 시나리오)

### Scenario A: 연구원의 일일 업무일지 처리

```
08:00 - 연구원 김박사 일지 제출:
  "오늘 실험 A를 완료했고, 결과 데이터 정리함.
   내일은 논문 초고를 시작할 예정.
   그런데 실험 B에 필요한 장비가 아직 안 와서 막힘.
   이박사에게 데이터 공유 요청 필요."

08:00:01 - [LogSubmitted Event] 발생 → CoordinatorAI 수신

08:00:02 - CoordinatorAI 파싱:
  intents:
    - TaskCompletion: "실험 A 완료" → Task_ExpA
    - DataProduct: "결과 데이터 정리" → Deliverable_DataA
    - PlanTomorrow: "논문 초고" → new Task_PaperDraft
    - Blocker: "실험 B 장비 미도착" → Blocker_EquipmentB
    - Request: "이박사에게 데이터 공유 요청"

08:00:03 - 병렬 Agent 디스패치:

  ScopeAgent:
    - Task_ExpA.status → Completed
    - Create Task_PaperDraft, link to Milestone_Publication
    
  ScheduleAgent:
    - Recompute critical path
    - Flag: Task_PaperDraft 일정이 Milestone 마감과 여유 3일
    
  RiskAgent:
    - Blocker_EquipmentB → Risk_EquipDelay (probability High)
    - Impact analysis: Task_ExpB delayed → Milestone_Phase2 at risk
    
  CommunicationAgent:
    - 이박사에게 데이터 공유 요청 메시지 자동 드래프트
    - 서브프로젝트책임자에게 장비 지연 알림
    
  KnowledgeAgent:
    - 실험A 데이터 → 프로젝트 Dataset repo에 인덱싱

08:00:05 - Decision 자동 기록:
  "김박사 2026-04-18 일지 처리 완료. 1 blocker 감지, 
   1 downstream risk 생성, 2 communication 드래프트."

08:00:06 - 김박사 대시보드 업데이트:
  "✅ 일지 처리 완료
   ⚠️ 실험 B 지연 리스크: 서브PL에게 알림 발송
   📧 이박사 요청 메시지 드래프트 (확인/발송 필요)
   📅 내일 논문 초고 작업 시간 블록 확보 (9-12시 제안)"

08:00:07 - 서브프로젝트책임자 알림:
  "김박사 일지에서 장비 지연 블로커 감지됨. 
   하위 영향: Task_ExpB→Milestone_Phase2 지연 가능.
   추천 조치: 구매팀 에스컬레이션 또는 대체 장비 확인"
```

### Scenario B: 총괄책임자 업무지시

```
09:30 - 박교수(총괄) 지시:
  "이번 달 내로 중간보고서 초안 작성해서 후원기관에 제출해야 함. 
   프로젝트 전체 진척도와 주요 리스크 포함할 것. 서브PL들 협조 필요."

09:30:01 - [DirectiveIssued Event] 발생

09:30:02 - CoordinatorAI 처리:
  1. 권한 확인: 박교수=ProgramDirector → 지시 유효
  2. 지시 분해:
     - Output: InterimReport
     - Deadline: 이번 달 말 (2026-04-30)
     - Addressees: 모든 SubprojectLead
     - Required content: [Progress, Risks]
  
09:30:03 - CommunicationAgent 주도:
  - Create Task_DraftInterimReport (owner: CommunicationAgent + 박교수 검토)
  - 각 SubprojectLead에게 자동 지시 파생:
    "중간보고용 서브 진척도 입력 요청 (마감: 2026-04-25)"
  - 보고서 템플릿 준비
  
09:30:04 - ScopeAgent + KPIAgent + RiskAgent:
  - 자동으로 현재까지 데이터 집계 시작
  - 마감 3일 전 자동 드래프트 완성 예정
  
09:30:05 - 박교수 대시보드:
  "✅ 지시 수신 처리됨
   📤 3명의 서브PL에게 서브지시 자동 발송
   📊 자동 보고서 초안: 2026-04-27까지 완성 예정
   👀 검토 슬롯: 2026-04-28 09:00 제안"
```

### Scenario C: 자율 감지 이벤트

```
매일 00:00 - [DailyCycle Event]

CoordinatorAI 자동 점검:
  - 모든 Project 순회
  - Logic Functions 재계산 (health_score, critical_path)
  - 이탈 탐지

발견 사항:
  - Project_P85.budget_burn_rate = 120% of plan
  - BudgetAgent.AlertOverrun 자동 트리거
  - ProjectLead에게 자동 알림 + 분석 리포트
  - IF 초과 지속 3일 → 자동으로 ProgramDirector 에스컬레이션
```

---

## 🛡️ Part 6: 자율성 & 안전장치

### 6.1 Delegation Matrix (요약)

| Action 카테고리 | 연구원 승인 | 서브PL 승인 | PL 승인 | 총괄 승인 |
|---------------|-----------|-----------|---------|---------|
| 일지 파싱/기록 | L4 자율 | - | - | - |
| 리스크 식별 | L4 자율 | - | - | - |
| 작업 스케줄 제안 | L3 | - | - | - |
| 리소스 재배치 <20% | - | L2 | - | - |
| 리소스 재배치 >20% | - | - | L2 | - |
| 범위 변경 | - | - | L1 | 승인 |
| 예산 재편성 >10% | - | - | - | L0 승인 |
| Gate 결정 | - | - | - | L0 승인 |
| 외부 커뮤니케이션 드래프트 | L3 | - | - | - |
| 외부 커뮤니케이션 발송 | L2 승인 | L2 | L1 | L0 |

### 6.2 안전장치

```yaml
Safety:
  1. Explainability: 모든 Agent Action에 reasoning chain 필수
  2. Reversibility: 치명 Action은 rollback_plan 필수
  3. Rate_Limit: Agent 자율 Action 빈도 제한
  4. Circuit_Breaker: 이상 패턴 감지 시 자동 중단 + 인간 통지
  5. Approval_Queue: L0-L2 Action은 인간 승인 대기열
  6. Dry_Run: 중대 Action은 먼저 시뮬레이션
```

---

## 🚀 Part 7: 구현 로드맵 (실용 중심)

### Phase 1: MVP 단일 시나리오 (Month 1-2)
**목표:** "일지 → 자동 반영" 단일 루프 작동

- Objects: Project, Task, Person, WorkLog, Decision
- Agents: CoordinatorAI + ScopeAgent + ScheduleAgent
- Events: LogSubmitted 하나만
- UI: 일지 입력 + 대시보드
- 프로젝트 유형: 1개 (Scientific Research)

**검증:** "연구원이 일지 쓰면 Task 상태가 자동 갱신되는가?"

### Phase 2: Multi-Agent Coordination (Month 3-4)
**목표:** 9개 Specialist 전체 작동 + Directive/Report

- + WorkDirective, WorkReport Events
- + 나머지 7개 Specialist Agents
- + Delegation Matrix 구현
- + Escalation 플로우

**검증:** "총괄 지시 → 서브PL 서브지시 → 연구원 수행 → 자동 보고" 체인

### Phase 3: Plan Document Generation (Month 4-5)
**목표:** 연구계획서 → 연구관리계획 자동 생성

- ProposalParser Agent
- 5개 프로젝트 유형 전체
- 템플릿 라이브러리
- 승인 워크플로우

### Phase 4: Full Governance (Month 5-6)
**목표:** Gate Review, KPI 자동화, Portfolio 대시보드

- Gate 이벤트 + 승인 플로우
- KPI 자동 수집/집계
- Portfolio 관점 대시보드

### Phase 5: Learning Loop (Month 7+)
**목표:** 시스템이 스스로 개선

- 의사결정 품질 평가
- 템플릿 자동 refinement
- 교차 프로젝트 학습

---

## 📋 핵심 설계 결정 요약

| 축 | 결정 |
|-----|------|
| 패러다임 | Event-Driven Agent Orchestration OS |
| 온톨로지 스타일 | 5-Layer (Intent/Event/Action/State/Knowledge) |
| 1차 이벤트 소스 | WorkLog (업무일지) |
| Agent 구조 | Coordinator(1) + Specialist(9) |
| 권한 모델 | Role-based Delegation Matrix + Autonomy L0-L4 |
| 문서 생성 | 연구계획서 → (AI 오케스트레이션) → 연구관리계획 |
| 안전장치 | Explainability + Reversibility + Circuit Breaker |
| MVP 범위 | Single-scenario loop: LogSubmitted → Task update |

---

## 🎬 리드의 다음 단계 제안

**Phase 1 MVP 즉시 착수 권장.** 이 시스템은 "완벽한 온톨로지 먼저"가 아니라 **"최소 루프 먼저 → 학습 기반 확장"** 이어야 함.

**Week 1-2 착수 항목:**
1. WorkLog 자연어 파싱 스키마 (intent extraction)
2. CoordinatorAI 이벤트 라우팅 로직
3. ScopeAgent + ScheduleAgent 최소 Action 4개
4. 일지 입력 UI + 대시보드 프로토타입
5. End-to-end 검증 (1개 Scientific Research 가상 프로젝트)

**리드 결정 요청:**
- ✅ 이 운영 온톨로지 설계를 채택?
- ⚙️ Phase 1 MVP 상세 구현 명세 (YAML 스키마 + Agent 프롬프트 템플릿) 작성 시작?
