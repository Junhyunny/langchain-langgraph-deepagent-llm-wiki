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
  - langgraph-source-streaming-2026-05-23
---

# Event Streaming

## 요약

Event Streaming은 agent 실행 중 발생하는 이벤트(메시지 생성, 도구 호출, 상태 업데이트)를 실시간으로 소비하는 기능이다. LangChain은 `stream_events(version="v3")` API를 제공하며, LangGraph `Pregel` 런타임 위에 구축된 typed projection 레이어다.

## 중요한 이유

- 사용자에게 응답을 점진적으로 표시하려면 스트리밍이 필수다.
- agent 내부 동작(어떤 도구가 호출됐는지, 어떤 서브에이전트가 실행됐는지)을 실시간 모니터링할 수 있다.
- LangChain agents는 LangGraph 위에 구축되어 있어 동일한 스트리밍 스택을 공유한다.

## LangGraph StreamMode 7종

*Source: `langgraph-source-streaming-2026-05-23`*

LangGraph의 기본 스트리밍 레이어. `graph.stream(input, stream_mode=...)`에서 사용.

| StreamMode | 설명 |
|-----------|------|
| `"values"` | 각 step 후 전체 state 스냅샷 |
| `"updates"` | 각 step 후 업데이트한 노드 이름 + 변경분만 |
| `"messages"` | LLM 호출의 토큰 단위 메시지 + 메타데이터 |
| `"custom"` | `StreamWriter`로 노드 내부에서 직접 방출한 임의 데이터 |
| `"checkpoints"` | checkpoint 생성 시 이벤트 |
| `"tasks"` | 태스크 시작/종료 이벤트 (결과·에러 포함) |
| `"debug"` | `checkpoints` + `tasks` (단계별 최대 정보) |

`stream_mode` 리스트 전달 시 `(mode, payload)` tuple yield. `subgraphs=True` + 리스트 시 `(namespace, mode, payload)`.

## stream_events v3 API

*Source: `langchain-docs-event-streaming-2026-05-18`, `langgraph-source-streaming-2026-05-23`*

권장 API: `stream_events(..., version="v3")`

### Pregel stream_mode와의 연결 고리 (소스 확인됨)

```
stream_events(version="v3")
    → _pregel_stream_v3()
        → StreamMux (Transformer 목록 구성)
        → Pregel.stream(
               stream_mode=_collect_stream_modes(mux),  # 합집합
               subgraphs=True,
               version="v2"
           )
        → GraphRunStream 반환
```

**핵심:** v3는 Pregel `stream()`을 그대로 사용하는 레이어다. 각 Transformer가 필요한 `stream_mode`를 선언하면 v3가 내부에서 이 모드들의 합집합으로 Pregel을 구동한다.

### 기본 내장 Transformer 4개

| Transformer | 사용 stream_mode | 제공 projection |
|------------|----------------|----------------|
| `ValuesTransformer` | `values` | `run.values` |
| `MessagesTransformer` | `messages` | `run.messages` |
| `LifecycleTransformer` | `tasks` | `run.lifecycle` |
| `SubgraphTransformer` | `tasks` | `run.subgraphs` |

추가로 compile-time Transformer (`ToolCallTransformer` 등)와 call-site `transformers=` 파라미터로 확장 가능.

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

### stream.messages 상세

`ChatModelStream` 객체를 yield한다.

- `.text` — 텍스트 델타 / `str(message.text)` → 최종 텍스트
- `.reasoning` — reasoning 델타 (지원 모델만)
- `.tool_calls` — argument chunk / `.get()` → finalized tool calls
- `.output` — 최종 AI message (usage_metadata 포함)
- `.node` — 어떤 노드에서 온 메시지인지

**주의:** `MessagesTransformer`는 V1 `AIMessageChunk` (`on_llm_new_token`) 무시. content-block 스트리밍을 받으려면 `stream_events(version="v3")` 필수.

### stream.tool_calls 상세

tool call **실행** 라이프사이클:
- `call.tool_name`, `call.input`
- `call.output_deltas` — 출력 델타 스트림
- `call.output` — 최종 출력
- `call.error` — 에러 (있을 경우)

### stream.subgraphs

- **모든** 중첩 `CompiledStateGraph`가 등록됨
- `create_agent(name=...)` 전달 → `subagent.graph_name`으로 필터링 가능
- 서브에이전트 handle은 자체 `.messages`, `.values`, `.tool_calls`, `.output` 노출

### 여러 프로젝션 동시 소비

**동기:**
```python
for name, item in stream.interleave("messages", "tool_calls", "values"):
    if name == "messages": ...
    elif name == "tool_calls": ...
```

**비동기:** `astream_events` + `asyncio.gather`

### 커스텀 프로젝션

```python
stream = agent.stream_events(input, transformers=[MyTransformer])
async for event in stream.extensions["my_key"]:
    ...
```

raw protocol events 접근: `event["method"]`, `event["params"]["namespace"]`, `event["params"]["data"]`

## stream_events 버전 비교

*Source: `langgraph-source-streaming-2026-05-23`*

| 버전 | 반환 타입 | 특징 |
|-----|---------|------|
| v1 | `Iterator[StreamEvent]` | 구버전 호환. `parent_ids` 빈 리스트. deprecated 예정 |
| v2 | `Iterator[StreamEvent]` | 기본값. custom events, `parent_ids` 지원 |
| v3 | `GraphRunStream` | typed projection. `BaseChatModel`·`CompiledGraph`만 지원. **현재 베타** |

## astream_log vs astream_events

*Source: `langgraph-source-streaming-2026-05-23`*

- `astream_log` → **deprecated** (langchain-core 1.3.3, 제거 예정 2.0.0). 대체: `astream` 사용 권장.
  - `RunLogPatch`/`RunLog` (JSON Patch 형식) yield — 구형 API
- `astream_events` → `StreamEvent` dict yield — 현재 API
- `stream_events(version="v3")` → `GraphRunStream` — typed projection 현재 권장

## 프레임워크별 지원

### LangChain

`create_agent`로 생성된 agent는 `stream_events(version="v3")` 완전 지원. compile 시 `ToolCallTransformer` + middleware transformers가 자동 등록되어 `run.tool_calls` 프로젝션 제공.

Source: `langchain-docs-event-streaming-2026-05-18`

### LangGraph

`CompiledStateGraph`가 `Pregel`을 상속하므로 `stream_events v3`를 네이티브로 지원. `stream_events v3`는 내부적으로 `stream_mode` 합집합으로 Pregel을 구동하는 레이어.

Source: `langgraph-source-streaming-2026-05-23`

### Deep Agents

**YES — 지원됨.** `create_deep_agent`는 `create_agent`를 통해 `CompiledStateGraph`를 반환하므로 동일한 streaming API를 지원한다.

⚠️ `create_deep_agent`의 `_subagent_factory` transformer가 `stream.subgraphs`에서 subagent를 정확히 식별하는지 여부는 미확인.

Source: `langgraph-source-streaming-2026-05-23`

## 미해결 질문

- `_collect_stream_modes(mux)` 함수의 정확한 구현 — Needs Source
- `ToolCallTransformer` 전체 구현 — Needs Source
- Custom stream transformer의 정확한 계약(contract)은 무엇인가? — Needs Source
- `SubgraphTransformer`가 `stream.subgraphs`에서 subagent handle을 어떻게 식별하는지 — Needs Source

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Subagents]]
- [[StateGraph]]

## Sources

- `langchain-docs-event-streaming-2026-05-18`
- `langgraph-source-streaming-2026-05-23`
