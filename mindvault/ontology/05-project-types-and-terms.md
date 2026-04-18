# 프로젝트 유형 & 핵심 용어의 역할 (v1 — 개념 해설)

> ⚠️ **SUPERSEDED BY:** [ontology/10-project-type-classification-v2.md](./10-project-type-classification-v2.md) — v2.0 (2026-04-18 확정)
>
> **본 문서 상태:** v1 (개념 해설·참조용 보존). 실제 프로젝트 유형 분류 체계의 **정본(SSOT)은 v2.0 문서**이다.
>
> **v1 → v2.0 주요 변화:**
> - 5유형(Scientific / Technology / Commercialization / Policy / Academic_Contract) → **WBS 성격 8유형 (A~H)**
> - 학술연구용역(Academic_Contract)은 유형이 아닌 **Cross-cutting 속성(`contract_modality = contract_research`)** 으로 재구성
> - B(개발형) / C(사업화·실증형) 분리 확정 (WBS 상이)
> - H(행사운영형) 신설 (Gate 비적용, D-Day 백워드)
> - `contract_research`에 대한 **First-class 관리 모듈** (L2-C Gate, 6-phase WBS Addon, 전용 KPI·AG 가중치·대시보드·RAG) 부착
>
> **보존 이유:** 본 v1 문서는 "프로젝트 유형 / TRL·CRL / Stage-Gate·Agile / 용어 정의" 4요소의 **라우팅 키 개념**을 가장 명료하게 해설한다. v2.0에서도 이 4요소 중요도는 동일하게 유지되며, 구체적 분류 목록만 갱신되었다.

---

**사용자 질문:**
> "프로젝트 유형(scientific research, tech dev, commercialization, policy research, 학술용역)과  
> 용어(TRL, CRL, stage-gate, agile)가 온톨로지에서 얼마나 중요한가? 어떻게 활용되는가?"

**답:** 이들은 **온톨로지의 "라우팅 키(Routing Key)"**. 없으면 AI가 어느 규칙/방법론/KPI를 적용할지 결정 불가.

---

## 🎯 결론 먼저

| 요소 | 중요도 | 역할 |
|------|-------|------|
| **프로젝트 유형** | 🔴 **최고** (없으면 시스템 작동 불가) | 어느 온톨로지 서브셋을 활성화할지 결정 |
| **TRL / CRL** | 🔴 **최고** | 현재 단계에 맞는 행동 결정 |
| **Stage-gate / Agile** | 🟡 **높음** | 어떤 실행 프로세스를 따를지 결정 |
| **용어 정의 (Project vs Program 등)** | 🟡 **높음** | 팀/에이전트 간 소통 일관성 |

---

## 1️⃣ 프로젝트 유형 — "1차 라우팅 키"

### 왜 "가장 중요"한가?

```
사용자 입력: "3년 프로젝트, 20명 팀, 예산 50억"
   ↓
❌ 유형 없음:
   AI: "어떤 방법론을 쓸까? 어떤 KPI? 어떤 규칙?"
   → 혼란, 부적절한 계획

✅ 유형 있음:
   유형 = "commercialization (신제품 개발)"
   ↓
   자동 활성화:
     - 방법론: Stage-Gate (NPD 표준)
     - KPI: 시장 진입 시간, 매출, ROI
     - 규칙: 특허 출원 타임라인, 품질 인증
     - 리스크: 시장 변화, 경쟁사
   ↓
   완전히 다른 계획 생성
```

### 유형별로 모든 것이 달라짐

| 항목 | Scientific Research | Tech Development | Commercialization | Policy Research | 학술연구용역 |
|------|---------------------|------------------|-------------------|-----------------|-------------|
| **방법론** | Inquiry-driven | TRL progression | Stage-Gate | Qualitative + Mixed | Deliverable-driven |
| **주요 KPI** | 논문, 인용수 | TRL 상승, 프로토타입 | 매출, 시장점유율 | 정책 채택률 | 보고서, 납기 |
| **WBS 구조** | Literature→Hypothesis→Experiment→Paper | Concept→Lab→Prototype→Pilot | Idea→Design→Launch→Scale | Review→Analysis→Recommend | 착수→중간→최종 |
| **리스크** | 가설 실패, 재현성 | 기술 실패, TRL 정체 | 시장 실패, 경쟁 | 정책 변화, 이해관계 | 납기 지연 |
| **게이트** | Peer review | TRL gate review | Stage gate (Go/Kill) | Stakeholder review | 중간/최종 평가 |
| **기간** | 2-5년 | 3-7년 | 1-3년 | 6개월-2년 | 3개월-1년 |
| **IP 전략** | Publication-first | Patent-first | Patent + Trade secret | Open publication | 발주처 귀속 |

