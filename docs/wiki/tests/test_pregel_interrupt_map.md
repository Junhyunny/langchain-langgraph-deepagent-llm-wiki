---
type: test_map
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-test-pregel-interrupt-2026-05-25
---

# test_pregel.py — interrupt / resume 테스트 맵

`libs/langgraph/tests/test_pregel.py`에서 [[HumanInTheLoop]] 관련 테스트를 읽고 정리한 맵이다.

## 테스트 파일 위치

- Repo: `langchain-ai/langgraph`
- 파일: `libs/langgraph/tests/test_pregel.py`
- 읽은 날짜: 2026-05-25

---

## 읽은 테스트 요약

### `test_interrupt_multiple` (line 4852)

**목적:** 단일 노드 내 sequential `interrupt()` 2개 동작 확인  
**검증된 동작:**
- `interrupt({"value": 1})` → 즉시 중단 (pending 1개)
- `Command(resume="answer 1")` → 재실행, `interrupt({"value": 2})` → 다시 중단
- `Command(resume="answer 2")` → 완료
- **3회 invoke 필요 (N interrupt → N+1 invoke)**
- `resume_style` 파라미터로 **null resume** ("answer 1")과 **map resume** (`{id: "answer 1"}`) 두 가지 모두 동작 확인

```python
def node(s: State) -> State:
    answer = interrupt({"value": 1})     # 첫 번째 중단
    answer2 = interrupt({"value": 2})    # 두 번째 중단
    return {"my_key": answer + " " + answer2}
```

---

### `test_interrupt_loop` (line 4922)

**목적:** `interrupt()` 를 루프 안에서 반복 호출 (유효성 검사 패턴)  
**검증된 동작:**
- `interrupt("How old are you?")` → 유효하지 않은 값(13, 15) → 루프 재진입 → `interrupt("invalid response")`
- 각 resume마다 노드가 **처음부터 재실행**됨 (`scratchpad.resume[idx]`로 이전 답변 복원)
- 유효한 값(19) → 루프 탈출 → 노드 완료

```python
for _ in range(10):
    value = interrupt(question)        # 루프 내 interrupt
    if not value.isdigit() or int(value) < 18:
        question = "invalid response"
    else:
        break
return {"age": int(value)}
```

**핵심 교훈:** interrupt()는 루프 안에서도 안전하게 사용 가능. 노드 재실행 시 scratchpad의 resume 배열에서 순서대로 값이 복원된다.

---

### `test_multiple_interrupt_state_persistence` (line 5305)

**목적:** 다중 interrupt 중 상태(state) 변화 시점 확인  
**검증된 동작:**
- interrupt 첫 번째 → `get_state().values == {"steps": []}` — **노드가 return하지 않았으므로 state 미변경**
- interrupt 두 번째 → `get_state().values == {"steps": []}` — **여전히 미변경**
- 두 번째 resume 후 완료 → `result["steps"] == ["step1", "step2"]` — **노드 return 후 state 갱신**

```python
def interruptible_node(state: State):
    first = interrupt("First interrupt")
    second = interrupt("Second interrupt")
    return {"steps": [first, second]}   # 두 번 모두 resume 후에야 return
```

**핵심 교훈:** state는 노드가 `return`할 때만 갱신된다. interrupt 중간에는 checkpoint에 pending_writes로만 존재한다.

---

### `test_task_before_interrupt_resume` (line 5832)

**목적:** Functional API(`@entrypoint` + `@task`)에서 `interrupt()` 동작  
**검증된 동작:**
- `@task` + `interrupt()` 조합: `interrupt()` 가 child scratchpad(서브태스크 스크래치패드)에서 실행됨
- 부모 scratchpad에 null resume 소비 추적 위임
- loop 내 N개 질문 → N+1회 invoke 패턴 확인

