---
type: flow
framework:
  - Deep Agents
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - deepagents-source-subagents-2026-05-23
---

# Deep Agents SubAgentMiddleware task tool flow

## Summary

`SubAgentMiddleware`는 subagent를 parent agent의 `task` tool로 노출한다. parent model이 `task`를 호출하면 middleware가 subagent state를 새로 만들고, subagent 결과를 `Command(update=...)`로 parent state에 되돌린다.

## Why It Matters

이 흐름은 [[Deep Agents]]의 [[Subagents]]가 단순한 문서상 기능이 아니라 [[Tool Calling]]과 LangGraph state update 위에서 구현된다는 점을 보여준다. 특히 context isolation, 결과 압축, state merge 경계를 이해하는 데 중요하다.

## Entry Point

```python
from deepagents.middleware import SubAgentMiddleware
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[],
    middleware=[
        SubAgentMiddleware(
            backend=StateBackend(),
            subagents=[compiled_subagent],
        )
    ],
)
```

`create_deep_agent()`를 쓰면 이 middleware 조립은 내부에서 수행된다. 이 페이지는 핵심 runtime 흐름을 보기 위해 `create_agent()`에 middleware를 직접 붙인 경로를 기준으로 설명한다.

## Call Path

```text
create_agent(..., middleware=[SubAgentMiddleware])
  ↓
SubAgentMiddleware.__init__()
  ↓
_get_subagents()
  - CompiledSubAgent이면 runnable.with_config(metadata/run_name) 적용
  - SubAgent이면 create_agent(model, tools, middleware, ...)로 subagent graph 생성
  ↓
_build_task_tool(subagent_specs)
  ↓
SubAgentMiddleware.tools = [task_tool]
  ↓
parent model bind_tools([... task ...])
  ↓
AIMessage(tool_calls=[task(description, subagent_type)])
  ↓
ToolNode executes task()
  ↓
_validate_and_prepare_state()
  ↓
subagent.invoke(subagent_state, subagent_config)
  ↓
_return_command_with_state_update()
  ↓
Command(update={...state_update, "messages": [ToolMessage(content)]})
  ↓
parent agent loop continues
```

## State Flow

입력 필터링:

```python
subagent_state = {
    k: v for k, v in runtime.state.items()
    if k not in _EXCLUDED_STATE_KEYS
}
subagent_state["messages"] = [HumanMessage(content=description)]
```

출력 필터링:

```python
state_update = {
    k: v for k, v in result.items()
    if k not in _EXCLUDED_STATE_KEYS
}
```

`_EXCLUDED_STATE_KEYS`:

```python
{
    "messages",
    "todos",
    "structured_response",
    "skills_metadata",
    "skills_load_errors",
    "memory_contents",
}
```

## Result Extraction

- `structured_response`가 있으면 JSON 직렬화 후 `ToolMessage.content`로 사용한다.
- 없으면 subagent `messages`를 뒤에서부터 읽어 마지막 non-empty `AIMessage.text`를 `ToolMessage.content`로 사용한다.
- subagent의 전체 message history는 parent에 직접 병합되지 않는다.

## Config Flow

parent runtime config 중 subagent로 전달되는 키:

- `callbacks`
- `tags`
- `configurable`

추가로 `configurable["ls_agent_type"] = "subagent"`가 설정된다.

의도적으로 전달하지 않는 키:

- `recursion_limit`
- `metadata`

## Verified Experiment

[[2026-05-30 deepagents subagentmiddleware task tool]]에서 API key 없이 fake model로 실행했다.

확인된 내용:

- parent model bound tools에 `task`가 포함된다.
- subagent state key는 `messages`, `project_id`만 관찰되었다.
- parent `todos`는 subagent에 전달되지 않았다.
- child `summary`는 parent state로 병합되었다.
- child `todos`는 parent state에 병합되지 않았다.
- subagent config에는 `ls_agent_type='subagent'`가 들어갔다.

[[2026-05-30 deepagents parallel task tool calls]]에서 단일 `AIMessage`의 `task` tool call 2개를 실행했다.

확인된 내용:

- slow/fast subagent가 같은 시점에 시작했고 fast가 먼저 끝났다. 즉 여러 `task` tool call은 병렬 실행된다.
- parent `ToolMessage` 순서는 완료 순서가 아니라 원래 `AIMessage.tool_calls` 순서였다.
- reducer가 붙은 `reports` state는 `['slow-report', 'fast-report']`로 병합되었다.
- child `todos` 출력은 다중 task 호출에서도 parent state에 병합되지 않았다.

## Source Code References

- Repo: `github.com/langchain-ai/deepagents`
- Commit: UNKNOWN
- Files:
  - `libs/deepagents/deepagents/middleware/subagents.py`

## Tests

- TBD: upstream Deep Agents 테스트에서 `SubAgentMiddleware` state filtering을 직접 검증하는 테스트 확인 필요.

## Related Pages

- [[Subagents]]
- [[Deep Agents]]
- [[Deep Agents create_deep_agent flow]]
- [[Tool Calling]]
- [[LangGraph ToolNode flow]]
- [[LangGraph ToolNode Command vs Deep Agents task tool]]

## Open Questions

- subagent runnable 예외는 `ToolMessage(status="error")`로 변환되는가, 아니면 graph 실행 예외로 전파되는가?
- reducer가 없는 동일 parent state key를 여러 subagent가 동시에 업데이트하면 어떤 에러가 발생하는가?
- async path(`ainvoke`)에서도 `asyncio.gather()` 결과 순서가 동일하게 tool call 순서를 보장하는가?

## Sources

- `deepagents-source-subagents-2026-05-23`
