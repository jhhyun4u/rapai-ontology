# 02. Specialized AI Model — 특화 AI 모델 개념·방법·13 AG-xxx 매핑

**작성일:** 2026-04-18
**상태:** ✅ Active (ADR-002 결정 7~22 기반)
**근거:** `decisions/002-ai-model-architecture.md`
**관련:** `system/01-harness-engineering.md`, `ontology/10-project-type-classification-v2.md`

> **이 문서의 역할**
> RAPai의 "특화 AI 모델"을 **개념**(무엇인가) · **방법**(어떻게 만드는가) · **배치**(13 AG-xxx 어디에 쓰는가)의 세 축으로 정의한다.
> ADR-002는 결정 그 자체를, 본 문서는 결정의 **설계 논리와 운영 가이드**를 다룬다.

---

## 1. 특화 AI 모델의 정의

### 1.1 개념 정의

**범용 Foundation Model의 대비 개념**으로, 다음 4가지 축에서 최적화된 모델·모델군의 집합체를 말한다.

| 축 | 범용 Foundation Model | RAPai 특화 AI 모델 |
|---|---|---|
| 도메인 | 전 세계 일반 지식 | 한국 R&D 프로세스 + PMBOK + NPD |
| 태스크 | 열린 대화·생성 | WBS 8유형 분류 / 일지 파싱 / Gate 판정 / 보고서 생성 |
| 데이터 | 웹 크롤링 | NTIS·규정·내부 계획서·일지 |
| 제약 | 클라우드 호출 허용 | 보안등급별 라우팅(PUBLIC~SECRET) + Hallucination-Zero |

### 1.2 "하나의 모델"이 아닌 "모델 포트폴리오"

RAPai 특화 AI 모델은 **단일 초거대 LLM**이 아니라 **4종 이종 모델의 협력체**다.

```
┌──────────────────────────────────────────────────────────┐
│ 유형 ① 도메인 특화 LLM                                     │
│   Research Manager LLM (Gemma 4 31B-MoE + LoRA SFT)      │
│   Parser LLM (Gemma 4 4B + QLoRA)                        │
│   외부 API (Claude Sonnet 4.6 — PUBLIC·RESTRICTED 전용)   │
│   → 자연어 접점·지식 합성·문서 생성 담당                    │
├──────────────────────────────────────────────────────────┤
│ 유형 ② 태스크 특화 소형 모델 (5종)                         │
│   ModernBERT-ko 400M — WBS 8유형 Classifier              │
│   Bi-encoder + BGE-Reranker — 시장적합성 Scorer           │
│   Temporal Fusion Transformer — 소요예측 Forecaster       │
│   Heterogeneous R-GCN — Task Graph GNN                   │
│   Isolation Forest / LSTM-AE — 이상탐지                    │
│   → 수치·회귀·그래프·분류 담당 (LLM 비대체 영역)            │
├──────────────────────────────────────────────────────────┤
│ 유형 ③ 수학 알고리즘 엔진                                   │
│   OR-Tools CP-SAT (MILP) — 자원배분 최적해                 │
│   RL Agent (SB3 PPO, Year 2+) — 동적 스케줄링              │
│   Rule Engine (Python pure) — EVM·SPI·DoD·L1·L2-C Gate   │
│     ⭐ 특허 CP3: 수치판정 LLM 배제                          │
│   → 최적화·판정 담당                                        │
├──────────────────────────────────────────────────────────┤
│ 유형 ④ RAG-Enhanced Retrieval                             │
│   BGE-M3 + KURE Embedding                                 │
│   Qdrant (main_corpus + contract_research_corpus)         │
│   Neo4j Enterprise (GATE_DECISION 그래프)                  │
│   PostgreSQL 16 + pg_audit (SSOT)                         │
│   → 지식·근거 검색 담당 (LLM Hallucination 방어 필수)       │
└──────────────────────────────────────────────────────────┘
```

