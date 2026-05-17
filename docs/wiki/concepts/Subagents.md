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

# Subagents

## 요약

Subagents는 더 큰 워크플로의 일부로 부모(오케스트레이션) agent에 의해 호출되는 agent다. 각 서브에이전트는 자신만의 도구, 상태, 프롬프트를 가질 수 있다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

서브에이전트 오케스트레이션은 복잡한 멀티 에이전트 시스템의 핵심 패턴이다. 부모 agent가 서브에이전트에 어떻게 위임하는지, 컨텍스트가 어떻게 전달되는지, 결과가 어떻게 수집되는지를 이해하는 것은 확장 가능한 agent 파이프라인을 구축하는 데 필수적이다.

## 핵심 개념

- **Orchestrator** — 계획하고 위임하는 최상위 agent
- **Subagent** — 하위 작업을 수행하는 특화된 agent
- **위임** — 부모에서 서브에이전트로 작업 또는 컨텍스트를 전달함
- **집계** — 여러 서브에이전트의 결과를 수집하고 병합함
- **Handoff** — agent 간 제어를 넘김

## 프레임워크별 동작

### LangChain

- 서브에이전트는 도구로 감싸서 [[Tool Calling]]을 통해 호출할 수 있다
- *소스 필요.*

### LangGraph

- 서브에이전트는 노드로 호출되는 별도의 `StateGraph` 인스턴스일 수 있다
- 또는 병렬 디스패치를 위해 `Send`로 구현할 수 있다
- *소스 필요.*

### Deep Agents

- 서브에이전트 오케스트레이션은 핵심 설계 패턴이다
- `create_deep_agent`가 서브에이전트 관리를 캡슐화할 가능성이 크다
- *소스 필요: 검증되지 않았다.*

## 미해결 질문

- 각 프레임워크는 orchestrator에서 subagent로 컨텍스트를 어떻게 전달하는가?
- 결과는 어떻게 집계되는가?
- 서브에이전트가 실패하면 어떻게 되는가?
- 서브에이전트 상태는 격리되는가, 공유되는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Context Engineering]]
- [[Deep Agents create_deep_agent flow]]

## 소스

*아직 없음.*
