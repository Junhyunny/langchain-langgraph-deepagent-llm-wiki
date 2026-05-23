---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - deepagents-docs-harness-2026-05-19
  - deepagents-docs-context-engineering-2026-05-18
  - langgraph-docs-persistence-2026-05-20
  - langgraph-store-base-2026-05-23
  - langchain-source-memory-api-2026-05-23
---

# Memory

## 요약

Memory는 LLM agent가 여러 턴, 세션, 작업에 걸쳐 정보를 유지하고 다시 불러올 수 있게 하는 메커니즘을 뜻한다. Memory는 단기적일 수도 있고(세션 내), 장기적일 수도 있다(세션 간).

*상태: LangGraph Store 인터페이스 + LangChain 레거시 API deprecated 현황 추가됨.*

## 중요한 이유

Memory가 없으면 모든 agent 턴은 무상태다. Memory는 연속성, 개인화, 누적된 지식을 가능하게 한다. 프레임워크가 Memory를 어떻게 구현하는지 이해하면 버그를 추적하고 더 나은 agent를 설계하는 데 도움이 된다.

## 핵심 개념

- **단기 메모리** — 세션 내 컨텍스트에 포함된 메시지 히스토리
- **장기 메모리** — 세션 간에 다시 불러오는 외부 저장소
- **에피소드 메모리** — 특정 과거 사건 또는 상호작용
- **의미 메모리** — 일반적인 사실 또는 지식
- **메모리 저장소** — 장기 메모리를 위한 외부 데이터베이스
- **메모리 검색** — 저장소에서 관련 메모리를 선택하는 것

## 프레임워크별 동작

### LangChain

*Source: `langchain-source-memory-api-2026-05-23`*

#### 레거시 API — 사실상 제거됨

| API | 상태 | 대체 |
|-----|------|------|
| `RunnableWithMessageHistory` | **deprecated** (langchain-core 1.3.3, 제거 예정 2.0.0) | LangGraph checkpointer (`create_agent(checkpointer=...)`) |
| `MessageGraph` | **deprecated** (langgraph 1.0.0, 제거 예정 2.0.0) | `StateGraph` + `MessagesState` |
| `ConversationBufferMemory` | ⚠️ 경로 404 (현재 LangChain 1.x에 파일 없음) | LangGraph checkpointer |
| `ConversationSummaryMemory` | ⚠️ 경로 404 (현재 LangChain 1.x에 파일 없음) | `SummarizationMiddleware` |

**참고:** `langchain-community` 패키지가 2026-05-22 sunset 선언됨. `ConversationBufferMemory` 등의 명시적 deprecated 선언 문서는 미발견이나, 파일 자체가 현재 LangChain 1.x API에 존재하지 않는다.

#### 현재 권장 패턴 (LangChain 1.x)

**단기 메모리 (thread-scoped):**
```python
from langchain.agents import create_agent
from langchain.checkpoint.memory import InMemorySaver

# add_messages reducer로 메시지 히스토리 자동 관리
agent = create_agent(
    model="...",
    checkpointer=InMemorySaver(),
)
# 같은 thread_id로 재호출 → 이전 대화 히스토리 유지
result = agent.invoke(input, {"configurable": {"thread_id": "session-1"}})
```

**대화 히스토리 자동 요약 (컨텍스트 압축):**
```python
from langchain.agents.middleware.summarization import SummarizationMiddleware

agent = create_agent(
    model="...",
    middleware=[
        SummarizationMiddleware(
            trigger=("fraction", 0.8),  # 컨텍스트 80% 차면 요약
            keep=10,                    # 최근 10개 메시지 보존
        )
    ],
    checkpointer=InMemorySaver(),
)
```

`SummarizationMiddleware` trigger 옵션:
- `("fraction", 0.8)` — context window의 80% 초과 시
- `("tokens", 3000)` — 토큰 수 기준
- `("messages", 50)` — 메시지 수 기준

**장기 메모리 (cross-session):**
```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
agent = create_agent(model="...", store=store)
# tool 내부에서 ToolRuntime.store로 접근
```

### LangGraph
*Source: `langgraph-docs-persistence-2026-05-20`*

**단기 메모리 (thread-scoped checkpoint):**

- Checkpointer는 `thread_id`를 primary key로 사용해 super-step 경계마다 상태를 저장한다
- 같은 `thread_id`로 재실행하면 이전 상태부터 이어서 실행 (session continuity)
- `graph.get_state(config)` → 최신 `StateSnapshot` 조회
- `graph.get_state_history(config)` → thread 내 모든 checkpoint 조회 (최신 순)
- `graph.update_state(config, values)` → 새 checkpoint 생성 (기존 mutate 아님)

