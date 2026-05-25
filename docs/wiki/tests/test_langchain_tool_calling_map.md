---
type: tests
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-27
sources:
  - langchain-core-test-tools-2026-05-27
---

# LangChain Tool Calling 테스트 맵

## Summary

`langchain-core`의 `test_tools.py`에서 도구 시스템의 핵심 동작을 검증하는 테스트들을 분석한다.
전체 3,743줄, 80개 이상의 테스트 함수가 포함되어 있다.

## Why It Matters

`@tool` 데코레이터, `BaseTool`, `StructuredTool`이 어떤 계약을 맺고 있는지 공식 테스트로 확인할 수 있다.
특히 Pydantic 스키마 연동, `InjectedToolArg`, `InjectedToolCallId`, 에러 처리, `ToolMessage` 반환 흐름은
LangGraph 상태 그래프와 직접 연결되므로 이 테스트를 이해하면 두 프레임워크의 경계를 명확히 알 수 있다.

## 테스트 파일 위치

```
libs/core/tests/unit_tests/test_tools.py
```

- Repo: `langchain-ai/langchain`
- Commit: `9a671d7919597eb7226e2f87cdfbc161a774daf7`

---

## 핵심 테스트 그룹

### 1. `@tool` 데코레이터 — 기본 동작

#### `test_unnamed_decorator`

```python
@tool
def search_api(query: str) -> str:
    """Search the API for the query."""
    return "API result"

assert isinstance(search_api, BaseTool)
assert search_api.name == "search_api"          # 함수명이 tool name이 된다
assert not search_api.return_direct              # 기본값 False
assert search_api.invoke("test") == "API result"
```

**확인된 동작:**
- `@tool`은 함수를 `BaseTool` 인스턴스로 변환한다
- `name`은 함수 이름에서 자동으로 결정된다
- `return_direct=False`가 기본값이다 (LLM이 결과를 다시 받아 처리)
- `invoke()`는 단일 문자열 입력도 허용한다

#### `test_tool_with_kwargs`

```python
@tool(return_direct=True)
def search_api(arg_0: str, arg_1: float = 4.3, ping: str = "hi") -> str:
    """Search the API for the query."""
    return f"arg_0={arg_0}, arg_1={arg_1}, ping={ping}"

result = search_api.run(tool_input={"arg_0": "foo"})
assert result == "arg_0=foo, arg_1=4.3, ping=hi"  # 기본값이 적용된다
```

**확인된 동작:**
- `return_direct=True` → tool 결과를 LLM에 넘기지 않고 사용자에게 바로 반환
- 기본값이 있는 파라미터는 생략 가능

#### `test_decorator_with_specified_schema`

```python
@tool(args_schema=_MockSchema)
def tool_func(*, arg1: int, arg2: bool, arg3: dict | None = None) -> str:
    return f"{arg1} {arg2} {arg3}"

assert tool_func.args_schema == _MockSchema
```

**확인된 동작:**
- `args_schema`를 직접 지정하면 타입 어노테이션 추론 대신 Pydantic 모델이 사용된다
- 커스텀 스키마가 그대로 유지된다

---

### 2. `StructuredTool` — 명시적 생성

#### `test_structured_tool_from_function`

```python
def foo(bar: int, baz: str) -> str:
    """Docstring thing."""
    raise NotImplementedError

structured_tool = StructuredTool.from_function(foo)
assert structured_tool.name == "foo"
assert structured_tool.args == {
    "bar": {"title": "Bar", "type": "integer"},
    "baz": {"title": "Baz", "type": "string"},
}
```

**확인된 동작:**
- `StructuredTool.from_function()`은 타입 어노테이션을 JSON Schema로 변환한다
- `args` 프로퍼티로 LLM이 사용할 파라미터 스키마에 접근할 수 있다
- 구현이 없어도 (`NotImplementedError`) 도구 선언 자체는 가능하다

---

### 3. 에러 처리 — `handle_tool_error`

`_FakeExceptionTool`은 실행 시 항상 `ToolException`을 발생시키는 픽스처다.

```python
class _FakeExceptionTool(BaseTool):
    def _run(self) -> str:
        raise ToolException()
```

#### `test_exception_handling_bool`

```python
tool_ = _FakeExceptionTool(handle_tool_error=True)
actual = tool_.run({})
assert actual == "Tool execution error"  # 기본 에러 메시지
```

#### `test_exception_handling_str`

```python
tool_ = _FakeExceptionTool(handle_tool_error="foo bar")
actual = tool_.run({})
assert actual == "foo bar"  # 커스텀 에러 메시지 문자열
```

#### `test_exception_handling_callable`

