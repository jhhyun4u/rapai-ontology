# ADR-002: AI Model Architecture — RAPai 특화 AI 모델 아키텍처 확정

**결정일:** 2026-04-18
**상태:** ✅ Accepted (확정)
**결정자:** 프로젝트 오너 (hyunjaeho@tenopa.co.kr)
**선행 ADR:** ADR-001 (Ontology Strategy)
**관련 문서:**
- `C:\claude\plans\memoized-mapping-dongarra.md` (Final Plan v2.9 정합판)
- `mindvault/ontology/10-project-type-classification-v2.md` (WBS 8유형 + Cross-cutting)
- `RAPai_통합설계명세서_v2.9.md` (시스템 근간)
**검토 주기:** 분기 1회 또는 주요 충돌 발생 시

---

## 🎯 결정 맥락 (Context)

RAPai(Research AI Platform)는 v2.9 통합설계명세서에서 확정된 시스템 근간을 보존하면서, 특화 AI 모델 계층의 상세 설계를 공식화할 필요가 있다. 동시에 사용자 피드백에 따른 두 가지 핵심 조정을 반영해야 한다:

1. **프로젝트 유형 분류 재설계** — v2.9의 6유형을 WBS 성격 8유형 + Cross-cutting 속성 2축으로 재편
2. **학술연구용역 관리 모듈 First-class화** — TENOPA 주 수익원으로서 robust한 PM 지원 필요

본 ADR은 **결정 7 ~ 결정 22** (총 16개)를 공식화하여, AI 모델 포트폴리오·보안등급 라우팅·파인튜닝 로드맵·학습 데이터 할당·Hallucination 방어·학술연구용역 모듈을 확정한다.

---

## 🔍 대안 검토 요약 (Options Considered)

| 영역 | 대안 | 채택 여부 |
|---|---|---|
| 시스템 브랜드 | 신규 명칭 / RAPai 유지 | ✅ **RAPai 유지** (v2.9 준용) |
| 프로젝트 유형 | v2.9 6유형 유지 / 9-카테고리 재설계 / **WBS 8유형 + Cross-cutting** | ✅ **WBS 8유형 + Cross-cutting** |
| 학술연구용역 위치 | 독립 유형(Framing 1) / **Cross-cutting 속성 + First-class 관리 모듈(Framing 2+)** | ✅ **Framing 2+** |
| LLM 전략 | 단일 클라우드 / 단일 로컬 / **보안등급 라우팅 하이브리드** | ✅ **하이브리드** |
| 로컬 LLM | EXAONE 3.5 단일 / LLaMA 단일 / **Gemma 4 Primary + EXAONE 4.0 Baseline** | ✅ **Gemma 4 + EXAONE 4.0** |
| FT 방법 | Full FT / **LoRA + QLoRA + DPO + RAG 하이브리드** | ✅ **LoRA 하이브리드** |
| 수치판정 | LLM 자유 추론 / **Rule Engine 분리 (특허 CP3)** | ✅ **Rule Engine 분리** |

---

## ✅ 확정 결정 16가지 (결정 7~22)

### 결정 7 — 시스템 브랜드 = RAPai (Research AI Platform)
- v2.9 통합설계명세서 준용. 향후 모든 산출물·문서·API·UI에서 공식 명칭.
- 영문: Research AI Platform. 한글: 연구 AI 플랫폼.

### 결정 8 — 프로젝트 유형 = WBS 8유형 + Cross-cutting 속성 (v2.0)
- **WBS 8유형**: A 탐구형 / B 개발형 / C 사업화·실증형 / D 조사·분석형 / E 기획·전략형 / F 컨설팅형 / G 복합·전주기형 / H 행사운영형
- **Cross-cutting 속성**: `contract_modality` · `funding_source` · `security_tier` · `scale_tier`
- v2.9의 6유형 체계는 본 v2.0 체계로 supersede (매핑 테이블은 `mindvault/ontology/10-project-type-classification-v2.md` 참조)
- SemVer v2.0.0 (MAJOR bump)

