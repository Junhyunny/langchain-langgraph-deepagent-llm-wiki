---
type: concept
framework:
  - LangGraph
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-07-30
sources:
  - langgraph-docs-checkpointers-2026-07-30
  - langgraph-docs-interrupts-2026-07-30
  - langgraph-docs-persistence-2026-07-30
  - langgraph-docs-persistence-2026-05-20
  - langgraph-docs-durable-execution-2026-05-20
  - langgraph-reference-stategraph-compile-2026-05-20
  - langgraph-reference-checkpoint-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
  - langgraph-source-checkpoint-savers-2026-05-23
  - langgraph-source-pregel-interrupts-2026-05-23
  - langgraph-source-checkpoint-internals-2026-05-23
  - langgraph-tests-checkpoint-recovery-2026-05-23
---

# Checkpointing

## Summary

[[Checkpointing]]은 [[LangGraph]] 실행 상태를 `thread_id` 아래 저장하고, 이후 같은 thread 또는 특정 `checkpoint_id`에서 상태를 조회, 재개, replay, fork할 수 있게 하는 persistence 메커니즘이다.

현재 학습 질문:

> LangGraph 체크포인팅은 `StateGraph.compile(checkpointer=...)` 이후 실행 중 무엇을 저장하고, 어떻게 재개하는가?

짧은 답: `StateGraph.compile(checkpointer=...)`는 컴파일된 graph에 checkpointer를 연결한다. 실행 시 `thread_id`를 기준으로 super-step마다 `StateSnapshot` checkpoint를 저장하고, super-step 내부에서 완료된 node/task write도 pending write로 저장한다. 재개 시에는 같은 `thread_id` 또는 `checkpoint_id`로 checkpoint tuple을 불러와 저장된 state, next tasks, metadata, pending writes를 기준으로 graph runtime을 다시 진행한다.

## 문서 구조 변경 안내 (2026-07-30 재확인)

공식 문서 구조가 2026-05 대비 바뀌었다. 이 페이지의 사실 자체는 유효하나, **출처 위치가 이동**했다.

- **`persistence` 페이지 축소** — 이전 상세 내용(threads / super-step / `StateSnapshot` 필드 / `get_state` / replay / `update_state` / durability modes)이 신규 **Checkpointers** 페이지로 이전됨. 현재 persistence 페이지는 개요 + Quickstart + Checkpointer vs Store 표 + Troubleshooting만 담는다. Source: `langgraph-docs-persistence-2026-07-30`
- **`durable-execution` 페이지 폐지** — 해당 URL은 이제 HTTP 308 영구 리다이렉트 → persistence. durability modes·deterministic replay·side-effect 가이드는 Checkpointers 페이지로 흡수됨. Source: `langgraph-docs-checkpointers-2026-07-30`
- 아래 본문에서 `langgraph-docs-persistence-2026-05-20` / `langgraph-docs-durable-execution-2026-05-20`으로 인용된 사실들은 현재 **Checkpointers 페이지**(`langgraph-docs-checkpointers-2026-07-30`)에서 재확인 가능하다.

## Why It Matters

Checkpointing은 다음을 가능하게 한다.
- 장기 실행 agent workflow의 일시 중지와 재개
- [[HumanInTheLoop]] 승인/수정 지점
- 장애 이후 마지막 성공 지점부터의 복구
- [[Time Travel]] debugging 및 과거 checkpoint replay
- 같은 `thread_id` 안에서 유지되는 short-term memory

## Key Concepts

- **Thread** — checkpointer가 checkpoint를 저장하고 불러오는 주 key. `config={"configurable": {"thread_id": "..."}}` 형태로 전달한다.
- **Checkpoint** — 특정 시점의 graph state snapshot.
- **Super-step** — 현재 예약된 node들이 실행되는 graph runtime tick. LangGraph는 super-step boundary마다 full checkpoint를 만든다.
- **`StateSnapshot`** — checkpoint의 public representation. `values`, `next`, `config`, `metadata`, `created_at`, `parent_config`, `tasks`를 포함한다.
- **Pending writes** — 같은 super-step 안에서 일부 node는 성공했지만 다른 node가 실패한 경우, 성공한 node output을 재실행하지 않기 위해 저장되는 task-level writes.
- **`BaseCheckpointSaver`** — checkpoint backend 인터페이스. 핵심 메서드는 `put`, `put_writes`, `get_tuple`, `list`, `delete_thread`, `get_next_version`.
- **`InMemorySaver` / `MemorySaver`** — 개발/테스트용 in-memory saver. 프로세스 종료 후 영속성은 제공하지 않는다.
- **Persistent saver** — SQLite, PostgreSQL, MongoDB, Redis 등 외부 저장소 기반 saver.

