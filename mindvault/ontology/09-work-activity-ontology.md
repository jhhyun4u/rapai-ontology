# Work Activity Ontology — 상세 설계 (v1.0)

**지위:** Layer 5. 이 시스템의 **영혼(Soul)**. 80% 자체 개발.  
**범위:** 업무일지(WorkLog), 업무지시(WorkDirective), 업무계획(WorkPlan), 업무보고(WorkReport)  
**목적:** 한국 R&D 업무 문화에 최적화된 "인간 의도 → 구조화 이벤트" 변환 체계

---

## 🎯 설계 철학

### 핵심 원칙
1. **자연어 우선(NL-First):** 연구원이 평소 쓰는 말투 그대로 입력. 양식 강요 금지.
2. **구조화는 AI 책임:** 사람은 쓰고, AI가 파싱·구조화·연결.
3. **Intent-Driven:** "무엇을 표현하려 하는가"(intent)가 1차 분류 키.
4. **Evidence-Preserving:** 원문은 항상 보존. 파싱 결과는 derived data.
5. **Feedback-Loop:** 파싱 오류 교정이 온톨로지를 성장시킴.

### 왜 표준이 없는가
- 해외 PM 툴(Jira, Asana)은 "티켓 중심" — 한국 R&D는 "일지/보고 중심"
- Activity Streams/BPMN은 너무 추상적 — 연구원 일상 작업에 부적합
- 국내 연구관리 시스템(IRIS, RCMS)은 문서 제출 양식이지 **의도의 의미 체계**가 아님

---

## 📐 Part 1: Core Concept Hierarchy

```
WorkActivity (abstract)
├─ WorkLog           (업무일지: 과거+미래, 자유 서술)
├─ WorkDirective     (업무지시: 상→하, 명령적)
├─ WorkPlan          (업무계획: 선제적 commitment)
└─ WorkReport        (업무보고: 공식 보고, 보통 응답)

모든 WorkActivity 공통 속성:
  - activity_id
  - author: Person
  - timestamp
  - raw_text (자연어 원문, 보존)
  - language: [ko, en]
  - context: {project, subproject}
  - parsed: ParsedContent (AI 생성)
  - confidence: 0.0-1.0
  - reviewed_by_human: bool
```

### 4자간 관계

```
WorkDirective --[triggers]--> WorkPlan (하급자가 받은 뒤 계획 수립)
WorkPlan      --[manifests_in]--> WorkLog (일지의 plan_tomorrow)
WorkLog       --[may_include]--> WorkReport (일지 안의 보고)
WorkReport    --[addresses]--> WorkDirective (지시에 대한 응답)
WorkLog       --[aggregates_into]--> WorkReport (주간/월간 보고)
```

---

## 🎯 Part 2: Intent Taxonomy (★ 핵심 IP)

### 2.1 1차 Intent (10종)

자연어 문장에서 파싱해야 하는 기본 의도:

```yaml
Intents:
  1. COMPLETION       완료 보고
     examples: 
       - "실험 A를 완료했음"
       - "초고 작성 마쳤습니다"
       - "논문 투고 완료"
  
  2. PROGRESS         진행 중 상황
     examples:
       - "데이터 분석 70% 진행"
       - "아직 결과 기다리는 중"
  
  3. PLAN             향후 계획
     examples:
       - "내일 세미나 발표 자료 준비"
       - "다음주부터 실험 C 시작 예정"
  
  4. BLOCKER          막힘/장애
     examples:
       - "장비가 고장나서 진행 못 함"
       - "예산 승인이 늦어져서 대기 중"
  
  5. REQUEST          요청/부탁
     examples:
       - "이박사에게 데이터 공유 부탁"
       - "구매팀에 장비 발주 요청 필요"
  
  6. DIRECTIVE        지시 (상→하)
     examples:
       - "서브PL들은 월말까지 중간보고서 준비할 것"
       - "김연구원, 오늘까지 데이터 정리"
  
  7. OBSERVATION      관찰/특이사항
     examples:
       - "측정값이 예상보다 20% 높게 나옴"
       - "참여기관 담당자가 교체됨"
  
  8. RISK_FLAG        리스크 경고
     examples:
       - "이 속도면 마감 맞추기 어려울 듯"
       - "경쟁 그룹이 유사 논문 발표함"
  
  9. DECISION         의사결정 기록
     examples:
       - "실험 방법을 B안으로 변경하기로 함"
       - "회의 결과 장비 구매 승인"
  
  10. QUERY           질문/확인 요청
      examples:
        - "이 규정이 맞는지 확인 필요"
        - "다음 마일스톤 일정이 언제였지?"
```

