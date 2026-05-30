---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-tools-2026-05-23
  - langchain-docs-messages-2026-05-23
  - langchain-source-tools-2026-05-23
  - langchain-source-bind-tools-function-calling-2026-05-23
---

# Tool Calling

## 요약

Tool Calling은 추론 중 LLM이 외부 함수(도구)를 선택하고 호출하는 메커니즘이다. LLM은 구조화된 도구 호출 요청을 출력하고, 런타임은 해당 도구를 실행한 뒤 결과를 `ToolMessage`로 반환한다.

## 중요한 이유

Tool Calling은 LLM agent가 외부 시스템과 상호작용하는 기본 방식이다. LLM의 지식 범위를 넘어 실시간 데이터 조회, 코드 실행, DB 쿼리, 세계에 대한 행동이 가능해진다.

---

## 초보자 요약 (Book 2.3 섹션)

> "LLM이 함수를 호출하는 원리" — 5단계로 이해하기

```
[1] 도구 정의
    @tool
    def get_weather(city: str) -> str:
        """Get current weather for a city."""
        ...

[2] LLM에 도구 등록 (bind_tools)
    model.bind_tools([get_weather])
    → 내부: @tool 의 docstring + 타입 힌트 → JSON Schema 변환
    → LLM API 호출 시 tools=[{"type": "function", "function": {...}}] 로 전달

[3] LLM이 도구 선택
    LLM이 tools 파라미터를 읽고 필요한 도구를 선택
    → AIMessage(tool_calls=[{"name": "get_weather", "args": {"city": "Seoul"}, "id": "call_abc"}])

[4] 런타임이 도구 실행
    tool.invoke({"city": "Seoul"})
    → ToolMessage(content="Sunny, 22°C", tool_call_id="call_abc")
    ← tool_call_id 가 반드시 AIMessage의 id 와 일치해야 함

[5] LLM이 결과를 받아 최종 응답 생성
    [HumanMessage, AIMessage(tool_calls), ToolMessage] → model.invoke()
    → AIMessage("서울은 현재 맑고 22°C입니다.")
```

**핵심 통찰:**
- LLM은 실제로 함수를 "호출"하지 않는다 — 호출 **요청**을 텍스트로 출력할 뿐이다
- 실제 실행은 **런타임(프레임워크)**이 담당한다
- docstring 품질이 LLM의 도구 선택 정확도를 직접 결정한다
- `tool_call_id`는 LLM이 생성하는 고유 식별자 — 결과를 요청과 매칭하는 키다

**예제 코드:**
- `examples/langchain_core/02_tool_calling.py` — 실행 경로 (`@tool` → `StructuredTool` → `ToolMessage`)
- `examples/langchain_core/02b_bind_tools.py` — 등록 경로 (`bind_tools` → JSON Schema → OpenAI API payload)

---

---

## LangChain에서의 Tool Calling
*Source: `langchain-docs-tools-2026-05-23`*

### @tool 데코레이터

가장 간단한 도구 생성 방법:

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

**핵심 규칙:**
- **타입 힌트 필수** — 도구의 JSON 입력 스키마를 자동 생성
- **Docstring = 모델이 읽는 설명** — 명확한 docstring이 모델의 도구 선택 근거가 됨

### 도구 이름/설명 커스터마이징

```python
@tool("web_search")  # 커스텀 이름
def search(query: str) -> str: ...

@tool("calculator", description="Performs arithmetic calculations.")
def calc(expression: str) -> str: ...
```

### ToolRuntime — 도구 내 컨텍스트 접근

| 컴포넌트 | 설명 |
|---------|------|
| `runtime.state` | 현재 대화 단기 메모리 (가변) |
| `runtime.context` | 호출 시 전달된 불변 설정 |
| `runtime.store` | 대화 간 영속적 장기 메모리 |
| `runtime.stream_writer` | 실시간 업데이트 발행 |
| `runtime.execution_info` | Thread ID, run ID |
| `runtime.tool_call_id` | ToolMessage 생성 시 필요한 call ID |

### 도구 반환값 3가지

