---
type: source_summary
source_id: langgraph-docs-graph-api-2026-05-23
framework:
  - LangGraph
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://docs.langchain.com/oss/python/langgraph/graph-api"
---

# Source Summary: LangGraph Graph API

## Key Facts

### 핵심 개념 3가지

LangGraph는 State, Nodes, Edges로 구성된 **상태 기계(stateful multi-actor)** 프레임워크다.

---

### State (상태)

특정 시점의 애플리케이션 스냅샷을 나타내는 공유 데이터 구조.

**정의 방법:**
```python
from typing_extensions import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]  # Reducer: 새 메시지 append
    user_name: str                  # Last-writer-wins (기본값)
```

**내장 MessagesState:**
```python
from langgraph.graph import MessagesState

class State(MessagesState):
    user_name: str  # 커스텀 필드 추가
# messages: Annotated[list[AnyMessage], add_messages] 포함
```

**Input/Output 분리 스키마:**
```python
class InputState(TypedDict): question: str
class OutputState(TypedDict): answer: str
class PrivateState(TypedDict): retrieved_docs: list

graph = StateGraph(PrivateState, input_schema=InputState, output_schema=OutputState)
```

**Context 스키마 (불변 런타임 설정):**
```python
class ContextSchema(TypedDict):
    user_id: str
    db_connection: Any

graph = StateGraph(State, context_schema=ContextSchema)
graph.invoke({"question": "..."}, context={"user_id": "alice", "db_connection": db})
```

---

### Reducers

부분 상태 업데이트를 현재 상태에 병합하는 방법 정의.

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

**RemainingSteps (재귀 제한 추적):**
```python
from langgraph.managed.is_last_step import RemainingSteps
class State(TypedDict):
    remaining_steps: RemainingSteps
# state["remaining_steps"]로 조기 종료 구현
```

---

### Nodes (노드)

상태를 변환하는 Python 함수.

**기본 서명:**
```python
def my_node(state: State) -> dict:
    return {"answer": "..."}  # 부분 업데이트만 반환

# config 포함
def my_node(state: State, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    return {"answer": "..."}

# runtime 포함 (LangGraph v1+)
def my_node(state: State, config: RunnableConfig, runtime: NodeRuntime) -> dict:
    user_id = runtime.context["user_id"]
    return {"answer": "..."}
```

**핵심 규칙:**
- 노드는 현재 전체 상태를 받는다
- 노드는 변경할 필드만 포함한 **부분 업데이트**를 반환한다
- Reducer가 부분 업데이트를 상태에 병합한다

**NodeRuntime 제공 항목:** context, store, stream_writer, execution_info, server_info, control, heartbeat

**START / END:**
```python
from langgraph.graph import START, END, StateGraph

builder = StateGraph(State)
builder.add_node("my_node", my_node)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)
graph = builder.compile()
```

---

### Edges (에지)

노드 간 흐름 제어.

**일반 에지:**
```python
builder.add_edge("node_a", "node_b")
```

**조건부 에지:**
```python
def route(state: State) -> str:
    if state["needs_retrieval"]:
        return "retrieve"
    return "generate"

builder.add_conditional_edges("decide", route, ["retrieve", "generate"])
```

리스트 반환으로 병렬 팬아웃:
```python
def route(state: State) -> list[str]:
    return ["node_a", "node_b"]  # 동시 실행
```

---

### Send (동적 팬아웃)

map-reduce 패턴을 위한 동적, 상태 의존적 분기:

```python
from langgraph.types import Send

def continue_to_reviews(state: OverallState):
    return [Send("write_review", {"subject": s}) for s in state["subjects"]]

builder.add_conditional_edges("generate_subjects", continue_to_reviews)
```

각 `Send(node_name, state)`는 해당 노드 호출에 대한 독립적인 그래프 복사본을 생성한다.

---

### Command

상태 업데이트와 라우팅을 결합하는 통합 프리미티브:

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

---

### 재귀 제한 (recursion_limit)

- 기본값: **1000** (LangGraph v1.0.6 이후)
- 초과 시 `GraphRecursionError` 발생
- 설정 위치: `config`의 **top-level key** (configurable 내부 ❌)

```python
# 올바른 설정
config = {"recursion_limit": 50}
graph.invoke(inputs, config=config)

# 잘못된 설정
config = {"configurable": {"recursion_limit": 50}}  # ❌
```

---

### 그래프 컴파일 및 실행

```python
from langgraph.checkpoint.memory import InMemorySaver

# 체크포인팅 없음
graph = builder.compile()

# 체크포인팅 포함 (thread 기반 상태 영속)
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# interrupt_before (human-in-the-loop)
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review_node"]
)

# 실행 — thread_id 필수 (체크포인팅 시)
config = {"configurable": {"thread_id": "thread-001"}}
result = graph.invoke({"question": "What is LangGraph?"}, config=config)
```

## Interpretation

- `Command`는 조건부 에지와 노드를 분리하던 기존 패턴을 단순화 — 라우팅 로직을 노드 안에 인캐슐레이션할 수 있다.
- `Send`는 LangGraph의 map-reduce 핵심 API — 동적으로 생성되는 병렬 작업에 필수.
- `add_messages` reducer가 `operator.add`보다 우선 권장 — 메시지 ID 기반 업데이트/중복 제거 기능 포함.
- `recursion_limit`이 `configurable` 안이 아닌 top-level key라는 점은 헷갈리기 쉬운 API 계약이다.
- Input/Output/Private State 분리는 노드 간 데이터 흐름을 명시적으로 제어하는 설계 패턴이다.

## Open Questions

- `NodeRuntime.control`과 `NodeRuntime.heartbeat`의 구체적인 사용 사례는?
- `Command(resume=value, goto="...")` 패턴은 `interrupt()`와 어떻게 연동되는가?
- `StateGraph`의 `input_schema`/`output_schema` 분리가 성능에 미치는 영향은?
- `Send` 사용 시 각 독립 그래프 복사본의 결과를 어떻게 집계하는가 (reduce 단계)?

## Related Wiki Pages

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Subagents]]

## Sources

- `langgraph-docs-graph-api-2026-05-23`
