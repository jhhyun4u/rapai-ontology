# RAPai 데이터 설계 명세서 v2.1

> **문서 정보**
> - 버전: v2.1
> - 작성일: 2026년 4월 16일
> - 기반: v2.0 + 4개 관점 교차 검토 21건 이슈 반영
> - 연계 문서: RAPai 통합 설계 명세서 v2.9
> - 문서 성격: 데이터 아키텍처 설계서 — 대외비 (TENOPA 내부용)

## v2.1 변경 내역 (v2.0 대비)

| 구분 | 내용 | 이슈 번호 |
|------|------|-----------|
| **신규 테이블** | `outbox` — 분산 트랜잭션 Outbox Pattern | C-2, C-5 |
| **신규 테이블** | `report_tags` — 태그 레지스트리 참조 테이블 | C-1 |
| **신규 테이블** | `access_control_policies` — ABAC 규칙 저장 | C-6 |
| **신규 테이블** | `system_audit_logs` — pg_audit 대상 상세 정책 | M-4 |
| **필드 추가** | `users.password_hash` · `users.mfa_secret` | C-6b |
| **필드 추가** | `gate_decisions.decision` CHECK CONSTRAINT | H-5 |
| **필드 추가** | `projects.active_gate_layers` NULL 가드 | H-6 |
| **필드 추가** | `agent_logs.retry_count` · `failed_reason` | C-4 |
| **필드 추가** | `daily_reports.is_offline` · `server_version` | C-2 |
| **필드 추가** | `notifications.escalation_level` (기존 확인) | H-11 |
| **Soft Delete** | 핵심 테이블 `is_archived` · `archived_at` 추가 | H-9 |
| **이벤트 추가** | `TASK_DONE` · `COST_INCURRED` · `PROJECT_CLOSE` | H-11 |
| **platform_metrics** | 집계 주기·담당 에이전트 명시 | M-5 |

---

## 0. 설계 원칙

### 0.1 4개 저장소 역할 분리

| 저장소 | 역할 | 변경 가능성 | 핵심 특성 |
|--------|------|------------|-----------|
| PostgreSQL 16 | SSOT DB — 현재 상태·운영·설정 데이터 | Mutable | 단일 진실 소스. 설정/참조 테이블 포함. pg_audit 감사. 수치 생성 금지. |
| Neo4j | MindVault — 불변 맥락·결정 이력 | Append-only | 법적 원본. Gate·TRL·CRL·학습·Override 이력 영구 보존. |
| Redis | 캐시·큐·세션 — 실시간 처리 | Ephemeral (TTL) | GraphState 캐시. 일일보고 큐. 분산 락. |
| Qdrant | 벡터 DB — 의미 검색·패턴 학습 | Append | INSIGHT 선례. Gate 패턴. 유사 과제. |

### 0.2 6대 핵심 설계 결정 (v2.1 추가: Outbox Pattern)

> **원칙 1** — 수치는 PostgreSQL에서만 생성: AI 에이전트는 수치를 생성하지 않음. SPI·CPI·달성률 = SSOT DB 직접 추출·계산.
>
> **원칙 2** — project_id가 모든 데이터의 파티션 키: 전 테이블 project_id 포함. SaaS 전환 시 tenant_id 추가만으로 격리 완성.
>
> **원칙 3** — 법적 원본은 Neo4j: GATE_DECISION·TRL_SNAPSHOT·CRL_SNAPSHOT·OVERRIDE_DECISION의 법적 원본 = Neo4j. PostgreSQL은 조회 편의용 사본.
>
> **원칙 4** — Redis는 영속 데이터 불보장: 모든 Redis 키는 TTL 보유. Redis 장애 시 PostgreSQL·Neo4j로 재구성 가능.
>
> **원칙 5** — 보안 등급별 암호화 분리: 일반(평문) / 주의(AES-256) / 보호(온프레미스+별도키) / 비밀(HSM).
>
> **원칙 6 (v2.1 신규)** — Outbox Pattern으로 분산 트랜잭션 보장: PostgreSQL에 먼저 쓰고 outbox 테이블을 통해 Neo4j·Redis에 전파. PostgreSQL ACID가 단일 진실 소스를 보장.

### 0.3 PostgreSQL 전체 테이블 목록 (v2.1 — 31개)

