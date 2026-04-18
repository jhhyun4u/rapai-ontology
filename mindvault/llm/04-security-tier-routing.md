# 04. Security-Tier LLM Routing — 보안등급 LLM 라우팅 운영 가이드

**작성일:** 2026-04-18
**상태:** ✅ Active (ADR-002 결정 13 + v2.9 Section 19.2 계승)
**근거:** `decisions/002-ai-model-architecture.md`
**관련:** `llm/01-model-selection.md`, `system/02-specialized-ai-model.md`

> **이 문서의 역할**
> "어떤 데이터가 어떤 모델로 흘러가는가"를 운영 가능한 수준으로 정의한다.
> ABAC (Attribute-Based Access Control) 기반 라우팅 결정 규칙, 위반 감지, 감사 대응의 SSOT.

---

## 1. 보안등급 4-Tier 정의 (v2.9 준용)

| 등급 | 코드 | 정의 | 예시 |
|---|---|---|---|
| **PUBLIC** | 1 | 공개 가능 | 보도자료, 일반 기술 동향, 공공 정책 자료 |
| **RESTRICTED** | 2 | 내부 공유 가능 | 내부 보고서 초안, 비공개 R&D 계획 요약 |
| **CONFIDENTIAL** | 3 | 보호 — 자체호스팅 필수 | 실험 원천 데이터, 미공개 특허 기술, 고객 NDA |
| **SECRET** | 4 | 비밀 — 완전 오프라인 | 국가 보안 R&D, 방산·안보 관련, 법무 특수 |

**원칙:** 데이터 security_tier는 프로젝트 수준 + 문서 수준 **둘 다** 부착 가능. 높은 쪽이 지배.

---

## 2. 라우팅 매트릭스

### 2.1 기본 라우팅 (결정 13)

| 데이터 보안등급 | 주력 LLM | 대체/백업 | 전송 경로 |
|---|---|---|---|
| **PUBLIC** | Claude API Sonnet 4.6 | 로컬 Gemma 4 31B-MoE | HTTPS → Anthropic Cloud |
| **RESTRICTED** | Claude API Sonnet 4.6 | 로컬 Gemma 4 31B-MoE | HTTPS → Anthropic Cloud (Zero Data Retention) |
| **CONFIDENTIAL** | **로컬 Gemma 4 31B-MoE + LoRA SFT** | 로컬 EXAONE 4.0 32B Dense | 내부 VPC only |
| **SECRET** | **로컬 Gemma 4 31B-MoE + LoRA SFT** | 로컬 EXAONE 4.0 32B Dense | **완전 오프라인** (에어갭) |
| **Parser (모든 등급)** | 로컬 Gemma 4 4B + QLoRA | — | 내부 전용 |

### 2.2 Task-Specific 모델 라우팅

모든 Task-Specific 소형 모델 + OR + Rule Engine = **전 등급 내부 처리** (외부 API 미사용).

| 컴포넌트 | 라우팅 |
|---|---|
| ModernBERT-ko WBS Classifier | 내부 전용 |
| Bi-encoder Scorer + BGE-Reranker | 내부 전용 |
| TFT Forecaster | 내부 전용 |
| R-GCN GNN | 내부 전용 |
| Isolation Forest + LSTM-AE | 내부 전용 |
| OR-Tools CP-SAT | 내부 전용 |
| Rule Engine (CP3) | 내부 전용 |
| Qdrant / Neo4j / PostgreSQL | 내부 전용 |

---

## 3. ABAC 기반 라우팅 결정 흐름

### 3.1 결정 알고리즘 (의사코드)

```
function route_llm(request):
    # 1. 요청에 포함된 모든 리소스의 보안등급 수집
    resource_tiers = collect_tiers(request.documents, request.project)

    # 2. 최대 등급 적용 (지배 규칙)
    max_tier = max(resource_tiers)

    # 3. ABAC 4속성 검사
    subject_cleared = check_subject_clearance(request.user, max_tier)
    if not subject_cleared:
        return DENY("사용자 권한 부족")

    env_ok = check_environment(request.ip, request.device)
    if not env_ok:
        return DENY("환경 조건 불충족")

    action_allowed = check_action(request.action, max_tier)
    if not action_allowed:
        return DENY("허용되지 않은 액션")

    # 4. 라우팅 결정
    if max_tier in [PUBLIC, RESTRICTED]:
        primary = ClaudeSonnet46
        fallback = LocalGemma31B_MoE
    elif max_tier in [CONFIDENTIAL, SECRET]:
        primary = LocalGemma31B_MoE_LoRA
        fallback = LocalExaone40_32B_Dense

    # 5. Parser 분기 (모든 등급)
    if request.task == "parse":
        return LocalGemma4_4B_QLoRA

    # 6. PROV-O 기록
    log_routing_decision(request, max_tier, primary, timestamp)

    return primary
```

