# 03. Evaluation Framework — 평가 메트릭 + Gold Set 300건 설계

**작성일:** 2026-04-18
**상태:** ✅ Active (ADR-002 결정 20 + Phase 1~4 수락 기준 기반)
**근거:** `decisions/002-ai-model-architecture.md`
**관련:** `llm/02-finetuning-roadmap.md`

> **이 문서의 역할**
> "무엇을·어떻게·얼마나 평가할 것인가"를 RAPai의 모든 AI 컴포넌트에 대해 단일 SSOT로 정의한다.
> Phase 게이트·Canary 판단·TTA 인증의 **공식 기준**.

---

## 1. 평가 체계 전체 개요

```
                ┌─────────────────────────────────┐
                │ 평가 입력 (Gold Set 300 + 로그)  │
                └─────────────┬───────────────────┘
                              ↓
       ┌──────────────────────┼──────────────────────┐
       ↓                      ↓                      ↓
┌─────────────┐      ┌───────────────┐      ┌────────────────┐
│ 태스크 메트릭│      │ Hallucination │      │ 사용자 만족도  │
│ (F1, MAPE 등)│      │ 방어 메트릭   │      │ (NPS, A/B)     │
└──────┬──────┘      └───────┬───────┘      └────────┬───────┘
       └──────────────────────┼──────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │ Phase Gate 판정 │
                    │ (진입/롤백/보강)│
                    └─────────────────┘
```

---

## 2. 태스크별 평가 메트릭

### 2.1 Research Manager LLM (Tier 2 Specialist)

| 태스크 | 메트릭 | Phase 1 목표 | Phase 2 목표 | Phase 4 목표 |
|---|---|---|---|---|
| 일지 → 온톨로지 객체화 | F1 (exact + partial) | 0.75 | 0.80 | **0.85** |
| 보고서 생성 품질 | 사람 5-스케일 | 3.5 | 4.0 | 4.3 |
| 보고서 BERTScore (참조 대비) | BERTScore F1 | 0.80 | 0.85 | 0.88 |
| 원인 분석·개입 제안 품질 | 사람 5-스케일 | 3.3 | 3.8 | 4.2 |
| Gate 패키지 조립 완결성 | 필수항목 Coverage | 0.90 | 0.95 | 0.98 |

### 2.2 Parser LLM (고빈도 저지연)

| 태스크 | 메트릭 | Phase 1 | Phase 2 | Phase 4 |
|---|---|---|---|---|
| 일지 NER (엔티티 추출) | F1 | 0.80 | 0.85 | **0.90** |
| 13 일일보고 태그 분류 | Macro F1 | 0.82 | 0.87 | 0.90 |
| 구조화 JSON 스키마 준수 | Schema Valid % | 0.95 | 0.98 | 0.99 |
| 지연 (p95) | seconds | <1.0 | <0.8 | <0.6 |

### 2.3 Task-Specific 5종

| 모델 | 메트릭 | Phase 1 | Phase 2 | Phase 4 |
|---|---|---|---|---|
| WBS 8유형 Classifier | Macro F1 (8-class) | 0.85 | 0.88 | **0.92** |
| 시장적합성 Scorer | NDCG@5 | 0.70 | 0.75 | 0.80 |
| 소요예측 TFT | MAPE | ≤ 20% | ≤ 15% | ≤ 12% |
| Task Graph GNN | 임계경로 정확도 (vs 전문가) | 0.85 | 0.90 | 0.93 |
| 이상탐지 | F1 (이상/정상 binary) | 0.75 | 0.80 | 0.85 |

### 2.4 OR·Rule Engine

| 컴포넌트 | 메트릭 | 목표 |
|---|---|---|
| OR-Tools CP-SAT | Feasibility 100% + Gap-to-Optimal | < 5% |
| Rule Engine (EVM/SPI) | 규정 산식 일치율 | **100%** (불일치 = Critical Bug) |
| L1 TRL/CRL Gate | 전문가 합의도 | ≥ 0.95 |
| L2-C Client Acceptance | 고객 서명 매칭율 | **100%** |

### 2.5 RAG Stack

