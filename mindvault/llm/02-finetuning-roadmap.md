# 02. Fine-tuning Roadmap — Phase 0~4 파인튜닝 로드맵 + WBS 8유형 데이터 할당

**작성일:** 2026-04-18
**상태:** ✅ Active (ADR-002 결정 18·19 기반)
**근거:** `decisions/002-ai-model-architecture.md`
**관련:** `llm/01-model-selection.md`, `llm/03-evaluation-framework.md`

> **이 문서의 역할**
> ADR-002 결정 18(학습 데이터)·19(4-Phase 로드맵)를 **월 단위 실행 계획**으로 상세화한다.
> "언제 무엇을 학습·평가·배포하는가"의 단일 진실(SSOT).

---

## 1. 로드맵 전체 타임라인 (36개월 기준)

```
Year 1 ─────────────────────────────────────────────────────────
  M1~M2   │ Phase 0 Baseline (Zero-shot 벤치마크)
  M3~M8   │ Phase 1 SFT + LoRA/QLoRA (주력 학습)
  M9~M12  │ Phase 2 평가·보강 (1차년도 KPI 점검)

Year 2 ─────────────────────────────────────────────────────────
  M13~M24 │ Phase 3 DPO + RAG 프로덕션 (내부 50명 피드백)

Year 3 ─────────────────────────────────────────────────────────
  M25~M36 │ Phase 4 실증·공개 (TTA/KAIC 인증, 오픈웨이트)
```

---

## 2. Phase 0 — Baseline (M1~M2)

### 2.1 목표

- 3개 후보 LLM + Parser 후보의 **Zero-shot 성능**을 실측
- **베이스 모델·사이즈 최종 확정**
- Phase 1 시작 전 "비교 가능한 출발선" 확보

### 2.2 주간 일정

| Week | 작업 | 산출 |
|---|---|---|
| W1 | 평가 데이터셋 100건 작성 (라벨 포함) | `evals/phase0/gold_100.jsonl` |
| W2 | Claude Sonnet 4.6 Zero-shot 실행 | `results/claude_zeroshot.csv` |
| W3 | Gemma 4 (27B Dense / 31B-MoE) Zero-shot 실행 | `results/gemma_*.csv` |
| W4 | EXAONE 4.0 32B Dense Zero-shot 실행 | `results/exaone_zeroshot.csv` |
| W5 | Parser 후보 비교 (Gemma 4 4B vs KoBERT+head) | `results/parser_compare.csv` |
| W6 | 통합 리포트 작성 | `research/phase0-benchmark-report.md` |
| W7 | Phase 1 계획 확정 | TodoWrite → 학습 데이터 수집 착수 |
| W8 | 버퍼 / 법무 검토 (Gemma Terms) | 법무 확인서 |

### 2.3 수락 기준

- 5개 모델 × 6개 태스크 = 30 데이터포인트 확보
- Gemma 4 31B-MoE Zero-shot F1 ≥ 0.70 (NER/IE)
- EXAONE 4.0 Zero-shot과 Gemma 4 Zero-shot의 성능 격차 <10pp

→ 조건 만족 시 Gemma 4 31B-MoE를 Primary로 확정 진행.

---

## 3. Phase 1 — SFT + LoRA/QLoRA (M3~M8)

### 3.1 목표

- Research Manager LLM: **7,800 페어 SFT (LoRA)**
- Parser LLM: **2,000 페어 QLoRA (4-bit)**
- Task-Specific 소형 5종 각각 학습

### 3.2 월별 일정

#### M3 — 학습 데이터 수집 착수

- 합성 500건 생성 (Claude Sonnet로 한국 R&D 일지 시뮬레이션)
- 내부 계획서·보고서·일지 DB 크롤링 시작 (목표 2,000건)
- Qdrant `contract_research_corpus` 별도 수집 라인 가동 (목표 600건)

#### M4 — Auto-labeling 파이프라인

- Claude Sonnet 기반 1차 라벨링 자동화
- 연구원 검수 UI 구축 (3명 × 일 50건)
- 중간 검수 결과 400건 확보

#### M5 — 1차 학습 착수

- **Research Manager LLM LoRA (v0.1):**
  - 베이스: Gemma 4 31B-MoE
  - 데이터: 합성 500 + 내부 400 = 900건
  - Hyperparam: r=32, α=64, lr=1e-4, epochs=3, batch=8
  - 산출: `adapters/research_mgr_v0.1`
