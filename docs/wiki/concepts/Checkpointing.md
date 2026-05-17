---
type: concept
framework:
  - LangGraph
  - LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Checkpointing

## 요약

Checkpointing은 agent 그래프의 상태를 단계 사이 또는 세션 간에 영속화하는 메커니즘이다. [[LangGraph]]에서는 각 노드 실행 후 체크포인트가 저장되며, 저장된 어느 지점에서든 재개할 수 있다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

Checkpointing은 다음을 가능하게 한다.
- 일시 중지하고 재개할 수 있는 장기 실행 agent 워크플로
- human-in-the-loop 상호작용(승인을 위해 일시 중지하고 이후 재개)
- 장애 허용성(실패 후 마지막 체크포인트부터 재개)
- 디버깅(어느 체크포인트에서든 재생)
- 다중 세션 연속성(같은 스레드, 다른 세션)

## 핵심 개념

- **체크포인트** — 특정 단계에서의 그래프 상태 스냅샷
- **Thread ID** — 대화 또는 세션 스레드를 식별한다
- **Checkpoint ID** — 스레드 내 특정 스냅샷을 식별한다
- **`BaseCheckpointSaver`** — 체크포인트 저장을 위한 추상 인터페이스
- **`MemorySaver`** — 인메모리 비영속 checkpointer
- **영속적 checkpointer** — SQLite, PostgreSQL 기반(소스 필요)

## 프레임워크별 동작

### LangGraph

- `StateGraph.compile(checkpointer=saver)`는 체크포인팅을 활성화한다
- `config = {"configurable": {"thread_id": "..."}}`
- 상태 델타는 각 노드 실행 후 저장된다
- `MemorySaver`는 개발용이고, 영속 saver는 운영용이다
- *소스 필요: 정확한 동작을 확인해야 한다.*

### LangChain

- 네이티브 체크포인팅 지원이 제한적이다
- *소스 필요.*

## 구현 메모

- 각 체크포인트는 노드 이름, 상태 스냅샷, 다음 노드를 저장한다
- 재개 시 마지막 체크포인트를 다시 불러와 실행을 이어간다
- *소스 필요.*

## 소스 코드 참조

- 저장소: langgraph
- 커밋: UNKNOWN
- 파일: 추후 작성 (`libs/langgraph/`, `libs/checkpoint/`)

## 테스트

- 소스 필요.

## 미해결 질문

- LangGraph는 단계별로 어떤 상태 델타를 저장할지 어떻게 결정하는가?
- 각 체크포인트에는 정확히 무엇이 저장되는가?
- `interrupt_before`는 실행을 어떻게 일시 중지하며 체크포인트는 어떤 모습인가?
- `MemorySaver`와 SQLite saver의 차이는 무엇인가?
- 스키마 버전이 달라져도 체크포인트를 마이그레이션할 수 있는가?

## 관련 페이지

- [[LangGraph]]
- [[StateGraph]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## 소스

*아직 없음.*
