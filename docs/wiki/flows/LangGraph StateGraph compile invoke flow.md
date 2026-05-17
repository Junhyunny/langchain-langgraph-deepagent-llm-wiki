---
type: flow
framework: LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangGraph StateGraph compile invoke flow

## 요약

이 페이지는 `StateGraph.compile()`에서 `.invoke()`까지의 실행 흐름을 추적하며, 그래프가 어떻게 구축되고 어떻게 실행되는지를 다룬다.

*상태: 초안 스텁이다. 아직 소스 코드를 읽지 않았다. 아래 내용은 모두 가설이다.*

## 진입점

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("agent", agent_fn)
graph.add_node("tools", tool_fn)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", route_fn, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")

compiled = graph.compile(checkpointer=MemorySaver())
result = compiled.invoke({"messages": [...]}, config={"configurable": {"thread_id": "1"}})
```

## 호출 경로(가설 — 미검증)

### compile()

1. `StateGraph.compile(checkpointer)`
   - 그래프 구조를 검증한다
   - 내부 표현을 구축한다(`Pregel`과 유사한가?)
   - checkpointer를 연결한다
   - `CompiledStateGraph`를 반환한다

### invoke()

1. `CompiledStateGraph.invoke(input, config)`
   - 존재하면 thread_id용 체크포인트를 불러온다
   - 입력과 체크포인트 상태를 병합한다
   - 실행 루프에 진입한다

2. 실행 루프:
   - 현재 상태에서 다음 노드를 결정한다
   - 노드 함수를 실행한다
   - 상태 reducer를 적용해 업데이트를 병합한다
   - 체크포인트를 저장한다
   - `interrupt_before` / `interrupt_after`를 확인한다
   - `END`에 도달할 때까지 반복한다

3. 최종 상태를 반환한다

## 읽어야 할 파일

- 추후 작성: `libs/langgraph/langgraph/graph/state.py` (`StateGraph`, `CompiledStateGraph`)
- 추후 작성: `libs/langgraph/langgraph/pregel/` (실행 런타임)
- 추후 작성: `libs/checkpoint/langgraph/checkpoint/base.py`

## 찾은 테스트

- 추후 작성

## 다이어그램

```
compile(checkpointer)
    │
    ▼
validate graph
    │
    ▼
build CompiledStateGraph
    │
    ▼
invoke(input, config)
    │
    ▼
load checkpoint (thread_id)
    │
    ▼
merge input + checkpoint state
    │
    ▼
─────── execution loop ───────
    │
    ▼
determine next node
    │
    ▼
execute node fn(state) → update
    │
    ▼
apply state reducers
    │
    ▼
save checkpoint
    │
    ├── interrupt? → pause (return partial state)
    │
    └── continue
            │
            ▼
        more nodes? → loop
            │
        END → return final state
──────────────────────────────
```

## 미해결 질문

- 런타임은 `Pregel` 기반인가? 코드에서는 어디에 있는가?
- 상태 reducer는 어떻게 동작하는가? 어디에서 정의되고 적용되는가?
- `interrupt_before`는 실행을 어떻게 중단하고 상태를 직렬화하는가?
- 각 체크포인트에는 정확히 무엇이 저장되는가?

## 관련 페이지

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[LangGraph Code Map]]

## 소스

*아직 없음.*