## What Is Stored

**검증됨:** 공식 persistence 문서 기준으로, full checkpoint는 super-step boundary마다 만들어진다. 예를 들어 `START -> A -> B -> END` 순차 graph는 초기 checkpoint, input checkpoint, A 출력 checkpoint, B 출력 checkpoint를 만든다. Source: `langgraph-docs-persistence-2026-05-20`

**검증됨:** `StateSnapshot`에는 다음이 포함된다. Source: `langgraph-docs-persistence-2026-05-20`
- `values`: checkpoint 시점의 state channel 값
- `next`: 다음에 실행할 node 이름들
- `config`: `thread_id`, `checkpoint_ns`, `checkpoint_id`
- `metadata`: `source`, node `writes`, `step`
- `created_at`: 생성 시각
- `parent_config`: 이전 checkpoint config
- `tasks`: 실행 예정 task, error, interrupt, subgraph snapshot 정보

**검증됨:** super-step 내부의 node/task writes도 checkpointer에 저장된다. 이들은 full `StateSnapshot`이 아니라 in-progress checkpoint에 연결된 task entries이며, pending writes recovery에 사용된다. Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-checkpoint-2026-05-20`

**검증됨:** 기본적으로 LangGraph checkpoint는 각 super-step에서 모든 state channel의 전체 값을 저장한다. Source: `langgraph-docs-persistence-2026-05-20`

**검증됨:** source 기준 `Checkpoint`는 `v`, `id`, `ts`, `channel_values`, `channel_versions`, `versions_seen`, `updated_channels`를 저장한다. `CheckpointTuple`은 여기에 `config`, `metadata`, `parent_config`, `pending_writes`를 함께 묶는다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`

**검증됨:** `InMemorySaver`는 checkpoint record, pending writes, channel blobs를 분리해 저장한다. `put()`은 새 channel version별 blob을 `(thread_id, checkpoint_ns, channel, version)`으로 저장하고, checkpoint 본문에서는 `channel_values`를 제거한 뒤 checkpoint metadata와 parent id를 저장한다. `put_writes()`는 `(thread_id, checkpoint_ns, checkpoint_id)` 아래 task write를 저장한다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`

## How Resume Works

**검증됨:** checkpointer가 활성화된 graph를 실행할 때는 `thread_id`가 필요하다. checkpointer는 이 값을 사용해 checkpoint를 저장하고, interrupt 이후 재개할 때 저장된 상태를 불러온다. Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-stategraph-compile-2026-05-20`

**검증됨:** `graph.get_state(config)`는 해당 `thread_id`의 최신 checkpoint를 반환한다. `checkpoint_id`를 함께 주면 특정 checkpoint를 조회할 수 있다. `graph.get_state_history(config)`는 thread의 checkpoint history를 최신순으로 반환한다. Source: `langgraph-docs-persistence-2026-05-20`

**검증됨:** interrupt로 멈춘 workflow는 같은 `thread_id`와 `Command(resume=...)`로 이어서 실행할 수 있다. Source: `langgraph-docs-durable-execution-2026-05-20`

**검증됨:** 재개는 Python call stack의 같은 줄에서 계속되는 방식이 아니다. LangGraph는 적절한 시작점을 찾아 replay한다. Graph API에서는 중단된 node의 시작점이 resume 시작점이다. Source: `langgraph-docs-durable-execution-2026-05-20`

