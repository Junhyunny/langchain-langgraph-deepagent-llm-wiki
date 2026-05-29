---
type: flow
framework:
  - LangGraph
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-29
sources:
  - langgraph-prebuilt-tool-node-2026-05-27
  - langchain-agents-factory-2026-05-28
---

# LangGraph ToolNode 실행 흐름

## Summary

`ToolNode`는 LangGraph 워크플로에서 도구를 실행하는 사전 구현 노드다.
`AIMessage.tool_calls`를 파싱해 등록된 `BaseTool` 인스턴스를 병렬 실행하고,
결과를 `ToolMessage` 리스트로 상태에 반환한다.

LangChain Core의 `@tool`/`BaseTool`과 LangGraph 상태 그래프 사이의 경계 역할을 한다.

## Why It Matters

- `InjectedToolCallId`, `InjectedState`, `InjectedStore` 같은 주입 패턴이 실제로 어디서 실행되는지 알 수 있다
- LLM이 생성한 `tool_calls`가 어떻게 `ToolMessage`로 변환되는지의 전체 경로를 볼 수 있다
- 에러 처리, 상태 주입, 보안(LLM 위조 방지)이 어느 시점에 일어나는지 확인할 수 있다

---

## 파일 위치

```
langgraph/prebuilt/tool_node.py  (2,030 lines)
```

- Repo: `langchain-ai/langgraph`
- Commit: UNKNOWN (.venv에서 읽음)

---

## 핵심 클래스/함수 맵

| 이름 | 역할 |
|------|------|
| `ToolNode` | 메인 노드 클래스. `RunnableCallable` 상속 |
| `ToolRuntime` | 도구에 주입되는 런타임 컨텍스트 (state, store, config, stream_writer 등) |
| `ToolCallRequest` | 도구 실행 요청 객체. 미들웨어에 전달됨 |
| `ToolCallWrapper` | 도구 실행을 감싸는 미들웨어 타입 |
| `_InjectedArgs` | 도구별 주입 인자 메타데이터 (init 시점에 한 번 분석) |
| `InjectedState` | 그래프 상태를 도구 인자로 주입하는 어노테이션 |
| `InjectedStore` | 퍼시스턴트 스토어를 도구 인자로 주입하는 어노테이션 |
| `tools_condition` | AIMessage에 tool_calls가 있으면 `"tools"`, 없으면 `"__end__"` 라우팅 |
| `_get_all_injected_args` | 도구 시그니처 분석 → `_InjectedArgs` 생성 |
| `_inject_tool_args` | 실행 직전 state/store/runtime을 tool_call 인자에 주입 |
| `_handle_tool_error` | 에러를 에러 메시지 문자열로 변환 |

---

## 실행 흐름

### 1. 초기화 (`__init__`)

```python
for tool in tools:
    tool_ = create_tool(tool) if not isinstance(tool, BaseTool) else tool
    self._tools_by_name[tool_.name] = tool_
    self._injected_args[tool_.name] = _get_all_injected_args(tool_)
```

- 모든 도구를 `BaseTool`로 변환해 `_tools_by_name` dict에 저장
- `_get_all_injected_args()`로 **도구 시그니처를 한 번만 분석** → `_InjectedArgs` 캐시
- 이후 실행 시마다 리플렉션 없이 캐시 사용

### 2. 입력 파싱 (`_parse_input`)

입력 3가지 형태를 모두 지원한다.

```
┌─────────────────────────────────────────────────────────┐
│ Input Type                 │ 동작                        │
├────────────────────────────┼─────────────────────────────┤
│ list[-1].type == tool_call │ 직접 tool_calls 리스트 사용  │
│ dict with __type==ctx      │ Send API(ToolCallWithContext) │
│ dict/BaseModel + messages  │ 마지막 AIMessage.tool_calls  │
└────────────────────────────┴─────────────────────────────┘
```

핵심 경로 (일반 에이전트):
```python
latest_ai_message = next(m for m in reversed(messages) if isinstance(m, AIMessage))
tool_calls = list(latest_ai_message.tool_calls)
```

### 3. ToolRuntime 생성

각 tool_call마다 `ToolRuntime` 인스턴스 생성:

