# 🎯 TIER 0 병렬 작업 실행 계획 (Week 5-7)

**문서 작성일**: 2026-04-22  
**목표**: Week 7 Friday Gate 통과 (모든 6개 항목 완료)  
**팀 구성**: Backend 2 + QA 1 + Enterprise-Exp 1 + Security 0.5

---

## 📊 TIER 0 작업 맵 (병렬도 분석)

```
Week 5 Monday ─────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  T0-1: SSOT (4d)           T0-2: Link/Action (3d)                  │
│  Backend-1 주도            Backend-2 주도                           │
│  ├─ core.py 완성           ├─ LinkBase model                        │
│  ├─ extended.py 통합       ├─ ActionBase model                      │
│  └─ 19/19 roundtrip        └─ 8 Link + 10 Action subclass          │
│     test ✅                 + cross-ref validator ✅                │
│                                                                      │
│  T0-4: Parser MVP (4d)                 T0-3: Governance CI (2d)    │
│  Backend-1 + QA-1 협업                 QA-1 주도                    │
│  ├─ Intent classifier                  ├─ GitHub Actions flow       │
│  ├─ Entity extractor                   ├─ SemVer diff check        │
│  ├─ 50 fixture validate                └─ Breaking PR blocker ✅   │
│  └─ F1 ≥0.80 ✅                                                    │
│                                                                      │
│  T0-5: PROV-O 정의 (2d)               T0-6: Perf Gate (1d)        │
│  Enterprise-Exp 주도                   QA-1 주도                    │
│  ├─ Event schema 최종화                ├─ pytest-benchmark         │
│  ├─ Security review                    ├─ P99 <1ms gate           │
│  └─ PROV-O spec ✅                    └─ CI 통합 ✅               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

병렬 독립성:
  ✅ T0-1, T0-2, T0-3, T0-4, T0-5, T0-6 모두 독립적 시작 가능
  ⚠️  T0-4(Parser)는 T0-1(schema 완성) 필요 없음 (현재 schema OK)
  ⚠️  T0-2(Link/Action)는 T0-1 schema 참조 가능하지만 대기 불필요
```

---

## 👥 팀별 상세 작업 계획

### **Team 1: Backend Architect × 2 (담당: T0-1, T0-2, T0-4 일부)**

#### **Backend-Arch-1: T0-1 SSOT 완성 (4일)**

**현황**: 
- core.py: Project, Task, WorkLog, Person, Event ✅ (5개)
- extended.py: 10개 객체 70% 완성 (Role, WorkDirective 아직 Pydantic화 필요)

**목표**: 19/19 schema → Pydantic 모델 1:1 매칭, 전수 roundtrip test

**작업 계획**:

```
Day 1 (Mon): Gap Audit + 미완성 모델 파악
  [ ] extended.py 현재 상태 분석 (70% = 어디까지 완성?)
  [ ] 미완성 10개 객체 리스트업
  [ ] 각 객체의 schema vs Pydantic 불일치 점 기록
  
  분석 대상:
    - Role (schema 있음, Pydantic?) 
    - WorkDirective (schema 있음, state machine validation?)
    - Milestone, Gate, Decision, Risk, IP 등 8개
    
  산출물: gap_analysis.md (어디가 막혔는가)

Day 2-3 (Tue-Wed): Pydantic 모델 완성
  [ ] 미완성 10개 객체 Pydantic v2 모델화
  [ ] 각 객체별 validator 추가 (business rules)
    예: WorkDirective 6-state machine validator
        Decision: Evidence 링크 필수
        Risk: probability/impact 범위 (0-1)
  [ ] enums.py 동기화 (모든 enum이 schema와 일치?)
  
  구현 순서 (의존성 고려):
    1. Role (Person과 분리, 권한 정의)
    2. WorkDirective (state 검증 복잡)
    3. 나머지 8개 (order 유연함)

Day 4 (Thu): Roundtrip test + 검증
  [ ] test_roundtrip.py 확장: 10개 모델 추가 (현재 13/27?)
  [ ] 각 모델 50-fixture roundtrip 통과
  [ ] pytest 실행, 모두 PASS
  
  완료 기준:
    ✅ 19/19 모델 exist
    ✅ 19/19 roundtrip test PASS
    ✅ enums 매칭 확인 (test_schema_shape.py)
```

