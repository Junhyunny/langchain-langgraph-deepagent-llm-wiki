# Source Summary: LangGraph Checkpoint Savers

**Source ID:** `langgraph-source-checkpoint-savers-2026-05-23`
**Type:** source_code
**Framework:** LangGraph
**URL:** https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint
**Retrieved:** 2026-05-23

---

## 핵심 확인 사항

### MemorySaver vs InMemorySaver

```python
# memory/__init__.py 마지막 줄:
MemorySaver = InMemorySaver  # Kept for backwards compatibility
```

**`MemorySaver`와 `InMemorySaver`는 완전히 동일한 클래스다.** `MemorySaver`는 하위 호환성을 위한 단순 alias.

---

## BaseCheckpointSaver 인터페이스

`libs/checkpoint/langgraph/checkpoint/base/__init__.py`

### 추상 메서드 (반드시 구현)

| 메서드 | 설명 |
|--------|------|
| `get_tuple(config)` | checkpoint tuple 조회 |
| `list(config, *, filter, before, limit)` | checkpoint 목록 조회 |
| `put(config, checkpoint, metadata, new_versions)` | checkpoint 저장 |
| `put_writes(config, writes, task_id, task_path)` | 중간 writes 저장 |
| `aget_tuple`, `alist`, `aput`, `aput_writes` | async 버전 |

### 기본 구현 메서드 (선택적 오버라이드)

- `get(config)` → `get_tuple` 래퍼
- `delete_thread(thread_id)` — thread 전체 삭제
- `delete_for_runs(run_ids)` — run ID 기준 삭제
- `copy_thread(source, target)` — thread 복사 (DeltaChannel 주의)
- `prune(thread_ids, strategy="keep_latest")` — checkpoint 정리 (DeltaChannel 주의)
- `get_delta_channel_history(config, channels)` — DeltaChannel 히스토리 조회 (beta)
- `get_next_version(current, channel)` — 기본값: 정수 +1 증가

---

## 핵심 데이터 클래스

### Checkpoint (TypedDict)

```python
class Checkpoint(TypedDict):
    v: int                          # 포맷 버전 (현재 1)
    id: str                         # unique + monotonically increasing
    ts: str                         # ISO 8601 타임스탬프
    channel_values: dict[str, Any]  # 역직렬화된 채널 스냅샷 값
    channel_versions: ChannelVersions  # dict[str, str|int|float]
    versions_seen: dict[str, ChannelVersions]  # 노드별 채널 버전 추적
    updated_channels: list[str] | None
```

### CheckpointTuple (NamedTuple)

```python
class CheckpointTuple(NamedTuple):
    config: RunnableConfig
    checkpoint: Checkpoint
    metadata: CheckpointMetadata
    parent_config: RunnableConfig | None = None
    pending_writes: list[PendingWrite] | None = None
```

### CheckpointMetadata (TypedDict, total=False)

```python
class CheckpointMetadata(TypedDict, total=False):
    source: Literal["input", "loop", "update", "fork"]
    # "input": invoke/stream/batch 입력에서 생성
    # "loop": pregel 루프 내부에서 생성
    # "update": 수동 상태 업데이트에서 생성
    # "fork": 다른 checkpoint 복사
    step: int   # -1(input), 0(첫 loop), n(n번째 이후)
    parents: dict[str, str]   # namespace -> checkpoint ID
    run_id: str
```

---

## Saver 구현체 비교

### InMemorySaver

**패키지:** `langgraph` (내장)

**내부 구조:**
```python
storage: defaultdict[
    str,   # thread_id
    dict[  # checkpoint_ns
        str,  # checkpoint_id
        tuple[
            tuple[str, bytes],  # 직렬화된 checkpoint
            tuple[str, bytes],  # 직렬화된 metadata
            str | None          # parent checkpoint_id
        ]
    ]
]
writes: defaultdict[
    tuple[str, str, str],  # (thread_id, checkpoint_ns, checkpoint_id)
    dict[tuple[str, int], tuple[str, str, tuple[str, bytes], str]]
    # key: (task_id, write_idx), value: (task_id, channel, serialized_value, task_path)
]
blobs: dict[
    tuple[str, str, str, str|int|float],  # (thread_id, checkpoint_ns, channel, version)
    tuple[str, bytes]  # 직렬화된 채널 blob
]
```

