# RAPai 데이터 설계 명세서 v2.0

> **문서 정보**
> - 버전: v2.0
> - 위치: 보완 참조 문서 (v2.1 MD가 "v2.0 유지"로 참조하는 섹션의 원본 상세 내용 포함)
> - 용도: 바이브코딩 시 v2.1.md와 함께 첨부하면 설정 테이블 4개·에이전트 운영 테이블 3개·Neo4j·Redis·Qdrant·GraphState 상세 전체 제공
> - 핵심 참조 섹션: 2장(설정·참조 테이블), 3장(에이전트 운영), 4장(Neo4j MindVault), 5장(Redis·Qdrant·GraphState), 6장(인덱스·파티셔닝·보안)

---

**RAPai 데이터 설계 명세서**

*Data Design Specification v2.0 완결판*

RAPai 통합 설계 명세서 v2.8 전 장(章) 대조 검증

  -------------------- --------------------------------------------------
  버전                 v2.0 완결판 --- v2.8 명세서 전 장 대조 검증 완료

  작성일               2026년 4월 15일

  PostgreSQL 테이블    27개 (crl_stage_config 포함)

  Neo4j 노드           14개 노드(CRL_SNAPSHOT 신규) · 9개 관계 유형

  추가 검증 항목       설정/참조 테이블 4개 · 에이전트 운영 테이블 3개 ·
                       기존 테이블 필드 보완 6건 · Neo4j 관계 완성

  저장소               PostgreSQL 16 · Neo4j Enterprise · Redis · Qdrant
  -------------------- --------------------------------------------------

## 0. 설계 원칙 및 전체 테이블 목록

### 0.1 4개 저장소 역할 분리

  -------------------------------------------------------------------------
  **저장소**      **역할**          **변경        **핵심 특성**
                                    가능성**      
  --------------- ----------------- ------------- -------------------------
  PostgreSQL 16   SSOT DB --- 현재  Mutable       단일 진실 소스. 설정/참조
                  상태·운영·설정                  테이블 포함. pg_audit
                  데이터                          감사. 수치 생성 금지.

  Neo4j           MindVault ---     Append-only   법적 원본.
                  불변 맥락·결정    (삭제·수정    Gate·TRL·학습·Override
                  이력              불가)         이력 영구 보존.

  Redis           캐시·큐·세션 ---  Ephemeral     GraphState 캐시. 일일보고
                  실시간 처리       (TTL)         큐. 분산 락. TTL 만료 =
                                                  소멸.

  Qdrant          벡터 DB --- 의미  Append        INSIGHT 선례. Gate 패턴.
                  검색·패턴 학습                  유사 과제.
  -------------------------------------------------------------------------

### 0.2 PostgreSQL 26개 테이블 전체 목록

  ----------------------------------------------------------------------------------------
  **\#**   **테이블명**               **분류**       **역할·주요 연관 에이전트**
  -------- -------------------------- -------------- -------------------------------------
  1        users                      사용자         다중 역할·보안등급·PWA 푸시 토큰

  2        projects                   과제           6유형·생명주기·포트폴리오 계층·활성
                                                     Gate 배열

  3        programs                   포트폴리오     프로그램 (과제 묶음)

  4        portfolios                 포트폴리오     포트폴리오 (전략 연계)

  5        project_members            과제           투입률·과부하 지수 (Generated)

  6        wbs_tasks                  과제           Task
                                                     10단계·선행관계·실험루프·자가배정

  7        task_threads               커뮤니케이션   PM 업무지시·NEGOTIATING 협의 대화

  8        daily_reports              보고           일일보고 원문·3-way 파싱·AI 검증

  9        kpi_baselines              KPI            KPI 3계층 목표·추적평가 일정

  10       kpi_actuals                KPI            SPI·EVM 실적 시계열

  11       budget_items               예산           비목별 예산·집행·잔액 (Generated)

  12       gate_criteria              Gate           Must·Should 기준 버전관리

  13       gate_decisions             Gate           결정 조회용 사본 (Neo4j 원본)

  14       risks                      위험           위험 레지스트리·VUCA 분류

  15       external_signals           AG-SENSE       외부 환경 신호·L4 발동 이력

  16       ip_signals                 AG-IP          IP·특허 신호

  17       attachments                파일           TRL 근거·ELN·산출물 첨부 메타데이터

  18       generated_reports          보고서         AG-REPORT 자동 생성 보고서 메타·버전

  19       requirements               요구사항       RFP 파싱 결과·충족률 (유형3·4·5)

  20       notifications              알람           경보 발송 이력·SLA·에스컬레이션

  21       agent_logs                 에이전트       처리 이력·오탐·학습 체인

  22       platform_metrics           ROI            플랫폼 ROI 측정 (행정시간·NPS·오탐률)

  23       spi_alert_thresholds       설정           유형별 SPI 경보 임계값
                                                     (CRITICAL/HIGH/MEDIUM)

  24       trl_stage_config           설정           TRL 9단계 달성 근거·관리 모드·Gate
                                                     Must 기준

  25       gate_criteria_templates    설정           유형별 Gate 기준 기본 템플릿

  26       team_competency_profiles   AG-TEAM        팀원 역량 프로파일·이탈 위험 지수
  ----------------------------------------------------------------------------------------

## 1. 핵심 운영 테이블 --- 상세 스키마

