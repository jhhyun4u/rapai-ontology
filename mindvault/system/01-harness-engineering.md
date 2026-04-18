# Harness Engineering - AI-Native 연구 프로젝트 관리 시스템

**Based on:** OpenAI's Harness Engineering Paper  
**Context:** AI-Native Research Project Management Platform  
**Date:** 2026-04-18

---

## 🎯 Core Philosophy

**"사람이 조정하고, AI 에이전트가 수행한다"**

```
사람의 역할: 설계 → 의도 명시 → 피드백 루프 구축 → 검증
AI 에이전트: 의사결정 실행 → 관리 자동화 → 자기 수정 → 근거 기록
```

---

## 📐 Harness Engineering의 5가지 핵심 요소

### 1️⃣ **Environment Design** - 에이전트가 작동할 수 있는 환경

#### 문제: 에이전트는 도구, 추상화, 내부 구조가 없으면 일을 수행할 수 없음

#### 해결책: 계층적 구조와 명확한 인터페이스 설계

```
연구 프로젝트 관리 에이전트가 작동하기 위한 기본 환경:

┌─────────────────────────────────────────────────────┐
│ 1. 온톨로지 시스템 (Ontology Layer)                  │
│    - 연구 프로젝트 도메인 개념 정의                  │
│    - PMBOK 6/7 프로세스 매핑                         │
│    - NPD 프로세스 통합                               │
│    - 의사결정 프레임워크                              │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 2. 지식 베이스 (Knowledge Repository)                │
│    - 설계 문서 (Design Docs)                         │
│    - 실행 계획 (Execution Plans)                     │
│    - 의사결정 기록 (Decision Logs)                   │
│    - 성공/실패 사례 (Case Studies)                   │
│    - 참고 자료 (Reference Materials)                 │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 3. 의사결정 도구 (Decision Tools)                    │
│    - 프로젝트 분류기 (Project Classifier)            │
│    - WBS 생성기 (WBS Generator)                      │
│    - Schedule 최적화기 (Scheduler)                   │
│    - 리스크 분석기 (Risk Analyzer)                   │
│    - 리소스 할당기 (Resource Allocator)              │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 4. 관찰 가능성 (Observability)                       │
│    - 프로젝트 상태 모니터링                           │
│    - 성과 지표 수집                                  │
│    - 리스크 신호 감지                                │
│    - 의사결정 근거 기록                              │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 5. 피드백 루프 (Feedback Loop)                       │
│    - 에이전트 성능 평가                              │
│    - 의사결정 검증                                   │
│    - 자동 개선 (수정 PR 생성)                        │
│    - 문서화 자동 갱신                                │
└─────────────────────────────────────────────────────┘
```

---

### 2️⃣ **Knowledge Repository** - 구조화된 지식 베이스

#### OpenAI의 실패: 큰 AGENTS.md 파일
```
문제:
- 컨텍스트 희소 (Context Scarcity)
- 모든 것이 중요 → 아무것도 중요하지 않음
- 빠르게 부실화됨
- 검증 불가능
```

#### 해결책: 기록 시스템으로서의 저장소

```
project_manager/
├── AGENTS.md                    # 목차 (100줄) - 맵 역할
├── ARCHITECTURE.md              # 아키텍처 최상위 맵
│
└── mindvault/                   # 구조화된 지식 베이스
    ├── system/
    │   ├── 01-philosophy.md           # 핵심 철학
    │   ├── 02-architecture.md         # 상세 아키텍처
    │   ├── 03-components.md           # 컴포넌트 설계
    │   └── 04-interfaces.md           # API/인터페이스
    │
    ├── ontology/
    │   ├── 01-framework.md            # 온톨로지 프레임워크
    │   ├── 02-research-domain.md      # 도메인 개념
    │   ├── 03-pmbok-mapping.md        # PMBOK 매핑
    │   ├── 04-npd-mapping.md          # NPD 매핑
    │   └── 06-entity-relationships.md # ER 다이어그램
    │
    ├── decisions/
    │   ├── adr-0001.md               # 아키텍처 의사결정 기록
    │   ├── adr-0002.md
    │   └── ...
    │
    ├── research/
    │   ├── pmbok/                     # PMBOK 가이드
    │   ├── npd/                       # NPD 프로세스
    │   ├── benchmarks/                # 경쟁 시스템 분석
    │   └── case-studies/              # 성공/실패 사례
    │
    ├── llm/
    │   ├── 01-model-selection.md      # 모델 선정 기준
    │   ├── 02-base-model-eval.md      # 모델 평가
    │   ├── 03-sft-strategy.md         # 미세조정 계획
    │   └── 04-rag-design.md           # RAG 설계
    │
    ├── implementation/
    │   ├── 01-phase-0-foundation.md
    │   ├── 02-phase-1-core-agent.md
    │   └── ...
    │
    └── tracing/
        ├── 01-tracing-architecture.md # 추적 시스템
        └── 02-evidence-linking.md     # 근거 연결
```