| 반환 타입 | 동작 |
|---------|------|
| `string` | ToolMessage로 자동 변환 |
| `object` | 직렬화 후 모델에 전달 |
| `Command` | 상태 업데이트 + 다음 노드 라우팅 |

**Command 반환 예시:**
```python
from langgraph.types import Command
from langchain.messages import ToolMessage

@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(
        update={
            "preferred_language": language,
            "messages": [
                ToolMessage(
                    content=f"Language set to {language}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

### 예약 파라미터

| 파라미터 | 목적 |
|---------|------|
| `config` | RunnableConfig 전달 |
| `runtime` | ToolRuntime 접근 |

---

## @tool 데코레이터 내부 구조
*Source: `langchain-source-tools-2026-05-23`*

### @tool → StructuredTool 변환 경로

`@tool` 데코레이터의 실제 구현은 `langchain_core/tools/convert.py`의 `tool()` 함수다.

```
@tool (convert.py: tool())
    │
    ├─ infer_schema=True (기본값) ──→ StructuredTool.from_function(func, coroutine, ...)
    │                                       │
    │                                       ├─ create_schema_from_function() → args_schema (Pydantic model)
    │                                       ├─ docstring → description_
    │                                       └─ StructuredTool(name, func, coroutine, args_schema, description)
    │
    └─ infer_schema=False, args_schema=None ──→ Tool (string→string 단순 도구)
```

- **sync 함수** → `func` 필드에 저장, `coroutine=None`
- **async 함수** → `coroutine` 필드에 저장, `func=None`
- **Runnable** → `invoke_wrapper`/`ainvoke_wrapper` 생성 후 `func`/`coroutine`으로 래핑

### docstring → LLM 전달 경로

```
함수 docstring
    │
    ▼
create_schema_from_function()
    │  ├─ pydantic validate_arguments → inferred_model
    │  ├─ _infer_arg_descriptions() → (description, arg_descriptions)
    │  └─ _create_subset_model(descriptions=arg_descriptions, fn_description=description)
    ▼
StructuredTool.args_schema (Pydantic BaseModel subclass)
    │
    ▼
tool_call_schema property → model_json_schema()
    │  {
    │    "title": "search_api",
    │    "description": "함수 docstring",  ← LLM이 도구 선택에 사용
    │    "properties": {
    │      "query": {"type": "string", "description": "Args: 섹션 설명"}
    │    }
    │  }
    ▼
LLM API 호출 payload (tools 파라미터)
```

**파라미터별 description 전달 방법:**
```python
# 방법 1: Google Style docstring
@tool(parse_docstring=True)
def search(query: str) -> str:
    """Search the database.
    Args:
        query: Search terms to look for.
    """

# 방법 2: Annotated 타입 힌트
from typing import Annotated
@tool
def search(query: Annotated[str, "Search terms to look for"]) -> str:
    """Search the database."""
```

### 실행 경로 (내부 구현)
*Source: `langchain-source-tools-2026-05-23` — `BaseTool.run()`*

```
invoke(ToolCall) [BaseTool]
    │
    ├─ _prep_run_args() → tool_input (dict), tool_call_id (str)
    │
    ▼
run(tool_input, tool_call_id=...)
    │
    ├─ _to_args_and_kwargs()
    │       └─ _parse_input()  ← args_schema로 Pydantic validation
    │                          ← InjectedToolCallId 주입
    │
    ├─ _run(*args, **kwargs)   ← 실제 함수 실행 (StructuredTool → self.func())
    │
    ├─ 예외 처리:
    │   ├─ ToolException → handle_tool_error 설정에 따라 에러 문자열 반환 or re-raise
    │   ├─ ValidationError → handle_validation_error 설정에 따라 처리
    │   └─ 기타 Exception → 항상 re-raise
    │
    └─ _format_output(content, tool_call_id=...)
            └─ tool_call_id 있으면 → ToolMessage(content, tool_call_id=..., name=..., status=...)
               tool_call_id 없으면 → content 그대로 반환
