---
type: framework
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain

## 요약

LangChain은 LLM 기반 애플리케이션을 구축하기 위한 프레임워크다. 체인, agent, 도구, 메모리, 문서 로더를 위한 추상화를 제공한다.

*상태: 소스 필요. 이 페이지는 초안 스텁이다.*

## 중요한 이유

LangChain은 이 생태계의 기반 프레임워크다. LangGraph와 Deep Agents는 모두 LangChain 추상화 위에 구축되므로, 이를 이해하기 전에 LangChain을 이해하는 것이 필요하다.

## 핵심 추상화

- `Runnable` — 모든 조합 가능한 컴포넌트의 기본 인터페이스
- `Chain` — 작업의 연속
- `AgentExecutor` — agent를 루프에서 실행하는 런타임
- `Tool` — LLM에 노출되는 외부 기능
- `BaseChatModel` — 모든 LLM 통합의 기본 클래스
- `BaseMemory` — 메모리 시스템의 기본 클래스
- `BaseRetriever` — 문서 검색의 기본 클래스

## 공개 API

- `create_react_agent()`
- `AgentExecutor`
- `ChatPromptTemplate`
- `RunnableSequence` / LCEL 파이프 `|`

*소스 필요: 각각이 어느 모듈에 존재하는지 확인해야 한다.*

## 내부 구현 맵

- 추후 작성: `create_react_agent` 추적 → [[LangChain create_agent flow]]

## 관련 테스트

- 소스 필요.

## 관련 예제

- `examples/` — 추후 추가 예정.

## 미해결 질문

- `AgentExecutor`는 도구 호출 루프를 언제 멈출지 어떻게 결정하는가?
- `create_react_agent`와 `create_openai_functions_agent`의 차이는 무엇인가?
- 메시지 히스토리는 내부적으로 어디에서 관리되는가?

## 관련 페이지

- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Memory]]
- [[LangChain Code Map]]
- [[LangChain create_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

*아직 없음.*
