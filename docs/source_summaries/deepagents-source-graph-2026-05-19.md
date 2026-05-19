---
type: source_summary
source_id: deepagents-source-graph-2026-05-19
title: "Deep Agents — graph.py (create_deep_agent 소스코드)"
framework: Deep Agents
retrieved_at: 2026-05-19
status: verified
confidence: high
---

# Source Summary: Deep Agents — graph.py

## Source Info
- **Source ID:** `deepagents-source-graph-2026-05-19`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/graph.py
- **Retrieved At:** 2026-05-19
- **Version / Commit:** UNKNOWN (main branch)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->

### 모듈 위치 및 진입점
- 파일 경로: `libs/deepagents/deepagents/graph.py`
- 모듈 docstring: "Primary graph assembly module for Deep Agents"
- `create_deep_agent`가 이 파일의 핵심 진입점
- 반환 타입: `CompiledStateGraph` (from `langgraph.graph.state`)

### create_deep_agent 시그니처
```python
def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format: ResponseFormat[ResponseT] | ... | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```

### LangGraph / LangChain 위임 구조
- `create_deep_agent`는 최종적으로 `langchain.agents.create_agent`에 위임함
- `StateGraph`를 직접 조립하지 않음
- `create_agent` 호출 시 `state_schema=_DeepAgentState`, `transformers=[_subagent_factory]` 전달
- 반환값에 `.with_config({"recursion_limit": 9_999, ...})`를 적용

### _DeepAgentState
- `AgentState`를 상속
- `messages` 필드에 `DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)` 적용
- 목적: checkpoint 크기를 O(N²) → O(N)으로 감소

### BASE_AGENT_PROMPT
- `graph.py` 내 상수로 직접 정의됨 (클래스/외부 파일이 아님)
- System prompt 조립 순서 (원문 주석 기준):
  - `USER` → `BASE` (또는 HarnessProfile의 `CUSTOM`) → `SUFFIX`
  - `USER`가 항상 앞 (caller 우선), `SUFFIX`가 항상 마지막 (model attention 활용)
  - `USER`가 `SystemMessage`이면 기존 content_blocks에 text block을 append (cache_control 보존)

### Middleware 조립 순서 (소스 기준)
**Base stack (고정):**
1. `TodoListMiddleware`
2. `SkillsMiddleware` — `skills` 파라미터 제공 시에만
3. `FilesystemMiddleware`
4. `SubAgentMiddleware` — inline subagents가 있을 때만
5. `AsyncSubAgentMiddleware` — async subagents가 있을 때만
6. `create_summarization_middleware` (SummarizationMiddleware)
7. `PatchToolCallsMiddleware`

**사용자 middleware** — `middleware` 파라미터로 전달된 것

**Tail stack:**
8. HarnessProfile `extra_middleware`
9. `_ToolExclusionMiddleware` — profile에 `excluded_tools`가 있을 때만
10. `AnthropicPromptCachingMiddleware` — **무조건 추가** (비-Anthropic 모델에서는 no-op)
11. `MemoryMiddleware` — `memory` 파라미터 제공 시에만
12. `HumanInTheLoopMiddleware` — `interrupt_on` 파라미터 제공 시에만

### Required Middleware (제거 불가)
- `FilesystemMiddleware` — built-in file tool + permissions 보안 보장
- `SubAgentMiddleware` — `task` tool handler
- `HarnessProfile.excluded_middleware`로 이 둘을 제거하려 하면 `ValueError` 발생

### HarnessProfile
- `_harness_profile_for_model(model, model_spec)`으로 모델에 맞는 profile 조회
- Profile 제공 기능: `tool_description_overrides`, `excluded_tools`, `excluded_middleware`, `extra_middleware`, `base_system_prompt`, `system_prompt_suffix`, `general_purpose_subagent`
- `_apply_profile_prompt`로 system prompt에 profile 내용 적용

### Subagent 처리
- 세 가지 타입 구분:
  - `SubAgent` (TypedDict, `graph_id` 없고 `runnable` 없음) — declarative sync
  - `CompiledSubAgent` (TypedDict, `runnable` 있음) — pre-compiled
  - `AsyncSubAgent` (TypedDict, `graph_id` 있음) — remote/background
- 기본 general-purpose subagent: caller가 "general-purpose" 이름의 subagent를 제공하지 않으면 자동 추가
- Subagent는 parent의 `interrupt_on`을 기본 상속; `CompiledSubAgent`·`AsyncSubAgent`는 상속 안 함
- Subagent는 parent의 `permissions`를 기본 상속; 자체 `permissions` 선언 시 대체