### 2.2 2차 Intent Modifier (보조 의미)

```yaml
Modifiers:
  - Urgency: [Critical, High, Medium, Low]
  - Certainty: [Confirmed, Likely, Tentative, Speculative]
  - Sentiment: [Positive, Neutral, Negative, Alarming]
  - Privacy: [Public, Team, Restricted, Confidential]
  - Effort: [Minutes, Hours, Days, Weeks]
```

### 2.3 Intent 조합 처리

한 문장에 복수 Intent 가능:

```
원문: "실험 A를 완료했는데, B는 장비 고장으로 지연될 듯해서 
       내일 대체 장비 확인 예정"

추출 Intent:
  - COMPLETION (실험 A)
  - BLOCKER (실험 B, 장비 고장)
  - RISK_FLAG (B 지연 예상)
  - PLAN (내일, 대체 장비 확인)
```

---

## 🔍 Part 3: Entity Recognition Schema

자연어에서 추출해야 할 **10가지 Entity 타입**:

```yaml
Entities:
  
  TASK_MENTION:
    patterns: ["실험 A", "논문 초고", "중간보고서 작성"]
    resolution: 
      1. Check existing Task objects (fuzzy match)
      2. If no match → candidate for new Task creation
      3. Prompt confirmation if confidence < 0.7
  
  PERSON_MENTION:
    patterns: ["김박사", "이박사님", "박교수", "서브PL"]
    resolution:
      - Match to Person/Role in project team
      - Korean honorifics 처리 (박사/교수/선생님/PL)
  
  DATE_MENTION:
    patterns:
      absolute: ["2026-04-18", "4월 18일", "18일"]
      relative: ["오늘", "내일", "다음주", "이번달", "월말"]
      deadline: ["까지", "전까지", "이내"]
    resolution:
      - Convert to ISO 8601
      - 상대 표현은 author의 timestamp 기준으로 해석
  
  DURATION_MENTION:
    patterns: ["3일", "2주", "한 달"]
  
  DELIVERABLE_MENTION:
    patterns: ["논문", "보고서", "특허", "프로토타입", "데이터셋"]
    resolution:
      - Type classification
      - Link to existing Deliverable object or create candidate
  
  MILESTONE_MENTION:
    patterns: ["중간평가", "최종보고", "Phase 2 종료"]
  
  EQUIPMENT_MENTION:
    patterns: ["장비", "기기", "장치", 특정 장비명]
  
  LOCATION_MENTION:
    patterns: ["본교 실험실", "협력기관", "현장"]
  
  AMOUNT_MENTION:
    patterns: ["500만원", "3천만원", "예산 20%"]
  
  METRIC_MENTION:
    patterns: ["정확도 95%", "처리속도 10배"]
    resolution:
      - Link to KPI if matches definition
```

### Entity Resolution Pipeline

```
자연어 문장
  ↓
[1. Tokenization + POS tagging] (한국어 형태소 분석)
  ↓
[2. Named Entity Recognition] (이름/날짜/숫자)
  ↓
[3. Domain Entity Extraction] (Task/Deliverable/...)
  ↓
[4. Coreference Resolution] (대명사 → 명시적 entity)
  ↓
[5. Object Linking] (기존 온톨로지 Object와 매칭)
  ↓
[6. Confidence Scoring]
  ↓
[7. Ambiguity Flagging] (신뢰도 낮으면 사용자 확인)
```

---

## 📋 Part 4: 네 가지 Artifact 상세 스키마

### 4.1 WorkLog (업무일지) — 1차 이벤트 소스 ★

