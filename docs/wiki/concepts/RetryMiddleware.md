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

# RetryMiddleware

## Summary

LangChain 빌트인 재시도 미들웨어 2종:
- **[[ModelRetryMiddleware]]** — 모델 호출(`wrap_model_call`) 실패 시 재시도
- **[[ToolRetryMiddleware]]** — 도구 실행(`wrap_tool_call`) 실패 시 재시도

두 클래스는 공통 유틸리티 `_retry.py`를 공유한다.

## Why It Matters

실제 에이전트 배포 환경에서 모델 API는 Rate Limit, Timeout, 일시적 서버 오류로 실패할 수 있고, 도구(웹 검색, DB 쿼리 등)도 네트워크 오류로 실패한다. 재시도 미들웨어는 이런 일시적 오류를 자동으로 처리해 에이전트의 내결함성을 높인다.

## Key Concepts

- [[AgentMiddleware]] — `wrap_model_call` / `wrap_tool_call` 훅
- [[ModelFallbackMiddleware]] — 재시도 대신 다른 모델로 전환
- Exponential Backoff — 지수 백오프로 재시도 간격 증가
- Thundering Herd — Jitter(±25%)로 동시 재시도 분산

---

## 공통 유틸리티: `_retry.py`

### 타입 정의

```python
RetryOn = tuple[type[Exception], ...] | Callable[[Exception], bool]
OnFailure = Literal["error", "continue"] | Callable[[Exception], str]
```

### `calculate_delay(retry_number, *, backoff_factor, initial_delay, max_delay, jitter)`

```
delay = initial_delay * (backoff_factor ** retry_number)
delay = min(delay, max_delay)
if jitter: delay += random.uniform(-delay*0.25, delay*0.25)
```

| 파라미터 | 역할 |
|----------|------|
| `backoff_factor=0.0` | 상수 딜레이 (지수 증가 없음) |
| `max_delay` | 딜레이 상한선 (기본 60초) |
| `jitter=True` | ±25% 랜덤 노이즈 → 동시 재시도 분산 |

### `should_retry_exception(exc, retry_on)`

- `retry_on`이 tuple → `isinstance(exc, retry_on)` 체크
- `retry_on`이 callable → `retry_on(exc)` 호출 결과로 판단

### `validate_retry_params()`

`max_retries < 0`, `initial_delay < 0`, `max_delay < 0`, `backoff_factor < 0`이면 `ValueError`.

---

## ModelRetryMiddleware

### 기본 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `max_retries` | 2 | 최대 재시도 횟수 (초기 시도 제외) |
| `retry_on` | `(Exception,)` | 재시도할 예외 타입 (기본: 모든 예외) |
| `on_failure` | `"continue"` | 소진 시 동작 |
| `backoff_factor` | 2.0 | 지수 백오프 배수 |
| `initial_delay` | 1.0 | 첫 재시도 딜레이(초) |
| `max_delay` | 60.0 | 딜레이 상한선(초) |
| `jitter` | `True` | ±25% 랜덤 노이즈 |

### 실행 흐름 (wrap_model_call)

```
for attempt in range(max_retries + 1):
    try:
        return handler(request)            # 모델 호출
    except Exception as exc:
        if not should_retry_exception(exc, retry_on):
            return _handle_failure(exc)    # 재시도 불가 → 즉시 실패 처리
        if attempt < max_retries:
            time.sleep(calculate_delay(attempt, ...))
        else:
            return _handle_failure(exc)    # 재시도 소진
```

총 시도 횟수 = `max_retries + 1` (초기 1회 + 재시도 N회)

### on_failure 동작

| 값 | 동작 |
|----|------|
| `"continue"` | `AIMessage(content="Model call failed after N attempts...")` 반환 → 에이전트 계속 실행 |
| `"error"` | 예외 re-raise → 에이전트 중단 |
| `Callable[[Exception], str]` | 반환값을 content로 한 `AIMessage` 반환 |

### retry_on 예시

```python
# 1. 특정 예외 타입만 재시도
ModelRetryMiddleware(retry_on=(ConnectionError, TimeoutError))

# 2. 상태 코드 기반 필터
from anthropic import APIStatusError
def should_retry(exc):
    if isinstance(exc, APIStatusError):
        return 500 <= exc.status_code < 600
    return False
ModelRetryMiddleware(retry_on=should_retry)
```

### 딜레이 계산 예시 (max_retries=3, initial_delay=1.0, backoff_factor=2.0, jitter=False)