#### 기계적 검증
```yaml
Linter & CI Jobs:
  - 모든 문서가 최신 상태인가?
  - 교차 링크가 올바른가?
  - 구조가 일관성 있는가?
  - 소유권이 명확한가?

Doc-Gardening Agent (정기 실행):
  - 코드 동작과 맞지 않는 문서 감지
  - 수정 PR 자동 생성
  - 오래된 지침 제거 제안
```

---

### 3️⃣ **Agent-First Readability** - 에이전트 우선 가독성

#### 원칙: "에이전트가 볼 수 없는 것은 존재하지 않음"

```
❌ 에이전트가 접근 불가능한 곳:
   - Google Docs / Slack 메시지
   - 사람의 머리 속 지식
   - 외부 도구 (JIRA, Azure DevOps)

✅ 에이전트가 접근 가능한 곳:
   - 리포지터리의 버전 관리 아티팩트
   - 마크다운 문서
   - 코드
   - 구조화된 데이터 (JSON, YAML)
```

#### 코드 설계 원칙

```python
# ❌ BAD: 불투명한 업스트림 의존성
from generic_library import SomeComplexBehavior

# ✅ GOOD: 투명하고 검증 가능한 내부 구현
class ResearchProjectWBS:
    """
    에이전트가 완전히 이해할 수 있는 구현
    - 소스 코드 가독성
    - 100% 테스트 커버리지
    - 명확한 경계
    - 문서화된 의도
    """
    def generate_from_research_plan(self, plan: ResearchPlan) -> WBSStructure:
        # 에이전트가 추론 가능한 로직
        pass
```

#### 관찰 가능성 스택 (Chrome DevTools Protocol 같은 역할)

```
에이전트가 실시간으로 접근할 수 있는 것:

┌────────────────────────────────────┐
│ 프로젝트 상태 모니터링              │
├────────────────────────────────────┤
│ 로그: LogQL 쿼리                    │
│ 메트릭: PromQL 쿼리                 │
│ 추적: 의사결정 추적 로그             │
│ 상태: 실시간 프로젝트 상태           │
└────────────────────────────────────┘

예시:
Agent Query: "이 프로젝트의 리스크 신호가 무엇인가?"
Agent Access: 
  - 실시간 KPI 대시보드 (메트릭)
  - 의사결정 로그 (의도)
  - 프로젝트 상태 (현황)
  → 종합 판단 가능
```

---

### 4️⃣ **Strict Architecture** - 엄격한 아키텍처 강제

#### 문제: 에이전트는 일관성 없이 드리프트할 수 있음

#### 해결책: 기계적 강제와 자동 정리

```
연구 프로젝트 관리 에이전트의 아키텍처:

┌────────────────────────────────────────────────┐
│ Domain: Research Project                       │
├────────────────────────────────────────────────┤
│                                                │
│  Types Layer        (의존성: None)             │
│    ↓                                           │
│  Domain Layer       (의존성: Types)            │
│    ↓                                           │
│  Repository Layer   (의존성: Domain, Types)    │
│    ↓                                           │
│  Service Layer      (의존성: Repository, ...)  │
│    ↓                                           │
│  API Layer          (의존성: Service)          │
│    ↓                                           │
│  UI/Output Layer    (의존성: API)              │
│                                                │
└────────────────────────────────────────────────┘

교차 관심사 (Cross-Cutting):
  - Authentication (Providers를 통해서만)
  - Logging (구조화된 로깅 필수)
  - Tracing (Decision Chain 기록)
  - Feature Flags (명시적 인터페이스)

기계적 강제:
  - Custom Linter: 순환 참조 금지
  - Structural Tests: 계층 경계 검증
  - Type Checker: 모든 의존성 명시
```

#### 구조적 테스트 예시

```typescript
// 아키텍처 규칙 검증
describe('Architecture Rules', () => {
  it('should not have circular dependencies', () => {
    const graph = buildDependencyGraph();
    expect(hasCycles(graph)).toBe(false);
  });

  it('Service should not import UI', () => {
    const imports = analyzeImports('service/');
    expect(imports).not.toContain('ui/');
  });

  it('Repository must use only Domain types', () => {
    const repos = analyzeImports('repository/');
    expect(repos).not.toContain('service/');
  });
});
```

