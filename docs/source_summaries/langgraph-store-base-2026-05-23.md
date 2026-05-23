---
type: source_summary
source_id: langgraph-store-base-2026-05-23
title: "LangGraph — BaseStore / InMemoryStore (Store Interface Source Code)"
framework: LangGraph
retrieved_at: 2026-05-23
status: verified
confidence: high
---

# Source Summary: LangGraph — BaseStore / InMemoryStore

## Source Info
- **Source ID:** `langgraph-store-base-2026-05-23`
- **Type:** source_code
- **URL:** https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint/langgraph/store/base/__init__.py
- **Retrieved At:** 2026-05-23
- **Version / Commit:** UNKNOWN (main branch)

---

## Key Facts

### 핵심 데이터 클래스

**Item**
- namespace + key로 식별되는 저장 단위
- 필드: `value: dict[str, Any]`, `key: str`, `namespace: tuple[str, ...]`, `created_at: datetime`, `updated_at: datetime`

**SearchItem(Item)**
- `Item`을 상속하여 relevance score 추가
- 추가 필드: `score: float | None`

### Namespace 개념
- namespace는 `tuple[str, ...]` 타입 — 계층 경로 표현
- 예: `("user", "123", "memories")`, `("agent", "todos")`
- Namespace 내에서 key는 고유 식별자

### BaseStore — 핵심 인터페이스

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

### 연산 클래스 (Op 타입들)

**GetOp(NamedTuple)**
- 필드: `namespace: tuple[str, ...]`, `key: str`, `refresh_ttl: bool = True`

**SearchOp(NamedTuple)**
- 필드: `namespace_prefix: tuple[str, ...]`, `filter: dict[str, Any] | None`, `limit: int = 10`, `offset: int = 0`, `query: str | None`, `refresh_ttl: bool = True`

**PutOp(NamedTuple)**
- 필드: `namespace: tuple[str, ...]`, `key: str`, `value: dict[str, Any] | None`, `index: Literal[False] | list[str] | None = None`, `ttl: float | None = None`
- `value=None` → 해당 key 삭제

**ListNamespacesOp(NamedTuple)**
- 필드: `match_conditions: tuple[MatchCondition, ...] | None`, `max_depth: int | None`, `limit: int = 100`, `offset: int = 0`

### TTL 지원
- `supports_ttl: bool = False` (기본값)
- `ttl_config: TTLConfig | None = None`
- `TTLConfig` 필드: `refresh_on_read: bool`, `default_ttl: float | None`, `sweep_interval_minutes: int | None`

### Vector Search (IndexConfig)
- `IndexConfig` 필드: `dims: int`, `embed: Embeddings | EmbeddingsFunc | AEmbeddingsFunc | str`, `fields: list[str] | None`
- `SearchOp`의 `query` 파라미터로 semantic search 가능 (구현체가 vector store 지원 시)
- `PutOp`의 `index` 파라미터: `False`=인덱싱 안 함, `list[str]`=지정 필드만 인덱싱, `None`=기본값

### MatchCondition
- `match_type: NamespaceMatchType` — `"prefix"` 또는 `"suffix"`
- `path: NamespacePath` — `tuple[str | Literal["*"], ...]`

### 예외
- `InvalidNamespaceError(ValueError)` — 잘못된 namespace 설정 시 발생

---

## Important Terms
- [[Checkpointing]] — Store는 Checkpointer와 구분되는 long-term memory 레이어
- [[Memory]] — Store가 cross-thread 영속 memory의 구현 기반
- [[Deep Agents]] — `create_deep_agent(store=...)` 파라미터로 전달 가능

---

## Interpretation
- `BaseStore`의 핵심 추상화 포인트는 `batch`/`abatch` 단 2개뿐이다. 나머지 편의 메서드는 모두 이것의 래퍼다.
- Namespace = 계층 경로 (tuple), Key = 해당 경로 내 고유 ID — 두 값의 조합이 Item을 식별한다.
- `value=None`으로 `put` 호출 = delete 의미 (별도 delete 메서드와 동일 효과).
- `search`의 `query` 파라미터는 구현체가 vector store를 지원할 때만 의미 있다. `InMemoryStore`는 기본적으로 keyword filter만 지원.
- TTL은 기본 비활성화(`supports_ttl=False`). 프로덕션 Store 구현체에서 선택적 지원.

---

## Implications for My AI Agent Project
- agent가 cross-thread 정보 접근이 필요하다면 `Checkpointer` 대신 `Store`를 쓴다.
- `create_deep_agent(store=InMemoryStore())` — 개발/테스트용 in-memory store.
- 프로덕션에서는 `InMemoryStore` 대신 Redis, PostgreSQL 기반 Store 구현체 필요.
- namespace 설계가 중요: `("user", user_id, "memories")` 같은 계층 구조로 멀티 사용자 분리 가능.

---

## Open Questions
- `InMemoryStore`의 구체적 구현은? vector search를 지원하는가?
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? (`langgraph-checkpoint-redis` 등)
- `query` 파라미터를 사용한 semantic search는 어떻게 embeddings와 연결되는가?
- `aget`/`asearch` 등 async 메서드의 내부 구현은 `abatch` 위임인가?
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`?)

---

## Used By
*(아직 없음 — wiki 페이지 생성 필요)*

---

## Notes
- `batch`/`abatch`만 구현하면 나머지 모든 편의 메서드가 자동으로 작동하는 설계.
- `NOT_PROVIDED` sentinel은 `ttl=None`(명시적 TTL 없음)과 `ttl=NOT_PROVIDED`(기본값 사용) 구분용.