**Daily Sync Points**:
- Day 1 Evening: Gap 분석 결과 → Backend-2/QA-1 공유
- Day 2 Lunch: 구현 상황 (몇 개 완료?)
- Day 4 EOD: 테스트 결과 → Gate 통과?

---

#### **Backend-Arch-2: T0-2 Link/Action 인프라 (3일)**

**현황**: 
- schemas/links.json, actions.json 존재
- Pydantic 모델 및 runtime validator 전혀 없음

**목표**: LinkBase + ActionBase 추상 모델, 8 Link + 10 Action subclass, cross-ref validator

**작업 계획**:

```
Day 1 (Mon): 설계 + 스키마 재검토
  [ ] links.json, actions.json 상세 분석
      - 8 Link types: decomposes_into, plays, produces, depends_on, 
                     justified_by, measured_by, threatens, blocks
      - 각 Link의 properties (lag_days, criticality 등)
  [ ] actions.json: 10 Intent type enum + guard syntax
  
  산출물: Link/Action Pydantic 설계 스펙 (Backend-1과 공유)

Day 2 (Tue): 모델 구현
  [ ] LinkBase(ABC): source_id, target_id, link_type, properties, created_at
  [ ] 8 subclass: decomposes_into_Link, depends_on_Link, ... (각각 특수 validation)
  [ ] ActionBase(ABC): name, parameters, guards, permissions, effects, audit
  [ ] 10 subclass: CreateProject, GenerateWBS, DetectBlocker, ... (각각 구체 guard)
  
  구현 주의:
    - Link properties는 Dict[str, Any] 정도로 유연
    - Action guards는 string 형식 ("new_TRL == current_TRL + 1")
    - Permission은 role list + autonomy_level enum

Day 3 (Wed): Validator + 테스트
  [ ] Cross-reference validator: source_id/target_id가 실제 객체?
  [ ] Link cycle detection: Task→Task depends_on이 circular?
  [ ] Action guard validator: 문법 정상?
  [ ] test suite 20건 작성
      - 정상 케이스 10건 (각 Link/Action type 1-2개)
      - 에러 케이스 10건 (invalid ref, circular, bad guard syntax)
  [ ] pytest 실행, 모두 PASS
```

**Daily Sync Points**:
- Day 1 EOD: 설계 spec → T0-1과 조율
- Day 2 Lunch: 구현 상황
- Day 3 EOD: 테스트 완료?

---

#### **Backend-Arch-1 + QA-1: T0-4 Work Activity Parser MVP (4일)**

**현황**: 
- 설계만 존재 (Work Activity Ontology 09 = 800줄 YAML)
- 구현 코드 0줄

**목표**: Intent 분류 F1 ≥0.80, P99 latency <500ms, 50개 fixture

**작업 계획**:

```
Day 1 (Mon): 파서 아키텍처 설계 + 데이터 준비
  [ ] Intent taxonomy 재정의 (10가지?)
      예: DONE, ISSUE, TRL_UP, PLAN, BLOCKER, ASSIGN, 
         DELIVERABLE, TIME, COST, REQUEST (구체 정의 필요)
  [ ] Entity types (5-7가지)
      예: TASK_MENTION, PERSON_MENTION, DATE_MENTION, ...
  
  [ ] 50개 fixture 준비 (실제 Korean R&D WorkLog 텍스트)
      - 다양한 상황: 진행 상황, 이슈, 예산, 일정 등
      - 각 fixture에 ground truth intent 라벨
      - CSV 또는 JSON 형식
  
  산출물: fixtures.json (50건, intent+entity 라벨)

Day 2 (Tue): Intent Classifier 구현
  [ ] Claude Haiku with structured output
      - Input: WorkLog.content (Korean text, 최대 1000자)
      - Output: { intents: [intent1 (0.92), intent2 (0.45), ...], confidence: 0.85 }
      - Temperature 낮게 (0.3~0.5, deterministic)
  
  [ ] Simple rule-based fallback (parser fail 대비)
      - "완료", "끝남" → DONE
      - "문제", "이슈", "막힘" → ISSUE
      - "TRL", "레디니스" → TRL_UP
  
  [ ] Batch async 처리 (Week 7 성능 목표)
  
  코드 위치: `ontology/worklog_parser/intent_classifier.py` (신규)

Day 3 (Wed): Entity Extractor + 통합
  [ ] Entity extractor (간단한 regex + fuzzy match)
      - "과제명: XYZ" → TASK_MENTION (XYZ = Task 이름)
      - "홍길동 교수" → PERSON_MENTION (홍길동 = Person 이름)
      - "2026-05-15" or "다음주" → DATE_MENTION
  
  [ ] Intent classifier + Entity extractor 통합
      def parse_worklog(content: str) -> Dict[str, Any]:
          intents = classify_intents(content)
          entities = extract_entities(content)
          confidence = average_confidence(intents, entities)
          return {...}
  
  [ ] 50 fixture에 대해 batch 실행
  
  코드 위치: `ontology/worklog_parser/parser.py` (신규)

Day 4 (Thu): 검증 + 성능 측정
  [ ] 50개 fixture 수동 검증 (QA-1이 각 결과 확인)
      - 각 intent 정확도 계산
      - 정오분류(false positive/negative) 분석
  
  [ ] Precision/Recall/F1 계산
      F1 = 2 * (precision * recall) / (precision + recall)
      목표: ≥0.80
      
      만약 미달이면:
        - 파일럿 5개 intent로 축소 (MVP 정의 완화)
        - Rule-based 강화
        - fixture 라벨 재검토
  
  [ ] 성능 측정 (P99 latency <500ms)
      - 1,000회 반복 실행 → 평균/P99 계산
      - Batch 크기 최적화 (batch 크기 vs latency tradeoff)
  
  [ ] pytest-benchmark 추가
  
  완료 기준:
    ✅ F1 ≥0.80 (또는 축소된 intent set에서)
    ✅ P99 latency <500ms
    ✅ 코드 저장소 정리 (코드 리뷰 준비)
```

