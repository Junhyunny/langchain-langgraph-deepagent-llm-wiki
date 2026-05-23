---
type: code_map
framework: LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langgraph-docs-persistence-2026-05-20
  - langgraph-reference-checkpoint-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
  - langgraph-docs-graph-api-2026-05-23
  - langgraph-store-base-2026-05-23
---

# LangGraph Code Map

## 요약

이 페이지는 LangGraph 저장소 구조를 매핑한다. 소스 코드를 읽을 때 탐색 가이드로 사용한다.

*상태: checkpointing 관련 경로는 commit `aa322c13cd5f16a3f6254a931a4104e412cd687c` 기준으로 검증. Graph API 및 Store 인터페이스 섹션은 2026-05-23 공식 docs 기준으로 추가됨.*

## 저장소

- **저장소:** `https://github.com/langchain-ai/langgraph`
- **검증된 커밋:** `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- **Raw local path:** `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/`

## 주요 패키지 / 디렉터리

```
libs/
  langgraph/              # Main graph runtime
    langgraph/graph/      # StateGraph, CompiledStateGraph
    langgraph/pregel/     # 실행 엔진 (Pregel loop)
    langgraph/types.py    # Send, Command, PARENT, interrupt
    langgraph/managed/    # RemainingSteps 등 managed values
    langgraph/prebuilt/   # ToolNode, create_react_agent
  checkpoint/             # Checkpoint + Store abstractions
    langgraph/checkpoint/base/    # BaseCheckpointSaver, Checkpoint, CheckpointTuple
    langgraph/checkpoint/memory/  # InMemorySaver
    langgraph/store/base/         # BaseStore, Item, Op 타입들
  checkpoint-sqlite/      # SQLite checkpoint backend
  checkpoint-postgres/    # Postgres checkpoint backend
  langgraph_sdk/          # Client SDK (optional)
```

*부분 검증됨: checkpointing 관련 디렉터리는 소스 직접 확인. 전체 monorepo 구조는 추가 확인 필요.*

## 중요한 진입점

### Graph API

- `langgraph.graph.StateGraph` — 그래프 정의
- `langgraph.graph.state.CompiledStateGraph` — 컴파일된 runnable (`Pregel` 상속)
- `langgraph.graph.MessagesState` — 내장 메시지 상태 스키마
- `langgraph.graph.message.add_messages` — 메시지 ID 기반 reducer
- `langgraph.graph.START`, `langgraph.graph.END` — 특별 내장 노드

### 타입 시스템

- `langgraph.types.Send` — 동적 팬아웃 (map-reduce)
- `langgraph.types.Command` — 상태 업데이트 + 라우팅 결합
- `langgraph.types.PARENT` — 서브그래프에서 상위 그래프로 라우팅
- `langgraph.types.interrupt` — human-in-the-loop 중단점
- `langgraph.managed.is_last_step.RemainingSteps` — 재귀 제한 추적

### Checkpointing

- `langgraph.checkpoint.base.BaseCheckpointSaver` — 체크포인트 인터페이스
- `langgraph.checkpoint.memory.MemorySaver` / `InMemorySaver` — 인메모리 checkpointer
- `langgraph.prebuilt.ToolNode` — 미리 만들어진 도구 실행 노드
- `langgraph.pregel` — graph 실행 엔진 (super-step, checkpoint commit, pending writes)

### Store (long-term memory)

- `langgraph.store.base.BaseStore` — Store 추상 인터페이스 (`batch`/`abatch` 구현 필수)
- `langgraph.store.memory.InMemoryStore` — 개발/테스트용 in-memory store
- `langgraph.store.base.Item` — `namespace + key`로 식별되는 저장 단위
- `langgraph.store.base.SearchItem` — `Item` + `score: float | None`

## Graph API 핵심 구조

### State 정의 패턴

```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.managed.is_last_step import RemainingSteps

class State(TypedDict):
    messages: Annotated[list, add_messages]  # ID 기반 중복 제거
    user_name: str                            # Last-writer-wins
    remaining_steps: RemainingSteps           # 재귀 제한 추적
```

Source: `langgraph-docs-graph-api-2026-05-23`

### Node 서명

```python
# 기본
def node(state: State) -> dict: ...