```yaml
WorkLog:
  # 식별
  log_id: uuid
  author: Person (FK)
  date: date
  submitted_at: timestamp
  
  # 원본
  raw_text: string (자연어, 보존)
  language: ko | en
  
  # 구조 (자유 서술을 AI가 분해)
  sections:
    done_today:        # 오늘 한 일
      - intent: COMPLETION | PROGRESS
        raw_excerpt: string
        related_task: Task (FK)
        outcome: {...}
        duration_actual: hours
        confidence: 0.0-1.0
    
    plan_tomorrow:     # 내일 계획 (→ WorkPlan 파생)
      - intent: PLAN
        raw_excerpt: string
        target_task: Task
        estimated_duration: hours
        priority: High|Med|Low
    
    blockers:          # 막힌 것
      - intent: BLOCKER
        raw_excerpt: string
        what_blocked: Task|Deliverable
        blocking_cause: string
        impact_scope: [Task ids]
        needs_help_from: [Person|Role]
    
    observations:      # 특이사항
      - intent: OBSERVATION | RISK_FLAG
        raw_excerpt: string
        severity: Info|Warn|Critical
        suggests_action: string?
    
    requests:          # 요청
      - intent: REQUEST
        raw_excerpt: string
        to: Person|Team
        what: string
        deadline: date?
  
  # 메타
  ai_confidence_avg: float
  human_reviewed: bool
  corrections_applied: [Correction]  # 사용자가 AI 파싱 수정한 내역
  
  # 파생 이벤트
  emitted_events: [Event id]
```

#### 실제 파싱 예시

```
[원문]
"오늘 실험A의 1차 측정을 완료함. 데이터 정리까지 마침.
 결과값이 예상보다 20% 높게 나와서 재검토 필요할 듯.
 내일은 논문 초고 시작할 예정인데, 3일 정도 걸릴 것 같음.
 이박사님한테 통계 자문 부탁드려야 함.
 아! 실험B는 장비 문제로 아직 시작 못 했음."

[파싱 결과]
WorkLog:
  sections:
    done_today:
      - {intent: COMPLETION, related_task: T_Exp_A_Measure1, duration_actual: ~8h}
      - {intent: COMPLETION, related_task: T_DataOrganize_A}
    
    observations:
      - {intent: OBSERVATION, severity: Warn,
         raw: "결과값이 예상보다 20% 높게 나와서 재검토 필요할 듯",
         suggests_action: "재측정 또는 원인 분석"}
    
    plan_tomorrow:
      - {intent: PLAN, target: Deliverable_Paper_Draft, 
         estimated_duration: 24h (3일), priority: High}
    
    requests:
      - {intent: REQUEST, to: Person_이박사, 
         what: "통계 자문", deadline: null}
    
    blockers:
      - {intent: BLOCKER, what_blocked: T_Exp_B,
         blocking_cause: "장비 문제", 
         impact_scope: [downstream tasks TBD]}
  
  emitted_events:
    - LogSubmitted
    - BlockerDetected (T_Exp_B)
    - RiskFlagged (측정값 이상)
    - RequestIssued (이박사 → 통계자문)
    - PlanCreated (Paper_Draft)
```

### 4.2 WorkDirective (업무지시)

```yaml
WorkDirective:
  directive_id: uuid
  
  # 당사자
  from: Person (반드시 Role 있음)
  to: Person | Team | Role
  authority_verified: bool  # 권한 체계 검증
  
  # 내용
  raw_text: string
  parsed:
    action_required: string
    expected_output: [Deliverable type]
    deadline: date
    urgency: Critical|High|Medium|Low
    
    # 분해 (AI가 Task로 변환 가능한가?)
    decomposable: bool
    proposed_tasks: [Task draft]
  
  # 응답 요구
  response_required: bool
  response_form: Report | Ack | Action
  
  # 상태
  status: Issued | Acknowledged | InProgress | Completed | Rejected | Cancelled
  
  # 추적
  addressed_by: WorkReport (FK, nullable)
  decomposed_into: [Task ids]
  
  # 계층
  parent_directive: WorkDirective (상위 지시 파생)
  child_directives: [WorkDirective]  # 연쇄 지시
```

#### 지시 파싱 예시