```python
tool_runtime = ToolRuntime(
    state=state,           # 현재 그래프 상태
    tool_call_id=call["id"],  # LLM이 생성한 tool call ID
    config=cfg,
    context=runtime.context,
    store=runtime.store,
    stream_writer=runtime.stream_writer,
    tools=list(self.tools_by_name.values()),
    ...
)
```

### 4. 병렬 실행

```python
with get_executor_for_config(config) as executor:
    outputs = list(
        executor.map(self._run_one, tool_calls, input_types, tool_runtimes)
    )
```

- `ThreadPoolExecutor`로 여러 tool_calls를 **병렬 실행**
- 단일 `AIMessage`에 여러 tool_calls가 있으면 동시에 실행

### 5. `_run_one` → `_execute_tool_sync`

```python
# 미들웨어(wrap_tool_call) 없으면 직접 실행
tool_request = ToolCallRequest(tool_call=call, tool=tool, state=..., runtime=...)
return self._execute_tool_sync(tool_request, input_type, config)
```

### 6. 인자 주입 (`_inject_tool_args`) — 핵심

```python
# 1. state/store/runtime 주입
injected_args = {}
for tool_arg, state_field in injected.state.items():
    injected_args[tool_arg] = state[state_field]  # 또는 전체 state
if injected.store:
    injected_args[injected.store] = tool_runtime.store
if injected.runtime:
    injected_args[injected.runtime] = tool_runtime

# 2. LLM 공급 주입 인자를 제거 (보안!)
stripped_args = {k: v for k, v in tool_call["args"].items()
                 if k not in injected.all_injected_keys}

# 3. 신뢰된 값만 병합
tool_call["args"] = {**stripped_args, **injected_args}
```

**보안 포인트**: LLM이 `InjectedState` 필드를 직접 채워 상태를 위조하려 해도
`stripped_args`에서 제거되고 시스템이 신뢰된 값만 주입한다.

### 7. 도구 실행

```python
# InjectedToolCallId 연결 포인트!
call_args = {**injected_call, "type": "tool_call"}
response = tool.invoke(call_args, config)
```

- `"type": "tool_call"`을 추가하는 것이 핵심
- LangChain Core의 `InjectedToolCallId`는 이 형태를 감지해 `call["id"]`를 추출해 도구에 주입한다
- 즉, `ToolNode`가 `tool.invoke({"type": "tool_call", ..., "id": "bar"})` 형태로 호출하면
  `InjectedToolCallId`가 `"bar"`를 도구 파라미터에 자동 주입

### 8. 에러 처리

```python
try:
    response = tool.invoke(call_args, config)
except ValidationError as exc:
    # 주입 인자 관련 에러는 필터링 (LLM에게는 관련 없는 에러)
    filtered_errors = _filter_validation_errors(exc, injected)
    raise ToolInvocationError(call["name"], exc, call["args"], filtered_errors)
except GraphBubbleUp:
    raise  # interrupt()는 항상 전파
except Exception as e:
    if not self._handle_tool_errors or not isinstance(e, handled_types):
        raise
    content = _handle_tool_error(e, flag=self._handle_tool_errors)
    return ToolMessage(content=content, ..., status="error")
```

- `GraphBubbleUp` (= `interrupt()`)은 항상 전파 (절대 삼키지 않음)
- `ValidationError`는 `ToolInvocationError`로 래핑해 LLM에게 유용한 메시지 전달
- 기본 `handle_tool_errors`는 `ToolInvocationError`만 잡고 나머지는 재발생

### 9. 응답 정규화 (`_normalize_tool_response`)

```python
if isinstance(response, Command):
    return self._validate_tool_command(response, ...)
if isinstance(response, ToolMessage):
    response.content = msg_content_output(response.content)
    return response
```

- 도구가 `str`을 반환하면 → 어디서 ToolMessage로 변환? → `BaseTool.invoke()`에서 처리 (LangChain Core)
- 도구가 `ToolMessage`를 반환하면 → content를 JSON-safe 형태로 변환
- 도구가 `Command`를 반환하면 → 상태 업데이트 검증 후 반환

### 10. 출력 결합 (`_combine_tool_outputs`)