**사용 시점:** 테스트/디버그 전용. 멀티 스레드 OK (sync/async 모두 지원, 내부적으로 동일 메서드 호출).

```python
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)
result = graph.invoke(1, {"configurable": {"thread_id": "t1"}})
```

### SqliteSaver

**패키지:** `langgraph-checkpoint-sqlite` (별도 설치 필요)

**특징:**
- 동기 전용 (단일 스레드 권장)
- `setup()` 자동 호출 (InMemorySaver와 달리 명시 호출 불필요)
- `check_same_thread=False` 사용 시 내부 lock으로 thread-safe

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 인메모리 SQLite
with SqliteSaver.from_conn_string(":memory:") as memory:
    graph = builder.compile(checkpointer=memory)

# 파일 기반
with SqliteSaver.from_conn_string("checkpoints.sqlite") as memory:
    graph = builder.compile(checkpointer=memory)
```

### PostgresSaver / AsyncPostgresSaver

**패키지:** `langgraph-checkpoint-postgres` (별도 설치 필요)

**특징:**
- `setup()` **반드시 명시적으로 호출** 필요 (테이블 생성 + 마이그레이션)
- `pipeline=True`: 배치 writes, 성능 향상 (단, 단일 Connection만 지원, ConnectionPool 불가)
- `AsyncPostgresSaver`: 비동기 버전, `asetup()` 호출

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgres://user:pass@localhost:5432/db?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as saver:
    saver.setup()  # 필수!
    graph = builder.compile(checkpointer=saver)
    graph.invoke(inputs, {"configurable": {"thread_id": "1"}})
```

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
    await saver.asetup()  # 필수!
    graph = builder.compile(checkpointer=saver)
    await graph.ainvoke(inputs, {"configurable": {"thread_id": "1"}})
```

---

## Saver 선택 가이드

| Saver | 패키지 | Sync | Async | 프로덕션 | 용도 |
|-------|--------|------|-------|---------|------|
| `InMemorySaver` | `langgraph` | ✅ | ✅ | ❌ | 테스트/디버그 |
| `MemorySaver` | `langgraph` | ✅ | ✅ | ❌ | `InMemorySaver` alias |
| `SqliteSaver` | `langgraph-checkpoint-sqlite` | ✅ | ⚠️ | ⚠️ | 소규모/단일 스레드 |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | ✅ | ❌ | ✅ | 프로덕션 (sync) |
| `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | ❌ | ✅ | ✅ | 프로덕션 (async) |

공식 권고: 프로덕션에서는 `PostgresSaver` / `AsyncPostgresSaver`. LangSmith Deployment 사용 시 checkpointer 지정 불필요 (자동 관리).

---

## 해소된 Open Questions

- ✅ `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가? → **동일. MemorySaver는 하위 호환 alias.**
- ✅ `SQLiteSaver` 설정 방법 → `from_conn_string(":memory:")` 또는 파일 경로. `setup()` 자동.
- ✅ `PostgresSaver` 설정 방법 → `from_conn_string(DB_URI)` + `setup()` 명시 호출 필수.
- ✅ `InMemorySaver`의 `storage/writes/blobs` 구조 → 위 내부 구조 참고.

---

## 잔여 Open Questions

- `SqliteSaver`의 async 지원 여부 → `aiosqlite` 패키지 별도 확인 필요 (`AsyncSqliteSaver` 존재 여부)
- `thread_id` 없이 `invoke`를 호출하면 어떤 에러가 발생하는가? → 소스에서 직접 확인 필요
- checkpointer가 있을 때 같은 `thread_id`로 재실행하면 이전 상태부터 이어서 실행되는가? → persistence docs 참고
