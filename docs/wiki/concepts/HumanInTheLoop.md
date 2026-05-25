---
type: concept
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-24
sources:
  - langgraph-venv-types-py-hitl-2026-05-24
  - langgraph-venv-loop-py-2026-05-24
---

# Human-in-the-Loop (HITL)

## Summary

LangGraph의 Human-in-the-Loop(HITL)는 그래프 실행 도중 사람의 입력이나 승인이 필요한 시점에 실행을 일시 중단하고, 인간의 응답을 받아 재개하는 메커니즘이다. `interrupt()` 함수와 `Command(resume=...)` 패턴으로 구현된다.

## Why It Matters

AI agent가 민감한 작업(파일 삭제, 결제, 외부 API 호출 등)을 수행하기 전에 인간의 확인이 필요하거나, agent가 모호한 입력을 사용자에게 확인받아야 할 때 필수적이다. checkpointing과 통합되어 인터럽트 상태가 영속적으로 유지된다.

## 핵심 공개 API

```python
from langgraph.types import interrupt, Command

# 노드 내에서 사용
def my_node(state):
    answer = interrupt("사용자 확인이 필요합니다: 계속할까요?")
    return {"result": answer}

# 재개
graph.invoke(Command(resume="yes"), config)
```

**필수 조건**: checkpointer가 반드시 설정되어 있어야 한다.

## Key Concepts

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph StateGraph compile invoke flow]]

---

## interrupt() 함수 상세

**검증됨** (`langgraph/types.py` line 801 직접 확인):

```python
def interrupt(value: Any) -> Any:
    ...
```

### 첫 번째 호출 (일시 중단)

1. `CONFIG_KEY_SCRATCHPAD`에서 `PregelScratchpad` 획득
2. `scratchpad.interrupt_counter()` 호출 → 현재 노드 내 interrupt 순번(`idx`) 획득
3. `scratchpad.resume` 목록 확인 → `idx` 위치에 resume 값이 있으면 즉시 반환 (재실행 경로)
4. `get_null_resume()` 확인 → null resume 있으면 반환
5. 위 모두 해당 없음 → `GraphInterrupt((Interrupt.from_ns(value=value, ns=checkpoint_ns),))` 발생

### 두 번째 이후 호출 (resume 후 노드 재실행)

노드는 **처음부터 완전히 재실행**된다. interrupt 호출 시 `scratchpad.resume[idx]`를 반환하여 정상적으로 진행한다.

```
1회차: interrupt("question") → GraphInterrupt 발생 → 노드 중단 + checkpoint 저장
resume: Command(resume="answer") → invoke
2회차: interrupt("question") → scratchpad.resume[0] = "answer" → 반환, 계속 실행
```

### `Interrupt` 데이터클래스

```python
@dataclass
class Interrupt:
    value: Any   # 클라이언트에게 전달되는 값
    id: str      # xxh3_128(checkpoint_ns) 기반 해시 ID
```

- `id`: 다중 interrupt 환경에서 특정 interrupt를 지정해 resume할 때 사용
- `StateSnapshot.interrupts` 필드에 `tuple[Interrupt, ...]`로 포함됨

---

## Command(resume=...) 처리 흐름

**검증됨** (`_loop.py` line 839-950 직접 확인):

```python
class Command:
    graph: str | None = None         # None: 현재 그래프 / Command.PARENT: 부모 그래프
    update: Any | None = None        # 상태 업데이트 dict
    resume: dict[str, Any] | Any | None = None  # resume 값
    goto: Send | Sequence[Send | N] | N = ()     # 다음 노드
```

### `resume` 형식에 따른 분기

| `resume` 값 | 처리 방식 |
|------------|----------|
| 단일 값 (`"yes"`) | 단일 interrupt에 적용 (`NULL_TASK_ID + RESUME` write로 저장) |
| `{interrupt_id: value}` dict | ID로 특정 interrupt 지정 (`CONFIG_KEY_RESUME_MAP` 사용) |
| `None` 또는 미설정 | resume 없이 상태 업데이트/goto만 수행 |

**다중 pending interrupt**: 단일 값 사용 시 `RuntimeError` 발생 → 반드시 `{id: value}` dict 형식 사용해야 함.

### `is_resuming` 감지 조건

```python
is_resuming = bool(checkpoint["channel_versions"]) and bool(
    input is None
    or isinstance(input, Command)
    or run_id == checkpoint_run_id  # 동일 run 재실행
)
```

