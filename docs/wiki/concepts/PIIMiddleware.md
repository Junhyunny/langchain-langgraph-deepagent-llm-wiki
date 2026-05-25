---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-26
sources:
  - langchain-source-builtin-middleware-2026-05-25
---

# PIIMiddleware

## Summary

`PIIMiddleware`는 `langchain/agents/middleware/pii.py`에 정의된 빌트인 미들웨어다.
에이전트 대화에서 **개인식별정보(PII)를 탐지하고 설정된 전략으로 처리**한다.
이메일, 신용카드, IP, MAC 주소, URL 5가지 타입을 빌트인 지원하며, 커스텀 detector도 가능하다.

핵심 메커니즘: `before_model`(입력 필터링) + `after_model`(출력 필터링) 훅 사용.

- 파일: `langchain/agents/middleware/pii.py` (376 lines)
- 의존: `langchain/agents/middleware/_redaction.py` (454 lines)
- 상속: `AgentMiddleware[AgentState[ResponseT], ContextT, ResponseT]`

---

## 기본 사용법

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

# 이메일 탐지 후 리댁션 (기본)
agent = create_agent(
    "openai:gpt-5",
    middleware=[PIIMiddleware("email", strategy="redact")],
)

# 여러 타입, 다른 전략 조합
agent = create_agent(
    "openai:gpt-4o",
    middleware=[
        PIIMiddleware("credit_card", strategy="mask"),    # 신용카드 마스킹
        PIIMiddleware("url", strategy="redact"),           # URL 리댁션
        PIIMiddleware("ip", strategy="hash"),              # IP 해시화
    ],
)

# 커스텀 PII 타입 (regex)
agent = create_agent(
    "openai:gpt-5",
    middleware=[
        PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block"),
    ],
)
```

---

## 핵심 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `pii_type` | **필수** | 탐지할 PII 타입 (`"email"`, `"credit_card"`, `"ip"`, `"mac_address"`, `"url"` 또는 커스텀 문자열) |
| `strategy` | `"redact"` | 탐지된 PII 처리 방식 |
| `detector` | `None` (빌트인 사용) | 커스텀 detector 함수 또는 regex 문자열 |
| `apply_to_input` | `True` | 사용자 메시지 필터링 여부 |
| `apply_to_output` | `False` | AI 메시지 필터링 여부 |
| `apply_to_tool_results` | `False` | Tool 결과 메시지 필터링 여부 |

**기본값 주의**: `apply_to_output=False` — AI 응답의 PII는 기본적으로 필터링되지 않음.

---

## 미들웨어 이름 (name 프로퍼티)

```python
PIIMiddleware("email").name   # → "PIIMiddleware[email]"
PIIMiddleware("ip").name      # → "PIIMiddleware[ip]"
```

타입 정보가 이름에 포함되어 트레이싱/로깅 시 식별 용이.

---

## 동작 흐름 (before_model 훅)

```
@hook_config(can_jump_to=["end"])
before_model(state, runtime)
  │
  ├─ apply_to_input=False AND apply_to_tool_results=False → None 반환
  │
  ├─ [apply_to_input=True]
  │    ├─ 역방향 탐색으로 마지막 HumanMessage 찾기
  │    └─ _process_content(content) → 탐지 + 전략 적용
  │
  ├─ [apply_to_tool_results=True]
  │    ├─ 역방향 탐색으로 마지막 AIMessage 찾기
  │    └─ 그 이후 모든 ToolMessage에 _process_content() 적용
  │
  └─ 변경이 있으면 {"messages": new_messages} 반환, 없으면 None
```

---

## 동작 흐름 (after_model 훅)

```
after_model(state, runtime)
  │
  ├─ apply_to_output=False → None 반환
  │
  ├─ 역방향 탐색으로 마지막 AIMessage 찾기
  ├─ _process_content(AIMessage.content) → 탐지 + 전략 적용
  └─ 변경이 있으면 {"messages": new_messages} 반환, 없으면 None
```

**async 버전**: `abefore_model` → `self.before_model()` sync 위임, `aafter_model` → `self.after_model()` sync 위임.

---

## @hook_config(can_jump_to=["end"])

`before_model`에 `@hook_config(can_jump_to=["end"])`가 적용되어 있다.

- `strategy="block"` 사용 시: PII 탐지 → `PIIDetectionError` 발생
- `can_jump_to=["end"]` 설정 덕분에 에이전트가 "end" 노드로 점프 가능
- → **사용자 메시지에 PII가 있으면 에이전트 실행 자체를 중단**시킬 수 있음

```python
# block 전략: PII 탐지 즉시 에러 발생, 에이전트 종료
PIIMiddleware("email", strategy="block")
```

---

## 5가지 빌트인 PII 타입

| 타입 | 탐지 방법 | 예시 |
|------|-----------|------|
| `email` | regex | `user@example.com` |
| `credit_card` | regex + Luhn 알고리즘 검증 | `4111-1111-1111-1111` |
| `ip` | IPv4 regex + `ipaddress.ip_address()` 검증 | `192.168.1.1` |
| `mac_address` | regex (`XX:XX:XX:XX:XX:XX` 또는 `-` 구분자) | `00:1A:2B:3C:4D:5E` |
| `url` | 2-pass regex (scheme 있는 URL + bare URL) + urlparse 검증 | `https://example.com`, `www.example.com/path` |