```python
# dict 입력 → {"messages": [ToolMessage(...)]}
# list 입력 → [ToolMessage(...)]
return flat_outputs if input_type == "list" else {self._messages_key: flat_outputs}
```

---

## InjectedState 주입 메커니즘

```python
class InjectedState(InjectedToolArg):
    def __init__(self, field: str | None = None) -> None:
        self.field = field
```

- `InjectedState()` 또는 `InjectedState(None)` → 전체 state dict 주입
- `InjectedState("messages")` → `state["messages"]`만 주입

사용 예:

```python
@tool
def state_tool(x: int, state: Annotated[dict, InjectedState]) -> str:
    return f"Messages: {len(state['messages'])}"

@tool
def foo_tool(x: int, foo: Annotated[str, InjectedState("foo")]) -> str:
    return foo + str(x)
```

---

## ToolRuntime 구조

```python
@dataclass
class ToolRuntime(_DirectlyInjectedToolArg, Generic[ContextT, StateT]):
    state: StateT            # 현재 그래프 상태
    context: ContextT        # 런타임 컨텍스트 (사용자 정의)
    config: RunnableConfig   # 실행 설정
    stream_writer: StreamWriter
    tool_call_id: str | None # 현재 tool call의 ID
    store: BaseStore | None  # 퍼시스턴트 스토어
    tools: list[BaseTool]    # 사용 가능한 모든 도구
```

`ToolRuntime`은 `_DirectlyInjectedToolArg`를 상속 → 타입 힌트만으로 감지, `Annotated` 불필요.

파라미터 이름이 `runtime`이거나 타입이 `ToolRuntime`이면 자동 주입:

```python
@tool
def my_tool(x: int, runtime: ToolRuntime) -> str:
    messages = runtime.state["messages"]
    print(runtime.tool_call_id)
    runtime.store.put(("key",), "data", value)
    runtime.stream_writer("processing...")
    return str(x)
```

---

## tools_condition 라우팅

```python
def tools_condition(state, messages_key="messages") -> Literal["tools", "__end__"]:
    ai_message = messages[-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"
```

표준 ReAct 패턴:

```
llm_node → tools_condition → "tools" → ToolNode → llm_node → ...
                           → "__end__"
```

---

## LangChain Core ↔ LangGraph 연결 포인트 요약

| LangChain Core 개념 | LangGraph ToolNode 연결 |
|---------------------|------------------------|
| `InjectedToolCallId` | `_execute_tool_sync`에서 `"type": "tool_call"` 추가 → LangChain Core가 `call["id"]` 추출해 주입 |
| `InjectedToolArg` | `_get_all_injected_args`로 감지 → `_inject_tool_args`에서 주입 |
| `InjectedState` | LangGraph 전용. `tool_runtime.state`에서 추출해 주입 |
| `InjectedStore` | LangGraph 전용. `tool_runtime.store` 주입 |
| `handle_tool_error` | `BaseTool` 수준에서 처리. ToolNode는 `ToolInvocationError`만 기본 처리 |
| `ToolOutputMixin` | `_normalize_tool_response`에서 처리하지 않음 → `BaseTool.invoke()`에서 처리 |

---

## Direct ToolNode 실행 실험

2026-05-28에 `examples/langgraph_core/08_toolnode_direct.py`로 `ToolNode`를 단독 runnable로 실행했다.

확인한 내용:

- state dict 입력은 `{"messages": [ToolMessage(...)]}` 형태로 반환된다.
- message list 입력은 `[ToolMessage(...)]` 형태로 반환된다.
- direct tool call list 입력은 로컬 버전에서 `{"messages": [ToolMessage(...)]}` 형태로 반환된다.
- standalone `ToolNode.invoke()`는 underlying runnable의 `runtime` 파라미터 때문에 config에 `Runtime`이 필요하다. compiled graph 안에서는 LangGraph가 자동 주입한다.
- `wrap_tool_call`은 `ToolCallRequest`를 받고, `request.override(tool_call=...)`로 실행 직전 인자를 바꿀 수 있다.
- LangChain `create_agent()`는 `AgentMiddleware.wrap_tool_call`을 합성한 뒤 `ToolNode(..., wrap_tool_call=...)`로 연결한다.

Source: [[2026-05-28 langgraph toolnode direct]]