| # | 테이블명 | 분류 | 역할 |
|---|----------|------|------|
| 1 | users | 사용자 | 다중 역할·보안등급·인증(password_hash v2.1) |
| 2 | projects | 과제 | 6유형·생명주기·포트폴리오·is_archived |
| 3 | programs | 포트폴리오 | 프로그램 묶음 |
| 4 | portfolios | 포트폴리오 | 전략 연계 |
| 5 | project_members | 과제 | 투입률·과부하 지수 (Generated) |
| 6 | wbs_tasks | 과제 | Task 10단계·선행관계·EXPERIMENT_LOOP·is_archived |
| 7 | task_threads | 커뮤니케이션 | PM 업무지시·NEGOTIATING 협의 |
| 8 | daily_reports | 보고 | 일일보고·3-way파싱·is_offline(v2.1) |
| 9 | kpi_baselines | KPI | KPI 3계층 목표 |
| 10 | kpi_actuals | KPI | SPI·EVM 실적 시계열 |
| 11 | budget_items | 예산 | 비목별 예산·집행·잔액(Generated)·is_archived |
| 12 | gate_criteria | Gate | Must·Should 기준 버전관리 |
| 13 | gate_decisions | Gate | 결정 조회용 사본 (CHECK CONSTRAINT v2.1) |
| 14 | risks | 위험 | 위험 레지스트리·VUCA |
| 15 | external_signals | AG-SENSE | 외부 환경 신호 |
| 16 | ip_signals | AG-IP | IP·특허 신호 |
| 17 | attachments | 파일 | TRL·CRL·ELN 근거 첨부 메타데이터 |
| 18 | generated_reports | 보고서 | AG-REPORT 자동 생성 보고서 |
| 19 | requirements | 요구사항 | RFP 파싱 결과 (유형3·4·5) |
| 20 | notifications | 알람 | 경보 발송 이력·SLA·에스컬레이션 |
| 21 | agent_logs | 에이전트 | 처리 이력·오탐·재시도(v2.1) |
| 22 | platform_metrics | ROI | 집계 주기·담당 에이전트 명시(v2.1) |
| 23 | spi_alert_thresholds | 설정 | 유형별 SPI 경보 임계값 |
| 24 | trl_stage_config | 설정 | TRL 9단계 설정 |
| 24b | crl_stage_config | 설정 | CRL 9단계 설정 |
| 25 | gate_criteria_templates | 설정 | 유형별 Gate 기준 템플릿 |
| 26 | project_type_configs | 설정 | 6유형별 활성 Gate·파라미터 |
| 27 | team_competency_profiles | AG-TEAM | 팀원 역량·이탈 위험 |
| 28 | agent_threshold_configs | AG-QA | 에이전트 임계값 |
| 29 | learning_cycle_records | AG-QA | 자가학습 사이클 이력 |
| **30** | **outbox** | **분산 트랜잭션** | **Outbox Pattern (v2.1 신규)** |
| **31** | **report_tags** | **참조** | **태그 레지스트리 (v2.1 신규)** |

---

## 1. 핵심 운영 테이블 상세 스키마

### 1.1 users (v2.1 보완: password_hash·mfa_secret 추가)

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| id | UUID | PK · DEFAULT gen_random_uuid() | |
| name | VARCHAR(100) | NOT NULL | 실명. |
| email | VARCHAR(200) | UNIQUE · NOT NULL | 조직 이메일. |
| teams_aad_id | VARCHAR(200) | UNIQUE · NULLABLE | Azure AD ID. |
| org_roles | VARCHAR(50)[] | NOT NULL · DEFAULT ARRAY['연구원'] | 역할 배열. 이중 역할 지원. |
| primary_role | VARCHAR(50) | NOT NULL · DEFAULT '연구원' | 활성 역할. PM/연구원/PI/기관관리자/oversight_manager |
| security_level | VARCHAR(20) | NOT NULL · DEFAULT '일반' | 일반/주의/보호/비밀. |
| is_active | BOOLEAN | NOT NULL · DEFAULT true | |
| push_token | TEXT | NULLABLE | Web Push 구독 토큰. |
| **password_hash** | **VARCHAR(255)** | **NULLABLE** | **SSO 장애 시 비상 로컬 로그인용. bcrypt 해시. NULL = SSO 전용 계정.** |
| **mfa_secret** | **VARCHAR(100)** | **NULLABLE** | **TOTP MFA 시크릿. 보호·비밀 등급 과제 접근 시 강제 적용.** |
| created_at | TIMESTAMPTZ | NOT NULL · DEFAULT now() | |
| last_login_at | TIMESTAMPTZ | NULLABLE | AG-TEAM 이탈 감지 활용. |

### 1.2 projects (v2.1 보완: is_archived 추가)

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| id | UUID | PK | |
| name | VARCHAR(200) | NOT NULL | |
| project_type | VARCHAR(50) | NOT NULL | basic_research/tech_rd/policy_research/roadmap_isp/management_consulting/hybrid |
| project_mode | VARCHAR(30) | NOT NULL | trl_driven/deliverable_driven/hybrid_mode |
| report_type | VARCHAR(10) | NOT NULL · DEFAULT 'B' | A/B/C/D. AG-REPORT 엔진 선택 기준. |
| security_level | VARCHAR(20) | NOT NULL | |
| lifecycle_status | VARCHAR(30) | NOT NULL · DEFAULT 'planning' | planning/active/gate_hold/pivot/completed/killed |
| active_gate_layers | VARCHAR(20)[] | NOT NULL · DEFAULT ARRAY[]::VARCHAR[] | 활성 Gate 계층. 착수 시 project_type_configs에서 자동 설정. **NULL 불허** (빈 배열로 초기화). |
| trl_target | SMALLINT | NULLABLE | 유형1·2만. 유형3·4·5는 NULL 허용. **NULL 시 TRL 관련 Gate Must 로직 스킵.** |
| trl_current | SMALLINT | NULLABLE · DEFAULT 0 | |
| crl_target | SMALLINT | NULLABLE | 유형1·2만. **NULL 시 CRL 관련 Gate Must 로직 스킵.** |
| crl_current | SMALLINT | NULLABLE · DEFAULT 0 | Valley of Death 감지 기준. |
| rd_zone | VARCHAR(30) | NULLABLE | exploration/valley_of_death/growth/maturity |
| current_stage | SMALLINT | NOT NULL · DEFAULT 0 | |
| strategic_goal_id | VARCHAR(100) | NULLABLE | |
| portfolio_id | UUID | NULLABLE · FK → portfolios.id | |
| program_id | UUID | NULLABLE · FK → programs.id | |
| complexity_level | VARCHAR(20) | NOT NULL · DEFAULT 'medium' | low/medium/high/very_high |
| vuca_profile | JSONB | NULLABLE | |
| start_date | DATE | NOT NULL | |
| end_date | DATE | NOT NULL | |
| pi_id | UUID | NOT NULL · FK → users.id | |
| pm_id | UUID | NULLABLE · FK → users.id | |
| **is_archived** | **BOOLEAN** | **NOT NULL · DEFAULT false** | **소프트 삭제·아카이브 여부. 과제 종료 후 5년 경과 시 true.** |
| **archived_at** | **TIMESTAMPTZ** | **NULLABLE** | **아카이브 처리 일시.** |
| created_at | TIMESTAMPTZ | NOT NULL · DEFAULT now() | |

