# 01. LLM Model Selection — 모델 선정 근거 상세

**작성일:** 2026-04-18
**상태:** ✅ Active (ADR-002 결정 13·14 기반)
**근거:** `decisions/002-ai-model-architecture.md`
**관련:** `llm/04-security-tier-routing.md`, `llm/02-finetuning-roadmap.md`

> **이 문서의 역할**
> ADR-002 결정 13·14에서 확정된 모델 선택의 **기술·라이선스·경제적 근거**를 상세화한다.
> "왜 Gemma 4인가 / 왜 EXAONE 4.0은 Baseline인가 / 왜 Claude Sonnet 4.6인가 / 왜 ModernBERT-ko·TFT·R-GCN인가"의 답을 제공한다.

---

## 1. 최종 선정 모델 매트릭스

### 1.1 LLM 포트폴리오 (결정 13)

| 역할 | 모델 | 공급자 | 라이선스 | 호스팅 | 보안등급 |
|---|---|---|---|---|---|
| **Coordinator / Specialist (Primary)** | Claude Sonnet 4.6 | Anthropic | Commercial API | Cloud | PUBLIC, RESTRICTED |
| **Coordinator / Specialist (Primary)** | **Gemma 4 31B-MoE + LoRA SFT** | Google | Gemma Terms | Self-hosted (A100×2) | CONFIDENTIAL, SECRET |
| **Coordinator / Specialist (Baseline/Backup)** | EXAONE 4.0 32B Dense | LG AI Research | Research / Commercial TBD | Self-hosted (A100×2) | CONFIDENTIAL, SECRET (백업) |
| **Parser (고빈도 저지연)** | **Gemma 4 4B + QLoRA** | Google | Gemma Terms | Self-hosted (1 GPU) | 모든 등급 |

### 1.2 Task-Specific 소형 모델 (결정 14)

| 모델 | 베이스 | 파라미터 | 용도 | 학습 방법 |
|---|---|---|---|---|
| WBS 8유형 Classifier | ModernBERT-ko | 400M + head | 계획서 → A~H 분류 | SFT (2,000 라벨) |
| 시장적합성 Scorer | Bi-encoder + BGE-Reranker | 수천만 | 기술·시장 매칭 | Contrastive + FT |
| 소요예측 Forecaster | Temporal Fusion Transformer | 커스텀 | 비용·일정 MAPE 예측 | 시계열 지도학습 |
| Task Graph GNN | Heterogeneous R-GCN (PyG) | 수천만 | 임계경로 재계산 | 그래프 지도학습 |
| 이상탐지 | Isolation Forest + LSTM-AE | 수백만 | KPI 이상점수 | 비지도 |

---

## 2. CONFIDENTIAL·SECRET 로컬 LLM 선정: Gemma 4 vs EXAONE 4.0

### 2.1 비교 평가표

| 평가 축 | Gemma 4 (Google) | EXAONE 4.0 (LG AI) | 가중 |
|---|---|---|---|
| **한국어 성능** | 🟡 중상 (멀티링구얼 커버) | 🟢 국내 SOTA (한국어 특화 사전학습) | ↑ |
| **라이선스** | 🟢 Gemma Terms (use-restriction만 준수하면 상용 가능) | 🔴 연구 전용, 상용은 LG 별도 계약 | ↑↑ |
| **SaaS 배포 가능성** | 🟢 가능 (금지목록만 회피) | 🔴 불가 (상용협약 전) | ↑↑ |
| **MoE 효율** | 🟢 31B-MoE (활성 3.8B, 추론 비용↓) | 🟡 32B Dense (Full compute) | ↑ |
| **멀티모달** | 🟢 비전·오디오 포함 | 🟡 텍스트 중심 | ↑ |
| **생태계** | 🟢 vLLM·HF·Unsloth 풍부 | 🟡 국내 중심, 해외 지원 제한 | ↑ |
| **커뮤니티 FT 레시피** | 🟢 Gemma 2/3 축적 많음 | 🟡 신규 | ↑ |
| **Anthropic Claude와의 상호 대조 평가 용이성** | 🟢 용이 | 🟡 내부 비교 | - |

**결론:**
- **Primary = Gemma 4 31B-MoE + LoRA SFT** — 라이선스 자유도·MoE 비용 우위·SaaS 로드맵 보존
- **Baseline·Backup = EXAONE 4.0 32B Dense** — 한국어 SOTA로 품질 상한선 측정 + LG 상용협약 성사 시 Primary 승격 옵션

