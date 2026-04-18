# RAPai 통합 개념 설계 명세서 v2.9

> **문서 정보**
> - 버전: v2.9
> - 작성일: 2026년 4월 16일
> - 기반: v2.8 + 4개 관점(이용자·개발자·관리운영자·보안관리자) 교차 검토 21건 이슈 반영
> - 문서 성격: 개념 설계 명세서 — 대외비 (TENOPA 내부용)

## v2.9 주요 변경 사항 (v2.8 대비)

| 구분 | 내용 | 이슈 번호 |
|------|------|-----------|
| **신규 11장** | 일일보고 태그 완전 레지스트리 정의 | C-1 |
| **신규 27장** | 시스템 가용성·SLA·백업·복구 정책 | C-7, H-8 |
| **신규 28장** | ABAC 접근 제어 모델 완전 정의 | C-6 |
| **신규 29장** | API 엔드포인트 핵심 명세 | C-3 |
| **신규 30장** | 분산 트랜잭션·Outbox Pattern 설계 | C-2 |
| **신규 31장** | 에이전트 오류 처리·재시도 정책 | C-4 |
| **11장 보완** | 오프라인 충돌 해소 정책 추가 | C-2 |
| **17장 보완** | CRL 연구원 가시성 정책 추가 | H-3 |
| **NFR 보완** | 시스템 SLA 수치 명시 | C-7 |
| **부록 C 신규** | 데이터 보존·아카이브 정책 | H-9 |

---

## 0. 이해관계자 요구사항 정의

### 0.1 이해관계자 식별

| 이해관계자 | 역할 | Gate 관련 주요 관심사 |
|------------|------|----------------------|
| 연구원·컨설턴트 | 주요 사용자 | Gate 준비 부담 최소화. 근거 자동 수집. 평가 패키지 자동 조립. |
| PM | 주요 사용자 | Gate 종류별 준비사항 명확화. D-14 경보 자동. Gate 패키지 자동 생성. |
| PI | 주요 사용자 | L1·L2 최종 결정권. L3 외부 평가 지원. L4 유효성 판단. |
| 발주처·클라이언트 | 외부 이해관계자 | L2 품질 Gate 승인권. 납기·산출물 품질 관리. |
| 정부·전문기관 | 외부 이해관계자 (L3) | L3 Annual Gate 평가권. 성과목표 달성도·예산 집행 확인. |
| 기관관리자 | 시스템 관리자 | 전체 포트폴리오 Gate 현황. 예산 배분 근거 데이터. |
| Human Oversight Manager | 시스템 감시자 | AG-QA 보고 수신. 에이전트 오작동 정정. 자가학습 승인. |

### 0.2 핵심 기능 요구사항

| ID | 요구사항 | Gate 계층 | 담당 에이전트 |
|----|----------|-----------|---------------|
| FR-G01 | 프로젝트 유형·TRL 단계에 따라 L1~L4 중 적용 가능한 Gate 계층을 자동으로 판단하여 활성화 | L1~L4 | AG-INT · AG-KPI |
| FR-G02 | TRL 달성 시 L1 Gate가 자동 트리거되고, PI 서명 후 TRL_SNAPSHOT이 생성되며 다음 Stage 파라미터가 자동 재설정 | L1 | AG-KPI · AG-SCOPE |
| FR-G03 | Stage 완료 시 AG-INT가 Must·Should·Could 기준으로 L2 Gate 판단 패키지를 자동 조립하고 PI에게 Go/Kill 결정 요청 | L2 | AG-INT |
| FR-G04 | 정부R&D 과제의 L3 연차·단계 평가 시점이 되면 성과목표 달성도를 자동 계산하고 제출용 평가 패키지를 자동 조립 | L3 | AG-KPI · AG-REPORT |
| FR-G05 | AG-SENSE가 CRITICAL 신호를 감지하면 L4 Moving Target Gate가 자동 발동되고 PI에게 72h SLA로 대응 옵션 결정 요청 | L4 | AG-SENSE → AG-KPI |

### 0.3 비기능 요구사항

| ID | 요구사항 | 목표값 |
|----|----------|--------|
| NFR-G01 | L1 Gate 트리거 → PI 서명 요청 발송 | TRL_ACHIEVED 이벤트 후 5분 이내 |
| NFR-G02 | L2 Gate 패키지 자동 조립 완료 | Stage 완료 이벤트 후 30분 이내 |
| NFR-G03 | L3 연차·단계 평가 패키지 자동 조립 | 평가 D-14 트리거 후 2시간 이내 |
| NFR-G04 | L4 Moving Target Gate 발동 | CRITICAL 신호 감지 후 5분 이내 |
| NFR-G05 | GATE_DECISION MindVault 기록 | PI 서명 완료 후 즉시 |
| **NFR-A01** | **시스템 가용성** | **99.9% (월간 다운타임 43.8분 이내)** |
| **NFR-A02** | **RTO (Recovery Time Objective)** | **4시간 이내** |
| **NFR-A03** | **RPO (Recovery Point Objective)** | **1시간 이내** |
| NFR-A04 | AI 검증 응답 시간 | Submit 후 3초 이내 |
| NFR-S01 | 보호 등급 이상 데이터 외부 채널 미전송 | 네트워크 차단 + API 키 격리 |
| NFR-S04 | Gate 패키지 원본 보존 | 5년 |

---

## 1. 시스템 정의

### 1.1 한 줄 정의

