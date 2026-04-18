# 규칙(Rules) vs 온톨로지(Ontology): 무엇이 다른가?

**사용자의 정확한 질문:**
> "인건비 편성지침, 연구비 정산지침 등이 규칙이고,  
> TRL, CRL, 프로젝트, 프로그램 등이 개념 정의인데,  
> 이것들이 온톨로지인가? 아니면 온톨로지가 뭔가 더 있나?"

**답: 이들은 온톨로지의 '부분'입니다. 하지만 온톨로지는 이것들을 '자동으로 적용'하도록 만든 것입니다.**

---

## 1️⃣ 규칙(Rules)만 있는 경우

### 예: 인건비 편성지침

```
❌ "규칙만" 제시:

정부 규칙 문서:
  "정부 R&D 프로젝트 인건비 편성 기준
   
   - 연구원급 급여: $50K/year
   - 박사급 급여: $80K/year
   - 석사급 급여: $50K/year
   - 학사급 급여: $30K/year
   - 인건비 비율: 전체 예산의 40-60%
   
   주의: 초과 근무비, 복리후생비 별도 계산"

사람의 역할:
  "이 규칙을 읽고 이해해야 함"
  "매번 프로젝트마다 이 규칙을 따라 계산"
  "계산 오류가 날 확률: 20-30%"

Agent의 역할:
  "이 규칙을 적용하라는 명령을 받으면 실행"
  "하지만 자동으로 적용할 수는 없음"
  "사람이 매번 '규칙을 적용해' 라고 명령해야 함"
  
결과:
  - 자동화율: 0% (항상 사람의 명령 필요)
  - 오류율: 20-30% (복잡한 계산 실수)
  - 실행 시간: 매번 1-2시간 (수동 계산)
```

### 문제점

```
프로젝트 50개:

  Project A: 인건비 편성 "규칙 적용" → 2시간 소요
  Project B: 인건비 편성 "규칙 적용" → 2시간 소요
  ...
  Project 50: 인건비 편성 "규칙 적용" → 2시간 소요
  
  총 시간: 50 × 2시간 = 100시간
  오류 수정: 50 × (25% 오류율) × 1시간 = 12.5시간
  
  총합: 112.5시간

그리고 여전히:
  - "왜 이렇게 했나?" 근거가 명확하지 않음
  - 다른 규칙들과의 상호작용 미고려
  - 프로젝트 특성별 예외 처리 복잡
```

---

## ✅ 온톨로지가 있는 경우

### 같은 인건비 편성, 하지만 "자동화"

```
✅ "온톨로지" 적용:

온톨로지의 구성:

Concepts:
  ProjectType: Government R&D
    └─ characteristics:
         - team_composition: ["PhD", "Master", "Bachelor"]
         - typical_team_size: "20-50"
         
Rules:
  SalaryScale:
    PhD: $80K
    Master: $50K
    Bachelor: $30K
    
  BudgetConstraints:
    salary_ratio: "40-60% of total budget"
    
Relations:
  ProjectType.team_composition ← applies → Rules.SalaryScale
  ProjectType.budget ← constrained_by → Rules.BudgetConstraints

Logic:
  IF ProjectType == "Government R&D" AND
     team_composition includes "PhD" 
  THEN
     apply_rule: SalaryScale.PhD
     validate: total_salary <= budget × 60%
     IF violation THEN warn_and_suggest_adjustment
```

### 자동 실행

```
Agent의 동작 (온톨로지 기반):

Step 1: 입력 분석
  "정부 R&D 프로젝트, 50명 팀, 예산 $5M"
  
Step 2: 온톨로지 매칭
  "정부 R&D 온톨로지 선택"
  
Step 3: 자동 인건비 편성
  온톨로지 규칙 자동 적용:
    - 팀 구성: PhD 5명, Master 20명, Bachelor 25명
    - 예상 인건비 계산:
      PhD: 5 × $80K = $400K
      Master: 20 × $50K = $1M
      Bachelor: 25 × $30K = $750K
      Total: $2.15M
      
Step 4: 자동 검증
    총 예산: $5M
    인건비 비율: $2.15M / $5M = 43% ✓
    제약 조건: 40-60% ✓
    Status: VALID
    
Step 5: 자동 근거 기록
    {
      "decision": "HR allocation",
      "rule_applied": "Government R&D Salary Scale",
      "reasoning": [
        "ProjectType: Government R&D",
        "Team composition: 5 PhD, 20 Master, 25 Bachelor",
        "Salary scale from Ontology v2.1",
        "Budget constraint: 43% (within 40-60% range)"
      ],
      "source": "Government R&D Ontology"
    }

결과:
  - 소요 시간: 1분 (자동)
  - 오류율: 0% (자동 검증)
  - 근거 추적: 완전함
  - 재사용: 즉시 가능
```

---

## 📊 비교표