- **Parser LLM QLoRA (v0.1):**
  - 베이스: Gemma 4 4B
  - 데이터: 500건 (합성 300 + 내부 200)
  - Hyperparam: r=16, α=32, 4-bit, lr=2e-4, epochs=5
  - 산출: `adapters/parser_v0.1`

#### M6 — 소형 모델 5종 학습

- WBS 8유형 Classifier (ModernBERT-ko): 1,500건 라벨
- 시장적합성 Scorer: 500 페어 Contrastive
- TFT Forecaster: NTIS + 내부 시계열
- R-GCN: WBS 그래프 300건
- Isolation Forest + LSTM-AE: 비지도 (전체)

#### M7 — 2차 학습 (데이터 확장)

- 내부 데이터 총 1,500건 누적 (Gold Set 300 분리 전)
- **Research Manager LLM LoRA (v0.2):** 데이터 합성 500 + 내부 1,500 = 2,000건
- **Parser LLM QLoRA (v0.2):** 1,500건

#### M8 — Phase 1 마감 학습

- 데이터 최종 2,300건 (Gold Set 300 제외)
- **Research Manager LLM LoRA (v1.0):** 전체 SFT
- **Parser LLM QLoRA (v1.0):** 전체 QLoRA
- 내부 5명 A/B 평가

### 3.3 WBS 8유형 + Cross-cutting 데이터 할당

**총 2,800건 목표 (합성 500 + 내부 2,000 + Gold Set 300):**

| 유형 | 비율 | 건수 | 대표 사례 |
|---|---|---|---|
| **A 탐구형** | 15% | 300 | 정부 기초연구, 학술연구 일지 |
| **B 개발형** | 20% | 400 | 중기부 기술개발·산업기술혁신 일지 |
| **C 사업화·실증형** | 15% | 300 | 사업화 지원·Scale-up 일지 |
| **D 조사·분석형** | 15% | 300 | 성과조사·통계·실태조사 일지 |
| **E 기획·전략형** | 10% | 200 | 기술로드맵·ISP 일지 |
| **F 컨설팅형** | 10% | 200 | AX·DX·경영 컨설팅 일지 |
| **G 복합·전주기형** | 10% | 200 | 원천→사업화 전환 일지 |
| **H 행사운영형** | 5% | 100 | 행사·컨퍼런스 운영 일지 |
| **합계 (WBS)** | 100% | 2,000 | (내부 데이터 기준) |
| + 합성 | — | 500 | Phase 0~1 초기 부트스트랩 |
| + Gold Set | — | 300 | 평가 전용 홀드아웃 |
| **총계** | — | **2,800** | |

**Cross-cutting 속성 의무:**

| 속성 | 최소 비율 | 비고 |
|---|---|---|
| `contract_modality = contract_research` | **≥ 30% (600건)** | 학술연구용역 전용 모듈 학습 필수 (결정 22) |
| `contract_modality = public_grant` | ≥ 40% (800건) | 정부 R&D 과제 주력 |
| `contract_modality = internal_rd` | 나머지 | 자체 R&D |
| `security_tier` 분포 | PUBLIC/RESTRICTED/CONFIDENTIAL 각 ≥ 20% | 보안등급 라우팅 학습 커버 |
| `scale_tier` 분포 | small/medium/large 각 ≥ 20% | 규모별 WBS 깊이 학습 |

### 3.4 데이터 수집 방법

| 단계 | 소스 | 규모 | 기간 |
|---|---|---|---|
| 합성 | Claude Sonnet | 500건 | M1~M3 |
| 내부·수요기업 | 실제 계획서·일지·보고서 | 2,000건+ | M3~M9 |
| Auto-labeling + 검수 | Claude 1차 → 연구원 3명 검수 | 2,000 검수 | M6~M11 |
| Gold Set | 홀드아웃 F1 평가용 | 300건 | M10~M12 |
| DPO 선호도 | Year 2 사용자 A/B 로그 | 2,000 페어 | M13~M24 |

### 3.5 수락 기준 (Phase 1 종료 시점)

- Research Manager LLM v1.0: Gold Set F1 ≥ 0.75
- Parser LLM v1.0: 일지 NER F1 ≥ 0.80, 지연 <1초
- WBS Classifier: Macro F1 ≥ 0.85
- TFT Forecaster: MAPE ≤ 20%
- Hallucination Citation Coverage ≥ 0.90

---

## 4. Phase 2 — 평가·보강 (M9~M12)

### 4.1 목표

- 1차년도 KPI 중간 점검
- TTA/KAIC 프리테스트
- 부족 영역 데이터 보강 + 재학습

### 4.2 월별 일정

