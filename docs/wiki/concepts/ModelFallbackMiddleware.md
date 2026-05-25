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

# ModelFallbackMiddleware

## Summary

모델 호출 실패 시 미리 등록한 fallback 모델을 순서대로 시도하는 `wrap_model_call` 기반 미들웨어. [[RetryMiddleware|ModelRetryMiddleware]]가 동일 모델을 재시도하는 것과 달리, `ModelFallbackMiddleware`는 **다른 모델**로 전환한다.

## Why It Matters

- Primary 모델(GPT-4o 등)이 다운되거나 Rate Limit에 걸릴 때 자동으로 더 저렴하거나 가용한 모델로 전환
- 멀티 프로바이더 전략(OpenAI → Anthropic → Mistral 등) 구현 가능
- 에이전트 코드 변경 없이 장애 대응

## Key Concepts

- [[AgentMiddleware]] — `wrap_model_call` 훅
- [[RetryMiddleware]] — 동일 모델 재시도 (이 미들웨어와 조합 가능)
- `request.override(model=...)` — 동일 요청으로 다른 모델 실행

---

## 인터페이스

```python
ModelFallbackMiddleware(
    first_model: str | BaseChatModel,
    *additional_models: str | BaseChatModel,
)
```

- 첫 번째 인자가 `first_model` (필수)
- 이후 가변 인자로 추가 fallback 등록
- `str` 입력은 `init_chat_model(model_str)`로 초기화

```python
fallback = ModelFallbackMiddleware(
    "openai:gpt-4o-mini",           # 1순위 fallback
    "anthropic:claude-haiku-3-5",   # 2순위 fallback
)

agent = create_agent(
    model="openai:gpt-4o",          # primary (create_agent에 지정)
    middleware=[fallback],
)
```

---

## 실행 흐름 (wrap_model_call)

```python
def wrap_model_call(self, request, handler):
    try:
        return handler(request)                    # ① primary 모델 시도
    except Exception as e:
        last_exception = e

    for fallback_model in self.models:             # ② fallback 순서대로 시도
        try:
            return handler(request.override(model=fallback_model))
        except Exception as e:
            last_exception = e
            continue

    raise last_exception                           # ③ 모두 실패 → 마지막 예외 re-raise
```

| 단계 | 동작 |
|------|------|
| ① primary 실패 | fallback 목록으로 진입 |
| ② `request.override(model=fallback)` | 요청 내용(messages, tools 등)은 유지, 모델만 교체 |
| ③ 모두 실패 | `last_exception` re-raise (on_failure 없음) |

### `request.override(model=fallback_model)`의 의미

`ModelRequest`의 `model` 필드만 교체한 새 요청 객체를 생성. messages, tools, config 등 나머지는 동일하게 유지된다. → fallback 모델도 원래 요청과 동일한 컨텍스트로 호출됨.

### ModelRetryMiddleware와의 차이

| | ModelRetryMiddleware | ModelFallbackMiddleware |
|--|----------------------|------------------------|
| 전략 | 동일 모델 N번 재시도 | 다른 모델로 순서 전환 |
| 실패 처리 | on_failure → AIMessage 또는 re-raise | 마지막 예외 re-raise (항상) |
| 딜레이 | 지수 백오프 + jitter | 없음 (즉시 다음 모델) |
| 사용 목적 | 일시적 오류 | 모델 다운/성능 차이 |

---

## 조합 패턴

```python
# 권장: ModelRetryMiddleware를 먼저, FallbackMiddleware를 나중에
agent = create_agent(
    model="openai:gpt-4o",
    middleware=[
        ModelRetryMiddleware(max_retries=2, retry_on=(ConnectionError,)),
        ModelFallbackMiddleware("openai:gpt-4o-mini", "anthropic:claude-haiku-3-5"),
    ],
)
```

> ⚠️ 미들웨어 실행 순서는 등록 순서에 의존한다. ModelRetryMiddleware가 먼저라면 재시도 소진 후 FallbackMiddleware가 처리하는지, 아니면 FallbackMiddleware가 wrap 외부에서 동작하는지 확인 필요.
> **Status: 미검증** — open question 참고.

---

## 주의 사항

- **on_failure 없음**: `ModelRetryMiddleware`와 달리 모든 모델 실패 시 예외를 re-raise한다. 에러 처리가 필요하면 `ModelRetryMiddleware(on_failure="continue")`와 조합할 것.
- **비용**: fallback 체인이 길수록 추가 API 비용 발생. 필요한 최소 fallback만 등록.
- **rate limit 주의**: primary와 동일 프로바이더의 다른 모델을 fallback으로 쓰면, 프로바이더 전체 장애 시 fallback도 실패한다.

## Source Code References

- Repo: langchain (langchain-ai/langchain)
- Commit: UNKNOWN
- Files:
  - `langchain/agents/middleware/model_fallback.py` (138 lines)
    - `ModelFallbackMiddleware.__init__`: fallback 모델 목록 초기화 (`init_chat_model` 사용)
    - `wrap_model_call`: primary → fallbacks 순서 실행
    - `awrap_model_call`: async 버전 (동일 로직)

## Tests

- TBD

## Related Pages

- [[RetryMiddleware]] — 동일 모델 재시도 (ModelRetry + ToolRetry)
- [[LLMToolSelectorMiddleware]] — `wrap_model_call` 사용 예
- [[AgentMiddleware]] — 훅 인터페이스

## Open Questions

- `ModelRetryMiddleware` + `ModelFallbackMiddleware` 조합 시 어떤 미들웨어의 `wrap_model_call`이 외부를 감싸는가? (등록 순서에 따라 다름인지 확인 필요)
- `request.override(model=...)` 내부 구현: `ModelRequest`의 immutable copy 패턴인가, shallow copy인가?
- fallback 모델에 tools를 bind할 때 원본 `bind_tools` 설정이 그대로 전달되는가?

## Sources

- `langchain-source-builtin-middleware-2026-05-25`

## Verified

- Primary 모델 실패 → fallback 모델 응답 반환 ✅ (예제 `07_retry_fallback_middleware.py`)
- 모든 모델 실패 시 마지막 예외 re-raise ✅ (소스 코드 확인)
