---
type: comparison
framework:
  - LangGraph
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-29
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
  - langchain-agents-factory-2026-05-28
---

# ToolNode in LangGraph vs LangChain create_agent

## Summary

`ToolNode` is a LangGraph prebuilt node that executes `AIMessage.tool_calls` and returns `ToolMessage` outputs.

LangChain `create_agent()` does not invent a separate tool executor. It creates a `ToolNode` internally and wires model -> tools -> model routing around it.

## Decision Rule

- 직접 LangGraph graph를 만들고 model/tool loop를 세밀하게 제어하려면 `ToolNode`를 직접 사용한다.
- 일반 agent loop, middleware hook, structured output, provider model binding까지 함께 쓰려면 LangChain `create_agent()`를 사용한다.

## Comparison

| 항목 | Direct `ToolNode` | LangChain `create_agent()` |
|------|-------------------|----------------------------|
| 소속 | LangGraph | LangChain |
| 역할 | Tool calls 실행 노드 | Agent graph factory |
| 입력 | state dict, message list, direct tool calls | agent state dict |
| 출력 | state update 또는 message list | final agent state |
| routing | 사용자가 `tools_condition`/edge 구성 | factory가 conditional edges 구성 |
| wrapper | `ToolNode(..., wrap_tool_call=...)` | `AgentMiddleware.wrap_tool_call`을 wrapper로 합성 |
| Command 반환 | compiled graph가 `update`/`goto` 적용 | 같은 ToolNode Command 경로를 사용하되 agent loop와 조합됨 |
| model binding | 없음 | `_get_bound_model()`에서 매 model call마다 `bind_tools()` |
| runtime config | 단독 실행 시 `Runtime` config 필요 | compiled graph가 자동 주입 |
| 사용 시점 | custom graph / tests / special control flow | standard ReAct-style agent |

## Runtime Link

```text
create_agent(...)
  ├─ normalize tools
  ├─ chain AgentMiddleware.wrap_tool_call
  ├─ ToolNode(tools=available_tools, wrap_tool_call=...)
  ├─ model node
  ├─ conditional edge: model/after_model -> tools or end
  └─ edge: tools -> loop_entry_node
```

## Experiment Evidence

- [[2026-05-28 langgraph toolnode direct]] shows direct `ToolNode` input/output shapes and `wrap_tool_call`.
- [[2026-05-29 langgraph toolnode command outputs]] shows `Command(update=...)`, `Command(goto=...)`, and matching `ToolMessage` validation.
- [[2026-05-28 langchain create_agent fake tool loop]] shows the same tool execution boundary inside `create_agent()`.

## Open Questions

- LangChain `create_agent()` 안에서 `AgentMiddleware.wrap_tool_call`이 `Command(goto=...)`를 반환할 때 agent loop edge와 어떻게 상호작용하는가?
- `ToolNode` direct tool calls input에서 state injection이 필요한 경우 `CONFIG_KEY_READ` 기반 state hydration이 어떤 graph context에서 안전하게 동작하는지 더 확인할 수 있다.

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
- `langchain-agents-factory-2026-05-28`
