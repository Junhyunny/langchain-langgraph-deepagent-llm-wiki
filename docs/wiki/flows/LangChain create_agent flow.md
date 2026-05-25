---
type: flow
framework:
  - LangChain
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-28
sources:
  - langchain-source-tools-2026-05-23
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-source-bind-tools-function-calling-2026-05-23
  - langchain-agents-factory-2026-05-28
  - langchain-agents-middleware-types-2026-05-28
---

# LangChain create_agent flow

## Summary

`create_agent`는 `langchain.agents.factory.py`에 정의된 현재 공식 API로,
deprecated된 `create_react_agent` + `AgentExecutor` 조합의 후속이다.
**미들웨어(Middleware) 시스템**을 도입해 에이전트 동작을 모듈식으로 확장할 수 있다.

**핵심 차이**: `create_react_agent`가 `pre_model_hook`/`post_model_hook` 2개 확장점을 제공하는 반면,
`create_agent`는 최대 6가지 훅 포인트를 가진 `AgentMiddleware` 플러그인 시스템을 제공한다.

- 파일 위치: `langchain/agents/factory.py` (1,885 lines), `langchain/agents/middleware/types.py` (600+ lines)
- Repo: `langchain-ai/langchain`, Commit: UNKNOWN (.venv에서 읽음)

---

## 진입점

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[...],
    system_prompt="...",                          # optional
    middleware=[SummarizationMiddleware(), ...],  # optional
    response_format=MySchema,                    # optional
)
result = agent.invoke({"messages": [HumanMessage("...")]})
```

**검증됨:** `create_agent`는 `langchain/agents/factory.py` L697에 구현됨. `StateGraph`를 동적으로 구성하는 팩토리 함수다.

---

## AgentMiddleware 훅 시스템

*Source: `langchain-agents-middleware-types-2026-05-28`*

### 6가지 훅 포인트

| 훅 | 실행 시점 | 루프 내/외 |
|----|-----------|-----------|
| `before_agent` | 에이전트 전체 시작 전 (1회) | **루프 외** |
| `before_model` | 매 모델 호출 전 | **루프 내** |
| `wrap_model_call` | 모델 실행 자체를 래핑 (retry/cache 등) | **루프 내** |
| `after_model` | 매 모델 호출 후 | **루프 내** |
| `wrap_tool_call` | 각 도구 실행을 래핑 | **루프 내** |
| `after_agent` | 에이전트 전체 종료 후 (1회) | **루프 외** |

모든 훅은 `async` 버전(`a` 접두사)도 제공된다.

### AgentMiddleware 기본 클래스 (types.py L380)

```python
class AgentMiddleware(Generic[StateT, ContextT, ResponseT]):
    state_schema: type[StateT]  # 미들웨어 전용 상태 스키마
    tools: Sequence[BaseTool]   # 미들웨어가 추가하는 도구

    def before_agent(state, runtime) -> dict | None: ...
    def before_model(state, runtime) -> dict | None: ...
    def wrap_model_call(request, handler) -> ModelCallResult: ...
    def after_model(state, runtime) -> dict | None: ...
    def wrap_tool_call(request, handler) -> ToolMessage | Command: ...
    def after_agent(state, runtime) -> dict | None: ...
```

---

## 그래프 구조 (동적 노드 조립)

*Source: `langchain-agents-factory-2026-05-28` L1477–1679*

미들웨어가 어떤 훅을 구현했는지에 따라 노드가 동적으로 추가된다.

```
[START]
  ↓
{middleware}.before_agent   ← 구현된 미들웨어에만 추가 (1회)
  ↓
{middleware}.before_model   ← 구현된 미들웨어에만 추가 (루프마다)
  ↓
model                       ← 항상 존재
  ↓
{middleware}.after_model    ← 구현된 미들웨어에만 추가 (루프마다)
  ↓
[조건 분기]
  ├─ tool_calls 있음 → tools → loop_entry_node
  └─ tool_calls 없음 → {middleware}.after_agent → [END]