| 컴포넌트 | 메트릭 | Phase 1 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| Hybrid Search Recall@10 | Recall@10 | 0.80 | 0.88 | 0.92 |
| BGE-Reranker NDCG@5 | NDCG@5 | 0.75 | 0.82 | 0.87 |
| Citation 정확도 | 인용 ID 정확 매칭 | 0.90 | 0.95 | 0.98 |

---

## 3. Hallucination-Zero 방어 메트릭

Hallucination 7계층 방어가 실제로 작동하는지 정량 측정.

### 3.1 핵심 메트릭 정의

| 메트릭 | 정의 | 계산 방법 |
|---|---|---|
| **Citation Coverage** | factual claim 중 출처 포함 비율 | `cited_claims / total_claims` |
| **Citation Accuracy** | 인용된 출처가 실제 근거인 비율 | `correct_citations / cited_claims` |
| **Fact-Check Pass Rate** | RAG 재조회 검증 통과율 | `passed / total_outputs` |
| **Schema Valid Rate** | JSON Schema 준수 비율 | `valid_json / total_outputs` |
| **Ontology Compliance** | 온톨로지 외 개체 생성 차단율 | `1 - out_of_ontology_rate` |
| **Confidence Threshold 통과율** | ≥ 0.7 confidence 비율 | `high_conf / total_outputs` |

### 3.2 Phase별 목표

| 메트릭 | Phase 1 | Phase 2 | Phase 4 |
|---|---|---|---|
| Citation Coverage | 0.90 | 0.95 | **0.98** |
| Citation Accuracy | 0.85 | 0.90 | 0.95 |
| Fact-Check Pass Rate | 0.85 | 0.90 | 0.95 |
| Schema Valid Rate | 0.95 | 0.98 | 0.99 |
| Ontology Compliance | 0.98 | 0.99 | 0.995 |

### 3.3 위반 분류 (Error Taxonomy)

| 유형 | 예시 | 심각도 |
|---|---|---|
| **T1. 출처 없는 주장** | "TRL 6에 도달했다" (근거 문서 ID 없음) | Critical |
| **T2. 존재하지 않는 출처 인용** | 문서 ID 999를 인용, 실제 DB 없음 | Critical |
| **T3. 출처와 다른 내용** | 문서에 "TRL 4"라고 적힌 것을 "TRL 6"으로 요약 | High |
| **T4. 온톨로지 외 개체** | `ActivityType="스파이더"` 생성 | Medium |
| **T5. Confidence 임계 미달 통과** | < 0.7인데 사용자에게 직접 답변 | Medium |
| **T6. Rule Engine 우회** | EVM 계산을 LLM이 수행 (CP3 위반) | **Critical** |
| **T7. PROV-O 미기록** | 모델 호출 로그 누락 | High |

T1·T2·T6 발생 시 **즉시 롤백** + 근본 원인 분석.

---

## 4. Gold Set 300건 설계

### 4.1 구성 원칙

1. **WBS 8유형 균형:** 각 유형 최소 30건 (부족 유형은 40건까지)
2. **Cross-cutting 속성 커버:** contract_research ≥ 30%, 각 security_tier ≥ 20%
3. **난이도 분포:** Easy 40% / Medium 40% / Hard 20%
4. **시간 분산:** 2024~2026 최근 3년 비율적 분포

### 4.2 유형별 할당 (300건)

| 유형 | 건수 | 난이도 E/M/H | 핵심 평가 초점 |
|---|---|---|---|
| A 탐구형 | 40 | 16/16/8 | TRL 산정 정확도, 기초연구 용어 |
| B 개발형 | 50 | 20/20/10 | 기술개발 WBS, 프로토타입 단계 |
| C 사업화·실증형 | 40 | 16/16/8 | CRL 산정, Valley of Death 탐지 |
| D 조사·분석형 | 40 | 16/16/8 | 설문·통계 태스크 구조화 |
| E 기획·전략형 | 30 | 12/12/6 | 로드맵·ISP 마일스톤 |
| F 컨설팅형 | 30 | 12/12/6 | 컨설팅 마일스톤·계약금 Tranche |
| G 복합·전주기형 | 30 | 12/12/6 | 단계 전환 판정 (원천→사업화) |
| H 행사운영형 | 20 | 8/8/4 | D-Day 백워드 스케줄링 |
| Cross-cutting 특화 | 20 | 0/10/10 | contract_research L2-C 중심 |
| **합계** | **300** | **112/112/66** | |