### 2.2 Gemma 4 31B-MoE의 기술적 이점

```
MoE (Mixture of Experts) 구조:
총 파라미터 31B — 하지만 토큰당 활성화 전문가 = 상위 2~3개 (~3.8B)
→ 추론 비용: 3.8B Dense 수준
→ 지식 용량: 31B Dense 수준

RAPai 운영 관점:
· VRAM: 양자화(FP8) 시 A100×2에서 서비스 가능
· 처리량: 초당 50~80 tokens (vLLM 배치 기준)
· 비용: EXAONE 32B Dense 대비 -60~70%
```

### 2.3 EXAONE 4.0을 완전 배제하지 않는 이유

1. **품질 상한선 측정:** 한국어 R&D 도메인에서 EXAONE 4.0의 Zero-shot 성능이 상한선. Gemma 4 + LoRA가 이 선에 얼마나 도달하는지 정량 검증 필수 (Phase 0).
2. **LG 상용협약 성사 시 승격 옵션:** 계약 조건 합의되면 Primary 교체 여지 유지.
3. **법률 리스크 대비:** Gemma Terms 향후 개정 리스크에 대한 헷지.

---

## 3. PUBLIC·RESTRICTED 외부 API: Claude Sonnet 4.6 선정

### 3.1 대안 비교

| 대안 | 장점 | 단점 | 채택 |
|---|---|---|---|
| **Claude Sonnet 4.6** | 최신 추론·도구사용 SOTA, Structured Output 안정 | 비용 중간 | ✅ |
| GPT-4o / GPT-5 | 생태계 풍부 | 도구사용 편차, Asia 리전 제한 | ❌ 서브 |
| Gemini 2.5 Pro | 긴 컨텍스트 | Tool Use 안정성 부족 | ❌ 서브 |
| 로컬 Gemma 4 단일화 | 비용 0 | PUBLIC 데이터 Claude 품질 활용 기회 상실 | ❌ |

### 3.2 Claude Sonnet 4.6 선정 근거

1. **NL-First Coordinator에 최적:** Tool Use + Structured Output + Citation 안정성
2. **Hallucination-Zero L5 요구 충족:** Citation 의무 준수율 우수
3. **보안 감사 대응:** Anthropic의 Enterprise SOC2·HIPAA 등 컴플라이언스 문서화
4. **비용:** 월 $5,000 한도 내 내부 50명 규모 운영 가능 (일 1,000 호출 기준)

### 3.3 버전 정책

- `claude-sonnet-4-6-*` 버전 명시 (날짜 suffix 포함)
- 상위 판(Opus 등) 호출은 Gate 패키지 조립·보고서 최종 리뷰 등 고비용 허용 태스크에 한정

---

## 4. Parser LLM 선정: Gemma 4 4B + QLoRA

### 4.1 요구사항

- **지연:** 일지 파싱 < 1초 (실시간 사용자 대화 흐름 유지)
- **처리량:** 일 10,000 건 파싱 (50명 × 일 200건 피크)
- **메모리:** 단일 GPU (A100 40GB) 또는 소비자 GPU (RTX 4090)에서 서비스
- **품질:** F1 ≥ 0.85 (NER/IE)

### 4.2 대안 비교

| 모델 | 크기 | 지연 | 한국어 F1 예상 | 선정 |
|---|---|---|---|---|
| **Gemma 4 4B + QLoRA 4-bit** | 4B (2GB VRAM) | 🟢 <0.8s | 🟢 0.85~0.90 (튜닝 후) | ✅ |
| Gemma 4 2B | 2B | 🟢 <0.5s | 🟡 0.80 | ❌ 품질 부족 |
| Gemma 4 9B | 9B | 🟡 1.5s | 🟢 0.90 | ❌ 지연 초과 |
| KoBERT + 별도 IE head | 110M | 🟢 <0.3s | 🟡 0.78 (단일 태그 중심) | ❌ 구조 추출 어려움 |
| Llama 3.1 8B | 8B | 🟡 1.3s | 🟡 0.82 | ❌ |

### 4.3 QLoRA 선정 이유

- 4-bit 양자화로 **VRAM 75% 절감** → 단일 소비자 GPU도 가능
- r=16 Adapter만 학습 → **파라미터 0.3% 업데이트** → 학습 시간 ~수시간
- 베이스 모델 버전업 시 Adapter만 재학습 (운영 부담 최소)