```python
@entrypoint(checkpointer=sync_checkpointer)
def workflow(number_of_topics: int) -> dict:
    @task
    def ask(question: str) -> str:
        return interrupt(question)   # @task 안의 interrupt

    for i in range(n):
        answers.append(ask(f"topic {i+1}?").result())
```

---

### `test_multi_resume` (line 6210)

**목적:** `Send()` 기반 병렬 그래프에서 다중 interrupt 동시 pending + dict resume  
**검증된 동작:**
- `add_conditional_edges(START, assign_workers, ["child_graph"])` + `Send()` → 5개 자식 노드 병렬 실행
- 5개 interrupt 동시 pending: `len(events["__interrupt__"]) == 5`
- `{id: value}` dict로 **모든 pending 한 번에 resume** 가능
- `get_state().interrupts` 로 pending interrupt 목록 조회 → id 추출

```python
resume_map = {i.id: f"human input for {i.value}" for i in graph.get_state(config).interrupts}
result = graph.invoke(Command(resume=resume_map), config)
```

---

### `test_parallel_interrupts` (line 7594)

**목적:** 병렬 자식 그래프 interrupt의 id별 순차 resume 패턴  
**검증된 동작:**
- 2개 자식 그래프 각각 `interrupt()` → 동시 pending
- `{current_interrupts[0].id: "Resume #1"}` → 하나씩 resume
- **총 3회 invoke** (invoke 1 → 2 pending, invoke 2 → 1 pending, invoke 3 → 완료)
- `invokes == 3` 테스트로 확인

**주의:** 2개 병렬 interrupt → one-at-a-time resume 시 3회 필요  
(모두 한번에 resume하면 2회로 가능)

---

## 핵심 패턴 정리

| 패턴 | 동작 | invoke 횟수 |
|------|------|-------------|
| 단일 노드 N개 sequential interrupt | 1개씩 pending | N+1 |
| 루프 내 interrupt (조건 검사) | 유효 답변 나올 때까지 반복 | 답변 횟수 + 1 |
| 병렬 노드 N개 각 1 interrupt | N개 동시 pending | dict resume 시 2 / one-at-a-time 시 N+1 |
| @task 안 interrupt | child scratchpad, 부모 resume 위임 | sequential과 동일 |

## state 변경 시점

```
interrupt() 첫 발생   → state 불변 (pending_writes에만 존재)
interrupt() 재발생    → state 불변
노드 return 완료      → state 갱신
```

## resume_style: null vs map

| 방식 | 형태 | 조건 |
|------|------|------|
| null resume | `Command(resume="value")` | 단일 pending interrupt 시 |
| map resume | `Command(resume={id: "value"})` | 병렬 pending 분리 지정 시, 또는 any 단일 |

## 테스트에서 확인된 API

- `graph.get_state(config).interrupts` → `list[Interrupt]` — pending 목록
- `interrupt.id` → `str` — AnyStr() (테스트에서 엄격한 ID 비교 안 함)
- `Command(resume=..., update={...})` — resume + state 업데이트 동시 가능

## Files Read
- `libs/langgraph/tests/test_pregel.py` (GitHub raw, 2026-05-25 기준 HEAD)
  - line 4852–4920: `test_interrupt_multiple`
  - line 4922–4995: `test_interrupt_loop`
  - line 5305–5345: `test_multiple_interrupt_state_persistence`
  - line 5832–5879: `test_task_before_interrupt_resume`
  - line 6210–6283: `test_multi_resume`
  - line 7594–7698: `test_parallel_interrupts`

## 관련 페이지

- [[HumanInTheLoop]]
- [[LangGraph Code Map]]
- [[Checkpointing]]

## 미해결 질문

- `test_multi_resume`에서 `add_conditional_edges(START, assign_workers, ["child_graph"])` — `["child_graph"]` list가 path_map인가? → ✅ 확인됨 (아래 참조)
- `test_parallel_interrupts_double` (line 7752) 패턴은? — 아직 미독

## Sources

- `langgraph-test-pregel-interrupt-2026-05-25`