### 결정 9 — Gate 계층 = L1 TRL/CRL / L2 Stage / L3 Annual / L4 Moving Target (유형별 활성화) + L2-C (Client Acceptance)
- L1 TRL: 유형 A·B 활성화
- L1 CRL: 유형 C 활성화
- L2 Stage: 유형 A·B(기술) / C(사업성) / D·E(품질) / F(마일스톤)
- L3 Annual: 유형 A~G 전체. 유형 H 제외.
- L4 Moving Target: 유형 A·B·C 전체 / D·E 선택적(△) / F·H 미적용
- **L2-C Client Acceptance Gate**: `contract_modality = contract_research`일 때 모든 유형에 cross-cutting으로 활성화. 고객 서명 = 유일한 통과 조건.

### 결정 10 — 에이전트 구조 = 13 PMBOK-based AG-xxx + LangGraph StateGraph
- Coordinator: **AG-INT** (사용자 접점 1개)
- Specialist 12: AG-SCOPE, AG-SCHED, AG-KPI, AG-BUDGET, AG-IP, AG-SENSE, AG-REPORT, AG-TEAM, AG-STAKE, AG-CHANGE, AG-QA, AG-RISK, AG-COMMS
- Orchestration: LangGraph StateGraph
- v2.9 에이전트 구조 그대로 유지

### 결정 11 — 5-Tier Hybrid AI 아키텍처
```
Tier 1. Coordinator Layer (AG-INT) ⭐ LLM 중심
Tier 2. Specialist Agent Layer (12 AG-xxx) ⭐ LLM 중심
Tier 3. Task-Specific ML/DL Layer (5종 소형 모델)
Tier 4. Algorithmic Engine Layer (OR-Tools CP-SAT + RL + Rule Engine)
Tier 5. Knowledge & Retrieval Layer (RAG: BGE-M3 + Qdrant + Neo4j + PostgreSQL)
Cross-cutting: PROV-O Lineage (CP5), Outbox, ABAC, DLQ, Hallucination-Zero 7계층
```

### 결정 12 — 생성형 LLM = Tier 1·2 중심축
LLM이 대체 불가능한 5대 영역 전담:
1. 자연어 입력 해석 (계획서·일지·메모)
2. 지식 합성·추론 (다수 문서·규정·사례 종합)
3. 문서 생성 (주간/월간/중간/최종 보고서, 정부양식)
4. Coordinator 대화 (NL-First 의도 파악 + 도구 호출 + 라우팅)
5. XAI Surface (ML/OR 수치 결정의 인간 설명)

ML/OR/Rule 전담 영역 (LLM 보조만):
- 수치 회귀 (소요예측) → TFT · LightGBM
- 조합 최적화 (자원배분) → MILP · CP-SAT
- 수치 판정 (EVM/SPI/DoD) → Rule Engine (특허 CP3)
- 이상탐지 → Isolation Forest · LSTM-AE

### 결정 13 — LLM 보안등급 라우팅 (v2.9 원칙 확장)

| 데이터 보안등급 | 주력 LLM | 대체/백업 | 비고 |
|---|---|---|---|
| **PUBLIC** | Claude API Sonnet 4.6 | 로컬 Gemma 4 31B-MoE | 계획서·보고서 |
| **RESTRICTED** | Claude API Sonnet 4.6 | 로컬 Gemma 4 31B-MoE | 내부 공유 가능 |
| **CONFIDENTIAL** | **로컬 Gemma 4 31B-MoE + LoRA SFT** | 로컬 EXAONE 4.0 32B Dense | 자체 호스팅 필수 |
| **SECRET** | **로컬 Gemma 4 31B-MoE + LoRA SFT** | 로컬 EXAONE 4.0 32B Dense | 완전 오프라인 |
| **Parser (고빈도 저지연)** | 로컬 Gemma 4 4B + QLoRA | — | 일지 실시간 파싱 ≤ 1초 |

