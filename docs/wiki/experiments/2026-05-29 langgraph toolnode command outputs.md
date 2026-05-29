---
type: experiment
framework:
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-29
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
---

# 2026-05-29 LangGraph ToolNode command outputs

## Goal

`ToolNode`에서 도구 또는 `wrap_tool_call`이 `ToolMessage`가 아니라 `Command`를 반환할 때 state update와 routing이 어떻게 처리되는지 확인한다.

## Setup

Code:

- `examples/langgraph_core/09_toolnode_command_outputs.py`

Command:

```bash
.venv/bin/python examples/langgraph_core/09_toolnode_command_outputs.py
```

## Expected Behavior

- standalone `ToolNode.invoke()`는 `Command`를 적용하지 않고 반환한다.
- compiled graph 안에서는 `Command.update`가 state update로 적용된다.
- `wrap_tool_call`도 `Command(update=..., goto=...)`를 반환할 수 있다.
- current graph로 반환하는 `Command.update`에는 해당 tool call id와 matching되는 `ToolMessage`가 있어야 한다.

## Actual Behavior

- standalone `ToolNode`:
  - output type은 `list`
  - 내부에 `Command(update={"messages": [ToolMessage(...)], "audit": [...]})`가 들어 있다.
- compiled graph:
  - `Command.update["messages"]`가 state의 `messages`에 병합된다.
  - `Command.update["audit"]`가 reducer를 통해 `audit`에 병합된다.
  - 이후 정적 edge `tools -> after`가 실행된다.
- wrapper `Command(goto="after")`:
  - `tools -> after` 정적 edge 없이도 `after` 노드로 이동한다.
  - wrapper가 반환한 `ToolMessage`와 `audit` update가 state에 반영된다.
- invalid command:
  - matching `ToolMessage` 없이 `Command(update={"audit": [...]})`만 반환하면 `ValueError`가 발생한다.

## Key Takeaways

- `ToolNode`는 `Command`를 직접 적용하는 노드가 아니다. 단독 runnable로 실행하면 `Command`를 반환한다.
- compiled graph는 `Command`를 해석해 update/goto를 적용한다.
- current graph에 대한 tool `Command`는 message history의 tool-call consistency를 깨지 않도록 matching `ToolMessage`를 포함해야 한다.
- `wrap_tool_call`은 도구 실행을 감쌀 뿐 아니라, 도구 실행을 건너뛰고 직접 `Command`를 반환할 수도 있다.

## Related Pages

- [[LangGraph ToolNode flow]]
- [[ToolNode in LangGraph vs LangChain create_agent]]
- [[Tool Calling]]
- [[StateGraph]]

## Open Questions

- `Command(graph=Command.PARENT)`와 `Send` 조합은 parent graph에서 어떻게 병합되는가?
- LangChain `create_agent()` 안에서 `AgentMiddleware.wrap_tool_call`이 `Command(goto=...)`를 반환할 때 agent loop edge와 어떻게 상호작용하는가?

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
