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

# Tool Calling

## 요약

Tool Calling은 추론 중 LLM이 외부 함수(도구)를 선택하고 호출하는 메커니즘이다. LLM은 구조화된 도구 호출 요청을 출력하고, 런타임은 해당 도구를 실행한 뒤 결과를 메시지로 반환한다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

Tool Calling은 LLM agent가 외부 시스템과 상호작용하는 기본 방식이다. 이를 이해하는 것은 agent를 구축하고, 예상치 못한 동작을 디버깅하며, 모델 출력에서 도구 실행까지의 호출 경로를 추적하는 데 필수적이다.

## 핵심 개념

- 도구 정의(이름, 설명, 스키마)
- 도구 호출(LLM의 구조화된 출력)
- 도구 실행(런타임이 함수를 호출함)
- 도구 결과(`ToolMessage`로 반환됨)
- 도구 레지스트리(사용 가능한 도구의 집합)

## 프레임워크별 동작

### LangChain

- 도구는 `create_react_agent()`에 전달되거나 `.bind_tools()`를 통해 모델에 바인딩된다
- `AgentExecutor`가 도구 호출 루프를 처리한다
- *소스 필요.*

### LangGraph

- 도구는 보통 `StateGraph` 안의 노드다
- 또는 `langgraph.prebuilt`의 `ToolNode`로 처리된다
- *소스 필요.*

### Deep Agents

- 추후 작성 — 도구 레지스트리와 도구 위임 메커니즘이 명확하지 않다
- *소스 필요.*

## 구현 메모

- 도구 스키마는 일반적으로 JSON Schema다
- LLM은 함수/도구 호출을 네이티브로 지원해야 한다(예: OpenAI, Anthropic)
- 병렬 도구 호출: 한 번의 LLM 단계에서 여러 도구를 호출할 수 있다

## 미해결 질문

- 각 프레임워크는 병렬 도구 호출을 내부적으로 어떻게 처리하는가?
- 도구가 예외를 발생시키면 어떻게 되는가?
- 도구 스키마는 어떻게 검증되는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Subagents]]

## 소스

*아직 없음.*