**검증됨:** checkpointer가 활성화된 graph에서 같은 `thread_id`로 새 입력을 전달해 재실행하면, LangGraph는 해당 thread의 최신 checkpoint를 불러와 이전 state 위에서 계속 실행한다. `_first()`가 기존 `channel_versions`의 존재로 resume 여부를 판단하며, 새 input이 있으면 기존 state에 적용 후 graph를 진행한다. 이것이 multi-turn conversation 연속성의 구현 방식이다. Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-source-checkpoint-runtime-2026-05-20`

**검증됨:** 과거 `checkpoint_id`로 invoke하면 그 checkpoint 이전 node는 저장된 결과를 사용하고, 이후 node는 다시 실행된다. 따라서 LLM call, API request, interrupt 같은 동작은 다시 발생할 수 있다. Source: `langgraph-docs-persistence-2026-05-20`

**검증됨:** source 기준 resume 여부는 기존 checkpoint에 `channel_versions`가 있고 입력이 `None`, `Command`, 같은 `run_id`, 또는 `CONFIG_KEY_RESUMING`인 경우로 판정된다. `Command(resume=...)`는 기존 state 위에 resume write를 추가하고, time-travel replay는 stale `RESUME` write를 제거할 수 있다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`

## What Is Not Stored Automatically

- 외부 시스템에 이미 발생한 side effect 자체. Replay/resume에서 side effect 중복을 피하려면 node/task 설계를 idempotent하게 하거나 LangGraph task를 사용해 결과를 persistence layer에서 재사용해야 한다. Source: `langgraph-docs-durable-execution-2026-05-20`
- thread 간 공유 memory. Checkpointer는 thread-scoped state를 저장한다. 사용자 선호처럼 여러 thread에서 공유할 정보는 `Store` interface가 담당한다. Source: `langgraph-docs-persistence-2026-05-20`
- process 종료 이후의 in-memory 저장 내용. `InMemorySaver` / `MemorySaver`는 개발과 테스트에 적합하고, 운영 영속성은 persistent saver가 필요하다. Source: `langgraph-reference-checkpoint-2026-05-20`

## Implementation Notes

- `StateGraph.compile(checkpointer=...)`는 `CompiledStateGraph` runnable을 만든다. Reference 문서는 이 checkpointer를 versioned short-term memory로 설명한다.
- `StateGraph.compile()`는 `checkpointer`를 검증한 뒤 `CompiledStateGraph(..., checkpointer=checkpointer, ...)`에 전달한다. `CompiledStateGraph`는 `Pregel`을 상속한다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `_defaults()`에서 `checkpointer=False`는 checkpointing을 끄고, config의 `CONFIG_KEY_CHECKPOINTER`는 runtime checkpointer override로 사용되며, `checkpointer=True`는 root graph에서 허용되지 않는다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `config = {"configurable": {"thread_id": "..."}}` 전달 경로: `graph.invoke(input, config)` → `Pregel._defaults(config)`에서 effective checkpointer 결정 → `SyncPregelLoop(checkpointer, config)` 생성 → `_first()`에서 `checkpointer.get_tuple(config)` 호출 → saver가 `config["configurable"]["thread_id"]`를 primary key로 thread checkpoint 조회. `InMemorySaver.get_tuple()`은 명시된 `checkpoint_id`가 없으면 해당 `thread_id`/`checkpoint_ns`의 최신 checkpoint를 반환한다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `BaseCheckpointSaver.put`은 full checkpoint와 metadata를 저장하고, `put_writes`는 checkpoint에 연결된 intermediate writes를 저장한다. Source: `langgraph-reference-checkpoint-2026-05-20`
- `get_tuple`은 config로 checkpoint tuple을 가져온다. 이 tuple에는 checkpoint, config, metadata, pending writes가 포함된다. Source: `langgraph-reference-checkpoint-2026-05-20`
- `checkpoint_ns`는 root graph와 subgraph checkpoint를 구분한다. Source: `langgraph-docs-persistence-2026-05-20`
- 실행 메서드는 `durability="exit" | "async" | "sync"` 옵션을 받을 수 있다. Source에서 기본값은 `"async"`다. `"sync"`는 각 tick 뒤 `_put_checkpoint_fut.result()`를 기다리고, `"exit"`는 `put_writes()`의 즉시 저장을 건너뛰고 loop exit 시 `_put_checkpoint()`와 `_put_pending_writes()`를 호출한다. Source: `langgraph-docs-durable-execution-2026-05-20`, `langgraph-source-checkpoint-runtime-2026-05-20`

## Checkpoint Saver 구현체 비교

Source: `langgraph-source-checkpoint-savers-2026-05-23`

### MemorySaver vs InMemorySaver

**검증됨:** `MemorySaver`와 `InMemorySaver`는 완전히 동일한 클래스다. `MemorySaver`는 하위 호환성을 위한 alias다.