| M | 작업 |
|---|---|
| M9 | Gold Set 300 전면 평가 실행 |
| M10 | 약점 영역 식별 (유형 F·G·H 데이터 부족 여부) + 보강 수집 |
| M11 | 보강 학습 (v1.1) + 내부 50명 A/B |
| M12 | TTA/KAIC 프리테스트 신청 + 성능 인증서 수령 |

### 4.3 수락 기준 (M12 종료 시점)

- Research Manager LLM v1.1: Gold Set F1 ≥ 0.80
- WBS Classifier Macro F1 ≥ 0.88
- Hallucination Citation Coverage ≥ 0.92
- 내부 NPS ≥ +20

---

## 5. Phase 3 — DPO + RAG 프로덕션 (Year 2, M13~M24)

### 5.1 목표

- 내부 50명 사용 **피드백 기반 DPO**
- RAG 파이프라인 **프로덕션 통합**
- 학술연구용역 Corpus 별도 심화 학습

### 5.2 분기별 일정

#### Q1 (M13~M15) — DPO 데이터 수집 체계 구축

- 사용자 선호도 A/B 로깅 UI 구축
- 월 500 페어 × 4개월 = 2,000 페어 목표
- PROV-O에 user_preference 이벤트 기록

#### Q2 (M16~M18) — DPO 학습

- Research Manager LLM DPO 튜닝 (v2.0)
- 베이스: v1.1 Adapter + DPO Adapter 스택
- Hyperparam: β=0.1, lr=5e-7, epochs=2

#### Q3 (M19~M21) — RAG 프로덕션 통합

- Qdrant Hybrid Search 최적화 (BM25 가중치 조정)
- BGE-Reranker 파인튜닝 (한국 R&D 도메인)
- Citation 강제 규칙 상향 (L5 방어 강화)

#### Q4 (M22~M24) — 학술연구용역 심화

- `contract_research_corpus` 전용 임베딩 재학습
- AG-QA L2-C Gate 룰 정교화
- 재수주 확률 Score ML 학습 (과거 3년 데이터)

### 5.3 수락 기준 (M24 종료 시점)

- Research Manager LLM v2.0: Gold Set F1 ≥ 0.82
- DPO 적용 후 사용자 선호 승률 ≥ 65%
- 학술연구용역 Gate 판정 정확도 ≥ 0.95
- 내부 NPS ≥ +40

---

## 6. Phase 4 — 실증·공개 (Year 3, M25~M36)

### 6.1 목표

- 내부 50명 실운영 데이터로 **최종 재학습**
- **TTA/KAIC 제3자 F1 인증 (목표 F1 ≥ 0.85)**
- 오픈웨이트 공개 (Gemma Terms 준수)

### 6.2 분기별 일정

#### Q1 (M25~M27) — 최종 재학습 준비

- 실운영 데이터 6,000건 누적
- WBS 유형 분포 재점검 + 부족 유형 수집
- Continued Pre-training 검토 (10만+ 코퍼스 확보 시)

#### Q2 (M28~M30) — 최종 학습

- Research Manager LLM v3.0: 전체 데이터 재학습
- Parser LLM v3.0: QLoRA 재학습
- 소형 모델 5종 재학습

#### Q3 (M31~M33) — 외부 인증

- TTA 또는 KAIC에 모델 성능 인증 요청
- Gold Set 300 + 외부 평가셋 별도 200건
- 인증서 수령 후 공개 자료 준비

#### Q4 (M34~M36) — 오픈웨이트 공개

- Gemma 4 + LoRA Adapter 공개 (HuggingFace)
- 모델 카드 작성 (사용법·한계·편향)
- 커뮤니티 피드백 수집 프로세스 가동

### 6.3 수락 기준 (M36 종료 시점)

- TTA/KAIC 인증 F1 ≥ 0.85
- Parser F1 ≥ 0.90
- 오픈웨이트 공개 완료
- 외부 사용자 수 ≥ 10개 기관

---

## 7. 학습 인프라 사양

### 7.1 Phase별 GPU 요구

| Phase | GPU | 기간 | 용도 |
|---|---|---|---|
| Phase 0 | A100×1 (임대) | 2주 | Zero-shot 벤치 |
| Phase 1 | **A100×8 (임대) × 4주** | M5, M7~M8 | Gemma 31B-MoE LoRA |
| Phase 1 | A100×1 | 상시 | Parser QLoRA + 소형 모델 |
| Phase 2 | A100×4 × 2주 | M11 | 보강 학습 |
| Phase 3 | A100×4 × 4주 | M18 | DPO 학습 |
| Phase 3 | A100×2 | 상시 | 프로덕션 서비스 |
| Phase 4 | A100×8 × 4주 | M28~M29 | 최종 재학습 |

