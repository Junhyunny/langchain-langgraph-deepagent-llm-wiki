---
type: experiment
framework:
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-28
sources:
  - deepagents-venv-create-deep-agent-2026-05-28
---

# 2026-05-28 Deep Agents tool call and filesystem

## Goal

`create_deep_agent()`로 만든 agent가 실제 `invoke()` 중에 custom tool과 built-in filesystem tool을 어떻게 실행하는지 확인한다.

API key 없이도 런타임 경로를 검증하기 위해 LangChain의 fake chat model을 확장해 `bind_tools()`를 지원하게 만들었다. 모델 응답은 deterministic fake지만, agent loop, tool 실행, checkpointed state 갱신은 실제 Deep Agents/LangChain/LangGraph 경로를 탄다.

## Setup

Code:

- `examples/deepagents_core/03_tool_call_and_filesystem.py`

Command:

```bash
.venv/bin/python examples/deepagents_core/03_tool_call_and_filesystem.py
```

## Expected Behavior

- fake model이 `record_finding` tool call을 반환하면 ToolNode가 사용자 정의 tool을 실행하고 `ToolMessage`를 추가한다.
- fake model이 `write_file` tool call을 반환하면 Deep Agents built-in filesystem tool이 실행되고 `files` state가 갱신된다.
- 기본 `StateBackend`는 sandbox backend가 아니므로 `execute` tool은 모델에 노출되지 않아야 한다.

## Actual Behavior

- custom tool run:
  - `HumanMessage`
  - `AIMessage` with `record_finding` tool call
  - `ToolMessage(name="record_finding", content="recorded:LangGraph:durable graph runtime")`
  - final `AIMessage`
- filesystem run:
  - `AIMessage` with `write_file` tool call
  - `ToolMessage(name="write_file", content="Updated file /notes/langgraph.md", status="success")`
  - checkpointed state includes `files["/notes/langgraph.md"]`
- bound tools with default `StateBackend`:
  - `write_todos`
  - `ls`
  - `read_file`
  - `write_file`
  - `edit_file`
  - `glob`
  - `grep`
  - `task`
  - custom tools if supplied

`execute` was not present in the bound tool list.

## Observations

- `FilesystemMiddleware` creates an `execute` tool, and `_create_execute_tool()` has a runtime error response for non-sandbox backends.
- However, `FilesystemMiddleware.wrap_model_call()` checks whether the active backend supports `SandboxBackendProtocol`. If it does not, the middleware removes `execute` from `request.tools` before the model is bound.
- Therefore, under the default `StateBackend`, a normal model call should not see or call `execute`.
- `write_file` writes to Deep Agents' virtual filesystem backed by LangGraph state, not to the local project directory.

## Key Takeaways

- Deep Agents can be tested without a provider API key by passing a `BaseChatModel` fake that supports `bind_tools()`.
- This is enough to verify framework mechanics: tool binding, model/tool loop, `ToolMessage` insertion, checkpointed state, and middleware tool filtering.
- Real LLM behavior remains a separate experiment because tool selection quality and provider-specific tool call formatting are not covered by the fake model.

## Related Concepts

- [[Deep Agents]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Context Engineering]]

## Open Questions

- With a real sandbox backend, what exact `execute` result shape is stored in messages?
- With a real provider model, does the model reliably choose `write_file` under the default Deep Agents prompt?

## Sources

- `deepagents-venv-create-deep-agent-2026-05-28`
