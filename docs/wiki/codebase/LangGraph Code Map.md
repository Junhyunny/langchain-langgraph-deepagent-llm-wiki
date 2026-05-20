---
type: code_map
framework: LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-20
sources:
  - langgraph-docs-persistence-2026-05-20
  - langgraph-reference-checkpoint-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
---

# LangGraph Code Map

## 요약

이 페이지는 LangGraph 저장소 구조를 매핑한다. 소스 코드를 읽을 때 탐색 가이드로 사용한다.

*상태: checkpointing 관련 경로는 commit `aa322c13cd5f16a3f6254a931a4104e412cd687c` 기준으로 검증했다. 전체 저장소 구조는 아직 미완성이다.*

## 저장소

- **저장소:** `https://github.com/langchain-ai/langgraph`
- **커밋:** `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- **Raw local path:** `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/`

## 주요 패키지 / 디렉터리

```
libs/
  langgraph/          # Main graph runtime
  checkpoint/         # Checkpoint saver abstractions
  checkpoint-sqlite/  # SQLite checkpoint backend
  checkpoint-postgres/# Postgres checkpoint backend
  langgraph_sdk/      # Client SDK (optional)
```

*부분 검증됨: checkpointing 관련 디렉터리 기준. 전체 monorepo 구조는 추가 확인 필요.*

## 중요한 진입점

- `langgraph.graph.StateGraph` — 그래프를 정의한다
- `langgraph.graph.state.CompiledStateGraph` — 컴파일된 runnable
- `langgraph.checkpoint.base.BaseCheckpointSaver` — 체크포인트 인터페이스
- `langgraph.checkpoint.memory.MemorySaver` — 인메모리 checkpointer
- `langgraph.prebuilt.ToolNode` — 미리 만들어진 도구 실행 노드
- `langgraph.prebuilt.create_react_agent` — 미리 만들어진 react agent
- `langgraph.pregel` runtime — graph 실행, super-step, checkpoint commit, pending writes와 관련

## 읽어야 할 소스 파일

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

## 읽어야 할 테스트

- checkpoint saver tests: 추후 작성
- pending writes recovery tests: 추후 작성
- interrupt/resume tests: 추후 작성

## 불명확한 영역

- `compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가?
- 상태 reducer는 어디에서 적용되는가?
- 스트리밍은 어떻게 구현되는가?
- pending writes recovery test는 어디에 있는가?
- `DeltaChannel` pruning/copying safety test는 어디에 있는가?

## 관련 페이지

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]

## 소스

- `langgraph-docs-persistence-2026-05-20`
- `langgraph-reference-checkpoint-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
