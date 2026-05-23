---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-event-streaming-2026-05-18
---

# Event Streaming

## 요약

Event Streaming은 agent 실행 중 발생하는 이벤트(메시지 생성, 도구 호출, 상태 업데이트)를 실시간으로 소비하는 기능이다. LangChain은 `stream_events(version="v3")` API를 제공하며, LangGraph 위에 구축된 모든 agent에서 동일한 스트리밍 스택을 공유한다.

Source: `langchain-docs-event-streaming-2026-05-18`

## 중요한 이유

- 사용자에게 응답을 점진적으로 표시하려면 스트리밍이 필수다.
- agent 내부 동작(어떤 도구가 호출됐는지, 어떤 서브에이전트가 실행됐는지)을 실시간 모니터링할 수 있다.
- LangChain agents는 LangGraph 위에 구축되어 있어 동일한 스트리밍 스택을 공유한다.

## LangChain Agent와 LangGraph의 관계

> "LangChain agents are built on LangGraph, so they support the same streaming stack"

`create_agent`로 생성된 agent는 내부적으로 LangGraph `CompiledStateGraph`를 반환하므로, LangGraph의 스트리밍 인프라를 그대로 사용한다.

Source: `langchain-docs-event-streaming-2026-05-18`

## stream_events v3 API

권장 API: `stream_events(..., version="v3")`

기존 stream-mode tuple 파싱 방식과 달리 **타입화된 프로젝션**을 독립적으로 소비할 수 있다.

### 10가지 프로젝션

| 프로젝션 | 설명 |
|----------|------|
| `for event in stream` | raw protocol events (전체 envelope + 모든 채널) |
| `stream.messages` | LLM 호출별 모델 메시지 스트림 |
| `message.text` | 텍스트 델타 + 최종 텍스트 |
| `message.reasoning` | reasoning content 델타 (모델 지원 시) |
| `message.tool_calls` | tool call argument chunk |
| `message.output` | 최종 AIMessage 객체 (usage_metadata 포함) |
| `stream.values` | agent state 스냅샷 |
| `stream.output` | 최종 agent state |
| `stream.subgraphs` | 중첩 그래프 실행 (서브에이전트 + 서브그래프) |
| `stream.extensions` | 커스텀 transformer 프로젝션 |
| `stream.tool_calls` | tool 실행 라이프사이클 |

Source: `langchain-docs-event-streaming-2026-05-18`

### stream.messages 상세

`ChatModelStream` 객체를 yield한다.

- `.text` — 텍스트 델타 / `str(message.text)` → 최종 텍스트
- `.reasoning` — reasoning 델타 (지원 모델만)
- `.tool_calls` — argument chunk / `.get()` → finalized tool calls
- `.output` — 최종 AIMessage (usage_metadata 포함)
- `.node` — 어떤 노드에서 온 메시지인지

### stream.tool_calls 상세

tool call **실행** 라이프사이클 (모델이 tool call을 생성한 이후 단계):

- `call.tool_name`, `call.input`
- `call.output_deltas` — 출력 델타 스트림
- `call.output` — 최종 출력
- `call.error` — 에러 (있을 경우)

### stream.subgraphs

- **모든** 중첩 `CompiledStateGraph`가 등록됨 (`create_agent`만 해당하지 않음)
- `create_agent(name=...)` 전달 → `subagent.graph_name`으로 필터링 가능
- 서브에이전트 handle은 자체 `.messages`, `.values`, `.tool_calls`, `.output` 노출

### 여러 프로젝션 동시 소비

**동기:**
```python
for name, item in stream.interleave("messages", "tool_calls", "values"):
    if name == "messages":
        ...
    elif name == "tool_calls":
        ...
```

**비동기:** `astream_events` + `asyncio.gather`

### 커스텀 프로젝션

```python
stream = agent.stream_events(input, transformers=[MyTransformer])
async for event in stream.extensions["my_key"]:
    ...
```

raw protocol events 접근: `event["method"]`, `event["params"]["namespace"]`, `event["params"]["data"]`

## 프레임워크별 지원

### LangChain

`create_agent`로 생성된 agent는 `stream_events(version="v3")` 완전 지원. 타입화된 프로젝션 10가지를 독립적으로 소비 가능.

Source: `langchain-docs-event-streaming-2026-05-18`

### LangGraph

LangChain agents의 스트리밍 스택 기반. `CompiledStateGraph`가 streaming 런타임을 제공한다. LangGraph의 Pregel stream mode와의 정확한 관계는 미해결이다 — Needs Source.

### Deep Agents

`create_deep_agent`가 내부적으로 LangGraph `CompiledStateGraph`를 반환하므로, 이론적으로 동일한 streaming API를 지원한다.

⚠️ Needs Verification — Deep Agents가 `stream_events`를 동일하게 지원하는지 공식 문서 확인 필요.

## 미해결 질문

- `stream_events` v3와 이전 버전의 차이는 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- LangGraph의 Pregel stream mode와 Event Streaming(`stream_events`)의 정확한 관계는? — Needs Source
- Custom stream transformer의 계약(contract)은 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- Deep Agents의 `create_deep_agent`도 `stream_events`를 동일하게 지원하는가? — Source: `langchain-docs-event-streaming-2026-05-18`
- `astream_events`와 `astream_log`의 차이는? — Source: `langchain-source-runnable-2026-05-23`

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Subagents]]
- [[StateGraph]]

## Sources

- `langchain-docs-event-streaming-2026-05-18`
