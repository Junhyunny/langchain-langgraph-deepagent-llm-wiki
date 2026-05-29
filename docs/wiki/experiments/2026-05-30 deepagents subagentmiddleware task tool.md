---
type: experiment
framework:
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - deepagents-source-subagents-2026-05-23
---

# 2026-05-30 Deep Agents SubAgentMiddleware task tool

## Goal

`SubAgentMiddleware`가 parent agent에 `task` tool을 추가하고, tool call 실행 중 parent state를 어떻게 subagent state로 변환하며, subagent 결과를 어떻게 parent state로 병합하는지 확인한다.

## Setup

Code:

- `examples/deepagents_core/04_subagent_middleware_task_tool.py`

Command:

```bash
.venv/bin/python examples/deepagents_core/04_subagent_middleware_task_tool.py
```

## Expected Behavior

- parent fake model은 `task(description, subagent_type)` tool call을 반환한다.
- `create_agent()`는 `SubAgentMiddleware.tools`에 들어 있는 `task` tool을 모델에 bind한다.
- compiled subagent는 parent message history가 아니라 task description 하나만 message로 받는다.
- parent state의 일반 키는 전달될 수 있지만 `_EXCLUDED_STATE_KEYS`에 포함된 키는 전달되지 않는다.
- subagent 결과는 `Command(update=...)`로 parent state에 병합되며, excluded key는 출력 병합에서도 제외된다.

## Actual Behavior

실행 결과:

```text
bound tools:
  ['task']

parent messages:
  1. HumanMessage: content='Research LangGraph checkpointing.'
  2. AIMessage: content=''
     tool_calls=[{'name': 'task', ...}]
  3. ToolMessage: content='Subagent report: project=llm-wiki, task=Explain why checkpointing matters in LangGraph.'
  4. AIMessage: content='Final: I used the researcher report.'

parent state updates:
  summary: 'researcher completed one isolated task'
  todos: ['parent todo should stay private from the subagent']

subagent observed:
  state keys: ['messages', 'project_id']
  messages: ['Explain why checkpointing matters in LangGraph.']
  ls_agent_type: 'subagent'
```

## Observations

- `task`는 parent model에 일반 tool처럼 노출된다.
- subagent state에는 `project_id`가 전달되었지만 parent `messages`와 `todos`는 전달되지 않았다.
- subagent가 반환한 `summary`는 parent state에 병합되었다.
- subagent가 반환한 `todos`는 parent state의 기존 값으로 남았다. 즉 child `todos`는 병합되지 않았다.
- subagent invoke config에는 `configurable["ls_agent_type"] = "subagent"`가 들어간다.

## Key Takeaways

- Deep Agents의 subagent는 LangGraph의 parent graph node로 직접 이동하는 방식이 아니라, parent agent의 tool loop 안에서 `task` tool로 호출된다.
- `SubAgentMiddleware`의 context isolation은 문서적 개념이 아니라 `_EXCLUDED_STATE_KEYS` 기반의 입력/출력 필터링으로 구현된다.
- parent는 subagent의 전체 중간 메시지를 보지 않는다. 마지막 AI text가 `ToolMessage` content로 압축되어 parent message history에 들어간다.

## Related Concepts

- [[Deep Agents]]
- [[Subagents]]
- [[Tool Calling]]
- [[Context Engineering]]
- [[Deep Agents SubAgentMiddleware task tool flow]]

## Open Questions

- subagent runnable이 예외를 던질 때 parent agent에는 error `ToolMessage`가 남는가, 아니면 graph 실행이 실패하는가?
- 단일 parent `AIMessage`가 여러 `task` tool call을 반환하면 실제 실행은 병렬 처리되는가?

## Sources

- `deepagents-source-subagents-2026-05-23`