---

## 5. Task-Specific 모델 선정 상세

### 5.1 WBS 8유형 Classifier — ModernBERT-ko

| 후보 | 장점 | 단점 | 선정 |
|---|---|---|---|
| **ModernBERT-ko 400M** | 긴 컨텍스트(8K), 한국어 학습, 추론 빠름 | 신규 모델 | ✅ |
| KoBERT-base | 안정, 레퍼런스 많음 | 512 토큰 한계 | ❌ |
| LLM Zero-shot (Gemma 4) | FT 없이 가능 | 비용·지연·확률 불안정 | ❌ Fallback용 |

**특화 방법:** SFT 단일 헤드(8-class softmax) + Confidence threshold 0.7.
**Fallback 규칙:** confidence < 0.7 → LLM Zero-shot 재확인 → 그래도 < 0.7 → 사용자 확인 질의 (Hallucination-Zero L3).

### 5.2 시장적합성 Scorer — Bi-encoder + BGE-Reranker

| 단계 | 모델 | 역할 |
|---|---|---|
| 1단계 | Bi-encoder (BGE-M3 기반) | 기술설명 + 시장 쿼리 임베딩 → top-50 후보 |
| 2단계 | BGE-Reranker | Cross-encoder로 top-50 → top-5 재정렬 |
| 3단계 | Rule 가중치 | 업종·TRL·Scale 매칭 가산 |

**선정 이유:** RAG Stack과 동일 임베딩 재활용 → 인프라 단순화.

### 5.3 소요예측 Forecaster — Temporal Fusion Transformer

**이유:**
- 다변량 시계열 + 정적 공변량(유형·규모)을 한 모델에서 처리
- Attention 기반 해석 가능성 (어떤 피처가 영향력이 컸는지)
- LightGBM 대비 MAPE 2~4pp 개선 (R&D 시계열 일반 벤치마크)

**Fallback:** 데이터 부족 시 LightGBM 단순 회귀 + 점진적 TFT 확장.

### 5.4 Task Graph GNN — Heterogeneous R-GCN (PyG)

**이유:**
- WBS는 이종 노드(Activity / Milestone / Deliverable / Risk)와 이종 엣지(depends_on / produces / blocks)의 그래프
- Heterogeneous GCN이 이 구조를 native로 표현
- PyTorch Geometric의 성숙도

**대안 기각:** Homogeneous GNN은 표현력 부족, GraphSAGE는 엣지 타입 미구분.

### 5.5 이상탐지 — Isolation Forest + LSTM-AE

| 용도 | 모델 | 이유 |
|---|---|---|
| 점수형 KPI 이상치 | Isolation Forest | 훈련 없이 즉시 적용, 해석 쉬움 |
| 시계열 패턴 이상 | LSTM-AE (Autoencoder) | 주기성·트렌드 이탈 탐지 |

**결합 규칙:** 둘 중 하나라도 임계 초과 → AG-SENSE가 CRITICAL 신호 발동 → L4 Moving Target Gate 트리거.

---

## 6. 라이선스·컴플라이언스 체크

### 6.1 Gemma Terms 준수 요건

- 사용 금지 목록: 불법·차별·무기화 등 (RAPai 해당 없음)
- 배포 시 "Gemma" 귀속 표시
- 모델 가중치 재배포 시 수정 사항 명시
- **상용 SaaS 배포 허용** (금지목록 회피 시)

→ **결정:** 법무 검토 1회 (Phase 1 초입) + 연 1회 라이선스 개정 추적.

### 6.2 EXAONE 4.0 라이선스 상태

- 공식 라이선스: 연구 전용 (Non-commercial)
- 상용 이용은 LG AI Research와 별도 계약
- **Phase 0 평가 단계**는 연구 전용 라이선스로 수행 가능
- **프로덕션 투입 시** 계약 필수 → Baseline 역할 한정 (Primary 아님)

### 6.3 Claude API 컴플라이언스

- Anthropic DPA 체결 (내부 데이터 처리 합의)
- Zero Data Retention 옵션 활성화 (Enterprise)
- **PUBLIC·RESTRICTED 한정** 전송 (보안등급 라우팅으로 강제)

---

## 7. 총비용 모델 (TCO) 추정

### 7.1 월간 운영비 추정 (내부 50명 기준)