### 4.3 각 건당 포함 정보

```jsonl
{
  "id": "gold-001",
  "wbs_type": "C",  // commercialization
  "cross_cutting": {
    "contract_modality": "contract_research",
    "funding_source": "민간수탁",
    "security_tier": "RESTRICTED",
    "scale_tier": "medium"
  },
  "difficulty": "medium",
  "input": {
    "plan_text": "...",
    "journal_text": "...",
    "prev_gate_decisions": [...]
  },
  "expected": {
    "wbs_classification": "C",
    "wbs_confidence": 0.85,
    "entities": [...],
    "evm_values": {"CV": -120000, "SPI": 0.92},
    "gate_decision": "proceed_with_conditions",
    "report_key_points": ["..."],
    "citations_required": ["doc_id_123", "doc_id_456"]
  },
  "evaluator_notes": "Valley of Death 탐지 케이스 (TRL 5, CRL 2)"
}
```

### 4.4 Gold Set 제작 프로세스

1. **소스 선정 (M10):** 내부 DB에서 대표 600건 1차 후보 추출
2. **샘플링 (M10):** WBS 유형별 층화 샘플 → 400건
3. **사람 라벨링 (M10~M11):** 연구원 3명 × 다중 라벨 → IAA ≥ 0.85 확인
4. **조정 회의 (M11):** 불일치 건 합의 → 최종 300건
5. **Freeze (M12):** Append-only 보관, 수정 금지 (버전 관리: `gold_v1.0`)

---

## 5. 평가 파이프라인 자동화

### 5.1 CI 통합

```
[Adapter 새 버전 푸시]
  ↓
[자동 평가 실행]
  ├─ Gold Set 300 전체
  ├─ Hallucination 메트릭 계산
  ├─ 지연·처리량 측정
  └─ PROV-O 샘플 체크
  ↓
[Phase Gate 판정]
  ├─ 수락 기준 통과 → Canary 10% 배포 승인
  └─ 미달 → 배포 차단 + 리포트 자동 생성
  ↓
[Canary 관찰 (4주)]
  ├─ 실시간 KPI 비교
  └─ 회귀 감지 시 롤백
  ↓
[100% 배포]
```

### 5.2 평가 스크립트 위치

| 스크립트 | 대상 |
|---|---|
| `evals/run_gold_set.py` | Research Manager LLM, Parser LLM |
| `evals/hallucination_check.py` | 7계층 방어 측정 |
| `evals/classifier_eval.py` | WBS 8유형 Classifier |
| `evals/forecaster_eval.py` | TFT MAPE |
| `evals/gnn_eval.py` | R-GCN 임계경로 |
| `evals/rule_engine_eval.py` | EVM/TRL/CRL/L2-C 산식 100% |

---

## 6. A/B 테스트 설계

### 6.1 Canary 배포 원칙

- 신 버전 10% 트래픽 → 4주 관찰 → 100% 전환
- 트래픽 분기 키: `user_id hash` (동일 사용자는 고정 버전)
- 관찰 메트릭: Gold Set F1 ± 3pp 이내 유지, Hallucination ≤ 1% 신규 발생

### 6.2 Preference Pair 수집 (Phase 3 DPO용)

- 동일 프롬프트에 두 모델 출력 제시
- 사용자 선호 선택 → `dpo_pairs.jsonl` 누적
- 주 100 페어 × 20주 = 2,000 페어 목표

### 6.3 관찰 기간 중 롤백 트리거

| 지표 | 임계 | 동작 |
|---|---|---|
| Gold Set F1 회귀 | ≥ 3pp 하락 | **즉시 롤백** |
| Hallucination T1·T2·T6 발생 | ≥ 1건 | **즉시 롤백** |
| p95 지연 증가 | ≥ 50% | Warn → 조사 |
| Citation Coverage 하락 | ≥ 5pp | Warn → 조사 |
| NPS 급락 | ≥ -10pt | 1주 추가 관찰 후 결정 |

