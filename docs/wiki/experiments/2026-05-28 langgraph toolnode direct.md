---
type: experiment
framework:
  - LangGraph
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-28
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
  - langchain-agents-factory-2026-05-28
---

# 2026-05-28 LangGraph ToolNode direct

## Goal

`ToolNode`를 LangGraph graph 안이 아니라 단독 runnable로 직접 실행해 입력/출력 형태, `tools_condition()` 라우팅, `wrap_tool_call` request override 패턴을 확인한다.

## Setup

Code:

- `examples/langgraph_core/08_toolnode_direct.py`

Command:

```bash
.venv/bin/python examples/langgraph_core/08_toolnode_direct.py
```

## Expected Behavior

- state dict 입력은 `{"messages": [ToolMessage(...)]}`를 반환한다.
- message list 입력은 `[ToolMessage(...)]`를 반환한다.
- direct tool call list 입력은 현재 로컬 버전에서 `{"messages": [ToolMessage(...)]}`를 반환한다.
- `tools_condition()`은 마지막 `AIMessage`에 tool calls가 있으면 `"tools"`, 없으면 `"__end__"`를 반환한다.
- `wrap_tool_call`은 `ToolCallRequest.override()`로 tool call args를 바꾼 뒤 `execute()`를 호출할 수 있다.

## Actual Behavior

- state dict input:
  - `add_numbers(2, 3)` -> `ToolMessage(content="5", tool_call_id="state-call")`
  - output shape: dict with `messages`
- message list input:
  - `add_numbers(4, 5)` -> `ToolMessage(content="9", tool_call_id="list-call")`
  - output shape: list
- direct tool calls input:
  - `add_numbers(6, 7)` -> `ToolMessage(content="13", tool_call_id="direct-call")`
  - output shape: dict with `messages`
- `tools_condition`:
  - with tool calls -> `"tools"`
  - without tool calls -> `"__end__"`
- wrapper experiment:
  - original args: `{"a": 2, "b": 3}`
  - wrapper changed `b` to `30`
  - result: `ToolMessage(content="32")`

## Observations

- `ToolNode` is a runnable boundary between message state and actual tool invocation.
- Its output shape depends on the parsed input type: graph state input returns a state update, message-list input returns a message list, and direct tool-call input currently returns a state update with `messages`.
- `wrap_tool_call` receives a `ToolCallRequest`, not raw args. The preferred modification pattern is `request.override(tool_call=modified_call)`.
- LangChain `create_agent()` uses this mechanism when it constructs `ToolNode(..., wrap_tool_call=wrap_tool_call_wrapper)`.
- Standalone `ToolNode.invoke()` in this local version needs a `Runtime` in config because the underlying runnable requires the `runtime` parameter. Inside a compiled graph, LangGraph supplies this automatically.

## Related Pages

- [[LangGraph ToolNode flow]]
- [[LangChain create_agent flow]]
- [[ToolNode in LangGraph vs LangChain create_agent]]
- [[Tool Calling]]

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
- `langchain-agents-factory-2026-05-28`