```
[원문 - 총괄 박교수]
"서브PL들은 이번 달 말까지 각 세부과제 중간진척도 정리해서 보내주세요.
 주요 리스크도 함께 정리 부탁드립니다."

[파싱 결과]
WorkDirective:
  from: Person_박교수 (ProgramDirector)
  to: [Role_SubprojectLead × 3명]  # 모든 서브PL
  authority_verified: true  # 총괄 → 서브PL 지시 권한 있음
  
  parsed:
    action_required: "세부과제 중간진척도 + 리스크 정리"
    expected_output: [Report]
    deadline: 2026-04-30
    urgency: Medium
    decomposable: true
    proposed_tasks:
      - {for: SubprojectLead_A, task: "서브과제A 진척도 작성", due: 2026-04-29}
      - {for: SubprojectLead_B, task: "서브과제B 진척도 작성", due: 2026-04-29}
      - {for: SubprojectLead_C, task: "서브과제C 진척도 작성", due: 2026-04-29}
  
  response_required: true
  response_form: Report
  
  # 연쇄 효과
  child_directives: 자동으로 각 서브PL이 하위 연구원에게 자료 요청하는 지시 파생 가능
```

### 4.3 WorkPlan (업무계획)

```yaml
WorkPlan:
  plan_id: uuid
  author: Person
  
  # 범위
  horizon: Daily | Weekly | Monthly | Quarterly | MilestoneSpan
  period_start: date
  period_end: date
  
  # 내용
  raw_text: string (있으면)
  embedded_in: WorkLog (일지 안의 plan_tomorrow인 경우)
  
  items:
    - item_id
      target: Task | Deliverable | Milestone
      intent: COMPLETION | PROGRESS | START
      committed_duration: hours
      planned_start: datetime
      planned_end: datetime
      priority: High|Med|Low
      dependencies: [Task ids]
      
  # 약속 수준
  commitment_level: 
    Tentative    # 예정
    Planned      # 계획
    Committed    # 약속
    Locked       # 확정 (변경 시 승인 필요)
  
  # 추적
  revisions: [PlanRevision]  # 변경 이력
  actual_outcomes: [Outcome] # 실행 결과 비교
```

### 4.4 WorkReport (업무보고)

```yaml
WorkReport:
  report_id: uuid
  author: Person
  
  # 대상
  addresses: WorkDirective | Milestone | SelfInitiated
  reported_to: Person | Role
  
  # 내용
  raw_text: string
  format: Text | Structured | Document
  
  parsed:
    status: Completed | InProgress | Blocked | Deferred | Cancelled
    completion_percentage: 0-100
    outputs: [Deliverable ids]
    issues_encountered: [Issue]
    next_steps: [string]
  
  # 증빙
  attachments: [Document]
  
  # 검토
  review_status: Draft | Submitted | UnderReview | Accepted | Revision_Needed
  reviewer: Person
  review_comments: [Comment]
  
  # 집계형 보고
  aggregates: [WorkLog ids]  # 주간/월간 보고는 일지들 집계
```

---

## 🔄 Part 5: State Machines

### WorkDirective State Machine

```
   Issued
     ├─→ Acknowledged (수신자 확인)
     │     └─→ InProgress 
     │           ├─→ Completed (Report 제출)
     │           ├─→ Blocked (블로커 발생)
     │           └─→ Deferred (연기 요청 승인)
     ├─→ Rejected (권한/실행 불가)
     └─→ Cancelled (발령자 취소)
```

### WorkReport State Machine

```
   Draft
     └─→ Submitted
           ├─→ UnderReview
           │     ├─→ Accepted
           │     └─→ Revision_Needed → Draft (loop)
           └─→ AutoAccepted (낮은 중요도 자동 승인)
```

### WorkLog 처리 Pipeline (상태)

```
   Submitted
     └─→ Parsing (AI)
           └─→ Parsed
                 ├─→ HighConfidence → AutoProcessed → Integrated
                 └─→ LowConfidence → PendingReview → (Human correction) → Integrated
```

---

## 🔗 Part 6: Core Object Linkage Model

### WorkActivity → Core Objects 연결 규칙