```python
# memory/__init__.py 마지막 줄:
MemorySaver = InMemorySaver  # Kept for backwards compatibility
```

### InMemorySaver 내부 구조

```
storage: thread_id → checkpoint_ns → checkpoint_id → (serialized_checkpoint, serialized_metadata, parent_id)
writes:  (thread_id, checkpoint_ns, checkpoint_id) → (task_id, write_idx) → (task_id, channel, serialized_value, task_path)
blobs:   (thread_id, checkpoint_ns, channel, version) → serialized_blob
```

### Saver 선택 가이드

| Saver | 패키지 | Sync | Async | 프로덕션 | 용도 |
|-------|--------|------|-------|---------|------|
| `InMemorySaver` | `langgraph` (내장) | ✅ | ✅ | ❌ | 테스트/디버그 |
| `MemorySaver` | `langgraph` (내장) | ✅ | ✅ | ❌ | `InMemorySaver` alias |
| `SqliteSaver` | `langgraph-checkpoint-sqlite` | ✅ | ⚠️ | ⚠️ | 소규모/단일 스레드 |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | ✅ | ❌ | ✅ | 프로덕션 (sync) |
| `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | ❌ | ✅ | ✅ | 프로덕션 (async) |

### SqliteSaver 설정

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 인메모리 SQLite (테스트용)
with SqliteSaver.from_conn_string(":memory:") as memory:
    graph = builder.compile(checkpointer=memory)

# 파일 기반 (소규모 앱)
with SqliteSaver.from_conn_string("checkpoints.sqlite") as memory:
    graph = builder.compile(checkpointer=memory)
```

- `setup()` 자동 호출됨
- 단일 스레드 권장 (내부 lock은 있지만 multi-user 확장성 없음)

### PostgresSaver 설정

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgres://user:pass@localhost:5432/db?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as saver:
    saver.setup()  # 반드시 명시적으로 호출 (테이블 생성 + 마이그레이션)
    graph = builder.compile(checkpointer=saver)
    graph.invoke(inputs, {"configurable": {"thread_id": "1"}})
```

비동기 버전:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
    await saver.asetup()  # 반드시 명시적으로 호출
    graph = builder.compile(checkpointer=saver)
    await graph.ainvoke(inputs, {"configurable": {"thread_id": "1"}})
```

### Serializer & 암호화

*Source: `langgraph-docs-checkpointers-2026-07-30`*

**검증됨:** checkpointer가 state를 저장할 때 channel 값 직렬화는 serializer 객체가 담당한다. 기본은 `JsonPlusSerializer`이며 내부적으로 ormsgpack + JSON을 쓴다. LangChain/LangGraph primitives, datetime, enum, Pydantic v2, dataclass, numpy 등을 처리한다.

**검증됨:** msgpack encoder가 지원하지 않는 타입(예: Pandas DataFrame)은 `pickle_fallback`으로 처리할 수 있다.

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

graph.compile(
    checkpointer=InMemorySaver(serde=JsonPlusSerializer(pickle_fallback=True))
)
```

**검증됨:** `EncryptedSerializer`를 saver의 `serde` 인자로 넘기면 저장 상태 전체를 암호화한다. `from_pycryptodome_aes()`는 `LANGGRAPH_AES_KEY` 환경변수(또는 `key` 인자)에서 AES 키를 읽는다. LangSmith 실행 시 `LANGGRAPH_AES_KEY`가 있으면 암호화가 자동 활성화된다. 다른 암호화 방식은 `CipherProtocol` 구현으로 가능.

```python
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
from langgraph.checkpoint.postgres import PostgresSaver

