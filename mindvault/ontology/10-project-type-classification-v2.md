# 프로젝트 유형 분류 체계 v2.0 — WBS 성격 기반 + Cross-cutting 속성

**작성일:** 2026-04-18
**버전:** v2.0.0 (SemVer MAJOR bump — v2.9의 6유형 체계 supersede)
**상태:** ✅ Accepted (사용자 확정: 2026-04-18)
**선행 ADR:** ADR-001 (Ontology Strategy), ADR-002 (AI Model Architecture, 결정 8 + 결정 22)
**supersedes:** `RAPai_통합설계명세서_v2.9.md` Section 18.1 (6유형 체계)
**계승:** `mindvault/ontology/05-project-types-and-terms.md` (v1 — 라우팅 키 개념 보존)

---

## 🎯 핵심 원칙

> **"WBS 구조가 동일하면 같은 유형이다"** — 프로젝트 유형 분류는 관리 규칙·Gate·KPI의 라우팅 키이며, 그 본질은 **작업분해구조(WBS) 패턴**이다.

이 원칙이 v2.9의 6유형 체계(basic_research / tech_rd / policy_research / roadmap_isp / management_consulting / hybrid)와 다른 점:
- v2.9는 **산업·정책 관점의 분류**였고, 실무 WBS와 1:1 대응이 불완전했음
- v2.0는 **WBS 성격(work-breakdown nature)**을 1차 축으로, **계약·보안 모달리티**를 2차 축(cross-cutting)으로 분리

---

## 📐 분류 체계 구조 (Two-Axis)

### Axis 1 — WBS 성격 유형 (Primary, 8 types)

```
A. 탐구형          (Exploratory)          — 가설·실험 중심, TRL 낮음
B. 개발형          (Developmental)        — 요구·설계·개발·검증 중심, TRL 중심
C. 사업화·실증형   (Commercialization)    — MVP·파일럿·실증·상용화, CRL 중심
D. 조사·분석형     (Investigative)        — 자료수집·분석·해석
E. 기획·전략형     (Strategic Planning)   — 환경분석·로드맵·이행계획
F. 컨설팅형        (Advisory)             — 진단·권고·이행지원
G. 복합·전주기형   (Full-Lifecycle Hybrid) — A→B→C / E→B→C 등 단계 전환
H. 행사운영형      (Event Operations)     — D-Day 백워드, Gate 비적용
```

### Axis 2 — Cross-cutting 속성 (Orthogonal to WBS)

```yaml
contract_modality:
  - internal_rd        # 자체 R&D 투자
  - public_grant       # 정부 국책 과제 (협약 체결)
  - contract_research  # 학술연구용역 (고객 발주, 커스텀 WBS)
  # ⭐ contract_research 부착 시 "학술연구용역 전용 관리 모듈" 자동 활성화

funding_source:
  - 정부국책
  - 민간수탁
  - 자체투자
  - 혼합

security_tier:
  - PUBLIC
  - RESTRICTED
  - CONFIDENTIAL
  - SECRET

scale_tier:
  - small   # ≤ 3억
  - medium  # 3~30억
  - large   # > 30억 (사업단급)
```

---

## 🗂️ WBS 유형별 상세 정의

### A. 탐구형 (Exploratory)
| 항목 | 값 |
|---|---|
| **project_type** | `exploratory` |
| **WBS 대표 단계** | 문헌조사 → 가설 수립 → 실험 설계 → 실험·측정 → 데이터 검증 → 논문·보고 |
| **Gate 계층** | L1 TRL (1~3) · L2 Stage(기술) · L3 Annual · L4 Moving Target |
| **TRL 범위** | 1~3 |
| **주 KPI (Output)** | 논문 편수, 발표, 데이터셋 공개 |
| **주 KPI (Outcome)** | 인용수, H-index, 후속 연구 유발 |
| **주 KPI (Value)** | 학계 영향, 원천기술 자산화 |
| **v2.9 매핑** | `basic_research` |
| **대표 사례** | 정부 기초연구 사업, 학술연구 프로젝트 |

