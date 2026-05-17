---
type: code_map
framework: LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangGraph Code Map

## 요약

이 페이지는 LangGraph 저장소 구조를 매핑한다. 소스 코드를 읽을 때 탐색 가이드로 사용한다.

*상태: 초안 스텁이다. 실제 저장소를 기준으로 한 소스 검증이 필요하다.*

## 저장소

- **저장소:** `https://github.com/langchain-ai/langgraph`
- **커밋:** UNKNOWN

## 주요 패키지 / 디렉터리

```
libs/
  langgraph/          # Main graph runtime
  checkpoint/         # Checkpoint saver abstractions
  checkpoint-sqlite/  # SQLite checkpoint backend
  checkpoint-postgres/# Postgres checkpoint backend
  langgraph_sdk/      # Client SDK (optional)
```

*소스 필요: 실제 디렉터리 구조를 확인해야 한다.*

## 중요한 진입점

- `langgraph.graph.StateGraph` — 그래프를 정의한다
- `langgraph.graph.state.CompiledStateGraph` — 컴파일된 runnable
- `langgraph.checkpoint.base.BaseCheckpointSaver` — 체크포인트 인터페이스
- `langgraph.checkpoint.memory.MemorySaver` — 인메모리 checkpointer
- `langgraph.prebuilt.ToolNode` — 미리 만들어진 도구 실행 노드
- `langgraph.prebuilt.create_react_agent` — 미리 만들어진 react agent

*소스 필요.*

## 읽어야 할 소스 파일

- 추후 작성: `StateGraph.__init__`, `StateGraph.compile()`에서 시작 → [[LangGraph StateGraph compile invoke flow]]
- 추후 작성: 체크포인트 저장 추적 → [[Checkpointing]]

## 읽어야 할 테스트

- 추후 작성

## 불명확한 영역

- `compile()`은 어떻게 `Pregel`과 유사한 런타임을 생성하는가?
- 상태 reducer는 어디에서 적용되는가?
- 스트리밍은 어떻게 구현되는가?

## 관련 페이지

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]

## 소스

*아직 없음.*