RAPai(Research AI Platform)는 L1 TRL Gate·L2 Stage Gate·L3 Annual Gate·L4 Moving Target Gate의 4계층 Gate 체계를 자동 운영하고, 프로젝트 유형(6종)과 TRL·CRL 단계를 동시에 인식하여 관리 프레임워크를 자동 전환하며, PMBOK 기반 13개 도메인 에이전트가 LangGraph StateGraph로 협업하는 R&D·학술용역 통합 프로젝트 관리 플랫폼입니다.

### 1.2 설계 원칙

> **v2.5 핵심 설계 원칙**
>
> 원칙 1 — Gate는 4계층이다: L1(TRL 기술 확인)·L2(투자 Go/Kill)·L3(정부R&D 연차·단계)·L4(Moving Target 유효성)는 서로 다른 목적·주체·주기를 가진 독립 계층이다.
>
> 원칙 2 — TRL과 Gate는 다르다: TRL 달성(L1)은 기술적 사실 확인이며 Go/Kill이 없다. Stage Gate(L2)는 경영적 투자 판단이며 TRL 달성이 L2의 Must 기준 중 하나다.
>
> 원칙 3 — 정부R&D 연차평가(L3)는 L2와 독립: L2는 내부 의사결정(PI·PM), L3는 외부 행정 평가(전문기관·평가위원회). 주기·기준·결정 구조가 모두 다르다.
>
> 원칙 4 — Gate 결정은 인간이 한다: RAPai는 패키지를 조립하고 근거를 제시할 뿐이다. 모든 Gate 최종 결정은 반드시 PI 서명을 요구한다.
>
> 원칙 5 — 유형별 Gate 활성화: 유형1·2에는 L1~L4 전부 활성화. 유형3·4·5에는 L2(품질/마일스톤 Gate)·L3(해당 시)만 활성화. L1·L4는 기술 R&D 전용.

---

## 2. 전체 시스템 아키텍처 (v2.8 유지)

9계층 구조, 비기능 요구사항 등 v2.8 2장 내용 유지.

---

## 3~10장 (v2.8 내용 유지)

프로젝트 생명주기, Gate 4계층 체계, 성공 기준 관리, 연구행정 자율화, 보고서 자동 생성 엔진, 보고서 기술 보호, Moving Target 관리, 이벤트 기반 동적 문서 생성은 v2.8 내용을 그대로 유지합니다.

---

## 11. 일일보고 채널 전략 — 전용 앱 단일 채널 (v2.8) + 보완

### 11.0 채널 전략 확정 배경 (v2.8 유지)

전용 앱(PWA)을 주 채널로 확정. Outlook·Teams는 보조 채널로 유지.

### 11.1 전용 앱 핵심 특성 (v2.8 유지)

### 11.2 일일보고 태그 완전 레지스트리 (v2.9 신규) ← 이슈 C-1 해소

> **설계 배경**: v2.8 곳곳에 태그가 사용됐지만 공식 태그 목록이 없었습니다. 개발자·연구원 모두 사용 가능한 태그를 한 곳에서 확인할 수 없었고, 데이터설계서의 `parsed_tags JSONB` 구조도 허용 태그 유형이 불명확했습니다. v2.9에서 공식 태그 레지스트리를 정의합니다.

#### 11.2.1 태그 완전 목록 (13개)

| 태그 | 분류 | 의미 | 워크플로 트리거 | 사용자 |
|------|------|------|----------------|--------|
| `[DONE]` | 진도 | Task 완료 보고 | AG-SCHED: Task DONE 처리 → SPI 갱신 | 연구원·PM |
| `[ISSUE]` | 위험 | 이슈·위험 보고 | AG-CHANGE: 심각도 평가 → 경보 발동 | 연구원·PM |
| `[TRL_UP]` | TRL | TRL 상승 보고 | AG-KPI: TRL_ACHIEVED 이벤트 → PI 서명 요청 | 연구원·PM |
| `[CRL_UP]` | CRL | CRL 상승 보고 | AG-KPI: CRL_UP_REPORTED 이벤트 → CRL_SNAPSHOT 생성 → 서명 요청 | PM |
| `[TIME]` | 투입 | 투입 시간 기록 | AG-KPI: 투입률 계산 → project_members.actual_rate 갱신 | 연구원·PM |
| `[COST]` | 예산 | 비용 발생 보고 | AG-BUDGET: budget_items.spent_amount 갱신 | 연구원·PM |
| `[IP]` | 지식재산 | IP 신호 보고 | AG-IP: ip_signals 등록 → 특허 검토 요청 | 연구원·PM |
| `[ASSIGN]` | 업무지시 | 팀원에게 업무 지시 | AG-INT: Task ASSIGNED 생성 → 팀원 알림 (PM 전용) | PM |
| `[DELIVERABLE]` | 산출물 | 산출물 납품 보고 | AG-REPORT: DELIVERABLE_SUBMITTED 이벤트 → 납품 패키지 생성 | 연구원·PM |
| `[EXPERIMENT]` | 실험 | 실험 반복 기록 | AG-SCHED: EXPERIMENT_LOOP 카운트 증가 → ELN 연동 | 연구원 |
| `[MGT]` | PM 분류 | PM 관리 행위 | AG-INT: mgt_actions 파싱 → 워크플로 분기 | PM |
| `[DO]` | PM 분류 | PM 실행 행위 | AG-INT: do_actions 파싱 → Task 자가배정 | PM |
| `[REV]` | PM 분류 | PM 검토 행위 | AG-INT: rev_actions 파싱 → 수정 요청 알림 | PM |

