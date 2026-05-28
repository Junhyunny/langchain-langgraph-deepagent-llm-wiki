---
type: source_summary
source_id: langchain-source-create-agent-factory-2026-05-23
title: "LangChain — create_agent 소스코드 (factory.py)"
framework: LangChain
retrieved_at: 2026-05-23
status: verified
confidence: high
---

# Source Summary: LangChain — create_agent (factory.py)

## Source Info
- **Source ID:** `langchain-source-create-agent-factory-2026-05-23`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/factory.py
- **Retrieved At:** 2026-05-23
- **Version / Commit:** master branch

---

## Key Facts

### 실제 파일 경로 (중요)

`create_agent`는 `libs/langchain_v1/langchain/agents/factory.py`에 있다.
이전 위키에 적힌 `libs/langchain/langchain/agents/tool_calling_agent/base.py` 경로는 구버전이며 현재 master에 존재하지 않는다.
`create_tool_calling_agent` / `AgentExecutor` API는 deprecated, `create_agent`가 현재 공식 API.

### create_agent 시그니처

```python
def create_agent(
    model: str | BaseChatModel,
    tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware[StateT_co, ContextT]] = (),
    response_format: ResponseFormat[ResponseT] | type[ResponseT] | dict[str, Any] | None = None,
    state_schema: type[AgentState[ResponseT]] | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache[Any] | None = None,
    transformers: Sequence[TransformerFactory] | None = None,
)
```

### Graph 구성

`create_agent`는 `StateGraph`를 동적으로 구성한다:

**노드:**
- **model node** — LLM 호출. middleware composition(`_chain_model_call_handlers()`)으로 래핑
- **tools node** — `ToolNode(tools=available_tools, wrap_tool_call=...)`. client-side tools가 있거나 middleware가 tool call wrapper를 정의할 때만 추가
- **middleware 훅 노드** — `before_agent`, `before_model`, `after_model`, `after_agent` (middleware 등록 여부에 따라 조건부 추가)

**엣지:**
- `add_conditional_edges()` 로 model→tools 전환 (tool_calls 있으면 tools 노드, 없으면 종료)
- tools 노드 → model 노드 (루프)

### 실행 루프

```
[START]
   │
   ▼
before_agent (middleware 훅, 있을 경우)
   │
   ▼
before_model (middleware 훅, 있을 경우)
   │
   ▼
model node ─── tool_calls 없음 ──→ after_agent ──→ [END]
   │
   └── tool_calls 있음
           │
           ▼
       tools node (ToolNode)
           │
           ▼
       after_model (middleware 훅, 있을 경우)
           │
           └──────────────────────────→ model node (루프)
```

### ToolNode 생성

```python
tool_node = (
    ToolNode(
        tools=available_tools,
        wrap_tool_call=wrap_tool_call_wrapper,
        awrap_tool_call=awrap_tool_call_wrapper,
    )
    if available_tools or wrap_tool_call_wrapper or awrap_tool_call_wrapper
    else None
)
```

### Middleware 조합

- `_chain_model_call_handlers()` — 여러 middleware의 model call handler를 체이닝
- `_chain_tool_call_wrappers()` — tool call wrapper 체이닝
- middleware는 각 단계에서 Command를 누적할 수 있음

### Structured Output 지원

- `response_format`이 있으면 tool 기반 또는 provider-specific 방식으로 구조화 출력 지원
- `_supports_provider_strategy()`로 모델 지원 여부 자동 감지

---

## Important Terms
- [[StateGraph]] — create_agent 내부에서 사용하는 graph runtime
- [[Tool Calling]] — ToolNode를 통한 tool 실행
- [[Agent Harness]] — Deep Agents의 create_deep_agent는 create_agent 위에 구축됨
- [[LangChain create_agent flow]] — 이 소스 기반 flow 페이지

---

## Interpretation

- `create_agent`는 LangGraph `StateGraph`를 직접 구성하는 팩토리 함수다. `AgentExecutor` 루프가 아니라 graph node와 conditional edge가 루프를 구현한다.
- middleware 없이 사용하면 model node + tools node + conditional edge로 구성된 매우 단순한 graph가 만들어진다.
- `create_tool_calling_agent` + `AgentExecutor` 패턴은 구버전 API이며 현재 master에는 없다.

---

## Open Questions
- ✅ `_chain_model_call_handlers()`의 구체적인 구현은 2026-05-28 `.venv` 소스에서 확인됨. 첫 번째 middleware가 outermost이며, command는 inner-first로 누적된다.
- ✅ `before_agent`, `after_agent` 훅의 시그니처와 반환 타입은 `AgentMiddleware` 소스에서 확인됨: `(state, runtime) -> dict[str, Any] | None`.
- ✅ `available_tools`는 사용자가 넘긴 tool과 middleware가 주입한 tool을 함께 포함한다. ToolNode 생성 전 `default_tools`/middleware tools가 병합된다.
- `wrap_tool_call`이 `Command`를 반환할 때 graph state에 어떤 update/goto 제한이 적용되는지는 별도 확인 필요.

---

## Used By
- `docs/wiki/flows/LangChain create_agent flow.md`
- `docs/wiki/experiments/2026-05-28 langchain create_agent fake tool loop.md`
- `docs/wiki/comparisons/create_agent vs create_deep_agent.md`
- `docs/wiki/codebase/LangChain Code Map.md`
- `docs/wiki/frameworks/LangChain.md`
