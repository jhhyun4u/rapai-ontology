# 온톨로지 스택 카탈로그 — 무엇을 재사용하고 무엇을 새로 만들 것인가

**중대한 재인식:** 우리가 만드는 것은 **"하나의 온톨로지"가 아니라 "온톨로지 스택(Stack)"**.

각 층은 **목적이 다르고**, **표준이 다르고**, **재사용 가능 여부도 다름**.

---

## 🎯 왜 이 논의가 필요한가

### 이전 설계의 공백
- 지금까지 "객체/관계/액션"만 설계
- 하지만 실제 운영에는 **8개 종류의 온톨로지**가 필요
- 각각을 **처음부터 만들면 2-3년 소요** → **표준 재사용 필수**
- "어떤 것은 재사용, 어떤 것은 자체 개발"을 명확히 해야 투자 계획 가능

---

## 🗺️ 온톨로지 아틀라스 (The 8 Required Ontologies)

```
┌──────────────────────────────────────────────────────┐
│  META LAYER                                           │
│  [8] Ontology Governance & Meta-Ontology             │
├──────────────────────────────────────────────────────┤
│  AGENT OS LAYER                                       │
│  [7] Agent Capability & Communication Ontology       │
│  [6] Event & Action Ontology                         │
├──────────────────────────────────────────────────────┤
│  WORK SEMANTICS LAYER                                 │
│  [5] Work Activity Ontology (일지/지시/보고/계획)    │
│  [4] Actor/Role/Authority Ontology                   │
├──────────────────────────────────────────────────────┤
│  DOMAIN LAYER                                         │
│  [3] R&D Project Domain Ontology                     │
│  [2] Knowledge/Document/Evidence Ontology            │
├──────────────────────────────────────────────────────┤
│  FOUNDATIONAL LAYER                                   │
│  [1] Upper Ontology (Time, Identity, Provenance)     │
└──────────────────────────────────────────────────────┘
```

---

## 📚 Layer 1: Upper Ontology (기초 온톨로지)

### 목적
시간, 사건, 정체성 같은 **범용 개념** 정의. 모든 상위 층이 이를 재사용.

### 권장 표준 (재사용)

| 표준 | 다루는 것 | 재사용 권장도 |
|------|----------|------------|
| **BFO (Basic Formal Ontology)** | 개체/프로세스/시공간 | 🟢 높음 |
| **W3C Time Ontology (OWL-Time)** | 시점/기간/주기 | 🟢 매우 높음 |
| **PROV-O (W3C)** | 출처/근거/활동 이력 | 🟢 매우 높음 ★ |
| **Schema.org (일부)** | 일반 엔티티 (Person, Organization) | 🟡 선택적 |

### 자체 개발 필요
- 거의 없음. 모두 표준 재사용.

### PROV-O가 왜 ★ 중요한가
- 모든 **Decision/Evidence/Audit**의 기반 온톨로지
- `wasGeneratedBy`, `wasDerivedFrom`, `wasAttributedTo` 관계로 **Hallucination 방지**
- W3C 표준이라 RDF/SPARQL 툴체인 바로 사용 가능

```turtle
# PROV-O 예시
:Decision_001 a prov:Entity ;
    prov:wasGeneratedBy :ScheduleAgent_Action_042 ;
    prov:wasDerivedFrom :WorkLog_김박사_20260418 ;
    prov:wasAttributedTo :ScheduleAgent .
```

---

## 🧠 Layer 2: Knowledge/Document/Evidence Ontology

### 목적
문서, 지식, 근거를 구조화. Hallucination 방지의 핵심.

### 권장 표준 (재사용)

| 표준 | 용도 | 재사용 |
|------|------|-------|
| **Dublin Core** | 문서 메타데이터 (title, creator, date) | 🟢 |
| **SKOS** | 용어/분류체계 (taxonomy) | 🟢 |
| **FRAPO** | 연구비/펀딩/프로젝트 행정 | 🟡 참고 |
| **FaBiO, CiTO** | 학술 논문/인용 | 🟢 SR 유형에 필수 |
| **DCAT** | 데이터셋 카탈로그 | 🟡 |

