---
type: experiment
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-23
sources:
  - langchain-docs-products-2026-05-23
  - langgraph-tests-checkpoint-recovery-2026-05-23
  - deepagents-evals-model-groups-harbor-bfcl-2026-05-23
---

# 2026-05-23 same task 3 frameworks

## 목표
동일한 리서치 태스크를 [[LangChain]], [[LangGraph]], [[Deep Agents]]로 각각 실행해 구현/운영 차이를 비교한다.

## 설정
- 공통 태스크: "문서 3개를 읽고 요약 + 액션 아이템 3개 도출"
- 공통 비교 항목: 단계 수, 도구 호출 수, 실패 시 재개성, 로그 해석 난이도

## 코드 링크
- TBD

## 기대 동작
- LangChain: 빠른 구현, 낮은 제어 복잡도
- LangGraph: 명시적 상태/체크포인트 기반 재개
- Deep Agents: 하네스 기본기능으로 빠른 실전 셋업

## 실제 동작
- 아직 실행 로그 없음

## 관찰 내용
- 실험 전 회귀 기준으로 LangGraph checkpoint resume 테스트 경로를 확보함 (`test_pregel.py`).
- Deep Agents eval 문서에서 Harbor/BFCL 범위를 확인했지만 judge 모델 결정 경로는 추가 소스가 필요함.

## 핵심 정리
- 실험 실행 전 단계에서 "회귀 기준 테스트 경로"와 "eval 카탈로그 경로"를 먼저 고정하는 접근이 유효하다.

## Related Pages
- [[LangChain vs LangGraph vs Deep Agents]]
- [[Checkpointing]]
- [[Evaluation]]

## Sources
- `langchain-docs-products-2026-05-23`
- `langgraph-tests-checkpoint-recovery-2026-05-23`
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
