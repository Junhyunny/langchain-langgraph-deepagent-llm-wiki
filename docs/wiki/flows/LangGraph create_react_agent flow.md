---
type: flow
framework:
  - LangGraph
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-28
sources:
  - langgraph-prebuilt-chat-agent-executor-2026-05-28
---

# LangGraph create_react_agent 흐름

## Summary

`create_react_agent`는 LangGraph `prebuilt/chat_agent_executor.py`에 정의된 함수로,
**LLM + ToolNode + StateGraph**를 조립해 ReAct 루프를 실행하는 `CompiledStateGraph`를 반환한다.

> ⚠️ **Deprecated**: LangGraph v1.0부터 `langchain.agents.create_agent`로 이동됨.
> `langgraph.prebuilt.create_react_agent`는 하위 호환용으로만 유지됨.

## Why It Matters

- ToolNode가 어떻게 StateGraph 안에서 조립되는지 전체 그림을 볼 수 있다
- v1(일괄 처리) vs v2(Send API 개별 dispatch) 차이를 이해할 수 있다
- `pre_model_hook`, `post_model_hook` 확장점이 어디에 삽입되는지 알 수 있다
- `remaining_steps`로 RecursionError 없이 루프를 안전하게 종료하는 패턴을 볼 수 있다

---

## 파일 위치

```
langgraph/prebuilt/chat_agent_executor.py  (1,015 lines)
```

- Repo: `langchain-ai/langgraph`
- Commit: UNKNOWN (.venv에서 읽음)

---

## 진입점

```python
from langgraph.prebuilt import create_react_agent

graph = create_react_agent(
    model,
    tools=[...],
    prompt="...",       # optional
    version="v2",       # default
    checkpointer=...,   # optional
)
```

---

## 그래프 구조 (v2, tool_calling 활성화 기준)

### 기본 노드 구성

```
[start]
  ↓
pre_model_hook  (optional)
  ↓
agent           (call_model: prompt | model → AIMessage)
  ↓ [should_continue]
  ├── tool_calls 있음 → [Send("tools", ToolCallWithContext)] × N  (v2)
  │                      ↓
  │                   tools  (ToolNode)
  │                      ↓ route_tool_responses
  │                      └── return_direct? → END
  │                          otherwise     → agent (entrypoint)
  └── tool_calls 없음 → post_model_hook? → generate_structured_response? → END
```

### v1 vs v2 핵심 차이

| | v1 | v2 (default) |
|--|--|--|
| 도구 dispatch 단위 | `"tools"` 노드에 전체 message 전달 | `Send("tools", ToolCallWithContext(call))` → 개별 tool_call |
| ToolNode 입력 | `AIMessage` (tool_calls 전체 포함) | `ToolCallWithContext` (tool_call 1개 + state) |
| 병렬 실행 위치 | ToolNode 내부 `ThreadPoolExecutor` | StateGraph `Send` API |

---

## 핵심 헬퍼 함수

### `_get_prompt_runnable(prompt)` (L137–170)

`prompt` 타입에 따라 적절한 `Runnable`로 변환:

| 타입 | 동작 |
|------|------|
| `None` | `state["messages"]` 그대로 |
| `str` | `[SystemMessage(str)] + messages` |
| `SystemMessage` | `[prompt] + messages` |
| `Callable` / `Runnable` | state 전체를 받아 LLM 입력 생성 |

### `_should_bind_tools(model, tools)` (L173–217)

모델에 이미 `bind_tools()`가 호출됐는지 확인:
- `RunnableBinding` + `"tools" in kwargs` → 이미 바인딩됨
- 도구 수 불일치 → `ValueError`
- 미등록 도구 있음 → `ValueError`
- 바인딩 안 됐으면 → `model.bind_tools(tool_classes)` 자동 호출

### `_validate_chat_history(messages)` (L243–271)

`AIMessage.tool_calls` 중 대응하는 `ToolMessage`가 없는 항목 있으면 `ValueError`:
```
"Every tool call ... MUST have a corresponding ToolMessage"
```

---

## call_model 노드 (L661–721)

```
state → _get_model_input_state → model.invoke → AIMessage
```

**remaining_steps 체크 (`_are_more_steps_needed`, L620–634):**
```python
if remaining_steps < 2 and has_tool_calls:
    return {"messages": [AIMessage(content="Sorry, need more steps...")]}
if remaining_steps < 1 and all_tools_return_direct:
    return {"messages": [AIMessage(content="Sorry, need more steps...")]}
```
→ `RecursionError` 없이 안전 종료. `remaining_steps`는 `RemainingSteps` managed value로 자동 감소.