**특화 AI 모델 = ① + ② + ③ + ④의 Hybrid 조합**
단일 모델로는 RAPai의 4대 목표(유형별 차별화 / 계획서→관리 자동화 / Hallucination-Zero / 보안등급 준수)를 달성할 수 없다.

---

## 2. 특화 방법 5가지

모델을 "특화"시키는 방법은 기술적으로 5가지가 존재하며, RAPai는 이를 **혼합 적용**한다.

### 2.1 방법 비교표

| 방법 | 비용 | 데이터 요구 | 적용 시점 | RAPai 적용처 |
|---|---|---|---|---|
| **Continued Pre-training** | 높음 (수억원, A100 수주) | 10만~ 코퍼스 | Phase 4+ (선택) | 후속 단계 도메인 LLM 1차 특화 |
| **SFT + LoRA** | 중 (수천만원, A100 수일) | 1,000~10,000 페어 | Phase 1 주력 | Research Manager LLM (7,800 페어) |
| **QLoRA** | 낮음 (수백만원, 1 GPU) | 500~2,000 페어 | Phase 1 병행 | Parser LLM (2,000 페어, 4-bit) |
| **DPO** | 중 (수천만원) | 2,000 선호 페어 | Phase 3 (Year 2) | Research Manager LLM 톤·품질 개선 |
| **RAG + Few-shot** | 낮음 (즉시) | 도큐먼트 DB만 | Phase 0부터 상시 | 전 LLM 입출력 경로 |

### 2.2 왜 Full Fine-tuning이 아닌 LoRA/QLoRA인가

| 고려 요인 | Full FT | LoRA/QLoRA | 결론 |
|---|---|---|---|
| 학습 비용 | 31B 모델 Full FT: A100 8장×주일 | r=32 기준 <1% 파라미터만 업데이트 | LoRA 압도 |
| 베이스 모델 버전업 대응 | 재학습 전체 | Adapter만 재학습 | LoRA 압도 |
| 저장 용량 | 62GB × 버전 | 수백MB × 버전 | LoRA 압도 |
| 도메인 지식 주입 | ✅ 강력 | 🟡 중상 (RAG 보완으로 충분) | RAPai 요구 수준 충족 |
| 배포 유연성 | 어려움 | 여러 Adapter 스위칭 | LoRA 압도 |

**결정 근거:** RAPai의 학습 데이터 규모(2,000~7,800페어)와 Phase 1 일정(M3~M8)에서는 LoRA가 최적. Full FT는 Phase 4+ 에서 데이터 10만+ 확보 시 재검토.

### 2.3 RAG가 왜 Fine-tuning의 대체가 아니라 보완인가

| 측면 | Fine-tuning | RAG | 상호작용 |
|---|---|---|---|
| **스타일·톤** | ✅ 학습 가능 | ❌ 불가 | FT 전담 |
| **최신 정보** | ❌ 학습 시점 고정 | ✅ 실시간 업데이트 | RAG 전담 |
| **출처 제시** | ❌ 증거 無 | ✅ 문서 ID·위치 | RAG 전담 (Hallucination-Zero L5) |
| **희소 지식** | 🟡 과적합 위험 | ✅ 검색으로 해결 | RAG 유리 |
| **구조화 출력** | ✅ Schema 학습 | 🟡 프롬프트 의존 | FT 유리 |

→ **결정:** LoRA SFT (스타일·구조) + RAG (근거·최신성) **둘 다** 의무.

---

## 3. 왜 "생성형 LLM이 중심"인가

### 3.1 LLM 대체 불가능 5대 영역

다음 5개 영역은 ML/OR/Rule로 **대체 불가**하며, RAPai의 사용자 가치 대부분이 여기서 발생한다.

