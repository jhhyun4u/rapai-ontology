# 온톨로지 핵심요소 & 고려요소 (Research-Based)

**맥락:** 다기관/다팀 R&D 프로젝트에서 인간 PM이 극소수 → AI가 **실질적 Coordinator** 역할

**연구 기반:** ProjectCO, PROMONT, SPMO, PPM Ontology (ISO 21504 / PMI / AXELOS), Graphiti (Temporal KG)

---

## 🎯 핵심요소 (Core Elements)

### 1️⃣ **프로젝트 구조 엔티티 (PROMONT 기반)**

실행 단위를 표현하는 가장 기본적인 개념:

```
Entity:
  ├─ Project        (프로젝트 자체)
  ├─ Program        (사업단형 — 복수 프로젝트 묶음)
  ├─ Portfolio      (기관 전체 R&D 포트폴리오)
  ├─ Task/Activity  (WBS의 작업 단위)
  ├─ Milestone      (검증 가능한 중간 목표)
  ├─ Deliverable    (산출물 — 논문, 특허, 보고서, SW)
  ├─ Resource       (인적/장비/예산)
  └─ Stakeholder    (PM, 연구원, 발주처, 협력기관)
```

**왜 중요한가:** "총괄연구책임자 vs 세부과제책임자 vs 참여연구원"의 역할/책임을 온톨로지가 명시적으로 구분해야 조정(coordination)이 가능.

---

### 2️⃣ **PMBOK 지식영역 매핑 (10 Knowledge Areas)**

```
KnowledgeArea:
  ├─ Scope          → WBS 자동 생성 근거
  ├─ Schedule       → 일정/마일스톤 근거
  ├─ Cost           → 인건비/연구비 편성 규칙
  ├─ Quality        → 산출물 품질 기준
  ├─ Resource       → 팀 구성 규칙
  ├─ Communication  → 보고/회의 프로토콜  ★ Coordinator 핵심
  ├─ Risk           → 리스크 식별/대응
  ├─ Procurement    → 외주/구매
  ├─ Stakeholder    → 이해관계자 관리  ★ Coordinator 핵심
  └─ Integration    → 통합관리         ★ Coordinator 핵심
```

**고려:** Coordinator 역할은 특히 **Communication / Stakeholder / Integration** 세 영역에 집중. 일반 PM 온톨로지는 Scope/Schedule 위주지만, 이 시스템은 **조정 3영역**을 강화해야 함.

---

### 3️⃣ **5-Tier 개념 계층 (ProjectCO 아키텍처)**

```
Layer 1: Foundational   (시간, 이벤트, 엔티티 — 범용)
Layer 2: Core           (프로젝트, 작업, 자원 — PM 공통)
Layer 3: Top-Domain     (R&D 특화 — TRL, CRL, 논문, 특허)
Layer 4: Low-Domain     (프로젝트 유형별 — 정부R&D, 정책연구, 기초연구)
Layer 5: Instance       (실제 프로젝트 인스턴스)
```

**왜 중요한가:** 계층화하지 않으면 "정부R&D 규칙"을 바꾸면 "기초연구"까지 영향 받음. 계층 분리 = 유지보수 가능성.

---

### 4️⃣ **Coordinator-특화 개념 (★ 이 시스템의 차별점)**

일반 PM 온톨로지에 **없는** 것들 — 직접 정의 필요:

```
CoordinationPrimitives:
  ├─ Handoff         (팀 간 작업 인계 — 누가→누가, 무엇을, 언제)
  ├─ Dependency      (팀 A 산출물 → 팀 B 입력)
  ├─ Liaison         (연결 담당자 — 누가 이 팀과 저 팀을 잇는가)
  ├─ Escalation      (충돌/지연 시 누구에게 올리는가)
  ├─ SyncPoint       (정기 동기화 시점 — 주간회의, 월간보고)
  ├─ SharedArtifact  (여러 팀이 공유하는 산출물)
  └─ Blocker         (한 팀의 지연이 다른 팀에 미치는 영향)
```

**왜 필요한가:** 사용자가 지적한 "각자도생" 문제 해결의 핵심. AI가 "팀 A가 지연되면 팀 B/C/D에 어떤 영향?"을 추론하려면 이 개념들이 명시적이어야 함.

