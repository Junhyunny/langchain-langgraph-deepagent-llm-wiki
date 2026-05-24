---
type: concept
framework:
  - LangGraph
status: partial
confidence: medium
last_reviewed: 2026-05-24
sources:
  - langgraph-venv-loop-py-2026-05-24
  - langgraph-source-checkpoint-runtime-2026-05-20
  - langgraph-tests-delta-migration-2026-05-24
---

# DeltaChannel

## Summary

`DeltaChannel`은 LangGraph v4 checkpoint 형식에서 도입된 채널 유형으로, 매 super-step마다 전체 상태 스냅샷을 저장하는 대신 **증분(delta) writes만 저장**한다. 긴 대화에서 대형 state 채널의 저장 비용을 줄이는 데 사용된다.

## Why It Matters

일반 LangGraph 채널은 super-step마다 `channel_values`에 전체 값을 저장한다. messages 목록처럼 데이터가 계속 누적되는 채널에서는 checkpoint 크기가 선형 증가한다. `DeltaChannel`은 delta만 저장하고 필요 시 ancestor walk + replay로 현재 값을 재구성하므로 저장 공간이 절약된다. 단, 복구 경로가 복잡해진다.

## Key Concepts

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]

## Details

### 일반 채널 vs DeltaChannel 저장 전략

| | 일반 채널 | DeltaChannel |
|---|---|---|
| 저장 단위 | 매 super-step: `channel_values`에 전체 값 | 매 write: delta만 별도 저장 |
| hydrate 경로 | `spec.from_checkpoint(stored)` 직접 호출 | ancestor walk + `replay_writes()` |
| snapshot | 항상 전체 스냅샷 | `snapshot_frequency` 또는 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` 조건 시 `_DeltaSnapshot` 생성 |
| 저장 비용 | O(n × size) | O(delta 크기) — snapshot 없을 때 |

### 스냅샷 트리거 조건 (`delta_channels_to_snapshot()`)

**검증됨** (`_checkpoint.py` 직접 확인):

```python
# 두 조건 중 하나를 충족하면 이번 step에서 전체 스냅샷 생성
updates >= snapshot_frequency  # 누적 update 횟수가 threshold 도달
supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT  # 마지막 snapshot 이후 super-step 수 초과
```

- `counters_since_delta_snapshot`: `checkpoint_metadata`에 `(updates, supersteps)` 쌍으로 관리
- `_put_checkpoint()` 호출마다 카운터 갱신 후 snapshot 대상 결정
- snapshot 생성 시: `create_checkpoint()`에서 `_DeltaSnapshot(ch.get())` blob 저장

### channels_from_checkpoint() 에서의 DeltaChannel 처리

**검증됨** (`_checkpoint.py` 직접 확인):

1. `checkpoint["channel_values"]`에 스냅샷이 있으면 `spec.from_checkpoint(stored)` 직접 호출 (일반 경로와 동일)
2. 스냅샷이 없으면:
   - `saver.get_delta_channel_history(config, channel_name)` 호출 — ancestor checkpoint들에서 delta write 이력 수집
   - `replay_writes(writes)` 호출 — 수집한 delta writes를 순서대로 재생하여 현재 값 재구성
   - **의미:** 스냅샷 없이 hydrate하려면 checkpointer가 `get_delta_channel_history()`를 구현해야 함

### DeltaChannel durability invariant (`_loop.py` 확인)

**검증됨** (`_loop.py` 직접 확인):

DeltaChannel write → checkpoint 저장 순서 보장이 중요하다.

```python
# _checkpointer_put_after_previous (SyncPregelLoop, line 1498)
1. _delta_write_futs 전체 드레인 (모든 DeltaChannel put_writes future 완료 대기)
2. 이전 checkpoint future 완료 대기
3. checkpointer.put() 호출
```

**이유:** DeltaChannel은 ancestor walk 방식으로 복구하므로, checkpoint 저장 전에 해당 step의 delta writes가 먼저 저장되어 있어야 한다. 순서가 역전되면 ancestor walk 시 최신 delta가 누락될 수 있다.

### durability="exit" 에서의 DeltaChannel 동작

**검증됨** (`_loop.py` 직접 확인):

- `put_writes()`: `checkpointer_put_writes` 호출 건너뜀 (delta writes 즉시 저장 안 함)
- `after_tick()`: DeltaChannel writes를 `_exit_delta_writes` 리스트에 누적
- 루프 종료 시 `_suppress_interrupt()` → `_put_exit_delta_writes()` + `_put_checkpoint()` 일괄 처리
  - `_put_exit_delta_writes()`: synthetic step-prefixed task_id로 누적된 delta writes 저장
  - 부모 checkpoint가 없으면 lazy stub 생성 후 저장

## Source Code References

- Repo: `https://github.com/langchain-ai/langgraph`
- Commit: UNKNOWN (`.venv` 설치본 기준)
- Files:
  - `.venv/lib/python3.14/site-packages/langgraph/pregel/_checkpoint.py`
    - `create_checkpoint()`: DeltaChannel + `_DeltaSnapshot` 저장 경로
    - `channels_from_checkpoint()`: DeltaChannel ancestor walk 경로
    - `delta_channels_to_snapshot()`: 스냅샷 대상 결정
  - `.venv/lib/python3.14/site-packages/langgraph/pregel/_loop.py`
    - `put_writes()`: `_delta_write_futs` 추가 (line ~407)
    - `after_tick()`: `_exit_delta_writes` 누적 (exit mode)
    - `_put_checkpoint()`: `counters_since_delta_snapshot` 갱신 (line ~1055)
    - `_checkpointer_put_after_previous`: `_delta_write_futs` 드레인 (line ~1498, sync)

