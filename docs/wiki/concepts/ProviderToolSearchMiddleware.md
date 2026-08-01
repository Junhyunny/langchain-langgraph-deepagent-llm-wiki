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

# ProviderToolSearchMiddleware

## Summary

`ProviderToolSearchMiddleware`는 많은 tool schema를 매 요청에 모두 보내는 대신
선택한 도구를 provider-native tool search 뒤로 지연 로딩하는 LangChain
미들웨어다.

## Why It Matters

도구가 많으면 schema 자체가 context와 요청 payload를 크게 만든다. 이
미들웨어는 검색 대상으로 지정한 `BaseTool`의
`extras["defer_loading"] = True`를 설정하고 provider 검색 도구를 함께 보내,
모델이 필요할 때만 전체 schema를 가져오게 한다.

## Details

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ProviderToolSearchMiddleware

agent = create_agent(
    "anthropic:claude-opus-4-8",
    tools=[get_weather, send_email, lookup_order],
    middleware=[
        ProviderToolSearchMiddleware(
            searchable_tools=["lookup_order"],
        )
    ],
)
```

**검증됨 (1.3.14 tag):**

- `wrap_model_call` / `awrap_model_call`에서 request를 준비한다.
- `searchable_tools`에는 tool 이름 또는 `BaseTool` 인스턴스를 줄 수 있다.
- 지정한 이름이 bound tool 목록에 없으면 `ValueError`다.
- 지연 tool이 하나도 없으면 provider 판별 없이 pass-through한다.
- 지연 tool이 있으면 bound model에서 provider를 추론한다.
- 태그 구현이 지원하는 provider는 Anthropic과 OpenAI다.
- 지원하지 않거나 provider를 판별할 수 없으면 조용히 fallback하지 않고
  `ValueError`를 낸다.

[[LLMToolSelectorMiddleware]]와 목적은 비슷하지만 실행 위치가 다르다.
LLM selector는 별도 모델 호출로 도구 목록을 먼저 줄이고,
`ProviderToolSearchMiddleware`는 provider의 server-side 검색 기능을 사용한다.

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: `185119f98e6286253a2326d7cf4f59592678023d`
- File:
  `libs/langchain_v1/langchain/agents/middleware/provider_tool_search.py`

## Tests

- Upstream:
  `libs/langchain_v1/tests/unit_tests/agents/middleware/implementations/test_provider_tool_search.py`

## Related Pages

- [[Tool Calling]]
- [[LLMToolSelectorMiddleware]]
- [[LangChain create_agent flow]]

## Open Questions

- provider별 검색 정확도와 schema/token 절감량은 실제 모델로 얼마나 차이 나는가?

## Sources

- `langchain-source-1-3-14-2026-07-30`