#### 11.2.2 태그 사용 규칙

- 하나의 보고에 복수 태그 허용. 예: `[DONE][TIME] Task 2-3 완료. 3시간 소요.`
- `[MGT][DO][REV]`는 PM 전용. 연구원 보고에 포함 시 AI 검증에서 WARN 처리.
- `[TRL_UP]`과 `[CRL_UP]`은 달성 근거 파일 첨부 없으면 AI 검증 BLOCK.
- `[ASSIGN]`은 담당자명과 납기일 포함 필수. 미포함 시 WARN.
- 미정의 태그는 `parsed_tags.unknown[]` 배열에 수집하여 AG-QA가 패턴 분석.

#### 11.2.3 태그 → DB 필드 매핑

| 태그 | PostgreSQL 테이블·필드 | Neo4j 노드 |
|------|----------------------|------------|
| `[DONE]` | wbs_tasks.status = 'DONE', done_at | EVENT |
| `[ISSUE]` | risks (신규 행) | EVENT |
| `[TRL_UP]` | projects.trl_current | TRL_SNAPSHOT |
| `[CRL_UP]` | projects.crl_current | CRL_SNAPSHOT |
| `[TIME]` | project_members.actual_rate | EVENT |
| `[COST]` | budget_items.spent_amount | EVENT |
| `[IP]` | ip_signals (신규 행) | EVENT |
| `[ASSIGN]` | wbs_tasks (신규 행, status=DRAFT) | EVENT |
| `[DELIVERABLE]` | generated_reports | DELIVERABLE |
| `[EXPERIMENT]` | wbs_tasks.experiment_loop_count | EVENT |
| `[MGT]` | daily_reports.mgt_actions | EVENT |
| `[DO]` | daily_reports.do_actions | EVENT |
| `[REV]` | daily_reports.rev_actions | EVENT |

### 11.3 오프라인 충돌 해소 정책 (v2.9 신규) ← 이슈 C-2 해소

> **설계 배경**: Service Worker + IndexedDB로 오프라인 입력이 가능하지만, 오프라인 중 서버 데이터가 변경됐을 경우의 충돌 처리 정책이 없었습니다.

#### 11.3.1 충돌 유형별 처리 정책

| 충돌 유형 | 감지 조건 | 처리 방식 |
|-----------|-----------|-----------|
| **Task 상태 충돌** | 오프라인 [DONE] 보고 후 서버에서 해당 Task 재배정됨 | 서버 버전 우선. 사용자에게 "Task 상태가 변경됐습니다" 알림 후 재확인 요청. |
| **중복 완료 보고** | 동일 Task를 온라인/오프라인에서 이중 DONE 처리 | 최초 완료 처리만 유효. 두 번째는 WARN 표시 후 무시. |
| **project_id 불일치** | 오프라인 중 과제가 종료·삭제됨 | 보고 수신 후 project_id 검증 실패 → DLQ로 이동 → PM에게 확인 알림. |
| **일반 텍스트 보고** | 오프라인 보고가 서버 보고와 내용 중복 가능성 | 충돌 없음으로 처리. 두 보고 모두 EVENT 노드에 저장. |

#### 11.3.2 동기화 처리 흐름

```
오프라인 보고 작성
  → IndexedDB 저장 (offline:{uid}:{uuid} Redis에도 7일 TTL)
  → 네트워크 복구 감지 (Service Worker)
  → POST /api/reports (channel="rapai_app_offline", is_offline=true)
  → Layer 2: server_version 필드로 서버 현재 상태 조회
  → 충돌 감지 시: conflict_type 반환 → 사용자 확인 팝업
  → 사용자 선택 후 최종 제출
```

#### 11.3.3 오프라인 보고 우선순위 규칙

- 서버 버전 우선이 기본값
- 단, `[DONE]` 태그 보고에서 서버가 여전히 IN_PROGRESS인 경우 → 오프라인 보고 우선 (연구원이 직접 수행한 사실 우선)
- `[ISSUE]` 태그는 항상 병합 (두 버전 모두 등록)

### 11.4 데이터 흐름 4계층 파이프라인 (v2.8 유지)

### 11.5 Human 흐름 / Agent 흐름 (v2.8 유지)

---

## 12~16장 (v2.8 내용 유지)

PM 업무지시 Task 생명주기, 에이전트 Gate 계층별 역할, LangGraph StateGraph 설계, MindVault, 알람 우선순위 및 권한 매트릭스 내용은 v2.8을 유지합니다.

---

## 17. TRL·CRL 기반 프로젝트 맥락 관리 (유형1·2 전용)

### 17.1 TRL 9단계 (v2.8 유지)

### 17.2 CRL 9단계 정의 (v2.8 신규)