serde = EncryptedSerializer.from_pycryptodome_aes()  # LANGGRAPH_AES_KEY 사용
checkpointer = PostgresSaver.from_conn_string("postgresql://...", serde=serde)
checkpointer.setup()
```

### 커스텀 Checkpointer 구현과 Conformance Suite

*Source: `langgraph-docs-checkpointers-2026-07-30`*

**검증됨:** persistence 계층은 두 storage 추상화 위에 있다 — **Checkpoints 테이블**(super-step당 1행, `channel_values`/`channel_versions`/`versions_seen` + parent 링크)과 **Writes 테이블**(super-step 내 node output당 1행, `(task_id, channel, value)`). custom saver는 두 테이블을 모두 관리하며 `BaseCheckpointSaver`를 상속해 `put`/`put_writes`/`get_tuple`/`list`/`delete_thread`(async는 `a*` 접두)를 구현한다. 누락 시 런타임 `NotImplementedError`.

**검증됨:** 구현 시 주의점.
- `put`은 `metadata`를 **전체 저장**해야 한다. LangGraph가 minor 릴리스에서 새 metadata 필드(예: delta channel용 `counters_since_delta_snapshot`)를 추가하므로 unknown key를 버리면 기능이 조용히 깨진다.
- `get_tuple`은 `checkpoint_id`가 있으면 정확히 그 checkpoint를, 없으면 thread+ns의 최신을 반환해야 한다. **specific-id 경로는 time travel과 [[DeltaChannel]] 재구성의 단일 실패점**이며, 깨지면 delta channel 상태가 조용히 빈 값으로 손상된다.
- `checkpoint_id`는 ULID라 사전식 정렬 시 큰 값이 최신 — "최신"은 `ORDER BY checkpoint_id DESC LIMIT 1`, "id 조회"는 PK 등치.
- `WRITES_IDX_MAP`(`langgraph.checkpoint.base`)은 특수 채널(`__error__`, `__interrupt__` 등)을 예약 음수 인덱스로 매핑한다.

**검증됨:** `langgraph-checkpoint-conformance` 패키지가 전체 계약(delta channel history 포함)을 검증한다. extended capability를 자동 감지해 관련 테스트를 돌린다. CI에서 실행 권장.

```python
from langgraph.checkpoint.conformance import checkpointer_test, validate
# validate(my_checkpointer) → report.passed_all_base() 로 계약 통과 여부 확인
```

> 기여 관점: custom saver PR을 낼 때 conformance suite 통과가 사실상의 계약이다.

### Extended Capabilities (Agent Server)

*Source: `langgraph-docs-checkpointers-2026-07-30`*

**검증됨:** 아래는 선택 구현이며, 구현 시 Agent Server가 startup에서 자동 감지해 해당 기능을 활성화한다.

| 메서드 | 활성화되는 기능 |
|--------|----------------|
| `adelete_for_runs` | Rollback multitask 전략 |
| `acopy_thread` | 효율적 thread forking |
| `aprune` | Thread history pruning |
| `aget_delta_channel_history` | 효율적 [[DeltaChannel]] 상태 재구성 |

**검증됨:** 사용 가능한 built-in saver 라이브러리: `langgraph-checkpoint`(base + `InMemorySaver` 내장), `langgraph-checkpoint-sqlite`, `langgraph-checkpoint-postgres`(LangSmith에서 사용), `langchain-azure-cosmosdb`(`CosmosDBSaver`/`CosmosDBSaverSync`, Microsoft Entra ID 인증).

---

## Source Code References

- Repo: `https://github.com/langchain-ai/langgraph`
- Commit: `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- Raw local path: `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/`
- Files read:
  - `libs/langgraph/langgraph/graph/state.py` — `StateGraph`, `CompiledStateGraph`, `compile()`
  - `libs/langgraph/langgraph/pregel/main.py` — runnable execution, state update, checkpoint update paths
  - `libs/langgraph/langgraph/pregel/_loop.py` — Pregel loop, task writes, checkpoint commit behavior
  - `libs/checkpoint/langgraph/checkpoint/base/__init__.py` — `BaseCheckpointSaver`, checkpoint data types
  - `libs/checkpoint/langgraph/checkpoint/memory/__init__.py` — in-memory saver implementation

## Human-in-the-Loop (Interrupt)
*Source: `langgraph-source-pregel-interrupts-2026-05-23`, `langgraph-docs-interrupts-2026-07-30`*

LangGraph는 checkpointing을 기반으로 두 가지 HITL 패턴을 제공한다. 두 방식 모두 **checkpointer와 thread_id가 필수**다.

> **최신 문서 기준(2026-07-30):** 공식 문서는 이제 `interrupt_before`/`interrupt_after`를 **static interrupts**로 부르며 **HITL에는 비권장**한다(디버깅/breakpoint 및 LangSmith Studio 용도). HITL은 동적 `interrupt()` 함수를 쓴다. Source: `langgraph-docs-interrupts-2026-07-30`

### 정적 중단: interrupt_before / interrupt_after (= static interrupts, 디버깅용)

`compile()` 시점(또는 runtime)에 중단할 노드를 지정한다. **HITL 워크플로에는 비권장** — 노드 단위로 step through 하는 breakpoint 용도다.

```python
graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"],   # 노드 실행 전 중단
    interrupt_after=["generate_draft"],  # 노드 실행 후 중단
)