> **NULL 가드 원칙 (이슈 H-6 해소)**: `trl_target`·`crl_target`이 NULL인 유형3·4·5 과제에서 Gate Must 판단 시, 에이전트는 `project_type_configs.active_gate_layers`를 확인하여 L1 Gate가 비활성인 경우 TRL/CRL 관련 Must 조건을 자동 스킵합니다.

### 1.3 programs / 1.4 portfolios (v2.0 유지)

### 1.5 project_members (v2.0 유지)

### 1.6 wbs_tasks (v2.1 보완: is_archived 추가)

v2.0 필드 전체 유지 + 아래 추가:

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| **is_archived** | **BOOLEAN** | **NOT NULL · DEFAULT false** | **과제 종료 후 5년 경과 시 아카이브.** |
| **archived_at** | **TIMESTAMPTZ** | **NULLABLE** | |

### 1.7 task_threads (v2.0 유지)

### 1.8 daily_reports (v2.1 보완: 오프라인 필드 추가)

v2.0 필드 전체 유지 + 아래 추가:

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| **is_offline** | **BOOLEAN** | **NOT NULL · DEFAULT false** | **PWA 오프라인 작성 후 동기화 여부.** |
| **server_version** | **JSONB** | **NULLABLE** | **오프라인 동기화 시 서버 현재 상태 스냅샷. 충돌 감지에 사용.** |
| **conflict_type** | **VARCHAR(50)** | **NULLABLE** | **충돌 유형. task_reassigned / duplicate_done / project_closed / none** |
| **is_archived** | **BOOLEAN** | **NOT NULL · DEFAULT false** | |
| **archived_at** | **TIMESTAMPTZ** | **NULLABLE** | |

### 1.9~1.11 kpi_baselines / kpi_actuals / budget_items

v2.0 유지. `budget_items`에 `is_archived BOOLEAN DEFAULT false`, `archived_at TIMESTAMPTZ` 추가.

### 1.12 gate_criteria (v2.0 유지)

### 1.13 gate_decisions (v2.1 보완: CHECK CONSTRAINT + insight_node_id)

v2.0 필드 전체 유지 + 아래 변경:

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| decision | VARCHAR(30) | NOT NULL · **CHECK (decision IN ('Go','Kill','Hold','Recycle','조건부Go','통과','미달','계속','조정','중단','유지','Pivot','가속'))** | **v2.1: CHECK CONSTRAINT 추가. 허용값 외 입력 차단.** |
| gate_type | VARCHAR(30) | NULLABLE | L2 전용: technical/quality/milestone |
| insight_node_id | VARCHAR(100) | NULLABLE | Kill·Pivot 후 Neo4j INSIGHT 노드 ID |
| mindvault_node_id | VARCHAR(100) | NOT NULL | Neo4j GATE_DECISION 노드 ID |

### 1.14 risks / 1.15 external_signals / 1.16 ip_signals (v2.0 유지)

### 1.17 attachments (v2.0 유지)

### 1.18 generated_reports (v2.0 유지)

### 1.19 requirements (v2.0 유지)

### 1.20 notifications (v2.0 유지 — escalation_level 포함 확인)

escalation_level SMALLINT NOT NULL DEFAULT 0 확인됨.
- 0 = 초기 발송
- 1 = PM → PI 상향 (SLA 초과 시 자동)
- 2 = PI → 기관관리자 상향

### 1.21 agent_logs (v2.1 보완: 재시도 필드 추가)

v2.0 필드 전체 유지 + 아래 추가:

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| **retry_count** | **SMALLINT** | **NOT NULL · DEFAULT 0** | **현재 재시도 횟수.** |
| **max_retries** | **SMALLINT** | **NOT NULL · DEFAULT 3** | **최대 재시도 횟수. 에이전트별 상이.** |
| **failed_reason** | **TEXT** | **NULLABLE** | **최종 실패 사유. DLQ 이동 시 기록.** |
| **is_dlq** | **BOOLEAN** | **NOT NULL · DEFAULT false** | **Dead Letter Queue 이동 여부.** |
| learning_cycle_id | UUID | NULLABLE (논리적 FK) | 연결된 LEARNING_CYCLE 노드 ID |

### 1.22 platform_metrics (v2.1 보완: 집계 주체·주기 명시)