---

## 7. 사용자 만족도 평가

### 7.1 NPS 측정

- **대상:** 내부 50명
- **빈도:** 월 1회 익명 설문
- **질문:** "RAPai를 동료에게 추천할 가능성 0~10?"
- **계산:** NPS = %Promoters (9~10) - %Detractors (0~6)

**목표:**
- Phase 1 말: NPS ≥ 0
- Phase 2 말: NPS ≥ +20
- Phase 3 말: NPS ≥ +40
- Phase 4 말: NPS ≥ +50

### 7.2 업무 효율 측정 (RFP 정합)

- **대상:** 내부 50명
- **지표:** 일일 행정·관리 업무 소요 시간
- **방법:** 전·후 6주 A/B (Time-tracking 툴)
- **목표:** 일일 2시간 단축 (RFP 요구 정합)

### 7.3 CSAT (학술연구용역 특화)

- **대상:** 외부 고객 (contract_research 검수 후)
- **빈도:** 프로젝트 종료 시
- **지표:** CSAT 5점 척도
- **목표:** 평균 ≥ 4.2 (Phase 3 이후)

---

## 8. TTA/KAIC 외부 인증 (Phase 4)

### 8.1 인증 범위

- Research Manager LLM v3.0 (일지 파싱 F1)
- Parser LLM v3.0 (구조화 정확도)
- WBS 8유형 Classifier v3.0 (Macro F1)

### 8.2 인증 프로세스

1. **사전 문의 (M31):** TTA 또는 KAIC 담당자 접촉
2. **평가셋 준비 (M32):** Gold Set 300 + 외부 독립 셋 200
3. **시험 실시 (M32~M33):** TTA/KAIC 테스트베드에서 실행
4. **리포트 수령 (M33):** 공식 성적서 발급
5. **공개 (M34):** 모델 카드·웹사이트 게시

### 8.3 목표 (M36 기준)

- Research Manager LLM F1 ≥ **0.85** (RFP 정합)
- Parser F1 ≥ **0.90**
- WBS Classifier Macro F1 ≥ **0.90**

---

## 9. 메트릭 대시보드 설계

### 9.1 실시간 대시보드 (Grafana)

| 패널 | 메트릭 |
|---|---|
| LLM 처리량 | 초당 토큰 (Claude / Gemma / Parser) |
| LLM 지연 | p50·p95·p99 |
| Hallucination | Citation Coverage (실시간 이동 평균) |
| GPU 사용률 | A100 VRAM·GPU Util |
| API 비용 | 일별 Claude 사용량 (USD) |
| Agent 호출 분포 | 13 AG-xxx별 호출 횟수 |

### 9.2 주간 리뷰 대시보드

| 패널 | 메트릭 |
|---|---|
| Gold Set 회귀 | 버전별 F1 트렌드 |
| Phase Gate 상태 | 현재 Phase 수락 기준 달성률 |
| Hallucination Taxonomy | T1~T7 발생 건수 |
| NPS 추이 | 월별 NPS 변화 |
| 학습 데이터 누적 | WBS 유형별 수집 건수 |

---

## 10. 참조 문서

- `decisions/002-ai-model-architecture.md` — 결정 20 (Hallucination 7계층)
- `llm/02-finetuning-roadmap.md` — Phase별 수락 기준 원문
- `llm/04-security-tier-routing.md` — 라우팅 정확도 평가
- `system/02-specialized-ai-model.md` — Hallucination 방어 계층

---

## 11. 변경 이력

| 버전 | 일자 | 변경 사항 |
|---|---|---|
| 1.0 | 2026-04-18 | 최초 작성 |

---

**이 문서의 한 줄 요약**
"Gold Set 300 (WBS 8유형 + Cross-cutting 층화) + Hallucination 7계층 메트릭(Citation·Fact-Check·Schema·Ontology) + Phase Gate 수락 기준 + Canary 4주 관찰 + TTA/KAIC 외부 인증. 모든 AI 컴포넌트의 공식 평가 SSOT."