```yaml
WorkLog 처리 시 자동 링크 생성:
  
  COMPLETION intent:
    → Task.status = Completed
    → Create Decision(who, when, evidence=WorkLog)
    → Trigger downstream Task scheduling
  
  BLOCKER intent:
    → Create Blocker object
    → Link to affected Task
    → Compute downstream impact
    → Trigger DetectBlocker event
  
  PLAN intent:
    → Create/Update WorkPlan
    → Propose Task scheduling
    → Check resource availability
  
  REQUEST intent:
    → Create Communication object (draft)
    → Link sender/receiver
    → Prepare Notification
  
  RISK_FLAG intent:
    → Create Risk object
    → Compute impact on Project.health_score
    → Alert Project Lead if severity >= Warn
  
  DECISION intent:
    → Create Decision object
    → Record rationale + evidence
    → Apply effects (if actionable)
```

### WorkDirective → Task 분해 규칙

```yaml
Decomposition Rules:
  
  IF directive.expected_output == Report AND deadline < 30days:
    → Single Task for addressee
    → Template: "Prepare {output} for {directive.from}"
  
  IF directive.to is Team:
    → One Task per member OR
    → Team Task with subtasks
  
  IF directive has multiple deliverables:
    → One Task per deliverable
    → Link as sibling Tasks
  
  IF directive is recurring (monthly report):
    → Create Recurring Task pattern
```

---

## 🇰🇷 Part 7: 한국 R&D 특화 패턴

### 7.1 보고 계층 문화

한국 R&D는 계층적 보고 문화:

```
연구원 일지 → 서브PL 주간취합 → PL 월간종합 → 총괄 분기보고 → 기관 연보
```

**온톨로지 반영:**
```yaml
AggregationRules:
  WeeklyReport: aggregates(DailyLog from 5 workdays, per SubprojectLead)
  MonthlyReport: aggregates(WeeklyReports, per ProjectLead)
  QuarterlyReport: aggregates(MonthlyReports, per ProgramDirector)
  AnnualReport: aggregates(QuarterlyReports, per Institution)
```

### 7.2 한국어 표현 패턴

```yaml
KoreanPatterns:
  
  완료 표현:
    ["완료", "마쳤", "끝냈", "완수", "제출함", "처리함", "결재 받음"]
  
  진행 표현:
    ["진행 중", "~하는 중", "작성 중", "~% 완료"]
  
  블로커 표현:
    ["막혔", "지연", "문제", "이슈", "장애", "대기 중", "기다리는 중"]
  
  요청 표현:
    ["부탁", "요청", "~해주시면", "필요합니다", "협조 바랍"]
  
  지시 표현:
    ["~하세요", "~해주세요", "~할 것", "~바랍니다", "~지시"]
  
  경어 체계:
    - 존댓말/반말 혼용 (상하 관계 파싱 중요)
    - "~님" 접미사 (Person 식별)
    - "~교수님/박사님/선생님" (Role 추론)
```

### 7.3 특유 문서 유형

```yaml
한국 R&D 특유:
  - 연구개발계획서 (RFP 제출용)
  - 주관기관/공동/위탁 협약서
  - 인건비 정산서
  - 연구결과보고서 (중간/최종)
  - 기술료 수입보고서
  - 참여연구원 변경 신청서
```

---

## 🤖 Part 8: NLP Pipeline 설계

### 8.1 파이프라인 단계

```
[1. Preprocessing]
   - 한국어 형태소 분석 (KoNLPy/Mecab/Kiwi)
   - 문장 분리
   - 오탈자 보정

[2. Intent Classification]
   - LLM 기반 multi-label (10개 Intent)
   - Confidence per label

[3. Entity Extraction]
   - NER (Koelectra, KoBERT 또는 LLM)
   - Domain entity (Task/Deliverable) linking

[4. Coreference Resolution]
   - "그것", "이거" → 명시적 entity

[5. Relation Extraction]
   - 누가 무엇을 했는가
   - 무엇이 무엇을 막았는가

[6. Ontology Linking]
   - 추출된 entity → 기존 Object 매칭
   - Fuzzy match + 사용자 확인

[7. Confidence Scoring]
   - Intent별, Entity별 confidence

[8. Event Generation]
   - 낮은 confidence → HumanReview queue
   - 높은 confidence → 자동 처리
```

### 8.2 LLM Prompt 구조 (예시)