### 자체 개발 필요
- **Evidence Quality Ontology** — 근거의 품질 등급 (직접측정/추론/유추)
- **Korean R&D Document Types** — 연구계획서/성과보고서/감사자료 등 국내 특유 문서 유형

---

## 🔬 Layer 3: R&D Project Domain Ontology ★ 핵심

### 목적
"R&D 프로젝트가 무엇인가"의 도메인 지식.

### 기존 연구 온톨로지 (참고 대상)

| 온톨로지 | 출처 | 재사용도 |
|---------|-----|--------|
| **ProjectCO** | 학계 (5-tier 아키텍처) | 🟢 아키텍처 채용 |
| **PROMONT** | 학계 | 🟡 Task/Resource 개념 |
| **SPMO** | 학계 | 🟡 참고 |
| **PPM Ontology** | ISO 21504 기반 | 🟢 Portfolio 층 |
| **NTIS 분류체계** | 한국 과기부 | 🟢 한국 연구분야 분류 필수 |
| **OECD R&D 분류 (Frascati)** | OECD | 🟢 R&D 유형 분류 표준 |

### 자체 개발 필요 (이 시스템의 핵심 IP)

```yaml
반드시 자체 구축:
  - 5개 프로젝트 유형의 상세 속성
    (Scientific Research, Tech Dev, Commercialization, Policy, Academic Contract)
  - 한국 정부 R&D 특유 개념
    (중간평가, 단계평가, 최종평가, 성과공유)
  - 사업단(Program)형 구조
    (세부과제 분할, 총괄-세부 책임 구조)
  - TRL/CRL 한국 정부 정의 (과기부 고시)
  - Methodology 매핑 (Stage-Gate, Agile, NPD)
```

### Frascati Manual 재사용 이점
OECD Frascati Manual의 R&D 분류:
- Basic Research / Applied Research / Experimental Development
- 이 3분류는 **전 세계 정부 R&D 통계 표준**
- 재사용 시 국제 벤치마킹 가능

---

## 👥 Layer 4: Actor/Role/Authority Ontology

### 목적
사람, 역할, 권한을 구조화.

### 권장 표준

| 표준 | 용도 |
|------|------|
| **FOAF (Friend of a Friend)** | Person, Organization 기초 |
| **org Ontology (W3C)** | 조직 구조 |
| **WebACL** | 권한/접근 제어 |
| **NCS (국가직무능력표준)** | 한국 직무/역량 표준 |

### 자체 개발 필요

```yaml
Korean R&D Roles (자체 구축):
  - 총괄연구책임자 (Program Director)
  - 세부과제책임자 (Subproject Lead)  
  - 연구책임자 (PI)
  - 참여연구원 (Researcher)
  - 연구원 등급 (책임/선임/주임/일반)
  - 과제 지원인력 (행정/기술/연구보조)

Authority Model:
  - Role → Permission 매핑
  - Delegation (인간 → AI) 규칙
  - Escalation chain
  - Approval matrix
```

**왜 자체 개발?** 한국 R&D 역할 체계는 해외 PM 표준과 다름. FOAF + 자체 확장.

---

## 📝 Layer 5: Work Activity Ontology ★ 차별 핵심

### 목적
**업무일지, 지시, 보고, 계획**의 의미 체계. **이 시스템의 진입점**.

### 참고 표준

| 표준 | 관련성 |
|------|------|
| **BPMN 2.0** | 업무 프로세스 모델링 | 🟢 참고 |
| **DMN (Decision Model Notation)** | 의사결정 모델 | 🟡 |
| **Activity Streams 2.0 (W3C)** | 활동 스트림 (일지 유사) | 🟡 참고 |
| **XES (Event logs)** | 프로세스 마이닝 | 🟢 로그 분석 |

### 자체 개발 필수 (★ 최우선 IP)

