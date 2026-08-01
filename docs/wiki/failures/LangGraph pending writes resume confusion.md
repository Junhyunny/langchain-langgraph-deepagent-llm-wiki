---
type: failure
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-07-30
updated_at: 2026-07-30
sources:
  - langgraph-tests-checkpoint-recovery-2026-05-23
  - langgraph-source-checkpoint-internals-2026-05-23
---

# LangGraph pending writes resume confusion

> **재검증 (2026-07-30):** `langgraph==1.2.10`에서 최소 재현의 모든
> assertion이 통과했다. 성공한 sibling의 pending write가 실패한 superstep
> 이후 재개 시 재사용되는 동작은 유지된다.

## 문제
노드 일부가 실패한 실행에서 `invoke(None, config)` 재개 시 어떤 노드가 재실행되고 어떤 값이 누적되는지 직관적으로 이해하기 어렵다.

## 기대 동작
이미 성공한 노드는 재실행 없이 pending writes를 반영하고, 실패 노드만 재시도한다.

## 실제 동작
`test_pending_writes_resume` 기준으로 다음이 확인된다.
- 성공 노드(`one`)는 재개 후 호출 횟수가 증가하지 않음
- 실패 노드(`two`)는 재개 시 재시도됨
- 최종 성공 시 pending write + 신규 write가 함께 반영됨

## 재현
- 기준 테스트: `libs/langgraph/tests/test_pregel.py::test_pending_writes_resume`

## 복구 흐름 (내부 경로)

```
invoke(None, config)
  └─ Pregel._defaults(config)
       └─ SyncPregelLoop 생성
            └─ _first(): checkpointer.get_tuple(config)
                 ├─ CheckpointTuple.pending_writes 로드
                 └─ channels_from_checkpoint(checkpoint, config, specs, store, saver)
                      ├─ 일반 채널: spec.from_checkpoint(channel_values[k])
                      └─ DeltaChannel: saver.get_delta_channel_history() → replay_writes()

  loop tick:
    - 이미 성공한 node의 task write는 pending_writes에서 재사용 (재실행 없음)
    - 에러 기록된 task(_error__)만 재스케줄됨
    - 재시도 성공 시 put_writes() → put() (full checkpoint)
```

## 핵심 구분

| 저장 위치 | 내용 | 저장 시점 |
|----------|------|---------|
| `checkpoint.channel_values` | 최종 state snapshot | super-step 완료 후 |
| `checkpoint_writes` (pending_writes) | task-level write (성공/실패 모두) | task 완료 직후 |
| `__error__` channel in pending_writes | 에러 발생 task 정보 | 에러 발생 즉시 |

## 확인된 원인
- `channels_from_checkpoint`는 채널 복원 중심이며 pending writes 처리의 핵심은 loop/runtime 경로에서 이루어진다.
- checkpoint와 pending writes가 다른 시점에 저장되기 때문에 state snapshot만 보면 실행 맥락을 오해하기 쉽다.
- `durability` 설정에 따라 checkpoint 저장 시점이 달라져 pending writes 개수도 달라진다.

## 관련 개념
- [[Checkpointing]]
- [[StateGraph]]

## 다음 행동
- async 경로(`test_pregel_async.py`)에서 동등한 재개 패턴을 확인한다.
- `_put_exit_delta_writes()` 검증 테스트 위치 확인 (`_loop.py` 탐색 필요)

## 상태
- **검증됨** — sync 경로 전체 확인 (`test_pending_writes_resume` 기준). async 경로는 Open Question으로 분리.

## Open Questions
- async 경로(`test_pregel_async.py`)의 동등한 재개 패턴이 sync 경로와 동일한가? — Needs Verification
- `_put_exit_delta_writes()` 검증 테스트 위치 — `_loop.py` 탐색 필요

## Sources
- `langgraph-tests-checkpoint-recovery-2026-05-23`
- `langgraph-source-checkpoint-internals-2026-05-23`