```

### 3가지 특수 노드 그룹

| 노드 | 역할 |
|------|------|
| `entry_node` | 시작 시 1회 진입 — before_agent 포함 |
| `loop_entry_node` | tools → 루프 재진입 시 — before_agent 제외 |
| `loop_exit_node` | 루프 각 이터레이션 끝 (after_model 또는 model) |
| `exit_node` | after_agent → END |

### `jump_to` 흐름 제어 (types.py L350)

`AgentState`의 `jump_to: JumpTo | None` 필드 — `EphemeralValue` (매 스텝 초기화):

```python
JumpTo = Literal["tools", "model", "end"]
```

미들웨어가 `before_model`/`after_model`에서 `{"jump_to": "end"}` 등을 반환해 흐름을 강제로 리디렉션 가능.

---

## create_react_agent vs create_agent 핵심 차이

| 항목 | `create_react_agent` (LangGraph) | `create_agent` (LangChain) |
|------|----------------------------------|---------------------------|
| 상태 | `remaining_steps` | `jump_to` (EphemeralValue) |
| 안전 종료 | `remaining_steps < 2` 조기 반환 | `recursion_limit: 9_999` |
| 확장점 | `pre_model_hook`, `post_model_hook` | 6가지 미들웨어 훅 |
| `bind_tools` 시점 | 에이전트 생성 시 (1회) | **매 모델 호출 시** (`_get_bound_model`) |
| v1/v2 Send API | Send("tools", ToolCallWithContext) | 없음 (단순 ToolNode) |
| deprecated | LangGraph v1.0부터 | 현재 활성 API |

---

## bind_tools 지연 바인딩

*Source: `langchain-agents-factory-2026-05-28` L1162*

`create_agent`는 **매 모델 호출 시** `_get_bound_model(request)` 내에서 `bind_tools()` 실행:

```python
def _get_bound_model(request):
    # request.tools: 미들웨어가 override() 로 수정 가능
    # request.response_format: 미들웨어가 수정 가능
    return model.bind_tools(final_tools), effective_response_format
```

**의미**: `wrap_model_call` 미들웨어가 `request.override(tools=[...])` 로 도구 목록을 런타임에 변경 가능.
→ `tool_selection`, `tool_emulator` 미들웨어가 이 방식으로 동적 도구 관리.

---

## ModelRequest / ModelResponse (types.py)

### ModelRequest (불변, override() 패턴) — L89

```python
@dataclass
class ModelRequest[ContextT]:
    model: BaseChatModel
    messages: list[AnyMessage]
    system_message: SystemMessage | None
    tools: list[BaseTool | dict]
    response_format: ResponseFormat | None
    tool_choice: Any | None
    state: AgentState
    runtime: Runtime[ContextT]
    model_settings: dict

    def override(self, **kwargs) -> ModelRequest:  # 새 인스턴스 반환
        ...
```

**직접 속성 할당 deprecated**: `request.tools = [...]` 대신 `request.override(tools=[...])` 사용.

### wrap_model_call 반환 타입 (L271, L289)

```python
# 단순 모델 응답
ModelResponse  → result: list[BaseMessage], structured_response: ...

# 추가 상태 업데이트 포함
ExtendedModelResponse → model_response + command: Command | None
  # command.goto / command.resume / command.graph 는 NotImplementedError