---

### 5️⃣ **Autonomous Improvement Loop** - 자동 개선 루프

#### OpenAI의 "가비지 컬렉션" 접근

```
기존 방식 (실패):
  - 매주 금요일 "AI 슬로프" 정리 (20% 시간)
  - 확장 불가능
  - 수동
  - 일관성 없음

개선된 방식 (성공):
  - "황금 원칙" 인코딩
  - 정기적인 정리 에이전트
  - 편차 자동 감지
  - 수정 PR 자동 생성
  - 자동 병합 (필요시)
```

#### 연구 프로젝트 관리 시스템의 자동 정리

```python
class RepositoryGardeningAgent:
    """
    정기적으로 실행되며 다음을 검증:
    1. 의사결정 기록 (근거 있는가?)
    2. 온톨로지 일관성 (오래되지 않았는가?)
    3. 구현 vs 설계 (갭이 없는가?)
    4. 코드 품질 (메트릭 기준 충족?)
    5. 성과 지표 (정의 명확한가?)
    """
    
    def detect_entropy(self):
        """
        에이전트가 복제한 패턴의 편차 감지
        """
        issues = {
            'outdated_docs': [],
            'inconsistent_patterns': [],
            'missing_evidence': [],
            'architecture_drift': []
        }
        return issues
    
    def create_fix_pr(self, issue):
        """
        자동으로 수정 PR 생성
        1분 이내에 검토 가능한 크기
        """
        pass
    
    def maintain_invariants(self):
        """
        황금 원칙 강제:
        - 공유 유틸리티 선호
        - YOLO 스타일 데이터 탐색 금지
        - 명시적 유형 지정
        """
        pass
```

---

## 🔄 에이전트 자율성 증가 단계

### Phase 1: 기초 기반 (Foundation)
```
에이전트 역할:
  ✓ 입력 분석
  ✓ 의사결정 근거 제시
  ✗ 의사결정 실행 (승인 필요)
  
인간 역할:
  ✓ 모든 주요 의사결정 승인
  ✓ 피드백 제공
  ✓ 환경 설계
```

### Phase 2: 자동화 (Automation)
```
에이전트 역할:
  ✓ WBS 자동 생성
  ✓ Schedule 최적화
  ✓ 리스크 분석
  ✓ PR 자동 검토 및 응답
  
인간 역할:
  ✓ 검증만 수행
  ✓ 예외 상황 처리
```

### Phase 3: 완전 자율 (Full Autonomy)
```
에이전트는 한 번의 프롬프트로:
  1. 연구계획서 분석
  2. 프로젝트 유형 분류
  3. WBS 생성
  4. Schedule 수립
  5. 리소스 계획
  6. 리스크 분석
  7. 성과 지표 정의
  8. 지식 저장소 구축
  9. 실행 계획 수립
  10. 피드백 대응
  11. 자동 개선
  
인간 역할:
  ✓ 중대 의사결정 검증만
  ✓ 방향 조정
```

---

## 📋 구현 체크리스트

### Harness Engineering 설계 완료 기준

- [ ] 온톨로지 시스템 구축
- [ ] 지식 베이스 구조화 (기록 시스템)
- [ ] 에이전트 관찰 가능성 스택 구성
- [ ] 아키텍처 강제 규칙 정의
- [ ] 자동 정리 에이전트 구현
- [ ] 피드백 루프 설계
- [ ] 자율성 단계별 목표 정의
- [ ] 메트릭 및 성공 기준 설정

---

## 🎯 핵심 성공 요소 (Critical Success Factors)

1. **명확한 경계** (Clear Boundaries)
   - 에이전트가 할 수 있는 것 / 없는 것 명시

2. **자동 검증** (Mechanical Enforcement)
   - 규칙은 코드로 구현
   - 인간의 일관성에 의존하지 않음

3. **다중 레이어 피드백** (Multi-Layer Feedback)
   - 로그, 메트릭, 트레이싱
   - 에이전트가 직접 관찰 가능

4. **버전 관리되는 모든 아티팩트** (VCS Everything)
   - 설계, 계획, 코드, 문서 모두
   - 에이전트의 지식 = 리포지터리 내용

5. **점진적 자율성** (Gradual Autonomy)
   - 처음부터 완전 자율은 불가능
   - 단계적 능력 확장