```
System: 당신은 R&D 업무일지 파싱 전문가입니다.
        다음 일지를 분석하여 intent와 entity를 추출하세요.
        
Context: 
  - 프로젝트: {project_name}
  - 작성자: {author_name} ({role})
  - 날짜: {date}
  - 팀원: {team_members}
  - 현재 Task 목록: {tasks}
  - 기존 Deliverable: {deliverables}

Input: {raw_text}

Output schema (JSON):
{
  "sections": {
    "done_today": [...],
    "plan_tomorrow": [...],
    "blockers": [...],
    "observations": [...],
    "requests": [...]
  },
  "overall_confidence": 0.0-1.0,
  "ambiguities": [...]
}
```

---

## 📈 Part 9: Feedback Loop (온톨로지 진화)

### 학습 메커니즘

```yaml
LearningMechanism:
  
  1. Parsing_Correction:
     - 사용자가 파싱 결과 수정
     - Correction pair 저장 (original vs corrected)
     - Intent/Entity 분류기 fine-tuning 데이터
  
  2. Pattern_Discovery:
     - 반복되는 Correction → 새 패턴
     - 새 Intent 카테고리 후보 (기존 10개로 분류 안 되는 것)
  
  3. Entity_Vocabulary_Growth:
     - 새 Task/Deliverable/Equipment 명 학습
     - 별칭(alias) 축적
  
  4. Cultural_Refinement:
     - 조직별 특유 표현 학습
     - Role별 말투 차이 반영
```

### Ontology Version Control

```yaml
Version Policy:
  - Major (X.0): Intent 카테고리 변경 시
  - Minor (x.Y): Entity 타입 추가
  - Patch (x.y.Z): Vocabulary/alias 추가
  
Backward Compatibility:
  - 기존 WorkLog는 자동 재파싱 가능
  - Intent deprecation은 2 minor 버전 공지
```

---

## 🚀 Part 10: MVP 구현 범위

### MVP Scope (2주)

```yaml
Week 1 - Ontology Definition:
  ✓ WorkLog schema (JSON Schema)
  ✓ Intent taxonomy (10개 확정)
  ✓ Entity types (10개 확정)
  ✓ State machine (4개 artifact)
  ✓ Sample corpus 50건 (가상 연구원 일지)

Week 2 - Parsing Pipeline:
  ✓ LLM prompt 템플릿
  ✓ 한국어 전처리
  ✓ Entity linking (기존 Object와 매칭)
  ✓ Confidence scoring
  ✓ 검증: 50건 중 80% 정확도 목표
```

### MVP 축소 범위

- WorkDirective, WorkPlan, WorkReport는 Phase 2
- MVP는 **WorkLog 하나에 집중**
- Intent 10개 중 핵심 6개만(COMPLETION/PROGRESS/PLAN/BLOCKER/REQUEST/OBSERVATION)
- Entity 10개 중 핵심 5개만(TASK/PERSON/DATE/DELIVERABLE/BLOCKER)

---

## ✅ 설계 결정 요약

| 축 | 결정 |
|-----|------|
| 입력 방식 | 자연어 우선, 구조화는 AI 책임 |
| 1차 분류 | 10개 Intent Taxonomy (자체 설계) |
| Entity | 10개 타입 (자체 + NER 표준) |
| 파싱 엔진 | LLM 기반 (Claude/GPT) + 한국어 형태소 |
| 원문 보존 | 항상 (derived data와 분리) |
| 신뢰도 | 저신뢰 → Human review queue |
| 진화 | Correction-based continuous learning |
| MVP 우선 | WorkLog + 6 Intent + 5 Entity |

---

## 🎬 리드의 다음 단계

**이 설계로 Phase 1 Week 1 착수.** 구체 산출물:

1. **WorkLog JSON Schema 파일** (기계 판독 가능)
2. **Intent 분류기 프롬프트 템플릿** (한국어 50개 샘플 포함)
3. **Entity Extraction 스키마**
4. **50건 Sample Corpus** (검증용 가상 연구원 일지)
5. **파싱 결과 Evaluation Rubric**

**리드 결정 요청:**
- ✅ 이 Work Activity Ontology 상세 설계 채택?
- ⚙️ 다음 작업: **실제 JSON Schema 파일 작성** (기계 판독용) 시작?
- 📝 또는 **50건 Sample Corpus 생성** (실제 한국 연구원 일지 스타일) 먼저?
