# 로드맵

## 현재 목표

LangChain, LangGraph, Deep Agents를 다음을 스스로 할 수 있을 만큼 깊이 이해한다.

1. 아키텍처를 설명한다
2. 트레이드오프를 비교한다
3. 공개 API에서 내부 구현까지 추적한다
4. 의미 있는 실험을 수행한다
5. 테스트를 읽고 동작 근거를 파악한다
6. 이슈를 스스로 재현한다
7. 근본 원인을 분석하고 패치 방향을 결정한다
8. 검토 가능한 PR을 스스로 작성해 제출한다

## 1단계 — 아키텍처 개요 (현재)

- [x] LangChain 핵심 추상화를 읽고 이해한다
- [x] LangGraph 핵심 추상화를 읽고 이해한다
- [x] Deep Agents 핵심 추상화를 읽고 이해한다
- [x] 검증된 요약으로 프레임워크 페이지를 채운다
- [x] 초기 트레이드오프를 담은 비교 페이지 초안을 작성한다

## 2단계 — 내부 추적

- [x] 공개 API부터 런타임까지 LangChain `create_agent` 호출 경로를 추적한다
- [x] LangGraph `StateGraph.compile()` 및 `.invoke()` 내부를 추적한다
- [x] Deep Agents `create_deep_agent` 호출 경로를 추적한다
- [x] 검증된 파일 경로와 호출 경로로 흐름 페이지를 채운다

## 3단계 — 개념 심화

- [x] Checkpointing: LangGraph와 LangChain에서 어떻게 동작하는지 이해한다
- [x] Tool Calling: 도구가 어떻게 등록되고, 해석되며, 호출되는지 이해한다
- [x] Memory: 단기 메모리와 장기 메모리, 프레임워크별 차이를 이해한다
- [x] Subagents: 오케스트레이션 패턴을 이해한다
- [x] Context Engineering: 컨텍스트가 어떻게 구성되고 관리되는지 이해한다
- [x] Agent Runtime: 모델 + 오케스트레이션 + 도구 개념 정립
- [x] Guardrails: 입출력 검증 패턴 정리
- [x] Handoffs: 에이전트 간 제어 이전 패턴 정리
- [x] Tracing: 실행 흐름 기록 메커니즘 정리
- [ ] Reasoning/Planning: ReAct, CoT, Plan-and-Execute 각 프레임워크별 탐구 필요

## 4단계 — 실험

- [x] LangChain, LangGraph에서 동일한 리서치 agent 작업을 실행한다 (Mock LLM, 2026-05-24)
- [x] 동작, 출력, 내부 구현을 비교한다 (메시지 흐름, LOC, 초기화 시간)
- [x] 실험 보고서에 문서화한다 (`experiments/2026-05-24 3개 프레임워크 리서치 에이전트 비교 실험 결과.md`)
- [ ] Deep Agents 실험 — 패키지 설치 방법 확인 후 실행

## 5단계 — PR 기여 준비

이 단계의 목표는 업스트림 저장소에 직접 기여할 수 있는 실력을 키우는 것이다.
재현 예제 작성, 근본 원인 분석, 테스트 읽기를 통해 스스로 패치를 만들 수 있는 상태를 목표로 한다.

**학습 달성:**
- [x] 이슈를 읽고 재현 예제를 스스로 작성했다 (`reproductions/langgraph_checkpoint_pending_writes/`)
- [x] 소스 코드를 추적해 deprecated API 원인을 직접 확인했다 (`_internal/_constants.py`)
- [x] 기존 테스트 파일을 읽고 동작 기준을 이해했다 (`test_pregel.py::test_pending_writes_resume`)
- [x] PR 후보 페이지에 근본 원인과 패치 제안을 직접 정리했다

**다음 학습 목표 (스스로 수행):**
- [ ] LangGraph / LangChain 이슈 중 `help wanted` 이슈를 읽고 근본 원인을 스스로 분석한다
- [ ] 테스트를 읽고 어떤 동작을 검증하는지 설명할 수 있다
- [ ] 기존 테스트 패턴을 참고해 새 테스트를 스스로 작성한다
- [ ] 작고 검토 가능한 패치를 직접 작성하고 PR을 제출한다

## 다음 학습 영역

- Guardrails: LangGraph / Deep Agents 구체적 구현 탐구
- Handoffs: LangGraph `Command(goto=)` + Deep Agents subagent 비교
- Tracing: LangSmith 통합 방식 탐구
- Reasoning/Planning: `create_react_agent` 내부 구조, Deep Agents planning 노드 존재 여부
- Production Store 구현체 (Redis/PostgreSQL) 패키지 확인
- SubagentTransformer 소스 탐구 (저장소 접근 필요)