# config 포함
def node(state: State, config: RunnableConfig) -> dict: ...

# NodeRuntime 포함 (v1+)
def node(state: State, config: RunnableConfig, runtime: NodeRuntime) -> dict:
    user_id = runtime.context["user_id"]
    store = runtime.store  # cross-thread store 접근
```

`NodeRuntime` 제공: `context`, `store`, `stream_writer`, `execution_info`, `server_info`, `control`, `heartbeat`

Source: `langgraph-docs-graph-api-2026-05-23`

### recursion_limit 위치 ⚠️

```python
# top-level key (올바름)
config = {"recursion_limit": 50}

# configurable 내부 (잘못됨 — 무시됨)
config = {"configurable": {"recursion_limit": 50}}  # ❌
```

Source: `langgraph-docs-graph-api-2026-05-23`

## 읽어야 할 소스 파일 (검증됨)

- `libs/langgraph/langgraph/graph/state.py`
  - `StateGraph`, `CompiledStateGraph`, `compile()`
  - 확인됨: `compile()`이 `CompiledStateGraph(... checkpointer=checkpointer ...)`를 생성하고 `Pregel` 기반 compiled graph를 반환한다.

- `libs/langgraph/langgraph/pregel/main.py`
  - 확인됨: `_defaults()`, `stream()`, `SyncPregelLoop`, `PregelRunner(... put_writes=loop.put_writes)`, durability handling

- `libs/langgraph/langgraph/pregel/_loop.py`
  - 확인됨: `put_writes()`, `after_tick()`, `_put_checkpoint()`, `_first()`, `_put_pending_writes()`, exit-mode checkpoint persistence

- `libs/checkpoint/langgraph/checkpoint/base/__init__.py`
  - 확인됨: `Checkpoint`, `CheckpointTuple`, `BaseCheckpointSaver`, `put`, `put_writes`, `get_tuple`, `list`, `prune`, `get_delta_channel_history`

- `libs/checkpoint/langgraph/checkpoint/memory/__init__.py`
  - 확인됨: `InMemorySaver` storage/writes/blobs, `get_tuple()`, `put()`, `put_writes()`

- `libs/checkpoint/langgraph/store/base/__init__.py`
  - 확인됨: `BaseStore`, `Item`, `SearchItem`, `GetOp`, `PutOp`, `SearchOp`, `ListNamespacesOp`, `TTLConfig`, `IndexConfig`
  - Source: `langgraph-store-base-2026-05-23`

## Store 인터페이스 요약

```python
# BaseStore — 핵심 추상 메서드 2개
def batch(ops: Iterable[Op]) -> list[Result]
async def abatch(ops: Iterable[Op]) -> list[Result]

# 편의 메서드 (모두 batch/abatch 위임)
store.get(namespace, key)          # → Item | None
store.put(namespace, key, value)   # → None (value=None이면 삭제)
store.search(namespace_prefix, query=None, filter=None, limit=10)  # → list[SearchItem]
store.delete(namespace, key)       # → None
store.list_namespaces(prefix=None) # → list[tuple[str, ...]]
```

**namespace:** `tuple[str, ...]` — 계층 경로 (`("user", "123", "memories")`)

Source: `langgraph-store-base-2026-05-23`

## 읽어야 할 테스트

- checkpoint saver tests: 추후 작성
- pending writes recovery tests: 추후 작성
- interrupt/resume tests: 추후 작성
- Store vector search tests: 추후 작성

## 불명확한 영역

- `compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가?
- 상태 reducer는 `state.py` 어디에서 적용되는가?
- 스트리밍(`stream_mode`)은 어떻게 구현되는가?
- `InMemoryStore`의 구체적 구현은? vector search를 지원하는가?
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가?
- `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가, 다른 클래스인가?

## 관련 페이지

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Store]]
- [[Subagents]]
- [[LangGraph StateGraph compile invoke flow]]

## 소스

- `langgraph-docs-persistence-2026-05-20`
- `langgraph-reference-checkpoint-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
- `langgraph-docs-graph-api-2026-05-23`
- `langgraph-store-base-2026-05-23`
