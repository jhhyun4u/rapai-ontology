# LLM Strategy - 모델 선정 & 튜닝 계획

## 📋 Contents

| Document | Purpose | Status |
|----------|---------|--------|
| [01-model-selection.md](./01-model-selection.md) | LLM 모델 평가 기준 | ⏳ |
| [02-base-model-evaluation.md](./02-base-model-evaluation.md) | Opus/Sonnet/Haiku 비교 분석 | ⏳ |
| [03-sft-strategy.md](./03-sft-strategy.md) | 미세조정 (SFT) 전략 | ⏳ |
| [04-rag-design.md](./04-rag-design.md) | 검색증강 (RAG) 설계 | ⏳ |
| [05-token-optimization.md](./05-token-optimization.md) | Token 최적화 계획 | ⏳ |
| [06-hallucination-prevention.md](./06-hallucination-prevention.md) | Hallucination 방지 기법 | ⏳ |

## 🎯 Key Decisions

### 1. Base Model Selection
**Criteria:**
- 프로젝트 관리 도메인 전문성
- 추론 능력 (Reasoning)
- Context Window 크기
- Cost/Performance 비율
- Structured Output 지원

**Candidates:**
- Claude Opus 4.7 (최고 성능)
- Claude Sonnet 4.6 (성능/비용 균형)
- Claude Haiku 4.5 (가볍고 빠름)

### 2. Fine-Tuning (SFT) Strategy
**Data Sources:**
- PMBOK 가이드라인
- NPD 프로세스 사례
- 의사결정 기록
- 성공/실패 사례 분석

### 3. RAG (Retrieval Augmented Generation)
**Knowledge Base:**
- 온톨로지 시스템
- 의사결정 근거
- 도메인 전문 자료
- 실시간 프로젝트 데이터

### 4. Hallucination Prevention
**Mechanisms:**
- Grounding with Evidence
- Decision Chain Tracing
- Confidence Scoring
- Verification Layer

### 5. Token Optimization
**Goals:**
- 응답 시간 < 5초
- 의사결정 정확도 > 95%
- Token 사용 효율성
- Context Window 활용도

---

**Critical Path:** 
Model Selection → Base Model Testing → SFT Data Preparation → Training → Evaluation