```

### tool_call_schema — LLM에 전달되는 스키마

`BaseTool.tool_call_schema` property는 LLM에 노출되는 스키마다. `InjectedToolArg`로 어노테이션된 파라미터는 **제외**된다.

```python
from typing import Annotated
from langchain_core.tools import InjectedToolArg, InjectedToolCallId

@tool
def process(
    query: str,                                           # ✅ LLM schema에 포함
    user_id: Annotated[str, InjectedToolArg()],          # ❌ LLM schema에서 제외 (runtime 주입)
    tool_call_id: Annotated[str, InjectedToolCallId()],  # ❌ LLM schema에서 제외 (자동 주입)
) -> str:
    """Process query for user."""
    return f"user {user_id}: {query}"
```

### 에러 처리 옵션

```python
# ToolException: 도구 에러를 agent에 알리는 전용 예외
from langchain_core.tools import ToolException

@tool(handle_tool_error=True)  # 에러 메시지를 LLM에 전달 (agent 중단 없음)
def risky_tool(input: str) -> str:
    """A tool that might fail."""
    if not input:
        raise ToolException("Input cannot be empty.")
    return "OK"

# handle_tool_error=True → ToolException.args[0] 를 LLM에 반환
# handle_tool_error="custom message" → 고정 문자열 반환
# handle_tool_error=callable → 함수(e) 결과 반환
# handle_tool_error=False (기본값) → re-raise (agent 중단)
```

---

## Tool Call 흐름 (메시지 관점)
*Source: `langchain-docs-messages-2026-05-23`*

```
1. HumanMessage("사용자 질문")
        ↓
2. AIMessage with tool_calls=[{"name": ..., "args": ..., "id": "call_123"}]
        ↓
3. Tool 실행
        ↓
4. ToolMessage(content=결과, tool_call_id="call_123")  ← id 반드시 매칭
        ↓
5. 모델 재호출 → 최종 AIMessage
```

`ToolMessage.tool_call_id`는 반드시 `AIMessage.tool_calls[i]['id']`와 일치해야 한다.

---

## bind_tools → LLM API Payload 변환 경로
*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

### BaseChatModel.bind_tools는 추상 메서드

**검증됨:** `BaseChatModel.bind_tools`는 `NotImplementedError`를 raise하는 추상 메서드다. 실제 변환 로직은 `langchain_openai`, `langchain_anthropic` 등 각 provider 구현체에 있다. Source: `langchain-source-bind-tools-function-calling-2026-05-23`

### OpenAI provider의 변환 체인

**검증됨:** OpenAI provider(`BaseChatOpenAI.bind_tools`)는 각 tool을 `convert_to_openai_tool()`로 변환한다.

```
BaseTool.tool_call_schema
    │  (InjectedToolArg 필드가 제외된 args_schema의 JSON schema)
    │
    ▼
bind_tools([tool])                     ← BaseChatOpenAI
    │
    ▼
convert_to_openai_tool(tool)           ← langchain_core/utils/function_calling.py
    │  · 잘 알려진 OpenAI tool(file_search 등)은 그대로 통과
    │  · 나머지는 convert_to_openai_function에 위임
    │
    ▼
convert_to_openai_function(tool)
    │  · Anthropic/Bedrock/OpenAI/JSON schema 포맷 자동 감지
    │  · BaseTool이면 _format_tool_to_openai_function에 위임
    │
    ▼
