---
type: flow
framework: Deep Agents
status: partial
confidence: high
last_reviewed: 2026-05-30
sources:
  - deepagents-source-graph-2026-05-19
  - deepagents-venv-create-deep-agent-2026-05-28
  - deepagents-docs-harness-2026-05-19
  - deepagents-source-subagents-2026-05-23
  - deepagents-source-patch-tool-calls-2026-05-23
---

# Deep Agents create_deep_agent flow

## 요약

`create_deep_agent()`는 middleware 스택을 조립한 뒤 `langchain.agents.create_agent`에 위임하는 "middleware 조립기"다.
LangGraph `StateGraph`를 직접 조립하지 않는다.

Source: `deepagents-source-graph-2026-05-19`, `deepagents-venv-create-deep-agent-2026-05-28`

---

## 진입점

```python
# libs/deepagents/deepagents/graph.py
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[my_tool],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

반환 타입: `CompiledStateGraph` (from `langgraph.graph.state`)
Source: `deepagents-source-graph-2026-05-19`

---

## 호출 경로 (소스코드 기반)

```
create_deep_agent(model, tools, ...)
    │
    ├─ 1. 모델 결정 (resolve_model)
    │       └─ model=None → ChatAnthropic("claude-sonnet-4-6") [deprecated 0.5.3]
    │
    ├─ 2. HarnessProfile 조회
    │       └─ _harness_profile_for_model(model, model_spec)
    │          → tool_description_overrides, excluded_tools, extra_middleware,
    │            base_system_prompt, system_prompt_suffix, general_purpose_subagent
    │
    ├─ 3. Backend 결정
    │       └─ backend=None → StateBackend()
    │
    ├─ 4. Subagent 처리
    │       ├─ AsyncSubAgent → async_subagents 목록
    │       ├─ CompiledSubAgent → inline_subagents (as-is)
    │       └─ SubAgent → middleware 조립 후 inline_subagents
    │
    ├─ 5. General-purpose subagent 자동 추가
    │       └─ "general-purpose" 이름의 subagent가 없으면 자동 추가
    │          (HarnessProfile이 disabled로 설정 시 생략)
    │
    ├─ 6. Main agent middleware 조립
    │       └─ (아래 middleware 순서 참조)
    │
    ├─ 7. System prompt 조립
    │       └─ USER → BASE (or profile CUSTOM) → profile SUFFIX
    │
    └─ 8. create_agent 위임
            └─ langchain.agents.create_agent(
                   model, system_prompt, tools, middleware,
                   state_schema=_DeepAgentState,
                   transformers=[_subagent_factory],
                   ...
               ).with_config({"recursion_limit": 9_999, ...})
```

Source: `deepagents-source-graph-2026-05-19`

---

## Middleware 조립 순서 (Main Agent)

```
Base stack (고정):
  1. TodoListMiddleware
  2. SkillsMiddleware             ← skills 파라미터 있을 때만
  3. FilesystemMiddleware         ← 항상 (required, 제거 불가)
  4. SubAgentMiddleware           ← inline subagents 있을 때만 (required)
  5. SummarizationMiddleware      ← 항상
  6. PatchToolCallsMiddleware      ← 항상
  7. AsyncSubAgentMiddleware      ← async subagents 있을 때만

  [사용자 middleware] ← middleware= 파라미터

Tail stack:
  8. HarnessProfile.extra_middleware
  9. _ToolExclusionMiddleware     ← profile excluded_tools 있을 때만
 10. AnthropicPromptCachingMiddleware  ← 항상 (비-Anthropic no-op)
 11. MemoryMiddleware             ← memory 파라미터 있을 때만
 12. HumanInTheLoopMiddleware     ← interrupt_on 파라미터 있을 때만
```

Source: `deepagents-source-graph-2026-05-19`, `deepagents-venv-create-deep-agent-2026-05-28`

---

## System Prompt 조립

```
final_system_prompt =
    USER (system_prompt 인자)
    + "\n\n"
    + BASE_AGENT_PROMPT (또는 HarnessProfile.base_system_prompt)
    + "\n\n"
    + HarnessProfile.system_prompt_suffix  (있을 때만)
```

- `system_prompt=None`이면 BASE만 사용
- `system_prompt`가 `SystemMessage`이면 content_blocks에 text block append (cache_control 보존)

Source: `deepagents-source-graph-2026-05-19`

---

## Local v0.6.3 실행 확인

2026-05-28 로컬 `.venv`에 설치된 `deepagents 0.6.3` 기준으로 다음 예제를 실행했다.

```bash
.venv/bin/python examples/deepagents_core/01_basic_deep_agent.py
.venv/bin/python examples/deepagents_core/02_middleware_stack.py
.venv/bin/python examples/research_agent_comparison/04_deep_agents_stub.py
```

확인한 내용:

- `create_deep_agent` 파라미터명은 `system_prompt=`다. `instructions=`가 아니다.
- `checkpointer`는 Deep Agents에서 별도 해석하지 않고 `langchain.agents.create_agent`로 전달된다.
- `Checkpointer` 타입 alias는 LangGraph의 `None | bool | BaseCheckpointSaver`다.
- API key가 없어 실제 LLM invocation은 건너뛰었다. 따라서 tool call 결과와 모델 응답 품질은 아직 미검증이다.

Source: `deepagents-venv-create-deep-agent-2026-05-28`

---

## 핵심 타입

### `_DeepAgentState`
```python
class _DeepAgentState(AgentState):
    messages: Required[Annotated[
        list[AnyMessage],
        DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)
    ]]
