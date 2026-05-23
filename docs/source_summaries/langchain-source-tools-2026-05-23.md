---
type: source_summary
source_id: langchain-source-tools-2026-05-23
framework: LangChain
retrieved_at: 2026-05-23
status: final
confidence: high
---

# Source Summary: LangChain Tools Source Code (BaseTool / StructuredTool / @tool)

## Source Info
- **Source ID:** `langchain-source-tools-2026-05-23`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/langchain/tree/master/libs/core/langchain_core/tools
- **Retrieved At:** 2026-05-23
- **Files:** `convert.py`, `structured.py`, `base.py`

---

## Key Facts

### @tool 데코레이터 (`convert.py`)
- `@tool` 데코레이터의 실제 타입은 함수 `tool()`이며, 4가지 `@overload` 시그니처를 가진다
- `infer_schema=True`(기본값)인 경우 → 항상 `StructuredTool` 반환
- `infer_schema=False`이고 `args_schema=None`인 경우 → 단순 `Tool` 반환 (string→string)
- async 함수(`async def`)를 데코레이트하면 `coroutine` 파라미터로, sync 함수는 `func` 파라미터로 분리
- `Runnable`을 데코레이트할 수 있으며, 이 경우 이름(str)이 필수
- 내부적으로 `StructuredTool.from_function(func, coroutine, name=..., description=..., args_schema=..., ...)` 호출로 위임
- `description` 우선순위: `@tool(description=...)` > 함수 docstring > `args_schema` description

### StructuredTool (`structured.py`)
- `BaseTool`을 상속하는 구체 구현 클래스
- 두 개의 핵심 필드: `func: Callable | None`, `coroutine: Callable | None`
- `from_function` classmethod가 실제 생성 진입점:
  1. `create_schema_from_function(name, source_function, ...)` 호출 → `args_schema` 자동 생성
  2. docstring에서 `description_` 추출 (없으면 `ValueError`)
  3. `StructuredTool(name=..., func=..., coroutine=..., args_schema=..., description=...)` 반환
- `_run`: `self.func(*args, **kwargs)` 호출. sync 함수 없으면 `NotImplementedError`
- `_arun`: `self.coroutine(...)` 호출. coroutine 없으면 부모의 `_arun`으로 폴백(thread pool에서 `_run` 실행)
- `ainvoke`: coroutine 없으면 `run_in_executor`로 sync `invoke`를 thread pool 실행

### BaseTool (`base.py`)
- `RunnableSerializable[str | dict | ToolCall, Any]` 상속 → `invoke`/`ainvoke`/`batch`/`stream` 자동 지원
- 핵심 필드: `name`, `description`, `args_schema`, `return_direct`, `handle_tool_error`, `handle_validation_error`, `response_format`, `extras`
- **실행 경로 (sync):**
  `invoke` → `_prep_run_args` → `run` → `_to_args_and_kwargs` → `_parse_input` → `_run` → `_format_output`
- **`tool_call_schema`** property: LLM에 전달되는 스키마. `InjectedToolArg`로 어노테이션된 필드를 제외한 subset 모델 반환
- **`_parse_input`**: `args_schema`로 Pydantic validation. `InjectedToolCallId` 주입 처리
- **`_to_args_and_kwargs`**: string input → `(tool_input,), {}`. dict input → `(), tool_input.copy()`
- **에러 처리:**
  - `ToolException` → `handle_tool_error` 설정에 따라 에러 문자열로 변환 또는 re-raise
  - `ValidationError` → `handle_validation_error` 설정에 따라 처리
  - 기타 예외 → 항상 re-raise
- **`_format_output`**: `tool_call_id` 있으면 `ToolMessage(content, tool_call_id=..., name=..., status=...)` 반환. 없으면 content 그대로 반환

### `create_schema_from_function` (`base.py`)
- pydantic `validate_arguments`로 함수 시그니처에서 inferred model 생성
- `FILTERED_ARGS = ("run_manager", "callbacks")` 자동 제외
- `InjectedToolArg` 어노테이션된 파라미터도 제외 가능 (`include_injected=False` 시)
- `parse_docstring=True`이면 Google Style docstring에서 파라미터별 description 추출
- 최종 결과는 `_create_subset_model`로 만든 Pydantic `BaseModel` subclass