# 1. 실행 — interrupt 노드에서 멈춤
graph.invoke(inputs, {"configurable": {"thread_id": "1"}})

# 2. 상태 확인 및 수정 (선택)
graph.update_state(
    {"configurable": {"thread_id": "1"}},
    {"state_key": new_value},
    as_node="human_review",
)

# 3. 재개 — None 입력으로 이어서 실행
graph.invoke(None, {"configurable": {"thread_id": "1"}})
```

**Pregel 내부 동작:**
- `interrupt_before_nodes`, `interrupt_after_nodes`로 저장
- stream 실행 시 `interrupt_before = interrupt_before or self.interrupt_before_nodes` 패턴으로 runtime override 가능
- `"*"` 또는 `All` 전달 시 모든 노드에서 인터럽트

### 동적 중단: interrupt() 함수 (현재 권장)

노드 함수 내에서 조건부로 중단하는 방식. HITL의 권장 패턴이다.

```python
from langgraph.types import interrupt, Command

def human_review_node(state):
    result = interrupt({
        "question": "이 결과를 승인하시겠습니까?",
        "draft": state["draft"]
    })
    # interrupt()가 resume 값을 반환 — 노드가 여기서 계속 실행됨
    if result == "approve":
        return {"approved": True}
    return {"approved": False, "feedback": result}

# 재개: Command(resume=...) 전달
graph.invoke(
    Command(resume="approve"),
    {"configurable": {"thread_id": "1"}}
)
```

#### 실행 API: `stream_events(version="v3")` (2026-07-30 문서 권장)

*Source: `langgraph-docs-interrupts-2026-07-30`*

**검증됨:** 위 `graph.invoke(...)`도 여전히 동작하며, 이 경우 interrupt는 `result["__interrupt__"]`로 노출된다. 다만 최신 공식 문서는 interrupt를 다루는 graph의 **권장 실행 방식으로 event streaming**을 제시한다. `graph.stream_events(..., version="v3")`는 typed projections를 제공한다.

- `stream.interrupts` — interrupt payload 튜플 (각 `Interrupt`는 `.id`, `.value`)
- `stream.interrupted` — 실행이 입력 대기로 멈췄으면 `True`
- `stream.output` — 최종 상태
- `stream.messages` / `stream.values` — 토큰 단위 메시지 / step별 상태 스냅샷

```python
config = {"configurable": {"thread_id": "thread-1"}}
stream = graph.stream_events({"input": "data"}, config=config, version="v3")
_ = stream.output                      # 스트림을 소진해 실행을 구동

if stream.interrupted:
    print(stream.interrupts)           # (Interrupt(value=..., id=...),)
    resumed = graph.stream_events(
        Command(resume=True), config=config, version="v3"
    )
    final = resumed.output
```

**검증됨:** 병렬 브랜치가 동시에 interrupt하면 `Command(resume={interrupt_id: value})` **맵**으로 한 번에 재개한다. Source: `langgraph-docs-interrupts-2026-07-30`

**검증됨:** `Command(resume=...)`는 invoke/stream/stream_events **입력으로 쓰이는 유일한** Command 패턴이다. `Command(update=/goto=/graph=)`는 노드 반환 전용 — 멀티턴 대화 지속에는 일반 입력 dict를 쓴다. Source: `langgraph-docs-interrupts-2026-07-30`

**검증됨 — 입력 검증 주의:** 노드 내 `while True` + `interrupt()` 루프는 금지다(재개 시 노드가 처음부터 재실행되어 지수적 재실행 발생). 노드당 `interrupt()`를 정확히 1회 호출하고, 무효 입력이면 재질문을 state에 저장한 뒤 **conditional edge로 노드에 되돌아오게** 한다. Source: `langgraph-docs-interrupts-2026-07-30`

**검증됨 — rules of interrupts:** ① `interrupt`를 bare `try/except`로 감싸지 말 것(특수 예외를 삼켜 interrupt가 전달 안 됨), ② 노드 내 interrupt 호출 순서 고정·조건부 skip 금지(매칭은 index 기반), ③ 직렬화 가능한 값만 전달, ④ interrupt 앞 side effect는 idempotent해야 함(재실행으로 중복). Source: `langgraph-docs-interrupts-2026-07-30`

**내부 구현 (`langgraph/types.py`):**
```python
def interrupt(value: Any) -> Any:
    conf = get_config()["configurable"]
    scratchpad = conf[CONFIG_KEY_SCRATCHPAD]
    idx = scratchpad.interrupt_counter()

    if scratchpad.resume and idx < len(scratchpad.resume):
        return scratchpad.resume[idx]          # ← 이미 resume 값 있으면 반환

    v = scratchpad.get_null_resume(True)
    if v is not None:
        scratchpad.resume.append(v)
        return v                               # ← 새 resume 값 반환

    raise GraphInterrupt(...)                  # ← 없으면 예외로 실행 중단