```
- `AgentState`를 상속
- `DeltaChannel`: checkpoint에 full snapshot 대신 delta만 저장 → O(N²) → O(N)
- `snapshot_frequency=50`: 50 steps마다 full snapshot

Source: `deepagents-source-graph-2026-05-19`

### `SubagentTransformer`
```python
subagent_names = frozenset(sub_agent_middleware.subagent_names ...)

def _subagent_factory(scope: tuple[str, ...] = ()) -> SubagentTransformer:
    return SubagentTransformer(scope, subagent_names=subagent_names)
```
- declared subagent 이름으로 subgraph 실행을 식별하는 scope-aware factory
- `create_agent`의 `transformers=` 파라미터로 전달
- 내부 구현은 `deepagents/_subagent_transformer.py` 확인 필요

Source: `deepagents-source-graph-2026-05-19`

---

## Source Code References

- **Repo:** `github.com/langchain-ai/deepagents`
- **Commit:** UNKNOWN (main branch, 2026-05-19 기준)
- **Files:**
  - `libs/deepagents/deepagents/graph.py` — 이 페이지의 주 소스
  - `libs/deepagents/deepagents/middleware/filesystem.py` — FilesystemMiddleware (미수집)
  - `libs/deepagents/deepagents/middleware/subagents.py` — SubAgentMiddleware (수집 완료: `deepagents-source-subagents-2026-05-23`)
  - `libs/deepagents/deepagents/_subagent_transformer.py` — SubagentTransformer (미수집)
  - `libs/deepagents/deepagents/profiles/harness/harness_profiles.py` — HarnessProfile (미수집)

Local venv files read (2026-05-28):

- `.venv/lib/python3.14/site-packages/deepagents/graph.py`
- `.venv/lib/python3.14/site-packages/deepagents/middleware/filesystem.py`
- `.venv/lib/python3.14/site-packages/deepagents/middleware/summarization.py`
- `.venv/lib/python3.14/site-packages/deepagents/backends/state.py`
- `.venv/lib/python3.14/site-packages/langgraph/types.py`

---

## SubAgentMiddleware task tool 흐름

`create_deep_agent()`는 inline subagent가 있을 때 `SubAgentMiddleware`를 main agent middleware stack에 넣는다. 이 middleware는 subagent를 `task` tool로 노출하고, parent model이 `task(description, subagent_type)`을 호출하면 subagent runnable을 실행한다.

세부 흐름은 [[Deep Agents SubAgentMiddleware task tool flow]]에 분리했다.

2026-05-30 실험에서 확인한 것:

- parent model bound tools에 `task`가 포함됨
- subagent는 parent message history가 아니라 task description 하나를 message로 받음
- parent `todos`는 child로 전달되지 않고, child `todos`도 parent로 병합되지 않음
- child `summary` 같은 일반 state update는 parent state로 병합됨

Experiment: [[2026-05-30 deepagents subagentmiddleware task tool]]

---

## Permissions 처리 흐름

*Source: `deepagents-docs-harness-2026-05-19`*

```
create_deep_agent(permissions=[rule1, rule2, ...])
    │
    └── FilesystemMiddleware ← permissions rules 주입
            │
            ├── tool 호출 시: rule 순서대로 first-match-wins 평가
            │       매칭 없으면 → 허용 (기본 allow)
            │
            └── subagent 생성 시: parent permissions 자동 상속
                    subagent 자체 permissions 선언 시 → 대체 (override)
