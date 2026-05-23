---
type: source_summary
source_id: langgraph-tests-checkpoint-recovery-2026-05-23
title: "LangGraph — test_pregel checkpoint recovery tests"
framework: LangGraph
retrieved_at: "2026-05-23"
status: verified
confidence: high
---

# Source Summary: LangGraph test_pregel checkpoint recovery

## Source Info
- **Source ID:** `langgraph-tests-checkpoint-recovery-2026-05-23`
- **Type:** source_code (tests)
- **URL:** `libs/langgraph/tests/test_pregel.py`
- **Retrieved At:** 2026-05-23

## Key Facts
- `test_pending_writes_resume`는 실패 노드와 성공 노드가 섞인 상태에서 pending writes가 저장되고, `invoke(None, thread_config)` 재개 시 이미 성공한 노드는 재실행하지 않음을 검증한다.
- 같은 테스트에서 `durability`가 `exit`일 때와 아닐 때 checkpoint 개수/저장되는 pending writes가 달라짐을 명시적으로 검증한다.
- `test_run_from_checkpoint_id_retains_previous_writes`는 특정 `checkpoint_id`로 재실행(`invoke(None, second_run_config)`)했을 때 기존 writes 문맥이 유지되는 포크 실행을 검증한다.
- `test_invoke_checkpoint_two`는 노드 에러 발생 시 checkpoint가 롤백되고, 에러가 `pending_writes`(`__error__`)로 기록되는 경로를 검증한다.

## Interpretation
- LangGraph의 canonical 회귀 루트로 `libs/langgraph/tests/test_pregel.py`가 우선순위가 높다.
- 특히 pending writes resume 회귀는 `test_pending_writes_resume`가 핵심 기준 테스트다.

## Open Questions
- async 경로의 동등 회귀 기준으로 `test_pregel_async.py`에서 어떤 테스트를 같이 묶어야 하는가?
- delta-channel migration과 pending writes 간 결합 회귀는 어느 테스트 조합이 가장 작은가?

## Related Wiki Pages
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## Sources
- `langgraph-tests-checkpoint-recovery-2026-05-23`
