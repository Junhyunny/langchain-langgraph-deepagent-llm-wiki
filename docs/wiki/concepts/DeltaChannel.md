---
type: concept
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-24
sources:
  - langgraph-venv-loop-py-2026-05-24
  - langgraph-venv-channels-delta-py-2026-05-24
  - langgraph-source-checkpoint-runtime-2026-05-20
  - langgraph-tests-delta-migration-2026-05-24
  - langgraph-tests-delta-channel-exit-mode-2026-05-24
---

# DeltaChannel

## Summary

`DeltaChannel`은 LangGraph v4 checkpoint 형식에서 도입된 채널 유형으로, 매 super-step마다 전체 상태 스냅샷을 저장하는 대신 **증분(delta) writes만 저장**한다. 긴 대화에서 대형 state 채널의 저장 비용을 줄이는 데 사용된다.

> ⚠️ **Beta**: API와 on-disk 표현이 향후 변경될 수 있다. 현재 thread는 계속 읽을 수 있지만, 주변 계약(`get_delta_channel_history`, `_DeltaSnapshot`, `counters_since_delta_snapshot`)은 아직 stable하지 않다.

## Why It Matters

일반 LangGraph 채널은 super-step마다 `channel_values`에 전체 값을 저장한다. messages 목록처럼 데이터가 계속 누적되는 채널에서는 checkpoint 크기가 선형 증가한다. `DeltaChannel`은 delta만 저장하고 필요 시 ancestor walk + replay로 현재 값을 재구성하므로 저장 공간이 절약된다. 단, 복구 경로가 복잡해진다.

## Key Concepts

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]

## Details

### 생성자 및 사용법

**검증됨** (`channels/delta.py` 직접 확인):

```python
from langgraph.channels.delta import DeltaChannel

# 생성자 시그니처
DeltaChannel(
    reducer: Callable[[Any, Sequence[Any]], Any],
    typ: type | None = None,           # Annotated로 자동 추론
    snapshot_frequency: int = 1000,    # 기본값 1000
)

# 사용 패턴 (TypedDict + Annotated)
class State(TypedDict):
    items: Annotated[list, DeltaChannel(_list_concat)]
    messages: Annotated[list, DeltaChannel(_messages_delta_reducer)]
```

**Reducer 제약 조건 (docstring)**:
- 결정론적이어야 한다
- batching-invariant(결합 법칙 성립)이어야 한다:
  `reducer(reducer(state, xs), ys) == reducer(state, xs + ys)`
- 두 배치를 따로 적용한 결과 = 한 번에 붙여서 적용한 결과

### 일반 채널 vs DeltaChannel 저장 전략

| | 일반 채널 | DeltaChannel |
|---|---|---|
| 저장 단위 | 매 super-step: `channel_values`에 전체 값 | 매 write: delta만 별도 저장 |
| `checkpoint()` 반환값 | 현재 값 | **항상 `MISSING`** |
| hydrate 경로 | `spec.from_checkpoint(stored)` 직접 호출 | ancestor walk + `replay_writes()` |
| snapshot | 항상 전체 스냅샷 | `snapshot_frequency` 또는 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` 조건 시 `_DeltaSnapshot` 생성 |
| 저장 비용 | O(n × size) | O(delta 크기) — snapshot 없을 때 |

**핵심**: `DeltaChannel.checkpoint()`는 **항상 `MISSING`을 반환**한다. `_DeltaSnapshot` 블롭은 `create_checkpoint()`가 직접 `channel_values`에 쓴다.

```python
# channels/delta.py line 195
def checkpoint(self) -> Any:
    return MISSING  # 항상 MISSING — 스냅샷은 _checkpoint.py가 직접 처리
```

### `from_checkpoint(checkpoint)` — 세 가지 분기

**검증됨** (`channels/delta.py` line 118 직접 확인):

```python
def from_checkpoint(self, checkpoint: Any) -> Self:
    if checkpoint is MISSING:
        new.value = self.typ()           # 빈 컨테이너 (ancestor walk 후 replay_writes 예정)
    elif isinstance(checkpoint, _DeltaSnapshot):
        new.value = checkpoint.value     # 스냅샷에서 직접 복원
    else:
        new.value = checkpoint           # 구형 BinaryOperatorAggregate blob 직접 사용 (migration)