| attempt | delay (jitter 없음) |
|---------|---------------------|
| 0 (첫 재시도) | 1.0 × 2⁰ = 1.0초 |
| 1 | 1.0 × 2¹ = 2.0초 |
| 2 | 1.0 × 2² = 4.0초 |

---

## ToolRetryMiddleware

`ModelRetryMiddleware`와 동일한 재시도 로직이지만 `wrap_tool_call` 훅을 사용한다.

### 추가 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `tools` | `None` | 재시도 대상 도구 목록 (None = 모든 도구) |

### on_failure 반환 타입 차이

| 미들웨어 | on_failure="continue" 반환 |
|---------|--------------------------|
| `ModelRetryMiddleware` | `AIMessage` |
| `ToolRetryMiddleware` | `ToolMessage(status="error")` |

### tools 필터

```python
# 특정 도구만 재시도
ToolRetryMiddleware(tools=["search_database", "fetch_url"])

# BaseTool 인스턴스로 지정
ToolRetryMiddleware(tools=[search_database_tool])
```

`_tool_filter` 리스트에 도구 이름을 저장. `_should_retry_tool(tool_name)`:
- `_tool_filter is None` → 모든 도구 재시도
- 그 외 → `tool_name in _tool_filter` 체크

### Deprecated on_failure 값

| Deprecated | 대체 |
|-----------|------|
| `"raise"` | `"error"` |
| `"return_message"` | `"continue"` |

### 실행 흐름 (wrap_tool_call)

```
tool_name = request.tool.name or request.tool_call["name"]
if not _should_retry_tool(tool_name):
    return handler(request)   # 필터 미포함 → 패스스루

for attempt in range(max_retries + 1):
    try:
        return handler(request)
    except Exception as exc:
        ...  # ModelRetryMiddleware와 동일 로직
        # 실패 시 _handle_failure → ToolMessage(status="error")
```

---

## 함께 사용하는 패턴

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

agent = create_agent(
    model=model,
    tools=[search_tool, db_tool],
    middleware=[
        ModelRetryMiddleware(max_retries=3, retry_on=(ConnectionError,)),
        ToolRetryMiddleware(max_retries=2, tools=["db_tool"]),
    ],
)
```

미들웨어는 등록 순서대로 체인된다. 각각 독립적으로 `wrap_model_call` / `wrap_tool_call` 훅을 처리한다.

## Source Code References

- Repo: langchain (langchain-ai/langchain)
- Commit: UNKNOWN
- Files:
  - `langchain/agents/middleware/_retry.py` — 공통 유틸 (RetryOn, OnFailure, calculate_delay, should_retry_exception, validate_retry_params)
  - `langchain/agents/middleware/model_retry.py` — ModelRetryMiddleware (312 lines)
  - `langchain/agents/middleware/tool_retry.py` — ToolRetryMiddleware (403 lines)

## Tests

- TBD — `.venv` 내 패키지이므로 upstream 테스트 확인 필요

## Related Pages

- [[ModelFallbackMiddleware]] — 재시도 대신 다른 모델로 전환
- [[PIIMiddleware]] — `before_model` / `after_model` 훅 사용 예
- [[SummarizationMiddleware]] — `before_model` 훅으로 메시지 압축
- [[LLMToolSelectorMiddleware]] — `wrap_model_call` 훅으로 도구 필터링
- [[AgentMiddleware]] — 훅 인터페이스 정의

## Open Questions

- `ModelRetryMiddleware` + `ModelFallbackMiddleware` 조합 시 어떤 미들웨어가 먼저 실행되는가? (등록 순서 의존성 확인 필요)
- `retry_on=should_retry` callable에서 비동기 callable은 지원되는가?
- `ToolRetryMiddleware`가 `Command` 반환 도구와 함께 동작할 때 재시도 후 `Command` 반환은 어떻게 처리되는가?

## Sources

- `langchain-source-builtin-middleware-2026-05-25`

## Verified

- `_generate` 오버라이드로 모델 실패 시뮬레이션 → `attempts = max_retries + 1` 확인 ✅
- `on_failure="continue"` → `AIMessage` 반환, 에이전트 계속 실행 ✅
- `on_failure="error"` → 예외 re-raise ✅
- `ToolRetryMiddleware` 도구 2회 실패 후 3번째 성공 → `tool_calls=3` 확인 ✅
- `ModelFallbackMiddleware` primary 실패 → fallback 응답 ✅ (예제 `07_retry_fallback_middleware.py`)