_format_tool_to_openai_function(tool: BaseTool)
    │  · tool.tool_call_schema 확인
    │  · dict schema → _convert_json_schema_to_openai_function
    │  · Pydantic model → _convert_pydantic_to_openai_function
    │  · args 없는 tool → generic string 파라미터 래퍼
    │
    ▼
{"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    │  OpenAI API 형식의 tool schema
    │
    ▼
self.bind(tools=[formatted_tool, ...])  ← 이후 LLM API 호출 시 tools= 파라미터로 전달
```

### tool_choice 정규화 (OpenAI)

**검증됨:** OpenAI provider는 `tool_choice`를 다음과 같이 정규화한다:
- tool 이름(str) → `{"type": "function", "function": {"name": ...}}`
- `"any"` → `"required"` (OpenAI 표준)
- `"file_search"`, `"code_interpreter"` 등 잘 알려진 이름 → `{"type": tool_choice}`

### provider별 변환 방식 차이

**검증됨:** `BaseChatModel.bind_tools`는 추상이므로 provider마다 다른 변환 경로를 사용한다. OpenAI는 `convert_to_openai_tool`을 공유하지만, Anthropic은 Anthropic API 형식(`{"name": ..., "description": ..., "input_schema": {...}}`)으로 자체 변환한다. Source: `langchain-source-bind-tools-function-calling-2026-05-23`

---

## LangGraph에서의 Tool Calling

- 도구는 `StateGraph` 안의 노드로 정의하거나 `ToolNode`를 사용
- `ToolNode`는 `langgraph.prebuilt`에서 제공
- `Command` 반환으로 상태 업데이트와 라우팅을 동시 처리 가능

*Source: 소스 코드 확인 필요*

---

## Deep Agents에서의 Tool Calling

- 추후 작성 — 도구 레지스트리와 도구 위임 메커니즘 확인 필요
- *소스 필요*

---

## 핵심 개념

- **도구 정의** — 이름, 설명, 입력 스키마 (타입 힌트에서 자동 생성)
- **도구 선택** — 모델이 docstring을 읽고 언제/어떤 도구를 쓸지 결정
- **도구 실행** — 런타임이 함수 호출
- **도구 결과** — ToolMessage로 반환, tool_call_id로 연결

## 미해결 질문

- 각 프레임워크는 병렬 도구 호출을 내부적으로 어떻게 처리하는가?
- LangGraph `ToolNode`와 `create_agent` 도구 실행의 차이는?
- LCEL `.bind_tools()` 방식과 `create_agent([tool])` 방식의 차이는?
- `@tool`로 만든 tool의 `args_schema.model_json_schema()`가 LLM API 호출 시 어떤 payload로 변환되는가? (ChatModel `bind_tools` 경로)
- `ToolRuntime`(`_DirectlyInjectedToolArg` 상속)의 전체 필드 구성은?

**해소됨 (2026-05-23):**
- ✅ `@tool` 데코레이터로 만든 tool의 내부 타입은? → `StructuredTool` (infer_schema=True 기본값). infer_schema=False면 단순 `Tool`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ docstring이 LLM에 전달되는 방식은? → `create_schema_from_function` → `_infer_arg_descriptions` → `_create_subset_model`의 `fn_description` → `model_json_schema()`의 `description` 필드. (Source: `langchain-source-tools-2026-05-23`)
- ✅ 비동기 tool 정의 방법은? → `async def`로 정의하면 `coroutine` 파라미터로 자동 처리. 별도 설정 불필요. (Source: `langchain-source-tools-2026-05-23`)
- ✅ tool 실행 중 예외 처리는? → `ToolException`은 `handle_tool_error` 설정에 따라 에러 메시지 반환 or re-raise. 기타 예외는 항상 re-raise. (Source: `langchain-source-tools-2026-05-23`)
- ✅ LLM tool call → tool 실행 → ToolMessage 반환 흐름은? → `invoke(ToolCall)` → `_prep_run_args` → `run()` → `_to_args_and_kwargs` → `_run()` → `_format_output` → `ToolMessage(content, tool_call_id=...)`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ `@tool`로 만든 tool의 `args_schema.model_json_schema()`가 LLM API 호출 시 어떤 payload로 변환되는가? → `BaseTool.tool_call_schema` → `bind_tools([tool])` → `convert_to_openai_tool` → `convert_to_openai_function` → `_format_tool_to_openai_function` → `{"type": "function", "function": {...}}` 형식의 OpenAI API payload. `BaseChatModel.bind_tools`는 추상이므로 provider별로 다른 변환 경로 사용. (Source: `langchain-source-bind-tools-function-calling-2026-05-23`)

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Subagents]]

## 소스

- `langchain-docs-tools-2026-05-23`
- `langchain-docs-messages-2026-05-23`
- `langchain-source-tools-2026-05-23`
- `langchain-source-bind-tools-function-calling-2026-05-23`
