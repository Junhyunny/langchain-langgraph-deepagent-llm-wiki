---
type: source_summary
source_id: langchain-docs-event-streaming-2026-05-18
title: "LangChain — Event Streaming"
framework: LangChain
status: verified
confidence: high
retrieved_at: 2026-05-18
url: https://docs.langchain.com/oss/python/langchain/event-streaming
---

# Source Summary: LangChain — Event Streaming

## Key Facts

### LangChain Agent와 LangGraph의 관계 (확인됨)

> "LangChain agents are built on LangGraph, so they support the same streaming stack"

- LangChain의 `create_agent`는 LangGraph 위에 구축되어 있음
- 동일한 스트리밍 스택 공유

### Event Streaming 기본

- 권장 API: `stream_events(..., version="v3")`
- 리턴: 타입화된 프로젝션이 있는 run object (stream-mode tuple 파싱 불필요)
- 각 프로젝션을 독립적으로 소비 가능

### 사용 가능한 프로젝션 10종

| 프로젝션 | 용도 |
|---|---|
| `for event in stream` | 전체 envelope + 모든 채널을 포함하는 raw protocol events |
| `stream.messages` | LLM 호출별 모델 메시지 스트림 |
| `message.text` | 텍스트 델타 및 최종 텍스트 |
| `message.reasoning` | reasoning content 델타 (모델이 지원하는 경우) |
| `message.tool_calls` | 모델이 tool call 생성 중 argument chunk |
| `message.output` | 모델 호출 완료 후 최종 메시지 객체 |
| `stream.values` | agent state 스냅샷 |
| `stream.output` | 최종 agent state |
| `stream.subgraphs` | 중첩 그래프 실행 (서브에이전트 + 일반 서브그래프) |
| `stream.extensions` | 커스텀 transformer 프로젝션 |
| `stream.tool_calls` | tool 실행 라이프사이클 (시작 후: inputs, output_deltas, output, error) |

### stream.messages 상세

- `ChatModelStream` 객체 yield
- `.text` — 텍스트 델타 / `str(message.text)`로 최종 텍스트
- `.reasoning` — reasoning 델타 (지원 모델만)
- `.tool_calls` — argument chunk / `.get()`으로 finalized tool calls
- `.output` — 최종 AI message (usage_metadata 포함)
- `.node` — 어떤 노드에서 온 메시지인지

### stream.tool_calls 상세

- tool call EXECUTION 라이프사이클 (모델이 tool call을 만든 이후)
- `call.tool_name`, `call.input`
- `call.output_deltas` — 출력 델타 스트림
- `call.output` — 최종 출력
- `call.error` — 에러

### stream.subgraphs

- **모든** 중첩 `CompiledStateGraph`가 등록됨 (create_agent만 해당하지 않음)
- `create_agent`에 `name=` 전달 → `subagent.graph_name`으로 필터링
- 서브에이전트 handle은 자체 `.messages`, `.values`, `.tool_calls`, `.output` 노출

### Multiple Projections

**동기:** `stream.interleave("messages", "tool_calls", "values")` 사용
```python
for name, item in stream.interleave("messages", "tool_calls", "values"):
    if name == "messages": ...
```

**비동기:** `astream_events` + `asyncio.gather` 사용

### Custom Projections

- `transformers=[MyTransformer]` 전달 → `stream.extensions["key"]` 로 접근
- raw protocol events: `event["method"]`, `event["params"]["namespace"]`, `event["params"]["data"]`

## Important Terms

- [[LangChain]]
- [[LangGraph]]
- [[Streaming]]
- [[Subagents]]
- [[Tool Calling]]
- `stream_events`
- `ChatModelStream`
- `CompiledStateGraph`
- `interleave()`
- `astream_events`

## Interpretation

- LangChain agents가 LangGraph 위에 구축된다는 사실은 LangGraph의 스트리밍 패턴이 LangChain agents에도 그대로 적용됨을 의미한다.
- Typed projection 패턴은 stream-mode tuple을 직접 파싱하던 이전 방식보다 훨씬 안전하고 유지보수하기 쉽다.
- `stream.subgraphs`가 `CompiledStateGraph` 전체를 커버한다는 점은 Deep Agents의 subagent streaming과도 연결된다.

## Open Questions

- `stream_events` v3와 이전 버전의 차이는 무엇인가?
- LangGraph의 Pregel stream mode와 Event Streaming의 관계는?
- Custom transformer의 정확한 계약(contract)은 무엇인가?
- `astream_events`의 반환 타입은 정확히 무엇인가?
- Deep Agents의 `create_deep_agent`도 `stream_events`를 동일하게 지원하는가?

## Used By

- [[LangChain]]
- [[Streaming]]

## Sources

- `langchain-docs-event-streaming-2026-05-18`