**선정 근거:**
- **CONFIDENTIAL↑ 기본 = Gemma 4 31B-MoE**: 장기 SaaS 로드맵·라이선스 자유도 + MoE 효율(활성 3.8B)
- **EXAONE 4.0 Baseline·백업**: 한국어 SOTA 기준점. LG 상용협약 성사 시 Primary 승격 옵션
- **PUBLIC·RESTRICTED = Claude API**: GPU 부담 최소화, 최신 성능 활용
- 월간 LLM 비용 $5,000 한도 내 운영 가능 (내부 50명 기준)

**v2.9 Section 19.2 supersede:** v2.9는 "Claude API / Exaone·LLaMA" 이원 체계였으나, 본 결정이 supersede.

### 결정 14 — Task-Specific 소형 모델 5종
| 모델 | 역할 | 연동 에이전트 |
|---|---|---|
| **ModernBERT-ko (400M + head)** | 프로젝트 WBS 유형 8 분류 | AG-INT |
| **Bi-encoder + BGE-Reranker** | 시장적합성 Scorer | AG-SENSE |
| **Temporal Fusion Transformer (TFT)** | 소요·일정 예측 | AG-SCHED |
| **Heterogeneous R-GCN (PyG)** | Task Graph GNN (임계경로 재계산) | AG-SCHED |
| **Isolation Forest + LSTM-AE** | 이상탐지 (이상·지연 감지) | AG-SENSE |

### 결정 15 — Valley of Death Detector
- 조건: **TRL-CRL Gap ≥ 3 AND CRL < 4**
- 경보 시: L2 Stage Gate Kill 검토 권고
- 적용 유형: A·B·C (G에서 전환 단계 해당 시)
- 구현: 규칙 기반 + ML Classifier 이중 확인

### 결정 16 — 수치·최적화 = OR-Tools CP-SAT + RL + Rule Engine 분리
- **자원배분**: Google OR-Tools CP-SAT (MILP) — AG-BUDGET 연동
- **스케줄링**: CPM + Critical Chain — AG-SCHED 연동
- **RL Agent (Year 2+)**: Stable-Baselines3 PPO
- **Rule Engine (특허 CP3)**: Python pure
  - EVM/SPI/DoD 판정 (LLM 배제)
  - L1 TRL Gate / L2 Must 기준 / L3 성과목표 달성도 / **L2-C Client Acceptance**
  - Valley of Death 규칙
  - 단일 엔트리 경로, LLM 유입 금지

### 결정 17 — RAG Stack
- **Embedding**: BGE-M3 + KURE (한국어 특화)
- **Vector DB**: Qdrant (온프레미스, v2.9 준용)
- **Graph DB**: Neo4j Enterprise (GATE_DECISION · TRL_SNAPSHOT 노드, Append-only)
- **RDB**: PostgreSQL 16 + pg_audit
- **Hybrid Search**: BM25 + Dense + BGE-Reranker
- **Sources**: NTIS · 규정 · 선행연구 · 내부 계획서·보고서 DB
- **Collections 분리**:
  - 기본 (`main_corpus`)
  - **`contract_research_corpus`** (학술연구용역 전용, 결정 22 참조)

### 결정 18 — 학습 데이터 전략

| 단계 | 소스 | 규모 | 기간 |
|---|---|---|---|
| 합성 | Claude Sonnet으로 한국 R&D 일지 시뮬레이션 | 500건 | M1~M3 |
| 내부·수요기업 | 실제 계획서·보고서·일지 수집 | 2,000+건 | M3~M9 |
| Auto-labeling + 검수 | Claude/GPT-4 1차 → 연구원 검수 | 2,000 검수 | M6~M11 |
| Gold Set | 홀드아웃 F1 평가용 | 300건 | M10~M12 |
| DPO 선호도 | 내부 사용자 A/B 선택 로그 | 2,000 페어 | Y2 전반 |