| 측면 | 규칙만 | 온톨로지 |
|------|-------|---------|
| **형태** | 문서 (인건비 지침.pdf) | 구조화된 데이터 + 로직 |
| **적용** | 수동 (읽고 이해하고 실행) | 자동 (Agent가 자동 실행) |
| **소요 시간** | 2시간/프로젝트 | 1분/프로젝트 |
| **오류율** | 20-30% | 0% |
| **근거 기록** | 수동 ("인건비 지침에 따라") | 자동 (온톨로지 버전까지 기록) |
| **프로젝트 적응** | 수동 조정 | 자동 조정 |
| **다른 규칙과의 상호작용** | 없음 (각각 독립) | 통합 (온톨로지가 조정) |
| **확장성** | 선형 증가 | 거의 증가 없음 |

---

## 🎯 온톨로지 = "규칙들을 에이전트가 자동으로 적용할 수 있도록 구조화한 것"

### 또 다른 예: 성과지표(KPI)

#### ❌ 규칙만

```
정부 성과지표 가이드:

"정부 R&D 프로젝트의 성과지표:
 1. 논문 게재 건수 (목표: 10건)
 2. 특허 등록 건수 (목표: 5건)
 3. 기술이전 건수 (목표: 2건)
 4. 정책 제안 건수 (목표: 3건)"

사람이 해야 할 일:
  "이 가이드를 읽고... 우리 프로젝트에 맞게 적용해야 하나?"
  "우리 프로젝트는 기초연구인데 정책제안이 필요해?"
  "기술이전 목표가 2건이면 충분할까?"
  "논문은 10건인데, 우리 분야에서는 현실적인가?"

결과: 부적절한 KPI 설정 → 프로젝트 실패 판정
```

#### ✅ 온톨로지

```
온톨로지:

Concepts:
  ProjectType.BasicResearch
    └─ typical_outputs: [논문, 특허, 기초데이터]
    └─ NOT typical: [정책제안, 기술이전]

Rules:
  KPI_Template.BasicResearch
    Paper: "10-15건 (분야마다 다름)"
    Patent: "2-3건"
    Technology_Transfer: "1건 (선택사항)"
    Policy_Proposal: "불필요"

Logic:
  IF ProjectType == "BasicResearch"
  THEN
    use_KPI_Template: BasicResearch
    validate_applicability: [논문, 특허] (필수)
                            [기술이전] (선택)
                            [정책제안] (불적절 - 경고!)

Agent의 자동 동작:

입력: "기초연구 프로젝트"
  ↓
온톨로지 매칭: "BasicResearch"
  ↓
자동 KPI 선택: BasicResearch Template
  ↓
자동 검증:
  "정책제안"이 KPI에 포함되었나?
  YES → ⚠️ 경고: "기초연구에는 정책제안이 부적절합니다"
  제안: "논문, 특허, 기술이전만 포함하세요"
  ↓
최종 KPI:
  - 논문: 12건
  - 특허: 2건
  - 기술이전: 1건
  (+ 근거: BasicResearch Ontology v2.1)

결과: 적절한 KPI 자동 설정 → 현실적인 목표 → 프로젝트 성공
```

---

## 🔗 온톨로지의 3가지 층(Three Layers)

### Layer 1: Concepts (개념/용어)
```
"프로젝트", "프로그램", "TRL", "CRL", "정부R&D", "정책연구"
→ 무엇인가? 서로 어떻게 다른가?
```

### Layer 2: Rules (규칙/기준)
```
"인건비 편성지침", "보고 기준", "성과지표 정의"
→ 어떤 제약이 있는가?
→ 어떤 기준을 지켜야 하는가?
```

### Layer 3: Logic (의사결정 로직)
```
IF 프로젝트타입 == "정부R&D" THEN
  - 이 개념들을 사용하고
  - 이 규칙들을 적용하고
  - 이 KPI들을 추적해
  
→ Agent가 자동으로 실행할 수 있는 로직
```

---

## 💡 결론

```
규칙 ("인건비는 이렇게 편성해")
  +
개념 정의 (TRL, CRL 정의)
  +
자동 실행 로직 (IF-THEN 규칙)
  +
검증 메커니즘 (오류 감지 및 경고)
  =
온톨로지 (Agent가 자동으로 활용 가능한 구조)
```

**온톨로지 = "규칙과 개념을 AI가 자동으로 이해하고 적용할 수 있도록 구조화한 시스템"**

---

## ✅ 당신의 이해가 맞습니다

> "인건비 편성지침, 연구비 정산지침... TRL, CRL, 프로젝트, 프로그램..."

이것들이 **온톨로지의 구성 요소들**입니다.

온톨로지는 이것들을:
1. **구조화**하고 (Concepts + Rules)
2. **자동화**하고 (Logic)
3. **검증**하고 (Validation)
4. **추적**하는 (Tracing) 

시스템입니다.

그래서:
- 규칙만: 사람이 각 프로젝트마다 "이 규칙을 적용해"라고 명령 필요
- 온톨로지: Agent가 자동으로 프로젝트 타입을 인식하고 규칙을 적용
