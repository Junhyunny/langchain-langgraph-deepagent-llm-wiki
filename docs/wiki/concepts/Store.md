---
type: concept
framework:
  - LangGraph
  - Deep Agents
status: verified
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-store-base-2026-05-23
  - langgraph-venv-store-memory-2026-05-25
---

# Store

## 요약

[[Store]]는 [[LangGraph]]의 cross-thread 장기 메모리 인터페이스다. [[Checkpointing]]이 단일 `thread_id` 내 실행 상태를 저장하는 것과 달리, Store는 여러 thread에 걸쳐 공유되는 데이터(사용자 선호, 누적 지식, 메모리 등)를 namespace + key 기반으로 저장하고 조회한다.

짧은 답: `BaseStore`의 모든 편의 메서드(`get`, `search`, `put`, `delete`, `list_namespaces`)는 `batch`/`abatch` 두 추상 메서드로 위임된다. 구현체는 이 두 메서드만 구현하면 전체 인터페이스가 동작한다.

## 중요한 이유

Checkpointer만으로는 thread 간 정보 공유가 불가능하다. 사용자 선호, 멀티 세션 지식, agent 간 공유 데이터가 필요할 때 Store가 필요하다. `create_deep_agent(store=...)` 파라미터로 Deep Agents에도 직접 연결된다.

## 핵심 개념

- **Namespace** — `tuple[str, ...]` 타입의 계층 경로. 예: `("user", "123", "memories")`, `("agent", "todos")`. Namespace 내에서 key는 고유하다.
- **Key** — namespace 내 항목의 고유 식별자.
- **Item** — namespace + key로 식별되는 저장 단위. 필드: `value: dict[str, Any]`, `key: str`, `namespace: tuple[str, ...]`, `created_at: datetime`, `updated_at: datetime`.
- **SearchItem** — `Item` 상속에 `score: float | None` 추가. semantic search 결과에 사용.
- **`batch`/`abatch`** — `BaseStore`의 유일한 추상 메서드. 구현 필수. 나머지 편의 메서드는 모두 이것의 래퍼다.
- **Op 타입** — `GetOp`, `SearchOp`, `PutOp`, `ListNamespacesOp`. 모두 NamedTuple.

## BaseStore 인터페이스

**추상 메서드 (구현 필수):**
```python
def batch(ops: Iterable[Op]) -> list[Result]        # 동기 배치
async def abatch(ops: Iterable[Op]) -> list[Result]  # 비동기 배치
```

**편의 메서드 (batch/abatch 위임):**

| 메서드 | 시그니처 | 반환 |
|--------|----------|------|
| `get` | `(namespace, key, *, refresh_ttl=None)` | `Item \| None` |
| `search` | `(namespace_prefix, /, *, query=None, filter=None, limit=10, offset=0, refresh_ttl=None)` | `list[SearchItem]` |
| `put` | `(namespace, key, value, index=None, *, ttl=NOT_PROVIDED)` | `None` |
| `delete` | `(namespace, key)` | `None` |
| `list_namespaces` | `(*, prefix=None, suffix=None, max_depth=None, limit=100, offset=0)` | `list[tuple[str, ...]]` |

비동기 변형: `aget`, `asearch`, `aput`, `adelete`, `alist_namespaces`

**검증됨:** `value=None`으로 `put`을 호출하면 해당 key를 삭제하는 것과 동일한 효과다. 별도 `delete` 메서드 호출과 의미가 같다. Source: `langgraph-store-base-2026-05-23`

## Op 타입 상세

**GetOp**
```python
GetOp(namespace: tuple[str, ...], key: str, refresh_ttl: bool = True)
```

**SearchOp**
```python
SearchOp(
    namespace_prefix: tuple[str, ...],
    filter: dict[str, Any] | None,
    limit: int = 10,
    offset: int = 0,
    query: str | None,         # vector search용 (구현체가 지원 시)
    refresh_ttl: bool = True,
)
```

**PutOp**
```python
PutOp(
    namespace: tuple[str, ...],
    key: str,
    value: dict[str, Any] | None,  # None이면 삭제
    index: Literal[False] | list[str] | None = None,
    ttl: float | None = None,
)
```

**ListNamespacesOp**
```python
ListNamespacesOp(
    match_conditions: tuple[MatchCondition, ...] | None,
    max_depth: int | None,
    limit: int = 100,
    offset: int = 0,
)
```

## Checkpointer vs Store

**검증됨:** Checkpointer와 Store는 분리된 인터페이스다. Source: `langgraph-docs-persistence-2026-05-20`

| | Checkpointer (단기) | Store (장기) |
|--|--|--|
| 범위 | 단일 thread | 여러 thread 간 |
| 식별 | `thread_id` + `checkpoint_id` | namespace + key |
| 용도 | 실행 재개, 상태 복원 | 사용자 선호, 누적 지식 |
| 저장 단위 | `StateSnapshot` (graph state 전체) | `Item` (임의 dict) |
| API | `get_state`, `update_state`, `get_state_history` | `store.get`, `store.put`, `store.search` |

## TTL 지원

**검증됨:** `supports_ttl: bool = False`가 기본값이다. TTL은 프로덕션 구현체에서 선택적으로 지원된다. `NOT_PROVIDED` sentinel은 `ttl=None`(명시적 TTL 없음)과 기본값 사용을 구분하기 위해 존재한다. Source: `langgraph-store-base-2026-05-23`

```python
TTLConfig(
    refresh_on_read: bool,
    default_ttl: float | None,
    sweep_interval_minutes: int | None,
)
```

