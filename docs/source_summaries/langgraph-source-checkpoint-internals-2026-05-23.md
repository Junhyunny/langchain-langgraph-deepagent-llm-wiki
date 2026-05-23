---
type: source_summary
source_id: langgraph-source-checkpoint-internals-2026-05-23
title: "LangGraph — Pregel _checkpoint.py (체크포인트 유틸리티)"
framework: LangGraph
retrieved_at: "2026-05-23"
status: verified
confidence: high
---

# Source Summary: LangGraph — _checkpoint.py

## Source Info
- **Source ID:** `langgraph-source-checkpoint-internals-2026-05-23`
- **Type:** source_code
- **URL:** `libs/langgraph/langgraph/pregel/_checkpoint.py`
- **Retrieved At:** 2026-05-23
- **Version:** main branch
- **Lines:** ~280줄, 함수 8개

---

## Key Facts

### LATEST_VERSION = 4

Checkpoint 스키마 버전 상수. `Checkpoint["v"]` 필드에 저장됨.

---

### empty_checkpoint()

완전히 빈 Checkpoint를 생성한다.

```python
Checkpoint(
    v=4,
    id=str(uuid6(clock_seq=-2)),  # clock_seq=-2는 "empty" 구분자
    ts=datetime.now(timezone.utc).isoformat(),
    channel_values={},
    channel_versions={},
    versions_seen={},
)
```

- `uuid6`는 LangGraph 내부 UUID 생성기
- `versions_seen`은 빈 dict — 아직 어떤 node도 어떤 채널 버전도 본 적 없음

---

### copy_checkpoint(checkpoint)

얕은 복사가 아닌 **부분 깊은 복사**:

- `channel_values`: `.copy()` — 1 depth
- `channel_versions`: `.copy()` — 1 depth
- `versions_seen`: `{k: v.copy() ...}` — 2 depth (각 node의 버전 dict까지 복사)
- `updated_channels`: 그대로 참조 (None이거나 sorted list)

---

### DeltaChannel 개념

`DeltaChannel`은 메시지 히스토리처럼 **누적되는 채널**이다. `Deep Agents`의 `_DeepAgentState.messages`가 이 타입으로 선언된다.

**핵심 설계**: 모든 super-step마다 전체 값을 직렬화하지 않고, 변경분(writes)만 저장한다. 주기적으로 `_DeltaSnapshot`(전체 값)을 저장해 재구성 비용을 제한한다.

| 저장 방식 | 조건 |
|---|---|
| `_DeltaSnapshot(ch.get())` | `k in channels_to_snapshot` (스냅샷 타이밍) |
| `ch.checkpoint()` (전체 값) | 일반 채널 |
| `channel_values`에 없음 | `DeltaChannel`이고 스냅샷 타이밍이 아님 |

---

### delta_channels_to_snapshot(channels, counters)

어떤 DeltaChannel이 이번 super-step에 snapshot을 찍어야 하는지 판단하는 **순수 함수**.

스냅샷 조건 (둘 중 하나 충족 시):
1. `updates >= ch.snapshot_frequency` — 누적 업데이트 수가 snapshot_frequency 도달
2. `supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` — 마지막 스냅샷 이후 super-step 수가 상수 도달

`counters_since_delta_snapshot`의 형식: `{channel_name: (updates_count, supersteps_count)}`

---

### create_checkpoint(checkpoint, channels, step, ...)

이전 checkpoint와 현재 live channel 상태에서 **새 Checkpoint를 빌드**한다.

**파라미터:**

| 파라미터 | 설명 |
|---|---|
| `checkpoint` | 이전 checkpoint (기준점) |
| `channels` | 현재 live channel dict. `None`이면 이전 값 그대로 복사 |
| `step` | 현재 super-step 번호 (UUID 생성에 사용) |
| `id` | 명시적 checkpoint ID (없으면 `uuid6(clock_seq=step)` 자동 생성) |
| `updated_channels` | 이번 super-step에서 실제 변경된 채널 이름 집합 |
| `get_next_version` | 버전 increment 함수 |
| `channels_to_snapshot` | 이번 super-step에 snapshot 찍을 DeltaChannel 이름 집합 |

**로직 요약:**