### B. 개발형 (Developmental)
| 항목 | 값 |
|---|---|
| **project_type** | `developmental` |
| **WBS 대표 단계** | 요구 정의 → 아키텍처·설계 → 구현·개발 → 시험·검증 → 기술 이전·보고 |
| **Gate 계층** | L1 TRL (3~7) · L2 Stage(기술) · L3 Annual · L4 Moving Target |
| **TRL 범위** | 3~7 |
| **주 KPI (Output)** | 특허, 프로토타입, 시험성적서 |
| **주 KPI (Outcome)** | TRL 상승, 기술 이전 건수 |
| **주 KPI (Value)** | 기술료, 상용화 연계 |
| **v2.9 매핑** | `tech_rd` (R&D 개발 부분) |
| **대표 사례** | 중기부 기술개발사업, 산자부 산업기술혁신 |

### C. 사업화·실증형 (Commercialization)
| 항목 | 값 |
|---|---|
| **project_type** | `commercialization` |
| **WBS 대표 단계** | 시장 검증 → BM 설계 → MVP 개발 → 파일럿 → 실증 → 상용화·확산 |
| **Gate 계층** | L1 CRL (4~9) · L2 Stage(사업성) · L3 Annual · L4 Moving Target |
| **TRL/CRL 범위** | TRL 7~9, CRL 4~9 |
| **주 KPI (Output)** | 제품·서비스 출시, 파일럿 계약, 인증 획득 |
| **주 KPI (Outcome)** | 고객 수, 매출 성장, 시장 점유율 |
| **주 KPI (Value)** | EBITDA, 투자 유치, 해외 진출 |
| **v2.9 매핑** | `tech_rd` (사업화 부분, B와 분리) |
| **대표 사례** | 중기부 사업화 지원, 실증 R&D, Scale-up 과제 |

> **B/C 분리 근거 (사용자 확정):** WBS가 명확히 다름. B는 기술적 완결성 중심(TRL gate), C는 시장 적합성 중심(CRL gate). 자원·위험·의사결정 기준 모두 상이.

### D. 조사·분석형 (Investigative)
| 항목 | 값 |
|---|---|
| **project_type** | `investigative` |
| **WBS 대표 단계** | 조사 설계 → 자료 수집(문헌·통계·인터뷰·설문) → 분석 → 해석 → 보고서 |
| **Gate 계층** | L2 Stage(품질) · L3 Annual · (△) L4 선택 |
| **TRL 범위** | N/A |
| **주 KPI (Output)** | 보고서, 데이터셋, 시각화 |
| **주 KPI (Outcome)** | 이해관계자 활용, 후속 정책 연계 |
| **주 KPI (Value)** | 의사결정 영향력, 재수주 |
| **v2.9 매핑** | `policy_research` (조사·분석 부분) |
| **대표 사례** | 성과조사·분석, 통계 조사, 실태조사 |

### E. 기획·전략형 (Strategic Planning)
| 항목 | 값 |
|---|---|
| **project_type** | `strategic_planning` |
| **WBS 대표 단계** | 환경 분석 → 이슈 도출 → 대안 설계 → 로드맵 → 이행 계획·거버넌스 |
| **Gate 계층** | L2 Stage(품질) · L3 Annual · (△) L4 정책변동 |
| **TRL 범위** | N/A |
| **주 KPI (Output)** | 로드맵 문서, ISP 산출물, 실행계획서 |
| **주 KPI (Outcome)** | 로드맵 공식 채택, 예산 반영 |
| **주 KPI (Value)** | 정책·전략 실현, 기관 영향력 |
| **v2.9 매핑** | `roadmap_isp` |
| **대표 사례** | 기술로드맵 수립, ISP, 과기정통부 전략 기획 |

### F. 컨설팅형 (Advisory)
| 항목 | 값 |
|---|---|
| **project_type** | `advisory` |
| **WBS 대표 단계** | 진단 → 원인 분석 → Best Practice → 권고안 → 이행 지원 |
| **Gate 계층** | L2 Stage(마일스톤) · L3 Annual |
| **TRL 범위** | N/A |
| **주 KPI (Output)** | 진단 보고서, 권고안, 실행 가이드 |
| **주 KPI (Outcome)** | 권고안 채택률, 이행 진척도 |
| **주 KPI (Value)** | 고객 조직 성과 개선, 재계약 |
| **v2.9 매핑** | `management_consulting` |
| **대표 사례** | 경영 컨설팅, AX 전략 컨설팅, DX 컨설팅 |

### G. 복합·전주기형 (Full-Lifecycle Hybrid)
| 항목 | 값 |
|---|---|
| **project_type** | `hybrid` |
| **WBS 대표 단계** | (단계별 전환) A→B→C / E→B→C / D→E→F 등 |
| **Gate 계층** | 단계별 Gate 활성화 (전환 시 Gate Transition Event 발생) |
| **TRL/CRL 범위** | 단계별 |
| **주 KPI** | 각 단계 KPI를 단계별로 전환·집계 |
| **v2.9 매핑** | `hybrid` |
| **대표 사례** | 원천기술 → 기술사업화 전환, 기획 → 개발 → 상용화 전주기 |