**WBS 유형별 할당 (2,000건 내부·수요기업 기준):**
| 유형 | 비율 | 최소 건수 |
|---|---|---|
| A 탐구형 | 15% | 300건 |
| B 개발형 | 20% | 400건 |
| C 사업화·실증형 | 15% | 300건 |
| D 조사·분석형 | 15% | 300건 |
| E 기획·전략형 | 10% | 200건 |
| F 컨설팅형 | 10% | 200건 |
| G 복합·전주기형 | 10% | 200건 |
| H 행사운영형 | 5% | 100건 |
| **합계** | 100% | 2,000건 |

**Cross-cutting 할당 (결정 22와 연동):**
- `contract_research` flagged ≥ 30% (600건) 의무 — TENOPA 주 수익원 품질 보장
- 유형 D·E·F × `contract_research` 조합 집중 수집

### 결정 19 — 파인튜닝 4-Phase 로드맵
```
Phase 0 (M1~M2)  베이스라인 벤치마크
  · Gemma 4 27B·31B-MoE + EXAONE 4.0 32B Zero-shot (한국 R&D 샘플 100건)
  · 메트릭: F1, 문체 품질(5-스케일), 지연시간, VRAM
Phase 1 (M3~M8)  SFT + LoRA
  · Research Manager LLM: 7,800 페어 SFT (LoRA r=32, α=64)
  · Parser LLM: 2,000 페어 QLoRA (4-bit, r=16)
  · Task-Specific 소형 모델 5종 학습
Phase 2 (M9~M12) 평가·보강
  · TTA/KAIC 성능 검증 프리테스트
  · 1차년도 F1 ≥ 0.80
Phase 3 (Year 2) DPO + RAG 프로덕션
  · 내부 50명 A/B 로그 → DPO 페어 2,000
  · RAG 파이프라인 프로덕션 통합
Phase 4 (Year 3) 실증·공개
  · 오픈웨이트 공개 (Gemma Terms 준수)
  · TTA/KAIC 최종 인증 (F1 ≥ 0.85 도전)
```

### 결정 20 — Hallucination-Zero 7계층 방어 + PROV-O Lineage
```
L1. Structured Output (JSON Schema 강제)
L2. Ontology 제약 (유형 분류 + Cross-cutting 속성)
L3. Confidence Threshold (< 0.7 → 사용자 재확인)
L4. Rule Engine 라우팅 (수치판정 LLM 배제, CP3)
L5. Citation 의무 (factual claim 모두 출처 링크)
L6. Retrieval Verification (답변 vs 문서 정합성 체크)
L7. PROV-O Lineage (모든 입출력·model_id 기록, CP5)
```

### 결정 21 — v2.9 인프라·거버넌스 보존
- **Outbox Pattern**: PostgreSQL → Neo4j/Redis 전파 (분산 트랜잭션)
- **ABAC**: subject · resource · environment · action 4속성
- **DLQ**: 에이전트 실패 격리
- **NFR-A01**: 99.9% 가용성 / RTO 4h / RPO 1h
- **13 일일보고 태그**: [DONE][ISSUE][TRL_UP][CRL_UP][TIME][COST][IP][ASSIGN][DELIVERABLE][EXPERIMENT][MGT][DO][REV]
- **KPI 3계층**: Output / Outcome / Value
- **Neo4j Append-only GATE_DECISION**: 불변 감사 로그

### 결정 22 ⭐ — 학술연구용역 전용 관리 모듈 (First-class)
**활성화 조건:** `contract_modality = contract_research`

**① WBS Addon Template (6-phase, 계약 체결부터 시작):**
```
Phase 1. 계약 체결·착수계 제출   ← 관리 시작점
Phase 2. 중간보고 (1회 또는 다회)
Phase 3. 최종보고서 제출
Phase 4. 검수·수정 반영
Phase 5. 납품·정산
Phase 6. 사후관리 (하자보수·재문의 대응)
```
> **RAPai 관리 경계 원칙**: 관리 시작점 = **계약 체결(`CONTRACT_SIGNED`)**. 영업·제안·RFP 단계는 범위 외.

