---
type: flow
framework: Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-19
sources:
  - deepagents-source-graph-2026-05-19
---

# Deep Agents create_deep_agent flow

## 요약

`create_deep_agent()`는 middleware 스택을 조립한 뒤 `langchain.agents.create_agent`에 위임하는 "middleware 조립기"다.
LangGraph `StateGraph`를 직접 조립하지 않는다.

Source: `deepagents-source-graph-2026-05-19`

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
  5. AsyncSubAgentMiddleware      ← async subagents 있을 때만
  6. SummarizationMiddleware      ← 항상
  7. PatchToolCallsMiddleware      ← 항상

  [사용자 middleware] ← middleware= 파라미터

Tail stack:
  8. HarnessProfile.extra_middleware
  9. _ToolExclusionMiddleware     ← profile excluded_tools 있을 때만
 10. AnthropicPromptCachingMiddleware  ← 항상 (비-Anthropic no-op)
 11. MemoryMiddleware             ← memory 파라미터 있을 때만
 12. HumanInTheLoopMiddleware     ← interrupt_on 파라미터 있을 때만
```

Source: `deepagents-source-graph-2026-05-19`

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
  - `libs/deepagents/deepagents/middleware/subagents.py` — SubAgentMiddleware (미수집)
  - `libs/deepagents/deepagents/_subagent_transformer.py` — SubagentTransformer (미수집)
  - `libs/deepagents/deepagents/profiles/harness/harness_profiles.py` — HarnessProfile (미수집)

---

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
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나?
- `PatchToolCallsMiddleware`는 어떤 tool call을 어떻게 패치하나?
- `create_summarization_middleware`는 어떤 조건에서 summarization을 트리거하나? (문서 기준 85% 초과 확인됨, 소스 확인 필요)

---

## 관련 페이지

- [[Deep Agents]]
- [[Deep Agents Code Map]]
- [[Subagents]]
- [[LangGraph]]
- [[Tool Calling]]
- [[Checkpointing]]
- [[Context Engineering]]

---

## 소스

- `deepagents-source-graph-2026-05-19`
