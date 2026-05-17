# 로드맵

## 현재 목표

LangChain, LangGraph, Deep Agents를 다음을 수행할 수 있을 만큼 깊이 이해한다.

1. 아키텍처를 설명한다
2. 트레이드오프를 비교한다
3. 공개 API에서 내부 구현까지 추적한다
4. 의미 있는 실험을 수행한다
5. 테스트를 이해한다
6. 이슈를 재현한다
7. 작은 PR 기회를 식별한다
8. 높은 품질의 업스트림 기여를 제출한다

## 1단계 — 아키텍처 개요 (현재)

- [ ] LangChain 핵심 추상화를 읽고 이해한다
- [ ] LangGraph 핵심 추상화를 읽고 이해한다
- [ ] Deep Agents 핵심 추상화를 읽고 이해한다
- [ ] 검증된 요약으로 프레임워크 페이지를 채운다
- [ ] 초기 트레이드오프를 담은 비교 페이지 초안을 작성한다

## 2단계 — 내부 추적

- [ ] 공개 API부터 런타임까지 LangChain `create_agent` 호출 경로를 추적한다
- [ ] LangGraph `StateGraph.compile()` 및 `.invoke()` 내부를 추적한다
- [ ] Deep Agents `create_deep_agent` 호출 경로를 추적한다
- [ ] 검증된 파일 경로와 호출 경로로 흐름 페이지를 채운다

## 3단계 — 개념 심화

- [ ] Checkpointing: LangGraph와 LangChain에서 어떻게 동작하는지 이해한다
- [ ] Tool Calling: 도구가 어떻게 등록되고, 해석되며, 호출되는지 이해한다
- [ ] Memory: 단기 메모리와 장기 메모리, 프레임워크별 차이를 이해한다
- [ ] Subagents: 오케스트레이션 패턴을 이해한다
- [ ] Context Engineering: 컨텍스트가 어떻게 구성되고 관리되는지 이해한다

## 4단계 — 실험

- [ ] LangChain, LangGraph, Deep Agents에서 동일한 리서치 agent 작업을 실행한다
- [ ] 동작, 출력, 내부 구현을 비교한다
- [ ] 실험 보고서에 문서화한다

## 5단계 — PR 준비

- [ ] 프레임워크별로 최소 하나의 작은 PR 후보를 식별한다
- [ ] 최소 재현 예제를 만든다
- [ ] 근거가 포함된 PR 후보 페이지를 작성한다

## 다음 학습 영역

- LangGraph 체크포인팅 내부 구조