v2.0 필드 전체 유지 + 아래 명시:

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| **aggregated_by** | **VARCHAR(30)** | **NOT NULL · DEFAULT 'AG-QA'** | **집계 담당 에이전트. AG-QA가 주관.** |
| **aggregation_schedule** | **VARCHAR(50)** | **NOT NULL · DEFAULT 'weekly'** | **집계 주기. daily/weekly/monthly/quarterly** |

> **집계 정책**: AG-QA가 Celery Beat로 주기적 집계를 실행. 집계 실패 시 `agent_logs`에 기록 + oversight_manager 알림. 집계 결과는 덮어쓰지 않고 period_start/period_end로 새 행 추가.

---

## 2. 설정·참조 테이블

### 2.1 spi_alert_thresholds (v2.0 유지)

### 2.2 trl_stage_config (v2.0 유지)

### 2.2b crl_stage_config (v2.0 유지)

### 2.3 gate_criteria_templates (v2.0 유지)

### 2.4 project_type_configs (v2.0 유지)

### 2.5 report_tags — 태그 레지스트리 (v2.1 신규) ← 이슈 C-1 해소

> **설계 배경**: v2.8에 `[DONE][ISSUE][TRL_UP]` 등 태그가 사용됐지만 DB에 허용 태그 목록이 없었습니다. `parsed_tags JSONB` 구조에서 어떤 태그가 유효한지 참조할 테이블이 필요합니다.

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| id | UUID | PK | |
| tag_code | VARCHAR(30) | NOT NULL · UNIQUE | `[DONE]`, `[ISSUE]`, `[TRL_UP]`, `[CRL_UP]`, `[TIME]`, `[COST]`, `[IP]`, `[ASSIGN]`, `[DELIVERABLE]`, `[EXPERIMENT]`, `[MGT]`, `[DO]`, `[REV]` |
| display_name | VARCHAR(50) | NOT NULL | 화면 표시명. |
| category | VARCHAR(30) | NOT NULL | 진도/위험/TRL/CRL/투입/예산/IP/업무지시/산출물/실험/PM분류 |
| workflow_trigger | VARCHAR(100) | NULLABLE | 발동 워크플로. 예: `AG-SCHED:TASK_DONE` |
| allowed_roles | VARCHAR(50)[] | NOT NULL | 사용 허용 역할 목록. |
| requires_attachment | BOOLEAN | NOT NULL · DEFAULT false | 파일 첨부 필수 여부. `[TRL_UP]`, `[CRL_UP]` = true. |
| description | TEXT | NULLABLE | 태그 설명. |
| is_active | BOOLEAN | NOT NULL · DEFAULT true | 비활성 태그는 AI 파싱에서 unknown으로 처리. |

**기본 데이터 (13개 태그)**

| tag_code | category | allowed_roles | requires_attachment |
|----------|----------|---------------|---------------------|
| `[DONE]` | 진도 | 연구원,PM,PI | false |
| `[ISSUE]` | 위험 | 연구원,PM,PI | false |
| `[TRL_UP]` | TRL | 연구원,PM | **true** |
| `[CRL_UP]` | CRL | PM | **true** |
| `[TIME]` | 투입 | 연구원,PM,PI | false |
| `[COST]` | 예산 | 연구원,PM | false |
| `[IP]` | IP | 연구원,PM | false |
| `[ASSIGN]` | 업무지시 | PM | false |
| `[DELIVERABLE]` | 산출물 | 연구원,PM | false |
| `[EXPERIMENT]` | 실험 | 연구원 | false |
| `[MGT]` | PM분류 | PM | false |
| `[DO]` | PM분류 | PM | false |
| `[REV]` | PM분류 | PM | false |

---

## 3. 에이전트 운영 데이터 테이블

### 3.1 team_competency_profiles (v2.0 유지)

### 3.2 agent_threshold_configs (v2.0 유지)

### 3.3 learning_cycle_records (v2.0 유지)

---

## 4. Neo4j MindVault — 완전 정의

### 4.1 설계 원칙 (v2.0 유지)

### 4.2 노드 완전 목록 (14개)

v2.0과 동일. `:CRL_SNAPSHOT` 포함.