| CRL | 단계명 | 정의·조건 | 달성 근거 | 확인자 | 연관 TRL |
|-----|--------|-----------|-----------|--------|----------|
| CRL 1 | 시장 문제 인식 | 풀어야 할 시장 문제가 존재함을 문헌·통계로 확인. 잠재 고객 탐색 시작. | 시장 조사 보고서 · 선행 문헌 검토 | PM | TRL 1~2 |
| CRL 2 | 잠재 고객 탐색 | 잠재 고객 5인 이상 인터뷰 완료. 문제 인식 공유 확인. | 잠재 고객 인터뷰 메모 (5건 이상) | PM | TRL 2~3 |
| CRL 3 | 관심 표명 확인 | 잠재 고객이 기술 시연에 관심 표명. 초기 요구사항 수렴 시작. | 미팅 기록 · 관심 표명 서한 | PM | TRL 3~4 |
| CRL 4 | 초기 요구사항 수렴 | 고객 요구사항 목록 작성 완료. 기술 방향과 시장 요구사항 정합성 1차 확인. | 요구사항 정의서 · 고객 확인 서명 | PM | TRL 4 |
| CRL 5 | 고객 PoC 완료 ★전환점 | 잠재 고객 대상 PoC 실행 완료. 고객 피드백 서면 확보. L2 Gate Must 기준. | 고객 PoC 결과 보고서 · 고객 피드백 서면 | PM+PI 공동 | TRL 5 |
| CRL 6 | 파트너십 탐색 | 채널 파트너·투자자·사업화 기관 협의 착수. MOU 또는 LOI 초안 교환. | 파트너십 탐색 보고서 · MOU 초안 | PI | TRL 6 |
| CRL 7 | 구매의향서(LOI) | 공식 구매의향서 또는 파일럿 계약 체결. 사업화 준비도 확인. | LOI 문서 · 파일럿 계약서 | PI | TRL 7 |
| CRL 8 | 파일럿 계약 완료 | 파일럿 공급·고객 검수 완료. 정식 계약 진입 직전. | 파일럿 납품 확인서 · 고객 검수서 | PI | TRL 8 |
| CRL 9 | 정식 계약·반복 구매 | 정식 계약 체결 완료. 초도 매출 발생. 반복 구매 확인. | 정식 계약서 · 매출 실적 증빙 | PI | TRL 9 |

> **CRL 달성 처리 절차**
> 1. 연구원/PM이 일일보고에 `[CRL_UP]` 태그 + CRL 단계 + 달성 근거 보고
> 2. AI 검증 엔진: 달성 근거 파일 첨부 여부 확인 (누락 시 BLOCK)
> 3. CRL 1~4: PM 확인으로 완료. CRL_SNAPSHOT 생성 (PM 서명)
> 4. CRL 5 (전환점): PM+PI 공동 서명 필수. L2 Gate Must 기준 충족 자동 갱신
> 5. CRL 6~9: PI 단독 서명. CRL_SNAPSHOT 생성 → GraphState.crl_current 갱신
> 6. Valley of Death 재감지: 서명 완료 후 AG-KPI가 TRL-CRL 갭 자동 재계산

### 17.2a CRL 연구원 가시성 정책 (v2.9 신규) ← 이슈 H-3 해소

> **설계 배경**: TRL은 연구원 일일보고 화면에서 현재 단계가 보이지만, CRL은 PM/PI 확인 사항이라 연구원이 "내가 수행한 고객 PoC 결과가 CRL에 반영됐는지"를 확인하는 경로가 없었습니다. Valley of Death 위험을 연구원도 인지해야 대응이 가능합니다.

#### 연구원 화면의 CRL 정보 표시 정책

| 정보 | 연구원 표시 여부 | 표시 방식 | 이유 |
|------|----------------|-----------|------|
| 현재 CRL 수준 | ✓ 표시 | 숫자 + 단계명 (예: CRL 4 — 초기 요구사항 수렴) | 자신의 기여가 어느 단계에 있는지 알아야 동기 부여 |
| CRL 목표 | ✓ 표시 | Gate 2 Must 기준 CRL 목표값 표시 | 목표 인지 필요 |
| Valley of Death 경보 | ✓ 표시 | "TRL 5 달성 / CRL 3 — 고객 연결 가속 필요" 배너 | 연구원도 위험 인식 필요 |
| CRL 달성 근거 세부 | ✗ 비표시 | PM/PI 전용 | 고객 정보 포함 가능, 보안 고려 |
| CRL 변경 이력 | ✓ 표시 (읽기 전용) | CRL_SNAPSHOT 날짜·단계만 표시 | 진행 상황 파악 |

#### Gate 준비도 연구원 화면 표시 경로 (이슈 H-4 해소)

```
게이트 준비도 계산 경로:
  AG-KPI → gate_readiness 계산 (규칙 엔진)
    → GraphState.gate_readiness 갱신
    → Redis spi:{project_id} 키에 gate_readiness 포함
  연구원 화면 GET /api/projects/{id}/readiness
    → Redis 캐시 우선 조회 (TTL 30분)
    → 없으면 PostgreSQL kpi_actuals 집계 계산
    → 화면에 "Gate 2 준비도 68%" 표시
```

### 17.3 Valley of Death 자동 감지 (v2.8 유지)

---

## 18~26장 (v2.8 내용 유지)

프로젝트 유형 분류, 구현 로드맵, Gate 거버넌스, KPI 3계층, AG-TEAM, AG-QA, 배포 전략, PMBOK 7판, 전용 앱 아키텍처는 v2.8 내용을 유지합니다.

---

## 27. 시스템 가용성·SLA·백업·복구 정책 (v2.9 신규) ← 이슈 C-7, H-8 해소

> **설계 배경**: NFR-A01이 "달성 기준"으로만 언급되고 실제 수치와 복구 정책이 없었습니다. 국가R&D Gate 결정 시스템의 다운은 PI 서명 SLA(72h)를 위반할 수 있는 심각한 문제입니다.

### 27.1 시스템 SLA