### 3.2 ABAC 4속성 상세

| 속성 | 정의 | 검사 대상 |
|---|---|---|
| **Subject** | 사용자 속성 | 역할(PI/연구원/외부), 소속 기관, clearance level |
| **Resource** | 대상 리소스 속성 | security_tier, funding_source, contract_modality |
| **Environment** | 환경 속성 | IP (VPN 여부), 디바이스 (회사 지급), 시간대 |
| **Action** | 요청 액션 | read / write / summarize / export |

### 3.3 등급별 허용 액션 매트릭스

| 등급 | read | summarize (LLM) | write | export | forward_to_external |
|---|---|---|---|---|---|
| PUBLIC | ✅ All | ✅ Claude/Gemma | ✅ | ✅ | ✅ |
| RESTRICTED | ✅ 내부 | ✅ Claude/Gemma | ✅ | 🟡 승인 | ❌ |
| CONFIDENTIAL | ✅ 인가자 | ✅ 로컬만 | ✅ | 🔴 PI 승인 | ❌ |
| SECRET | ✅ 인가자+로그 | ✅ 로컬만 (에어갭) | ✅ | 🔴 이사회 승인 | ❌ |

---

## 4. 예외 처리 및 Fallback 규칙

### 4.1 Fallback 트리거

| 트리거 | 동작 |
|---|---|
| Claude API 장애 (5xx × 3회) | PUBLIC·RESTRICTED → 로컬 Gemma 4 31B-MoE 전환 (1시간 Cooldown) |
| 로컬 Gemma 4 GPU 장애 | CONFIDENTIAL·SECRET → EXAONE 4.0 자동 전환 |
| EXAONE 4.0 전환 빈도 ≥ 일 3회 | SRE 알람 + 근본 원인 조사 |
| Claude API 월 비용 한도 ≥ 95% | PUBLIC·RESTRICTED → 로컬 전환으로 감량 |
| Parser 지연 p95 > 1.5s | 소비자 GPU에서 A100으로 승격 |

### 4.2 등급 상향 이벤트

문서 내용에 다음 키워드 감지 시 **자동 등급 상향 후 사용자 확인:**

- "국가 안보", "방산", "NIS", "대외비", "극비", "특정 비공개"
- 또는 첨부 문서가 암호화/DRM 보호 상태

→ 사용자 확인 전까지 **로컬 경로로 처리** (보수적 안전).

### 4.3 등급 불명확 시 기본값

security_tier 미지정 → **RESTRICTED 기본 적용** (보수적). 사용자에게 명시 요청.

---

## 5. PROV-O 감사 로그 설계

### 5.1 기록 필수 항목

모든 LLM 호출마다 다음을 Append-only로 기록:

```json
{
  "prov_id": "prov-2026-04-18-001234",
  "timestamp": "2026-04-18T14:35:22Z",
  "user_id": "hyunjaeho@tenopa.co.kr",
  "project_id": "proj-2026-042",
  "document_ids": ["doc-123", "doc-456"],
  "max_security_tier": "CONFIDENTIAL",
  "routing_decision": {
    "selected_model": "gemma-4-31b-moe-lora-v1.0",
    "adapter_version": "research_mgr_v1.0",
    "reason": "max_tier=CONFIDENTIAL → local_gemma required"
  },
  "abac_checks": {
    "subject_cleared": true,
    "env_ok": true,
    "action_allowed": true
  },
  "action": "summarize",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "citations": ["doc-123#p.3", "doc-456#p.7"],
  "confidence": 0.87,
  "hallucination_checks": {
    "schema_valid": true,
    "ontology_compliant": true,
    "citation_coverage": 0.95,
    "fact_check_passed": true
  }
}
```

### 5.2 저장소