| 영역 | LLM만 가능한 이유 | RAPai 적용 |
|---|---|---|
| **자연어 입력 해석** | 계획서·일지·메모의 비정형 긴 문맥 처리 | Parser LLM → 온톨로지 객체화 |
| **지식 합성·추론** | 다수 문서·규정·사례의 종합 | Research Manager LLM + RAG |
| **문서 생성** | 주간/월간/중간/최종 보고서 + 정부양식 | AG-REPORT → Gate 패키지 조립 |
| **Coordinator 대화** | NL-First 의도파악 + 도구호출 + 라우팅 | AG-INT (특허 CP1) |
| **XAI surface** | ML/OR의 수치 결정을 사람에게 설명 | "왜 이 자원 배치인가?" 답변 |

### 3.2 LLM이 "보조역"인 영역 (특허 CP3)

반대로 다음 영역은 LLM이 **주력이 되면 안 된다** — 환각 리스크가 치명적이거나 결정론이 필수이기 때문.

| 영역 | 주력 모델 | LLM 역할 | 이유 |
|---|---|---|---|
| 수치 회귀 (소요예측) | TFT, LightGBM | 결과 해석 설명만 | 환각·재현성 결여 |
| 조합 최적화 (자원배분) | MILP, CP-SAT | 사용자 의도→제약식 변환만 | 최적성 보장 불가 |
| 수치 판정 (EVM/SPI/DoD) | Rule Engine | 절대 개입 금지 ⭐ | 특허 CP3 핵심 |
| L1 TRL/CRL Gate | Rule Engine | 절대 개입 금지 ⭐ | 특허 CP3 핵심 |
| L2-C Client Acceptance | Rule Engine | 절대 개입 금지 ⭐ | 계약적 구속력 |
| 이상탐지 | Isolation Forest, LSTM-AE | 원인 설명만 | 오탐·미탐 정량 보장 필요 |

### 3.3 중심 원칙 한 줄 요약

> **"사용자 접점·지식처리·문서생성은 LLM이 주축 · 수치·그래프·판정은 ML/OR/Rule이 전담"**
> 이 경계가 흐려지면 특허 CP3 위반 + Hallucination-Zero 파기.

---

## 4. 5-Tier Hybrid 아키텍처 (13 AG-xxx 매핑)

ADR-002 결정 11에서 확정된 5-Tier. 각 AG-xxx가 어떤 Tier의 어떤 모델을 호출하는지 명시한다.

### 4.1 Tier 1 — COORDINATOR LAYER

**담당 AG:** AG-INT (Coordinator Agent)
**담당 모델:**
- PUBLIC·RESTRICTED 데이터 → Claude API Sonnet 4.6
- CONFIDENTIAL·SECRET 데이터 → 로컬 Gemma 4 31B-MoE + LoRA SFT
**역할:**
- NL-First 의도파악 (특허 CP1 Intent Routing)
- 13 Specialist 라우팅 결정
- Gate 패키지 최종 조립 + PI 결정 지원
- 사용자 대화 기록 → PROV-O Lineage 기록 (특허 CP5)

**특징:** 보안등급 라우팅의 **단일 진입점**. 모든 외부 API 호출은 AG-INT 경유.

### 4.2 Tier 2 — SPECIALIST AGENT LAYER (12 Specialist)

12개 AG-xxx 각각의 주 모델 매핑:

| AG | PMBOK 영역 | 주 LLM | Task-Specific 모델 | Rule Engine | 핵심 역할 |
|---|---|---|---|---|---|
| **AG-SCOPE** | Scope | Research Manager LLM | — | — | WBS 구조화·범위 변경 |
| **AG-SCHED** | Schedule | 설명 LLM (Coordinator 위임) | Heterogeneous R-GCN (GNN) | CPM Critical Chain | 임계경로 재계산 |
| **AG-KPI** | Integration / Perform. | Research Manager LLM | — | ✅ L1 TRL/CRL + L3 성과 판정 | 3계층 KPI + 스냅샷 |
| **AG-BUDGET** | Cost | 설명 LLM (Coordinator 위임) | TFT Forecaster (비용예측) | ✅ EVM/SPI/CPI 판정 (CP3) | 예산·계약금 Tranche |
| **AG-IP** | (확장 영역) | Research Manager LLM | — | — | 특허·IP 라이프사이클 |
| **AG-SENSE** | Risk (확장) | Research Manager LLM | Isolation Forest + LSTM-AE | — | CRITICAL 신호 → L4 트리거 |
| **AG-REPORT** | Communications | Research Manager LLM | — | — | Gate 패키지 자동 조립 |
| **AG-TEAM** | Resource (내부) | Research Manager LLM | LightGBM (투입률 예측) | — | 팀 투입·이탈 위험 |
| **AG-STAKE** | Stakeholder | Research Manager LLM | — | — | 외부 이해관계자 관리 |
| **AG-CHANGE** | Change Control | Research Manager LLM | — | Append-only 검증 | GATE_CRITERIA 버전 관리 |
| **AG-QA** | Quality | Research Manager LLM | Bi-encoder Scorer (시장적합성) | ✅ DoD 판정 (CP3) + L2-C | 품질·검수 |
| **AG-RISK** | Risk | Research Manager LLM | Isolation Forest (이상치) | — | 리스크 레지스터 |
| **AG-COMMS** | Communications | Research Manager LLM | — | — | 공지·알림·임박 Alert |

**규칙:**
1. **Task-Specific 모델이 있는 AG는 먼저 호출** → 그 결과를 LLM이 "해석·요약"만 담당
2. **Rule Engine 필수 AG는 LLM 개입 금지** (AG-KPI·AG-BUDGET·AG-QA의 판정 단계)
3. **학술연구용역 활성화 시** 6개 AG 가중치 상향: STAKE·QA·SCOPE·BUDGET·REPORT·COMMS

### 4.3 Tier 3 — TASK-SPECIFIC ML/DL LAYER

5종 소형 모델의 운영 사양:

| 모델 | 구조 | 입력 | 출력 | 사용 AG | 학습 데이터 |
|---|---|---|---|---|---|
| **WBS 8유형 Classifier** | ModernBERT-ko 400M + head | 계획서 텍스트 1~3장 | 8-class softmax + confidence | AG-INT (Intake), AG-SCOPE | 2,000건 |
| **시장적합성 Scorer** | Bi-encoder + BGE-Reranker | 기술설명 + 시장 쿼리 | 0~1 점수 + top-k 근거 | AG-QA, AG-STAKE | 500건 페어 |
| **소요 TFT Forecaster** | Temporal Fusion Transformer | 과거 EVM·시계열 | MAPE 기반 예측 | AG-SCHED, AG-BUDGET | NTIS + 내부 1,500건 |
| **Task Graph GNN** | Heterogeneous R-GCN (PyG) | WBS 노드 + 의존성 | 임계경로 노드셋 | AG-SCHED | WBS 그래프 500건 |
| **이상탐지** | Isolation Forest + LSTM-AE | 일지 태그 + KPI 시계열 | 이상점수 + 원인 후보 | AG-SENSE, AG-RISK | 비지도 전체 |

### 4.4 Tier 4 — ALGORITHMIC ENGINE LAYER

**Rule Engine 경계 (특허 CP3):**

```
┌───────────────────────────────────────────────────────┐
│ Rule Engine 단일 엔트리 (Python pure, LLM 차단)       │
├───────────────────────────────────────────────────────┤
│ 1. EVM Calculator — CV/SV/CPI/SPI 판정                │
│ 2. L1 TRL Gate — TRL 1~9 산식 규정                    │
│ 3. L1 CRL Gate — CRL 1~9 산식 규정                    │
│ 4. L2 Stage Must Criteria — 유형별 체크리스트         │
│ 5. L2-C Client Acceptance — 고객 서명 유일 조건 ⭐    │
│ 6. L3 성과목표 달성도 — 정량 계산                      │
│ 7. Valley of Death Rule — TRL-CRL Gap ≥ 3 & CRL < 4   │
│ 8. DoD Checker — Definition of Done 판정              │
└───────────────────────────────────────────────────────┘
           ↓
    PROV-O Lineage 자동 기록
    (model_id = "rule-engine-v1.0")
```

