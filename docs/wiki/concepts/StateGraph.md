---
type: concept
framework:
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langgraph-reference-stategraph-compile-2026-05-20
  - langgraph-docs-persistence-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
  - langgraph-docs-graph-api-2026-05-23
---

# StateGraph

## 요약

`StateGraph`는 [[LangGraph]]에서 상태를 가진 agent 그래프를 정의하기 위한 핵심 추상화다. 공유된 타입 상태 위에서 동작하는 노드(함수)와 엣지(전이)로 agent를 방향 그래프로 표현한다.

*상태: Graph API 소스(2026-05-23)로 Reducer, MessagesState, Send, Command, recursion_limit 섹션 추가. Checkpointing 계약은 commit `aa322c13cd5f16a3f6254a931a4104e412cd687c` 기준으로 검증됨.*

## 중요한 이유

`StateGraph`는 LangGraph에서 복잡한 agent를 정의하는 기본 방식이다. 그 컴파일 및 실행 모델을 이해하는 것은 LangGraph 내부 구조를 이해하기 위한 토대다.

## 핵심 개념

- **상태 스키마** — 공유 상태를 정의하는 TypedDict, Pydantic, 또는 dataclass
- **Reducer** — 부분 상태 업데이트를 현재 상태에 병합하는 방법을 정의
- **노드** — Python 함수 `(state) -> partial_update`
- **엣지** — 한 노드에서 다른 노드로의 무조건 전이
- **조건부 엣지** — 라우팅 함수가 결정하는 전이
- **`START` / `END`** — 특별한 내장 노드
- **`Send`** — 동적 팬아웃(map-reduce 패턴)
- **`Command`** — 상태 업데이트와 라우팅을 결합한 통합 프리미티브
- **`compile()`** — `CompiledStateGraph` runnable을 생성한다
- **`invoke()` / `stream()`** — 컴파일된 그래프를 실행한다
- **checkpointer** — `compile(checkpointer=...)`로 연결되는 versioned short-term memory

## 상태 스키마 정의

### 기본 TypedDict

```python
from typing_extensions import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]  # Reducer: 새 메시지 append
    user_name: str                  # Last-writer-wins (기본값)
```

Source: `langgraph-docs-graph-api-2026-05-23`

### 내장 MessagesState

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    user_name: str  # 커스텀 필드 추가 가능
# messages: Annotated[list[AnyMessage], add_messages] 포함
```

Source: `langgraph-docs-graph-api-2026-05-23`

### Input / Output / Private 스키마 분리

```python
class InputState(TypedDict): question: str
class OutputState(TypedDict): answer: str
class PrivateState(TypedDict): retrieved_docs: list

graph = StateGraph(PrivateState, input_schema=InputState, output_schema=OutputState)
```

Source: `langgraph-docs-graph-api-2026-05-23`

### Context 스키마 (불변 런타임 설정)

```python
class ContextSchema(TypedDict):
    user_id: str
    db_connection: Any

graph = StateGraph(State, context_schema=ContextSchema)
graph.invoke({"question": "..."}, context={"user_id": "alice", "db_connection": db})
```

Source: `langgraph-docs-graph-api-2026-05-23`

## Reducers

부분 상태 업데이트를 현재 상태에 병합하는 방법을 정의한다.

| 방식 | 설명 |
|------|------|
| 기본값 (없음) | Last-writer-wins |
| `Annotated[list, add]` | 리스트에 append |
| `Annotated[list, add_messages]` | 메시지 추가 + ID 기반 중복 제거/업데이트 |

**add_messages reducer (권장):**
```python
from langgraph.graph.message import add_messages
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

`add_messages`는 `operator.add`보다 권장: 메시지 ID 기반 업데이트/중복 제거 기능 포함.

**RemainingSteps — 재귀 제한 추적:**
```python
from langgraph.managed.is_last_step import RemainingSteps
class State(TypedDict):
    remaining_steps: RemainingSteps
# state["remaining_steps"]로 조기 종료 구현 가능
```

Source: `langgraph-docs-graph-api-2026-05-23`

## 노드 (Nodes)

상태를 변환하는 Python 함수.

```python
def my_node(state: State) -> dict:
    return {"answer": "..."}  # 변경할 필드만 부분 업데이트 반환

# config 포함
def my_node(state: State, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    return {"answer": "..."}

# runtime 포함 (LangGraph v1+)
def my_node(state: State, config: RunnableConfig, runtime: NodeRuntime) -> dict:
    user_id = runtime.context["user_id"]
    return {"answer": "..."}
```

`NodeRuntime` 제공 항목: `context`, `store`, `stream_writer`, `execution_info`, `server_info`, `control`, `heartbeat`

Source: `langgraph-docs-graph-api-2026-05-23`

## 엣지 (Edges)

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("agent", agent_fn)
builder.add_node("tools", tool_fn)
builder.add_edge(START, "agent")