| 노드 타입 | 핵심 속성 | 생성 조건 | v2.1 변경 |
|-----------|-----------|-----------|-----------|
| :EVENT | event_id·project_id·author_id·channel·raw_text·parsed·gate_impact | 일일보고 Layer 4 | `is_offline`, `conflict_type` 속성 추가 |
| :TRL_SNAPSHOT | snapshot_id·project_id·trl_from·trl_to·evidence[]·pi_signature·signed_at·mindvault_hash | TRL_ACHIEVED + PI 서명 | 변경 없음 |
| :CRL_SNAPSHOT | snapshot_id·project_id·crl_from·crl_to·evidence[]·approver_signature·approver_role·signed_at·mindvault_hash | CRL_UP + 서명 | 변경 없음 |
| :GATE_DECISION | decision_id·project_id·gate_layer·gate_type·decision·rationale·should_score·must_results·decided_by·decided_at·signature_hash | Gate 결정 PI 서명 | `gate_type` 필드 (technical/quality/milestone) |
| :GATE_CRITERIA | criteria_id·project_id·gate_layer·criteria_content·version·approved_by | 착수·기준 변경 | 변경 없음 |
| :KPI_RECONFIG | reconfig_id·project_id·old_kpis·new_kpis·reason | TRL 전환·L4 Pivot | 변경 없음 |
| :VALIDITY_REVIEW | review_id·project_id·trigger_signal·market_score·tech_score·policy_score·investment_score·total_score·options[]·decided_option | L4 Gate 발동 | 변경 없음 |
| :TAILORING_DECISION | tailoring_id·project_id·project_type·lifecycle_template·gate_layers[]·selection_rationale·approved_by | 착수·project_type 변경 | 변경 없음 |
| :OUTCOME_SNAPSHOT | snapshot_id·project_id·review_year·output_results·outcome_results·value_results·snapshot_date | TRACKING_REVIEW | 변경 없음 |
| :LEARNING_CYCLE | cycle_id·agent_id·learning_layer·trigger_type·evidence_count·param_before·param_after·simulated_improvement·approved_by·deployed_at·rollback_params | 자가학습 완료 | 변경 없음 |
| :OVERRIDE_DECISION | override_id·project_id·target_type·target_node_id·override_reason·overridden_by·original_value·corrected_value | Human Override | 변경 없음 |
| :INSIGHT | insight_id·project_id·trigger_type·content·lessons_learned·next_recommendations·retrospective_context | Gate Kill·Pivot·Retrospective | `trigger_type` 구분 |
| :DELIVERABLE | deliverable_id·project_id·name·type·completion_rate·client_approved·submitted_at | 산출물 납품 | 변경 없음 |
| :CLIENT_FEEDBACK | feedback_id·project_id·deliverable_id·feedback_content·satisfaction_score·action_required | 발주처 검토 | 변경 없음 |

### 4.3 관계 유형 (9개, v2.0 유지)

TRIGGERS · CAUSED_BY · CORRECTS · FEEDS_INTO · SUPERSEDES · INFORMS · PRODUCES · SUBMITTED_TO · RETROSPECTIVE_YIELDS

### 4.4 핵심 그래프 쿼리 (v2.0 유지)

---

## 4b. 이벤트 레지스트리 — PostgreSQL events 테이블

### 4b.1 events 테이블 스키마 (v2.0 유지)

### 4b.2 이벤트 유형 목록 (v2.1 — 누락 이벤트 추가) ← 이슈 H-11 해소

| 이벤트 유형 | 발동 조건 | 담당 에이전트 | 처리 결과 |
|-------------|-----------|---------------|-----------|
| TRL_ACHIEVED | TRL_UP 태그 + PI 서명 | AG-KPI → AG-SCOPE | TRL_SNAPSHOT 생성 · KPI_RECONFIG |
| CRL_UP_REPORTED | `[CRL_UP]` 태그 + 서명 | AG-KPI → crl_stage_config 참조 | CRL_SNAPSHOT 생성 · crl_current 갱신 |
| CRL_LAGGING | TRL≥5 AND CRL≤3 | AG-KPI → AG-CHANGE → AG-INT | Valley of Death L4 즉시 발동 |
| GATE_REVIEW | Stage 완료 결정 | AG-INT (전체 병렬) | GATE_DECISION(L2) · WBS 확정 |
| GATE_DECISION_RECORDED | Gate 결정 PI 서명 | AG-INT · outbox → Neo4j | GATE_DECISION 노드 생성 |
| ANNUAL_REVIEW_DUE | 회계연도 D-30 | AG-KPI · AG-REPORT | L3 평가 패키지 자동 조립 |
| EXTERNAL_SIGNAL_CRITICAL | AG-SENSE CRITICAL 감지 | AG-SENSE → AG-KPI | L4 유효성 평가 · PI 72h SLA |
| SCOPE_CHANGE | 범위 변경 요청 | AG-SCOPE → AG-INT(CCB) | CCB 승인 후 L2 기준 재검토 |
| DELIVERABLE_SUBMITTED | 산출물 납품 이벤트 | AG-REPORT · AG-STAKE | 납품 패키지 · 발주처 검토 요청 |
| PROJECT_TYPE_TRANSITION | project_type 변경 | AG-INT | TAILORING_DECISION · 파라미터 재설정 |
| TRACKING_REVIEW | 과제 종료 후 1·3·5년 | AG-KPI · AG-REPORT | OUTCOME_SNAPSHOT · 추적평가 초안 |
| RETROSPECTIVE_DUE | Stage 완료 직후 자동 | AG-TEAM · AG-INT | Retrospective Task 자동 등록 |
| TEAM_OVERLOAD | 투입률 > 120% | AG-TEAM · AG-CHANGE | 과부하 경보 · 재배치 초안 |
| TEAM_CHANGE | 팀원 합류·이탈 | AG-TEAM · AG-SCOPE | 역할 공백 감지 · WBS 영향 분석 |
| INSIGHT_GENERATED | Gate Kill·Pivot 직후 자동 | AG-INT · MindVault | INSIGHT 노드 생성 · 학습 입력 요청 |
| DAILY_REPORT_SUBMITTED | 일일보고 Layer 1 수신 | AG-INT (이중 분기) | Human 흐름 + Agent 흐름 동시 |
| **TASK_DONE** | **wbs_tasks.status = 'DONE' 갱신** | **AG-SCHED · AG-KPI** | **SPI 갱신 · Gate 준비도 재계산 · 진도 알림** |
| **COST_INCURRED** | **`[COST]` 태그 파싱 후 비용 기록** | **AG-BUDGET** | **budget_items.spent_amount 갱신 · 잔액 경보** |
| **PROJECT_CLOSE** | **lifecycle_status = 'completed' 또는 'killed'** | **AG-INT · AG-REPORT · MindVault** | **과제 종료 정산 패키지 · L2 최종 Gate · MindVault 아카이브 처리** |