| 항목 | 목표값 | 근거 |
|------|--------|------|
| 가용성 | 99.9% | 월간 다운타임 43.8분 이내 |
| RTO | 4시간 | DB 복구 후 에이전트 재기동 포함 |
| RPO | 1시간 | PostgreSQL WAL 연속 백업 기준 |
| AI 검증 응답 | 3초 이내 (p95) | Submit → BLOCK/WARN/SUGGEST 반환 |
| Gate 패키지 조립 | 30분 이내 | Stage 완료 이벤트 → PI 발송 |
| 푸시 알림 발송 | 1분 이내 | CRITICAL 경보 기준 |

### 27.2 DB별 백업 정책

#### PostgreSQL 16

| 항목 | 정책 |
|------|------|
| WAL 연속 백업 | 실시간 (RPO 1시간 달성 핵심) |
| 전체 백업 | 매일 새벽 2시 (pg_dump) |
| 증분 백업 | 매 4시간 (WAL 아카이브) |
| 백업 보존 | 30일 (일별) + 1년 (주별) + 5년 (월별) |
| 백업 저장소 | 온프레미스 NAS + 암호화 외장 스토리지 (보호 등급 이상) |
| 복구 절차 | PITR (Point-in-Time Recovery) — 1시간 단위 복구 지점 |
| 복구 테스트 | 분기 1회 복구 드릴 (격리 환경에서 실제 복구 검증) |

#### Neo4j Enterprise (MindVault)

| 항목 | 정책 |
|------|------|
| 전체 백업 | 매일 새벽 3시 (neo4j-admin dump) |
| 트랜잭션 로그 | 연속 보존 (Append-only 특성상 손실 최소화) |
| 백업 보존 | 영구 (Gate 결정·TRL 달성 근거는 법적 원본) |
| HA 구성 | Primary-Replica 구조 (읽기 분산) |
| 손상 감지 | 매일 자동 무결성 체크 (neo4j-admin check-consistency) |

#### Redis

| 항목 | 정책 |
|------|------|
| 영속화 방식 | AOF (Append Only File) + RDB 조합 |
| Redis는 캐시 전용 | TTL 만료 = 정상 소멸. 장애 시 PostgreSQL에서 재구성 |
| Sentinel | Primary-Replica 3노드 (자동 Failover) |
| 복구 우선순위 | 낮음 — Redis 없이도 PostgreSQL로 서비스 가능 |

### 27.3 고가용성(HA) 구성

```
[PostgreSQL HA]
  Primary ──────────── Replica 1 (Hot Standby, 읽기 분산)
  │                    Replica 2 (Warm Standby, Failover용)
  └── pgBouncer (커넥션 풀링)
  
[Neo4j HA]
  Primary ──────────── Replica (읽기 전용 쿼리)
  
[Redis Sentinel]
  Master ─── Replica 1
           └── Replica 2
  Sentinel x 3 (쿼럼 자동 Failover)

[LangGraph 에이전트]
  Celery Worker x N (수평 확장)
  Redis Broker (에이전트 큐)
```

### 27.4 장애 시나리오별 대응 절차

| 시나리오 | 탐지 방법 | 대응 절차 | 예상 복구 시간 |
|----------|-----------|-----------|----------------|
| PostgreSQL Primary 장애 | Watchdog 프로세스 헬스체크 실패 | Replica → Primary 자동 승격 (pgBouncer 재연결) | 5분 이내 |
| Neo4j 장애 | AG-INT 연결 오류 3회 이상 | Replica 읽기 전용 모드 전환 + 알림 발송. MindVault 쓰기는 Outbox 큐 대기. | 30분 이내 |
| Redis 장애 | Sentinel 쿼럼 감지 | Sentinel 자동 Failover + GraphState PostgreSQL에서 재구성 | 1분 이내 |
| 에이전트 전체 다운 | Celery Beat 미응답 | 수동 재기동 + DLQ 미처리 이벤트 재처리 | 30분 이내 |
| 전체 시스템 장애 | 외부 모니터링 감지 | DR 사이트 전환 (RTO 4시간) | 4시간 이내 |

---

## 28. ABAC 접근 제어 모델 완전 정의 (v2.9 신규) ← 이슈 C-6 해소

> **설계 배경**: "ABAC 4속성" 언급만 있고 실제 속성·규칙이 없어 구현이 불가능했습니다.

### 28.1 ABAC 4속성 정의

#### 속성 1 — 주체 속성 (Subject Attributes)

| 속성 | 값 | 설명 |
|------|-----|------|
| `role` | PI / PM / 연구원 / RA / 기관관리자 / oversight_manager | users.org_roles 배열 |
| `security_clearance` | 일반 / 주의 / 보호 / 비밀 | users.security_level |
| `project_membership` | [project_id, ...] | project_members 테이블 소속 과제 |
| `primary_role` | PM / 연구원 | 현재 활성 역할 (이중 역할 스위치) |

#### 속성 2 — 자원 속성 (Resource Attributes)

| 속성 | 값 | 설명 |
|------|-----|------|
| `resource_type` | project / task / report / gate_decision / kpi / budget | 접근 대상 유형 |
| `resource_project_id` | UUID | 자원이 속한 과제 |
| `resource_security_level` | 일반 / 주의 / 보호 / 비밀 | 자원의 보안 등급 |
| `resource_owner_id` | UUID | 자원 소유자 (PI/PM) |

#### 속성 3 — 환경 속성 (Environment Attributes)