**장기 메모리 (cross-thread Store):**
*Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-store-base-2026-05-23`*

- Checkpointer는 단일 thread 내 상태를 저장, **Store는 thread 간 공유 데이터**를 저장 — 두 개념은 분리된 인터페이스
- `InMemoryStore` 등 Store 구현체를 graph에 주입하여 사용자 선호, 누적 지식 등을 스레드 간에 공유

| | Checkpointer (단기) | Store (장기) |
|--|--|--|
| 범위 | 단일 thread | 여러 thread 간 |
| 식별 | `thread_id` + `checkpoint_id` | namespace + key |
| 용도 | 실행 재개, 상태 복원 | 사용자 선호, 누적 지식 |
| API | `get_state`, `update_state` | `store.get`, `store.put` |

**BaseStore 인터페이스 계약:**

- **추상 메서드**: `batch(ops)` / `abatch(ops)` 단 2개 — 나머지 편의 메서드는 모두 이것의 래퍼
- `store.get(namespace, key)` → `Item | None`
- `store.put(namespace, key, value)` → `None` (`value=None` 전달 시 해당 key 삭제)
- `store.search(namespace_prefix, query=None, filter=None, limit=10)` → `list[SearchItem]`
- `store.delete(namespace, key)` → `None`

**Namespace & Item 구조:**

```python
# namespace: tuple[str, ...] 계층 경로
("user", "alice", "memories")   # 멀티 사용자 분리 패턴
("agent", "todos")

# Item 필드
item.value      # dict[str, Any]
item.key        # str
item.namespace  # tuple[str, ...]
item.created_at # datetime
item.updated_at # datetime

# SearchItem: Item + score
search_item.score  # float | None (vector search 시 relevance score)
```

**Vector Search (semantic search):**

- `search(namespace_prefix, query="검색어")` → 구현체가 vector store를 지원할 때만 semantic search 작동
- `InMemoryStore` 기본값: keyword filter만 지원, vector search 미지원
- Vector search 활성화: `IndexConfig(dims=..., embed=...)` 설정으로 `InMemoryStore` 또는 외부 Store에서 지원 가능

**프로덕션 Store 구현체:**
- `InMemoryStore` — 개발/테스트용 (vector search 기본 미지원)
- Redis, PostgreSQL 기반 구현체 — `langgraph-checkpoint-redis` 등 별도 패키지 필요 (source: 미수집)

### Deep Agents
*Source: `deepagents-docs-harness-2026-05-19`, `deepagents-docs-context-engineering-2026-05-18`*

**Verified Facts:**
- `AGENTS.md` 파일 형식 사용 (agents.md 표준)
- `memory=` 파라미터에 파일 경로 목록 전달
- **항상 로드** — Skills와 달리 progressive disclosure 없음
- agent state에 영속됨; backend(StateBackend, StoreBackend, FilesystemBackend)에 저장
- agent가 interaction/feedback 기반으로 memory 직접 업데이트 가능

**Memory vs Skills (원문 기준):**
| | Memory (`AGENTS.md`) | Skills (`SKILL.md`) |
|--|--|--|
| 로딩 방식 | **항상 로드** | **progressive disclosure** (frontmatter 먼저, 관련 시 전체 로드) |
| 용도 | 일반 규칙, 선호도, 프로젝트 가이드라인 | 특화 워크플로우, 도메인 지식 |
| 토큰 효율 | 낮음 (항상 소비) | 높음 (필요 시에만 소비) |

**Long-term memory (스레드 간 영속):**
- 기본 `StateBackend`: 단일 스레드 내에서만 영속
- 스레드 간 영속: `CompositeBackend` + `StoreBackend` (`/memories/` 경로 라우팅)

```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    )

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    backend=make_backend,
    memory=["/memory/AGENTS.md"],
)
```
Source: `deepagents-docs-context-engineering-2026-05-18`

## 미해결 질문

**해소됨 (2026-05-23):**
- ✅ LangGraph Store의 내부 구현은? `store.get`, `store.put` 계약은? → `BaseStore`의 핵심은 `batch`/`abatch` 추상 메서드 2개. `get`→`Item|None`, `put`→`None` (value=None=삭제), `search`→`list[SearchItem]`. (Source: `langgraph-store-base-2026-05-23`)
- ✅ Store에서 관련 메모리를 검색해 컨텍스트에 주입하는 방법은? → `store.search(namespace_prefix, query="검색어")`로 semantic search. `InMemoryStore` 기본값은 keyword filter만 지원. Vector search는 `IndexConfig(dims, embed)` 설정 필요. (Source: `langgraph-store-base-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `ConversationBufferMemory`, `ConversationSummaryMemory` deprecated 여부 → 경로 404 (현재 LangChain 1.x에 파일 없음). `langchain-community` 2026-05-22 sunset. 현재 권장: LangGraph checkpointer + SummarizationMiddleware. (Source: `langchain-source-memory-api-2026-05-23`)
- ✅ `RunnableWithMessageHistory` deprecated 여부 → **YES.** deprecated (langchain-core 1.3.3, 제거 예정 2.0.0). 대체: LangGraph checkpointer. (Source: `langchain-source-memory-api-2026-05-23`)
- ✅ `MemorySaver`와 `InMemorySaver` 동일 여부 → **동일. `MemorySaver = InMemorySaver` (하위 호환 alias).** (Source: `langgraph-source-checkpoint-savers-2026-05-23`)

**잔여 질문:**
- `ConversationBufferMemory`의 명시적 deprecated 선언 문서 위치 — Needs Source (파일 자체가 404, 마이그레이션 가이드 403으로 접근 불가)
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? — Needs Source
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`와의 관계?) — Needs Source

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Checkpointing]]
- [[Context Engineering]]

## 소스

- `deepagents-docs-harness-2026-05-19`
- `deepagents-docs-context-engineering-2026-05-18`
- `langgraph-docs-persistence-2026-05-20`
- `langgraph-store-base-2026-05-23`
