---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-07-30
updated_at: 2026-07-30
langchain_version: 1.3.14
sources:
  - langchain-source-1-3-14-2026-07-30
---

# ToolErrorMiddleware

## Summary

`ToolErrorMiddleware`는 명시적으로 선택한 tool 실행 예외만
`ToolMessage(status="error")`로 바꾸는 `wrap_tool_call` 기반 미들웨어다.
처리하지 않은 예외는 그대로 전파한다.

## Why It Matters

도구 오류를 모델이 읽고 입력을 고쳐 재시도하게 만들 수 있지만, 내부 예외
메시지를 무조건 모델이나 사용자에게 노출하면 민감한 정보가 샐 수 있다.
이 API는 예외별로 무엇을 노출할지 opt-in handler에서 결정하게 한다.

## Details

```python
from langchain.agents.middleware import ToolErrorMiddleware

def on_error(exc, request):
    if isinstance(exc, ValueError):
        return f"{request.tool_call['name']} 입력을 수정해 다시 시도하세요."
    return None  # 처리하지 않음: 예외 전파

middleware = ToolErrorMiddleware(
    on_error,
    tools=["search_database"],
)
```

**검증됨 (1.3.14 tag):**

- `on_error`와 `aon_error` 중 하나 이상이 필수다.
- handler가 문자열 또는 content block 목록을 반환하면 error
  `ToolMessage`로 변환한다.
- handler가 `None`을 반환하면 원래 예외를 다시 던진다.
- `tools`로 적용 대상 이름을 제한할 수 있다.
- LangGraph interrupt와 parent command 같은 `GraphBubbleUp` 제어 신호는
  handler에 넘기지 않고 항상 전파한다.
- argument binding/validation 오류는 upstream `ToolNode`가 먼저 처리하므로
  이 미들웨어가 보지 않는다.
- 이 미들웨어는 retry하지 않는다. retry가 필요하면
  [[RetryMiddleware|ToolRetryMiddleware]]와 조합한다.

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: `185119f98e6286253a2326d7cf4f59592678023d`
- File: `libs/langchain_v1/langchain/agents/middleware/tool_error.py`

## Tests

- Upstream:
  `libs/langchain_v1/tests/unit_tests/agents/middleware/implementations/test_tool_error.py`

## Related Pages

- [[Tool Calling]]
- [[RetryMiddleware]]
- [[LangChain create_agent flow]]

## Open Questions

- `ToolRetryMiddleware(on_failure="error")`와 조합할 때 가장 안전한 ordering을
  실험으로 고정할 필요가 있는가?

## Sources

- `langchain-source-1-3-14-2026-07-30`