```

| 입력 | 의미 | 처리 |
|------|------|------|
| `MISSING` | 스냅샷 없음 → ancestor walk 필요 | 빈 컨테이너 초기화 후 `replay_writes()` |
| `_DeltaSnapshot(v)` | 전체 스냅샷 존재 | 값 직접 복원 |
| plain value | 구형 `BinaryOperatorAggregate` blob (migration 경로) | 값 직접 사용 |

### `replay_writes(writes)` — delta 재생

**검증됨** (`channels/delta.py` line 139 직접 확인):

```python
def replay_writes(self, writes: Sequence[PendingWrite]) -> None:
    values = [v for _, _, v in writes]
    if not values:
        return
    base = self.value
    start = 0
    for i, v in enumerate(values):
        is_ow, ow_value = _get_overwrite(v)
        if is_ow:
            base = _copy.copy(ow_value) if ow_value is not None else self.typ()
            start = i + 1
    remaining = values[start:]
    self.value = self.reducer(base, remaining) if remaining else base
```

**핵심 동작**:
- `Overwrite` 값이 있으면: **마지막 Overwrite 이후** 의 writes만 reducer에 적용
- 마지막 Overwrite가 reset point — 이전 값을 버리고 새 base 설정
- 정상 writes: `self.reducer(base, remaining)` 한 번에 일괄 적용 (batching-invariant 활용)

### `update(values)` — live 실행 시 (per super-step)

**검증됨** (`channels/delta.py` line 159 직접 확인):

- 한 super-step에서 `Overwrite`는 **최대 1개** (위반 시 `InvalidUpdateError`)
- Overwrite 있으면: `base = overwrite_value`, 나머지 values를 reducer에 적용
- 정상: `self.reducer(base, list(values))`

### 스냅샷 트리거 조건 (`delta_channels_to_snapshot()`)

**검증됨** (`_checkpoint.py` 직접 확인):

```python
# 두 조건 중 하나를 충족하면 이번 step에서 전체 스냅샷 생성
updates >= snapshot_frequency              # 기본값 1000
supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT  # 기본값 5000
```

- `snapshot_frequency` 기본값: **1000** (update/write 횟수 기준)
- `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` 기본값: **5000** (writes가 없는 채널도 anchor)
- `counters_since_delta_snapshot`: `checkpoint_metadata`에 `(updates, supersteps)` 쌍으로 관리
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

**추가 확인** (`test_exit_count_parity_sync_vs_exit`): sync와 exit durability는 동일한 `counters_since_delta_snapshot`를 생성한다. durability mode는 저장 타이밍만 다르고 카운터 논리는 동일하다.

### durability="exit" 에서의 DeltaChannel 동작

**검증됨** (`_loop.py` 직접 확인 + `test_delta_channel_exit_mode.py` 전체 읽음):

- `put_writes()`: `checkpointer_put_writes` 호출 건너뜀 (delta writes 즉시 저장 안 함)
- `after_tick()`: DeltaChannel writes를 `_exit_delta_writes` 리스트에 누적
- 루프 종료 시 `_suppress_interrupt()` → `_put_exit_delta_writes()` + `_put_checkpoint()` 일괄 처리
  - `_put_exit_delta_writes()`: synthetic step-prefixed task_id로 누적된 delta writes 저장
  - 부모 checkpoint가 없으면 **lazy stub** (step=-2) 생성 후 저장

**lazy stub** 생성 조건 (테스트에서 확인):

| 조건 | stub 생성 여부 |
|------|--------------|
| DeltaChannel write 없음 | ❌ 생성 안 함 |
| `snapshot_frequency=1` (매 run 스냅샷) | ❌ 생성 안 함 — `_DeltaSnapshot`이 직접 저장됨 |
| 첫 run, writes 있음, 스냅샷 threshold 미달 | ✅ **생성** (step=-2) |
| 두 번째 이후 run | ❌ 생성 안 함 — 첫 run의 final_checkpoint에 앵커 |

**스냅샷 카운터 동작 (exit mode)**:
- 각 invoke에서 `messages` 채널: **2 updates** 발생 (input write + respond node write)
- `snapshot_frequency=3`이면 2번째 invoke 후 누적=4 → 스냅샷 발동 → counter 리셋=0
- 스냅샷 발동 후: `channel_values["messages"] = _DeltaSnapshot(...)`, counter = 0
- 스냅샷 없을 때: `"messages"` 키가 `channel_values`에 없음 (버전만 있음)

## Source Code References

- Repo: `https://github.com/langchain-ai/langgraph`
- Commit: UNKNOWN (`.venv` 설치본 기준)
- Files:
  - `.venv/lib/python3.14/site-packages/langgraph/channels/delta.py` ✅ 전체 읽음 (2026-05-24)
    - `DeltaChannel.__init__`: reducer, typ, snapshot_frequency (기본값 1000)
    - `from_checkpoint()`: MISSING / _DeltaSnapshot / plain value 3분기
    - `replay_writes()`: Overwrite handling, 일괄 reducer 적용
    - `update()`: live 실행 시 Overwrite 1개 제한, reducer 적용
    - `checkpoint()`: 항상 MISSING 반환 (스냅샷은 `_checkpoint.py`가 처리)
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