### H. 행사운영형 (Event Operations)
| 항목 | 값 |
|---|---|
| **project_type** | `event_operations` |
| **WBS 대표 단계** | 기획 → 섭외·계약 → 홍보·마케팅 → 등록·접수 → D-Day 운영 → 결산 |
| **Gate 계층** | **Gate 비적용** (TRL/CRL 무관) — D-Day 백워드 스케줄링 |
| **TRL 범위** | N/A |
| **주 KPI (Output)** | 참가자 수, 만족도, 홍보 노출 |
| **주 KPI (Outcome)** | 네트워킹 성과, 후속 연계 |
| **주 KPI (Value)** | 주최사 브랜드, 재의뢰 |
| **v2.9 매핑** | (신규) |
| **대표 사례** | 홍보마케팅 지원, 투자유치 행사, 학술대회·컨퍼런스 운영 |

> **H 유형 특수성:** 전체 계획이 D-Day로부터 역산(backward scheduling). TRL/CRL 무관. 시간 지연 = 치명적 실패.

---

## ⭐ Cross-cutting: 학술연구용역 전용 관리 모듈 (contract_research)

### 활성화 조건
`contract_modality = contract_research` → 아래 모듈이 **WBS 유형(A~F)과 직교**하여 자동 overlay.

### ① WBS Addon Template (6-phase, 계약 체결부터 시작)

```
[기본 WBS (A~F 중 하나)]
      ↓ (overlay on contract_research)
┌─────────────────────────────────────────────┐
│ Phase 1. 계약 체결·착수계 제출      ← 관리 시작점 │
│ Phase 2. 중간보고 (1회 또는 다회)                │
│ Phase 3. 최종보고서 제출                        │
│ Phase 4. 검수·수정 반영                         │
│ Phase 5. 납품·정산                             │
│ Phase 6. 사후관리 (하자보수·재문의 대응)         │
└─────────────────────────────────────────────┘
```

> **RAPai 관리 경계 원칙**: 관리 시작점 = **계약 체결(또는 선정 확정, `CONTRACT_SIGNED` 이벤트)**. 영업·제안·RFP 단계는 범위 외 (별도 CRM/영업 시스템 영역).
> 이 원칙은 `contract_research`뿐 아니라 `public_grant`(협약 체결 이후) · `internal_rd`(착수 승인 이후) 모든 모달리티에 공통 적용.

### ② 전용 Gate — L2-C (Client Acceptance Gate)

- **기존 L1-L4와 병렬 작동** — `contract_research`에만 추가 활성화
- **판정 기준:** 고객 서명(검수확인서) = **유일한 통과 조건**
- **LLM 배제:** Rule Engine 전담 (특허 CP3 준수 — 수치·법적 판정은 LLM 배제)
- **실패 시 흐름:**
  ```
  검수 Reject → 수정요청 카운트 +1
    → 임계치(기본 3회) 초과 → AG-RISK 경보 발생
    → AG-SCOPE 재협상 트리거 (범위 축소 / 납기 연장 / 금액 조정 검토)
  ```

### ③ 전용 KPI (3계층 + 계약 KPI 전용 패널)

| 계층 | 메트릭 |
|---|---|
| **Output** | 납기 준수율, 중간보고 적시 제출률, 문서 품질 점수 |
| **Outcome** | 검수 1차 합격률, 수정요청 건수(평균), 최종 만족도(CSAT) |
| **Value** | 재수주율, 고객 LTV, 매출 실현율, 원가율·수익성 |

### ④ AG-xxx 가중치 상향 규칙

`contract_modality = contract_research`일 때 아래 에이전트의 실행 우선순위·리소스 할당 자동 상향:

| 에이전트 | 기본 | contract_research 시 | 변경 사유 |
|---|---|---|---|
| AG-STAKE (이해관계자) | normal | **high** | 발주처 = primary stakeholder |
| AG-QA (품질) | normal | **high** | 검수 대비 품질 게이트 강화 |
| AG-SCOPE (범위) | normal | **high** | 요구 변경·추가 발주 빈번 |
| AG-BUDGET (예산) | normal | **high** | 계약금 Tranche(착수금·중간금·잔금) 관리 |
| AG-REPORT (보고) | normal | **high** | 발주처 포맷·용어 준수 필수 |
| AG-COMMS (커뮤니케이션) | normal | **high** | 공식 문서·서신 중심 소통 |