**OR 최적화:**
- OR-Tools CP-SAT (MILP): 자원배분 가장 하드한 경우
- RL Agent (SB3 PPO): Year 2+, 동적 일정 재배치

### 4.5 Tier 5 — KNOWLEDGE & RETRIEVAL LAYER

**RAG Stack 구성:**

```
입력 쿼리 (NL)
  ↓
BGE-M3 + KURE Embedding (한국어 강화)
  ↓
Qdrant Hybrid Search (BM25 + Dense)
  ├─ main_corpus (일반)
  └─ contract_research_corpus (학술연구용역 전용)
  ↓
BGE-Reranker (top-50 → top-5)
  ↓
LLM에 Citation과 함께 주입 (Hallucination-Zero L5)
  ↓
Neo4j GATE_DECISION 그래프 조회 (근거 연결)
  ↓
PostgreSQL SSOT 검증 (Fact-Check)
```

---

## 5. Cross-cutting 메커니즘

5-Tier 전체를 가로지르는 4가지 공통 메커니즘.

### 5.1 PROV-O Lineage (특허 CP5)

**모든 Tier의 입출력·model_id·version·timestamp 자동 기록.** 감사·특허 방어·책임 추적의 단일 진실.

```
[입력] → [모델 A] → [중간 결과] → [모델 B] → [출력]
   ↓         ↓           ↓           ↓         ↓
  ID1       M_A,v1      ID2       M_B,v2    ID3
   └─────────┴───────────┴───────────┴─────────┘
              PROV-O 체인 (Append-only)
```

### 5.2 Outbox Pattern

PostgreSQL → Neo4j/Redis 전파. 분산 트랜잭션 실패 방지 (v2.9 원칙 유지).

### 5.3 ABAC (4속성)

- Subject: 사용자 역할·소속
- Resource: 프로젝트 security_tier + 문서 분류
- Environment: 시간·IP·디바이스
- Action: read/write/exec

→ **보안등급별 LLM 라우팅의 기준** (Tier 1에서 적용)

### 5.4 Hallucination-Zero 7계층 방어

모든 LLM 출력이 **7계층을 순차 통과**해야 사용자에게 도달.

| 계층 | 방어 기법 | 실패 시 |
|---|---|---|
| **L1** | Structured Output (JSON Schema) | 파서 에러 → 재생성 |
| **L2** | Ontology 제약 (Work/Activity/Intent/Entity) | 온톨로지 외 개체 차단 |
| **L3** | Confidence Threshold (≥ 0.7) | 재시도 or 사용자 확인 |
| **L4** | Rule Engine 라우팅 (CP3) | 수치판정은 LLM 차단 |
| **L5** | Citation 의무 (모든 factual claim) | 출처 없으면 reject |
| **L6** | Retrieval Verification (RAG 결과 재조회) | 불일치 시 reject |
| **L7** | PROV-O Lineage (감사 추적) | 추적 불가 시 reject |

---

## 6. 13 AG-xxx × 5-Tier 통합 매트릭스