```yaml
WorkLog Ontology (자체 구축):
  schema:
    - 구조화 필드 + 자유 자연어
    - Intent 분류 체계
      [완료보고, 진행보고, 계획, 블로커, 요청, 관찰, 질의]
    - Entity 언급 추출 스키마
      [Task/Person/Deliverable/Date/Risk]
    - Sentiment/Urgency 태깅

WorkDirective Ontology:
  - 지시 유형 분류
  - 권한 검증 체계
  - 분해 가능성 판정 (AI가 Task로 분해 가능한가)
  - 응답 요구 수준

WorkReport Ontology:
  - 보고 대상 (지시 응답/자발)
  - 완료 수준 분류
  - 증빙 요구 수준

WorkPlan Ontology:
  - Horizon (일/주/월)
  - Commitment level (계획/약속)
  - 조정 가능성
```

**왜 핵심 IP인가?** 
- 한국 R&D 업무 문화에 최적화된 일지/보고 패턴은 **어디에도 표준이 없음**
- 이 온톨로지의 품질 = 시스템 전체 품질

---

## ⚡ Layer 6: Event & Action Ontology

### 목적
이벤트 유형, 액션 유형, 동력학(kinetics)의 체계.

### 참고 표준

| 표준 | 관련성 |
|------|------|
| **CloudEvents (CNCF)** | 이벤트 포맷 표준 | 🟢 envelope 재사용 |
| **EventStorming** | 이벤트 모델링 방법론 | 🟢 설계 기법 |
| **DOLCE Event** | 이벤트 철학적 정의 | 🟡 |

### 자체 개발 필요

```yaml
Event Taxonomy (자체):
  - HumanEvent (6종)
  - SystemEvent (5종)  
  - AgentEvent (5종)
  - TemporalEvent (4종)
  
Action Taxonomy (자체):
  - Lifecycle Actions
  - Planning Actions
  - Coordination Actions (★ 차별)
  - Governance Actions
  
Action Contract (자체):
  - Guards (전제조건)
  - Permissions (권한)
  - Effects (효과)
  - Rollback (복구)
  - Audit (증적)
```

**CloudEvents 재사용 이점:**
Cloud-native 이벤트 포맷 표준. Kafka/EventBridge 등 인프라와 즉시 호환.

```json
{
  "specversion": "1.0",
  "type": "com.project-mgr.worklog.submitted",
  "source": "/researchers/kim",
  "id": "uuid",
  "time": "2026-04-18T08:00:00Z",
  "data": { ... }
}
```

---

## 🤖 Layer 7: Agent Capability & Communication Ontology

### 목적
AI 에이전트의 능력, 에이전트 간 소통 프로토콜.

### 권장 표준 (2024-2026 최신)

| 표준 | 용도 | 재사용 |
|------|------|------|
| **MCP (Model Context Protocol)** | Agent ↔ 도구/리소스 통신 | 🟢 **필수** |
| **A2A (Agent-to-Agent) Protocol** | Agent 간 통신 (신규) | 🟢 주시 |
| **FIPA-ACL** | 고전 Agent 통신 | 🟡 |
| **OpenAPI 3.x** | Agent 기능 명세 | 🟢 |
| **JSON-LD** | 의미 있는 JSON | 🟢 |

### 자체 개발 필요

```yaml
Agent Capability Registry (자체):
  각 Agent가 제공하는:
    - 처리 가능 Event 유형
    - 실행 가능 Action 목록
    - 입출력 스키마
    - SLA (응답시간, 신뢰도)
    - 필요 권한
  
Agent Collaboration Patterns (자체):
  - Request-Response
  - Publish-Subscribe  
  - Orchestration (Coordinator-driven)
  - Choreography (분산)
  - Negotiation (리소스 충돌 시)
```

**MCP 재사용이 왜 필수?** 
- Anthropic MCP는 2025년 이후 **de facto 표준**
- Claude/GPT/Gemini 모두 지원
- 자체 프로토콜 개발은 낭비

---

## 📏 Layer 8: Meta-Ontology (Governance)

### 목적
온톨로지 자체의 거버넌스. 변경 관리, 버전, 충돌 해결.

### 권장 표준

| 표준 | 용도 |
|------|------|
| **OWL 2** | 온톨로지 기술 언어 | 🟢 |
| **SHACL** | 제약조건 검증 | 🟢 |
| **SKOS Mapping** | 온톨로지 간 매핑 | 🟢 |
| **Git/DVC** | 버전 관리 | 🟢 |

