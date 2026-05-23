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
---

# Memory

## 요약

Memory는 LLM agent가 여러 턴, 세션, 작업에 걸쳐 정보를 유지하고 다시 불러올 수 있게 하는 메커니즘을 뜻한다. Memory는 단기적일 수도 있고(세션 내), 장기적일 수도 있다(세션 간).

*상태: LangGraph 섹션 추가됨. LangChain 섹션 소스 필요.*

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

- `ConversationBufferMemory`, `ConversationSummaryMemory` 등
- 체인 또는 agent에 연결된다
- *소스 필요.*

### LangGraph
*Source: `langgraph-docs-persistence-2026-05-20`*

**단기 메모리 (thread-scoped checkpoint):**

- Checkpointer는 `thread_id`를 primary key로 사용해 super-step 경계마다 상태를 저장한다
- 같은 `thread_id`로 재실행하면 이전 상태부터 이어서 실행 (session continuity)
- `graph.get_state(config)` → 최신 `StateSnapshot` 조회
- `graph.get_state_history(config)` → thread 내 모든 checkpoint 조회 (최신 순)
- `graph.update_state(config, values)` → 새 checkpoint 생성 (기존 mutate 아님)

**장기 메모리 (cross-thread Store):**

- Checkpointer는 단일 thread 내 상태를 저장, **Store는 thread 간 공유 데이터**를 저장 — 두 개념은 분리된 인터페이스
- `InMemoryStore` 등 Store 구현체를 graph에 주입하여 사용자 선호, 누적 지식 등을 스레드 간에 공유

| | Checkpointer (단기) | Store (장기) |
|--|--|--|
| 범위 | 단일 thread | 여러 thread 간 |
| 식별 | `thread_id` + `checkpoint_id` | namespace + key |
| 용도 | 실행 재개, 상태 복원 | 사용자 선호, 누적 지식 |
| API | `get_state`, `update_state` | `store.get`, `store.put` |

Source: `langgraph-docs-persistence-2026-05-20`

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

- LangGraph Store의 내부 구현은? `store.get`, `store.put` 계약은? — Needs Source
- Store에서 관련 메모리를 검색해 컨텍스트에 주입하는 방법은? (vector search 연동?) — Needs Source
- LangChain의 `ConversationBufferMemory`, `ConversationSummaryMemory`는 현재도 권장 API인가, 아니면 deprecated인가? — Needs Source
- LangGraph에서 `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가, 다른 클래스인가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Checkpointing]]
- [[Context Engineering]]

## 소스

- `deepagents-docs-harness-2026-05-19`
- `deepagents-docs-context-engineering-2026-05-18`
- `langgraph-docs-persistence-2026-05-20`