---

## Command 반환 실험

2026-05-29에 `examples/langgraph_core/09_toolnode_command_outputs.py`로 `ToolNode`의 `Command` 반환 경로를 확인했다.

확인한 내용:

- standalone `ToolNode.invoke()`는 `Command`를 적용하지 않고 `[Command(...)]` 형태로 반환한다.
- compiled graph 안에서는 `Command.update`가 실제 state update로 적용된다.
- `wrap_tool_call`은 도구 실행을 건너뛰고 직접 `Command(update=..., goto=...)`를 반환할 수 있다.
- `Command(goto="after")`는 정적 `tools -> after` edge 없이도 `after` 노드로 라우팅했다.
- 현재 graph에 대한 `Command.update`에는 matching `ToolMessage(tool_call_id=...)`가 필요하다. 없으면 `ValueError`가 발생한다.

Source: [[2026-05-29 langgraph toolnode command outputs]]

---

## Parent Command + Send 실험

2026-05-30에 `examples/langgraph_core/10_toolnode_parent_command_send.py`로 child graph 안의 `ToolNode`가 parent graph로 `Send`를 올리는 경로를 확인했다.

확인한 내용:

- child graph tool이 `Command(graph=Command.PARENT, goto=[Send("collector", {...})])`를 반환할 수 있다.
- parent graph에 정적 `child -> collector` edge가 없어도 parent `collector` 노드가 실행된다.
- tool call 2개가 각각 parent `Send`를 반환하면 parent collector가 2번 실행된다.
- `ToolNode._combine_tool_outputs()`는 여러 parent `Send` command를 하나의 parent command로 병합한다.
- `Command.PARENT + Send` 경로는 current graph `Command(update=...)`와 달리 matching `ToolMessage`를 요구하지 않았다.

Source: [[2026-05-30 langgraph toolnode parent command send]]

---

## Source Code References

- Repo: `langchain-ai/langgraph`
- Commit: UNKNOWN
- File: `langgraph/prebuilt/tool_node.py` (2,030 lines)

주요 함수 위치:
- `ToolNode.__init__`: line ~743
- `ToolNode._func`: line ~793
- `ToolNode._parse_input`: line ~1224
- `ToolNode._inject_tool_args`: line ~1315
- `ToolNode._execute_tool_sync`: line ~922
- `_get_all_injected_args`: line ~1967
- `InjectedState`: line ~1753
- `InjectedStore`: line ~1829
- `ToolRuntime`: line ~1662
- `tools_condition`: line ~1582

---

## Open Questions

- `ToolOutputMixin`을 반환하는 도구의 출력은 `BaseTool.invoke()` 내부에서 어떻게 처리되는가? (LangChain Core 쪽)
- `wrap_tool_call` 미들웨어를 사용한 retry 패턴이 HITL과 어떻게 조합되는가?
- ✅ `wrap_tool_call`이 `Command`를 반환할 때의 current graph update/goto는 확인됨. `Command.update`는 compiled graph가 적용하고, `Command.goto`는 정적 edge 없이도 대상 노드로 라우팅할 수 있다. Source: [[2026-05-29 langgraph toolnode command outputs]]
- ✅ `Command(graph=Command.PARENT, goto=[Send(...)])`는 parent graph의 대상 노드를 동적으로 실행한다. 여러 Send는 parent command로 병합되어 parent collector를 여러 번 호출할 수 있다. Source: [[2026-05-30 langgraph toolnode parent command send]]
- `_extract_state`에서 `CONFIG_KEY_READ`를 통해 채널에서 상태를 읽는 경로 — Send API와의 관계?

---

## Related Pages

- [[Tool Calling]]
- [[LangGraph]]
- [[LangChain]]
- [[Human-in-the-Loop]]
- [[Subagents]]
- [[test_langchain_tool_calling_map]]
- [[2026-05-28 langgraph toolnode direct]]
- [[2026-05-29 langgraph toolnode command outputs]]
- [[2026-05-30 langgraph toolnode parent command send]]
- [[ToolNode in LangGraph vs LangChain create_agent]]

## Sources

- `langgraph-prebuilt-tool-node-2026-05-27`
- `langchain-agents-factory-2026-05-28`