| AG | T1 LLM | T2 LLM (주력) | T3 소형 | T4 Rule/OR | T5 RAG |
|---|---|---|---|---|---|
| AG-INT | ✅ Claude/Gemma 라우팅 | — | ✅ Classifier (Intake) | — | ✅ 전체 |
| AG-SCOPE | — | ✅ Research Mgr | — | — | ✅ main |
| AG-SCHED | — | 🟡 설명만 | ✅ GNN | ✅ CPM | ✅ main |
| AG-KPI | — | ✅ Research Mgr | — | ✅ TRL/CRL Rule | ✅ main |
| AG-BUDGET | — | 🟡 설명만 | ✅ TFT | ✅ EVM Rule | ✅ main |
| AG-IP | — | ✅ Research Mgr | — | — | ✅ main |
| AG-SENSE | — | ✅ Research Mgr | ✅ IF+LSTM-AE | — | ✅ main |
| AG-REPORT | — | ✅ Research Mgr | — | — | ✅ main + contract |
| AG-TEAM | — | ✅ Research Mgr | ✅ LightGBM | — | ✅ main |
| AG-STAKE | — | ✅ Research Mgr | — | — | ✅ main + contract |
| AG-CHANGE | — | ✅ Research Mgr | — | ✅ Append-only | ✅ main |
| AG-QA | — | ✅ Research Mgr | ✅ Scorer | ✅ DoD + L2-C | ✅ main + contract |
| AG-RISK | — | ✅ Research Mgr | ✅ IF | — | ✅ main |
| AG-COMMS | — | ✅ Research Mgr | — | — | ✅ main |

**범례:** ✅ 필수 사용 / 🟡 결과 해석만 / — 미사용

---

## 7. 운영 원칙 (Operating Principles)

### 7.1 모델 선택 원칙

1. **보안등급 우선:** 데이터 security_tier → 라우팅 결정 (Claude / Gemma / EXAONE)
2. **지연 요구 우선:** 실시간 파싱 < 1초 → Parser LLM 4B 강제
3. **수치판정 금지:** Rule Engine 경로 고정 (CP3)
4. **RAG 의무:** factual claim 모든 LLM 출력에 Citation

### 7.2 모델 버전 관리

- 모든 모델에 `model_id` + `version` + `training_data_hash` 기록
- PROV-O 노드에 필수 포함
- ADR-002 결정 변경 시 **Superseded 선언** + 신 버전 ADR

### 7.3 Canary & Rollback

- Phase 1 신규 모델 배포 시 10% Canary → 4주 관찰 → 100% 전환
- Rule Engine 룰 변경은 Append-only, 이전 룰 보존
- 롤백 기준: Gold Set F1 회귀 ≥ 3pp 또는 Hallucination율 ≥ 1%

### 7.4 학술연구용역 (contract_research) 특별 조치

- AG 가중치 자동 상향 (6개 AG): STAKE·QA·SCOPE·BUDGET·REPORT·COMMS → high
- Qdrant collection 분리: `contract_research_corpus`
- 학습 데이터 ≥ 30% 의무 (전체 2,000건 중 600건)
- L2-C Client Acceptance Gate는 Rule Engine 전담

---

## 8. 참조 문서

- `decisions/002-ai-model-architecture.md` — 결정 7~22 원문
- `decisions/001-ontology-strategy.md` — 결정 1~6 (온톨로지 전제)
- `ontology/10-project-type-classification-v2.md` — WBS 8유형 + Cross-cutting
- `llm/01-model-selection.md` — 모델 선정 상세 근거
- `llm/02-finetuning-roadmap.md` — Phase 0~4 파인튜닝 로드맵
- `llm/03-evaluation-framework.md` — 평가 메트릭 + Gold Set
- `llm/04-security-tier-routing.md` — 보안등급 라우팅 운영 가이드
- `특허관련 문서/RD_AI_에이전트_길목특허_명세서_v3.md` — CP1~CP5

---

## 9. 변경 이력

| 버전 | 일자 | 변경 사항 |
|---|---|---|
| 1.0 | 2026-04-18 | 최초 작성 (ADR-002 결정 7~22 반영) |

---

**이 문서의 한 줄 요약**
"RAPai 특화 AI 모델 = ① 도메인 LLM(Gemma/Claude/Parser) + ② 태스크 소형 5종 + ③ OR·Rule Engine + ④ RAG의 Hybrid. 생성형 LLM이 Tier 1·2에서 사용자 접점·지식·문서 5대 영역 전담, ML/OR/Rule이 Tier 3·4에서 수치·그래프·판정 전담. 특허 CP3(수치판정 분리) + Hallucination-Zero 7계층 + PROV-O(CP5) 필수."