**② L2-C Client Acceptance Gate:** 고객 서명 = 유일한 통과 조건. Rule Engine 전담(CP3).

**③ 전용 KPI 3계층:**
- Output: 납기 준수율, 중간보고 적시율, 문서 품질
- Outcome: 검수 1차 합격률, 수정요청 건수, CSAT
- Value: 재수주율, 고객 LTV, 매출 실현율, 원가율

**④ AG-xxx 가중치 자동 상향:** AG-STAKE · AG-QA · AG-SCOPE · AG-BUDGET · AG-REPORT · AG-COMMS → `high`

**⑤ 전용 대시보드:** 수익 Pipeline(5-stage) · 검수 임박 Alert(D-14/D-7/D-1) · 재수주 확률 Score · 포트폴리오 수익성 매트릭스

**⑥ 전용 RAG**: `contract_research_corpus` Qdrant collection (과거 계약서·보고서·검수확인서 전용)

**⑦ 학습 데이터 Cross-cutting 할당:** `contract_research` ≥ 30% (600건) 의무

**근거:** TENOPA 주 수익원으로서 PM 관리 깊이가 실매출 직결. 분류 visibility는 요구사항 아님(사용자 확정, 2026-04-18).

---

## 📋 운영 거버넌스

| 규칙 | 내용 |
|---|---|
| **G1. SemVer** | `MAJOR.MINOR.PATCH` — 본 ADR은 v1.0.0 |
| **G2. Append-Only** | 결정 번호는 재사용 금지. 폐기 시 Deprecated 마킹 |
| **G3. 전 LLM 시스템 프롬프트 바인딩** | 유형 + contract_modality + active gates 자동 주입 |
| **G4. Rule Engine 단일 경로 (CP3)** | 수치 판정 LLM 유입 절대 금지 — 코드 리뷰 체크리스트 |
| **G5. Model ID Lineage (CP5)** | 모든 LLM·ML 호출 시 model_id · version · prompt_hash 기록 |
| **G6. Confidence Threshold** | LLM 출력 confidence < 0.7 → AG-INT 재질문 |

---

## 🔗 영향받는 문서

### 본 ADR이 supersede 하는 부분
- `RAPai_통합설계명세서_v2.9.md` Section 18.1 (6유형 체계) → 결정 8 (WBS 8유형 + Cross-cutting)
- `RAPai_통합설계명세서_v2.9.md` Section 19.2 (Claude + Exaone/LLaMA 이원) → 결정 13 (보안등급 라우팅 + Gemma 4 Primary)

### 본 ADR이 **보완** 하는 부분 (v2.9가 미상세)
- ML/OR 특화 모델 5종 → 결정 14
- 파인튜닝 전략·데이터 할당 → 결정 18·19
- Hallucination-Zero 7계층 상세 → 결정 20
- 학술연구용역 전용 모듈 → 결정 22

### 본 ADR이 **보존** 하는 부분 (v2.9 그대로)
- 시스템 브랜드 RAPai (결정 7)
- 13 AG-xxx + LangGraph StateGraph (결정 10)
- Outbox / ABAC / DLQ / NFR-A01 (결정 21)
- PostgreSQL 16 + Qdrant + Neo4j Append-only (결정 17·21)
- 13 일일보고 태그 + KPI 3계층 (결정 21)
- 특허 5 Chokepoint (CP1~CP5) 전면 준수

