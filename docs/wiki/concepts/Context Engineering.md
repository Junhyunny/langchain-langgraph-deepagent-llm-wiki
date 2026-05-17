---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Context Engineering

## 요약

Context Engineering은 출력의 품질과 신뢰성을 극대화하기 위해 LLM에 전달되는 컨텍스트(시스템 프롬프트, 대화 히스토리, 도구 설명, 주입된 데이터)를 의도적으로 구성하는 실천이다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

컨텍스트는 LLM의 주요 입력이다. 컨텍스트가 잘못 구성되면 agent 동작도 나빠진다. 프레임워크가 컨텍스트를 어떻게 구축하는지 이해하는 것은 agent 실패를 진단하고 agent 품질을 개선하는 데 필수적이다.

## 핵심 개념

- **시스템 프롬프트** — LLM에 대한 최상위 지시문
- **메시지 히스토리** — 이전 대화 턴
- **도구 스키마 주입** — 컨텍스트에 추가되는 도구 설명
- **RAG 주입** — 컨텍스트에 추가되는 검색 문서
- **컨텍스트 윈도우** — LLM이 처리할 수 있는 최대 토큰 수
- **컨텍스트 압축** — 컨텍스트 윈도우에 맞추기 위해 히스토리를 줄이는 것

## 프레임워크별 동작

### LangChain

- `ChatPromptTemplate`가 프롬프트를 구성한다
- 메시지 히스토리는 `BaseChatMessageHistory`를 통해 관리된다
- *소스 필요.*

### LangGraph

- 상태의 메시지 목록이 LLM 노드에 전달된다
- 프롬프트는 보통 노드 함수 내부에서 구성된다
- *소스 필요.*

### Deep Agents

- 서브에이전트로의 컨텍스트 전달은 핵심 관심사다
- *소스 필요.*

## 미해결 질문

- 각 프레임워크는 컨텍스트 윈도우 초과를 어떻게 처리하는가?
- 어떤 압축 또는 요약 전략이 내장되어 있는가?
- 도구 설명은 어떤 형식으로 구성되고 주입되는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Memory]]
- [[Subagents]]
- [[Tool Calling]]

## 소스

*아직 없음.*