---

## 5. Redis · Qdrant · GraphState

### 5.1 Redis 키 패턴 (v2.1 — 알람 일관성 보완) ← 이슈 M-1 해소

| 키 패턴 | 타입 | TTL | 내용·v2.1 변경 |
|---------|------|-----|----------------|
| report:queue | Stream | 무제한 | 일일보고 수신 큐. DLQ: `report:queue:dlq`. |
| graph_state:{project_id} | Hash | 1시간 | GraphState 실시간 캐시. |
| spi:{project_id} | String | 30분 | SPI + gate_readiness 포함 (v2.1). |
| alert:{user_id} | Sorted Set | 24시간 | **ZCARD 최대 15건 강제. 초과 시 요약 알림으로 묶음. notifications 테이블과 동기화.** |
| session:{user_id} | Hash | 8시간 | org_roles 배열 포함. |
| lock:gate:{project_id} | String | 5분 | Gate 결정 분산 락. |
| offline:{user_id}:{uuid} | String | 7일 | PWA 오프라인 임시 저장. **server_version 필드 포함 (v2.1).** |
| rate_limit:{user_id}:{endpoint} | String | 1분 | API 호출 속도 제한. |
| agent_result:{event_id}:{agent_id} | Hash | 30분 | 에이전트 처리 결과 임시. |
| push_token:{user_id} | String | 30일 | Web Push 토큰. |

> **알람 피로 방지 통일 원칙 (v2.1)**: Redis `alert:{user_id}` Sorted Set은 ZCARD ≤ 15를 코드 레벨에서 강제합니다. 15건 초과 시 새 알람을 추가하는 대신 요약 알람("오늘 15건 이상의 경보가 있습니다")으로 대체합니다. `notifications` 테이블의 `daily_count_for_user` 필드와 동기화하여 두 채널의 제한 기준을 통일합니다.

### 5.2 Qdrant 컬렉션 (v2.0 유지)

### 5.3 GraphState 전체 필드 (v2.1 — gate_readiness 명시)

```python
class RDProjectState(TypedDict):
    # ── 과제 기본 컨텍스트 ──────────────────────────────────────────
    project_id:              str
    project_type:            str        # project_type_configs 참조
    project_mode:            str
    lifecycle_status:        str
    active_gate_layers:      List[str]  # 빈 배열 허용, NULL 불허

    # ── TRL / CRL ──────────────────────────────────────────────────
    trl_target:              Optional[int]   # 유형3·4·5는 None
    trl_current:             Optional[int]
    crl_target:              Optional[int]   # 유형3·4·5는 None
    crl_current:             Optional[int]
    crl_snapshot_ids:        List[str]       # CRL_SNAPSHOT 노드 ID 목록
    rd_zone:                 str
    experiment_loop_counts:  Dict[str, int]  # task_id → 반복 횟수

    # ── Gate 계층 컨텍스트 ──────────────────────────────────────────
    gate_layer:              str
    current_stage:           int
    gate_must_status:        Dict[str, bool]
    gate_should_scores:      Dict[str, float]
    gate_overall_score:      float
    pending_gate_type:       str        # technical/quality/milestone
    annual_review_due:       date
    performance_rate:        float
    l3_grade:                str
    validity_score:          float
    last_l4_trigger:         datetime
    l4_decision:             str
    gate_readiness:          float      # Gate 준비도 %. v2.1: API 응답에 포함

    # ── SPI 경보 임계값 (spi_alert_thresholds 캐시) ─────────────────
    spi_thresholds:          dict       # {critical:0.70, high:0.75, ...}

    # ── KPI 3계층 ───────────────────────────────────────────────────
    kpi_layer:               str
    output_kpis:             List[dict]
    outcome_kpis:            List[dict]
    value_kpis:              List[dict]
    tracking_reviews:        List[date]

    # ── 가치 전달 사슬 ──────────────────────────────────────────────
    strategic_goal_id:       Optional[str]
    program_id:              Optional[str]
    portfolio_id:            Optional[str]

    # ── 불확실성·복잡성 ─────────────────────────────────────────────
    complexity_level:        str
    vuca_profile:            dict

    # ── 팀 관리 ─────────────────────────────────────────────────────
    team_profiles:           List[dict]
    retrospective_due:       Optional[date]

    # ── AG-QA 모니터링 ──────────────────────────────────────────────
    qa_monitor:              dict
    agent_thresholds:        dict       # agent_threshold_configs 캐시

    # ── 에이전트별 처리 결과 ────────────────────────────────────────
    integration_result:      Optional[dict]   # AG-INT
    scope_result:            Optional[dict]   # AG-SCOPE
    schedule_result:         Optional[dict]   # AG-SCHED
    kpi_result:              Optional[dict]   # AG-KPI
    ip_result:               Optional[dict]   # AG-IP
    change_result:           Optional[dict]   # AG-CHANGE
    sense_result:            Optional[dict]   # AG-SENSE
    budget_result:           Optional[dict]   # AG-BUDGET
    stake_result:            Optional[dict]   # AG-STAKE
    report_result:           Optional[dict]   # AG-REPORT
    team_result:             Optional[dict]   # AG-TEAM
    qa_result:               Optional[dict]   # AG-QA

    # ── 일일보고 처리 컨텍스트 ─────────────────────────────────────
    last_report_id:          Optional[str]
    pending_alerts:          List[dict]
```