### 7.2 스토리지 요구

- 모델 가중치: ~100GB (Gemma 31B FP8 + Adapter 여러 버전)
- 학습 데이터: ~50GB (2,800건 + 검수 로그)
- PROV-O Lineage: ~200GB/년 (S3 Cold)
- Gold Set + 평가 로그: ~10GB

### 7.3 MLOps 체계

- 학습: HuggingFace TRL + Unsloth (Gemma 최적화)
- 실험 추적: MLflow (모델별 버전·메트릭·하이퍼파라미터)
- 배포: vLLM 서빙 + Canary 라우팅 (10% → 100%)
- 모니터링: Prometheus + Grafana (p95 지연·토큰량·GPU 사용률)

---

## 8. 리스크 & 컨틴전시

### 8.1 리스크 매트릭스

| 리스크 | 영향 | 확률 | 대응 |
|---|---|---|---|
| 내부 데이터 2,000건 미달 | 상 | 중 | 합성 600건 추가 + Phase 1 4주 연장 |
| Gemma 4 Zero-shot F1 < 0.65 | 상 | 저 | EXAONE 4.0 Primary 전환 또는 LG 상용협약 추진 |
| 학술연구용역 600건 미달 | 중 | 중 | TENOPA 과거 프로젝트 전수 수집 + 동의서 |
| GPU 공급 제약 (A100) | 중 | 중 | H100·A10G 대체안 + 학습 배치 축소 |
| 라이선스 개정 (Gemma) | 상 | 저 | 분기 1회 법무 검토 + EXAONE 승격 옵션 |

### 8.2 Phase Gate 규칙

각 Phase 종료 시 수락 기준 **미달 시 다음 Phase 진입 금지**:
- Phase 0 미달 → W8 재벤치마크 또는 데이터 보강
- Phase 1 미달 → M9~M10 집중 보강 후 재학습
- Phase 2 미달 → Phase 3 시작 연기 (최대 2개월)
- Phase 3 미달 → DPO 재설계 (β 조정 + 선호 데이터 재수집)

---

## 9. 산출물 체크리스트

### 9.1 Phase 0 산출물

- [ ] `research/phase0-benchmark-report.md`
- [ ] `evals/phase0/gold_100.jsonl`
- [ ] 법무 확인서 (Gemma Terms)

### 9.2 Phase 1 산출물

- [ ] `adapters/research_mgr_v1.0/` + 카드
- [ ] `adapters/parser_v1.0/` + 카드
- [ ] 소형 모델 5종 각 `models/*/v1.0/`
- [ ] `evals/gold_set_300.jsonl`
- [ ] 학습 데이터 메타 (`data/metadata.jsonl`)

### 9.3 Phase 2 산출물

- [ ] TTA/KAIC 프리테스트 성적서
- [ ] v1.1 Adapter + 개선 리포트

### 9.4 Phase 3 산출물

- [ ] `adapters/research_mgr_dpo_v2.0/`
- [ ] DPO 선호 데이터셋 2,000 페어
- [ ] `contract_research_corpus` 파인튠 재임베딩

### 9.5 Phase 4 산출물

- [ ] TTA/KAIC 공식 인증서
- [ ] 오픈웨이트 HuggingFace 공개 페이지
- [ ] 모델 카드 (사용법·한계·편향)

---

## 10. 참조 문서

- `decisions/002-ai-model-architecture.md` — 결정 18·19 원문
- `llm/01-model-selection.md` — 모델 선정 근거
- `llm/03-evaluation-framework.md` — 평가 메트릭·Gold Set
- `llm/04-security-tier-routing.md` — 라우팅 운영
- `ontology/10-project-type-classification-v2.md` — WBS 8유형

---

## 11. 변경 이력

| 버전 | 일자 | 변경 사항 |
|---|---|---|
| 1.0 | 2026-04-18 | 최초 작성 (ADR-002 결정 18·19 반영) |

---

**이 문서의 한 줄 요약**
"Phase 0 (M1~M2 벤치) → Phase 1 (M3~M8 SFT+LoRA/QLoRA, 2,800건) → Phase 2 (M9~M12 보강 + TTA 프리테스트) → Phase 3 (Y2 DPO + RAG 프로덕션) → Phase 4 (Y3 실증·공개, F1 ≥ 0.85). WBS 8유형별 할당 + contract_research ≥ 30% 의무로 편향 제거."