---

## should_continue 라우팅 (L831–859)

```python
def should_continue(state):
    last_message = messages[-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return END  # (or post_model_hook / generate_structured_response)
    else:
        if version == "v1":
            return "tools"
        elif version == "v2":
            return [Send("tools", ToolCallWithContext(call, state))
                    for call in last_message.tool_calls]
```

`ToolCallWithContext`는 `ToolNode`의 `_parse_input`에서 `{"__type": "tool_call_with_context", "tool_call": ..., "state": ...}` 형태로 처리됨. → [[LangGraph ToolNode flow]] 참고.

---

## route_tool_responses (L970–983)

`return_direct=True`인 도구가 실행됐을 때 루프를 즉시 종료:

```python
def route_tool_responses(state):
    for m in reversed(messages):
        if not isinstance(m, ToolMessage): break
        if m.name in should_return_direct:
            return END
    return entrypoint  # → agent
```

parallel Send에서 `return_direct` 도구와 아닌 도구가 섞인 경우:
마지막 메시지가 `AIMessage`이고 `tool_calls` 중 `return_direct` 있으면 `END`.

---

## pre_model_hook / post_model_hook

| 훅 | 삽입 위치 | 용도 |
|---|---|---|
| `pre_model_hook` | agent 노드 앞 | 메시지 트리밍, 요약 등 긴 히스토리 관리 |
| `post_model_hook` | agent 노드 뒤 | HITL, 가드레일, 검증 |

`pre_model_hook`을 쓰면 `input_schema`에 `llm_input_messages` 필드가 동적으로 추가됨.

`post_model_hook` 있을 때는 `agent → post_model_hook → post_model_hook_router` 로 흐름이 바뀜:
- pending tool calls 있으면 → `Send("tools", ...)`
- ToolMessage가 마지막이면 → `entrypoint` (agent)
- 없으면 → END (또는 generate_structured_response)

---

## response_format (구조화 출력)

`response_format`이 지정되면 `generate_structured_response` 노드 추가:
- 에이전트 루프 **완료 후** 별도 LLM 호출로 구조화 출력 생성
- `model.with_structured_output(schema)`를 사용
- `(system_prompt, schema)` 튜플 형태도 지원

---

## State Schema

기본값 `AgentState` (deprecated → `langchain.agents.AgentState`):

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    remaining_steps: NotRequired[RemainingSteps]
```

`response_format` 있으면 `AgentStateWithStructuredResponse` (위 + `structured_response` 필드).

---

## 동적 모델 지원

```python
def select_model(state: AgentState, runtime: Runtime[Context]) -> BaseChatModel:
    ...
    return model.bind_tools(tools)
```

`callable(model)` 이고 `isinstance(model, Runnable)` 아니면 dynamic 모드.
매 step마다 `_resolve_model(state, runtime)` 호출 → 상태에 따라 다른 모델 선택 가능.

---

## ToolNode와의 연결 포인트

```
create_react_agent
  ├── ToolNode 생성: ToolNode([t for t in tools if not isinstance(t, dict)])
  ├── v2 Send: ToolCallWithContext(tool_call=call, state=state)
  └── v1: "tools" 노드 직접 연결 (AIMessage 통째로)
```

→ ToolNode 내부 흐름: [[LangGraph ToolNode flow]]

---

## Source Code References

- Repo: `langchain-ai/langgraph`
- Commit: UNKNOWN (.venv에서 읽음)
- Files:
  - `langgraph/prebuilt/chat_agent_executor.py` (1,015 lines)
    - `create_react_agent`: L278–1002
    - `should_continue`: L831
    - `call_model`: L661
    - `_should_bind_tools`: L173
    - `_get_prompt_runnable`: L137
    - `_validate_chat_history`: L243
    - `_are_more_steps_needed`: L620
    - `route_tool_responses`: L970
    - `post_model_hook_router`: L919

---

## Key Concepts

- [[StateGraph]]
- [[Tool Calling]]
- [[LangGraph ToolNode flow]]
- [[Checkpointing]]
- [[Human in the Loop]]

---

## Open Questions

- `langchain.agents.create_agent`는 어떻게 다른가? "middleware system"이 무엇인지?
- v2에서 `Send`로 개별 dispatch할 때, 중간에 interrupt가 걸리면 어떻게 resume하는가?
- `RemainingSteps`의 실제 감소 로직은 어디 있는가? (`langgraph.managed`?)
- `post_model_hook`과 HITL을 함께 쓸 때 interrupt 위치가 어떻게 되는가?

---

## Sources

- `langgraph-prebuilt-chat-agent-executor-2026-05-28`