# 조건부 엣지
def route(state: State) -> str:
    if state["needs_tools"]:
        return "tools"
    return END

builder.add_conditional_edges("agent", route, ["tools", END])
builder.add_edge("tools", "agent")

# 병렬 팬아웃 (리스트 반환)
def fan_out(state: State) -> list[str]:
    return ["node_a", "node_b"]  # 동시 실행
builder.add_conditional_edges("decide", fan_out)
```

Source: `langgraph-docs-graph-api-2026-05-23`

## Send — 동적 팬아웃 (map-reduce)

각 아이템에 독립적인 그래프 복사본을 생성해 병렬 실행:

```python
from langgraph.types import Send

def continue_to_reviews(state: OverallState):
    return [Send("write_review", {"subject": s}) for s in state["subjects"]]

builder.add_conditional_edges("generate_subjects", continue_to_reviews)
```

각 `Send(node_name, state)`는 해당 노드 호출에 대한 **독립적인 그래프 복사본**을 생성한다.

Source: `langgraph-docs-graph-api-2026-05-23`

## Command — 상태 업데이트 + 라우팅 결합

```python
from langgraph.types import Command

def node_a(state: State) -> Command:
    return Command(
        update={"answer": "42"},  # 상태 업데이트
        goto="node_b",            # 다음 노드 (문자열 또는 리스트)
    )
```

**크로스 그래프 네비게이션:**
```python
from langgraph.types import Command, PARENT

def child_node(state: State) -> Command:
    return Command(update={"result": "done"}, goto=PARENT)
```

**interrupt 후 재개:**
```python
from langgraph.types import Command, interrupt

def human_review(state: State):
    value = interrupt("Please review: " + state["draft"])
    return Command(resume=value, goto="process_review")
```

Source: `langgraph-docs-graph-api-2026-05-23`

## 재귀 제한 (recursion_limit)

- 기본값: **1000** (LangGraph v1.0.6 이후)
- 초과 시 `GraphRecursionError` 발생
- 설정 위치: `config`의 **top-level key** — `configurable` 내부가 아님 ⚠️

```python
# 올바른 설정
config = {"recursion_limit": 50}
graph.invoke(inputs, config=config)

# 잘못된 설정
config = {"configurable": {"recursion_limit": 50}}  # ❌ 무시됨
```

Source: `langgraph-docs-graph-api-2026-05-23`

## compile() 및 실행

```python
from langgraph.checkpoint.memory import InMemorySaver

# 체크포인팅 없음
graph = builder.compile()

# 체크포인팅 포함 (thread 기반 상태 영속)
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# human-in-the-loop
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review_node"]
)

# 실행 — thread_id 필수 (체크포인팅 시)
config = {"configurable": {"thread_id": "thread-001"}}
result = graph.invoke({"question": "What is LangGraph?"}, config=config)
```

Source (compile 계약): `langgraph-reference-stategraph-compile-2026-05-20`
Source (내부 구현): `langgraph-source-checkpoint-runtime-2026-05-20`

## 소스 코드 참조

- 저장소: `langgraph`
- 커밋: `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- 파일:
  - `libs/langgraph/langgraph/graph/state.py`
  - `libs/langgraph/langgraph/pregel/main.py`
  - `libs/langgraph/langgraph/pregel/_loop.py`

## 미해결 질문

- `compiled.validate()`는 정확히 어떤 graph 구조 검사를 수행하는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `NodeRuntime.control`과 `NodeRuntime.heartbeat`의 구체적인 사용 사례는? — Source: `langgraph-docs-graph-api-2026-05-23`
- `Send` 사용 시 각 독립 복사본의 결과를 reduce 단계에서 어떻게 집계하는가? — Source: `langgraph-docs-graph-api-2026-05-23`
- `Command(resume=value, goto="...")` 패턴은 `interrupt()`와 어떻게 연동되는가? — Source: `langgraph-docs-graph-api-2026-05-23`
- `TypedDict` vs `Pydantic` 상태 스키마의 실질적인 차이는? (런타임 유효성 검사, 직렬화) — Needs Source
- `checkpointer=None`의 subgraph inheritance는 parent runtime config에서 어떻게 전달되는가? — Needs Source
- `input_schema`/`output_schema` 분리가 성능에 미치는 영향은? — Source: `langgraph-docs-graph-api-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ 조건부 에지의 라우팅 함수가 반환할 수 있는 값 타입: 문자열, 문자열 리스트(병렬 팬아웃), `Send` 객체 리스트 (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ 노드 함수 반환값: 변경된 키만 포함한 부분 업데이트 반환 → Reducer가 상태에 병합 (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ `recursion_limit`은 `configurable` 안이 아닌 config top-level key (Source: `langgraph-docs-graph-api-2026-05-23`)

## 관련 페이지

- [[LangGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[Subagents]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## 소스

- `langgraph-reference-stategraph-compile-2026-05-20`
- `langgraph-docs-persistence-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
- `langgraph-docs-graph-api-2026-05-23`