```

- Sandbox backend의 `execute` tool에는 permissions **미적용** (임의 명령 실행 가능)
- `FilesystemMiddleware`는 `execute` tool을 생성하지만, 기본 `StateBackend`처럼 backend가 `SandboxBackendProtocol`을 지원하지 않으면 `wrap_model_call()`에서 `execute`를 model bind 전 `request.tools`에서 제거한다.
- deny rule을 allow rule 앞에 배치해야 first-match-wins 의미대로 동작함

## Skills / Memory 로딩 타이밍

*Source: `deepagents-docs-harness-2026-05-19`*

```
create_deep_agent(skills=[...], memory=[...])
    │
    ├── SkillsMiddleware (base stack #2)
    │       startup: frontmatter만 로드 (progressive disclosure)
    │       실행 중: 관련성 판단 시 전체 skill 로드
    │
    └── MemoryMiddleware (tail stack #11)
            항상 전체 로드 (no progressive disclosure)
```

- `SkillsMiddleware`는 base stack에, `MemoryMiddleware`는 tail stack에 위치
- Skills는 토큰 효율을 위해 lazy loading; Memory는 항상 context에 포함

## Verified Facts

- `create_deep_agent`는 `langchain.agents.create_agent`에 최종 위임한다.
  Source: `deepagents-source-graph-2026-05-19`
- 반환 타입은 `CompiledStateGraph`.
  Source: `deepagents-source-graph-2026-05-19`
- `FilesystemMiddleware`와 `SubAgentMiddleware`는 `excluded_middleware`로 제거할 수 없다. 시도 시 `ValueError`.
  Source: `deepagents-source-graph-2026-05-19`
- `AnthropicPromptCachingMiddleware`는 항상 추가된다 (비-Anthropic 모델에서 no-op).
  Source: `deepagents-source-graph-2026-05-19`
- `recursion_limit`는 9,999로 하드코딩된다.
  Source: `deepagents-source-graph-2026-05-19`
- 로컬 `deepagents 0.6.3` 기준으로 `execute` tool은 기본 `StateBackend`에서 model bind 전 필터링된다. `_create_execute_tool()`에는 non-sandbox backend error message 경로가 있지만, 일반 agent loop에서는 `wrap_model_call()`이 먼저 제거한다.
  Source: `deepagents-venv-create-deep-agent-2026-05-28`
- Subagent는 fresh context로 실행되며 stateless다. 단일 최종 보고서만 반환 가능.
  Source: `deepagents-docs-harness-2026-05-19`
- `PatchToolCallsMiddleware`는 `before_agent` hook에서 dangling tool call을 감지해 더미 `ToolMessage`로 채운다. LangGraph interrupt, 사용자 중단, 인자 파싱 실패 등으로 미응답 tool call이 히스토리에 남을 때 LLM 오류를 방지한다.
  Source: `deepagents-source-patch-tool-calls-2026-05-23`
- `create_summarization_middleware`는 모델 profile에 `max_input_tokens`가 있으면 `("fraction", 0.85)`에서 트리거하고 `("fraction", 0.10)`만 유지한다. profile token 정보가 없으면 `("tokens", 170000)`에서 트리거하고 최근 6개 메시지를 유지한다.
  Source: `deepagents-venv-create-deep-agent-2026-05-28`

---

## Interpretation

- `create_deep_agent`의 핵심 역할은 "middleware 조립기"다. LangGraph/LangChain을 직접 다루는 것이 아니라, 적절한 middleware 순서로 `create_agent`를 호출한다.
- `AnthropicPromptCachingMiddleware`가 항상 추가된다는 사실은 Anthropic 모델이 기본 타겟임을 시사한다.
- `_DeepAgentState`의 `DeltaChannel` 최적화는 long-running task에서 checkpointing이 실제 성능 병목임을 인식한 설계 결정이다.

---

## Superseded Notes

- **Old (스텁):** "실제 저장소 URL은 무엇인가?" — 미확인
- **New:** `github.com/langchain-ai/deepagents`, 파일 경로 `libs/deepagents/deepagents/graph.py`
  Source: `deepagents-source-graph-2026-05-19`

- **Old (스텁):** "내부적으로 LangGraph를 사용하는가?" — 가설
- **New:** `create_deep_agent`는 `langchain.agents.create_agent`에 위임. `CompiledStateGraph` 반환.
  Source: `deepagents-source-graph-2026-05-19`

- **Old (스텁):** "서브에이전트는 어떻게 표현되는가(도구인가? 노드인가? 별도의 그래프인가?)" — 가설
- **New:** `SubAgent` / `CompiledSubAgent` / `AsyncSubAgent` 세 TypedDict 타입. `SubAgentMiddleware`를 통해 `task` tool로 노출됨.
  Source: `deepagents-source-graph-2026-05-19`

---

## Open Questions

- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 어떻게 조립하나? (`langchain/agents/` 소스 확인 필요)
- `SubagentTransformer`는 scope를 어떻게 활용하나? streaming/tracing에서 어떤 역할인가?
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나?
- `DeltaChannel`의 `snapshot_frequency=50`이 long-running Deep Agents checkpoint 크기에 주는 실제 효과는 어느 정도인가? (의미는 확인됨: 50 writes마다 snapshot)
- ✅ `PatchToolCallsMiddleware` 역할 확인됨 — `before_agent` hook에서 dangling tool call (AIMessage에 tool_call이 있는데 그에 대응하는 ToolMessage가 없는 경우)을 감지해 더미 ToolMessage를 삽입. invalid_tool_call(인자 파싱 실패)과 cancelled(중단된 정상 호출) 두 케이스 처리. `Overwrite`로 state.messages 전체 교체. Source: `deepagents-source-patch-tool-calls-2026-05-23`
- sandbox backend에서 `execute` tool 호출 결과가 실제로 어떤 payload shape로 message history에 남는가?

---

## 관련 페이지

- [[Deep Agents]]
- [[Deep Agents Code Map]]
- [[Subagents]]
- [[LangGraph]]
- [[Tool Calling]]
- [[Checkpointing]]
- [[Context Engineering]]
- [[2026-05-28 deepagents tool call and filesystem]]

---

## 소스

- `deepagents-source-graph-2026-05-19`
- `deepagents-venv-create-deep-agent-2026-05-28`
