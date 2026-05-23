---
source_id: langgraph-source-pregel-interrupts-2026-05-23
title: "LangGraph — interrupt_before/interrupt_after 및 interrupt() 함수 (Pregel 소스코드)"
type: source_code
framework: LangGraph
url: "https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/pregel/main.py"
retrieved_at: "2026-05-23"
status: current
used_by:
  - "docs/wiki/concepts/Checkpointing.md"
---

# Summary

LangGraph의 Human-in-the-Loop 구현 — `interrupt_before` / `interrupt_after` 파라미터와 `interrupt()` 함수.

---

## interrupt_before / interrupt_after (정적 중단)

### 저장 위치 (Pregel 클래스)

```python
interrupt_after_nodes: All | Sequence[str]
interrupt_before_nodes: All | Sequence[str]
```

`StateGraph.compile(interrupt_before=["node_name"], interrupt_after=["node_name"])` 으로 설정.
`"*"` (또는 `All` literal) 전달 시 모든 노드에서 인터럽트.

### 실행 시 동작

```python
# stream/invoke 실행 시 override 가능
interrupt_before = interrupt_before or self.interrupt_before_nodes
interrupt_after = interrupt_after or self.interrupt_after_nodes
```

- graph 수준 기본값으로 동작
- 호출자가 실행 시점에 override 가능
- graph validation 및 시각화 함수에도 전달됨

### 사용 패턴

```python
graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["human_review"],   # 노드 실행 전 중단
    interrupt_after=["generate_draft"],  # 노드 실행 후 중단
)

# 실행 — 중단 지점에서 멈춤
graph.invoke(inputs, {"configurable": {"thread_id": "1"}})

# 상태 확인 및 수정
state = graph.get_state({"configurable": {"thread_id": "1"}})

# 재개
graph.invoke(None, {"configurable": {"thread_id": "1"}})
```

**주의:** checkpointer 필수. thread_id 없으면 동작 안 함.

---

## interrupt() 함수 (동적 중단)

### 구현

```python
def interrupt(value: Any) -> Any:
    """Interrupt the graph with a resumable exception from within a node."""
    conf = get_config()["configurable"]
    scratchpad = conf[CONFIG_KEY_SCRATCHPAD]
    idx = scratchpad.interrupt_counter()

    # 이미 제공된 resume 값이 있으면 반환
    if scratchpad.resume and idx < len(scratchpad.resume):
        conf[CONFIG_KEY_SEND]([(RESUME, scratchpad.resume)])
        return scratchpad.resume[idx]

    # 새 resume 값이 있으면 사용
    v = scratchpad.get_null_resume(True)
    if v is not None:
        scratchpad.resume.append(v)
        conf[CONFIG_KEY_SEND]([(RESUME, scratchpad.resume)])
        return v

    # 없으면 예외 발생 → 실행 중단
    raise GraphInterrupt(
        (Interrupt.from_ns(value=value, ns=conf[CONFIG_KEY_CHECKPOINT_NS]),)
    )
```

### 동작 흐름

1. 노드 내에서 `interrupt(value)` 호출
2. `GraphInterrupt` 예외 → LangGraph가 state를 checkpoint에 저장
3. 실행 중단, `value`가 호출자에게 노출
4. 재개: `graph.invoke(Command(resume=user_input), config)`
5. `interrupt(value)` 가 `user_input`을 반환 값으로 반환하며 노드 계속 실행

### Command(resume=...) 클래스

```python
@dataclass
class Command(Generic[N], ToolOutputMixin):
    graph: str | None = None
    update: Any | None = None
    resume: dict[str, Any] | Any | None = None  # 단일 값 또는 interrupt_id → 값 매핑
    goto: Send | Sequence[Send | N] | N = ()
```

---

## 정적 중단 vs 동적 중단 비교

| 구분 | interrupt_before/after | interrupt() |
|------|----------------------|-------------|
| 설정 위치 | compile() 시 | 노드 함수 내부 |
| 조건부 가능 | ❌ (항상 해당 노드에서 중단) | ✅ (if 조건으로 제어 가능) |
| 코드 변경 필요 | ❌ | ✅ |
| 도입 시기 | 초기부터 | 2024-12 신규 (권장) |
| 권장 여부 | 구 방식 | ✅ 현재 권장 |

LangChain 공식 블로그 (2024-12): interrupt() 방식이 interrupt_before/after보다 더 유연하며 현재 권장.

---

## update_state 패턴

interrupt 없이 상태만 수정:

```python
graph.update_state(
    {"configurable": {"thread_id": "1"}},
    {"state_key": new_value},
    as_node="node_name",  # 해당 노드에서 업데이트한 것처럼 처리
)
```
