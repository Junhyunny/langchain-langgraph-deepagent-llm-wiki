---
type: source_summary
source_id: langchain-source-bind-tools-function-calling-2026-05-23
title: "LangChain — bind_tools 및 tool schema → API payload 변환 경로"
framework: LangChain
retrieved_at: 2026-05-23
status: verified
confidence: high
---

# Source Summary: LangChain — bind_tools & convert_to_openai_tool

## Source Info
- **Source ID:** `langchain-source-bind-tools-function-calling-2026-05-23`
- **Type:** source_code
- **URLs:**
  - `https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/language_models/chat_models.py`
  - `https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/utils/function_calling.py`
  - `https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/chat_models/base.py`
- **Retrieved At:** 2026-05-23
- **Version / Commit:** master branch

---

## Key Facts

### BaseChatModel.bind_tools (추상 메서드)

```python
# libs/core/langchain_core/language_models/chat_models.py
def bind_tools(
    self,
    tools: Sequence[builtins.dict[str, Any] | type | Callable | BaseTool],
    *,
    tool_choice: str | None = None,
    **kwargs: Any,
) -> Runnable[LanguageModelInput, AIMessage]:
    raise NotImplementedError
```

**핵심:** `BaseChatModel.bind_tools`는 추상 메서드(NotImplementedError). 실제 변환 로직은 각 provider 구현체(`langchain_openai`, `langchain_anthropic` 등)에 있다.

### BaseChatOpenAI.bind_tools (OpenAI 구현)

```python
# libs/partners/openai/langchain_openai/chat_models/base.py
def bind_tools(
    self,
    tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
    *,
    tool_choice: dict | str | bool | None = None,
    strict: bool | None = None,
    parallel_tool_calls: bool | None = None,
    response_format: _DictOrPydanticClass | None = None,
    **kwargs: Any,
) -> Runnable[LanguageModelInput, AIMessage]:
```

**변환 핵심:**
```python
formatted_tools = [
    convert_to_openai_tool(tool, strict=strict) for tool in tools
]
```

각 tool을 `convert_to_openai_tool`로 변환 후 `self.bind(tools=formatted_tools, ...)`로 바인딩.

**tool_choice 정규화:**
- tool 이름 → `{"type": "function", "function": {"name": ...}}`
- `"any"` → `"required"` (OpenAI 표준)
- 잘 알려진 tool(`"file_search"`, `"code_interpreter"`) → `{"type": tool_choice}`

### 변환 체인: BaseTool → OpenAI API payload

```
BaseTool.tool_call_schema
    │  (InjectedToolArg 필드 제외된 args_schema)
    │
    ▼
bind_tools([tool])
    │
    ▼
convert_to_openai_tool(tool, strict=...)
    │  libs/core/langchain_core/utils/function_calling.py
    │
    ▼
convert_to_openai_function(tool)
    │  Anthropic/Bedrock/OpenAI/JSON schema 포맷 자동 감지
    │
    ▼
_format_tool_to_openai_function(tool: BaseTool)
    │  tool.tool_call_schema 확인
    │  → dict schema면 _convert_json_schema_to_openai_function()
    │  → Pydantic model이면 _convert_pydantic_to_openai_function()
    │  → args 없는 단순 tool이면 generic string 파라미터 래퍼
    │
    ▼
{"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    │  OpenAI API 형식의 tool schema
    │
    ▼
LLM API 호출 시 tools=[...] 파라미터로 전달
```

### convert_to_openai_function 입력 타입 지원

`convert_to_openai_function`은 다음 타입을 자동 감지하여 변환:
- Anthropic 포맷 (`name` + `input_schema` 키 보유)
- Amazon Bedrock Converse 포맷 (`toolSpec` 키 보유)
- OpenAI function 포맷 딕셔너리
- JSON schema (title 키 보유)
- Pydantic BaseModel 클래스
- TypedDict 클래스
- LangChain BaseTool 객체
- 일반 Python callable

### _format_tool_to_openai_function 처리 경로

```python
def _format_tool_to_openai_function(tool: BaseTool) -> FunctionDescription:
    """Format tool into the OpenAI function API."""
    # tool_call_schema가 있으면 그것을 변환
    # dict schema → _convert_json_schema_to_openai_function
    # Pydantic model → _convert_pydantic_to_openai_function
    # 없으면 generic string parameter wrapper 반환
```

### Anthropic의 변환 경로

Anthropic provider(`langchain_anthropic`)는 자체 `bind_tools`를 구현하며, tool schema를 Anthropic API 형식(`{"name": ..., "description": ..., "input_schema": {...}}`)으로 변환한다. `convert_to_openai_tool`을 거치지 않고 별도 변환 유틸리티를 사용한다.

---

## Important Terms
- [[Tool Calling]] — bind_tools가 이 개념의 핵심 구현 경로
- [[LangChain Code Map]] — function_calling.py 위치
- [[LangChain create_agent flow]] — bind_tools가 사용되는 컨텍스트

---

## Interpretation

- `bind_tools`는 LangChain에서 provider-agnostic한 공개 API이지만, 실제 구현은 provider마다 다르다.
- 핵심 변환 유틸리티 `convert_to_openai_tool`은 `langchain_core`에 있어 여러 provider가 공유 가능하지만, Anthropic 등 일부 provider는 자체 변환 경로를 사용한다.
- `BaseTool.tool_call_schema`는 LLM에 전달될 최종 스키마의 출발점이다. `InjectedToolArg`가 제외된 정제된 schema.

---

## Open Questions
- `langchain_anthropic`의 bind_tools는 어떤 변환 유틸리티를 사용하는가?
- `strict=True`일 때 JSON schema에 어떤 제약이 추가되는가?
- `parallel_tool_calls=False`는 API 요청에서 어떤 파라미터로 매핑되는가?

---

## Used By
- `docs/wiki/concepts/Tool Calling.md`
- `docs/wiki/flows/LangChain create_agent flow.md`
- `docs/wiki/codebase/LangChain Code Map.md`