### ⑤ 전용 대시보드 섹션

| 뷰 | 내용 |
|---|---|
| **수익 Pipeline** | `[계약체결] → [진행중] → [검수대기] → [납품완료] → [정산대기]` 5-stage funnel |
| **검수 임박 Alert** | D-14 / D-7 / D-1 자동 경보 (AG-SENSE 특화 규칙) |
| **재수주 확률 Score** | 과거 검수 성과 × 고객사 이력 × CSAT → ML Tier 3 예측 |
| **포트폴리오 수익성** | WBS 유형(A-H) × `contract_research` 매트릭스, 유형별 원가율 비교 |

### ⑥ 전용 RAG 컬렉션

- Qdrant 별도 collection (`contract_research_corpus`)
  - 과거 학술연구용역 계약서, 제안서, 중간·최종 보고서, 검수확인서
  - 고객사별 선호 포맷·톤·용어 학습 데이터
- 착수계·중간보고·최종보고 템플릿 자동 retrieval
- DPO 타겟: 고객사별 문체·구조 선호도 페어

### ⑦ 학습 데이터 할당 반영

기존 유형별(A~H) 할당과 별개로 **Cross-cutting 차원** 추가:

```
총 2,000건 (내부·수요기업) 중:
  · contract_research flagged ≥ 30% (600건 의무)
  · 유형 D·E·F × contract_research 조합에 집중 수집
  · 이유: TENOPA 주 수익원 → 도메인 LLM 품질이 실매출 직결
```

---

## 🔗 v2.9 원문과의 매핑 (Migration Table)

| v2.9 6유형 | v2.0 WBS 유형 | 비고 |
|---|---|---|
| basic_research | **A 탐구형** | 1:1 대응 |
| tech_rd (R&D 개발) | **B 개발형** | tech_rd를 B와 C로 분리 |
| tech_rd (사업화) | **C 사업화·실증형** | WBS 상이 → 분리 확정 |
| policy_research | **D 조사·분석형** | 명확한 1:1 |
| roadmap_isp | **E 기획·전략형** | 명확한 1:1 |
| management_consulting | **F 컨설팅형** | 명확한 1:1 |
| hybrid | **G 복합·전주기형** | 명확한 1:1 |
| (해당 없음, 신설) | **H 행사운영형** | v2.9 미존재, 실무 수요로 신설 |
| (해당 없음, 속성화) | Cross-cutting `contract_research` | 학술연구용역을 속성으로 flatten |

### v2.9 Section 18.1 Gate 활성화 매트릭스 확장

| 유형 | L1 TRL | L1 CRL | L2 Stage | L3 Annual | L4 Moving Target | L2-C Client Accept |
|---|---|---|---|---|---|---|
| A | ✅ | ✗ | ✅ 기술 | ✅ | ✅ | (해당 시) |
| B | ✅ | ✗ | ✅ 기술 | ✅ | ✅ | (해당 시) |
| C | ✗ | ✅ | ✅ 사업성 | ✅ | ✅ | (해당 시) |
| D | ✗ | ✗ | ✅ 품질 | ✅ | △ | (해당 시) |
| E | ✗ | ✗ | ✅ 품질 | ✅ | △ | (해당 시) |
| F | ✗ | ✗ | ✅ 마일스톤 | ✅ | ✗ | (해당 시) |
| G | 단계별 | 단계별 | 단계별 | ✅ | 단계별 | (해당 시) |
| H | ✗ | ✗ | D-Day | ✗ | ✗ | (해당 시) |

> `L2-C` 열: `contract_modality = contract_research` 부착 시 모든 유형에 활성화되는 cross-cutting Gate.

---

## 🧬 온톨로지 구현 스펙 (JSON Schema SSOT 준수)

