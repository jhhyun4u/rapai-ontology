# ADR-001: Ontology Strategy — 온톨로지 전략 확정

**결정일:** 2026-04-18
**상태:** ✅ Accepted (확정)
**결정자:** 프로젝트 오너 (hyunjaeho@tenopa.co.kr)
**검토 주기:** 분기 1회 또는 주요 충돌 발생 시

---

## 🎯 결정 맥락 (Context)

본 프로젝트(AI-Native R&D Project Management Platform)는 다음 4가지를 동시에 달성해야 한다:

1. **다중 에이전트 협력** — Coordinator AI + Specialist Agents가 공유 어휘로 협업
2. **Hallucination 제로** — LLM 자유 추론을 구조로 제한
3. **완전한 의사결정 추적** — 정부 R&D 감사·특허 방어에 필수
4. **한국 R&D 도메인 특화** — 과제/사업단/TRL/NTIS 등 용어를 LLM이 오역하지 않도록

이 4가지는 "온톨로지" 없이는 구조적으로 달성 불가하다.  
그러나 **어떤 수준의 온톨로지**인가가 결정의 핵심이었다.

---

## 🔍 고려한 대안 (Options Considered)

| 대안 | 장점 | 단점 | 채택 여부 |
|------|-----|------|---------|
| L0. 무 온톨로지 (DB 스키마만) | 단순 | 에이전트 협력·추적 불가 | ❌ 기각 |
| L1. 태그 레지스트리만 | 구현 쉬움 | 사용자 부담 큼, NL-First 비전 상실 | ❌ 기각 |
| **L2.5. Typed + Object/Link/Action** | 균형 | 중간 수준 유지보수 | ✅ **채택** |
| L4. W3C OWL/SHACL 형식 온톨로지 | 표준 호환 | 소팀 유지보수 불가 | ❌ 기각 |
| L5. Upper Ontology + 도메인 전층 | 완벽 | 10배 과잉 | ❌ 기각 |
| Palantir Foundry 풀 채택 | 강력 | 수백만달러/년, 100+명 필요 | ❌ 기각 |

---

## ✅ 확정 결정 6가지

### 결정 1 — 온톨로지 레벨: L2.5
- **Typed Concepts + Object/Link/Action 3축 + 선택적 Event 타입**
- OWL/RDF/SHACL은 **도입하지 않음**
- JSON Schema 수준 타입 제약 + 관계 타입 + 액션 타입으로 충분

### 결정 2 — Palantir는 철학만 차용, 플랫폼 미채택
- ✅ 차용: Object/Link/Action 개념, Action-First 사고, Write-back Discipline, Kinetic Layer 철학
- ❌ 불채택: Foundry 플랫폼, Workshop UI, AIP 라이선스, 엔터프라이즈 거버넌스
- **비유:** "항공모함 말고 고속 프리깃함" — 소수 정예·빠른 기동 적합

### 결정 3 — 실전 뼈대: DDD + Event Storming
- Domain-Driven Design(DDD) + 이벤트 스토밍을 **실전 모델링 방법론**으로 채택
- Palantir 개념 모델을 그 위에 얹음
- Bounded Context로 R&D 도메인 분할

### 결정 4 — 표준 최대 재사용
- **PROV-O** (출처·추적) → 감사 로그에 필수
- **CloudEvents** (이벤트 엔벨로프) → 이벤트 라우팅 포맷
- **MCP** (에이전트 I/O 계약) → 모든 Agent Capability는 MCP 스타일
- **FOAF** (인물·조직) → 연구진 네트워크
- **Frascati Manual** (R&D 분류) → 프로젝트 유형 분류 근거
- **NTIS 분류체계** (한국 특화) → 한국 R&D 용어 정규화
- 한국 R&D 도메인 고유 부분(과제/사업단/13태그 등)만 자체 개발

### 결정 5 — JSON Schema가 SSOT (Single Source of Truth)
- 온톨로지 정의의 **정본은 JSON Schema 파일**
- OWL, Markdown 문서, LLM 프롬프트는 모두 JSON Schema에서 생성되는 **파생물**
- SemVer 버전 관리 (`v1.0.0` → `v1.1.0` 추가 → `v2.0.0` 파괴적 변경)
- **Append-Only Core**: 코어 Object/Link는 삭제하지 않고 Deprecate 마킹만

### 결정 6 — MVP는 8~10개 Object로 시작, Bottom-Up 증설
- 초기 Object 풀: Project, Task, WorkLog, WorkDirective, Person, Role, Milestone, Blocker, Decision, Event (±2)
- 전담 온톨로지 엔지니어 **불필요** (PL급 1인 오너 겸직)
- 매 2주 리뷰에서 LLM 파싱 저confidence 신호를 모아 신규 Object 승격 판단

---

## 📋 운영 거버넌스 5규칙

| 규칙 | 내용 |
|------|------|
| R1. SemVer | `MAJOR.MINOR.PATCH` 의미론 준수 |
| R2. Append-Only Core | 코어는 삭제 금지, Deprecate만 |
| R3. JSON Schema = SSOT | 문서·프롬프트·OWL은 모두 파생물 |
| R4. LLM Prompt Binding | 모든 Intent/Entity 정의는 LLM 시스템 프롬프트에 자동 주입 (단일 소스) |
| R5. Event-Signal Evolution | 저confidence 파싱 실패를 월 1회 확장 회의 근거로 |

---

## 🔗 영향받는 문서

### 이 결정이 우선(Supersede)하는 부분
- `mindvault/ontology/06-ontology-design-charter.md` §AD-001~AD-005 — Palantir 완전 채택 뉘앙스 → **철학 차용만으로 조정**
- `mindvault/ontology/08-ontology-stack-catalog.md` — 8-Layer는 참고용 카탈로그로 유지, **강제 구현 대상 아님**

### 이 결정과 정합하는 문서 (보존)
- `mindvault/ontology/07-operational-ontology-design.md` — Event-Driven Agentic OS 비전
- `mindvault/ontology/09-work-activity-ontology.md` — NL-First Intent/Entity 설계
- `mindvault/ontology/05-project-types-and-terms.md` — 프로젝트 유형·TRL/CRL 라우팅 키

---

## 🚦 후속 실행 항목

- [ ] MVP 8~10 Object를 Event Storming으로 도출 (별도 세션)
- [ ] 각 Object의 JSON Schema 초안 작성
- [ ] 연구자 일지 샘플 5~10건으로 파싱 검증 시뮬레이션
- [ ] `mindvault/ontology/00~09`에 본 ADR 참조 헤더 추가

---

## ♻️ 재검토 트리거 (Revisit When)

- MVP 운영 6개월 시점의 회고
- JSON Schema SSOT가 실제 LLM 통합에서 한계 노출 시
- OWL/SHACL 도입 필요성을 강하게 요구하는 외부 규제 변화 발생 시
- Palantir/Foundry 오픈소스 대체재 성숙도가 전환을 정당화할 시

---

**이 결정의 한 줄 요약:**  
"온톨로지는 필요하되 **형식적 Semantic Web은 과잉**. L2.5(Typed + O/L/A) + 표준 재사용 + JSON Schema SSOT로 간다."
