---
type: flow
framework:
  - Deep Agents
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-06-06
sources:
  - deepagents-source-subagents-2026-05-23
---

# Deep Agents SubAgentMiddleware task tool flow

## Summary

`SubAgentMiddleware`는 subagent를 parent agent의 `task` tool로 노출한다. parent model이 `task`를 호출하면 middleware가 subagent state를 새로 만들고, subagent 결과를 `Command(update=...)`로 parent state에 되돌린다.

## Why It Matters

이 흐름은 [[Deep Agents]]의 [[Subagents]]가 단순한 문서상 기능이 아니라 [[Tool Calling]]과 LangGraph state update 위에서 구현된다는 점을 보여준다. 특히 context isolation, 결과 압축, state merge 경계를 이해하는 데 중요하다.

## Entry Point

**SubAgent (declarative) 방식:**

```python
from deepagents.middleware import SubAgentMiddleware
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[],
    middleware=[
        SubAgentMiddleware(
            backend=StateBackend(),
            subagents=[SubAgent(
                name="researcher",
                description="Searches the web and summarizes results.",
                system_prompt="You are a research specialist.",
            )],
        )
    ],
)
```

**CompiledSubAgent (pre-compiled runnable) 방식 (Verified):**

```python
# 직접 컴파일된 runnable을 subagent로 주입
SubAgentMiddleware(
    subagents=[CompiledSubAgent(
        name="specialist",
        description="...",
        runnable=my_precompiled_graph,  # state schema에 반드시 "messages" key 필요
    )]
)
```

- `CompiledSubAgent.runnable`의 상태 스키마에는 반드시 `messages` key가 포함되어야 한다.
- `structured_response`가 non-None이면 JSON 직렬화 후 `ToolMessage.content`로 반환된다.

Source: `deepagents-source-subagents-2026-05-23`

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

## Result Extraction (Verified)

결과 추출 우선순위:

1. **`structured_response`가 non-None** → JSON 직렬화:
   - Pydantic model → `model_dump_json()`
   - dataclass → `asdict()` → `json.dumps()`
   - 기타 → `json.dumps()`
2. **없으면** → `messages`를 역순으로 순회, 마지막 비어있지 않은 `AIMessage.text`

**Anthropic trailing empty AIMessage 방어 로직:**
- Anthropic은 `tool_use` 블록 뒤에 빈 `end_turn` AIMessage를 추가하는 경우가 있다.
- 역순 순회 시 빈 text AIMessage는 건너뛰고 마지막 non-empty AIMessage를 찾는다.

subagent의 전체 message history는 parent에 직접 병합되지 않는다.

Source: `deepagents-source-subagents-2026-05-23`

## wrap_model_call — System Prompt 조립 (Verified)

`SubAgentMiddleware.wrap_model_call`은 모델 호출 전에 system message에 task tool 사용법과 available subagent 목록을 append한다.

```python
def wrap_model_call(self, request, handler):
    if self.system_prompt is not None:
        new_system_message = append_to_system_message(
            request.system_message, self.system_prompt
        )
        return handler(request.override(system_message=new_system_message))
    return handler(request)
```

`self.system_prompt`에 포함되는 내용 (빌드 시점에 결정됨):

| 상수 | 역할 |
|------|------|
| `TASK_TOOL_DESCRIPTION` | `{available_agents}` placeholder 포함. task tool의 LLM 설명. |
| `TASK_SYSTEM_PROMPT` | task tool 사용 가이드라인 — 언제 써야 하는지/쓰지 말아야 하는지. |
| `DEFAULT_SUBAGENT_PROMPT` | 기본 subagent 지시사항. 중간 작업 결과가 아닌 최종 응답에 완전한 답 포함 요구. |
| `GENERAL_PURPOSE_SUBAGENT` | 기본으로 자동 추가되는 general-purpose subagent 스펙. |

Source: `deepagents-source-subagents-2026-05-23`

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

- 실험으로 주요 동작 확인: `_EXCLUDED_STATE_KEYS` 필터링, config 전파, 결과 추출 우선순위 — [[2026-05-30 deepagents subagentmiddleware task tool]], [[2026-05-30 deepagents parallel task tool calls]]
- upstream 소스 테스트 직접 확인은 미완료: `SubAgentMiddleware` state filtering 유닛 테스트 위치 미확인

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
