---
type: source_summary
framework:
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-28
sources:
  - deepagents-venv-create-deep-agent-2026-05-28
---

# Deep Agents local venv create_deep_agent reading

## Summary

로컬 `.venv`에 설치된 `deepagents 0.6.3` 기준으로 `create_deep_agent()`는 Deep Agents 고유 런타임을 직접 만드는 함수가 아니라, middleware 스택과 `_DeepAgentState`를 조립한 뒤 `langchain.agents.create_agent()`에 위임하는 factory다.

## Source

- Package: `deepagents`
- Installed version: `0.6.3`
- Local files read:
  - `.venv/lib/python3.14/site-packages/deepagents/graph.py`
  - `.venv/lib/python3.14/site-packages/deepagents/middleware/filesystem.py`
  - `.venv/lib/python3.14/site-packages/deepagents/middleware/summarization.py`
  - `.venv/lib/python3.14/site-packages/deepagents/backends/state.py`
  - `.venv/lib/python3.14/site-packages/langgraph/types.py`

## Verified

- `create_deep_agent()`의 공개 파라미터는 `system_prompt=`를 사용한다. `instructions=`가 아니다.
- 반환은 `langchain.agents.create_agent(...).with_config(...)` 결과이며, `recursion_limit`는 `9_999`로 설정된다.
- `checkpointer`는 Deep Agents 내부에서 해석하지 않고 `create_agent()`에 그대로 전달된다.
- `checkpointer` 타입은 LangGraph의 `Checkpointer = None | bool | BaseCheckpointSaver` alias를 따른다. `True`, `False`, `None`의 의미는 LangGraph subgraph checkpointer inheritance 규칙에 속한다.
- `_DeepAgentState.messages`는 `DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)`로 오버라이드된다.
- 기본 backend는 `StateBackend()`이며, file state는 LangGraph config의 `CONFIG_KEY_READ` / `CONFIG_KEY_SEND`를 통해 읽고 쓴다.
- 기본 tool suite에는 `write_todos`, filesystem tools, `execute`, `task`가 포함된다.
- `FilesystemMiddleware`는 `execute` tool을 생성하지만, `wrap_model_call()`에서 backend가 `SandboxBackendProtocol`을 지원하지 않으면 `execute`를 `request.tools`에서 제거한 뒤 model binding으로 넘긴다.
- `_create_execute_tool()` 자체에도 non-sandbox backend에 대한 error `ToolMessage` 경로가 있지만, 기본 `StateBackend`의 일반 model call에서는 그 전에 tool 목록에서 필터링된다.
- 기본 general-purpose subagent는 같은 이름의 subagent가 명시되지 않았고 profile이 비활성화하지 않은 경우 자동 추가된다.

## Middleware Order

Main agent stack:

1. `TodoListMiddleware`
2. `SkillsMiddleware` if `skills` is provided
3. `FilesystemMiddleware`
4. `SubAgentMiddleware` if inline subagents are available
5. `SummarizationMiddleware`
6. `PatchToolCallsMiddleware`
7. `AsyncSubAgentMiddleware` if async subagents are provided
8. caller-provided `middleware`
9. harness profile `extra_middleware`
10. `_ToolExclusionMiddleware` if profile excludes tools
11. `AnthropicPromptCachingMiddleware`
12. `MemoryMiddleware` if `memory` is provided
13. `HumanInTheLoopMiddleware` if `interrupt_on` is provided

## Summarization Defaults

`compute_summarization_defaults(model)`:

- 모델 profile에 `max_input_tokens`가 있으면:
  - trigger: `("fraction", 0.85)`
  - keep: `("fraction", 0.10)`
  - truncate args trigger/keep도 같은 fraction 값
- 모델 profile에 max token 정보가 없으면:
  - trigger: `("tokens", 170000)`
  - keep: `("messages", 6)`
  - truncate args trigger/keep: `("messages", 20)`

Offloaded messages are written as markdown under `/conversation_history/{thread_id}.md`.

## Example Execution

검증 명령:

```bash
.venv/bin/python -m py_compile examples/deepagents_core/01_basic_deep_agent.py examples/deepagents_core/02_middleware_stack.py
.venv/bin/python examples/deepagents_core/01_basic_deep_agent.py
.venv/bin/python examples/deepagents_core/02_middleware_stack.py
.venv/bin/python examples/deepagents_core/03_tool_call_and_filesystem.py
```

결과:

- 구조 검사와 source introspection은 성공했다.
- API key가 없어 실제 LLM invocation은 건너뛰었다.
- fake chat model 기반 `invoke()`는 성공했다. custom tool call, built-in `write_file`, checkpointed `files` state 갱신, non-sandbox `execute` filtering을 확인했다.

## Still Unclear

- sandbox backend가 있을 때 실제 `execute` result payload가 어떤 message shape로 저장되는지는 별도 확인이 필요하다.
- `SubagentTransformer`가 streaming/tracing scope에 어떤 이벤트 구조를 붙이는지는 별도 소스 리딩이 필요하다.
- `MemoryMiddleware`가 `store=`와 어떤 관계를 갖는지는 별도 소스 리딩이 필요하다.

## Used By

- `docs/wiki/flows/Deep Agents create_deep_agent flow.md`
- `docs/wiki/experiments/2026-05-28 deepagents tool call and filesystem.md`
- `docs/wiki/_roadmap.md`
- `docs/wiki/_open_questions.md`

## Sources

- `deepagents-venv-create-deep-agent-2026-05-28`