```

### interrupt_before/after vs interrupt() 비교

| 구분 | interrupt_before/after (static interrupts) | interrupt() |
|------|----------------------|-------------|
| 설정 위치 | compile() 시 또는 runtime | 노드 함수 내부 |
| 조건부 중단 | ❌ | ✅ |
| 코드 변경 | ❌ | ✅ |
| 용도 | **디버깅/breakpoint** (LangSmith Studio 포함) | **HITL 워크플로** |
| 현재 권장 (2026-07-30 문서) | HITL에는 비권장 | ✅ **권장** |

*Source: `langgraph-docs-interrupts-2026-07-30`*

---

## DeltaChannel — 효율적 누적 채널 저장

*Source: `langgraph-source-checkpoint-internals-2026-05-23`*

`DeltaChannel`은 메시지 히스토리처럼 **누적되는 채널**에 사용된다. Deep Agents의 `_DeepAgentState.messages`가 이 타입으로 선언된다. 일반 채널과 달리 매 super-step마다 전체 값을 직렬화하지 않고 **변경분(writes)만 저장**하다가 주기적으로 전체 스냅샷을 기록한다.

### 저장 전략

| 상황 | `channel_values`에 저장되는 값 |
|------|-------------------------------|
| 스냅샷 타이밍 (`updates >= snapshot_frequency` 또는 `supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`) | `_DeltaSnapshot(전체값)` |
| 일반 super-step | 저장 안 됨 — writes만 `checkpoint_writes`에 보존 |
| 일반 채널 | `ch.checkpoint()` 직렬화 값 |

### 스냅샷 판단 — `delta_channels_to_snapshot()`

```python
# 두 조건 중 하나 충족 시 스냅샷
updates >= ch.snapshot_frequency          # 누적 업데이트 수
supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT  # 최대 super-step 수 상수
```

순수 함수 — mutation 없음.

### 복원 — `channels_from_checkpoint()`

```
DeltaChannel이고 channel_values에 없으면 (_needs_replay=True):
    saver.get_delta_channel_history(config, channels=delta_names)  ← 배치 단일 호출
    → history["seed"] (가장 최근 _DeltaSnapshot 또는 pre-migration 값)
    → replay_ch = spec.from_checkpoint(seed)
    → replay_ch.replay_writes(history["writes"])  ← seed 이후 writes 순서 재적용

일반 채널 또는 channel_values에 있으면:
    spec.from_checkpoint(checkpoint["channel_values"][k])