## Tests

**읽은 테스트: `test_delta_channel_migration.py` (2026-05-24)**

GitHub: `https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/tests/test_delta_channel_migration.py`

이 파일은 `BinaryOperatorAggregate → DeltaChannel` migration 경로를 집중적으로 검증한다.

### Migration 메커니즘 (docstring에서 확인)

1. `get_delta_channel_history(config, channels)`: 부모 체인을 walk
2. ancestor의 `channel_values[channel]`에 실제 값 발견 → `DeltaChannelHistory`의 `seed` 필드에 저장
3. root까지 walk해도 값 없으면 `seed` 필드 생략 (TypedDict absence = "start empty")
4. `DeltaChannel.from_checkpoint(seed)`: seed를 base 값으로 사용
5. `replay_writes(writes)`: on-path delta들을 순서대로 fold

### 검증된 DeltaChannel API

```python
# 생성자: reducer 함수를 받음
DeltaChannel(_list_concat)               # list 누적
DeltaChannel(_messages_delta_reducer)    # LangChain messages 전용

# 채널 연결 방식 (Annotated)
class State(TypedDict):
    items: Annotated[list, DeltaChannel(_list_concat)]
    messages: Annotated[list, DeltaChannel(_messages_delta_reducer)]

# 내부 호출 흐름
DeltaChannel.from_checkpoint(seed)  # hydrate from stored value
replay_writes(writes)               # fold deltas onto current state
```

### 9개 테스트 시나리오 요약

| # | 테스트명 | 검증 내용 |
|---|---------|----------|
| 1 | `test_basic_migration_preserves_pre_migration_state` (sync+async) | BinopAggregate → DeltaChannel 동일 checkpointer에서 settled boundary 값 보존 |
| 2 | `test_time_travel_into_pre_migration_checkpoint` | migration 후 `get_state(pre_migration_cfg)` time travel 정상 동작 |
| 3 | `test_continuing_migrated_thread_folds_deltas_on_seed` | `invoke(None, cfg)` — pre-migration 조상에서 resume 시 seed+deltas 올바르게 fold |
| 4 | `test_base_saver_fallback_matches_optimized_override` | `BaseCheckpointSaver.get_delta_channel_history` fallback = optimized `InMemorySaver` override (동일 결과) |
| 5 | `test_delta_and_migrated_threads_do_not_cross_contaminate` | `get_delta_channel_history`는 thread 단위로 scope — 다른 thread 데이터 leak 없음 |
| 6 | `test_tip_of_pre_migration_hydrates_directly` | 최신 checkpoint에 real value 있으면 ancestor walk 없이 직접 사용 |
| 7 | `test_update_state_after_migration_uses_written_value` | `update_state()` 후 새 blob 직접 사용 (ancestor walk skip) |
| 8 | `test_fork_from_update_state_checkpoint` | `update_state` checkpoint에서 fork → 해당 blob이 base, 새 delta는 fold됨 |
| 9 | `test_add_messages_to_delta_migration_preserves_message_history` (sync+async) | **주요 real-world 사례**: `add_messages` → `DeltaChannel(_messages_delta_reducer)` message ID 보존 |

### 핵심 불변 조건 (테스트에서 확인됨)

- **settled boundary**: `state.next == ('__start__',)` — super-step 경계 (invoke 간 stable point)
- **ancestor walk scope**: `thread_id` 단위로 격리. 다른 thread의 checkpoint 조상 walk 없음
- **직접 사용 우선**: checkpoint에 real value가 있으면 ancestor walk보다 직접 사용이 우선 (update_state, tip 포함)
- **migration 투명성**: `BinaryOperatorAggregate` → `DeltaChannel` 교체 시 기존 state 보존 (settled boundaries 기준)

Source: `langgraph-tests-delta-migration-2026-05-24`

## Related Pages

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]

## Open Questions

- `DeltaChannel` 객체 자체의 구현(`channel/delta.py` 또는 유사)은 어디에 있는가? `replay_writes()` 내부는?
  → `langgraph/channels/delta.py`에 있는 것으로 확인됨 (import: `from langgraph.channels.delta import DeltaChannel`). 내부 구현은 **Needs Source** — `.venv` 직접 읽기 필요
- `snapshot_frequency`의 기본값은 얼마인가?
  → **Needs Source** — `delta_channels_to_snapshot()`에서 파라미터로 전달됨
- `get_delta_channel_history()`가 `InMemorySaver`에 어떻게 구현되어 있는가?
  → 테스트 4에서 `InMemorySaver`에 optimized override가 있음을 확인. `BaseCheckpointSaver`에도 fallback 구현 있음. 내부 코드는 **Needs Source**
- `test_delta_channel_exit_mode.py` 읽기 — exit mode durability invariant 검증

## Sources

- `langgraph-venv-loop-py-2026-05-24`
- `langgraph-source-checkpoint-runtime-2026-05-20`
- `langgraph-tests-pregel-2026-05-24`
- `langgraph-tests-delta-migration-2026-05-24`