**Daily Sync Points**:
- Day 1 EOD: fixture 준비 상황 → QA-1과 공유
- Day 2 Lunch: Intent classifier 작동 확인
- Day 3 Lunch: Entity extractor 작동 확인
- Day 4 EOD: F1/latency 수치 → Gate 통과?

**위험 요소 & 대응**:
- F1 <0.80: Intent 축소 (5개로), rule-based 보강
- Latency >500ms: Batch 최적화, cache 추가
- Fixture 부족: Synthetic fixture 생성 (LLM으로)

---

### **Team 2: QA Strategist × 1 (담당: T0-3, T0-6, 지원 T0-4)**

#### **QA-1: T0-3 Governance CI/CD (2일) + T0-6 Performance Gate (1일)**

**목표**: GitHub Actions에서 schema 변경 → SemVer 검증 → breaking 시 PR 차단

**작업 계획**:

```
Day 1 (Tue): Governance CI/CD 설계 + GitHub Actions 구성
  [ ] governance.py 분석
      - validate_semver_bump() 로직 확인
      - compare_schemas() 로직 확인
      - 커버리지 현황 파악
  
  [ ] GitHub Actions workflow 작성 (.github/workflows/ontology-governance.yml)
      ```yaml
      name: Ontology Governance Check
      on: [pull_request]
      jobs:
        semver-check:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
              with:
                fetch-depth: 0
            - uses: actions/setup-python@v4
              with:
                python-version: "3.11"
            - run: pip install -e ".[dev]"
            - run: pytest ontology/tests/unit/test_governance.py -v
            - run: python scripts/check_semver.py
              # This script:
              #   1. Get old schema from main branch
              #   2. Get new schema from PR branch
              #   3. Call governance.validate_semver_bump()
              #   4. If breaking change but version not bumped → FAIL
      ```
  
  [ ] check_semver.py 스크립트 작성
      - main vs HEAD schema diff
      - SemVer violation 감지
      - PR comment로 설명 (왜 차단되었나)
  
  [ ] governance.py 테스트 커버리지 추가
      - test_semver_major_breaking.py (10건)
      - test_semver_minor_nonbreaking.py (10건)
      - test_append_only_enforcement.py (10건)

Day 2 (Wed): Performance Gate (pytest-benchmark CI 통합)
  [ ] pyproject.toml에 pytest-benchmark config 추가
      [tool.pytest.ini_options]
      addopts = "--benchmark-min-rounds=100"
      
  [ ] .github/workflows/performance.yml 작성
      ```yaml
      name: Performance Regression Gate
      on: [pull_request]
      jobs:
        benchmark:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
            - uses: actions/setup-python@v4
            - run: pip install -e ".[dev]"
            - run: pytest ontology/tests/perf/ --benchmark-only --benchmark-json=output.json
            - run: python scripts/compare_benchmarks.py output.json
              # If P99 > 1ms (5% regression tolerance) → FAIL
      ```
  
  [ ] scripts/compare_benchmarks.py 작성
      - baseline JSON 비교
      - P99 회귀율 계산
      - threshold 초과 시 fail with comment

  [ ] 현재 P99 baseline 측정 (현재값 저장)
      pytest ontology/tests/perf/ --benchmark-only --benchmark-json=baseline.json
      
  완료 기준:
    ✅ GitHub Actions 2개 workflow 가동
    ✅ baseline.json 저장됨
    ✅ 다음 PR에서 자동 검증 작동 확인
```