---

## 6. 인덱스·파티셔닝·보안

### 6.1 전체 인덱스 목록 (v2.1 추가분)

v2.0 인덱스 전체 유지 + 아래 추가:

| 테이블 | 인덱스 컬럼 | 목적 |
|--------|------------|------|
| outbox | status · created_at (WHERE status='PENDING') | 미처리 Outbox 빠른 스캔 |
| report_tags | tag_code | 태그 코드 조회 |
| daily_reports | is_archived · project_id | 아카이브 제외 조회 |
| projects | is_archived · lifecycle_status | 활성 과제 필터링 |
| wbs_tasks | is_archived · project_id · status | 활성 Task 조회 |
| agent_logs | is_dlq · created_at | DLQ 이동 로그 스캔 |

### 6.2 파티셔닝 전략 (v2.0 유지)

### 6.3 보안 등급별 처리 (v2.0 유지)

### 6.4 pg_audit 감사 정책 (v2.1 신규) ← 이슈 M-4 해소

> **설계 배경**: pg_audit 사용이 언급됐지만 어떤 작업을 어느 수준으로 기록하는지 미정의였습니다.

| 감사 대상 | 감사 수준 | 이유 |
|-----------|-----------|------|
| gate_decisions | DDL + DML (INSERT·UPDATE·SELECT) | 법적 원본. 모든 접근 기록 필수. |
| trl_snapshot (PostgreSQL 사본) | DDL + DML | TRL 달성 근거. 법적 증빙. |
| users | DDL + DML | 권한 변경 추적 필수. |
| agent_threshold_configs | DDL + DML | 임계값 변경 = 시스템 행동 변경. |
| override_decisions | DDL + DML | Human Override 전체 이력. |
| budget_items | DML (UPDATE) | 예산 집행 변경 추적. |
| daily_reports | DML (INSERT) | 보고 원본 등록 이력. |
| 기타 테이블 | DDL만 | 스키마 변경 추적. |

**감사 로그 보존 기간**: gate_decisions·users·override_decisions = 영구. budget_items = 10년. 나머지 = 5년.

**감사 로그 보호**: pg_audit 로그를 별도 감사 전용 DB에 복제. 애플리케이션 계정에서 감사 로그 테이블 접근 금지 (DBA 전용).

---

## 7. 신규 테이블 상세 스키마 (v2.1)

### 7.1 outbox — 분산 트랜잭션 Outbox Pattern ← 이슈 C-2, C-5 해소

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(50) NOT NULL,
    -- 'gate_decision' | 'trl_snapshot' | 'crl_snapshot' | 'event'
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(80) NOT NULL,
    payload         JSONB NOT NULL,
    target_store    VARCHAR(20) NOT NULL,
    -- 'neo4j' | 'redis' | 'both'
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- PENDING | PROCESSING | DONE | FAILED
    retry_count     SMALLINT NOT NULL DEFAULT 0,
    max_retries     SMALLINT NOT NULL DEFAULT 3,
    failed_reason   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX ON outbox (status, created_at) WHERE status = 'PENDING';
CREATE INDEX ON outbox (aggregate_type, aggregate_id);
```

**Outbox Worker 처리 흐름**:

```
Celery Beat (5초 간격):
  SELECT * FROM outbox WHERE status='PENDING' ORDER BY created_at LIMIT 100
  FOR EACH row:
    UPDATE outbox SET status='PROCESSING' WHERE id = row.id
    IF target_store = 'neo4j':
      → Neo4j 노드 생성
    IF target_store = 'redis':
      → Redis 키 갱신
    성공: UPDATE outbox SET status='DONE', processed_at=now()
    실패: retry_count += 1
          IF retry_count >= max_retries:
            UPDATE outbox SET status='FAILED', failed_reason=error
            → oversight_manager CRITICAL 알림 발송
          ELSE:
            UPDATE outbox SET status='PENDING' (재시도 대기)
```

### 7.2 access_control_policies — ABAC 규칙 저장 ← 이슈 C-6 해소

```sql
CREATE TABLE access_control_policies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name     VARCHAR(100) NOT NULL UNIQUE,
    resource_type   VARCHAR(50) NOT NULL,
    -- project | task | report | gate_decision | kpi | budget | admin
    action          VARCHAR(20) NOT NULL,
    -- read | write | sign | delete | admin
    subject_roles   VARCHAR(50)[] NOT NULL,
    -- 허용 역할 목록
    require_membership BOOLEAN NOT NULL DEFAULT true,
    -- project_members 소속 필수 여부
    min_security_clearance VARCHAR(20) NOT NULL DEFAULT '일반',
    -- 최소 보안 등급
    require_internal_network BOOLEAN NOT NULL DEFAULT false,
    -- 내부망 접근 필수 여부 (보호·비밀 등급)
    require_mfa     BOOLEAN NOT NULL DEFAULT false,
    -- MFA 필수 여부
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**기본 정책 데이터 (핵심 5개)**:

| policy_name | resource_type | action | subject_roles | require_membership |
|-------------|---------------|--------|---------------|-------------------|
| gate_decision_sign | gate_decision | sign | PI | true |
| gate_decision_read | gate_decision | read | PM, PI, 기관관리자 | true |
| trl_sign | trl_snapshot | sign | PI | true |
| crl_sign_pm | crl_snapshot | sign | PM (CRL 1~4) | true |
| admin_threshold | agent_threshold_configs | admin | oversight_manager | false |

---

## 8. 데이터 보존·아카이브 정책 (v2.1) ← 이슈 H-9 해소

### 8.1 테이블별 보존 정책

| 테이블 | 보존 기간 | 아카이브 방식 | Hard Delete 허용 |
|--------|-----------|---------------|-----------------|
| gate_decisions | 영구 | — | 불가 |
| trl/crl_snapshot (PostgreSQL 사본) | 영구 | — | 불가 |
| daily_reports | 과제 종료 후 5년 | is_archived = true | 불가 |
| wbs_tasks | 과제 종료 후 5년 | is_archived = true | 불가 |
| kpi_actuals | 과제 종료 후 10년 | 파티션 cold storage | 불가 |
| budget_items | 과제 종료 후 5년 | is_archived = true | 불가 |
| agent_logs | 5년 | 월별 파티션 삭제 | 가능 (5년 후) |
| notifications | 1년 | 월별 파티션 삭제 | 가능 |
| outbox | 처리 완료 후 30일 | — | 가능 (DONE/FAILED) |
| platform_metrics | 3년 | — | 가능 (3년 후) |

### 8.2 아카이브 자동화

```sql
-- PROJECT_CLOSE 이벤트 발생 시 자동 실행 (AG-INT)
-- 과제 종료 후 5년 경과 시 아카이브 처리

CREATE OR REPLACE FUNCTION archive_project_data(pid UUID)
RETURNS void AS $$
BEGIN
    UPDATE daily_reports
    SET is_archived = true, archived_at = now()
    WHERE project_id = pid
      AND submitted_at < now() - INTERVAL '5 years';

    UPDATE wbs_tasks
    SET is_archived = true, archived_at = now()
    WHERE project_id = pid;

    UPDATE projects
    SET is_archived = true, archived_at = now()
    WHERE id = pid
      AND created_at < now() - INTERVAL '5 years';
END;
$$ LANGUAGE plpgsql;

-- 활성 데이터 뷰 (아카이브 자동 제외)
CREATE VIEW v_active_projects AS
    SELECT * FROM projects WHERE is_archived = false;

CREATE VIEW v_active_tasks AS
    SELECT * FROM wbs_tasks WHERE is_archived = false;

CREATE VIEW v_active_reports AS
    SELECT * FROM daily_reports WHERE is_archived = false;
```

---

## 부록. 스키마 마이그레이션 전략 (v2.1 신규) ← 이슈 H-7 해소

### 마이그레이션 도구 및 정책

| 항목 | 결정 사항 |
|------|-----------|
| 마이그레이션 도구 | Alembic (Python · FastAPI와 동일 생태계) |
| 버전 관리 | 순차 버전 번호 (001, 002, ...). Git으로 마이그레이션 파일 관리. |
| Zero-downtime 원칙 | 컬럼 추가·인덱스 생성은 논블로킹. 컬럼 삭제·타입 변경은 2단계 배포. |
| 롤백 정책 | 각 마이그레이션 파일에 downgrade() 함수 필수 작성. |
| 테스트 필수 | 마이그레이션 적용 전 스테이징 환경 검증. pg_dump 복원 테스트 포함. |

**Zero-downtime 컬럼 삭제 2단계**:

```
1단계 배포: 컬럼을 NOT NULL → NULLABLE로 변경. 코드에서 해당 컬럼 참조 제거.
2단계 배포: CONCURRENTLY 옵션으로 컬럼 삭제.
(두 배포 사이에 충분한 검증 기간 확보)
```

**v2.1 마이그레이션 목록**:

| 파일명 | 내용 |
|--------|------|
| 001_add_password_hash_to_users.py | users.password_hash · mfa_secret 추가 |
| 002_add_is_archived_fields.py | projects·wbs_tasks·daily_reports·budget_items에 is_archived·archived_at 추가 |
| 003_gate_decisions_check_constraint.py | gate_decisions.decision CHECK CONSTRAINT 추가 |
| 004_add_offline_fields_to_reports.py | daily_reports.is_offline·server_version·conflict_type 추가 |
| 005_agent_logs_retry_fields.py | agent_logs.retry_count·max_retries·failed_reason·is_dlq 추가 |
| 006_create_outbox_table.py | outbox 테이블 신규 생성 |
| 007_create_report_tags_table.py | report_tags 테이블 신규 생성 + 기본 13개 태그 데이터 삽입 |
| 008_create_access_control_policies.py | access_control_policies 테이블 신규 생성 + 기본 정책 데이터 |
| 009_platform_metrics_aggregation.py | platform_metrics.aggregated_by·aggregation_schedule 추가 |
| 010_create_archive_views.py | v_active_projects·v_active_tasks·v_active_reports 뷰 생성 |