### InjectedToolArg 시스템
- `InjectedToolArg`: LLM schema에서 제외되는 runtime 주입 인자의 base annotation
- `InjectedToolCallId(InjectedToolArg)`: tool_call_id를 runtime에 주입받을 때 사용
- `_DirectlyInjectedToolArg`: `ToolRuntime` 등 직접 타입으로 주입되는 인자용
- `_is_injected_arg_type()`: `Annotated[..., InjectedToolArg()]` 패턴을 감지

---

## Important Terms

- **StructuredTool** — `@tool`이 기본적으로 생성하는 구체 클래스. `func`/`coroutine` 필드 보유
- **tool_call_schema** — LLM에 전달되는 JSON schema. `InjectedToolArg` 필드 제외
- **InjectedToolArg** — LLM schema에 노출되지 않고 runtime에 주입되는 파라미터의 annotation
- **InjectedToolCallId** — `AIMessage.tool_calls[].id`를 tool 함수에 runtime 주입할 때 사용
- **ToolException** — tool 에러를 agent에 알리는 전용 예외. `handle_tool_error`로 처리
- **_format_output** — tool 출력을 `ToolMessage`로 래핑하는 내부 함수
- **FILTERED_ARGS** — `("run_manager", "callbacks")` — schema에서 항상 제외되는 인자

---

## Interpretation

- `@tool` 데코레이터는 단순히 `StructuredTool.from_function` 호출의 syntactic sugar
- docstring → LLM 전달 경로: `docstring` → `create_schema_from_function` → `description_` 필드 → `tool_call_schema` JSON schema의 `description` key → LLM tool spec
- **파라미터별 description** 전달 경로: `Annotated[type, "description string"]` 또는 Google Style docstring `Args:` 섹션 → `_infer_arg_descriptions` → `_create_subset_model`의 `descriptions` dict → 각 파라미터의 `description` 필드
- LLM tool call → 실행 → 응답 흐름:
  1. LLM이 `AIMessage.tool_calls = [{name, args, id}]` 반환
  2. `BaseTool.invoke(ToolCall)` 호출
  3. `_prep_run_args`에서 `tool_call_id = ToolCall["id"]` 추출
  4. `run()` → `_to_args_and_kwargs` → `_run()`
  5. `_format_output(content, tool_call_id=id, ...)` → `ToolMessage(content, tool_call_id=id)`
  6. Agent가 `ToolMessage`를 다음 LLM 호출의 메시지 히스토리에 추가

---

## Implications for My AI Agent Project

- tool 함수에 `async def`를 쓰면 자동으로 async tool이 됨. 별도 설정 불필요
- `handle_tool_error=True`를 설정하면 `ToolException` 발생 시 에이전트가 중단되지 않고 에러 메시지를 LLM에 전달
- `InjectedToolCallId`를 사용하면 tool 함수 내에서 `ToolMessage`를 직접 구성할 수 있음
- `response_format="content_and_artifact"`로 tool 출력에 구조화된 아티팩트를 포함할 수 있음

---

## Open Questions

- `@tool` 데코레이터로 만든 tool의 `args_schema.model_json_schema()`가 실제로 LLM API 호출 시 어떤 형태의 payload로 변환되는가? (ChatModel의 `bind_tools` 경로 확인 필요)
- `ToolRuntime`(직접 주입 타입)의 전체 필드 구성은? (`_DirectlyInjectedToolArg` 상속 클래스)
- `BaseTool.run()`의 callback(`on_tool_start`, `on_tool_end`) 이벤트가 LangSmith 트레이싱과 어떻게 연결되는가?

---

## Used By

- [[Tool Calling]] — `docs/wiki/concepts/Tool Calling.md`
- [[LangChain]] — `docs/wiki/frameworks/LangChain.md`
- [[LangChain Code Map]] — `docs/wiki/codebase/LangChain Code Map.md`
- [[LangChain create_agent flow]] — `docs/wiki/flows/LangChain create_agent flow.md`

---

## Notes

- `simple.py`의 `Tool` 클래스(string→string)는 수집하지 않음. `StructuredTool`이 실질적 주요 구현체
- pydantic v1/v2 혼용 지원 코드(`validate_arguments_v1` 분기)는 하위호환성 레거시