**Daily Sync Points**:
- Day 1 Lunch: workflow 설계 → Backend-1/2와 협의
- Day 1 EOD: Actions 최초 테스트
- Day 2 Lunch: Performance baseline 수치 확인

---

### **Team 3: Enterprise Expert × 1 (담당: T0-5)**

#### **Enterprise-Exp: T0-5 PROV-O 정의 (2일)**

**현황**: 
- Event schema에 PROV-O 필드 약간 있음 (prov_id, actor_agent_id, model_id)
- 완전한 스펙 없음

**목표**: PROV-O lineage 스키마 최종화, Agent 구현팀이 참조 가능하도록

**작업 계획**:

```
Day 1 (Mon): PROV-O 스펙 최종화
  [ ] Event schema 점검
      현재: prov_id (URI), actor_agent_id, model_id, confidence
      필요: 다른 필드?
  
  [ ] PROV-O 모델 이해 (W3C spec)
      - prov:Entity (Project, Task, WorkLog, ...)
      - prov:Agent (Person, Agent AI)
      - prov:Activity (Action 실행)
      - prov:wasGeneratedBy (Activity → Entity)
      - prov:wasAttributedTo (Entity → Agent)
      - prov:wasDerivedFrom (Entity → Entity)
  
  [ ] Decision + Evidence 연결 스키마 정의
      Decision {
        id: UUID
        what_was_decided: str
        evidence: [WorkLog.id | Document.id | ...] ← Evidence는 Entity들
        decided_by: Person.id
        created_at: datetime
        prov_id: str (W3C PROV-O URI)
      }
      
      Event (Decision created 시):
        type: "ontology.decision.made"
        subject: Decision.id
        prov_id: "prov:wasGeneratedBy(Decision, DecisionMadeActivity)"
        actor_person_id: Person.id (의사결정자)
        actor_agent_id: null (AI 아님)
  
  [ ] 3가지 시나리오 정의
      1. Human decision: PM이 Gate 승인
         Actor = Person, actor_agent_id = null
      2. AI-assisted decision: Agent가 risk 제안, PM이 승인
         Actor = Person, actor_agent_id = "AG-risk-detector", model_id = "claude-3.5-sonnet"
      3. AI decision: Agent가 자율적 action 실행 (L4)
         Actor = Agent, actor_agent_id = "AG-planner", model_id = "claude-3.5-sonnet"

Day 2 (Tue): Schema 최종화 + 보안 검토
  [ ] Event schema (ontology/schemas/event.json) 업데이트
      ```json
      {
        "properties": {
          "id": {"type": "string", "pattern": "^[0-9A-HJKMNP-TV-Z]{26}$"},
          "type": {"type": "string"},
          "data": {"type": "object"},
          "prov_id": {"type": "string", "description": "W3C PROV-O URI"},
          "actor_person_id": {"type": ["string", "null"]},
          "actor_agent_id": {"type": ["string", "null"], "pattern": "^(AG-|null)"},
          "model_id": {"type": ["string", "null"], "description": "LLM model if AI-sourced"},
          "confidence": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0}
        }
      }
      ```
  
  [ ] Pydantic validator (Event model)
      @field_validator('actor_agent_id', 'model_id')
      def validate_agent_lineage(cls, values):
          # If actor_agent_id starts with 'AG-', then model_id must be present
          if values.actor_agent_id and values.actor_agent_id.startswith('AG-'):
              if not values.model_id:
                  raise ValueError("If actor is AI (AG-*), model_id is required")
          return values
  
  [ ] x-ontology-version bump (0.1.0 → 0.2.0?)
  
  [ ] Security review checklist
      [ ] PROV-O 체인이 조작 가능한가? (immutable Event 필요)
      [ ] Actor 권한 검증? (AI agent는 L4까지만, etc)
      [ ] 감사 추적이 log-structured? (delete 방지)
  
  산출물: PROV-O-schema.md + Event schema updated
  
  완료 기준:
    ✅ Event schema 최종화
    ✅ 3가지 시나리오 negative test 작성 (10건)
    ✅ Security-Arch 승인
```