---

### 5️⃣ **규칙/제약 (Rules & Constraints)**

```
Rules:
  ├─ GovernmentGuideline    (정부 지침 — 인건비, 정산)
  ├─ InstitutionalPolicy    (기관 정책 — IRB, 보안)
  ├─ ContractualObligation  (계약 — 납기, 산출물 사양)
  ├─ MethodologyStandard    (PMBOK, NPD, Agile 등)
  └─ DomainBestPractice     (분야별 모범사례)
```

**고려:** 규칙은 버전 관리 필수. "2024년 인건비 지침"과 "2026년 지침"이 다르면 과거 프로젝트 추적이 무너짐.

---

### 6️⃣ **시간/버전 축 (Graphiti Temporal KG 기반)**

```
TemporalAspects:
  ├─ ValidFrom / ValidTo   (이 사실이 언제부터 언제까지 참인가)
  ├─ DecisionTimestamp     (이 의사결정은 언제 내려졌나)
  ├─ Supersedes            (이전 버전을 대체)
  └─ ProjectPhase          (Planning / Execution / Monitoring / Closing)
```

**왜 중요한가:** R&D 프로젝트는 3~5년 진행 — 중간에 팀 구성, 예산, 목표가 바뀜. "2026-04-18 시점에 팀은 20명이었다"는 사실이 "2026-10-01 시점에 25명"과 충돌하지 않아야 함.

---

### 7️⃣ **의사결정 & 근거 (Decision Provenance)**

```
DecisionLayer:
  ├─ Decision        (무엇을 결정했나)
  ├─ RuleApplied     (어떤 규칙 적용)
  ├─ Evidence        (근거 — 문서, 데이터, 이전 사례)
  ├─ Alternatives    (고려된 다른 선택지)
  ├─ Confidence      (신뢰도 0-1)
  └─ Reviewer        (인간 검토자 — 총괄연구책임자?)
```

**왜 중요한가:** Hallucination 방지 + 감사 증적. 정부 R&D는 사후 감사 필수.

---

## 🔍 고려요소 (Considerations)

### ⚠️ 1. "각자도생" 문제를 온톨로지로 어떻게 깰 것인가

**현실:** 연구원들은 자기 과제만 보고, 총괄책임자는 자기 연구로 바빠서 조정이 안 됨.

**온톨로지 요구사항:**
- **강제적 의존성 그래프** — 팀 A의 Task 완료 없이 팀 B Task 시작 불가 명시
- **자동 Blocker 감지** — AI가 지연을 선제적으로 파악
- **Coordinator Agent의 권한 모델** — 단순 알림이 아닌 "조정 행동" 권한 정의

---

### ⚠️ 2. 다중 계층 Scope (Project / Program / Portfolio)

**현실:** 사업단(Program)은 10개 세부 프로젝트를 묶음. 각 프로젝트는 다시 세부과제로 분할.

**고려:**
- 온톨로지가 **3단계 중첩**을 지원해야 함
- 상위(Program) KPI ≠ 하위(Project) KPI 합산 — 별도 정의 필요
- 예산은 하향식, 성과는 상향식 집계

**참조 표준:** ISO 21504, PMI Standard for Portfolio Management

---

### ⚠️ 3. 연구자 vs PM 역할 모호성

**현실:** 총괄연구책임자 = 연구자 + PM 겸직 → 둘 다 못함.

**온톨로지 설계:**
- Role과 Person을 분리 (한 사람이 여러 Role)
- AI Coordinator가 **PM Role의 작업**을 대리 수행하되, 의사결정 권한은 인간에게 유지
- "연구자로서의 판단" vs "PM으로서의 판단" 구분 필요

---

### ⚠️ 4. 단계별 온톨로지 활성화 (Stage-Dependent)

**현실:** 기획 단계, 중간평가, 종료 단계의 필요한 정보가 다름.

```
Planning Stage:    WBS, Budget, Team → 많은 입력
Mid-Review:        Progress, Risk, Pivot → 현황 추적
Closing Stage:     Deliverable, IP, Lessons → 정리/이관
```