```yaml
# ontology/schemas/project.v2.json (SSOT)
$schema: https://json-schema.org/draft/2020-12/schema
$id: rapai://ontology/project/v2.0.0
title: Project
type: object
required: [id, name, wbs_type, contract_modality, created_at]
properties:
  id: {type: string, format: uuid}
  name: {type: string}
  wbs_type:
    type: string
    enum: [exploratory, developmental, commercialization, investigative,
           strategic_planning, advisory, hybrid, event_operations]
  contract_modality:
    type: string
    enum: [internal_rd, public_grant, contract_research]
  funding_source:
    type: string
    enum: [gov_grant, private_contract, self_invest, mixed]
  security_tier:
    type: string
    enum: [PUBLIC, RESTRICTED, CONFIDENTIAL, SECRET]
  scale_tier:
    type: string
    enum: [small, medium, large]
  trl_current: {type: integer, minimum: 1, maximum: 9}
  crl_current: {type: integer, minimum: 1, maximum: 9}
  gates_active:
    type: array
    items:
      type: string
      enum: [L1_TRL, L1_CRL, L2_STAGE, L2_C_ACCEPT, L3_ANNUAL, L4_MOVING]
  contract_phase:
    # contract_modality == contract_research일 때만 사용
    type: string
    enum: [signed, in_progress, interim_report, final_report,
           under_review, delivered, post_mgmt_active, closed]
  created_at: {type: string, format: date-time}
```

### LLM 시스템 프롬프트 자동 주입 (R4 규칙 준수)

```
[CONTEXT]
Project WBS Type: {wbs_type}
Contract Modality: {contract_modality}
Active Gates: {gates_active}
{if contract_modality == contract_research}:
  Contract Phase: {contract_phase}
  ⚠️ Acceptance Gate (L2-C) is ACTIVE. Rule Engine handles acceptance decision.
  ⚠️ Agent weights elevated: AG-STAKE/QA/SCOPE/BUDGET/REPORT/COMMS = high.
```

---

## 📋 운영 규칙 (Governance)

| 규칙 | 내용 |
|---|---|
| **R1. SemVer** | v2.0.0 (MAJOR bump from v2.9의 6유형). 향후 WBS 유형 추가는 MINOR, 속성 값 추가는 PATCH. |
| **R2. Append-Only** | 유형 A~H는 삭제 금지. 폐기 필요 시 Deprecated 마킹만. |
| **R3. JSON Schema SSOT** | `ontology/schemas/project.v2.json`이 유일한 진실의 원천. 본 Markdown은 derived. |
| **R4. LLM Prompt Binding** | 유형·모달리티 정보는 모든 LLM 호출 시 시스템 프롬프트에 자동 주입. |
| **R5. Classification Uncertainty** | 유형 분류 Classifier confidence < 0.7 → AG-INT가 사용자에게 확인 요청 (hallucination 방지). |
| **R6. Contract Phase Append-Only** | `contract_phase` 전이는 역행 불가 (signed → in_progress → ... → closed). 재개 시 새 프로젝트 생성. |

---

## ♻️ 재검토 트리거 (Revisit When)

- 실제 운영 6개월 시점 — 유형 분류 정확도 90% 미달 시 재설계
- 신규 WBS 패턴 발견 시 — 월 1회 확장 회의에서 승격 판단
- v2.9 → v3.0 통합설계명세서 개정 시 — 본 v2.0이 내재화되는 형태로 재정합
- 고객 요구 WBS 패턴이 H(기타)로 분류되는 빈도 증가 시 — 신규 유형 분할 검토

---

## 🚦 후속 실행 항목

- [ ] `ontology/schemas/project.v2.json` JSON Schema 파일 작성 (SSOT 정본)
- [ ] 유형 6 → 유형 8 Classifier 재학습 (ModernBERT-ko, Gold Set 300건 재라벨링)
- [ ] AG-xxx 가중치 상향 규칙 코드 구현 (13 에이전트 base class 수정)
- [ ] Qdrant `contract_research_corpus` collection 분리 생성
- [ ] 대시보드 `수익 Pipeline`·`검수 임박 Alert`·`재수주 확률` 섹션 설계 (AG-REPORT 연동)
- [ ] v2.9 원문 Section 18.1 → 본 v2.0 참조로 supersede 주석 추가
- [ ] `RAPai_통합설계명세서_v3.0` 차기 개정 시 본 v2.0을 원문에 내재화

---

**본 문서의 한 줄 요약:**
"프로젝트 유형은 **WBS 성격 8유형(A~H) × Cross-cutting 속성(contract_modality·funding_source·security_tier·scale_tier)**의 2축 분류. 학술연구용역(contract_research)은 분류상 속성으로 두되, **관리 레이어에서는 first-class 모듈**로 robust하게 overlay — 계약 체결부터 시작하는 6-phase WBS Addon + L2-C Gate + KPI + AG 가중치 + 전용 대시보드·RAG·학습데이터."