- Hot: PostgreSQL `prov_routing_log` (최근 90일)
- Warm: S3 Standard-IA (90일~1년)
- Cold: S3 Glacier (1년~영구)

### 5.3 Append-only 보장

- DB 레벨: `INSERT ONLY`, `UPDATE`·`DELETE` 권한 박탈
- 파일 레벨: S3 Object Lock (Governance mode)
- 해시 체인: 각 레코드 `prev_hash` 필드로 무결성 검증

---

## 6. 위반 감지 및 대응

### 6.1 자동 감지 룰

| 유형 | 룰 | 대응 |
|---|---|---|
| **V1. 등급 위반 전송** | CONFIDENTIAL 데이터가 Claude API로 라우팅됨 | **즉시 차단** + SRE 페이징 + 감사 리포트 |
| **V2. ABAC 우회 시도** | 사용자가 clearance 없이 SECRET 액세스 | 액세스 차단 + 사용자 계정 일시 정지 |
| **V3. 로그 누락** | LLM 호출인데 PROV-O 레코드 없음 | Alert + 근본 원인 조사 |
| **V4. Rule Engine 우회 (CP3 위반)** | LLM이 EVM/TRL/CRL 판정 시도 | **Critical** — 즉시 롤백 + 특허 리스크 검토 |
| **V5. Citation 미포함** | factual claim에 출처 0건 | 재생성 강제 |
| **V6. 로컬 모델 외부 포트 노출** | Gemma 4 서빙 포트가 인터넷 노출 | 방화벽 자동 재설정 + 보안팀 에스컬레이션 |

### 6.2 감사 대응 절차

정부 R&D 감사·특허 방어 등 **외부 감사 요청 시:**

1. `prov_id` 범위로 Log Export (사용자·프로젝트 기준)
2. 해시 체인 무결성 증명서 동봉
3. ABAC 결정 근거 첨부
4. LLM 출력의 입출력 hash + 모델 버전 타임스탬프 포함
5. Anthropic Zero Data Retention 증빙 (Claude 경로 한정)

### 6.3 인시던트 플레이북

V1 (등급 위반) 발생 시:

```
T+0  자동 차단 + SRE 페이징
T+15 로그 보존 + 영향 범위 파악 (몇 건, 어떤 문서)
T+60 내부 보안위원회 소집
T+4h 외부 노출 여부 확인 (Anthropic DPA 기반 요청)
T+24h 사용자 통지 (프로젝트 소유자)
T+72h 재발방지 대책 수립 + 라우팅 룰 Patch
T+1W 감사 보고서 작성 + 이사회 보고
```

---

## 7. 배포·운영 토폴로지

### 7.1 네트워크 구성

```
[사용자 브라우저/CLI]
  ↓ HTTPS
[RAPai API Gateway (VPC)]
  ↓
[ABAC Decision Engine]
  ├─ PUBLIC·RESTRICTED 경로
  │   └─ [Claude API (Anthropic Cloud)] ← Outbound HTTPS only
  └─ CONFIDENTIAL·SECRET 경로
      ├─ [vLLM: Gemma 4 31B-MoE + LoRA] (내부 GPU 노드)
      ├─ [vLLM: EXAONE 4.0 32B] (백업 노드)
      └─ [vLLM: Gemma 4 4B Parser] (Edge 노드)
  ↓
[PROV-O Log Writer]
  ↓
[PostgreSQL + S3]
```

### 7.2 SECRET 등급 에어갭 모드

- 별도 네트워크 구획: Outbound 차단 (NIS·방산 등)
- 모델 가중치는 오프라인 복사본만 사용
- 로그 Export는 물리 매체 (USB 암호화)로만 가능

### 7.3 GPU 리소스 할당

| 노드 | GPU | 모델 | 용도 |
|---|---|---|---|
| GPU-PRIMARY-01 | A100 80GB ×2 | Gemma 4 31B-MoE + LoRA | 주력 서빙 |
| GPU-BACKUP-01 | A100 80GB ×2 | EXAONE 4.0 32B Dense | 백업·Phase 0 벤치 |
| GPU-PARSER-01 | A100 40GB ×1 | Gemma 4 4B + QLoRA | Parser 전용 |
| GPU-SMALL-01 | RTX 4090 ×2 | Task-Specific 5종 | 소형 모델 서빙 |

---

## 8. 라우팅 정확도 평가