**고려:** 온톨로지 전체를 항상 로드하지 말고, **Stage 컨텍스트**에 따라 서브셋 활성화 → 토큰 최적화.

---

### ⚠️ 5. 정적 온톨로지 vs Agentic 지식그래프

**선택지:**
- **정적 (OWL/RDF)**: 사전 정의, 안정적, 느린 진화
- **동적 (Graphiti-style)**: Agent가 실시간 사실 추가/갱신, 진화 빠름

**권장:** **하이브리드**
- Core 개념은 정적 (PMBOK, 규칙) — 변하면 안 됨
- 프로젝트 인스턴스 사실은 동적 (Graphiti) — 계속 갱신

---

### ⚠️ 6. 규칙의 버전 관리 & 충돌

**현실:** 정부지침 개정 시 기존 프로젝트에 소급 적용 여부 모호.

**고려:**
- 규칙 엔티티에 `effective_date`, `sunset_date` 필수
- 프로젝트 엔티티에 `bound_rule_version` 기록
- 충돌 시 우선순위: 계약 > 정부지침 > 기관정책 > 모범사례

---

### ⚠️ 7. 개인 연구 작업 ↔ 프로젝트 조정 통합점

**현실:** 연구원 개인이 쓰는 노트, 실험 기록, 논문 초안 → 프로젝트 KPI와 어떻게 연결?

**고려:**
- **Integration Point** 정의: 개인 산출물 → 프로젝트 Deliverable 매핑 규칙
- **Privacy boundary**: 개인 아이디어/초안은 보호, 최종 산출물만 공유
- **자동 집계 vs 수동 등록** 선택

---

### ⚠️ 8. 프로젝트 유형별 차별화 깊이

**질문:** 정부R&D / 정책연구 / 기초연구 / 응용R&D / 생명과학 / 사회과학... 어디까지 세분화?

**권장:** 
- **MVP: 3~4개 유형**만 시작 (정부R&D, 정책연구, 기초연구)
- 검증 후 확장
- 지나친 세분화는 유지보수 부담

---

### ⚠️ 9. 인간-in-the-Loop 포인트

**현실:** AI가 모든 걸 자율로 하면 신뢰 붕괴.

**온톨로지 내 명시:**
```
HumanApprovalRequired:
  ├─ Budget changes > 10%
  ├─ Scope changes (major)
  ├─ Stakeholder escalation
  ├─ Risk level = High
  └─ Ethical/IRB concerns
```

---

### ⚠️ 10. 다국어/다문화 — 기관 협업

**현실:** 국제공동연구 시 용어가 달라짐 (TRL vs MRL, Milestone vs Gate).

**고려:** 용어집(Glossary) 계층 — 다국어 레이블, 기관별 별칭 매핑.

---

## 📊 요약: 구축 우선순위

| 우선순위 | 요소 | 이유 |
|---------|------|------|
| 🔴 P0 | 프로젝트 구조 엔티티 (PROMONT) | 모든 것의 기반 |
| 🔴 P0 | Coordinator 특화 개념 | 이 시스템의 차별점 |
| 🔴 P0 | PMBOK 조정 3영역 (Comm/Stakeholder/Integration) | 핵심 가치 |
| 🟡 P1 | 5-Tier 계층 구조 | 유지보수성 |
| 🟡 P1 | 규칙 버전 관리 | 감사 대응 |
| 🟡 P1 | 시간/버전 축 (Temporal) | 장기 프로젝트 추적 |
| 🟢 P2 | Portfolio/Program 확장 | 사업단형 대응 |
| 🟢 P2 | 다국어 Glossary | 국제협업 시 |

---

## 🎬 다음 단계 제안

1. **P0 요소 상세 설계** — 엔티티/관계/속성 정의
2. **MVP 프로젝트 유형 3개 선정** — 정부R&D / 정책연구 / 기초연구
3. **Coordinator Agent 권한 모델** — 어디까지 자율, 어디서 인간 승인
4. **YAML 스키마 초안** — 실제 온톨로지 파일 구조

**질문:** 어느 부분부터 깊이 들어갈까요? (P0 엔티티 설계 / Coordinator 권한 모델 / MVP 3유형 정의 중 선택)