### 온톨로지에서의 구현 (실제 구조)

```yaml
ProjectType:
  Scientific_Research:
    subtypes: [Basic_Science, Applied_Science, Experimental]
    default_methodology: "Inquiry-Driven"
    required_concepts: [Hypothesis, Experiment, Peer_Review, Reproducibility]
    typical_KPIs: [Publications, Citations, H_Index]
    applicable_rules: [IRB, Research_Ethics, Data_Management]
    
  Technology_Development:
    subtypes: [Component, System, Integration]
    default_methodology: "TRL-Progression"
    required_concepts: [TRL, Prototype, Validation]
    typical_KPIs: [TRL_Advancement, Patent_Count, Tech_Transfer]
    applicable_rules: [Gov_RnD_Guidelines, IP_Policy]
    
  Commercialization:
    subtypes: [New_Product, New_Service, Process_Innovation]
    default_methodology: "Stage-Gate"
    required_concepts: [CRL, MRL, Market_Fit, Gate_Criteria]
    typical_KPIs: [Time_to_Market, Revenue, Market_Share]
    applicable_rules: [Quality_Cert, Regulatory_Compliance]
    
  Policy_Research:
    subtypes: [Legislative, Regulatory, Strategic]
    default_methodology: "Mixed-Methods"
    required_concepts: [Stakeholder_Analysis, Policy_Cycle]
    typical_KPIs: [Policy_Adoption, Stakeholder_Satisfaction]
    applicable_rules: [Ethics, Political_Neutrality]
    
  Academic_Contract:  # 학술연구용역
    subtypes: [Short_Term, Feasibility, Expert_Opinion]
    default_methodology: "Deliverable-Driven"
    required_concepts: [SOW, Acceptance_Criteria, Milestone]
    typical_KPIs: [On_Time_Delivery, Client_Satisfaction]
    applicable_rules: [Contract_Law, Confidentiality]
```

**활용 흐름:**
```
입력 → [유형 분류기] → ProjectType 결정 → 해당 서브셋만 활성화 → 맞춤 계획 생성
```

---

## 2️⃣ TRL / CRL — "단계별 라우팅 키"

### 왜 중요한가?

같은 "기술개발 프로젝트"라도 **현재 단계**에 따라 할 일이 완전히 다름.

```
TRL 3 (개념증명):
  지금 할 일: 실험실 검증, 논문 작성
  KPI: 핵심 기술 원리 입증
  리스크: 원리가 틀릴 가능성
  
TRL 7 (시스템 실증):
  지금 할 일: 실환경 테스트, 파일럿 운영
  KPI: 실환경 성능, 신뢰성
  리스크: 스케일업 실패, 비용 초과
  
TRL 9 (실용화):
  지금 할 일: 상용화, 인증, 마케팅
  KPI: 판매량, 고객 만족
  리스크: 시장 실패

→ TRL을 모르면 TRL 3에게 "시장 진입 전략"을 요구하는 실수 발생
```

### TRL / CRL / MRL 개념 정의 (온톨로지 내)

```yaml
ReadinessLevel:
  TRL:  # Technology Readiness Level (1-9)
    definition: "기술 성숙도"
    scale: 
      1: "기초 원리 관찰"
      2: "기술 개념 정립"
      3: "개념 증명 (PoC)"
      4: "실험실 검증"
      5: "관련 환경 검증"
      6: "관련 환경 시연"
      7: "실환경 시연"
      8: "시스템 완성 및 인증"
      9: "실환경 성공 운영"
      
  CRL:  # Commercialization Readiness Level (1-9)
    definition: "사업화 성숙도"
    scale:
      1: "시장 기회 식별"
      2-3: "시장 조사, 경쟁 분석"
      4-5: "비즈니스 모델 검증"
      6-7: "초기 고객, 파일럿 판매"
      8-9: "본격 시장 진입"
      
  MRL:  # Manufacturing Readiness Level
    definition: "제조 성숙도"
    
  IRL:  # Integration Readiness Level
    definition: "시스템 통합 성숙도"
```

### 어떻게 활용되나