```python
def handling(e: ToolException) -> str:
    return "foo bar"

tool_ = _FakeExceptionTool(handle_tool_error=handling)
actual = tool_.run({})
assert actual == "foo bar"  # 콜백 함수로 에러를 처리
```

**확인된 동작:**
- `handle_tool_error=True` → ToolException 메시지를 반환
- `handle_tool_error="string"` → 지정된 문자열을 반환
- `handle_tool_error=callable` → callable에 ToolException을 전달하고 반환값 사용
- `handle_tool_error` 미설정 시 → ToolException이 전파됨 (별도 테스트 확인)

**패턴 의미:**
LangGraph agent 루프에서 도구 실패를 graceful하게 처리할 때
에러 메시지를 ToolMessage로 만들어 다음 LLM 호출에 넘기는 패턴을 지원한다.

---

### 4. Validation Error 처리 — `handle_validation_error`

#### `test_validation_error_handling_bool`

```python
tool_ = _MockStructuredTool(handle_validation_error=True)
actual = tool_.run({})  # 필수 인자 누락 → Pydantic ValidationError
assert actual == "Tool input validation error"
```

**확인된 동작:**
- Pydantic 스키마 검증 실패(ValidationError)도 별도로 핸들링할 수 있다
- `handle_tool_error`와는 독립적으로 `handle_validation_error`가 존재한다

---

### 5. `InjectedToolArg` — 런타임 주입 인자

#### `test_filter_injected_args_from_callbacks`

```python
@tool
def search_tool(
    query: str,
    state: Annotated[dict, InjectedToolArg()],
) -> str:
    """Search with injected state."""
    return f"Results for: {query}"

result = search_tool.invoke(
    {"query": "test query", "state": {"user_id": 123}},
    ...
)
```

**확인된 동작:**
- `InjectedToolArg`로 표시된 인자는 LLM이 생성하는 args schema에 포함되지 않는다
- 런타임에 별도로 주입되는 인자 (예: 현재 상태, 컨텍스트 객체)
- 콜백 핸들러에도 주입 인자는 필터링된다 (LLM에 보내지 않음)

#### `test_tool_injected_arg_with_custom_schema`

```python
class InputSchema(BaseModel):
    query: str

@tool(args_schema=InputSchema)
def search_tool(
    query: str, context: Annotated[CustomContext, InjectedToolArg]
) -> str:
    """Search with custom context."""
    ...
```

**확인된 동작:**
- 커스텀 `args_schema`와 `InjectedToolArg`를 함께 사용할 수 있다
- `args_schema`에 없는 주입 인자도 런타임에 정상 전달된다

---

### 6. `InjectedToolCallId` — ToolMessage 연동

#### `test_tool_injected_tool_call_id`

```python
@tool
def foo(x: int, tool_call_id: Annotated[str, InjectedToolCallId]) -> ToolMessage:
    """Foo."""
    return ToolMessage(str(x), tool_call_id=tool_call_id)

# ToolCall 형태로 invoke 필수
result = foo.invoke({
    "type": "tool_call",
    "args": {"x": 0},
    "name": "foo",
    "id": "bar",
})
assert result == ToolMessage("0", tool_call_id="bar")

# dict로 직접 invoke 시 에러
with pytest.raises(ValueError, match="InjectedToolCallId"):
    foo.invoke({"x": 0})
```

**확인된 동작:**
- `InjectedToolCallId`는 LLM이 생성한 `ToolCall`의 `id`를 자동으로 주입한다
- `ToolMessage` 반환 시 `tool_call_id`를 올바르게 설정할 수 있다
- `InjectedToolCallId`가 있는 도구는 반드시 `ToolCall` 형태(`{"type": "tool_call", ...}`)로 invoke해야 한다

**패턴 의미:**
LangGraph의 `ToolNode`가 AIMessage의 `tool_calls`를 실행하는 방식과 정확히 일치한다.
`ToolNode`는 내부적으로 `tool_call` dict를 구성해 각 도구를 invoke한다.

---

### 7. Pydantic 스키마 — Default 처리

#### `test_tool_args_schema_default_values`

```python
class SearchArgs(BaseModel):
    query: str = Field(..., description="The search query")
    page: int = Field(default=1, description="Page number")
    size: int = Field(default=10, description="Results per page")

@tool("search", args_schema=SearchArgs)
def search_tool(query: str, page: int, size: int) -> str:
    """Perform a search with pagination."""
    ...
```

**확인된 동작:**
- `args_schema`의 Pydantic default 값이 도구 실행 시 적용된다
- LLM이 `page`, `size`를 생략해도 기본값이 사용된다

#### `test_tool_default_factory_not_required`