| 속성 | 값 | 설명 |
|------|-----|------|
| `network_zone` | internal / external | 내부망 / 외부망 |
| `time_of_access` | datetime | 접근 시각 (야간 접근 추가 검증) |
| `device_type` | web / mobile / api | 접근 기기 유형 |

#### 속성 4 — 행위 속성 (Action Attributes)

| 행위 코드 | 의미 |
|-----------|------|
| `read` | 조회 |
| `write` | 생성·수정 |
| `sign` | 전자 서명 (Gate 결정·TRL/CRL 확인) |
| `delete` | 삭제 (soft delete만 허용) |
| `admin` | 시스템 설정 변경 |

### 28.2 접근 제어 규칙 매트릭스

| 자원 | 행위 | 허용 조건 |
|------|------|-----------|
| gate_decisions | read | role ∈ {PM, PI, 기관관리자} AND project_membership 포함 |
| gate_decisions | sign | role = PI AND project_membership 포함 |
| gate_decisions | write | role ∈ {PM, PI} AND project_membership 포함 (패키지 조립만) |
| trl_snapshot | sign | role = PI AND project_membership 포함 |
| crl_snapshot | sign | (role = PM AND crl_level ≤ 4) OR (role = PI AND crl_level ≥ 5) AND project_membership 포함 |
| daily_reports | write | role ∈ {연구원, PM, PI} AND project_membership 포함 |
| budget_items | write | role ∈ {PM, 기관관리자} AND project_membership 포함 |
| agent_threshold_configs | admin | role = oversight_manager |
| override_decisions | write | role = oversight_manager |
| projects (보호 등급) | read | role ∈ {연구원, PM, PI} AND security_clearance ≥ 보호 AND project_membership 포함 |
| 모든 자원 (비밀 등급) | read | security_clearance = 비밀 AND network_zone = internal |

### 28.3 보호 등급 이상 데이터 LLM 전송 차단 (이슈 H-10 해소)

```python
# 에이전트 LLM 호출 전 보안 등급 체크
def get_llm_client(project_security_level: str):
    if project_security_level in ['보호', '비밀']:
        # 로컬 LLM만 허용
        return LocalLLMClient(model='exaone-3.5')
    elif project_security_level == '주의':
        # Claude API RESTRICTED 엔드포인트
        return ClaudeAPIClient(tier='RESTRICTED')
    else:
        # 일반 — Claude API PUBLIC
        return ClaudeAPIClient(tier='PUBLIC')

# 네트워크 레벨 차단 (iptables / 방화벽 규칙)
# 보호·비밀 등급 서버에서 외부 IP (api.anthropic.com 등) 아웃바운드 차단
# 화이트리스트: 내부 LLM 서버 IP만 허용
```

### 28.4 사용자 인증 정책 (이슈 C-6b 해소)

| 시나리오 | 처리 방법 |
|----------|-----------|
| 정상 조직 구성원 | AD/LDAP SSO (SAML 2.0) |
| AD 장애 시 | 로컬 계정 비상 로그인 (users.password_hash 컬럼 추가 필요 → DD v2.1 반영) |
| 외부 협력 연구원 | 별도 로컬 계정 생성 (보안 등급 '일반' 고정) |
| 세션 만료 | 8시간 비활동 시 자동 로그아웃 (Redis session TTL) |
| MFA | 보호·비밀 등급 과제 접근 시 강제 (TOTP) |

---

## 29. API 엔드포인트 핵심 명세 (v2.9 신규) ← 이슈 C-3 해소

> **설계 배경**: POST /api/reports 외에 아무 엔드포인트도 정의되지 않아 개발자가 구현을 시작할 수 없었습니다. 핵심 15개 엔드포인트를 정의합니다. 상세 OpenAPI 명세는 별도 문서로 관리합니다.

### 29.1 인증 헤더 공통 사항

```
Authorization: Bearer {JWT_TOKEN}
X-Security-Level: {일반|주의|보호|비밀}  ← 보안 등급 명시적 전달
Content-Type: application/json
```

### 29.2 핵심 API 목록

#### 일일보고

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| POST | `/api/reports` | 일일보고 제출 (Layer 1 진입) | `{report_id, validation_status, validation_results}` |
| GET | `/api/reports/{id}/validation` | AI 검증 결과 조회 | `{status, BLOCK[], WARN[], SUGGEST[]}` |
| PATCH | `/api/reports/{id}` | 검증 후 수정 재제출 | `{report_id, validation_status}` |

#### 프로젝트·Task

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| GET | `/api/projects/{id}/tasks` | 과제 Task 목록 | Task 배열 |
| PATCH | `/api/tasks/{id}/status` | Task 상태 변경 | `{task_id, new_status}` |
| POST | `/api/tasks/{id}/threads` | Task 스레드 메시지 추가 | `{thread_id}` |
| GET | `/api/projects/{id}/readiness` | Gate 준비도 조회 | `{gate_layer, readiness_pct, must_items[], should_score}` |

#### Gate

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| GET | `/api/projects/{id}/gate-package` | Gate 패키지 조회 | Gate 패키지 전체 |
| POST | `/api/gates/{id}/decision` | Gate 결정 서명 | `{decision_id, mindvault_node_id}` |
| GET | `/api/gates/{id}/decisions` | Gate 결정 이력 | GATE_DECISION 배열 |

#### TRL·CRL

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| GET | `/api/projects/{id}/trl-crl` | TRL/CRL 현황 조회 | `{trl_current, crl_current, gap, vod_risk}` |
| POST | `/api/projects/{id}/trl-snapshot` | TRL_SNAPSHOT 서명 생성 | `{snapshot_id}` |
| POST | `/api/projects/{id}/crl-snapshot` | CRL_SNAPSHOT 서명 생성 | `{snapshot_id}` |