| 항목 | 비용 | 근거 |
|---|---|---|
| Claude API (Sonnet 4.6) | ~$3,500/월 | PUBLIC·RESTRICTED 일 1,000 호출 × 30일 × 평균 8K token |
| GPU 임대 (A100×2, Gemma 4 31B) | ~$1,800/월 | 24/7 운영, AWS/GCP Spot |
| GPU 임대 (A100×1, Parser 4B) | ~$600/월 | 24/7 운영 |
| Qdrant + PostgreSQL + Neo4j | ~$500/월 | 온프레미스 유지 기준 |
| **합계** | **~$6,400/월** | Phase 2 정상 운영 |

### 7.2 Phase별 비용 변동

- **Phase 0 (M1~M2):** Claude API 비중 높음 (~$4,000/월)
- **Phase 1 (M3~M8):** GPU 학습 비용 +$3,000/월 (Phase당 일시)
- **Phase 2 (M9~M12):** 위 정상 운영 ~$6,400/월
- **Phase 3+ (Y2+):** 로컬 모델 의존 확대로 Claude 비중 감소 → ~$5,000/월 목표

---

## 8. Phase 0 벤치마크 프로토콜 (즉시 실행)

### 8.1 평가 데이터

- 한국 R&D 샘플 100건 (기초연구 20 / 기술개발 30 / 사업화 20 / 정책 15 / 컨설팅 10 / 학술용역 5)
- 라벨: WBS 유형, 주요 엔티티, Gate 판정 결과 (사람 작성 골드)

### 8.2 비교 후보

1. Claude Sonnet 4.6 (Zero-shot)
2. Gemma 4 27B Dense (Zero-shot)
3. Gemma 4 31B-MoE (Zero-shot)
4. EXAONE 4.0 32B Dense (Zero-shot)
5. Parser 검증: Gemma 4 4B (Zero-shot) vs KoBERT+head

### 8.3 메트릭

- F1 (exact + partial), Macro F1, MAPE(예측), 지연시간, VRAM, 월 API 비용 환산
- 문체 품질: 사람 5-스케일 평가 (내부 3인 IAA)

### 8.4 산출물

`research/phase0-benchmark-report.md` — 베이스 모델·사이즈 최종 확정 근거 리포트.

---

## 9. 선정 변경 트리거 (Revisit Conditions)

다음 조건 발생 시 본 문서·ADR-002 결정 13·14 재검토:

| 트리거 | 대응 |
|---|---|
| Gemma 4 새 버전 (5·다음 메이저) 출시 | Phase 0 재벤치 후 마이너 업데이트 |
| Gemma Terms 개정 (제약 강화) | 법무 검토 + EXAONE Primary 승격 검토 |
| LG AI Research와 상용협약 성사 | EXAONE 4.0을 Primary 후보로 재평가 |
| Claude Sonnet 월 비용 $6,000 초과 | 로컬 전환 비율 상향 |
| Gold Set F1이 1년간 0.85 미달 | Full Fine-tuning 또는 Continued Pre-training 투입 |

---

## 10. 참조 문서

- `decisions/002-ai-model-architecture.md` — 결정 7~22 원문
- `system/02-specialized-ai-model.md` — 5-Tier 아키텍처 + AG 매핑
- `llm/02-finetuning-roadmap.md` — Phase 0~4 로드맵
- `llm/03-evaluation-framework.md` — 평가 메트릭 상세
- `llm/04-security-tier-routing.md` — 라우팅 운영 가이드

---

## 11. 변경 이력

| 버전 | 일자 | 변경 사항 |
|---|---|---|
| 1.0 | 2026-04-18 | 최초 작성 (ADR-002 결정 13·14 반영) |

---

**이 문서의 한 줄 요약**
"RAPai LLM 포트폴리오 = Claude Sonnet 4.6 (PUBLIC·RESTRICTED) + Gemma 4 31B-MoE + LoRA SFT (CONFIDENTIAL·SECRET Primary) + EXAONE 4.0 32B Dense (Baseline·백업) + Gemma 4 4B + QLoRA (Parser). 소형 모델 5종 = ModernBERT-ko 8-class / Bi-encoder Scorer / TFT / R-GCN / Isolation Forest+LSTM-AE. 라이선스·MoE 효율·SaaS 로드맵이 Gemma를 Primary로 결정한 핵심 근거."
