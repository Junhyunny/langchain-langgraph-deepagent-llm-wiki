---
type: flow
framework: LangChain
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-source-tools-2026-05-23
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-source-bind-tools-function-calling-2026-05-23
---

# LangChain create_agent flow

## 요약

이 페이지는 LangChain에서 tool calling agent를 생성하고 실행하는 흐름을 추적한다.
`create_agent` 진입점은 소스 코드 기반으로 검증됨. tool 실행 경로(`BaseTool` 이하)도 소스 코드 기반으로 검증됨.

**중요:** `create_tool_calling_agent` + `AgentExecutor`는 구버전 API. 현재 공식 API는 `create_agent`이며 LangGraph `StateGraph` 기반으로 구현됨.

---

## create_agent 전체 흐름

*Source: `langchain-source-create-agent-factory-2026-05-23`*

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search_db, send_email],
    system_prompt="You are a helpful assistant.",
)
result = agent.invoke({"messages": [HumanMessage("...")]})
```

**검증됨:** `create_agent`는 `libs/langchain_v1/langchain/agents/factory.py`에 구현됨. `StateGraph`를 동적으로 구성하는 팩토리 함수다.

---

## create_agent Graph 구성

*Source: `langchain-source-create-agent-factory-2026-05-23`*

**검증됨:** `create_agent`는 내부에서 `StateGraph`를 구성한다. 노드와 엣지 구성:

### 노드

| 노드 | 역할 | 조건 |
|------|------|------|
| model node | LLM 호출. middleware가 있으면 `_chain_model_call_handlers()`로 래핑 | 항상 존재 |
| tools node | `ToolNode(tools=available_tools)` | client-side tools 있거나 middleware가 wrap_tool_call 정의 시 |
| before_agent | middleware 훅 | middleware 등록 시 |
| before_model | middleware 훅 | middleware 등록 시 |
| after_model | middleware 훅 | middleware 등록 시 |
| after_agent | middleware 훅 | middleware 등록 시 |

### 실행 루프 (graph edges)

```
[START]
    │
    ▼
before_agent (있을 경우)
    │
    ▼
before_model (있을 경우)
    │
    ▼
model node ─── tool_calls 없음 ──→ after_agent (있을 경우) ──→ [END]
    │
    └── tool_calls 있음
            │
            ▼
        tools node (ToolNode)
            │  · BaseTool.invoke(ToolCall) 실행
            │  · 결과를 ToolMessage로 반환
            │
            ▼
        after_model (있을 경우)
            │
            └──────────────────────────────→ model node (루프)
```

**검증됨:** conditional edge는 `add_conditional_edges()`로 구현. model → tools 전환은 tool_calls 유무로 결정. tools → model 루프는 무조건 반복.

### ToolNode 생성 조건

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

---

## Tool 등록 경로 (검증됨)

*Source: `langchain-source-tools-2026-05-23`*

```
@tool 데코레이터 또는 StructuredTool.from_function()
    │
    ├─ create_schema_from_function(name, func)
    │       ├─ pydantic validate_arguments → inferred_model
    │       ├─ _infer_arg_descriptions() → (description, arg_descriptions)
    │       └─ _create_subset_model(...) → args_schema (Pydantic BaseModel)
    │
    └─ StructuredTool(name, func, coroutine, args_schema, description)
            │
            └─ .tool_call_schema (property)
                    └─ args_schema.model_json_schema() - InjectedToolArg 필드 제외
                       → LLM API에 전달될 JSON schema
```

---

## bind_tools — tool schema → LLM API payload 변환

*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

**검증됨:** `BaseChatModel.bind_tools`는 추상 메서드(NotImplementedError). OpenAI provider는 다음 경로로 변환:

```
BaseTool.tool_call_schema
    │
    ▼
bind_tools([tool])              ← provider 구현체 (BaseChatOpenAI 등)
    │
    ▼
convert_to_openai_tool(tool)    ← langchain_core/utils/function_calling.py
    │
    ▼
convert_to_openai_function(tool)
    │
    ▼
