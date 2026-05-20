---
type: concept
framework:
  - LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-20
sources:
  - langgraph-reference-stategraph-compile-2026-05-20
  - langgraph-docs-persistence-2026-05-20
  - langgraph-source-checkpoint-runtime-2026-05-20
---

# StateGraph

## 요약

`StateGraph`는 [[LangGraph]]에서 상태를 가진 agent 그래프를 정의하기 위한 핵심 추상화다. 공유된 타입 상태 위에서 동작하는 노드(함수)와 엣지(전이)로 agent를 방향 그래프로 표현한다.

*상태: checkpointing 관점의 `compile(checkpointer=...)` 계약과 source attach path를 commit `aa322c13cd5f16a3f6254a931a4104e412cd687c` 기준으로 검증했다.*

## 중요한 이유

`StateGraph`는 LangGraph에서 복잡한 agent를 정의하는 기본 방식이다. 그 컴파일 및 실행 모델을 이해하는 것은 LangGraph 내부 구조를 이해하기 위한 토대다.

## 핵심 개념

- **상태 스키마** — 공유 상태를 정의하는 typed dict 또는 dataclass
- **노드** — Python 함수 `(state) -> state_update`
- **엣지** — 한 노드에서 다른 노드로의 무조건 전이
- **조건부 엣지** — 라우팅 함수가 결정하는 전이
- **`START` / `END`** — 특별한 내장 노드
- **`compile()`** — `CompiledStateGraph` runnable을 생성한다
- **`invoke()` / `stream()`** — 컴파일된 그래프를 실행한다
- **checkpointer** — `compile(checkpointer=...)`로 연결되는 versioned short-term memory

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

Reference 기준으로 `compile(checkpointer=...)`는 checkpointer를 graph의 versioned short-term memory로 연결한다. Checkpointer가 있으면 invoke config에 `thread_id`를 전달해야 한다. Source: `langgraph-reference-stategraph-compile-2026-05-20`

Source 기준으로 `compile()`은 `ensure_valid_checkpointer()`를 거친 checkpointer를 `CompiledStateGraph(..., checkpointer=checkpointer, ...)`에 전달한다. 이후 `START`, node, edge, waiting edge, branch를 attach하고 `compiled.validate()`를 반환한다. `CompiledStateGraph`는 `Pregel`을 상속한다. Source: `langgraph-source-checkpoint-runtime-2026-05-20`

## 소스 코드 참조

- 저장소: langgraph
- 커밋: `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- 파일:
  - `libs/langgraph/langgraph/graph/state.py`
  - `libs/langgraph/langgraph/pregel/main.py`
  - `libs/langgraph/langgraph/pregel/_loop.py`

## 테스트

- 소스 필요.

## 미해결 질문

- `compiled.validate()`는 정확히 어떤 graph 구조 검사를 수행하는가?
- 조건부 엣지는 런타임에 어떻게 평가되는가?
- 상태 업데이트 병합은 어떻게 동작하는가(reducer)?
- `checkpointer=None`의 subgraph inheritance는 parent runtime config에서 정확히 어떻게 전달되는가?

## 관련 페이지

- [[LangGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## 소스

- `langgraph-reference-stategraph-compile-2026-05-20`
- `langgraph-docs-persistence-2026-05-20`
- `langgraph-source-checkpoint-runtime-2026-05-20`
