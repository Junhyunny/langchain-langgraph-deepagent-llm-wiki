---
type: experiment
framework:
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
---

# 2026-05-30 LangGraph ToolNode parent command send

## Goal

child graph 안의 `ToolNode`가 `Command(graph=Command.PARENT, goto=[Send(...)])`를 반환할 때 parent graph에서 어떤 노드가 어떤 입력으로 실행되는지 확인한다.

## Setup

Code:

- `examples/langgraph_core/10_toolnode_parent_command_send.py`

Command:

```bash
.venv/bin/python examples/langgraph_core/10_toolnode_parent_command_send.py
```

## Expected Behavior

- child graph의 tool이 parent graph를 대상으로 `Send("collector", {...})`를 반환한다.
- parent graph에는 정적 `child -> collector` edge가 없어도 `collector`가 실행된다.
- child tool call이 2개면 parent collector가 2번 실행된다.
- parent collector의 결과는 parent state reducer로 병합된다.

## Actual Behavior

실행 출력:

```text
collector input: {'item': 'alpha', 'source': 'child-tool'}
collector input: {'item': 'beta', 'source': 'child-tool'}
collected: ['child-tool:alpha', 'child-tool:beta']
```

관찰:

- parent graph에는 `START -> child`, `collector -> END` edge만 있었다.
- 정적 `child -> collector` edge 없이도 child `ToolNode`가 올린 parent `Send`가 collector를 실행했다.
- `ToolNode._combine_tool_outputs()`는 여러 tool call에서 나온 parent `Send` command들을 하나의 parent command로 병합한다.
- `Command(graph=Command.PARENT, goto=[Send(...)])`는 current graph `Command(update=...)`와 달리 matching `ToolMessage`를 요구하지 않았다.
- parent `messages`는 비어 있었다. parent command가 `goto`만 운반했고 parent state의 `messages`를 update하지 않았기 때문이다.

## Key Takeaways

- `Command.PARENT + Send`는 subgraph 내부에서 parent graph의 특정 노드를 동적으로 호출하는 fan-out 패턴이다.
- 이 패턴은 [[Subagents]]와 [[Handoffs]]를 이해할 때 중요하다. child graph가 결과를 단순 반환하지 않고 parent graph의 다른 노드로 작업을 넘길 수 있기 때문이다.
- current graph의 tool command는 tool-call consistency를 위해 matching `ToolMessage`가 필요하지만, parent graph 대상으로 보내는 `Send` command는 그 검증 경로와 다르게 동작한다.

## Related Pages

- [[LangGraph ToolNode flow]]
- [[Subagents]]
- [[Handoffs]]
- [[StateGraph]]

## Open Questions

- `Command(graph=Command.PARENT, update=...)`와 `goto=[Send(...)]`를 함께 반환하면 parent state update와 Send fan-out은 어떤 순서로 적용되는가?
- parent collector가 다시 child graph를 호출하는 cyclic handoff 패턴에서 recursion limit과 checkpoint는 어떻게 작동하는가?

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