#### 시스템

| Method | Endpoint | 설명 | 응답 |
|--------|----------|------|------|
| GET | `/api/health` | 시스템 헬스체크 | `{status, db_status, agent_status}` |
| GET | `/api/projects/{id}/dashboard` | PM 대시보드 데이터 | 통합 현황 |

### 29.3 오류 응답 표준 형식

```json
{
  "error_code": "VALIDATION_BLOCKED",
  "message": "AI 검증 BLOCK 항목이 있습니다.",
  "details": [
    {"type": "BLOCK", "field": "task_id", "message": "Task 2-3이 이미 DONE 상태입니다."}
  ],
  "request_id": "req_20260416_001"
}
```

---

## 30. 분산 트랜잭션·Outbox Pattern 설계 (v2.9 신규) ← 이슈 C-2, C-4 해소

> **설계 배경**: PostgreSQL ↔ Neo4j ↔ Redis에 걸친 2PC(Two-Phase Commit)는 불가능합니다. Gate 결정 시 두 DB에 동시 쓰기 실패 시 정합성이 깨지는 문제를 Outbox Pattern으로 해결합니다.

### 30.1 Outbox Pattern 적용 원칙

```
원칙: PostgreSQL에 먼저 쓰고, Outbox 테이블을 통해 Neo4j·Redis에 전파
이유: PostgreSQL의 ACID 트랜잭션이 단일 진실 소스 보장
결과: PostgreSQL이 살아있으면 Neo4j·Redis는 eventually consistent
```

### 30.2 outbox 테이블 스키마 (DD v2.1에 추가 예정)

```sql
CREATE TABLE outbox (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type  VARCHAR(50) NOT NULL,  -- 'gate_decision' | 'trl_snapshot' | 'crl_snapshot'
  aggregate_id    UUID NOT NULL,          -- 대상 레코드 ID
  event_type      VARCHAR(80) NOT NULL,   -- 'GATE_DECISION_RECORDED' 등
  payload         JSONB NOT NULL,         -- Neo4j 또는 Redis에 전달할 데이터
  target_store    VARCHAR(20) NOT NULL,   -- 'neo4j' | 'redis' | 'both'
  status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING | PROCESSING | DONE | FAILED
  retry_count     SMALLINT NOT NULL DEFAULT 0,
  max_retries     SMALLINT NOT NULL DEFAULT 3,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at    TIMESTAMPTZ
);
CREATE INDEX ON outbox (status, created_at) WHERE status = 'PENDING';
```

### 30.3 Gate 결정 이중 쓰기 흐름

```
[PI가 Gate 결정 서명]
  │
  ▼ PostgreSQL 트랜잭션 시작
  ① gate_decisions INSERT (status='pending_neo4j')
  ② outbox INSERT (event_type='GATE_DECISION_RECORDED', target='neo4j')
  ③ 트랜잭션 COMMIT
  │
  ▼ Celery Outbox Worker (5초마다 폴링)
  ④ outbox WHERE status='PENDING' SELECT
  ⑤ Neo4j GATE_DECISION 노드 생성
  ⑥ 성공 시: outbox.status='DONE' + gate_decisions.mindvault_node_id 갱신
     실패 시: retry_count+1, 3회 실패 시 status='FAILED' + 관리자 알림
```

### 30.4 에이전트 처리 실패 재시도 정책 (이슈 C-4 해소)

| 실패 유형 | 재시도 횟수 | 재시도 간격 | 최종 실패 처리 |
|-----------|-----------|-----------|----------------|
| AG-KPI SPI 계산 타임아웃 | 3회 | 10초, 30초, 60초 (지수 백오프) | DLQ 이동 + oversight_manager 알림 |
| AG-REPORT 보고서 생성 실패 | 2회 | 60초, 300초 | DRAFT 상태 유지 + PM 알림 |
| AG-SENSE 스캔 실패 | 1회 | 300초 | 로그 기록 후 다음 스캔 주기로 이동 |
| Neo4j 노드 생성 실패 | 5회 | Outbox Worker 5초 간격 | 3회 초과 시 FAILED + 관리자 알림 |
| 이벤트 큐 메시지 처리 실패 | 3회 | Celery 자동 재시도 | DLQ (report:queue:dlq) 이동 |

```
[DLQ 처리 절차]
  1. Celery Beat가 매 1시간 DLQ 모니터링
  2. DLQ 메시지 수 > 10건 시 oversight_manager CRITICAL 알림
  3. 관리자가 수동 검토 후:
     - 재처리 명령: XMOVE dlq → report:queue
     - 폐기 명령: XDEL dlq {id}
  4. 재처리 결과 agent_logs에 기록
```

---

## 31. 에이전트 메시지 스키마 (v2.9 신규) ← 이슈 M-5 해소

> **설계 배경**: AG-INT → 각 에이전트로 이벤트를 라우팅할 때 전달되는 payload 구조가 정의되지 않았습니다.

### 31.1 에이전트 공통 입력 스키마

```python
class AgentInput(TypedDict):
    event_id:       str           # events 테이블 ID
    event_type:     str           # 이벤트 유형
    project_id:     str           # 과제 ID
    project_type:   str           # 6개 유형 중 하나
    report_id:      Optional[str] # 트리거 보고 ID
    trigger_data:   dict          # 이벤트별 페이로드
    graph_state:    dict          # GraphState 서브셋 (에이전트별 필요 필드만)
    security_level: str           # 보안 등급 (LLM 선택에 사용)
    timestamp:      str           # ISO 8601
```