## Vector Search (IndexConfig)

**검증됨:** `SearchOp`의 `query` 파라미터로 semantic search가 가능하지만, 구현체가 vector store를 지원할 때만 의미 있다. `InMemoryStore`는 기본적으로 keyword filter만 지원한다. Source: `langgraph-store-base-2026-05-23`

```python
IndexConfig(
    dims: int,
    embed: Embeddings | EmbeddingsFunc | AEmbeddingsFunc | str,
    fields: list[str] | None,
)
```

`PutOp`의 `index` 파라미터:
- `False` → 인덱싱 안 함
- `list[str]` → 지정 필드만 인덱싱
- `None` → 기본값 사용

## 사용 패턴

**LangGraph에서 Store 주입:**
```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
graph = StateGraph(...).compile(store=store)
graph.invoke({"messages": [...]}, config={"configurable": {"thread_id": "t1"}})
```

**Deep Agents에서 Store 연결:**
```python
from deepagents import create_deep_agent
from langgraph.store.memory import InMemoryStore

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    store=InMemoryStore(),
)
```

**Namespace 설계 예시:**
```python
# 멀티 사용자 분리
store.put(("user", user_id, "memories"), "pref_lang", {"value": "Korean"})
store.get(("user", user_id, "memories"), "pref_lang")

# agent별 할 일 목록
store.put(("agent", agent_id, "todos"), task_id, {"status": "pending", "title": "..."})
store.search(("agent", agent_id, "todos"), filter={"status": "pending"})
```

## 구현 Notes

**검증됨:** `BaseStore`의 핵심 추상화 포인트는 `batch`/`abatch` 단 2개뿐이다. 나머지 편의 메서드는 모두 이것의 래퍼다. 구현체는 이 두 메서드만 구현하면 전체 API가 동작한다. Source: `langgraph-store-base-2026-05-23`

**검증됨:** `MatchCondition`은 `match_type: NamespaceMatchType`("prefix" 또는 "suffix")와 `path: NamespacePath`(`tuple[str | Literal["*"], ...]`)로 namespace 패턴 매칭에 사용된다. Source: `langgraph-store-base-2026-05-23`

**검증됨:** `InvalidNamespaceError(ValueError)`는 잘못된 namespace 설정 시 발생한다. Source: `langgraph-store-base-2026-05-23`

## 관련 페이지

- [[LangGraph]]
- [[Checkpointing]]
- [[Memory]]
- [[Deep Agents]]
- [[LangGraph Code Map]]

## InMemoryStore 내부 구현 (검증됨)

Source: `langgraph-venv-store-memory-2026-05-25`

### 데이터 구조

```python
class InMemoryStore(BaseStore):
    _data: dict[tuple[str, ...], dict[str, Item]]
    # namespace → key → Item

    _vectors: dict[tuple[str, ...], dict[str, dict[str, list[float]]]]
    # namespace → key → path → vector (float list)
```

### Vector Search 지원

**검증됨:** `InMemoryStore`는 `index` 파라미터를 통해 **vector search를 직접 지원**한다.

```python
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": init_embeddings("openai:text-embedding-3-small"),
        "fields": ["text"],   # 어떤 필드를 임베딩할지
    }
)
store.put(("docs",), "doc1", {"text": "Python tutorial"})
results = store.search(("docs",), query="python programming")
```

`index` 없이 생성 시 semantic search 비활성 — filter 기반 exact search만 가능.

### `batch()` 처리 흐름

```
ops: list[Op]
  ↓ GetOp → _data[ns].get(key)
  ↓ SearchOp → _filter_items(op) → cosine similarity → sorted SearchItem[]
  ↓ PutOp → _extract_texts() → embeddings.embed_documents() → _insertinmem_store()
            → _apply_put_ops() → _data[ns][key] = Item(...)
  ↓ ListNamespacesOp → _handle_list_namespaces(op)
```

### Cosine Similarity (벡터 검색)

- `_embed_search_queries()`: ThreadPoolExecutor로 쿼리 임베딩 병렬 처리
- `_batch_search()`: `_cosine_similarity(query_vector, candidate_vectors)` → 점수 내림차순 정렬
- **Max pooling**: 같은 (namespace, key)에 여러 path 벡터가 있을 때 최고 점수 유지
- `score: float | None` — `SearchItem`에 포함

### `put()` 시 임베딩

- `value=None` → `_data[ns].pop(key)` + `_vectors[ns].pop(key)` — 삭제
- `index_config` 있고 `embeddings` 있을 때만 임베딩 수행
- `PutOp.index=False` → 해당 항목 임베딩 스킵

### 프로덕션 Store 구현체

**현재 확인된 패키지:**

| 패키지 | 구현체 | 백엔드 |
|--------|--------|--------|
| `langgraph-checkpoint-postgres` | `PostgresStore` (추정) | PostgreSQL |
| `langgraph-checkpoint-redis` | `RedisStore` (추정) | Redis |
| `langgraph.store.memory` | `InMemoryStore` | Dict (메모리) |

⚠️ **가설**: 프로덕션 구현체 패키지명은 위와 같을 것으로 추정되나 직접 소스 확인 필요. Status: Needs verification

## 미해결 질문

- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? — ⚠️ 가설 수준
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`?)
- `list_namespaces`의 wildcard `"*"` 패턴 실제 동작 확인

## 소스

- `langgraph-store-base-2026-05-23`
- `langgraph-venv-store-memory-2026-05-25`
