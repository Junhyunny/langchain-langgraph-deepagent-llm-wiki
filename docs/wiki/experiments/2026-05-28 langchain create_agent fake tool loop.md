---
type: experiment
framework:
  - LangChain
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-28
sources:
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-agents-factory-2026-05-28
  - langchain-agents-middleware-types-2026-05-28
---

# 2026-05-28 LangChain create_agent fake tool loop

## Goal

`langchain.agents.create_agent()`가 tool call과 middleware hook을 실제 실행 중 어떻게 처리하는지 API key 없이 확인한다.

## Setup

Code:

- `examples/langchain_core/08_create_agent_fake_tool_loop.py`

Command:

```bash
.venv/bin/python examples/langchain_core/08_create_agent_fake_tool_loop.py
```

## Expected Behavior

- 첫 번째 model call은 `lookup_topic` tool call을 가진 `AIMessage`를 반환한다.
- `ToolNode`가 `lookup_topic`을 실행해 `ToolMessage`를 추가한다.
- 두 번째 model call은 final `AIMessage`를 반환한다.
- `before_agent`와 `after_agent`는 전체 실행 전후에 한 번씩만 실행된다.
- `before_model`, `wrap_model_call`, `after_model`은 모델 호출마다 실행된다.
- `wrap_tool_call`은 ToolNode의 tool 실행을 감싼다.

## Actual Behavior

Message sequence:

1. `HumanMessage`
2. `AIMessage` with `lookup_topic` tool call
3. `ToolMessage(name="lookup_topic")`
4. final `AIMessage`

Middleware event sequence:

1. `before_agent`
2. first `before_model`
3. first `wrap_model_call:before`
4. first `wrap_model_call:after`
5. first `after_model`
6. `wrap_tool_call:before`
7. `wrap_tool_call:after`
8. second `before_model`
9. second `wrap_model_call:before`
10. second `wrap_model_call:after`
11. second `after_model`
12. `after_agent`

`bind_tools()` was called twice with `["lookup_topic"]`: once for each model call.

## Observations

- The experiment confirms the source reading: `create_agent()` builds a LangGraph loop, not a classic imperative `while` loop.
- `bind_tools()` is deliberately late-bound. Middleware can alter `request.tools` inside `wrap_model_call`, and the final bound model reflects that runtime request.
- `before_agent` is excluded from the tools-to-model loop. Tool execution returns to the loop entry node, which starts at `before_model` when that hook exists.
- `after_agent` runs once after the loop decides there are no remaining tool calls.

## Related Pages

- [[LangChain create_agent flow]]
- [[Tool Calling]]
- [[StateGraph]]
- [[2026-05-28 deepagents tool call and filesystem]]

## Sources

- `langchain-source-create-agent-factory-2026-05-23`
- `langchain-agents-factory-2026-05-28`
- `langchain-agents-middleware-types-2026-05-28`