**Daily Sync Points**:
- Day 1 EOD: PROV-O 스펙 → Security-Arch/Backend-1 리뷰
- Day 2 Lunch: Schema 최종안 → PM에게 설명
- Day 2 EOD: Security review 완료?

---

### **Team 4: Security Architect × 0.5 (담당: T0-5 review)**

#### **Security-Arch: T0-5 Security Review (1일, 병렬)**

**목표**: PROV-O/Event schema 보안성 검증

**작업 계획**:

```
Day 1 (Mon-Tue): PROV-O 보안 리뷰
  [ ] Event immutability 검증
      - Event는 append-only여야 함
      - UPDATE/DELETE 불가능
      - PostgreSQL constraint?
      
  [ ] Actor 권한 체인
      - actor_person_id + actor_agent_id 조합이 valid?
      - Role + autonomy_level이 action과 일치?
      
  [ ] PROV-O 조작 방지
      - prov_id (URI)가 위조 불가능?
      - signature or cryptographic commitment?
      
  [ ] 민감 정보 노출
      - model_id 공개 괜찮나? (경쟁사가 볼 수 있음)
      - confidence 점수 공개 괜찮나?
  
  산출물: security-review.md (통과/지적사항)
```

**Daily Sync Points**:
- Day 2 EOD: Review 완료, Enterprise-Exp에 피드백 전달

---

## 📅 일일 동기화 (Daily Standup) 구조

**시간**: 매일 09:00 (오전, 모든 팀 sync)  
**형식**: 15분 (5분 × 3 track)

```
09:00-09:05: SSOT 진행 (Backend-1)
  - 어제 완료한 것?
  - 오늘 계획?
  - Blocker 있나?

09:05-09:10: Link/Action 진행 (Backend-2)
  - 어제 완료한 것?
  - 오늘 계획?
  - Blocker 있나?

09:10-09:15: Parser + Governance + PROV-O (Backend-1 + QA-1 + Enterprise-Exp)
  - 어제 완료한 것?
  - 오늘 계획?
  - Cross-team blocker?
```

**주간 동기화 (Friday 4pm, CTO 포함)**:
```
16:00-16:30: CTO + Backend-1/2 + QA-1 + Enterprise-Exp
  - TIER 0 6개 진행률 (%)
  - 주요 blocker
  - 다음주 계획
  - 🚦 Gate (Friday EOD) 통과 예상?
```

---

## ✅ TIER 0 Gate 체크리스트 (Week 7 Friday)

| # | 항목 | Status | 증거 |
|---|------|--------|------|
| **T0-1** | 19/19 Pydantic roundtrip ✅ | pending | test_roundtrip.py (100% PASS) |
| **T0-2** | Link/Action 모델 + cross-ref validator ✅ | pending | pytest (20건 PASS) |
| **T0-3** | Governance CI/CD (GitHub Actions 가동) ✅ | pending | Actions workflow 동작 증명 |
| **T0-4** | Parser F1 ≥0.80, P99 <500ms ✅ | pending | 50-fixture 결과 + benchmark |
| **T0-5** | PROV-O schema 최종화 ✅ | pending | event.json updated + security review |
| **T0-6** | Performance gate (P99 <1ms) ✅ | pending | baseline.json + CI workflow |

**Go Decision**: 6/6 ✅ → Week 8 Monday Agent Design Kickoff  
**No-Go Decision**: 4개 이상 미달 → Week 8 1주 연기

---

## 📌 주의사항

1. **No multitasking**: 각 팀원은 할당된 task 1개만 집중
2. **Daily sync 필수**: 15분이라도 매일 (async 금지)
3. **Blocker 즉시 보고**: "내일이면 되겠지" 금지, CTO에 바로 보고
4. **Code review는 나중에**: TIER 0은 속도 > 품질. Week 7 이후 리뷰
5. **Scope creep 금지**: 설계에서 "이것도 필요한데"라는 생각 나면 TIER 1로 넘김

---

**이 문서를 팀에 공유하고 월요일 09:00 첫 standup을 시작하세요.**
