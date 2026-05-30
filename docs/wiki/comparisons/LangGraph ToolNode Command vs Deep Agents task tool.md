---
type: comparison
framework:
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
  - deepagents-source-subagents-2026-05-23
---

# LangGraph ToolNode Command vs Deep Agents task tool

## Summary

LangGraph `ToolNode`의 `Command` 반환은 graph control/state update를 직접 표현한다. Deep Agents `task` tool은 parent agent가 subagent를 호출하기 위한 higher-level delegation tool이며, 내부적으로는 subagent 결과를 `Command(update=...)`로 parent state에 병합한다.

## Decision Rule

- 그래프 노드 이동, parent graph fan-out, reducer 병합 같은 control flow를 직접 설계하려면 LangGraph `ToolNode` + `Command`를 사용한다.
- parent agent가 독립 작업을 subagent에게 맡기고, 중간 context를 숨긴 채 최종 보고서만 받게 하려면 Deep Agents `task` tool을 사용한다.

## Comparison

| 항목 | LangGraph `ToolNode` + `Command` | Deep Agents `task` tool |
|------|----------------------------------|--------------------------|
| 추상화 수준 | low-level graph/runtime primitive | high-level subagent delegation |
| 호출 주체 | graph 안의 `ToolNode` | parent agent의 model/tool loop |
| 주요 반환 | `Command(update=...)`, `Command(goto=...)`, `Command(graph=Command.PARENT, ...)` | `Command(update={state_update, messages=[ToolMessage]})` |
| control flow | 정적 edge 없이 node 이동 가능, parent graph로 이동 가능 | parent agent loop로 결과 반환 |
| context isolation | 사용자가 state/schema/Send로 직접 설계 | `_EXCLUDED_STATE_KEYS`로 입력/출력 필터링 |
| 결과 형태 | state update, goto, Send fan-out 등 자유도 높음 | subagent 마지막 AI text 또는 structured response를 ToolMessage로 압축 |
| subagent 중간 메시지 | graph 설계에 따라 노출 가능 | parent에 직접 병합하지 않음 |
| 좋은 사용처 | custom graph orchestration, map-reduce, HITL 라우팅 | research delegation, context offloading, specialized agents |

## Tradeoffs

LangGraph 방식은 더 직접적이고 강력하지만, 상태 스키마와 routing을 직접 설계해야 한다. Deep Agents 방식은 subagent delegation을 즉시 사용할 수 있게 해주지만, parent graph의 임의 노드로 이동하는 제어권은 노출하지 않는다.

## Example Evidence

- [[2026-05-29 langgraph toolnode command outputs]]: `Command(update=...)`, `Command(goto=...)` 반환 확인.
- [[2026-05-30 langgraph toolnode parent command send]]: child `ToolNode`에서 `Command.PARENT + Send`로 parent collector fan-out 확인.
- [[2026-05-30 deepagents subagentmiddleware task tool]]: Deep Agents `task` tool이 subagent state isolation과 parent state merge를 수행하는 것 확인.
- [[2026-05-30 deepagents parallel task tool calls]]: Deep Agents 다중 `task` 호출이 병렬 실행되고, parent-visible 결과 순서는 tool call 순서를 따르는 것 확인.

## Decision Implications

- Deep Agents는 LangGraph 위에 만들어진 harness지만, subagent 사용자 경험은 graph node handoff보다 tool delegation에 가깝다.
- Deep Agents `task`는 [[Context Engineering]]을 위해 parent message history를 줄이는 데 초점이 있다.
- LangGraph `Command`는 runtime graph 제어에 초점이 있다.

## Open Questions

- Deep Agents `task` tool call 여러 개가 reducer 없는 동일 key를 업데이트하면 어떤 에러가 발생하는가?

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
- `deepagents-source-subagents-2026-05-23`