**credit_card Luhn 검증**: 정규식 매치 후 Luhn 체크섬으로 실제 카드 번호 형식인지 추가 검증 → false positive 감소.

**url 2-pass 탐지**:
1. `https?://...` 형태 (scheme 있는 URL)
2. `www.example.com/path` 또는 `example.com/path` (bare URL) — `/` 포함 또는 `www.` 시작만 허용

---

## 4가지 처리 전략

| 전략 | 결과 예시 | 특징 |
|------|----------|------|
| `redact` | `[REDACTED_EMAIL]` | 완전 대체, 범용 |
| `mask` | `user@****.com` | 타입별 부분 마스킹, 가독성 유지 |
| `hash` | `<email_hash:a1b2c3d4>` | SHA256 앞 8자 결정론적 해시, 분석 목적 |
| `block` | `PIIDetectionError` 발생 | PII 자체를 거부 |

### mask 전략 타입별 포맷

```
email:        user@****.tld
credit_card:  ****-****-****-1234
ip:           *.*.*.4   (마지막 옥텟만 유지)
mac_address:  **:**:**:**:**:5E  (마지막 2자만 유지)
url:          [MASKED_URL]
custom:       ****1234  (마지막 4자 유지)
```

### 치환 순서 (역방향 치환)

모든 전략은 **매치를 역방향으로 정렬** (`sort(reverse=True)`) 후 치환:
→ 앞에서 치환하면 뒤 매치의 인덱스가 바뀌는 문제 방지.

---

## 커스텀 Detector

```python
# 1. Regex 문자열
PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block")

# 2. Callable (returns list[PIIMatch] or list[dict])
def my_detector(content: str) -> list[PIIMatch]:
    ...

PIIMiddleware("custom_id", detector=my_detector, strategy="redact")
```

커스텀 callable은 `_normalizing_detector` 래퍼로 감싸져 `value`/`text` 키 차이를 흡수.

`pii_type`이 빌트인이 아닌데 `detector=None`이면 초기화 시 `ValueError`.

---

## _redaction.py 구조

`PIIMiddleware`가 의존하는 내부 모듈:

```
_redaction.py
  ├─ PIIMatch (TypedDict)          ← type, value, start, end
  ├─ PIIDetectionError             ← block 전략 시 발생
  ├─ BUILTIN_DETECTORS (dict)     ← {"email": detect_email, ...}
  ├─ detect_email/credit_card/ip/mac_address/url
  ├─ apply_strategy()              ← 전략 디스패처
  ├─ _apply_redact/mask/hash_strategy()
  ├─ _passes_luhn()                ← 신용카드 Luhn 검증
  ├─ resolve_detector()            ← None/str/callable → Detector
  ├─ RedactionRule (dataclass)     ← .resolve() → ResolvedRedactionRule
  └─ ResolvedRedactionRule         ← .apply(content) → (new_content, matches)
```

---

## SummarizationMiddleware와 비교

| 구분 | `PIIMiddleware` | `SummarizationMiddleware` |
|------|----------------|--------------------------|
| 훅 | `before_model` + `after_model` | `before_model` |
| 추가 LLM 호출 | 없음 (regex/rule 기반) | 있음 (요약 모델) |
| 상태 변경 | 메시지 내용 일부 치환 | 메시지 히스토리 전체 재구성 |
| 초기화 검증 | `pii_type` 빌트인 여부 + detector | `trigger` 미설정 시 비활성 |
| block 전략 | `@hook_config(can_jump_to=["end"])` | 해당 없음 |

---

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN (.venv에서 읽음)
- Files:
  - `langchain/agents/middleware/pii.py` (376 lines)
    - `PIIMiddleware.__init__`: L100
    - `PIIMiddleware.name`: L156 (property)
    - `before_model` + `@hook_config(can_jump_to=["end"])`: L169
    - `after_model`: L286
  - `langchain/agents/middleware/_redaction.py` (454 lines)
    - `PIIMatch`: L20
    - `detect_email/credit_card/ip/mac_address/url`: L50–L206
    - `BUILTIN_DETECTORS`: L209
    - `apply_strategy`: L306
    - `_passes_luhn`: L222
    - `resolve_detector`: L339
    - `RedactionRule` / `ResolvedRedactionRule`: L397–L441

---

## Key Concepts

- [[LangChain create_agent flow]] — 미들웨어가 등록되는 시스템
- [[Guardrails]] — PII 필터링은 가드레일의 구체적 구현 예시
- [[Context Engineering]] — 입출력 컨텐츠 제어

---

## Open Questions

- `apply_to_tool_results=True` 사용 시 Tool 결과에 PII가 있으면 요약 등 다른 미들웨어에도 영향을 주는가?
- `strategy="hash"`로 같은 이메일이 여러 메시지에 걸쳐 나타나면 항상 같은 해시가 나오는가? (결정론적 — SHA256이므로 Yes)
- `before_model`과 `after_model` 모두 활성화할 때 동일 PII가 두 번 처리되는 경우는?

---

## Sources

- `langchain-source-builtin-middleware-2026-05-25`