### 1.1 users (v2.0 보완: 다중 역할·역할 스위치)

  ----------------------------------------------------------------------------------------------------
  **컬럼명**       **타입**          **제약**              **설명**
  ---------------- ----------------- --------------------- -------------------------------------------
  id               UUID              PK · DEFAULT          
                                     gen_random_uuid()     

  name             VARCHAR(100)      NOT NULL              실명.

  email            VARCHAR(200)      UNIQUE · NOT NULL     조직 이메일.

  teams_aad_id     VARCHAR(200)      UNIQUE · NULLABLE     Azure AD ID.

  org_roles        VARCHAR(50)\[\]   NOT NULL · DEFAULT    역할 배열. PM+연구원 이중 역할 =
                                     ARRAY\[\'연구원\'\]   ARRAY\[\'PM\',\'연구원\'\].

  primary_role     VARCHAR(50)       NOT NULL · DEFAULT    활성 역할. 역할 스위치 시 갱신.
                                     \'연구원\'            PM/연구원/PI/기관관리자/oversight_manager

  security_level   VARCHAR(20)       NOT NULL · DEFAULT    일반/주의/보호/비밀.
                                     \'일반\'              

  is_active        BOOLEAN           NOT NULL · DEFAULT    
                                     true                  

  push_token       TEXT              NULLABLE              Web Push 구독 토큰.

  created_at       TIMESTAMPTZ       NOT NULL · DEFAULT    
                                     now()                 

  last_login_at    TIMESTAMPTZ       NULLABLE              AG-TEAM 이탈 감지 활용.
  ----------------------------------------------------------------------------------------------------

### 1.2 projects (v2.0 보완: active_gate_layers 추가)

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **컬럼명**           **타입**          **제약**                 **설명**
  -------------------- ----------------- ------------------------ ---------------------------------------------------------------------------------------------------
  id                   UUID              PK                       

  name                 VARCHAR(200)      NOT NULL                 

  project_type         VARCHAR(50)       NOT NULL                 basic_research/tech_rd/policy_research/roadmap_isp/management_consulting/hybrid

  project_mode         VARCHAR(30)       NOT NULL                 trl_driven/deliverable_driven/hybrid_mode

  report_type          VARCHAR(10)       NOT NULL · DEFAULT \'B\' A=표준서식/B=자유/C=용역컨설팅/D=정책전략. AG-REPORT 엔진 선택 기준.

  security_level       VARCHAR(20)       NOT NULL                 

  lifecycle_status     VARCHAR(30)       NOT NULL · DEFAULT       planning/active/gate_hold/pivot/completed/killed
                                         \'planning\'             

  active_gate_layers   VARCHAR(20)\[\]   NOT NULL · DEFAULT       활성 Gate 계층 목록. project_type_configs 참조로 자동 설정. GraphState.active_gates와 동기화.
                                         ARRAY\[\]::VARCHAR\[\]   

  trl_target           SMALLINT          NULLABLE                 유형1·2 전용.

  trl_current          SMALLINT          NULLABLE · DEFAULT 0     L1 Gate 서명 후 갱신.

  crl_target           SMALLINT          NULLABLE                 

  crl_current          SMALLINT          NULLABLE · DEFAULT 0     Valley of Death 감지 기준.

  rd_zone              VARCHAR(30)       NULLABLE                 exploration/valley_of_death/growth/maturity

  current_stage        SMALLINT          NOT NULL · DEFAULT 0     L2 Gate 통과 시 증가.

  strategic_goal_id    VARCHAR(100)      NULLABLE                 기관 전략 목표 ID.

  portfolio_id         UUID              NULLABLE · FK →          
                                         portfolios.id            

  program_id           UUID              NULLABLE · FK →          
                                         programs.id              

  complexity_level     VARCHAR(20)       NOT NULL · DEFAULT       low/medium/high/very_high
                                         \'medium\'               

  vuca_profile         JSONB             NULLABLE                 {\"volatility\":\"low\",\"uncertainty\":\"medium\",\"complexity\":\"high\",\"ambiguity\":\"low\"}

  start_date           DATE              NOT NULL                 

  end_date             DATE              NOT NULL                 

  pi_id                UUID              NOT NULL · FK → users.id PI.

  pm_id                UUID              NULLABLE · FK → users.id PM.

  created_at           TIMESTAMPTZ       NOT NULL · DEFAULT now() 
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 1.3 programs / 1.4 portfolios

v2.0 초안과 동일. programs(id·name·portfolio_id·owner_id·created_at) /
portfolios(id·name·strategic_goal_id·owner_id·created_at). 변경 없음.

### 1.4 project_members

  ----------------------------------------------------------------------------------------------------------------
  **컬럼명**        **타입**       **제약**                                  **설명**
  ----------------- -------------- ----------------------------------------- -------------------------------------
  id                UUID           PK                                        

  project_id        UUID           NOT NULL · FK · INDEX                     

  user_id           UUID           NOT NULL · FK                             

  role              VARCHAR(50)    NOT NULL                                  PI/PM/연구원/RA/컨설턴트

  allocation_rate   NUMERIC(5,2)   NOT NULL · DEFAULT 100                    계획 투입률 %.

  actual_rate       NUMERIC(5,2)   NOT NULL · DEFAULT 0                      실제 투입률. \[TIME\] 태그 자동 계산.

  overload_index    NUMERIC(5,2)   GENERATED ALWAYS AS                       과부하 지수. 1.2 초과 →
                                   (actual_rate/NULLIF(allocation_rate,0))   TEAM_OVERLOAD.
                                   STORED                                    

  joined_at         DATE           NOT NULL                                  

  left_at           DATE           NULLABLE                                  NULL = 현재 참여 중.

  UNIQUE            (project_id,   ---                                       
                    user_id,                                                 
                    joined_at)                                               
  ----------------------------------------------------------------------------------------------------------------

### 1.5 wbs_tasks (v2.0 보완: 선행관계·EXPERIMENT_LOOP 추가)

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **컬럼명**              **타입**       **제약**       **설명**
  ----------------------- -------------- -------------- ---------------------------------------------------------------------------------------------------------------------
  id                      UUID           PK             

  project_id              UUID           NOT NULL · FK  
                                         · INDEX        

  parent_task_id          UUID           NULLABLE · FK  WBS 계층 구조.
                                         → wbs_tasks.id 

  predecessor_task_id     UUID           NULLABLE · FK  선행 Task. BLOCKED 원인 추적.
                                         → wbs_tasks.id 

  task_code               VARCHAR(20)    NOT NULL       예: \"2-3\", \"AI-01\"

  name                    VARCHAR(300)   NOT NULL       

  status                  VARCHAR(30)    NOT NULL ·     DETECTED/DRAFT/ASSIGNED/ACKNOWLEDGED/NEGOTIATING/ACCEPTED/IN_PROGRESS/EXPERIMENT_LOOP/BLOCKED/REVIEW_REQUESTED/DONE
                                         DEFAULT        
                                         \'DRAFT\'      

  stage_no                SMALLINT       NOT NULL ·     소속 Stage 번호.
                                         DEFAULT 1      

  priority                VARCHAR(20)    NOT NULL ·     높음/보통/낮음
                                         DEFAULT        
                                         \'보통\'       

  assigned_to             UUID           NULLABLE · FK  담당자. NULL = 미배정.
                                         → users.id     

  assigned_by             UUID           NULLABLE · FK  지시자(PM).
                                         → users.id     

  due_date                DATE           NULLABLE       

  done_at                 TIMESTAMPTZ    NULLABLE       완료 일시.

  instruction             TEXT           NULLABLE       PM 업무지시 내용.

  dod_criteria            TEXT           NULLABLE       완료 기준(DoD).

  blocked_reason          TEXT           NULLABLE       BLOCKED 사유.

  experiment_loop_count   SMALLINT       NOT NULL ·     EXPERIMENT_LOOP 반복 횟수. 유형1 전용. ELN 기록 누적 횟수.
                                         DEFAULT 0      

  time_spent_h            NUMERIC(6,2)   NOT NULL ·     누적 투입시간.
                                         DEFAULT 0      

  gate_linked             BOOLEAN        NOT NULL ·     Gate 패키지 Task 여부.
                                         DEFAULT false  

  is_self_assigned        BOOLEAN        NOT NULL ·     PM 자가배정 (플레잉코치).
                                         DEFAULT false  

  created_at              TIMESTAMPTZ    NOT NULL ·     
                                         DEFAULT now()  
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 1.6 task_threads

v2.0 초안과 동일. 변경 없음.

### 1.7 daily_reports (v2.0 보완: 3-way 파싱 필드 완성)

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **컬럼명**           **타입**      **제약**        **설명**
  -------------------- ------------- --------------- ----------------------------------------------------------------------------------------------------------------
  id                   UUID          PK              report_id. Neo4j EVENT 노드 연결 키.

  project_id           UUID          NOT NULL · FK · 
                                     INDEX           

  author_id            UUID          NOT NULL · FK   

  channel              VARCHAR(30)   NOT NULL ·      rapai_app/outlook/teams
                                     DEFAULT         
                                     \'rapai_app\'   

  pm_role_context      VARCHAR(10)   NULLABLE        MGT/DO/REV. PM 플레잉코치 분류.

  mgt_actions          JSONB         NULLABLE        관리 행위 목록. \[{\"type\":\"assign\",\"task_id\":\"\...\",\"assignee\":\"\...\",\"due_date\":\"\...\"}\]

  do_actions           JSONB         NULLABLE        실행 행위 목록. \[{\"type\":\"task_done\",\"task_id\":\"\...\",\"time_h\":2.5,\"output\":\"\...\"}\]

  rev_actions          JSONB         NULLABLE        검토 행위 목록. \[{\"type\":\"review\",\"target_id\":\"\...\",\"result\":\"수정요청\",\"issues\":\[\...\]}\]

  raw_text             TEXT          NOT NULL        원문. UPDATE 트리거로 차단.

  parsed_tags          JSONB         NULLABLE        {\"DONE\":\[\"task_id\"\],\"ISSUE\":\[\"text\"\],\"TRL_UP\":{\"from\":4,\"to\":5},\"TIME\":2.5,\"COST\":45000}

  task_actions         JSONB         NULLABLE        {\"task_2_3\":\"DONE\",\"task_2_5\":\"IN_PROGRESS\"}

  trl_signal           JSONB         NULLABLE        {\"from\":4,\"to\":5,\"evidence\":\"ELN#415\"}

  cost_items           JSONB         NULLABLE        \[{\"category\":\"재료비\",\"amount\":45000}\]

  validation_status    VARCHAR(20)   NOT NULL ·      PENDING/PASSED/BLOCKED/WARN_IGNORED
                                     DEFAULT         
                                     \'PENDING\'     

  validation_results   JSONB         NULLABLE        {\"BLOCK\":\[\],\"WARN\":\[\...\],\"SUGGEST\":\[\...\]}

  human_bucket         VARCHAR(30)   NULLABLE        즉각행동/현황파악/판단필요.

  submitted_at         TIMESTAMPTZ   NOT NULL ·      
                                     DEFAULT now()   

  pm_read_at           TIMESTAMPTZ   NULLABLE        PM 열람 일시.
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------

**1.8\~1.11: kpi_baselines / kpi_actuals / budget_items (변경 없음)**

v2.0 초안과 동일. 각 테이블 상세는 v2.0 초안 참조.

### 1.12 gate_criteria / 1.13 gate_decisions (v2.0 보완)

  ------------------------------------------------------------------------------------
  **컬럼명**           **타입**       **제약**   **설명**
  -------------------- -------------- ---------- -------------------------------------
  (기존 필드)          ---            ---        v2.0 초안과 동일.

  gate_type            VARCHAR(30)    NULLABLE   L2 세부 유형:
  \[gate_decisions\]                             technical/quality/milestone. Gate
                                                 판단 패키지 유형 구분.

  insight_node_id      VARCHAR(100)   NULLABLE   Kill·Pivot 후 자동 생성된 Neo4j
  \[gate_decisions\]                             INSIGHT 노드 ID.
  ------------------------------------------------------------------------------------

**1.14 risks / 1.15 external_signals / 1.16 ip_signals / 1.17
attachments**

v2.0 초안과 동일. 변경 없음.

**1.18 generated_reports / 1.19 requirements / 1.20 notifications (v2.0
보완)**

  -------------------------------------------------------------------------------
  **컬럼명**          **타입**   **제약**   **설명**
  ------------------- ---------- ---------- -------------------------------------
  (기존 필드)         ---        ---        v2.0 초안과 동일.

  escalation_level    SMALLINT   NOT NULL · 에스컬레이션 단계. 0=초기발송 /
  \[notifications\]              DEFAULT 0  1=PM→PI 상향 / 2=PI→기관관리자 상향.
                                            SLA 초과 시 자동 증가.
  -------------------------------------------------------------------------------

### 1.21 agent_logs / 1.22 platform_metrics

v2.0 초안과 동일. 변경 없음.

## 2. 설정·참조 테이블 (v2.0 완결판 신규)

| **설정 테이블의 역할**                                                |
|                                                                       |
| 설정 테이블은 에이전트가 판단 기준으로 참조하는 시스템 파라미터       |
| 저장소입니다.                                                         |
|                                                                       |
| SPI 임계값·TRL 단계 정의·Gate 기준 템플릿은 코드에 하드코딩하지 않고  |
| DB에서 조회하여 유지보수성을 확보합니다.                              |
|                                                                       |
| 기관관리자가 RAPai 화면에서 직접 수정 가능합니다. 수정 시 versioning  |
| 필드가 자동 증가하고 이전 버전은 보존됩니다.                          |

### 2.1 spi_alert_thresholds --- SPI 경보 임계값

프로젝트 유형별·TRL 구간별 SPI 경보 임계값(CRITICAL/HIGH/MEDIUM/LOW)을
저장합니다. AG-KPI가 SPI 계산 후 이 테이블을 참조하여 경보 등급을
결정합니다.

  ------------------------------------------------------------------------------------
  **컬럼명**           **타입**       **제약**   **설명**
  -------------------- -------------- ---------- -------------------------------------
  id                   UUID           PK         

  project_type         VARCHAR(50)    NOT NULL   기준을 적용할 project_type. \"all\" =
                                                 전 유형 기본값.

  trl_range_min        SMALLINT       NULLABLE   TRL 범위 하한. NULL = 전 구간.

  trl_range_max        SMALLINT       NULLABLE   TRL 범위 상한. NULL = 전 구간.

  critical_threshold   NUMERIC(4,3)   NOT NULL · SPI 이 값 미만 → CRITICAL. (예:
                                      DEFAULT    0.700)
                                      0.700      

  high_threshold       NUMERIC(4,3)   NOT NULL · SPI 이 값 미만 → HIGH.
                                      DEFAULT    
                                      0.750      

  medium_threshold     NUMERIC(4,3)   NOT NULL · SPI 이 값 미만 → MEDIUM.
                                      DEFAULT    
                                      0.850      

  low_threshold        NUMERIC(4,3)   NOT NULL · SPI 이 값 미만 → LOW.
                                      DEFAULT    
                                      0.900      

  version              SMALLINT       NOT NULL · 변경 시 증가. 이전 버전 보존.
                                      DEFAULT 1  

  is_current           BOOLEAN        NOT NULL · 현행 기준 여부.
                                      DEFAULT    
                                      true       

  updated_by           UUID           NOT NULL · 최종 수정자 (기관관리자).
                                      FK →       
                                      users.id   

  updated_at           TIMESTAMPTZ    NOT NULL · 
                                      DEFAULT    
                                      now()      
  ------------------------------------------------------------------------------------

| **기본 임계값 (v2.8 설계서 16.1장 기준)**                             |
|                                                                       |
| basic_research (유형1): CRITICAL \< 0.70 / HIGH \< 0.75 / MEDIUM \<   |
| 0.85 / LOW \< 0.90                                                    |
|                                                                       |
| tech_rd (유형2): CRITICAL \< 0.70 / HIGH \< 0.75 / MEDIUM \< 0.85 /   |
| LOW \< 0.90                                                           |
|                                                                       |
| policy_research (유형3): CRITICAL \< 0.75 / HIGH \< 0.80 / MEDIUM \<  |
| 0.90 (납기 민감)                                                      |
|                                                                       |
| management_consulting (유형5): CRITICAL \< 0.75 / HIGH \< 0.80 /      |
| MEDIUM \< 0.90                                                        |

### 2.2 trl_stage_config --- TRL 9단계 설정

TRL 1\~9 각 단계의 명칭, L1 Gate 달성 근거 유형, 관리 모드, L2 Gate Must
기준을 저장합니다. AG-KPI가 TRL 달성 판단 시 참조합니다.

  ------------------------------------------------------------------------------------------
  **컬럼명**          **타입**           **제약**      **설명**
  ------------------- ------------------ ------------- -------------------------------------
  id                  UUID               PK            

  trl_level           SMALLINT           NOT NULL ·    TRL 단계 (1\~9).
                                         UNIQUE ·      
                                         CHECK(1\~9)   

  stage_name          VARCHAR(100)       NOT NULL      단계명. 예: \"기본 원리 관찰\"

  management_mode     VARCHAR(30)        NOT NULL      기초연구 모드/응용연구 모드/실증개발
                                                       모드/사업화 모드

  l1_evidence_types   VARCHAR(100)\[\]   NOT NULL      L1 Gate 달성 근거 유형 목록. 예:
                                                       ARRAY\[\"ELN 실험 기록\",\"PoC
                                                       데이터\",\"논문 초안\"\]

  l2_must_crl_min     SMALLINT           NULLABLE      해당 TRL 통과를 위한 L2 Must CRL
                                                       최소값. 예: TRL4 → CRL 3.

  description         TEXT               NULLABLE      단계 설명.
  ------------------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  **TRL**   **단계명**     **관리 모드**  **L1 근거 유형       **L2 Must CRL**
                                          (예시)**             
  --------- -------------- -------------- -------------------- -----------------
  1         기본 원리 관찰 기초연구 모드  이론 검토            NULL
                                          보고서·참고문헌      

  2         기술 개념 정립 기초연구 모드  개념 보고서·응용     NULL
                                          가능성 분석          

  3         개념 타당성    응용연구 모드  ELN 실험 기록·PoC    NULL
            입증                          데이터               

  4         실험실 환경    응용연구 모드  Lab-scale 실험       3
            검증                          보고서·성능 데이터   

  5         관련 환경 검증 실증개발 모드  Pilot 테스트         5
                                          보고서·고객 피드백   

  6         관련 환경      실증개발 모드  통합 프로토타입 시연 NULL
            프로토타입                    보고서               

  7         실제 환경      실증개발 모드  현장 실증            7
            시스템 실증                   보고서·실증기관 확인 

  8         완성 시스템    사업화 모드    인증서·규제 승인서   NULL
            검증                                               

  9         실제 환경 검증 사업화 모드    매출 실적·고객       9
            완료                          계약서               
  ------------------------------------------------------------------------------

### 2.2b crl_stage_config --- CRL 9단계 설정 (v2.0 완결판 신규)

CRL 1\~9 각 단계의 명칭, 조건, 달성 근거 유형, 확인자를 저장합니다.
AG-KPI가 CRL 달성 판단 시 참조합니다.

  ----------------------------------------------------------------------------------------------
  **컬럼명**              **타입**           **제약**      **설명**
  ----------------------- ------------------ ------------- -------------------------------------
  id                      UUID               PK            

  crl_level               SMALLINT           NOT NULL ·    CRL 단계 (1\~9).
                                             UNIQUE ·      
                                             CHECK(1\~9)   

  stage_name              VARCHAR(100)       NOT NULL      단계명. 예: \"고객 PoC 완료\"

  definition              TEXT               NOT NULL      단계 정의.

  evidence_types          VARCHAR(100)\[\]   NOT NULL      달성 근거 유형 목록. 예:
                                                           ARRAY\[\"고객 PoC 결과
                                                           보고서\",\"고객 피드백 서면\"\]

  approver_role           VARCHAR(30)        NOT NULL      확인자 역할. PM / PM+PI / PI

  l2_must_for_trl         SMALLINT           NULLABLE      이 CRL이 Must 기준인 대응 TRL 수준.
                                                           예: CRL 5 → TRL 5.

  requires_pi_signature   BOOLEAN            NOT NULL ·    PI 서명 필요 여부. CRL 5 이상 true.
                                             DEFAULT false 

  description             TEXT               NULLABLE      상세 설명.
  ----------------------------------------------------------------------------------------------

  -----------------------------------------------------------------------------------------------------
  **CRL**   **단계명**            **approver_role**   **requires_pi_signature**   **l2_must_for_trl**
  --------- --------------------- ------------------- --------------------------- ---------------------
  1         시장 문제 인식        PM                  false                       NULL

  2         잠재 고객 탐색        PM                  false                       NULL

  3         관심 표명 확인        PM                  false                       NULL

  4         초기 요구사항 수렴    PM                  false                       NULL

  5         고객 PoC 완료         PM+PI               true                        5
            ★전환점★                                                              

  6         파트너십 탐색         PI                  true                        NULL

  7         구매의향서(LOI)       PI                  true                        7

  8         파일럿 계약 완료      PI                  true                        NULL

  9         정식 계약·반복 구매   PI                  true                        9
  -----------------------------------------------------------------------------------------------------

### 2.3 gate_criteria_templates --- Gate 기준 템플릿

유형별 Gate 기준 기본 템플릿을 저장합니다. 착수 시 AG-INT가
project_type을 감지하여 해당 템플릿을 gate_criteria 테이블에 복사합니다.
기관관리자가 기관 특성에 맞게 커스터마이징 가능합니다.

  ----------------------------------------------------------------------------------------------
  **컬럼명**              **타입**       **제약**   **설명**
  ----------------------- -------------- ---------- --------------------------------------------
  id                      UUID           PK         

  project_type            VARCHAR(50)    NOT NULL   적용 유형.

  gate_layer              VARCHAR(20)    NOT NULL   L1_trl/L2_stage/L3_annual/L4_moving_target

  gate_type               VARCHAR(30)    NULLABLE   L2 전용: technical/quality/milestone

  criterion_name          VARCHAR(200)   NOT NULL   기준 명칭.

  criterion_level         VARCHAR(10)    NOT NULL   Must/Should/Could

  weight                  NUMERIC(4,2)   NULLABLE   Should·Could 가중치 (합계=1.0).

  default_description     TEXT           NULLABLE   기본 설명. 착수 시 복사됨.

  is_mandatory_template   BOOLEAN        NOT NULL · 삭제 불가 필수 템플릿 여부.
                                         DEFAULT    
                                         false      

  version                 SMALLINT       NOT NULL · 
                                         DEFAULT 1  

  updated_by              UUID           NOT NULL · 
                                         FK →       
                                         users.id   

  updated_at              TIMESTAMPTZ    NOT NULL · 
                                         DEFAULT    
                                         now()      
  ----------------------------------------------------------------------------------------------

### 2.4 project_type_configs --- 프로젝트 유형 설정

6개 project_type별 활성화할 Gate 계층 목록, 기본 파라미터를 저장합니다.
착수 시 AG-INT가 참조하여 GraphState.active_gates와
projects.active_gate_layers를 초기화합니다.

  -------------------------------------------------------------------------------------------------------------------------
  **컬럼명**             **타입**          **제약**   **설명**
  ---------------------- ----------------- ---------- ---------------------------------------------------------------------
  id                     UUID              PK         

  project_type           VARCHAR(50)       NOT NULL · 
                                           UNIQUE     

  display_name           VARCHAR(100)      NOT NULL   예: \"원천기술 연구\"

  active_gate_layers     VARCHAR(20)\[\]   NOT NULL   기본 활성 Gate 목록. 예:
                                                      ARRAY\[\"L1_trl\",\"L2_stage\",\"L3_annual\",\"L4_moving_target\"\]

  default_project_mode   VARCHAR(30)       NOT NULL   기본 project_mode.

  default_report_type    VARCHAR(10)       NOT NULL   기본 보고서 유형 (A/B/C/D).

  l4_partial_apply       BOOLEAN           NOT NULL · L4를 부분 적용하는 유형 여부 (유형3·4).
                                           DEFAULT    
                                           false      

  version                SMALLINT          NOT NULL · 
                                           DEFAULT 1  

  updated_by             UUID              NOT NULL · 
                                           FK →       
                                           users.id   

  updated_at             TIMESTAMPTZ       NOT NULL · 
                                           DEFAULT    
                                           now()      
  -------------------------------------------------------------------------------------------------------------------------

  --------------------------------------------------------------------------------------
  **project_type**        **display_name**   **active_gate_layers**   **보고서 유형**
  ----------------------- ------------------ ------------------------ ------------------
  basic_research          원천기술 연구      L1_trl, L2_stage,        B (자유)
                                             L3_annual,               
                                             L4_moving_target         

  tech_rd                 기술사업화 R&D     L1_trl, L2_stage,        B (자유)
                                             L3_annual,               
                                             L4_moving_target         

  policy_research         정책연구           L2_stage, L3_annual (L4  C (용역컨설팅)
                                             부분)                    

  roadmap_isp             기술로드맵·ISP     L2_stage, L3_annual (L4  C (용역컨설팅)
                                             부분)                    

  management_consulting   경영전략·AX 컨설팅 L2_stage, L3_annual      D (정책전략)

  hybrid                  복합·하이브리드    단계별 자동 전환 ---     단계별
                                             project_type 변경 시     
                                             갱신                     
  --------------------------------------------------------------------------------------

## 3. 에이전트 운영 데이터 테이블 (v2.0 완결판 신규)

### 3.1 team_competency_profiles --- 팀원 역량 프로파일

AG-TEAM이 팀원별 역량, 전문 분야, 이탈 위험 지수를 관리합니다.
project_members와 1:1로 연결됩니다.

  --------------------------------------------------------------------------------------------------------------------
  **컬럼명**                **타입**          **제약**             **설명**
  ------------------------- ----------------- -------------------- ---------------------------------------------------
  id                        UUID              PK                   

  project_member_id         UUID              NOT NULL · FK →      project_members와 1:1 연결.
                                              project_members.id · 
                                              UNIQUE               

  project_id                UUID              NOT NULL · FK ·      역정규화.
                                              INDEX                

  user_id                   UUID              NOT NULL · FK ·      
                                              INDEX                

  competency_tags           VARCHAR(50)\[\]   NULLABLE             역량 태그 목록. 예:
                                                                   ARRAY\[\"나노소재\",\"실험설계\",\"데이터분석\"\]

  seniority_level           VARCHAR(20)       NULLABLE             junior/mid/senior/principal

  consecutive_issue_count   SMALLINT          NOT NULL · DEFAULT 0 연속 \[ISSUE\] 태그 횟수. 3회↑ → 이탈 위험 신호.

  consecutive_no_report     SMALLINT          NOT NULL · DEFAULT 0 연속 미보고 일수. AG-TEAM 이탈 감지 기준.

  spi_trend                 VARCHAR(20)       NULLABLE             improving/stable/declining. 최근 4주 SPI 추이.

  attrition_risk_score      NUMERIC(4,2)      NOT NULL · DEFAULT 0 이탈 위험 지수 (0.0\~10.0). AG-TEAM 규칙 엔진 계산.

  last_retrospective_at     DATE              NULLABLE             최근 Retrospective 참여일.

  updated_at                TIMESTAMPTZ       NOT NULL · DEFAULT   AG-TEAM 갱신 일시.
                                              now()                
  --------------------------------------------------------------------------------------------------------------------

### 3.2 agent_threshold_configs --- 에이전트 임계값 설정

에이전트별 현재 임계값을 저장합니다. 즉각 학습(±5% 자동 조정) 후 이
테이블이 갱신됩니다. AG-QA가 이 테이블을 기준으로 드리프트를 감시합니다.

  ------------------------------------------------------------------------------------------------------------
  **컬럼명**          **타입**        **제약**   **설명**
  ------------------- --------------- ---------- -------------------------------------------------------------
  id                  UUID            PK         

  agent_id            VARCHAR(30)     NOT NULL   AG-KPI/AG-SENSE/AG-CHANGE/AG-INT/AG-REPORT/AG-SCOPE/AG-TEAM
                                                 등

  param_name          VARCHAR(100)    NOT NULL   파라미터 이름. 예: \"vod_detection_sensitivity\"

  current_value       NUMERIC(10,4)   NOT NULL   현재 값.

  baseline_value      NUMERIC(10,4)   NOT NULL   기준값 (즉각 학습 전 원점).

  min_allowed         NUMERIC(10,4)   NOT NULL   최솟값 (즉각 학습 허용 하한).

  max_allowed         NUMERIC(10,4)   NOT NULL   최댓값 (즉각 학습 허용 상한).

  auto_adjust_limit   NUMERIC(5,4)    NOT NULL · 즉각 학습 자동 조정 허용 변폭. DEFAULT 5% (±0.05).
                                      DEFAULT    
                                      0.05       

  last_adjusted_by    VARCHAR(50)     NULLABLE   조정 주체. auto/관리담당자명

  last_adjusted_at    TIMESTAMPTZ     NULLABLE   최근 조정 일시.

  UNIQUE              (agent_id,      ---        에이전트별 파라미터 중복 방지.
                      param_name)                
  ------------------------------------------------------------------------------------------------------------

### 3.3 learning_cycle_records --- 자가학습 사이클 기록

AG-QA가 조율하는 3계층(즉각/주기/심층) 자가학습 사이클의 실행 이력을
저장합니다. Neo4j LEARNING_CYCLE 노드의 PostgreSQL 조회용 사본입니다.

  --------------------------------------------------------------------------------------------------------------------
  **컬럼명**              **타입**       **제약**           **설명**
  ----------------------- -------------- ------------------ ----------------------------------------------------------
  id                      UUID           PK                 

  agent_id                VARCHAR(30)    NOT NULL           학습 대상 에이전트.

  learning_layer          VARCHAR(20)    NOT NULL           immediate/periodic/deep (즉각/주기/심층)

  trigger_type            VARCHAR(50)    NOT NULL           false_positive/gate_decision/retrospective/monthly_batch

  evidence_count          INTEGER        NOT NULL · DEFAULT 학습에 사용된 데이터 건수.
                                         0                  

  param_before            JSONB          NOT NULL           학습 전 파라미터 스냅샷.

  param_after             JSONB          NOT NULL           학습 후 파라미터.

  simulated_improvement   NUMERIC(5,4)   NULLABLE           시뮬레이션 예상 성능 향상률.

  approved_by             UUID           NULLABLE · FK →    승인자. 즉각학습은 NULL (자동).
                                         users.id           

  approval_status         VARCHAR(20)    NOT NULL · DEFAULT auto_applied/pending/approved/rejected/rolled_back
                                         \'auto_applied\'   

  deployed_at             TIMESTAMPTZ    NULLABLE           실제 적용 일시.

  rollback_params         JSONB          NULLABLE           롤백용 이전 파라미터 보존.

  mindvault_node_id       VARCHAR(100)   NULLABLE           Neo4j LEARNING_CYCLE 노드 ID.

  created_at              TIMESTAMPTZ    NOT NULL · DEFAULT 
                                         now()              
  --------------------------------------------------------------------------------------------------------------------

## 4. Neo4j MindVault --- 완전 정의 (v2.0 완결판)

### 4.1 설계 원칙

| **MindVault 4원칙**                                                   |
|                                                                       |
| 원칙 1 --- Append-only: 생성만 가능. 수정·삭제 불가. 오류 →           |
| OVERRIDE_DECISION 신규 생성.                                          |
|                                                                       |
| 원칙 2 --- 관계가 맥락을 전달: 노드에 모든 정보를 넣지 않음. 관계     |
| 유형이 의미를 전달.                                                   |
|                                                                       |
| 원칙 3 --- project_id 파티셔닝: SaaS 전환 시 tenant_id 추가만으로     |
| 격리 완성.                                                            |
|                                                                       |
| 원칙 4 --- PostgreSQL은 조회 사본:                                    |
| GATE_DECISION·TRL_SNAPSHOT·OVERRIDE_DECISION의 법적 원본 = Neo4j.     |

### 4.2 노드 완전 목록 (14개 --- CRL_SNAPSHOT 신규)

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **노드 타입**         **핵심 속성**                                                                                                                                         **생성 조건**              **v2.0 변경**
  --------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------- --------------------------------------
  :EVENT                event_id·project_id·author_id·channel·raw_text·parsed·gate_impact·created_at                                                                          일일보고 Layer 4 Agent     변경 없음
                                                                                                                                                                              흐름                       

  :TRL_SNAPSHOT         snapshot_id·project_id·trl_from·trl_to·evidence\[\]·pi_signature·signed_at·mindvault_hash                                                             TRL_ACHIEVED + PI 서명     attachments\[\] 필드 추가 --- ELN 첨부
                                                                                                                                                                                                         ID 목록

  :CRL_SNAPSHOT         snapshot_id·project_id·crl_from·crl_to·evidence\[\]·approver_signature·approver_role·signed_at·mindvault_hash                                         \[CRL_UP\] 태그 + 서명     v2.0 신규 --- TRL_SNAPSHOT과 대칭
                                                                                                                                                                              완료 (CRL 1\~4: PM / CRL   구조. CRL 5 이상은 PI 서명 포함.
                                                                                                                                                                              5: PM+PI / CRL 6\~9: PI)   

  :GATE_DECISION        decision_id·project_id·gate_layer·gate_type·decision·rationale·should_score·must_results·decided_by·decided_at·signature_hash                         Gate 결정 PI 서명          gate_type 필드 추가
                                                                                                                                                                                                         (technical/quality/milestone)

  :GATE_CRITERIA        criteria_id·project_id·gate_layer·criteria_content·version·approved_by·effective_from·created_at                                                      착수·기준 변경             변경 없음

  :KPI_RECONFIG         reconfig_id·project_id·old_kpis·new_kpis·reason·reconfigured_by·reconfigured_at                                                                       TRL 전환·L4 Pivot          변경 없음

  :VALIDITY_REVIEW      review_id·project_id·trigger_signal·market_score·tech_score·policy_score·investment_score·total_score·options\[\]·decided_option·reviewed_at          L4 Moving Target Gate 발동 변경 없음

  :TAILORING_DECISION   tailoring_id·project_id·project_type·lifecycle_template·gate_layers·selection_rationale·approved_by·effective_from                                    착수·project_type 변경     gate_layers\[\] 필드 추가

  :OUTCOME_SNAPSHOT     snapshot_id·project_id·review_year·output_results·outcome_results·value_results·snapshot_date·recorded_by                                             TRACKING_REVIEW 이벤트     output_results 필드 추가
                                                                                                                                                                              (1·3·5년)                  

  :LEARNING_CYCLE       cycle_id·agent_id·learning_layer·trigger_type·evidence_count·param_before·param_after·simulated_improvement·approved_by·deployed_at·rollback_params   자가학습 사이클 완료       learning_records_id → PostgreSQL 연결

  :OVERRIDE_DECISION    override_id·project_id·target_type·target_node_id·override_reason·overridden_by·original_value·corrected_value·impact_scope·overridden_at             Human Override 실행        변경 없음

  :INSIGHT              insight_id·project_id·trigger_type·content·lessons_learned·next_recommendations·retrospective_context·created_at                                      Gate                       trigger_type 구분 추가
                                                                                                                                                                              Kill·Pivot·Retrospective   (gate_kill/gate_pivot/retrospective)

  :DELIVERABLE          deliverable_id·project_id·name·type·completion_rate·client_approved·submitted_at                                                                      산출물 납품 이벤트         generated_report_id 연결

  :CLIENT_FEEDBACK      feedback_id·project_id·deliverable_id·feedback_content·satisfaction_score·action_required·received_at                                                 발주처 검토 의견 수신      requirements_ids\[\] 연결 --- 충족률
                                                                                                                                                                                                         갱신 대상
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 4.3 관계 유형 완전 정의 (9개)

  ---------------------------------------------------------------------------------------------------------------------------------
  **관계 유형**          **방향**   **의미**           **주요 경로**
  ---------------------- ---------- ------------------ ----------------------------------------------------------------------------
  TRIGGERS               →          이 이벤트가 저     (:EVENT)→TRIGGERS→(:TRL_SNAPSHOT\|:CRL_SNAPSHOT\|:GATE_DECISION\|:INSIGHT)
                                    노드를 생성시킴    

  CAUSED_BY              →          이 노드가 저       (:KPI_RECONFIG)→CAUSED_BY→(:TRL_SNAPSHOT\|:GATE_DECISION)
                                    원인으로 발생함    

  CORRECTS               →          Override 노드가    (:OVERRIDE_DECISION)→CORRECTS→(:GATE_DECISION\|:TRL_SNAPSHOT)
                                    대상 노드를 정정함 

  FEEDS_INTO             →          학습 데이터로      (:OVERRIDE_DECISION)→FEEDS_INTO→(:LEARNING_CYCLE)
                                    환류됨             

  SUPERSEDES             →          신버전이 구버전을  (:GATE_CRITERIA v2)→SUPERSEDES→(:GATE_CRITERIA v1)
                                    대체함             

  INFORMS                →          판단 근거로 제공됨 (:VALIDITY_REVIEW)→INFORMS→(:GATE_DECISION)

  PRODUCES               →          결과물을 생성함    (:GATE_DECISION)→PRODUCES→(:INSIGHT)

  SUBMITTED_TO           →          평가 패키지에      (:OUTCOME_SNAPSHOT)→SUBMITTED_TO→(L3 추적평가)
                                    포함됨             

  RETROSPECTIVE_YIELDS   →          Retrospective가    (Retrospective Event)→RETROSPECTIVE_YIELDS→(:INSIGHT)
                                    인사이트를 산출함  
  ---------------------------------------------------------------------------------------------------------------------------------

### 4.4 핵심 그래프 쿼리

| // 1. Gate 결정 전체 흐름 조회 (감사·이의신청용)                      |
|                                                                       |
| MATCH (gd:GATE_DECISION {project_id: \$pid})                          |
|                                                                       |
| OPTIONAL MATCH (gd)-\[:PRODUCES\]-\>(ins:INSIGHT)                     |
|                                                                       |
| OPTIONAL MATCH (od:OVERRIDE_DECISION)-\[:CORRECTS\]-\>(gd)            |
|                                                                       |
| OPTIONAL MATCH (vr:VALIDITY_REVIEW)-\[:INFORMS\]-\>(gd)               |
|                                                                       |
| RETURN gd, ins, od, vr ORDER BY gd.decided_at                         |
|                                                                       |
| // 2. Pivot 결정 선례 검색 (L4 Gate 패키지용)                         |
|                                                                       |
| MATCH (gd:GATE_DECISION {decision: \"Pivot\"})                        |
|                                                                       |
| WHERE gd.project_id \<\> \$current_pid                                |
|                                                                       |
| MATCH (gd)-\[:PRODUCES\]-\>(ins:INSIGHT)                              |
|                                                                       |
| RETURN gd.rationale, ins.lessons_learned ORDER BY gd.decided_at DESC  |
| LIMIT 5                                                               |
|                                                                       |
| // 3. 자가학습 환류 체인 추적                                         |
|                                                                       |
| MATCH (od:OVERRIDE_DECISION {project_id: \$pid})                      |
|                                                                       |
| -\[:FEEDS_INTO\]-\>(lc:LEARNING_CYCLE)                                |
|                                                                       |
| RETURN od.override_reason, lc.agent_id, lc.learning_layer,            |
|                                                                       |
| lc.simulated_improvement ORDER BY od.overridden_at                    |
|                                                                       |
| // 4. TRL 달성 근거 원본 조회 (법적 증빙)                             |
|                                                                       |
| MATCH (ts:TRL_SNAPSHOT {project_id: \$pid})                           |
|                                                                       |
| WHERE ts.trl_to = \$trl_level                                         |
|                                                                       |
| RETURN ts.evidence, ts.pi_signature, ts.signed_at, ts.mindvault_hash  |

**4b. 이벤트 레지스트리 --- PostgreSQL events 테이블**

v2.8 명세서 10장의 이벤트를 저장하고 처리 이력을 추적합니다.
CRL_UP_REPORTED 이벤트가 v2.0에서 신규 추가됩니다.

**4b.1 events 테이블 스키마**

  -----------------------------------------------------------------------------
  **컬럼명**     **타입**      **제약**   **설명**
  -------------- ------------- ---------- -------------------------------------
  id             UUID          PK         

  project_id     UUID          NOT NULL · 
                               FK · INDEX 

  event_type     VARCHAR(80)   NOT NULL · 이벤트 유형. 아래 목록 참조.
                               INDEX      

  triggered_by   VARCHAR(50)   NOT NULL   report_id / agent_id / scheduler /
                                          manual

  trigger_id     UUID          NULLABLE   트리거 소스 레코드 ID.

  payload        JSONB         NULLABLE   이벤트 페이로드.

  processed      BOOLEAN       NOT NULL · 처리 완료 여부.
                               DEFAULT    
                               false      

  processed_at   TIMESTAMPTZ   NULLABLE   처리 완료 일시.

  created_at     TIMESTAMPTZ   NOT NULL · 
                               DEFAULT    
                               now()      
  -----------------------------------------------------------------------------

**4b.2 이벤트 유형 목록 (v2.0 --- CRL 이벤트 추가)**

  ------------------------------------------------------------------------------------
  **이벤트 유형**            **발동 조건**     **담당 에이전트**  **처리 결과**
  -------------------------- ----------------- ------------------ --------------------
  TRL_ACHIEVED               TRL_UP 태그 + PI  AG-KPI → AG-SCOPE  TRL_SNAPSHOT 생성 ·
                             서명                                 KPI_RECONFIG

  CRL_UP_REPORTED            \[CRL_UP\] 태그   AG-KPI →           CRL_SNAPSHOT 생성 ·
                             일일보고 수신     crl_stage_config   crl_current 갱신 ·
                                               참조               CRL5+ 서명 요청 ·
                                                                  VoD 재감지

  CRL_LAGGING                TRL≥5 AND CRL≤3   AG-KPI → AG-CHANGE L4 즉시 발동
                             (VoD)             → AG-INT           (CRITICAL) · PI 72h
                                                                  SLA

  GATE_REVIEW                Stage 완료 결정   AG-INT (전체 병렬) GATE_DECISION(L2) ·
                                                                  WBS 확정

  GATE_DECISION_RECORDED     Gate 결정 PI 서명 AG-INT · MindVault GATE_DECISION 노드
                                                                  생성

  ANNUAL_REVIEW_DUE          회계연도 D-30     AG-KPI · AG-REPORT L3 평가 패키지 자동
                                                                  조립

  EXTERNAL_SIGNAL_CRITICAL   AG-SENSE CRITICAL AG-SENSE → AG-KPI  L4 유효성 평가 · PI
                             감지                                 72h SLA

  SCOPE_CHANGE               범위 변경 요청    AG-SCOPE →         CCB 승인 후 L2 기준
                                               AG-INT(CCB)        재검토

  DELIVERABLE_SUBMITTED      산출물 납품       AG-REPORT ·        납품 패키지 · 발주처
                             이벤트            AG-STAKE           검토 요청

  PROJECT_TYPE_TRANSITION    project_type 변경 AG-INT             TAILORING_DECISION ·
                                                                  파라미터 재설정

  TRACKING_REVIEW            과제 종료 후      AG-KPI · AG-REPORT OUTCOME_SNAPSHOT ·
                             1·3·5년                              추적평가 초안

  RETROSPECTIVE_DUE          Stage 완료 직후   AG-TEAM · AG-INT   Retrospective Task
                             자동                                 자동 등록

  TEAM_OVERLOAD              투입률 \> 120%    AG-TEAM ·          과부하 경보 · 재배치
                                               AG-CHANGE          초안

  TEAM_CHANGE                팀원 합류·이탈    AG-TEAM · AG-SCOPE 역할 공백 감지 · WBS
                                                                  영향 분석

  INSIGHT_GENERATED          Gate Kill·Pivot   AG-INT · MindVault INSIGHT 노드 생성 ·
                             직후 자동                            학습 입력 요청

  DAILY_REPORT_SUBMITTED     일일보고 Layer 1  AG-INT (이중 분기) Human 흐름 + Agent
                             수신                                 흐름 동시
  ------------------------------------------------------------------------------------

## 5. Redis · Qdrant · GraphState

### 5.1 Redis 키 패턴 (10개 --- 변경 없음)

v2.0 초안과 동일.
report:queue·graph_state·spi·alert·session·lock·offline·rate_limit·agent_result·push_token.
상세는 v2.0 초안 참조.

### 5.2 Qdrant 컬렉션 (4개 --- 변경 없음)

v2.0 초안과 동일.
insight_embeddings·gate_decision_embeddings·report_embeddings·deliverable_embeddings.
상세는 v2.0 초안 참조.

### 5.3 GraphState 전체 필드 (v2.0 완결판 --- 설정 테이블 연동 추가)

| class RDProjectState(TypedDict):                                      |
|                                                                       |
| \# ── 과제 기본 컨텍스트 ──────────────────────────────────────────   |
|                                                                       |
| project_id: str                                                       |
|                                                                       |
| project_type: str \# project_type_configs 참조                        |
|                                                                       |
| project_mode: str                                                     |
|                                                                       |
| lifecycle_status: str                                                 |
|                                                                       |
| active_gate_layers: List\[str\] \# project_type_configs에서 로드      |
|                                                                       |
| \# ── TRL / CRL ──────────────────────────────────────────────────    |
|                                                                       |
| trl_target: int                                                       |
|                                                                       |
| trl_current: int                                                      |
|                                                                       |
| crl_target: int                                                       |
|                                                                       |
| crl_current: int                                                      |
|                                                                       |
| rd_zone: str                                                          |
|                                                                       |
| experiment_loop_counts: Dict\[str, int\] \# task_id → 반복 횟수       |
|                                                                       |
| \# ── Gate 계층 컨텍스트 ──────────────────────────────────────────   |
|                                                                       |
| gate_layer: str                                                       |
|                                                                       |
| current_stage: int                                                    |
|                                                                       |
| gate_must_status: Dict\[str, bool\]                                   |
|                                                                       |
| gate_should_scores: Dict\[str, float\]                                |
|                                                                       |
| gate_overall_score: float                                             |
|                                                                       |
| pending_gate_type: str \# technical/quality/milestone                 |
|                                                                       |
| annual_review_due: date                                               |
|                                                                       |
| performance_rate: float                                               |
|                                                                       |
| l3_grade: str                                                         |
|                                                                       |
| validity_score: float                                                 |
|                                                                       |
| last_l4_trigger: datetime                                             |
|                                                                       |
| l4_decision: str                                                      |
|                                                                       |
| gate_readiness: float \# Gate 준비도 % (AG-KPI 계산)                  |
|                                                                       |
| \# ── KPI 3계층 ───────────────────────────────────────────────────   |
|                                                                       |
| kpi_layer: str                                                        |
|                                                                       |
| output_kpis: List\[dict\]                                             |
|                                                                       |
| outcome_kpis: List\[dict\]                                            |
|                                                                       |
| value_kpis: List\[dict\]                                              |
|                                                                       |
| tracking_reviews: List\[date\]                                        |
|                                                                       |
| \# ── SPI 경보 임계값 (spi_alert_thresholds 캐시) ─────────────────   |
|                                                                       |
| spi_thresholds: dict \# {critical:0.70, high:0.75, medium:0.85,       |
| low:0.90}                                                             |
|                                                                       |
| \# ── 가치 전달 사슬 ──────────────────────────────────────────────   |
|                                                                       |
| strategic_goal_id: Optional\[str\]                                    |
|                                                                       |
| program_id: Optional\[str\]                                           |
|                                                                       |
| portfolio_id: Optional\[str\]                                         |
|                                                                       |
| \# ── 불확실성·복잡성 ─────────────────────────────────────────────   |
|                                                                       |
| complexity_level: str                                                 |
|                                                                       |
| vuca_profile: dict                                                    |
|                                                                       |
| \# ── 팀 관리 ─────────────────────────────────────────────────────   |
|                                                                       |
| team_profiles: List\[dict\] \# team_competency_profiles 캐시          |
|                                                                       |
| retrospective_due: Optional\[date\]                                   |
|                                                                       |
| \# ── AG-QA 모니터링 ──────────────────────────────────────────────   |
|                                                                       |
| qa_monitor: dict \# {error_rates, drift_flags, override_history,      |
|                                                                       |
| \# false_positive_rates, last_audit_at}                               |
|                                                                       |
| agent_thresholds: dict \# agent_threshold_configs 캐시                |
|                                                                       |
| \# ── 에이전트별 처리 결과 ────────────────────────────────────────   |
|                                                                       |
| integration_result: Optional\[dict\] \# AG-INT                        |
|                                                                       |
| scope_result: Optional\[dict\] \# AG-SCOPE                            |
|                                                                       |
| schedule_result: Optional\[dict\] \# AG-SCHED                         |
|                                                                       |
| kpi_result: Optional\[dict\] \# AG-KPI                                |
|                                                                       |
| ip_result: Optional\[dict\] \# AG-IP                                  |
|                                                                       |
| change_result: Optional\[dict\] \# AG-CHANGE                          |
|                                                                       |
| sense_result: Optional\[dict\] \# AG-SENSE                            |
|                                                                       |
| budget_result: Optional\[dict\] \# AG-BUDGET                          |
|                                                                       |
| stake_result: Optional\[dict\] \# AG-STAKE                            |
|                                                                       |
| report_result: Optional\[dict\] \# AG-REPORT                          |
|                                                                       |
| team_result: Optional\[dict\] \# AG-TEAM                              |
|                                                                       |
| qa_result: Optional\[dict\] \# AG-QA                                  |
|                                                                       |
| \# ── 일일보고 처리 컨텍스트 ─────────────────────────────────────    |
|                                                                       |
| last_report_id: Optional\[str\]                                       |
|                                                                       |
| pending_alerts: List\[dict\]                                          |

## 6. 인덱스·파티셔닝·보안

### 6.1 전체 인덱스 목록

  --------------------------------------------------------------------------------
  **테이블**                 **인덱스 컬럼**      **타입**     **목적**
  -------------------------- -------------------- ------------ -------------------
  projects                   lifecycle_status     B-tree       활성 과제 조회.

  projects                   project_type ·       복합 B-tree  유형별·등급별 조회.
                             security_level                    

  projects                   active_gate_layers   GIN          Gate 계층별 과제
                                                               조회.

  wbs_tasks                  project_id · status  복합 B-tree  과제별 미완료 Task
                                                               (PM 대시보드 핵심).

  wbs_tasks                  assigned_to · status 복합 B-tree  팀원별 Task
                                                               (AG-TEAM 투입률).

  daily_reports              project_id ·         복합 B-tree  과제별 보고 시계열.
                             submitted_at                      

  daily_reports              author_id ·          복합 B-tree  팀원별 보고 이력.
                             submitted_at                      

  kpi_actuals                baseline_id ·        복합 B-tree  KPI 시계열.
                             recorded_at                       

  gate_decisions             project_id ·         복합 B-tree  Gate 결정 이력.
                             decided_at                        

  agent_logs                 project_id ·         복합 B-tree  에이전트
                             agent_id ·                        이력·오탐률.
                             executed_at                       

  task_threads               task_id · created_at 복합 B-tree  Task 대화 이력.

  notifications              recipient_id ·       복합 B-tree  사용자별 알람.
                             sent_at                           

  notifications              project_id ·         복합 B-tree  과제별 경보·SLA.
                             severity · sent_at                

  external_signals           project_id ·         복합 B-tree  AG-SENSE 신호 이력.
                             severity ·                        
                             detected_at                       

  events                     project_id ·         복합 B-tree  이벤트 이력.
                             event_type ·                      
                             created_at                        

  events                     processed ·          복합 B-tree  미처리 이벤트 스캔.
                             created_at                        

  spi_alert_thresholds       project_type ·       복합 B-tree  현행 임계값 조회.
                             is_current                        

  agent_threshold_configs    agent_id ·           복합 B-tree  파라미터 조회.
                             param_name           (UNIQUE)     

  team_competency_profiles   user_id · project_id 복합 B-tree  팀원 프로파일 조회.

  learning_cycle_records     agent_id ·           복합 B-tree  학습 사이클 이력.
                             created_at                        
  --------------------------------------------------------------------------------

### 6.2 파티셔닝 전략

  -------------------------------------------------------------------------
  **테이블**         **파티션 키**  **방식**     **이유**
  ------------------ -------------- ------------ --------------------------
  daily_reports      submitted_at   RANGE 월별   보고 데이터 고성장.

  kpi_actuals        recorded_at    RANGE 분기별 시계열 집계·추적평가
                                                 최적화.

  agent_logs         executed_at    RANGE 월별   로그 고성장. 5년 감사
                                                 보관.

  notifications      sent_at        RANGE 월별   알람 이력 고성장.

  events             created_at     RANGE 월별   이벤트 고성장.

  wbs_tasks          project_id     HASH 16 버킷 멀티테넌시 격리 준비.
  -------------------------------------------------------------------------

### 6.3 보안 등급별 처리

  ------------------------------------------------------------------------
  **등급**     **PostgreSQL**         **Neo4j**          **LLM 사용**
  ------------ ---------------------- ------------------ -----------------
  일반         평문. 클라우드 SaaS    일반 클러스터.     Claude API
               가능.                                     (PUBLIC).

  주의         컬럼 AES-256.          암호화 전송.       Claude API
               온프레미스 권장.                          (RESTRICTED).

  보호         DB 전체 암호화.        에어갭.            로컬 LLM
               온프레미스 전용.                          (Exaone·LLaMA).
               외부망 차단.                              

  비밀         HSM 키 관리. 독립 물리 완전 격리.         로컬 LLM. LLM
               서버. 강제 감사 로그.                     최소화.
  ------------------------------------------------------------------------

*--- 이하 여백 ---*
