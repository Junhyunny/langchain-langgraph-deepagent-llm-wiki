---
type: comparison
framework:
  - LangChain
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-28
sources:
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-agents-factory-2026-05-28
  - deepagents-venv-create-deep-agent-2026-05-28
---

# create_agent vs create_deep_agent

## Summary

`create_agent()`는 LangChain의 기본 agent factory다. 내부에서 LangGraph `StateGraph`를 구성하고 model/tool loop와 middleware hook 노드를 만든다.

`create_deep_agent()`는 이보다 한 층 위의 harness factory다. Deep Agents용 middleware stack, filesystem backend, subagent layer, summarization, prompt caching, `_DeepAgentState`를 조립한 뒤 최종적으로 `langchain.agents.create_agent()`에 위임한다.

## Decision Rule

- 낮은 수준에서 tool loop, middleware, state schema를 직접 통제하려면 [[LangChain]] `create_agent()`를 쓴다.
- 장기 작업, 가상 filesystem, subagents, context compaction, harness profile이 기본으로 필요하면 [[Deep Agents]] `create_deep_agent()`를 쓴다.

## Comparison

| 항목 | `create_agent` | `create_deep_agent` |
|------|----------------|---------------------|
| 소속 | LangChain | Deep Agents |
| 역할 | LangGraph agent graph factory | Deep Agents harness factory |
| 최종 반환 | `CompiledStateGraph` | `CompiledStateGraph` |
| 내부 graph 구성 | 직접 `StateGraph` 구성 | 직접 구성하지 않고 `create_agent()`에 위임 |
| 기본 tools | 사용자가 넘긴 tools + middleware tools | todo, filesystem, task, optional execute + 사용자 tools |
| middleware | 사용자가 명시 | Deep Agents 기본 stack + 사용자 middleware |
| state schema | 기본 `AgentState` 또는 사용자 `state_schema` | `_DeepAgentState` with `DeltaChannel(snapshot_frequency=50)` |
| filesystem | 기본 없음 | `StateBackend()` 기반 virtual filesystem |
| subagents | 직접 middleware/tool로 구성해야 함 | `SubAgentMiddleware`와 default general-purpose subagent |
| recursion_limit | `9_999` | `9_999` |

## Runtime Link

```text
create_deep_agent(...)
  ├─ resolve model/profile/backend
  ├─ build Deep Agents middleware stack
  ├─ build _DeepAgentState
  └─ create_agent(
       model,
       tools,
       middleware=deepagent_middleware,
       state_schema=_DeepAgentState,
       transformers=[SubagentTransformer factory],
     )
       └─ StateGraph.compile(...)
```

## Experiment Evidence

- [[2026-05-28 LangChain create_agent fake tool loop]] shows `create_agent()` model/tool loop, middleware hook order, and late `bind_tools()`.
- [[2026-05-28 deepagents tool call and filesystem]] shows `create_deep_agent()` running on top of the same agent loop while adding Deep Agents filesystem behavior.

## Open Questions

- Deep Agents `SubagentTransformer`가 `create_agent(transformers=...)` 안에서 streaming/tracing 이벤트를 어떻게 바꾸는가?
- Deep Agents middleware stack 중 어떤 hook이 runtime tool 목록을 가장 크게 바꾸는가?

## Sources

- `langchain-source-create-agent-factory-2026-05-23`
- `langchain-agents-factory-2026-05-28`
- `deepagents-venv-create-deep-agent-2026-05-28`
