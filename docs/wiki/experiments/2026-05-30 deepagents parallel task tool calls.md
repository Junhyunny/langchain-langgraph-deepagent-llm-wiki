---
type: experiment
framework:
  - Deep Agents
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - deepagents-source-subagents-2026-05-23
  - langgraph-prebuilt-tool-node-2026-05-27
---

# 2026-05-30 Deep Agents parallel task tool calls

## Goal

단일 parent `AIMessage`가 여러 `task` tool call을 반환할 때 Deep Agents subagent 호출이 병렬로 실행되는지, 그리고 parent state에는 어떤 순서로 병합되는지 확인한다.

## Setup

Code:

- `examples/deepagents_core/05_subagent_parallel_tasks.py`

Command:

```bash
.venv/bin/python examples/deepagents_core/05_subagent_parallel_tasks.py
```

## Expected Behavior

- parent model은 하나의 `AIMessage` 안에 `task` tool call 두 개를 반환한다.
- LangGraph `ToolNode`는 여러 tool call을 executor로 병렬 실행한다.
- `executor.map()`은 완료 순서가 아니라 입력 순서대로 output list를 만든다.
- 따라서 fast task가 먼저 끝나도 parent `ToolMessage`와 reducer state merge는 원래 tool call 순서를 따를 것으로 예상한다.

## Actual Behavior

실행 결과:

```text
subagent timeline:
  ~0.006s fast/slow start
  ~0.006s slow/fast start
  ~0.060s fast end
  ~0.261s slow end

parent messages:
  2. AIMessage: tool_calls=['call-slow:slow: ...', 'call-fast:fast: ...']
  3. ToolMessage: content='slow report finished after 0.25s'
  4. ToolMessage: content='fast report finished after 0.05s'

parent state:
  reports: ['slow-report', 'fast-report']
  todos: ['parent todo stays parent-owned']
```

## Observations

- slow와 fast subagent가 거의 동시에 시작했다. fast가 slow보다 먼저 끝났으므로 병렬 실행이 확인된다.
- parent `ToolMessage` 순서는 완료 순서가 아니라 원래 `AIMessage.tool_calls` 순서였다.
- `reports` state도 `['slow-report', 'fast-report']`로 병합되었다.
- `reports`는 `Annotated[list[str], add]` reducer를 사용했다. 여러 child가 같은 key를 업데이트하는 경우 reducer가 병합 의미를 정의한다.
- child `todos`는 parent `todos`를 덮어쓰지 않았다. `_EXCLUDED_STATE_KEYS` 출력 필터가 다중 task 호출에서도 동일하게 적용된다.

## Key Takeaways

- Deep Agents `task` tool의 다중 호출 병렬성은 `SubAgentMiddleware` 자체보다 LangGraph `ToolNode`의 multi tool call 실행 모델에서 나온다.
- 다중 subagent 호출 결과의 parent-visible 순서는 완료 시간이 아니라 tool call/output list 순서다.
- 여러 subagent가 같은 parent state key를 업데이트하려면 reducer를 명시하는 것이 안전하다.

## Related Concepts

- [[Deep Agents]]
- [[Subagents]]
- [[Tool Calling]]
- [[Deep Agents SubAgentMiddleware task tool flow]]
- [[LangGraph ToolNode flow]]

## Open Questions

- reducer가 없는 동일 key를 여러 subagent가 동시에 업데이트하면 어떤 에러 메시지가 발생하는가?
- async path(`ainvoke`)에서도 `asyncio.gather()` 결과 순서가 동일하게 tool call 순서를 보장하는가?

## Sources

- `deepagents-source-subagents-2026-05-23`
- `langgraph-prebuilt-tool-node-2026-05-27`