```yaml
Logic:
  IF current_TRL == 3 THEN
    recommend_tasks: [PoC_Experiment, Parameter_Optimization]
    avoid_tasks: [Market_Launch, Mass_Production]
    required_deliverable: [Technical_Report, Data_Validation]
    
  IF current_TRL < 6 AND ProjectType == "Commercialization" THEN
    WARN: "TRL 6 미만에서 상용화 프로젝트는 리스크 매우 높음"
    suggest: "기술개발 단계 추가 검토"
    
  IF current_TRL advances from 5→6 THEN
    auto_update: CRL (보통 2-3단계 뒤따름)
    trigger: Gate_Review_Required
```

**핵심 효과:** AI가 "지금 이 프로젝트가 어느 단계인지" 알기 때문에 **단계 부적합한 제안을 하지 않음**.

---

## 3️⃣ Stage-Gate vs Agile — "실행 프로세스 선택"

### 왜 중요한가?

같은 "신제품 개발"이라도 어떤 프로세스를 쓰느냐에 따라 WBS, 회의 주기, 의사결정 방식이 전부 달라짐.

```
Stage-Gate (전통적):
  Discovery → Scoping → Business Case → Development → Testing → Launch
  각 단계 끝에 Gate Review (Go / Kill / Hold / Recycle)
  특징: 선형, 게이트 기반, 하드웨어/규제산업 적합
  
Agile (반복적):
  Sprint 1 → Sprint 2 → ... (2-4주 반복)
  각 Sprint 끝에 Review + Retrospective
  특징: 반복, 적응적, SW/서비스 적합
  
Hybrid (Stage-Gate + Agile):
  Discovery (Agile) → Development (Agile Sprints) → Gate → Launch
  특징: 유연성 + 통제 균형
```

### 온톨로지에서의 구현

```yaml
Methodology:
  Stage_Gate:
    phases: [Discovery, Scoping, Business_Case, Development, Testing, Launch]
    decision_points: "Gate at each phase end"
    decision_criteria: [Go, Kill, Hold, Recycle]
    best_for: [Hardware, Regulated, Capital_Intensive]
    
  Agile_Scrum:
    iterations: "Sprint (2-4 weeks)"
    ceremonies: [Planning, Daily, Review, Retrospective]
    artifacts: [Backlog, Increment, Burndown]
    best_for: [Software, Services, Uncertain_Requirements]
    
  Hybrid:
    structure: "Stage-Gate outer, Agile inner"
    best_for: [Complex_Systems, Long_Duration]

SelectionLogic:
  IF ProjectType == "Commercialization" AND domain == "Hardware" THEN
    recommend: Stage_Gate
  IF ProjectType == "Commercialization" AND domain == "Software" THEN
    recommend: Agile_Scrum
  IF duration > 3_years THEN
    recommend: Hybrid
```

---

## 4️⃣ 용어 정의 (Project vs Program 등) — "소통의 기반"

### 왜 중요한가?

에이전트 간, 팀 간 소통에서 **용어가 다르면 혼란**.

```
❌ 혼란:
  팀 A: "이 프로젝트의 일정은..."  (Project = 3년짜리 대형)
  팀 B: "이 프로젝트의 일정은..."  (Project = 3개월짜리 세부과제)
  AI: ??? 어느 쪽 말하는 거지?

✅ 정의:
  Program = 사업단 (3-5년, 다중 Project 포함)
  Project = 단위 프로젝트 (1-3년)
  Subproject = 세부과제 (3개월-1년)
  Task = 작업 단위
  
  → 모든 에이전트/팀이 같은 의미로 사용
```

### 필수 용어집 (MVP)

```yaml
Glossary:
  # 규모 계층
  Portfolio: "기관의 전체 프로젝트 집합"
  Program: "공통 목표를 가진 Project 집합 (사업단)"
  Project: "독립적 목표를 가진 단위"
  Subproject: "Project 내 세부과제"
  Task: "실행 가능한 작업 단위"
  
  # 성과 계층
  Outcome: "최종 결과 (사회적/경제적 영향)"
  Output: "직접 산출물 (논문, 특허, 제품)"
  Deliverable: "계약상 납품물"
  Milestone: "검증 가능한 중간 목표"
  
  # 역할 계층
  총괄연구책임자 = Program_Director
  세부과제책임자 = Project_Lead
  참여연구원 = Researcher
  Coordinator = "조정자 (AI Agent 역할)"
  
  # 단계 용어
  Phase: "프로젝트 생명주기의 주요 구간"
  Stage: "Stage-Gate의 단일 구간"
  Sprint: "Agile의 반복 주기"
  Gate: "의사결정 지점"
```

