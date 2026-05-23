---
type: decision
framework:
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-docs-products-2026-05-23
  - deepagents-docs-overview-2026-05-18
  - deepagents-source-graph-2026-05-19
---

# When to use LangGraph vs Deep Agents for orchestration

## 결정 사항
초기 구현은 Deep Agents를 우선 사용하고, 체크포인트/재개/분기 제어를 세밀히 다뤄야 하는 구간은 LangGraph 직접 구현으로 내린다.

## 컨텍스트
이 저장소의 목표는 학습→실험→업스트림 기여 루프를 빠르게 돌리는 것이다.

## 검토한 옵션
- 옵션 A: LangGraph 직접 구현만 사용
- 옵션 B: Deep Agents 기본, 필요 시 LangGraph 하향

## 트레이드오프
- 옵션 A 장점: 제어력/내부 가시성
- 옵션 A 단점: 실험 속도 저하
- 옵션 B 장점: 빠른 실험 및 하네스 재사용
- 옵션 B 단점: 내부 동작 추적이 더 필요함

## 이유
공식 분류에서 Deep Agents는 Harness, LangGraph는 Runtime 역할로 구분된다. 학습 초기에는 Harness로 빠르게 실험하고, 회귀/제어가 필요한 지점에서 Runtime으로 내려가는 접근이 현재 목표와 가장 맞다.

## 결과
- 실험 페이지와 실패 사례 페이지를 먼저 구축해 의사결정을 검증 가능한 형태로 유지한다.

## 재검토 기준
- 한 주 동안 실패 사례의 50% 이상이 하네스 추상화에서 원인 파악 지연을 유발하면 LangGraph 직접 구현 비중을 높인다.

## Sources
- `langchain-docs-products-2026-05-23`
- `deepagents-docs-overview-2026-05-18`
- `deepagents-source-graph-2026-05-19`
