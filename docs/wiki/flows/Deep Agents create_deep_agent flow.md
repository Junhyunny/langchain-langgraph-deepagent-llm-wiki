---
type: flow
framework: Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Deep Agents create_deep_agent flow

## 요약

이 페이지는 Deep Agents에서 `create_deep_agent()`의 실행 흐름을 추적한다.

*상태: 초안 스텁이다. 아직 소스 코드를 읽지 않았다. 저장소 위치도 검증되지 않았다. 모든 내용은 가설이다.*

## 진입점

```python
# Hypothetical — needs source
from deepagents import create_deep_agent

agent = create_deep_agent(
    llm=...,
    tools=...,
    subagents=...,
)
result = agent.invoke({"input": "..."})
```

*소스 필요: 실제 API 시그니처를 알 수 없다.*

## 호출 경로(가설 — 미검증)

1. `create_deep_agent(llm, tools, subagents, ...)`
   - orchestrator agent를 구축한다
   - 서브에이전트를 등록한다(도구일 가능성도 있음)
   - 실행 그래프를 구성한다(LangGraph 기반인가?)

2. `agent.invoke(input)`
   - orchestrator가 입력을 받는다
   - 작업 분해를 계획한다
   - 하위 작업을 서브에이전트에 위임한다
   - 결과를 수집하고 집계한다
   - 최종 출력을 반환한다

## 읽어야 할 파일

- 추후 작성: 먼저 실제 저장소를 찾아야 한다

## 찾은 테스트

- 추후 작성

## 미해결 질문

- 실제 저장소 URL은 무엇인가?
- `create_deep_agent`의 함수 시그니처는 무엇인가?
- 내부적으로 LangGraph를 사용하는가?
- 서브에이전트는 어떻게 표현되는가(도구인가? 노드인가? 별도의 그래프인가?)
- 컨텍스트는 서브에이전트로 어떻게 전달되는가?
- 결과는 어떻게 집계되는가?

## 관련 페이지

- [[Deep Agents]]
- [[Deep Agents Code Map]]
- [[Subagents]]
- [[LangGraph]]
- [[Tool Calling]]

## 소스

*아직 없음.*
