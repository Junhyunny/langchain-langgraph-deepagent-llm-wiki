---
type: code_map
framework: LangGraph
status: partial
confidence: medium
last_reviewed: 2026-05-24
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

*상태: checkpointing 관련 경로는 commit `aa322c13cd5f16a3f6254a931a4104e412cd687c` 기준으로 검증. Graph API 및 Store 인터페이스 섹션은 2026-05-23 공식 docs 기준으로 추가됨. validate/stream/reducer/MemorySaver 관련 불명확한 영역 일부 해소 (2026-05-24, .venv 설치본 직접 읽음).*

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
  - 확인됨: state 키에 `Annotated[Type, reducer]` 형태로 reducer를 지정할 수 있다.

- `libs/langgraph/langgraph/pregel/main.py`
  - 확인됨: `_defaults()`, `stream()`, `SyncPregelLoop`, `PregelRunner(... put_writes=loop.put_writes)`, durability handling
  - 확인됨: `validate()` — `_validate.py`의 `validate_graph()`를 호출하고 `trigger_to_nodes`를 빌드한다.
  - 확인됨: node timeout 지원 여부 검사 포함.

- `libs/langgraph/langgraph/pregel/_validate.py`
  - 확인됨: `validate_graph()` 구현.
    - channel/managed/node 이름 RESERVED 충돌 검사
    - 각 node가 구독하는 channel이 known channels에 존재하는지 검사
    - input/output/stream channel 존재 검사
    - interrupt_before/after 노드 존재 검사

- `libs/langgraph/langgraph/pregel/_algo.py`
  - 확인됨: `apply_writes(checkpoint, channels, tasks, get_next_version, trigger_to_nodes)`
    - task 결과를 checkpoint와 channel에 적용
    - task 정렬: `task_path_str(t.path[:3])` 기준 (결정론적 순서 보장)
    - `checkpoint["versions_seen"]` 업데이트
    - channel 버전 bump 후 `ch.update()` 호출 → **reducer 적용 지점**

- `libs/langgraph/langgraph/pregel/_loop.py`
  - 확인됨: `put_writes()`, `after_tick()`, `_put_checkpoint()`, `_first()`, `_put_pending_writes()`, exit-mode checkpoint persistence

- `libs/langgraph/langgraph/pregel/_checkpoint.py`
  - 확인됨: `LATEST_VERSION = 4`
  - 확인됨: `empty_checkpoint()` — 초기 빈 checkpoint 생성 (`v=4`, `channel_values={}`)
  - 확인됨: `create_checkpoint()` — 이전 checkpoint + 현재 channel 상태로 새 checkpoint 생성
    - `DeltaChannel` + `channels_to_snapshot`에 포함된 경우: `_DeltaSnapshot(ch.get())` blob 저장
    - 일반 channel: `ch.checkpoint()` 값 저장 (MISSING이면 제외)
  - 확인됨: `channels_from_checkpoint()` — checkpoint에서 channel hydrate
    - `DeltaChannel`이 `channel_values`에 없는 경우: `saver.get_delta_channel_history()`로 ancestor walk, `replay_writes()` 재생
    - 일반 channel: `spec.from_checkpoint(stored)` 직접 호출
  - 확인됨: `delta_channels_to_snapshot()` — 스냅샷 필요 여부 결정 (update count ≥ `snapshot_frequency` OR supersteps ≥ `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`)

- `libs/checkpoint/langgraph/checkpoint/base/__init__.py`
  - 확인됨: `Checkpoint`, `CheckpointTuple`, `BaseCheckpointSaver`, `put`, `put_writes`, `get_tuple`, `list`, `prune`, `get_delta_channel_history`

- `libs/checkpoint/langgraph/checkpoint/memory/__init__.py`
  - 확인됨: `InMemorySaver` storage/writes/blobs, `get_tuple()`, `put()`, `put_writes()`
  - 확인됨: `MemorySaver = InMemorySaver` (line 631) — 하위 호환용 별칭. 동일 클래스.