### 자체 개발 필요

```yaml
Ontology Governance Process:
  - RFC process for changes
  - Deprecation policy
  - Backward compatibility rules
  - Extension protocols
  - Conflict resolution (예: 규칙 충돌)
  - Multilingual management (한/영)
```

---

## 📊 종합 매트릭스: 재사용 vs 자체 개발

| # | 온톨로지 | 재사용 비중 | 자체 개발 비중 | 착수 우선순위 |
|---|---------|-----------|--------------|------------|
| 1 | Upper (Time/PROV) | 95% | 5% | P1 |
| 2 | Knowledge/Document | 70% | 30% | P2 |
| 3 | R&D Project Domain | 40% | 60% ★ | **P0** |
| 4 | Actor/Role/Authority | 50% | 50% | **P0** |
| 5 | Work Activity | 20% | 80% ★★★ | **P0** |
| 6 | Event & Action | 40% | 60% | **P0** |
| 7 | Agent Capability | 60% (MCP) | 40% | P1 |
| 8 | Meta/Governance | 80% | 20% | P2 |

**평균:** 재사용 약 54% / 자체 개발 약 46%

**핵심 자체 IP:**
- Work Activity Ontology (80% 자체) ← 이게 이 시스템의 **영혼**
- R&D Project Domain의 한국 특화 부분 (60% 자체)
- Event/Action Taxonomy (60% 자체)

---

## 🎯 MVP 온톨로지 구축 계획

### MVP에 반드시 필요한 최소 집합 (P0)

```yaml
MVP Ontology Bundle:
  
  Foundation:
    - PROV-O (Decision/Evidence 기록)
    - OWL-Time (모든 시간 표현)
    - FOAF (Person/Team)
  
  Domain (한정):
    - R&D Project (1-2 유형만)
    - PMBOK Core (Scope/Schedule/Risk)
    - TRL (9단계 정의)
  
  Work Activity (필수):
    - WorkLog 스키마 ★
    - Intent 분류 (7-10개)
    - Entity 추출 패턴
  
  Actor:
    - 4개 역할 (총괄/PL/서브PL/연구원)
    - 기본 Delegation matrix
  
  Event/Action:
    - 5개 Event 유형
    - 4-6개 Action 유형
  
  Agent:
    - MCP 프로토콜 채택
    - Capability registry 스키마
```

### MVP 구축 기간 추산

```
Week 1-2: 표준 채택 + 통합 (PROV-O, OWL-Time, FOAF, MCP)
Week 3-4: Work Activity Ontology 설계 ★ 핵심
Week 5-6: R&D Domain 1개 유형 + Role + Delegation
Week 7-8: Event/Action Taxonomy + 통합 검증
Week 9-10: End-to-end 시나리오 검증

총 10주 (2.5개월) MVP 온톨로지 구축
```

---

## 🎬 리드의 결론

### 이전 설계의 보완점
- "운영 온톨로지(operational ontology)" 문서는 **시스템 설계** 
- 이 문서가 **"그 시스템이 작동하기 위해 필요한 온톨로지 카탈로그"**
- 둘은 **보완적**, 둘 다 필요

### 실용적 권장

1. **표준 최대 재사용** — PROV-O, OWL-Time, FOAF, MCP, Dublin Core
2. **3개 영역에 자체 투자 집중:**
   - Work Activity Ontology (80% 자체)
   - 한국 R&D Domain 특화 부분
   - Event/Action Taxonomy
3. **MVP는 얇게** — 1개 유형, 4개 역할, 5개 이벤트로 시작
4. **확장성 설계** — 나중에 유형 추가 시 기존 구조 유지

### 리드 결정 요청
- ✅ 이 **8-Layer Ontology Stack**을 공식 채택?
- ⚙️ 다음 문서로 "Layer 5: Work Activity Ontology 상세 설계" 작성 시작? (가장 핵심 IP)
- 🔄 또는 "MVP Ontology Bundle — 10주 상세 계획" 작성?
