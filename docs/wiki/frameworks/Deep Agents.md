---
type: framework
framework: Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Deep Agents

## 요약

Deep Agents는 깊이 있는 오케스트레이션이 필요한 멀티 에이전트 시스템을 구축하기 위해 설계된 프레임워크다(LangChain 생태계의 일부). 서브에이전트 생성, 도구 위임, 다단계 추론을 위한 구조화된 패턴을 제공한다.

*상태: 소스 필요. 이 페이지는 초안 스텁이다. "Deep Agents"의 정확한 범위와 저장소 위치를 확인해야 한다.*

## 중요한 이유

Deep Agents는 [[LangChain]]과 잠재적으로 [[LangGraph]] 위에 놓인 더 높은 수준의 추상화를 나타내며, 더 정교한 오케스트레이션 패턴을 가능하게 한다. 이를 이해하면 복잡한 멀티 에이전트 파이프라인이 어떻게 구성되는지 알 수 있다.

## 핵심 추상화

- `create_deep_agent()` — 주요 진입점(소스 필요: 정확한 시그니처와 동작)
- 서브에이전트 오케스트레이션 패턴
- 도구 레지스트리
- 에이전트 간 상태와 컨텍스트 전달

*소스 필요: 여기의 모든 추상화는 아직 검증되지 않았다.*

## 공개 API

- `create_deep_agent()` — 소스 필요.

## 내부 구현 맵

- 추후 작성: `create_deep_agent` 추적 → [[Deep Agents create_deep_agent flow]]

## 관련 테스트

- 소스 필요.

## 관련 예제

- `examples/` — 추후 추가 예정.

## 미해결 질문

- Deep Agents는 어떤 저장소에 존재하는가? `langchain-ai/deepagents`인가?
- `create_deep_agent`와 `create_react_agent`의 정확한 역할 차이는 무엇인가?
- 내부적으로 서브에이전트 오케스트레이션을 어떻게 처리하는가?
- 서브에이전트가 호출될 때의 호출 경로는 무엇인가?
- 도구 레지스트리는 어디에서 유지되는가?
- 상태 관리를 위해 LangGraph에 의존하는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Subagents]]
- [[Tool Calling]]
- [[Deep Agents Code Map]]
- [[Deep Agents create_deep_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

*아직 없음.*
