---
type: flow
framework: LangChain
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-source-tools-2026-05-23
---

# LangChain create_agent flow

## 요약

이 페이지는 LangChain에서 tool calling agent를 생성하고 실행하는 흐름을 추적한다.
`create_agent` 진입점 소스 코드는 미수집이며, tool 실행 경로(`BaseTool` 이하)는 소스 코드 기반으로 검증됨.

---

## Tool 실행 경로 (검증됨)
*Source: `langchain-source-tools-2026-05-23`*

tool 실행 경로는 `BaseTool`과 `StructuredTool` 소스 코드로 완전히 추적됨:

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

## Agent 생성 경로 (가설 — 소스 코드 미수집)

```python
# 현대적 방식 (tool calling agent)
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "..."})
```

**가설적 흐름 (미검증):**
1. `create_tool_calling_agent(llm, tools, prompt)`
   - `llm.bind_tools(tools)` → 각 tool의 `tool_call_schema`를 LLM에 바인딩
   - `prompt | llm_with_tools | output_parser` LCEL chain 구성
2. `AgentExecutor.invoke(input)`
   - 입력을 포맷하여 agent chain 실행
   - agent loop: LLM 호출 → tool_calls 파싱 → tool 실행 → ToolMessage 누적 → 반복
   - `max_iterations` 초과 또는 tool_calls 없으면 종료

---

## 읽어야 할 파일 (미수집)

- `libs/langchain/langchain/agents/tool_calling_agent/base.py` — `create_tool_calling_agent` 구현
- `libs/langchain/langchain/agents/agent.py` — `AgentExecutor` 구현 (루프 로직, max_iterations)
- `langchain_core/language_models/chat_models.py` — `bind_tools()`, tool schema → API payload 변환

---

## 다이어그램

```
tools = [StructuredTool, ...]
    │  각 tool.tool_call_schema → JSON schema
    │
    ▼
llm.bind_tools(tools)
    │  LLM API 호출 시 tools 파라미터에 JSON schema 전달
    │
    ▼
AgentExecutor.invoke({"input": "..."})
    │
    ├─ format_messages(input, chat_history) → messages
    │
    ├─────────────── Agent Loop ────────────────┐
    │                                           │
    │  LLM(messages) → AIMessage               │
    │      │                                   │
    │      ├─ tool_calls 없음 → 최종 답변       │
    │      │                                   │
    │      └─ tool_calls 있음:                  │
    │             │                            │
    │             ▼                            │
    │        BaseTool.invoke(ToolCall)          │
    │             └─ ToolMessage               │
    │                    │                     │
    │             messages에 추가              │
    │                    └──────────────────────┘
    │
    └─ 최종 AIMessage content 반환
```

---

## 미해결 질문

- `AgentExecutor`는 최대 반복 횟수(`max_iterations`)를 어떻게 처리하는가?
- 메시지 히스토리는 `AgentExecutor` 내부에서 어떻게 누적되는가?
- `create_react_agent`(ReAct, scratchpad 방식)과 `create_tool_calling_agent`(native tool calling)의 내부 구현 차이는?
- `bind_tools()`가 `tool_call_schema`를 어떤 provider별 API payload 형태로 변환하는가?

---

## 관련 페이지

- [[LangChain]]
- [[LangChain Code Map]]
- [[Tool Calling]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

- `langchain-source-tools-2026-05-23` (tool 실행 경로 검증)

*미수집: `create_agent` 진입점, `AgentExecutor` 루프 내부*