### Default Values (소스 기준)
- `model=None` → `ChatAnthropic(model_name="claude-sonnet-4-6")` (deprecated since 0.5.3, 제거 예정 1.0.0)
- `backend=None` → `StateBackend()`
- `recursion_limit` → 9,999

### SubagentTransformer
- `subagent_names`를 frozenset으로 보유
- scope-aware factory: `_subagent_factory(scope: tuple[str, ...] = ()` → `SubagentTransformer`
- `create_agent`의 `transformers=` 파라미터로 전달

---

## Important Terms
- [[Deep Agents]] — 이 파일의 핵심 구현 대상
- [[Subagents]] — `SubAgent`, `CompiledSubAgent`, `AsyncSubAgent` 세 타입
- [[Tool Calling]] — `FilesystemMiddleware`가 tool injection 담당
- [[Memory]] — `MemoryMiddleware`로 tail에 추가
- [[Context Engineering]] — middleware 조립 순서 = context 조립 순서
- [[Checkpointing]] — `checkpointer` 파라미터 + `_DeepAgentState`의 `DeltaChannel`
- `DeltaChannel` — LangGraph 채널 타입, snapshot_frequency로 checkpoint 크기 최적화
- `HarnessProfile` — 모델별 middleware/prompt 커스터마이징 프로파일
- `SubagentTransformer` — subgraph 실행을 declared subagent 이름으로 식별하는 transformer
- `PatchToolCallsMiddleware` — tool call 패치 미들웨어 (구체적 역할은 별도 확인 필요)
- `AnthropicPromptCachingMiddleware` — Anthropic 전용 prompt caching (비-Anthropic no-op)

---

## Interpretation
- `create_deep_agent`는 LangGraph를 직접 조립하지 않고 `langchain.agents.create_agent`를 감싸는 구조다. 즉, "middleware 조립기 + create_agent 호출자"가 핵심 역할이다.
- middleware 조립 순서가 Context Engineering 문서의 system prompt 조립 순서와 직접 대응된다. FilesystemMiddleware가 filesystem context를, MemoryMiddleware가 memory context를, SkillsMiddleware가 skills를 주입한다.
- `AnthropicPromptCachingMiddleware`가 항상 추가된다는 점은 Anthropic 모델을 기본 타겟으로 설계되었음을 보여준다.
- `_DeepAgentState`의 `DeltaChannel`은 long-running task에서 checkpoint 크기 폭발 문제를 방지하는 실용적 최적화다.
- HarnessProfile 패턴은 모델별 행동 차이를 코드 분기 없이 profile 데이터로 처리하는 설계다.

---

## Implications for My AI Agent Project
- `create_deep_agent`의 동작을 수정하려면 middleware 파라미터 또는 HarnessProfile 등록으로 접근해야 한다. 소스 코드를 직접 수정할 필요가 없다.
- tool을 추가하는 방법: `tools=` 파라미터 (additive). tool을 제거하는 방법: HarnessProfile의 `excluded_tools`.
- checkpoint 효율성을 신경 써야 한다면 `_DeepAgentState`의 `DeltaChannel` 설계를 참고할 수 있다.
- 다음 분석 대상: `langchain.agents.create_agent` 내부 (LangGraph graph를 어떻게 조립하나?)

---

## Open Questions
- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 직접 조립하나?
- `SubagentTransformer`는 scope를 어떻게 활용하나? 어떤 streaming/tracing 기능을 제공하나? (`deepagents/_subagent_transformer.py` 확인 필요)
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 확인 필요)
- `create_summarization_middleware`가 반환하는 middleware의 실제 동작은? (`deepagents/middleware/summarization.py`)
- `_messages_delta_reducer`의 구체적 동작은? (`deepagents/_messages_reducer.py`)
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 어떤 의미인가?
- `PatchToolCallsMiddleware`는 어떤 tool call 패치를 수행하나?

---

## Used By
- [[Deep Agents]]
- [[Deep Agents create_deep_agent flow]]
- [[Deep Agents Code Map]]

---

## Notes
- `model=None` 기본값은 0.5.3부터 deprecated. 1.0.0에서 제거 예정.
- `recursion_limit=9_999`는 하드코딩된 값으로, 사용자가 직접 오버라이드할 수 없음.