```
channels is None → 이전 checkpoint 값 그대로 사용
channels is not None → 각 채널 순회:
    k in channels_to_snapshot (DeltaChannel, 스냅샷 타이밍):
        (exit 모드 보정) updated_channels에 없으면 channel_versions 수동 bump
        values[k] = _DeltaSnapshot(ch.get())   ← 전체 스냅샷
    else:
        v = ch.checkpoint()
        if v is not MISSING:
            values[k] = v                        ← 일반 직렬화 값
        (DeltaChannel이고 스냅샷 타이밍이 아니면 values에 포함 안 됨)
```

**exit 모드 버그 수정 주석**: exit 모드에서는 마지막 super-step에 채널 쓰기가 없으면 channel_versions가 bump되지 않아 스냅샷 blob이 저장에서 누락될 수 있다. 이를 방지하기 위해 `get_next_version`으로 수동 bump.

---

### _needs_replay(spec, stored) → bool

```python
if not isinstance(spec, DeltaChannel):
    return False
return stored is MISSING  # channel_values에 없으면 True
```

- 일반 채널: 항상 `False`
- `DeltaChannel`이고 `channel_values`에 없으면 `True` → ancestor walk 필요

---

### channels_from_checkpoint(specs, checkpoint, *, saver, config)

checkpoint에서 **채널을 복원**한다.

**일반 채널**: `spec.from_checkpoint(checkpoint["channel_values"][k])` 로 직접 복원

**DeltaChannel (ancestor walk 필요):**
1. `_needs_replay(spec, stored)` 로 ancestor walk 대상 식별
2. `saver.get_delta_channel_history(config, channels=delta_channels)` — **배치 단일 호출**
3. history에서 `seed` (가장 최근 `_DeltaSnapshot` 또는 pre-migration 값) 복원
4. `replay_ch.replay_writes(history["writes"])` — seed 이후의 write 목록 순서대로 재적용

```
saver 또는 config가 None이면 ancestor walk 건너뜀
  → DeltaChannel이 비어있는 채널로 복원됨 (테스트/디버그 시나리오)
```

**async 버전** (`achannels_from_checkpoint`): 동일 로직, `await saver.aget_delta_channel_history(...)` 사용.

---

## Interpretation

### DeltaChannel의 저장 전략

```
일반 super-step:
    channel_values에 DeltaChannel 미포함 → writes만 checkpoint_writes에 저장

스냅샷 타이밍 (snapshot_frequency 또는 MAX_SUPERSTEPS 도달):
    channel_values[k] = _DeltaSnapshot(전체값) 저장
    → 이후 ancestor walk의 seed가 됨
```

### 재구성 비용 상한

`DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` 상수가 존재하므로, 스냅샷 없이 누적되는 writes의 최대 super-step 수가 bounded됨. `snapshot_frequency`와 함께 이중 안전망.

### _put_exit_delta_writes

이 파일에는 없음. exit durability 처리는 `_loop.py` 또는 별도 파일에 위치하는 것으로 추정됨.

### pending writes recovery

`channels_from_checkpoint`는 **pending writes를 직접 처리하지 않는다**. pending writes는 `checkpoint_writes` (saver에 저장된 태스크 레벨 쓰기 목록)이며, `_loop.py`의 `SyncPregelLoop._first()`에서 `checkpointer.put_writes()`와 함께 처리됨. `_checkpoint.py`는 채널 상태 복원만 담당.

---

## Open Questions (이 소스로 해소)

- ✅ `create_checkpoint`와 `channels_from_checkpoint`의 구현 확인
- ✅ `DeltaChannel` reconstruction: seed → replay_writes 패턴 확인
- ✅ snapshot 조건: `snapshot_frequency` 또는 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`
- ✅ exit 모드 channel_versions bump 이유: 쓰기 없는 채널의 스냅샷 blob 누락 방지
- ⚠️ `_put_exit_delta_writes`: 이 파일에 없음, `_loop.py` 탐색 필요
- ⚠️ `saver.get_delta_channel_history` 구현: `BaseCheckpointSaver`에 이 메서드가 추가됐는지 확인 필요

## Related Wiki Pages

- [[Checkpointing]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]

## Sources

- `langgraph-source-checkpoint-internals-2026-05-23`
