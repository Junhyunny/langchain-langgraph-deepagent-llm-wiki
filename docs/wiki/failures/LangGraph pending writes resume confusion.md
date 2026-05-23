---
type: failure
framework:
  - LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langgraph-tests-checkpoint-recovery-2026-05-23
  - langgraph-source-checkpoint-internals-2026-05-23
---

# LangGraph pending writes resume confusion

## 문제
노드 일부가 실패한 실행에서 `invoke(None, config)` 재개 시 어떤 노드가 재실행되고 어떤 값이 누적되는지 직관적으로 이해하기 어렵다.

## 기대 동작
이미 성공한 노드는 재실행 없이 pending writes를 반영하고, 실패 노드만 재시도한다.

## 실제 동작
`test_pending_writes_resume` 기준으로 다음이 확인된다.
- 성공 노드(one)는 재개 후 호출 횟수가 증가하지 않음
- 실패 노드(two)는 재개 시 재시도됨
- 최종 성공 시 pending write + 신규 write가 함께 반영됨

## 재현
- 기준 테스트: `libs/langgraph/tests/test_pregel.py::test_pending_writes_resume`

## 의심되는 원인
- checkpoint와 pending writes가 다른 시점에 저장되기 때문에 state snapshot만 보면 실행 맥락을 오해하기 쉽다.

## 확인된 원인
- `channels_from_checkpoint`는 채널 복원 중심이며 pending writes 처리의 핵심은 loop/runtime 경로에서 이루어진다.

## 관련 개념
- [[Checkpointing]]
- [[StateGraph]]

## 다음 행동
- async 경로(`test_pregel_async.py`)에서 동등한 재개 패턴을 확인한다.

## 상태
- 부분 검증됨

## Sources
- `langgraph-tests-checkpoint-recovery-2026-05-23`
- `langgraph-source-checkpoint-internals-2026-05-23`