_format_tool_to_openai_function(tool: BaseTool)
    │  tool.tool_call_schema → JSON 변환
    │
    ▼
{"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    │
    ▼
LLM API 호출 시 tools=[...] 파라미터로 전달
```

---

## Tool 실행 경로 (검증됨)

*Source: `langchain-source-tools-2026-05-23`*

```
[Agent가 AIMessage.tool_calls 수신]
    │
    ▼
BaseTool.invoke(ToolCall)
    │  ToolCall = {"name": "...", "args": {...}, "id": "call_abc123", "type": "tool_call"}
    │
    ├─ _prep_run_args(ToolCall)
    │       ├─ tool_call_id = ToolCall["id"]       ← "call_abc123"
    │       └─ tool_input = ToolCall["args"].copy() ← {"query": "..."}
    │
    ▼
BaseTool.run(tool_input, tool_call_id="call_abc123")
    │
    ├─ CallbackManager.on_tool_start(...)    ← 트레이싱 시작
    │
    ├─ _to_args_and_kwargs(tool_input, tool_call_id)
    │       └─ _parse_input(tool_input, tool_call_id)
    │               ├─ args_schema.model_validate(tool_input) ← Pydantic validation
    │               └─ InjectedToolCallId 주입 (해당 필드 있을 경우)
    │
    ├─ StructuredTool._run(*args, **kwargs)
    │       └─ self.func(*args, **kwargs)     ← 실제 Python 함수 실행
    │
    ├─ (예외 처리)
    │   ├─ ToolException → handle_tool_error에 따라 처리
    │   ├─ ValidationError → handle_validation_error에 따라 처리
    │   └─ 기타 Exception → re-raise
    │
    ├─ _format_output(content, tool_call_id="call_abc123", name="...", status="success")
    │       └─ ToolMessage(content, tool_call_id="call_abc123", name="...", status="success")
    │
    └─ CallbackManager.on_tool_end(...)      ← 트레이싱 종료

    반환값: ToolMessage
```

---

## 전체 흐름 다이어그램

```
tools = [StructuredTool, ...]
    │  각 tool.tool_call_schema → convert_to_openai_tool → JSON schema
    │
    ▼
create_agent(model, tools, system_prompt=...)
    │  StateGraph 구성: model node + tools node + conditional edges
    │
    ▼
agent.invoke({"messages": [HumanMessage("...")]})
    │
    ├─────────────── Agent Loop (StateGraph) ────────────────┐
    │                                                        │
    │  model node: LLM(messages) → AIMessage                │
    │      │                                                 │
    │      ├─ tool_calls 없음 → [END] (최종 답변)            │
    │      │                                                 │
    │      └─ tool_calls 있음:                               │
    │             │                                          │
    │             ▼                                          │
    │        tools node: BaseTool.invoke(ToolCall)           │
    │             └─ ToolMessage                             │
    │                    │                                   │
    │             messages에 추가                           │
    │                    └────────────────────────────────────┘
    │
    └─ 최종 AIMessage content 반환
```

---

## 소스 파일 위치

**검증됨:**
- `libs/langchain_v1/langchain/agents/factory.py` — `create_agent` 구현. StateGraph 구성, middleware 조합, ToolNode 생성.
- `libs/core/langchain_core/tools/base.py` — `BaseTool`, tool 실행 경로
- `libs/core/langchain_core/tools/structured.py` — `StructuredTool`
- `libs/core/langchain_core/tools/convert.py` — `@tool` 데코레이터
- `libs/core/langchain_core/utils/function_calling.py` — `convert_to_openai_tool`, `convert_to_openai_function`, `_format_tool_to_openai_function`
- `libs/partners/openai/langchain_openai/chat_models/base.py` — `BaseChatOpenAI.bind_tools` OpenAI 구현

**구버전 경로 (현재 master에 없음):**
- `libs/langchain/langchain/agents/tool_calling_agent/base.py` — `create_tool_calling_agent` (deprecated)
- `libs/langchain/langchain/agents/agent.py` — `AgentExecutor` (deprecated)

---

## 미해결 질문

- `_chain_model_call_handlers()`의 구체적인 구현은? middleware 체이닝 메커니즘
- `before_agent`, `after_agent` 훅의 시그니처와 반환 타입은?
- `response_format` 처리 시 structured output과 tool calling의 내부 차이는?
- `create_react_agent`(LangGraph prebuilt)과 `create_agent`(LangChain)의 구현 차이는?

---

## 관련 페이지

- [[LangChain]]
- [[LangChain Code Map]]
- [[Tool Calling]]
- [[StateGraph]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

- `langchain-source-tools-2026-05-23` (tool 실행 경로 검증)
- `langchain-source-create-agent-factory-2026-05-23` (create_agent graph 구성 검증)
- `langchain-source-bind-tools-function-calling-2026-05-23` (bind_tools → API payload 변환 검증)