- `libs/checkpoint/langgraph/store/base/__init__.py`
  - 확인됨: `BaseStore`, `Item`, `SearchItem`, `GetOp`, `PutOp`, `SearchOp`, `ListNamespacesOp`, `TTLConfig`, `IndexConfig`
  - Source: `langgraph-store-base-2026-05-23`

## StreamMode

**검증됨** (`.venv/langgraph/types.py` 직접 확인):

```python
StreamMode = Literal[
    "values",       # 각 super-step 후 전체 state 방출
    "updates",      # node/task 이름 + 반환 값만 방출
    "checkpoints",  # checkpoint 생성 시 StateSnapshot 방출
    "tasks",        # task 시작/완료 이벤트 방출
    "debug",        # "checkpoints" + "tasks" 동시
    "messages",     # LLM 메시지 토큰 단위 스트리밍
    "custom",       # 노드 내부에서 StreamWriter로 직접 방출
]
```

기본값: `"values"`. `graph.stream(input, config, stream_mode="updates")` 식으로 지정.

## DeltaChannel (신규 — v4 체크포인트 기능)

**검증됨** (`_checkpoint.py` 직접 확인):

`DeltaChannel`은 매 super-step마다 전체 스냅샷을 저장하는 대신 **증분(delta) writes만 저장**하는 채널 유형이다.

- `snapshot_frequency` — N번 update마다 또는 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` super-step마다 전체 스냅샷(`_DeltaSnapshot`) 생성
- 스냅샷이 없는 checkpoint에서 hydrate 시 → `saver.get_delta_channel_history()`로 ancestor walk 후 `replay_writes()` 재생
- 저장 공간 절약에 유리하지만 복구 경로가 더 복잡

`channels_from_checkpoint()`: `DeltaChannel`이 `channel_values`에 없으면 ancestor 탐색 분기. 일반 channel과 DeltaChannel 처리 경로가 분리되어 있음.

## Reducer 적용 위치

**검증됨** (`_algo.py apply_writes()` 직접 확인):

reducer는 `state.py`가 아니라 **`pregel/_algo.py`의 `apply_writes()`** 에서 적용된다.

흐름:
1. task 결과 writes 수집 (task path 기준 정렬 → 결정론적 순서)
2. `checkpoint["versions_seen"]` 업데이트
3. 각 channel의 버전 bump
4. `ch.update(writes)` 호출 → **channel 내부에서 reducer 실행**

`state.py`에서는 `Annotated[Type, reducer]` 형태를 파싱해 `StateGraph` 구성 시 channel 객체를 생성할 때 reducer를 등록한다.



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

## 불명확한 영역 (잔여)

- `compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가?
  → **✅ 해소**: `_validate.py`의 `validate_graph()` 호출. channel/managed/node 이름 RESERVED 충돌, 구독 channel 존재, input/output/stream channel 존재, interrupt 노드 존재 검사. 마지막으로 `trigger_to_nodes` 빌드.
- 스트리밍(`stream_mode`)은 어떻게 구현되는가?
  → **✅ 해소 (부분)**: `StreamMode` 타입 7종 직접 확인. `main.py`의 `stream()` 구현 세부는 미수집.
- `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가, 다른 클래스인가?
  → **✅ 해소**: `MemorySaver = InMemorySaver` (line 631 alias). 완전히 동일한 클래스.
- 상태 reducer는 `state.py` 어디에서 적용되는가?
  → **✅ 해소**: `state.py`는 구성 시 reducer 등록. 실제 적용은 `pregel/_algo.py apply_writes()` → `ch.update()` 내부.
- `InMemoryStore`의 구체적 구현은? vector search를 지원하는가?
  → 아직 미확인. (Needs Source)
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가?
  → 아직 미확인. (Needs Source)

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
