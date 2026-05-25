---
type: tests
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-test-pregel-raw-2026-05-25
---

# test_pregel.py — 체크포인팅 & 에러 복구 테스트 맵

`test_pregel.py`에서 직접 읽은 체크포인트/에러 복구 관련 테스트들의 분석이다.

---

## 읽은 테스트 목록

| 테스트 이름 | 줄 번호 | 검증하는 동작 |
|------------|---------|--------------|
| `test_pending_writes_resume` | 876 | 병렬 노드 에러 → pending_writes 혼재 → resume 동작 |
| `test_checkpoint_metadata` | 3779 | checkpoint 메타데이터 구조 및 config 값 검증 |
| `test_checkpoint_recovery` | 5386 | RuntimeError 후 resume → 에러 노드만 재시도 |

---

## test_pending_writes_resume (line 876)

### 설정

```python
# 두 노드가 병렬 실행; 하나는 성공, 하나는 에러
builder = StateGraph(Annotated[list, operator.add])
builder.add_node("one", lambda s: ["one"])        # 성공
builder.add_node("two", lambda s: (_ for _ in ()).throw(RuntimeError("error")))  # 에러
builder.add_edge(START, "one")
builder.add_edge(START, "two")
builder.add_edge("one", END)
builder.add_edge("two", END)
graph = builder.compile(checkpointer=MemorySaver())
```

### 테스트 흐름

```
invoke(["input"], thread_id="1")  → RuntimeError 발생
  - pending_writes 상태: {one: ["one"]  ✅, two: RuntimeError ❌}

invoke(None, thread_id="1")  → resume
  - one 노드: 재실행 안 함 (이미 성공했으므로)
  - two 노드: 재시도 → 이번에도 에러 (무한 에러 케이스)

invoke(None, thread_id="1") with fixed two → 정상 완료
  - 최종 state: ["input", "one", "two"]
```

### state 반환 차이

```python
# thread_id 기반 → pending_writes 반영한 최신 state
state = graph.get_state({"configurable": {"thread_id": "1"}})
# state.values == ["input", "one"]  (one의 pending_write 반영됨)

# checkpoint_id 명시 → raw checkpoint 값 (pending 미반영)
state = graph.get_state(state.config)  # config에 checkpoint_id 포함
# state.values == ["input"]  (pending 미반영)
```

### 검증 핵심

- `state.tasks[0].error` 에 에러 문자열 포함됨 (직접 확인 가능)
- `durability != "exit"` → 체크포인트 3개 (초기 + 실패 + 재시도)
- `durability == "exit"` → 체크포인트 2개 (초기 + 완료만)
- 성공 노드는 resume 시 재실행하지 않음 (idempotency)

### 관련 개념

- [[Checkpointing]] — `pending_writes` 구조
- [[HumanInTheLoop]] — `invoke(None)` resume 패턴

---

## test_checkpoint_metadata (line 3779)

### 설정

```python
# 단순 노드가 metadata를 반환하는 그래프
builder = StateGraph(...)
graph = builder.compile(checkpointer=MemorySaver())
```

### 검증 핵심

- `checkpoint.config["configurable"]`에 `thread_id`, `checkpoint_id`, `checkpoint_ns` 포함됨
- `checkpoint.metadata`에 `step`, `writes`, `parents` 포함됨
- `step=0` → `__start__` 실행 checkpoint
- `step=1` → 첫 번째 노드 실행 후 checkpoint
- `writes` → 해당 checkpoint에서 어떤 채널에 무엇을 썼는지 기록

### checkpoint metadata 구조

```python
{
    "step": 1,
    "writes": {"node": {"output": "value"}},
    "parents": {"": "parent_checkpoint_id"},
    "source": "loop",
    "thread_id": "1"
}
```

---

## test_checkpoint_recovery (line 5386)

### 설정

```python
# 특정 조건에서 RuntimeError를 발생시키는 노드
call_count = 0
def node(state):
    nonlocal call_count
    call_count += 1
    if call_count == 1:
        raise RuntimeError("First call fails")
    return {"output": "recovered"}

builder = StateGraph(...)
graph = builder.compile(checkpointer=MemorySaver())
```

### 테스트 흐름

```
invoke() → RuntimeError 발생 (call_count=1)
resume invoke(None) → 성공 (call_count=2)
```

### 검증 핵심

- `get_state_history(config)` → 실패한 checkpoint에 `tasks[0].error` 포함
- 실패 checkpoint `metadata["step"]` 값으로 어느 step에서 실패했는지 추적 가능
- `checkpointer.delete_thread(config)` 로 thread 삭제 후 재시작 가능
- resume 시 성공 노드는 재실행 안 함 (test_pending_writes_resume와 동일 패턴)

### state_history 읽는 법

```python
history = list(graph.get_state_history(config))
# history는 역순 (최신 → 오래된 순)
latest = history[0]   # 최신 (성공 또는 현재 상태)
failed = history[1]   # 실패했던 checkpoint
assert failed.tasks[0].error is not None
```

---

## 핵심 패턴 요약

### 병렬 에러 복구 패턴

| 상황 | 동작 |
|------|------|
| 병렬 노드 중 일부 실패 | 성공 노드의 writes는 `pending_writes`에 저장 |
| `invoke(None)` resume | 성공 노드 재실행 안 함, 실패 노드만 재시도 |
| get_state(thread_id만) | pending_writes 반영된 최신 값 반환 |
| get_state(checkpoint_id 포함) | raw checkpoint 값 반환 (pending 미반영) |

### checkpoint durability

| durability 값 | 체크포인트 생성 시점 |
|--------------|-------------------|
| `"sync"` (기본) | 각 superstep 완료 후 |
| `"exit"` | graph 완전 종료 시만 |

---

## 미해결 질문

- `delete_thread()` API가 모든 CheckpointSaver 구현에서 동일하게 동작하는가? (PostgresSaver 등)
- `pending_writes` 구조가 버전 업그레이드 시 호환성은 어떻게 유지되는가?

---

## Sources

- `langgraph-test-pregel-raw-2026-05-25`
- Source Code References:
  - Repo: langgraph
  - File: `libs/langgraph/tests/test_pregel.py`
  - Lines: 876, 3779, 5386

## Related Pages

- [[test_pregel_interrupt_map]]
- [[Checkpointing]]
- [[HumanInTheLoop]]