---

**읽은 테스트: `test_delta_channel_exit_mode.py` (2026-05-24)**

GitHub: `https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/tests/test_delta_channel_exit_mode.py`

docstring: "Validates that `durability="exit"` correctly persists delta-channel writes using count-based snapshot decisions (rather than force-snapshotting every channel), lazy stub creation when no parent exists, and proper read-path reconstruction via ancestor walks."

### Write-path 테스트 (8a)

| # | 테스트명 | 검증 내용 |
|---|---------|----------|
| 1 | `test_exit_first_run_no_delta_writes` | DeltaChannel에 writes 없으면 stub 생성 없음, checkpoint 1개 |
| 2 | `test_exit_first_run_all_snapshot` (freq=1) | 모든 채널 스냅샷 → stub 없음, `_DeltaSnapshot` 직접 저장 |
| 3 | `test_exit_first_run_sub_freq_with_writes` (freq=1000) | writes 있고 threshold 미달 → **stub 1개** 생성, `channel_values`에 `"messages"` 키 없음 |
| 4 | `test_exit_resumed_run_sub_freq` | 2번 연속 run → stub 1개만 유지 (2번째 run은 1번째 checkpoint에 앵커) |
| 5 | `test_exit_count_parity_sync_vs_exit` | sync/exit durability 동일한 `counters_since_delta_snapshot` 생성 (updates=2, supersteps≥2) |
| 6 | `test_exit_snapshot_fires_at_frequency` (freq=3) | 2번째 invoke 후 누적 updates=4≥3 → 스냅샷 발동, counter=0으로 리셋 |
| 7 | `test_exit_mixed_snapshot_and_non_snapshot` | 두 채널(freq=1, freq=1000) 혼합 → fast만 스냅샷, slow는 ancestor walk |

### Read-path 테스트 (8b)

| # | 테스트명 | 검증 내용 |
|---|---------|----------|
| 8 | `test_exit_multi_run_replay_chain` | K=4 run, 매 run 후 `get_state`가 전체 순서 보존 |
| 9 | `test_exit_metadata_round_trip` (freq=5) | counters 단조 증가, freq 초과 시 리셋 |
| 10 | `test_exit_mixed_durability_round_trip` | sync/exit 교대 사용 → 상태 단조 누적 |
| 11 | `test_exit_snapshot_then_tail_deltas` | run1(freq=1) 스냅샷 → run2(freq=1000) tail deltas → 합산 올바름 |

### 핵심 발견 (exit mode)

- **per-invoke update count**: 각 invoke마다 `messages` 채널에 **2 updates** — input write(1) + respond node write(1)
- **lazy stub**: step=-2, 첫 run에서만 생성, 이후 run은 첫 run의 final_checkpoint에 앵커
- **스냅샷 없을 때**: `channel_values`에 키 없음, `channel_versions`에만 버전 기록
- **sync/exit 카운터 동등성**: durability mode는 저장 타이밍만 다를 뿐, 카운터 로직은 완전히 동일

Source: `langgraph-tests-delta-channel-exit-mode-2026-05-24`

## Related Pages

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]

## Open Questions

- `DeltaChannel` 자체 구현: ✅ 해소 (2026-05-24, `channels/delta.py` 전체 읽음)
- `snapshot_frequency`의 기본값: ✅ 해소 — **1000** (update/write 횟수 기준). `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` = **5000**
- `test_delta_channel_exit_mode.py` 읽기: ✅ 해소 (2026-05-24) — 11개 시나리오, lazy stub(step=-2), per-invoke 2 updates, sync/exit 카운터 동등성 확인
- `get_delta_channel_history()`의 `InMemorySaver` 최적화 override vs `BaseCheckpointSaver` fallback 구현 상세
  → `test_delta_channel_migration.py` test 4에서 두 경로 동일 결과 확인됨. 내부 코드는 **Needs Source** — `memory/__init__.py` 읽기 필요

## Sources

- `langgraph-venv-loop-py-2026-05-24`
- `langgraph-venv-channels-delta-py-2026-05-24`
- `langgraph-source-checkpoint-runtime-2026-05-20`
- `langgraph-tests-delta-migration-2026-05-24`
- `langgraph-tests-delta-channel-exit-mode-2026-05-24`
