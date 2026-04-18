# MindVault - RAPai (Research AI Platform)

**Last Updated:** 2026-04-18
**Project Owner:** hyunjaeho@tenopa.co.kr
**System Brand:** RAPai — AI-Native R&D Project Management Platform (v2.9 통합설계명세서 준용)

---

## 📚 Knowledge Structure

### 1. [System Design](./system/) - 시스템 설계 & 아키텍처
- 전체 시스템 비전 및 철학
- 시스템 아키텍처
- 컴포넌트 설계
- 인터페이스 정의
- ✅ [01-harness-engineering.md](./system/01-harness-engineering.md) — Harness Engineering 5 요소
- ✅ **[02-specialized-ai-model.md](./system/02-specialized-ai-model.md)** — 특화 AI 모델 개념·방법·13 AG-xxx 매핑 (ADR-002 기반)

### 2. [Ontology](./ontology/) - 개념 체계 & 데이터 모델
- 연구 프로젝트 도메인 온톨로지
- PMBOK 매핑
- NPD Process 매핑
- 의사결정 프레임워크
- ✅ **[10-project-type-classification-v2.md](./ontology/10-project-type-classification-v2.md)** — WBS 8유형(A~H) + Cross-cutting 속성 2축 분류 체계 **(v2.0 정본)**
- 📎 [05-project-types-and-terms.md](./ontology/05-project-types-and-terms.md) — v1 개념 해설 (보존, v2.0으로 superseded)

### 3. [Decisions](./decisions/) - 의사결정 기록 & 근거
- 아키텍처 의사결정 기록 (ADR)
- 의사결정 근거
- 선택지 분석
- 트레이싱 체인
- ✅ **[ADR-001: Ontology Strategy](./decisions/001-ontology-strategy.md)** — 온톨로지 전략 확정 (L2.5 + Palantir 철학 차용, 결정 1~6)
- ✅ **[ADR-002: AI Model Architecture](./decisions/002-ai-model-architecture.md)** — 특화 AI 모델 아키텍처 확정 (결정 7~22, 학술연구용역 First-class 모듈 포함)

### 4. [Research](./research/) - 참고 자료 & 벤치마크
- PMBOK 6 & 7 가이드라인
- NPD Process 참고
- 경쟁사 및 유사 시스템 분석
- 기술 트렌드

### 5. [LLM Strategy](./llm/) - LLM 모델 선정 & 튜닝
- 모델 평가 기준 (보안등급별 라우팅)
- 기본 모델 선정 (Claude Sonnet 4.6 + Gemma 4 31B-MoE + EXAONE 4.0 Baseline + Gemma 4 4B Parser)
- 미세조정 전략 (LoRA / QLoRA / DPO / RAG 하이브리드)
- Token 최적화 계획
- 📎 [00-discussion-opener.md](./llm/00-discussion-opener.md) — 초기 논의 문서 (참고용, ADR-002로 결정 공식화 완료)
- ✅ **[01-model-selection.md](./llm/01-model-selection.md)** — 모델 선정 근거 상세 (Gemma 4 vs EXAONE 4.0 vs Claude, Task-Specific 5종)
- ✅ **[02-finetuning-roadmap.md](./llm/02-finetuning-roadmap.md)** — Phase 0~4 파인튜닝 로드맵 + WBS 8유형 데이터 할당
- ✅ **[03-evaluation-framework.md](./llm/03-evaluation-framework.md)** — 평가 메트릭 + Gold Set 300건 설계 + Hallucination-Zero 7계층
- ✅ **[04-security-tier-routing.md](./llm/04-security-tier-routing.md)** — 보안등급 LLM 라우팅 운영 가이드 + ABAC 4속성 + PROV-O

### 6. [Implementation](./implementation/) - 구현 로드맵
- 개발 단계별 계획
- 스프린트 정의
- 체크포인트 및 검증

### 7. [Tracing System](./tracing/) - 모든 의사결정 추적
- Hallucination Prevention 방법론
- Decision Tree Tracing
- Audit Log Design
- Evidence Linking

---

## 🎯 Current Status

| Phase | Status | Priority | Artifact |
|-------|--------|----------|----------|
| System Philosophy & Identity (RAPai) | ✅ Confirmed | **HIGH** | v2.9 통합설계명세서 |
| Ontology Strategy | ✅ Accepted | **HIGH** | ADR-001 (결정 1~6) |
| Project Type Classification v2.0 | ✅ Accepted | **HIGH** | ontology/10-project-type-classification-v2.md |
| AI Model Architecture | ✅ Accepted | **HIGH** | ADR-002 (결정 7~22) |
| LLM Strategy Detail | ✅ Accepted | **HIGH** | llm/01~04 (4종 완비) |
| Specialized AI Model Design | ✅ Accepted | **HIGH** | system/02-specialized-ai-model.md |
| Tracing System Design | ⏳ Planning | **HIGH** | PROV-O Lineage (결정 20) |
| Implementation Roadmap | 🟡 In Progress | **MEDIUM** | Phase 0~4 (결정 19) |

---

## 📖 How to Use This Vault

1. **Browse by Category:** 위의 카테고리별 링크로 이동
2. **Search Tags:** 태그로 관련 문서 검색
3. **Decision Tracing:** `decisions/` 폴더에서 의사결정 근거 확인
4. **Latest Updates:** 최신 업데이트 먼저 확인

---

## 🔗 Quick Links

- [ADR-001: Ontology Strategy](./decisions/001-ontology-strategy.md) — 결정 1~6 (L2.5 + JSON Schema SSOT)
- [ADR-002: AI Model Architecture](./decisions/002-ai-model-architecture.md) — 결정 7~22 (5-Tier Hybrid + 학술연구용역 모듈)
- [Project Type Classification v2.0](./ontology/10-project-type-classification-v2.md) — WBS 8유형 + Cross-cutting
- [Specialized AI Model](./system/02-specialized-ai-model.md) — 5-Tier × 13 AG-xxx 매핑
- [LLM Model Selection](./llm/01-model-selection.md) — Gemma 4 / EXAONE 4.0 / Claude 선정
- [Finetuning Roadmap](./llm/02-finetuning-roadmap.md) — Phase 0~4 + WBS 8유형 할당
- [Evaluation Framework](./llm/03-evaluation-framework.md) — Gold Set 300 + Hallucination-Zero 메트릭
- [Security-Tier Routing](./llm/04-security-tier-routing.md) — ABAC + PROV-O 감사
- [Ontology Stack Catalog](./ontology/08-ontology-stack-catalog.md) — 온톨로지 기술 스택
- [Operational Ontology Design](./ontology/07-operational-ontology-design.md) — Event-Driven Agentic OS
- [Work & Activity Ontology](./ontology/09-work-activity-ontology.md) — NL-First Intent/Entity
- [Final Plan (v2.9 정합판)](../../../claude/plans/memoized-mapping-dongarra.md) — 실행 플랜 (C:\claude\plans 위치)

---

## 💡 Key Principles

✅ **Hallucination Zero** - 모든 답변은 근거와 함께  
✅ **Decision Tracing** - 모든 의사결정 기록  
✅ **Harness Engineering** - 체계적인 검증  
✅ **Token Optimization** - 효율적인 자원 사용
