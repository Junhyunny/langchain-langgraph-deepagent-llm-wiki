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

# Evaluation

## 요약

Evaluation은 agent의 품질, 정확성, 동작을 측정하는 과정이다. 여기에는 오프라인 벤치마크, 온라인 모니터링, 회귀 테스트가 포함된다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

Evaluation이 없으면 agent 개선이 실제인지 착시인지 판단하기 어렵다. 좋은 PR에는 테스트가 포함되거나 갱신되므로, 업스트림 기여를 위해서도 평가 프레임워크는 중요하다.

## 핵심 개념

- **오프라인 평가** — 배포 전에 테스트 케이스를 실행하는 것
- **온라인 평가** — 운영 중인 agent 동작을 모니터링하는 것
- **LLM-as-judge** — agent 출력을 채점하는 데 LLM을 사용하는 것
- **Trajectory evaluation** — 최종 출력뿐 아니라 agent 단계의 순서를 평가하는 것
- **회귀 테스트** — 새로운 변경이 기존 동작을 깨뜨리지 않도록 보장하는 것
- **LangSmith** — LangChain의 추적 및 평가 플랫폼

## 프레임워크별 동작

### LangChain

- `langchain`은 `langchain.evaluation`에 평가 유틸리티를 제공한다
- *소스 필요.*

### LangGraph

- LangGraph 앱은 LangSmith를 통해 추적할 수 있다
- *소스 필요.*

### Deep Agents

- 추후 작성
- *소스 필요.*

## 미해결 질문

- 각 프레임워크에는 어떤 내장 평가 유틸리티가 존재하는가?
- LangSmith를 Trajectory evaluation에 어떻게 사용할 수 있는가?
- 각 프레임워크의 테스트 스위트에는 어떤 테스트 패턴이 사용되는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[LangChain Code Map]]
- [[LangGraph Code Map]]

## 소스

*아직 없음.*
