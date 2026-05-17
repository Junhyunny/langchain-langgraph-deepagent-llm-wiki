---
type: concept
framework:
  - LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# StateGraph

## 요약

`StateGraph`는 [[LangGraph]]에서 상태를 가진 agent 그래프를 정의하기 위한 핵심 추상화다. 공유된 타입 상태 위에서 동작하는 노드(함수)와 엣지(전이)로 agent를 방향 그래프로 표현한다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

`StateGraph`는 LangGraph에서 복잡한 agent를 정의하는 기본 방식이다. 그 컴파일 및 실행 모델을 이해하는 것은 LangGraph 내부 구조를 이해하기 위한 토대다.

## 핵심 개념

- **상태 스키마** — 공유 상태를 정의하는 typed dict 또는 dataclass
- **노드** — Python 함수 `(state) -> state_update`
- **엣지** — 한 노드에서 다른 노드로의 무조건 전이
- **조건부 엣지** — 라우팅 함수가 결정하는 전이
- **`START` / `END`** — 특별한 내장 노드
- **`compile()`** — `CompiledGraph` runnable을 생성한다
- **`invoke()` / `stream()`** — 컴파일된 그래프를 실행한다

## 상세

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list

graph = StateGraph(State)
graph.add_node("agent", agent_fn)
graph.add_node("tools", tool_fn)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")
compiled = graph.compile()
result = compiled.invoke({"messages": [...]})
```

*소스 필요: 정확한 API를 확인해야 한다.*

## 소스 코드 참조

- 저장소: langgraph
- 커밋: UNKNOWN
- 파일: 추후 작성

## 테스트

- 소스 필요.

## 미해결 질문

- `StateGraph.compile()`은 내부적으로 `CompiledGraph`를 어떻게 생성하는가?
- 조건부 엣지는 런타임에 어떻게 평가되는가?
- 상태 업데이트 병합은 어떻게 동작하는가(reducer)?

## 관련 페이지

- [[LangGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## 소스

*아직 없음.*