```

---

## wrap_model_call 미들웨어 체이닝

*Source: `langchain-agents-factory-2026-05-28` L221*

`_chain_model_call_handlers()`: right-to-left 합성 → 첫 번째 미들웨어가 outermost (양파 모델):

```
Request:  [mw1] → [mw2] → [mw3] → model
Response: model → [mw3] → [mw2] → [mw1]
```

---

## AutoStrategy (response_format 자동 감지)

실행 시점(`_get_bound_model`)에서:
1. 모델이 `ProviderStrategy` 지원 → `model.with_structured_output()` 사용
2. 미지원 → `ToolStrategy` (도구 호출 방식으로 구조화 출력 유도)
3. Gemini < 3-series: 도구와 structured output 동시 불가 → ToolStrategy 강제

---

## 빌트인 미들웨어 목록

`langchain/agents/middleware/` 에서 확인됨 (⚠️ 내부 구현은 아직 읽지 않음):

| 파일 | 역할 |
|------|------|
| `summarization.py` | 메시지 히스토리 요약 |
| `human_in_the_loop.py` | HITL (사람 개입) |
| `pii.py` | PII 감지/제거 |
| `_redaction.py` | 내용 리덱션 |
| `model_retry.py` | 모델 호출 재시도 |
| `model_fallback.py` | 모델 폴백 |
| `model_call_limit.py` | 모델 호출 횟수 제한 |
| `tool_retry.py` | 도구 재시도 |
| `tool_emulator.py` | 도구 에뮬레이션 |
| `tool_selection.py` | 동적 도구 선택 |
| `tool_call_limit.py` | 도구 호출 횟수 제한 |
| `file_search.py` | 파일 검색 |
| `shell_tool.py` | 쉘 실행 |
| `context_editing.py` | 컨텍스트 편집 |
| `todo.py` | Todo 추적 |

---

## 상태 스키마 병합

미들웨어 각각이 자신의 `state_schema`를 가질 수 있으며, `_resolve_schemas()`로 병합됨:

`OmitFromSchema` 어노테이션 (types.py L329):
- `PrivateStateAttr` = `OmitFromInput` + `OmitFromOutput` → 미들웨어 내부 상태 필드를 input/output schema에서 숨김

---

## Tool 등록 경로 (기존 검증됨)

*Source: `langchain-source-tools-2026-05-23`*

```
@tool 데코레이터 또는 StructuredTool.from_function()
    │
    ├─ create_schema_from_function(name, func)
    │       └─ args_schema (Pydantic BaseModel)
    │
    └─ StructuredTool(name, func, coroutine, args_schema, description)
            └─ .tool_call_schema → LLM API에 전달될 JSON schema
```

## bind_tools → LLM API payload 변환 (기존 검증됨)

*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

```
BaseTool.tool_call_schema
    → bind_tools([tool])           ← provider 구현체 (BaseChatOpenAI 등)
    → convert_to_openai_tool(tool)
    → {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
```

## Tool 실행 경로 (기존 검증됨)

```
AIMessage.tool_calls → BaseTool.invoke(ToolCall)
    → _prep_run_args → run(tool_input, tool_call_id)
    → Pydantic validation → StructuredTool._run(*args, **kwargs)
    → ToolMessage(content, tool_call_id, name, status)
```

---

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN (.venv에서 읽음)
- Files:
  - `langchain/agents/factory.py` (1,885 lines)
    - `create_agent`: L697
    - `_chain_model_call_handlers`: L221
    - `_get_bound_model`: L1162
    - `model_node`: L1318
    - 그래프 노드/엣지 동적 조립: L1477–1679
    - `recursion_limit: 9_999`: L1665
  - `langchain/agents/middleware/types.py` (600+ lines)
    - `AgentMiddleware`: L380
    - `ModelRequest`: L89
    - `ModelResponse`: L271
    - `ExtendedModelResponse`: L289
    - `AgentState`: L350
    - `OmitFromSchema`: L329

---

## 관련 페이지

- [[LangChain]]
- [[LangGraph create_react_agent flow]]
- [[LangGraph ToolNode flow]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Human-in-the-Loop]]
- [[Guardrails]]

---

## Open Questions

- 각 빌트인 미들웨어(`summarization.py`, `pii.py`, `tool_selection.py` 등)의 내부 구현은? — Needs Source
- `wrap_model_call`과 `before_model`의 실질적 차이는? (하나는 handler를 직접 감싸고, 다른 하나는 상태 변환만)
- `before_agent` → `before_model` 전환 시 `remaining_steps` 없는데 무한 루프 방어는 recursion_limit 9999에만 의존하는가?
- `wrap_tool_call`이 `Command`를 반환할 때 어떤 상태 변화가 가능한가?
- Deep Agents의 middleware 시스템과 이 구조는 동일한가, 유사한가, 다른가? — Needs Source

---

## Sources

- `langchain-source-tools-2026-05-23`
- `langchain-source-create-agent-factory-2026-05-23`
- `langchain-source-bind-tools-function-calling-2026-05-23`
- `langchain-agents-factory-2026-05-28`
- `langchain-agents-middleware-types-2026-05-28`