```

`saver` 또는 `config`가 `None`이면 ancestor walk를 건너뛰어 빈 채널로 복원된다 (테스트/디버그 시나리오).

### exit 모드 버전 bump

exit 모드에서는 마지막 super-step에 채널 쓰기가 없으면 `channel_versions`가 bump되지 않아 `_DeltaSnapshot` blob이 saver에서 누락될 수 있다. `create_checkpoint()`는 이를 방지하기 위해 `updated_channels`에 없는 snapshot 대상 채널에 `get_next_version()`으로 수동 bump한다.

---

## Tests

Source: `langgraph-tests-checkpoint-recovery-2026-05-23` (`libs/langgraph/tests/test_pregel.py`)

### test_pending_writes_resume

노드 일부가 실패한 실행에서 `invoke(None, config)` 재개 시 동작을 검증한다.

- **설정:** 두 노드(`one`, `two`) 중 `two`가 첫 실행에서 예외를 발생시킴
- **검증 포인트:**
  - 재개 후 `one`은 호출 횟수가 증가하지 않음 (pending write 재사용)
  - `two`는 재시도됨
  - `durability="exit"` 여부에 따라 저장되는 checkpoint 개수가 달라짐
- **의미:** pending writes recovery의 canonical 기준 테스트

### test_run_from_checkpoint_id_retains_previous_writes

특정 `checkpoint_id`로 재실행할 때 기존 writes 컨텍스트가 유지됨을 검증한다.

- **설정:** 첫 번째 실행에서 checkpoint_id 저장 → 동일 checkpoint_id로 두 번째 invoke
- **검증 포인트:**
  - 두 번째 실행에서 이전 writes 문맥이 보존됨 (fork 실행)
  - time-travel replay 시 stale RESUME writes가 제거됨
- **의미:** Time Travel / fork 실행의 writes 연속성 보장 확인

### test_invoke_checkpoint_two

노드 에러 발생 시 checkpoint rollback과 `__error__` pending write 기록을 검증한다.

- **설정:** 노드에서 의도적 예외 발생
- **검증 포인트:**
  - 에러 발생 시 checkpoint가 롤백됨
  - 에러가 `pending_writes`의 `__error__` 채널에 기록됨
- **의미:** 에러 → pending write → 재개 전체 사이클 검증

## Related Pages

- [[LangGraph]]
- [[StateGraph]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]
- [[Memory]]
- [[Context Engineering]]

## Open Questions

**해소됨 (2026-05-23):**
- ✅ `create_checkpoint` 구현 → DeltaChannel 분기, exit 모드 버전 bump, `_DeltaSnapshot` vs `ch.checkpoint()`. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)
- ✅ `channels_from_checkpoint` 구현 → ancestor walk 패턴: `_needs_replay` → `get_delta_channel_history` 배치 → `from_checkpoint(seed)` + `replay_writes()`. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)
- ✅ `DeltaChannel` snapshot 조건 → `snapshot_frequency` 또는 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)

**잔여 질문:**
- `thread_id` 없이 `invoke`를 호출하면 어떤 에러가 발생하는가? — Needs Verification
- `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가? — Needs Source
- pending writes recovery를 정의하는 canonical test는 어디에 있는가? — Needs Source
- `_put_exit_delta_writes()` 검증 테스트 → `_checkpoint.py`에 없음, `_loop.py` 탐색 필요
- `saver.get_delta_channel_history()` 메서드는 `BaseCheckpointSaver`에 언제 추가됐는가? — Needs Source (문서에는 존재하나 도입 버전 미상, Source: `langgraph-docs-checkpointers-2026-07-30`)
- checkpoint schema migration 대응은 공식적으로 어떻게 권장되는가? — Needs Source

**신규 (2026-07-30 문서 기반):**
- `stream_events(version="v3")`의 typed projection 객체(`stream.output`/`interrupts`/`interrupted`/`messages`/`values`) 소스 구현 위치는? — Needs Source (Source: `langgraph-docs-interrupts-2026-07-30`)
- `EncryptedSerializer`/`JsonPlusSerializer(pickle_fallback=True)`의 소스 구현과 `pickle_fallback` 보안 경고 위치는? — Needs Source (Source: `langgraph-docs-checkpointers-2026-07-30`)
- `langgraph-checkpoint-conformance`가 검증하는 base capability 전체 목록과 실패 기준은? — Needs Source
- `CosmosDBSaver`(Azure)의 sync/async 클래스 차이와 Entra ID 인증 흐름 소스는? — Needs Source

## Sources

- `langgraph-docs-checkpointers-2026-07-30`
- `langgraph-docs-interrupts-2026-07-30`
- `langgraph-docs-persistence-2026-07-30`
- `langgraph-docs-persistence-2026-05-20` *(구조 변경 전 스냅샷 — [[#문서 구조 변경 안내 (2026-07-30 재확인)]] 참고)*
- `langgraph-docs-durable-execution-2026-05-20` *(페이지 폐지, 308 → persistence)*
- `langgraph-reference-stategraph-compile-2026-05-20`
- `langgraph-reference-checkpoint-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
- `langgraph-source-checkpoint-savers-2026-05-23`
- `langgraph-source-pregel-interrupts-2026-05-23`
- `langgraph-source-checkpoint-internals-2026-05-23`
- `langgraph-tests-checkpoint-recovery-2026-05-23`
