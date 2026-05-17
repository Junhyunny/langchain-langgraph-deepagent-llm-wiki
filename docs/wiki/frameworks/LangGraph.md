---
type: framework
framework: LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangGraph

## 요약

LangGraph는 상태를 가진 멀티 액터 LLM 애플리케이션을 그래프로 구축하기 위한 라이브러리다. 명시적인 상태 관리, 체크포인팅, 그래프 기반 제어 흐름을 통해 LangChain을 확장한다.

*상태: 소스 필요. 이 페이지는 초안 스텁이다.*

## 중요한 이유

LangGraph는 영속적 상태, human-in-the-loop, 구조화된 실행 흐름이 필요한 복잡한 agent를 위한 핵심 오케스트레이션 프레임워크다. 이를 이해하는 것은 현대 AI agent를 구축하고 기여하는 데 필수적이다.

## 핵심 추상화

- `StateGraph` — 노드, 엣지, 상태 스키마를 정의한다
- `CompiledGraph` — `StateGraph.compile()`이 생성하는 컴파일된 runnable
- `BaseCheckpointSaver` — 영속화를 위한 추상 클래스
- `MemorySaver` — 인메모리 checkpointer(비영속)
- `interrupt_before` / `interrupt_after` — human-in-the-loop 훅
- `Send` — 여러 대상으로 라우팅하는 동적 엣지

## 공개 API

- `StateGraph(schema)`
- `graph.add_node(name, fn)`
- `graph.add_edge(from, to)`
- `graph.add_conditional_edges(from, fn, map)`
- `graph.compile(checkpointer=...)`
- `compiled.invoke(input, config)`
- `compiled.stream(input, config)`
- `compiled.astream_events(input, config)`

*소스 필요: 모듈 경로를 확인해야 한다.*

## 내부 구현 맵

- 추후 작성: `StateGraph.compile()` 및 `.invoke()` 추적 → [[LangGraph StateGraph compile invoke flow]]
- 추후 작성: 체크포인팅 추적 → [[Checkpointing]]

## 관련 테스트

- 소스 필요.

## 관련 예제

- `examples/` — 추후 추가 예정.

## 미해결 질문

- `StateGraph.compile()`은 runnable을 내부적으로 어떻게 생성하는가?
- 체크포인팅은 어떤 상태 델타를 저장할지 어떻게 결정하는가?
- `interrupt_before`는 실행을 어떻게 일시 중지하고 재개하는가?
- `MemorySaver`와 영속적 checkpointer의 차이는 무엇인가?

## 관련 페이지

- [[LangChain]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[Subagents]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

*아직 없음.*
