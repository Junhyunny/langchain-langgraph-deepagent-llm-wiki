---
type: framework
framework: LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langgraph-docs-graph-api-2026-05-23
  - langgraph-docs-persistence-2026-05-20
  - langgraph-reference-stategraph-compile-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
---

# LangGraph

## 요약

LangGraph는 상태를 가진 멀티 액터 LLM 애플리케이션을 그래프로 구축하기 위한 라이브러리다. 명시적인 상태 관리, 체크포인팅, 그래프 기반 제어 흐름을 통해 LangChain을 확장한다. LangChain.inc가 개발했으며 기존 선형 체인 구조를 넘어 복잡한 다중 에이전트 시스템을 지원한다.

## 중요한 이유

LangGraph는 영속적 상태, human-in-the-loop, 구조화된 실행 흐름이 필요한 복잡한 agent를 위한 핵심 오케스트레이션 프레임워크다.

---

## 핵심 개념

### 1. State (상태)
*Source: `langgraph-docs-graph-api-2026-05-23`*

State는 특정 시점의 애플리케이션 스냅샷을 나타내는 공유 데이터 구조다.

```python
from typing_extensions import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]  # Reducer: append
    user_name: str                  # Last-writer-wins (기본값)
```

**내장 MessagesState (권장):**
```python
from langgraph.graph import MessagesState

class State(MessagesState):
    user_name: str  # 커스텀 필드 추가 가능
```

**Input/Output 스키마 분리:**
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

graph = StateGraph(State, context_schema=ContextSchema)
graph.invoke({"question": "..."}, context={"user_id": "alice"})
```

### 2. Reducers

부분 상태 업데이트를 현재 상태에 병합하는 방법.

| 방식 | 설명 |
|------|------|
| 기본값 (없음) | Last-writer-wins |
| `Annotated[list, add]` | 리스트에 append |
| `Annotated[list, add_messages]` | 메시지 추가 + ID 기반 중복 제거/업데이트 |

**add_messages reducer:**
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
```

### 3. Nodes (노드)

상태를 변환하는 Python 함수. 전체 상태를 받고 부분 업데이트를 반환한다.

```python
def my_node(state: State) -> dict:
    return {"answer": "..."}  # 변경할 필드만 반환

# config 포함
def my_node(state: State, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    return {"answer": "..."}

# runtime 포함 (LangGraph v1+)
from langgraph.types import NodeRuntime

def my_node(state: State, config: RunnableConfig, runtime: NodeRuntime) -> dict:
    user_id = runtime.context["user_id"]
    return {"answer": "..."}
```

NodeRuntime 제공 항목: `context`, `store`, `stream_writer`, `execution_info`, `server_info`, `control`, `heartbeat`

### 4. Edges (에지)

노드 간 흐름 제어.

**일반 에지:**
```python
builder.add_edge("node_a", "node_b")
```

**조건부 에지:**
```python
def route(state: State) -> str:
    return "retrieve" if state["needs_retrieval"] else "generate"

builder.add_conditional_edges("decide", route, ["retrieve", "generate"])
```

**병렬 팬아웃 (리스트 반환):**
```python
def route(state: State) -> list[str]:
    return ["node_a", "node_b"]  # 동시 실행
```

### 5. Send (동적 팬아웃)

map-reduce 패턴을 위한 동적 분기. 각 `Send`는 독립적인 그래프 복사본을 생성한다:

```python
from langgraph.types import Send

def continue_to_reviews(state: OverallState):
    return [Send("write_review", {"subject": s}) for s in state["subjects"]]

builder.add_conditional_edges("generate_subjects", continue_to_reviews)
```

### 6. Command

상태 업데이트와 라우팅을 결합한 통합 프리미티브:

```python
from langgraph.types import Command

def node_a(state: State) -> Command:
    return Command(
        update={"answer": "42"},  # 상태 업데이트
        goto="node_b",            # 다음 노드
    )
```

**크로스 그래프 네비게이션:**
```python
from langgraph.types import PARENT

def child_node(state: State) -> Command:
    return Command(update={"result": "done"}, goto=PARENT)
```

**interrupt 후 재개:**
```python
from langgraph.types import interrupt

def human_review(state: State):
    value = interrupt("Please review: " + state["draft"])
    return Command(resume=value, goto="process_review")
```

### 7. 재귀 제한 (recursion_limit)

- 기본값: **1000** (LangGraph v1.0.6 이후)
- 초과 시 `GraphRecursionError` 발생
- 설정: `config`의 **top-level key** (configurable 내부 ❌)

```python
config = {"recursion_limit": 50}                    # ✅ 올바름
config = {"configurable": {"recursion_limit": 50}}  # ❌ 잘못됨
```

---

## 그래프 컴파일 및 실행

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph

builder = StateGraph(State)
builder.add_node("my_node", my_node)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)

# 체크포인팅 포함
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 실행 (thread_id 필수)
config = {"configurable": {"thread_id": "thread-001"}}
result = graph.invoke({"question": "What is LangGraph?"}, config=config)
```

---

## 체크포인팅
*Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-stategraph-compile-2026-05-20`*

체크포인터는 그래프 실행 중 각 노드의 상태를 저장하는 영속화 시스템이다.

| 구현체 | 특징 |
|--------|------|
| `BaseCheckpointSaver` | 추상 기본 클래스 |
| `InMemorySaver` | 메모리 기반 (비영속) |
| `SQLiteSaver` | SQLite 파일 기반 영속 |
| `PostgresSaver` | PostgreSQL 기반 영속 |

체크포인터를 사용하면 `thread_id`로 여러 독립적 대화 세션을 관리한다.
`config`의 `configurable.thread_id`를 매 실행 시 전달해야 한다.

→ 자세한 내용: [[Checkpointing]]

---

## 공개 API

- `StateGraph(schema)` — 그래프 빌더
- `graph.add_node(name, fn)`
- `graph.add_edge(from, to)`
- `graph.add_conditional_edges(from, fn, map)`
- `graph.compile(checkpointer=...)`
- `compiled.invoke(input, config)`
- `compiled.stream(input, config)`
- `compiled.astream_events(input, config)`

---

## 미해결 질문

- `StateGraph.compile()`은 runnable을 내부적으로 어떻게 생성하는가?
- `NodeRuntime.control`과 `NodeRuntime.heartbeat`의 구체적인 사용 사례는?
- `interrupt()`와 `Command(resume=value, ...)` 패턴은 내부적으로 어떻게 연동되는가?
- `Send` 사용 시 독립 그래프 복사본의 결과를 어떻게 집계하는가 (reduce 단계)?
- Input/Output/Private State 스키마 분리가 성능에 미치는 영향은?

## 관련 페이지

- [[LangChain]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[Subagents]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

- `langgraph-docs-graph-api-2026-05-23`
- `langgraph-docs-persistence-2026-05-20`
- `langgraph-reference-stategraph-compile-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