### 31.2 에이전트별 graph_state 서브셋

| 에이전트 | 필요 GraphState 필드 |
|----------|---------------------|
| AG-SCHED | task_ids, current_stage, gate_readiness |
| AG-KPI | trl_current, crl_current, spi_thresholds, output_kpis |
| AG-CHANGE | vuca_profile, rd_zone, risks_summary |
| AG-BUDGET | budget_summary, time_spent_h |
| AG-IP | trl_current, crl_current, ip_signals_recent |
| AG-SENSE | l4_decision, validity_score, complexity_level |
| AG-REPORT | gate_layer, l3_grade, performance_rate, report_type |
| AG-TEAM | team_profiles, retrospective_due |
| AG-QA | qa_monitor, agent_thresholds |

### 31.3 에이전트 공통 출력 스키마

```python
class AgentOutput(TypedDict):
    agent_id:       str           # 에이전트 식별자
    event_id:       str           # 처리한 이벤트 ID
    status:         str           # 'SUCCESS' | 'FAILED' | 'SKIPPED'
    duration_ms:    int           # 처리 시간
    db_mutations:   list[dict]    # PostgreSQL 갱신 항목 목록
    outbox_items:   list[dict]    # Neo4j/Redis 전파 항목 (Outbox 패턴)
    alerts:         list[dict]    # 발동할 경보 목록
    graph_state_updates: dict     # GraphState 갱신 필드
    error:          Optional[str] # 실패 시 오류 메시지
```

---

## 부록 A. 주요 용어 정의 (v2.9 업데이트)

v2.8 부록 A 전체 내용 유지 + 아래 신규 항목 추가:

| 용어 | 정의 |
|------|------|
| **Outbox Pattern** | PostgreSQL에 먼저 쓰고 outbox 테이블을 통해 Neo4j·Redis에 비동기 전파하는 분산 트랜잭션 패턴. 이중 쓰기 정합성 보장. |
| **DLQ (Dead Letter Queue)** | 재시도 횟수 초과 후 최종 실패한 메시지가 이동하는 격리 큐. `report:queue:dlq`. Human 검토 후 수동 재처리 또는 폐기. |
| **ABAC** | Attribute-Based Access Control. 주체·자원·환경·행위 4개 속성 조합으로 접근 권한을 동적으로 결정하는 접근 제어 모델. |
| **Outbox Worker** | outbox 테이블을 5초 간격으로 폴링하여 PENDING 항목을 Neo4j·Redis에 전파하는 Celery 워커. |
| **RTO** | Recovery Time Objective. 장애 발생 후 서비스 복구까지 목표 시간. RAPai = 4시간. |
| **RPO** | Recovery Point Objective. 장애 발생 시 허용 가능한 데이터 손실 시점. RAPai = 1시간. |
| **`[CRL_UP]`** | 일일보고 태그. 연구원/PM이 CRL 상승 사실을 보고할 때 사용. AI 검증 엔진이 달성 근거 첨부 여부 확인. CRL 5 이상은 PM+PI 서명 요청 자동 발동. |

## 부록 B. Gate 의사결정 트리 (v2.8 유지)

## 부록 C. 데이터 보존·아카이브 정책 (v2.9 신규) ← 이슈 H-9 해소

> **설계 배경**: "5년 보존"이 언급됐지만 실제 DB 구현 방법(soft delete, archived_at)이 없었습니다.

### C.1 테이블별 보존 정책

| 테이블 | 보존 기간 | 아카이브 방식 | 삭제 허용 |
|--------|-----------|---------------|-----------|
| gate_decisions | 영구 | — (삭제 불가) | 불가 |
| daily_reports | 과제 종료 후 5년 | is_archived = true + archived_at | 불가 |
| wbs_tasks | 과제 종료 후 5년 | is_archived = true | 불가 |
| kpi_actuals | 과제 종료 후 10년 (국가R&D 추적평가) | 파티션 아카이브 | 불가 |
| budget_items | 과제 종료 후 5년 (국가R&D 회계 기준) | is_archived = true | 불가 |
| agent_logs | 5년 | 월별 파티션 → cold storage | 가능 (5년 후) |
| notifications | 1년 | 월별 파티션 삭제 | 가능 |
| platform_metrics | 3년 | — | 가능 (3년 후) |

### C.2 Soft Delete 구현 (DD v2.1 반영 예정)

다음 테이블에 `is_archived BOOLEAN DEFAULT false`, `archived_at TIMESTAMPTZ` 컬럼 추가:
- `daily_reports`, `wbs_tasks`, `budget_items`, `kpi_baselines`, `projects`

```sql
-- 아카이브 처리 (삭제 대신)
UPDATE daily_reports
SET is_archived = true, archived_at = now()
WHERE project_id = $pid
  AND submitted_at < now() - INTERVAL '5 years';

-- 일반 조회에서 아카이브 제외
CREATE VIEW active_daily_reports AS
SELECT * FROM daily_reports WHERE is_archived = false;
```

### C.3 Neo4j MindVault 보존

Neo4j는 모든 노드 영구 보존 (Append-only 원칙). 물리적 삭제 없음.
과제 종료 후 해당 project_id 노드에 `archived: true` 속성 추가 (탐색 제외용).