```python
class Args(BaseModel):
    names: list[str] = Field(default_factory=list, description="Some names")

@tool(args_schema=Args)
def some_func(names: list[str] | None = None) -> None:
    """Do something."""

schema = convert_to_openai_tool(some_func)
params = schema["function"]["parameters"]
assert "names" not in params.get("required", [])
```

**확인된 동작:**
- `default_factory`가 있는 필드는 OpenAI function calling 스키마의 `required`에 포함되지 않는다
- LLM이 해당 인자를 생략해도 된다는 신호를 올바르게 전달한다

---

### 8. 불변성 보장

#### `test_tool_invoke_does_not_mutate_inputs`

```python
tool = StructuredTool(
    name="sample_tool",
    description="",
    args_schema={...},
    coroutine=async_no_op,
    func=sync_no_op,
)
inputs = {"foo": 1}
original_inputs = inputs.copy()
tool.invoke(inputs)
assert inputs == original_inputs  # invoke 후 입력이 변경되지 않아야 한다
```

**확인된 동작:**
- `tool.invoke()`는 입력 dict를 수정하지 않는다
- LangGraph 상태 관리에서 중요한 불변성 보장

---

### 9. `ToolOutputMixin` — 커스텀 반환 타입

#### `test_tool_return_output_mixin`

```python
class Bar(ToolOutputMixin):
    def __init__(self, x: int) -> None:
        self.x = x

@tool
def foo(x: int) -> Bar:
    """Foo."""
    return Bar(x=x)

result = foo.invoke({
    "type": "tool_call",
    "args": {"x": 0},
    "name": "foo",
    "id": "bar",
})
assert result == Bar(x=0)
```

**확인된 동작:**
- `ToolOutputMixin`을 상속한 커스텀 타입을 도구 반환값으로 사용할 수 있다
- `ToolMessage`가 아닌 커스텀 객체도 그대로 반환된다

---

## 핵심 추상화 맵

| 클래스/타입 | 역할 | 위치 |
|-------------|------|------|
| `BaseTool` | 모든 도구의 기반 클래스. `invoke()`, `run()`, `_run()` 정의 | `langchain_core.tools` |
| `StructuredTool` | 함수로부터 도구 생성. `from_function()` 팩토리 메서드 | `langchain_core.tools` |
| `@tool` 데코레이터 | 함수를 `BaseTool`로 변환 | `langchain_core.tools` |
| `ToolException` | 도구 실패 시 발생시키는 전용 예외 | `langchain_core.tools` |
| `InjectedToolArg` | LLM schema에서 숨기고 런타임에 주입하는 인자 표시자 | `langchain_core.tools.base` |
| `InjectedToolCallId` | `ToolCall.id`를 자동 주입. `ToolMessage` 연동에 사용 | `langchain_core.tools.base` |
| `ToolOutputMixin` | 커스텀 반환 타입 선언 | `langchain_core.messages.tool` |
| `convert_to_openai_tool()` | 도구를 OpenAI function calling 스키마로 변환 | `langchain_core.utils.function_calling` |

---

## LangGraph 연결 포인트

- **`ToolNode`** ← `InjectedToolCallId`의 사용 패턴과 정확히 대응
  - `ToolNode`는 `AIMessage.tool_calls`를 순회하며 `{"type": "tool_call", "args": ..., "id": ...}` 형태로 각 도구를 invoke
- **에러 처리** ← `handle_tool_error` 패턴
  - `ToolNode`에도 `handle_tool_errors` 옵션이 존재하며, 동일한 원리로 동작
- **불변성** ← `test_tool_invoke_does_not_mutate_inputs`
  - LangGraph의 상태 업데이트 메커니즘(reducer)은 입력 불변성에 의존

---

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: `9a671d7919597eb7226e2f87cdfbc161a774daf7`
- File: `libs/core/tests/unit_tests/test_tools.py` (3,743 lines)

---

## Open Questions

- `InjectedToolArg`를 `InjectedToolCallId` 없이 사용할 때 LangGraph `ToolNode`는 어떻게 주입하는가?
- `handle_tool_error`와 `handle_validation_error`를 동시에 설정할 때 우선순위는?
- `ToolOutputMixin`을 사용한 커스텀 반환 타입이 `ToolNode`에서 `ToolMessage`로 어떻게 변환되는가?
- `ArgsSchema`, `_DirectlyInjectedToolArg` 등 `base.py` 비공개 타입의 역할은?

---

## Related Pages

- [[Tool Calling]]
- [[LangChain]]
- [[LangGraph]]
- [[Subagents]]

## Sources

- `langchain-core-test-tools-2026-05-27`