- checkpoint에 이미 데이터가 있고 + 위 조건 중 하나를 충족하면 resuming 모드
- resuming 시: `versions_seen[INTERRUPT]` 업데이트 → interrupt로 중단된 노드들 재실행 허용

### `is_time_traveling` vs `is_resuming`

| | is_resuming | is_time_traveling |
|---|---|---|
| 의미 | 인터럽트 재개 | 특정 과거 checkpoint로 되돌아가기 |
| RESUME writes | 보존 | 제거됨 |
| fork checkpoint | 생성 안 함 | 생성 (새 브랜치 필요) |
| Command(resume=) | O | X |

---

## 내부 재실행 메커니즘 (PregelScratchpad)

**검증됨** (`_algo.py` line 1280-1345 직접 확인):

`_scratchpad()` 함수가 각 task 실행 직전에 `PregelScratchpad`를 생성한다.

```python
PregelScratchpad(
    step=step,
    stop=stop,
    interrupt_counter=LazyAtomicCounter(),   # 동일 노드 내 interrupt 순번
    resume=task_resume_write,                # [value1, value2, ...] — 이 task의 resume 값 목록
    get_null_resume=get_null_resume,         # null (전체 대상) resume 조회 함수
    ...
)
```

**`task_resume_write` 결정 순서**:
1. `pending_writes`에서 `(task_id, RESUME)` 항목 → task-specific resume
2. `resume_map[namespace_hash]` 항목 → namespace + task 조합 resume (서브그래프용)
3. 없으면 빈 리스트 `[]`

**다중 interrupt 지원**: 같은 노드에서 `interrupt()`를 여러 번 호출하면 `interrupt_counter`로 순번 관리. `resume = [v0, v1, v2, ...]` 배열에서 순서대로 반환.

---

## interrupt → resume 전체 흐름

```
[첫 번째 invoke]
graph.invoke(input, config)
  ↓
노드 실행 → interrupt("question") 호출
  ↓
GraphInterrupt 발생
  ↓
_suppress_interrupt() 실행:
  1. checkpoint + pending writes 저장
  2. values 이벤트 emit (최종 상태)
  3. {INTERRUPT: (Interrupt(value="question", id="abc..."),)} 이벤트 emit
  4. return True (exception 억제)
  ↓
invoke 반환 (정상 종료처럼 보임)
  ↓
클라이언트: StateSnapshot.interrupts 에서 Interrupt 확인

[두 번째 invoke — 재개]
graph.invoke(Command(resume="answer"), config)
  ↓
is_resuming = True 감지
  ↓
(NULL_TASK_ID, RESUME, "answer") write 저장
  ↓
versions_seen[INTERRUPT] 업데이트 → 이전에 중단된 노드 재실행 허용
  ↓
노드 처음부터 재실행
  ↓
interrupt("question") 호출 → scratchpad.resume[0] = "answer" → 반환
  ↓
노드 계속 실행 → 완료
```

---

## Command(goto=...) — 노드 이동

```python
# 특정 노드로 이동
Command(goto="node_name")

# 여러 노드로 동시 이동
Command(goto=["node_a", "node_b"])

# Send로 특정 상태와 함께 이동
Command(goto=Send("node_name", {"key": "value"}))

# 부모 그래프로 제어 이동
Command(graph=Command.PARENT, goto="parent_node")
```

---

## Command(update=...) — 상태 직접 업데이트

```python
# 상태 업데이트와 함께 resume
Command(
    resume="user_answer",
    update={"status": "approved"}  # 상태 직접 패치
)
```

---

## 다중 interrupt 패턴

### 단일 노드 내 순차 interrupt (실행으로 검증됨)

**검증됨** (`examples/langgraph_core/04_hitl_advanced.py` 실행 2026-05-24):

```python
def review_node(state):
    # 첫 번째 interrupt: 즉시 GraphInterrupt → pending 1개
    security = interrupt({"question": "보안 승인?", "code": state["code"]})
    # 두 번째 interrupt: 첫 resume 후 재실행 시 도달 → 또 pending 1개
    style = interrupt({"question": "스타일 승인?", "code": state["code"]})
    return {"security_ok": security, "style_ok": style}
```

각 `interrupt()` 호출은 즉시 실행 중단 → **항상 pending 1개**.
노드 내 2개의 interrupt = **3회의 invoke 필요**:

```
invoke(input)              → pause at interrupt 1  (next=('review',))
invoke(Command(resume=T))  → pause at interrupt 2  (next=())
invoke(Command(resume=T))  → node completes
```

**`next=()` 주의**: 두 번째 resume 후 `get_state().next == ()` 이지만 `tasks[0].interrupts` 에 interrupt가 있으면 아직 중단 상태. 마지막 resume이 아님.

### 병렬 노드 각각 interrupt (이때 `{id: value}` dict 사용)

여러 노드가 **동일 superstep**에서 병렬 실행 → 각각 interrupt 발생 → 동시에 pending 2개 이상:

```python
# 이 경우 단일 값으로 resume 불가 → RuntimeError
# 반드시 {interrupt_id: value} dict 사용
graph.invoke(
    Command(resume={"id_from_node_a": "yes", "id_from_node_b": True}),
    config
)
```

**`_loop.py` line 895 검증**: `len(self._pending_interrupts()) > 1` 이면 단일 값 → RuntimeError.

---

## interrupt vs compile(interrupt_before=...) 비교

| | `interrupt()` | `compile(interrupt_before=["node"])` |
|---|---|---|
| 위치 | 노드 내부 임의 위치 | 노드 진입 직전 |
| 조건부 | O (if 분기 가능) | X (항상 중단) |
| resume 값 전달 | O (`Command(resume=)`) | X (상태 업데이트만 가능) |
| 다중 interrupt | O | X |
| 도입 버전 | 0.2.24 | 초기부터 |

현대 LangGraph에서는 `interrupt()`가 더 유연하고 권장된다.

---

## Source Code References

- Repo: `https://github.com/langchain-ai/langgraph`
- Commit: UNKNOWN (`.venv` 설치본 기준)
- Files:
  - `.venv/lib/python3.14/site-packages/langgraph/types.py` ✅ 관련 부분 읽음 (2026-05-24)
    - `interrupt()` 함수 (line 801): 첫 호출 → GraphInterrupt, 재호출 → resume 값 반환
    - `Interrupt` dataclass (line 525): value + id(xxh3_128 기반)
    - `Command` dataclass (line 749): graph/update/resume/goto
  - `.venv/lib/python3.14/site-packages/langgraph/pregel/_loop.py`
    - `is_resuming` 감지 (line 839)
    - `is_time_traveling` 감지 (line 857)
    - `Command(resume=)` 처리 + `resume_is_map` 분기 (line 882)
    - `versions_seen[INTERRUPT]` 업데이트 (line 925)
    - `_suppress_interrupt()`: GraphInterrupt 억제 + checkpoint 저장 (line 1304)
  - `.venv/lib/python3.14/site-packages/langgraph/pregel/_algo.py`
    - `_scratchpad()` (line 1280): PregelScratchpad 생성, resume 값 목록 구성

---

## Tests

**`test_pregel.py` (2026-05-25 읽음) — 상세 맵: [[test_pregel_interrupt_map]]**

| 테스트 | 핵심 검증 |
|--------|-----------|
| `test_interrupt_multiple` (line 4852) | sequential N interrupt → N+1 invoke; null/map resume 양쪽 동작 |
| `test_interrupt_loop` (line 4922) | 루프 내 interrupt; 노드 재실행 시 scratchpad 복원 |
| `test_multiple_interrupt_state_persistence` (line 5305) | interrupt 중 state 미변경; 노드 return 후 state 갱신 |
| `test_task_before_interrupt_resume` (line 5832) | `@task` + `interrupt()` 조합; child scratchpad 위임 |
| `test_multi_resume` (line 6210) | `Send()` 병렬 → N개 동시 pending → `{id:v}` dict 한번에 resume |
| `test_parallel_interrupts` (line 7594) | 병렬 2개 interrupt → one-at-a-time resume → 3 invoke 확인 |

---

## Related Pages

- [[Checkpointing]]
- [[LangGraph]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

---

## Open Questions

- `compile(interrupt_before=["node"])` 의 내부 구현 경로는? `interrupt()`와 동일한 `_suppress_interrupt()`를 거치는가? — Needs Source
- 서브그래프에서 `interrupt()`가 발생하면 부모 그래프에서 어떻게 처리되는가? — Needs Source
- `Command(graph=Command.PARENT, ...)` 처리 경로는 어디에 있는가? — Needs Source

---

## Sources

- `langgraph-venv-types-py-hitl-2026-05-24`
- `langgraph-venv-loop-py-2026-05-24`