### 본 ADR과 정합하는 참조 문서
- `mindvault/decisions/001-ontology-strategy.md` — ADR-001 (L2.5 + Palantir 철학 차용 + JSON Schema SSOT)
- `mindvault/ontology/10-project-type-classification-v2.md` — 유형 분류 v2.0 상세
- `mindvault/ontology/05-project-types-and-terms.md` — 라우팅 키 개념 (v1, 보존)
- `mindvault/ontology/07-operational-ontology-design.md` — Event-Driven Agentic OS
- `mindvault/ontology/09-work-activity-ontology.md` — NL-First Intent/Entity
- `특허관련 문서/RD_AI_에이전트_길목특허_명세서_v3.md` — 5 Chokepoint

---

## 🚦 후속 실행 항목

### 즉시 (본 세션 연속)
- [x] `mindvault/ontology/10-project-type-classification-v2.md` 작성
- [x] `mindvault/decisions/002-ai-model-architecture.md` 작성 (본 ADR)
- [ ] `mindvault/ontology/05-project-types-and-terms.md` v2 참조 헤더 추가
- [ ] `mindvault/INDEX.md` 신규 문서 링크 반영
- [ ] `C:\claude\plans\memoized-mapping-dongarra.md` Part 1.2 · 10 · 11 업데이트

### 1주일 내
- [ ] `mindvault/system/02-specialized-ai-model.md` 신규 작성 (특화 AI 모델 개념·방법·13 AG-xxx 매핑)
- [ ] `mindvault/llm/01-model-selection.md` — 보안등급 라우팅 + Gemma 4/EXAONE/Claude 선정 근거
- [ ] `mindvault/llm/02-finetuning-roadmap.md` — Phase 0~4 + WBS 8유형 할당 상세
- [ ] `mindvault/llm/03-evaluation-framework.md` — 평가 메트릭 + Gold Set 300건 설계
- [ ] `mindvault/llm/04-security-tier-routing.md` — 보안등급 LLM 라우팅 운영 가이드
- [ ] `mindvault/research/rfp-item6-compatibility-check.md` — RFP 정합성 체크리스트

### 중기 (1~3개월)
- [ ] `ontology/schemas/project.v2.json` JSON Schema 정본 파일 작성 (R3 준수)
- [ ] Phase 0 베이스라인 벤치마크 착수 (Gemma 4 vs EXAONE 4.0 vs Claude)
- [ ] `RAPai_통합설계명세서_v3.0.md` 차기 개정 — 본 ADR 결정 내재화
- [ ] AG-xxx 가중치 상향 규칙 코드 구현 (13 에이전트 base class)

---

## ♻️ 재검토 트리거 (Revisit When)

- Phase 0 벤치마크 결과가 Gemma 4 < EXAONE 4.0인 경우 → 결정 13 재검토
- 운영 6개월 시점 — WBS 유형 분류 정확도 90% 미달 시 결정 8·14 재검토
- LG 상용협약 성사 → 결정 13의 CONFIDENTIAL↑ Primary를 EXAONE 4.0으로 전환 검토
- 월간 LLM 비용 초과 → 결정 13의 PUBLIC·RESTRICTED를 로컬 Gemma 4로 전환 검토
- 특허 CP3 위반 의심 사례 발생 → 결정 16 Rule Engine 격리 재점검
- Hallucination 사고 발생 → 결정 20 7계층 방어 전 계층 재검증

---

**본 ADR의 한 줄 요약:**
"RAPai의 특화 AI 모델 아키텍처는 **5-Tier Hybrid(Claude API + Gemma 4 31B-MoE Primary + EXAONE 4.0 Baseline + Task-Specific 5종 ML/OR + Rule Engine CP3 + RAG)** 를 **보안등급 라우팅**으로 구동하고, **WBS 8유형 + Cross-cutting 속성**을 라우팅 키로 하며, **학술연구용역 전용 First-class 관리 모듈(L2-C Gate + 6-phase WBS + 전용 KPI·AG 가중치·대시보드·RAG·학습데이터 30%)**을 overlay한다. v2.9 근간(13 AG-xxx, LangGraph, 특허 CP1-CP5, Outbox, ABAC, NFR-A01) 보존, 3건 supersede + 4건 보완."
