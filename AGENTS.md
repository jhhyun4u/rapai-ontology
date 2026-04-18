# AGENTS.md - AI-Native Research Project Management Platform

**목차 역할 파일입니다. 자세한 내용은 `mindvault/` 폴더를 참고하세요.**

---

## 🎯 에이전트의 역할

이 플랫폼에서 AI 에이전트는:
- **연구 프로젝트 자동 관리**: 계획서 입력 → WBS, Schedule, 리스크 관리 자동 생성
- **의사결정 추적**: 모든 결정의 근거를 기록하고 추적
- **지속적 개선**: 피드백을 받아 자동으로 수정 및 개선
- **관찰 가능성 제공**: 실시간 프로젝트 상태, KPI, 리스크 신호 제공

---

## 📚 지식 베이스 구조

```
mindvault/
├── system/              → 시스템 설계 및 아키텍처
│   └── 01-harness-engineering.md (핵심: Harness 설계)
├── ontology/            → 도메인 개념 및 매핑
│   └── 01-framework.md
├── decisions/           → 의사결정 기록 및 근거
│   └── ADR 형식
├── research/            → 참고 자료 (PMBOK, NPD, 사례)
│   └── benchmarks/
├── llm/                 → LLM 선정 및 튜닝 전략
│   └── 01-model-selection.md
├── implementation/      → 개발 로드맵
│   └── Phase 0~5
└── tracing/             → 의사결정 추적 시스템
    └── 01-tracing-architecture.md
```

---

## 🔗 주요 문서 (Quick Links)

| 문서 | 목적 | 상태 |
|------|------|------|
| [Harness Engineering](./mindvault/system/01-harness-engineering.md) | 시스템의 핵심 설계 철학 | ✅ |
| [Ontology Framework](./mindvault/ontology/01-framework.md) | 개념 체계 정의 | ⏳ |
| [LLM Selection](./mindvault/llm/01-model-selection.md) | 모델 선정 기준 | ⏳ |
| [Tracing System](./mindvault/tracing/01-tracing-architecture.md) | 의사결정 추적 | ⏳ |
| [Implementation Plan](./mindvault/implementation/README.md) | 개발 로드맵 | ⏳ |

---

## ⚙️ 에이전트 동작 원칙

### 입력
```
사용자가 제공:
  1. 연구계획서 (Research Plan)
  2. 프로젝트 제약 (Constraints)
  3. 우선순위 (Priorities)
```

### 프로세싱
```
에이전트가 수행:
  1. 프로젝트 유형 분류 (PMBOK + NPD 기준)
  2. 적절한 관리 방법론 선택
  3. WBS, Schedule, 리소스 계획 생성
  4. 리스크 분석 및 대응 계획
  5. 성과 지표 정의
  6. 모든 의사결정 근거 기록
```

### 출력
```
생성물:
  - WBS (Work Breakdown Structure)
  - Project Schedule (간트 차트)
  - Resource Plan
  - Risk Register & Mitigation
  - KPI Dashboard
  - Decision Log (근거와 함께)
  - Knowledge Repository (프로젝트별)
```

---

## 🎯 에이전트가 따라야 할 원칙

✅ **MUST DO**
- 모든 의사결정에 근거 기록
- PMBOK 6/7 가이드라인 준수
- 프로젝트 유형별 맞춤 관리
- 실시간 모니터링 및 리포팅

❌ **MUST NOT**
- 근거 없는 의사결정
- Hallucination (환각)
- 아키텍처 규칙 위반
- 오래된 정보 사용

---

## 🔧 구현 현황

| 단계 | 항목 | 진행도 |
|------|------|--------|
| **Phase 0: Foundation** | Harness 설계 | 50% |
| | Ontology 설계 | 0% |
| | LLM 전략 | 0% |
| | Tracing 시스템 | 0% |
| **Phase 1: Core Agent** | 의사결정 엔진 | 0% |
| | 기본 에이전트 | 0% |
| **Phase 2+** | 기능 구현 | 0% |

---

## 📞 에이전트 사용 방법

```bash
# 간단한 프로젝트 관리
claude-agent "소프트웨어 R&D 프로젝트 계획서" < research_plan.md

# 복잡한 프로젝트 (실행 계획 포함)
claude-agent --plan --monitor research_plan.md

# 실시간 모니터링
claude-agent --monitor --dashboard research_project_id
```

---

**더 자세한 내용은 `mindvault/` 폴더의 해당 섹션을 참고하세요.**