### 8.1 메트릭 정의

| 메트릭 | 정의 | 목표 |
|---|---|---|
| **Routing Accuracy** | 올바른 등급·모델로 라우팅된 비율 | **100%** (등급 위반 시 Critical) |
| **ABAC 통과율** | 정당 요청의 허용 비율 | ≥ 99% |
| **Fallback 전환 시간** | 장애 감지 → 전환 완료 | p95 < 30초 |
| **Over-classification 율** | 낮은 등급인데 상향 처리한 비율 | ≤ 5% (허용) |
| **Under-classification 율** | 높은 등급인데 하향 처리한 비율 | **0%** (Critical) |

### 8.2 평가 방법

- 월 1회 합성 테스트 케이스 200건 (보안등급·문서 조합) 주입
- Under-classification 발생 시 즉시 롤백
- PROV-O 로그에서 실제 위반 사례 분석 (주 1회)

---

## 9. 운영 대시보드

Grafana 패널:

| 패널 | 메트릭 |
|---|---|
| 등급별 트래픽 분포 | PUBLIC / RESTRICTED / CONFIDENTIAL / SECRET 비율 |
| 모델별 호출량 | Claude / Gemma 31B / EXAONE / Parser |
| 라우팅 위반 건수 | V1~V6 일별 집계 |
| Fallback 발동 빈도 | 일/주 단위 |
| Claude API 비용 | 실시간 USD |
| ABAC 거부 사유 Top 5 | 권한·환경·액션 |
| PROV-O 해시 무결성 | 일별 체크 결과 |

---

## 10. 비상 운영 시나리오

### 10.1 Claude API 장기 장애 (>24h)

- PUBLIC·RESTRICTED 전량 로컬 Gemma 4 31B-MoE로 라우팅
- 성능 저하 공지 + 비용 재산정
- GPU 용량 임시 증설 (클라우드 Spot)

### 10.2 GPU 화재·물리 장애

- GPU-BACKUP-01 (EXAONE 4.0) 즉시 활성화
- 장애 노드 복구 전까지 CONFIDENTIAL·SECRET 요청 Queue 대기
- PI에게 지연 통지

### 10.3 법무 이슈 (Gemma 라이선스 강제 변경)

- 본 라우팅 문서를 24시간 내 재수정
- Primary를 EXAONE 4.0으로 전환 (LG 상용협약 전제)
- ADR-002 결정 13 재검토 Revisit Trigger 발동

### 10.4 Anthropic DPA 해지 시

- PUBLIC·RESTRICTED도 로컬 전환 검토
- 사용자 통지 + 대체 API (Azure OpenAI 등) 검증

---

## 11. 정책 리뷰 주기

| 주기 | 리뷰 항목 |
|---|---|
| **주 1회** | PROV-O 위반 리포트 리뷰 |
| **월 1회** | 라우팅 정확도 합성 테스트 실시 + 리포트 |
| **분기 1회** | 등급별 트래픽 분포 점검 + 비용 최적화 |
| **반기 1회** | ABAC 룰 재검토 + Subject clearance 재인증 |
| **연 1회** | 외부 보안 감사 + 펜 테스트 + 본 문서 전면 개정 |

---

## 12. 참조 문서

- `decisions/002-ai-model-architecture.md` — 결정 13 원문
- `llm/01-model-selection.md` — 모델 선정 근거
- `llm/03-evaluation-framework.md` — 평가 메트릭
- `system/02-specialized-ai-model.md` — 5-Tier 아키텍처
- `특허관련 문서/RD_AI_에이전트_길목특허_명세서_v3.md` — CP3·CP5

---

## 13. 변경 이력

| 버전 | 일자 | 변경 사항 |
|---|---|---|
| 1.0 | 2026-04-18 | 최초 작성 (ADR-002 결정 13 + v2.9 Section 19.2 계승) |

---

**이 문서의 한 줄 요약**
"PUBLIC·RESTRICTED = Claude Sonnet 4.6 / CONFIDENTIAL·SECRET = 로컬 Gemma 4 31B-MoE + LoRA (백업 EXAONE 4.0) / Parser = Gemma 4 4B + QLoRA. ABAC 4속성 의무 + PROV-O Append-only 감사 + V1~V6 위반 자동 감지. Under-classification 발생 시 Critical 롤백."