---

## 🔄 4개 요소의 상호작용 (통합 흐름)

```
[1. 입력] 연구계획서
         ↓
[2. 유형 분류] → ProjectType: Commercialization
         ↓ (1차 라우팅)
[3. 서브셋 활성화] → 신제품 온톨로지 로드
         ↓
[4. 용어 정규화] → "세부과제" = Subproject, "책임자" = Project_Lead
         ↓
[5. 현재 단계 파악] → TRL 5, CRL 3
         ↓ (2차 라우팅)
[6. 방법론 선택] → Hybrid (Stage-Gate + Agile)
         ↓
[7. 맞춤 계획 생성]
   - WBS: Stage-Gate 구조, 현재 Development Stage
   - 다음 할 일: TRL 5→6 전환 작업
   - 경고: CRL 3이라 상용화 논의는 시기상조
   - KPI: TRL 상승, 파일럿 준비도
   - 게이트: TRL 6 도달 시 Gate Review
```

---

## 📊 온톨로지에서의 위상 (계층도)

```
Layer 3: Top-Domain (R&D 특화)
  ├─ ReadinessLevel (TRL, CRL, MRL, IRL)  ★ 단계 판단
  ├─ Methodology (Stage-Gate, Agile, Hybrid)  ★ 프로세스 선택
  └─ Glossary (공통 용어)  ★ 소통 기반
         ↑ 참조됨
Layer 4: Low-Domain (유형별)
  ├─ Scientific_Research
  ├─ Technology_Development
  ├─ Commercialization        ★ 1차 라우팅 키
  ├─ Policy_Research
  └─ Academic_Contract
         ↓ 활성화
Layer 5: Instance
  └─ 실제 프로젝트
```

---

## ✅ 요약: "얼마나 중요한가?"

### 프로젝트 유형
> **없으면 시스템이 작동 불가.** 모든 후속 의사결정의 출발점.

### TRL / CRL
> **없으면 단계 부적합 제안 발생.** "TRL 3에게 상용화 전략 요구" 같은 실수.

### Stage-Gate / Agile
> **없으면 WBS/회의/의사결정 구조 결정 불가.** 실행 체계의 뼈대.

### 용어 정의
> **없으면 에이전트/팀 간 소통 혼란.** 모든 협업의 전제.

---

## 🎬 다음 단계 제안 (v1 당시)

이 4가지 요소가 중요하다는 것을 확인했다면:

1. **MVP 유형 정의 깊이** — 5가지 유형 각각을 어느 수준까지 상세화?
2. **TRL/CRL 측정 방법** — 누가, 언제, 어떻게 현재 레벨을 판단?
3. **Methodology 선택 자동화** — AI가 어떤 기준으로 Stage-Gate vs Agile 추천?
4. **용어집 구축 우선순위** — 어떤 용어부터 정의할지?

---

## ✅ v2.0 후속 결정 (2026-04-18)

위 질문들은 v2.0에서 다음과 같이 확정되었다:

| v1 질문 | v2.0 결정 |
|---|---|
| MVP 유형 정의 깊이 | **WBS 8유형(A~H) 확정** — 10-project-type-classification-v2.md |
| TRL/CRL 측정 방법 | **Rule Engine 전담(CP3)** — 결정 16 (ADR-002), LLM 배제 |
| Methodology 선택 자동화 | **유형별 Gate 활성화 매트릭스** — 결정 9 (L1-L4 + L2-C) |
| 용어집 구축 우선순위 | **JSON Schema SSOT** — ADR-001 결정 5 |

### 추가로 확정된 v2.0 핵심 내용
- **Cross-cutting 속성 2축**: `contract_modality` · `funding_source` · `security_tier` · `scale_tier`
- **학술연구용역 First-class 모듈**: 결정 22 (ADR-002) — L2-C Gate + 6-phase WBS Addon
- **RAPai 관리 경계 원칙**: 관리 시작점 = 계약 체결 (영업·제안 단계 범위 외)

→ 실제 구현·운영 시에는 반드시 [ontology/10-project-type-classification-v2.md](./10-project-type-classification-v2.md) 및 [decisions/002-ai-model-architecture.md](../decisions/002-ai-model-architecture.md)를 정본으로 따른다.
