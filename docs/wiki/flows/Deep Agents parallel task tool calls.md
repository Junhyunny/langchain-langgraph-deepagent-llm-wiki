---
type: flow
framework: Deep Agents
status: partial
confidence: high
last_reviewed: 2026-06-06
sources:
  - deepagents-source-subagents-2026-05-23
  - langgraph-prebuilt-tool-node-2026-05-27
---

# Deep Agents parallel task tool calls

## Summary

단일 `AIMessage`가 `task` tool call을 여러 개 반환할 때, Deep Agents는 subagent를 **병렬로** 실행한다.
병렬성의 원천은 `SubAgentMiddleware` 자체가 아니라 **LangGraph `ToolNode`의 multi-tool-call 실행 모델**이다.

## Why It Matters

병렬 task 실행은 fan-out 패턴의 핵심이다. 여러 subagent를 순차가 아닌 동시에 실행하면 latency를 줄일 수 있다.
그러나 parent state 병합 순서는 완료 시간이 아니라 **tool call 입력 순서**를 따르기 때문에, reducer 설계에 주의가 필요하다.

## 병렬 실행이 작동하는 원리

```
parent AIMessage
  tool_calls: [
    { name: "task", id: "call-slow", args: { subagent_type: "slow-worker", ... } },
    { name: "task", id: "call-fast", args: { subagent_type: "fast-worker", ... } },
  ]
  ↓
LangGraph ToolNode
  → executor.map(run_one, tool_calls)   ← ThreadPoolExecutor 또는 asyncio.gather
  → slow-worker 시작 (t=0)
  → fast-worker 시작 (t≈0)
  → fast-worker 완료 (t=0.06s)
  → slow-worker 완료 (t=0.26s)
  → results 리스트: [slow-result, fast-result]   ← 입력 순서 유지
  ↓
parent state
  messages: [ToolMessage("slow report"), ToolMessage("fast report")]  ← tool call 순서
```

**핵심**: `executor.map()`은 완료 순서가 아니라 **입력 순서**로 output 리스트를 구성한다.

Source: `deepagents-source-subagents-2026-05-23`, `langgraph-prebuilt-tool-node-2026-05-27`

## 실험 결과 (2026-05-30)

실험 코드: `examples/deepagents_core/05_subagent_parallel_tasks.py`

```text
subagent timeline:
  ~0.006s  slow-worker start
  ~0.006s  fast-worker start    ← 거의 동시에 시작 → 병렬 실행 확인
  ~0.060s  fast-worker end
  ~0.261s  slow-worker end

parent messages (AIMessage.tool_calls 순서):
  ToolMessage: "slow report finished after 0.25s"   ← slow가 먼저 (입력 순서)
  ToolMessage: "fast report finished after 0.05s"   ← fast가 나중 (입력 순서)

parent state:
  reports: ["slow-report", "fast-report"]            ← 입력 순서 유지
  todos:   ["parent todo stays parent-owned"]        ← _EXCLUDED_STATE_KEYS 적용됨
```

Source: `[[2026-05-30 deepagents parallel task tool calls]]`

## Parent State 병합 규칙

병렬 task 실행에서 여러 subagent가 같은 parent state key를 업데이트할 때:

| 상황 | 결과 |
|------|------|
| key에 reducer 있음 (`Annotated[list, add]` 등) | reducer가 병합 의미 정의 (안전) |
| key에 reducer 없음 (덮어쓰기) | 나중에 완료된 subagent가 이전 값을 덮어씀 → **비결정적** ⚠️ |
| `_EXCLUDED_STATE_KEYS`에 포함된 key | 출력 병합에서 제외 — 어떤 subagent도 parent에 영향 없음 |

**권장**: 여러 subagent가 같은 key를 업데이트하면 reducer를 명시한다.

Source: `deepagents-source-subagents-2026-05-23`

## _EXCLUDED_STATE_KEYS — 다중 task에서도 적용

```python
_EXCLUDED_STATE_KEYS = {
    "messages",
    "todos",
    "structured_response",
    "skills_metadata",
    "skills_load_errors",
    "memory_contents",
}
```

다중 task 병렬 호출에서도 이 필터는 각 subagent의 입력/출력에 동일하게 적용된다.
실험에서 child `todos`가 여러 subagent 모두에서 parent로 병합되지 않음을 확인.

Source: `deepagents-source-subagents-2026-05-23`

## async 경로

- **sync**: `ToolNode` 내부 `ThreadPoolExecutor.map()` 사용
- **async**: `asyncio.gather()` 사용 — 결과 순서 보장 여부는 **미검증**

Source: `langgraph-prebuilt-tool-node-2026-05-27` (부분 검증)

## Call Path (상세)

```
parent AIMessage(tool_calls=[task_A, task_B])
  ↓
LangGraph ToolNode.run_many(tool_calls)
  → ThreadPoolExecutor.map(run_one, [task_A, task_B])
     ├── Thread-1: SubAgentMiddleware._run_task(task_A)
     │     → _validate_and_prepare_state()
     │     → subagent_A.invoke(state_A)
     │     → _return_command_with_state_update()
     └── Thread-2: SubAgentMiddleware._run_task(task_B)
           → _validate_and_prepare_state()
           → subagent_B.invoke(state_B)
           → _return_command_with_state_update()
  → results = [result_A, result_B]   ← 입력 순서
  ↓
Command(update={...merged_state...}, messages=[ToolMessage_A, ToolMessage_B])
  ↓
parent agent loop continues
```

## 관련 개념

- **fan-out 패턴**: `Send` (LangGraph)와의 차이
  - LangGraph `Send`: 노드 레벨 fan-out, 상태 merge를 명시적으로 설계
  - Deep Agents `task` 병렬: tool call 레벨 fan-out, `ToolNode`가 자동 처리

→ [[LangGraph ToolNode Command vs Deep Agents task tool]] 비교 참조

## Source Code References

- Repo: `https://github.com/langchain-ai/deepagents`
- Commit: UNKNOWN
- Files:
  - `libs/deepagents/deepagents/middleware/subagents.py` — `SubAgentMiddleware._run_task`, `_EXCLUDED_STATE_KEYS`

- Repo: `https://github.com/langchain-ai/langgraph`
- Files:
  - `libs/langgraph/langgraph/prebuilt/tool_node.py` — `ToolNode.run_many`, executor 구현

## Related Pages

- [[Deep Agents SubAgentMiddleware task tool flow]]
- [[Deep Agents]]
- [[Subagents]]
- [[LangGraph ToolNode flow]]
- [[LangGraph ToolNode Command vs Deep Agents task tool]]

## Open Questions

- `async` 경로(`ainvoke`)에서도 `asyncio.gather()` 결과 순서가 tool call 입력 순서를 보장하는가?
- reducer 없는 동일 key를 여러 subagent가 동시에 업데이트하면 어떤 에러 메시지가 발생하는가?
- `SubAgentMiddleware._run_task`에서 예외 발생 시 나머지 parallel task의 실행은 취소되는가?

## Sources

- `deepagents-source-subagents-2026-05-23`
- `langgraph-prebuilt-tool-node-2026-05-27`
