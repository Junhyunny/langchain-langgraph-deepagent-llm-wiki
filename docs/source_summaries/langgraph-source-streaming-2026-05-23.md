---
source_id: langgraph-source-streaming-2026-05-23
title: "LangGraph — Streaming Source Code (StreamMode, Transformers, stream_events v3, GraphRunStream)"
type: source_code
framework:
  - LangGraph
  - LangChain
url: "https://github.com/langchain-ai/langgraph/tree/main/libs/langgraph/langgraph"
retrieved_at: "2026-05-23"
status: current
used_by:
  - "docs/wiki/concepts/Event Streaming.md"
---

# Summary

LangGraph `StreamMode`, `stream_events v3` 내부 구현, `GraphRunStream` Transformer 구조.
Source: `langgraph/types.py`, `langgraph/pregel/main.py`, `langchain_core/runnables/base.py`

---

## StreamMode 7종

```python
StreamMode = Literal[
    "values",       # 각 step 후 전체 state 스냅샷
    "updates",      # 각 step 후 업데이트한 노드 이름 + 변경분만
    "messages",     # LLM 호출의 토큰 단위 메시지 + 메타데이터
    "custom",       # StreamWriter로 직접 방출한 임의 데이터
    "checkpoints",  # checkpoint 생성 시 이벤트
    "tasks",        # 태스크 시작/종료 이벤트 (결과·에러 포함)
    "debug",        # checkpoints + tasks (단계별 최대 정보)
]
```

Source: `langgraph/types.py`

---

## stream() 출력 형태

| 호출 방식 | 출력 형태 |
|---------|---------|
| `stream_mode="values"` (단일 문자열) | payload 그대로 yield |
| `stream_mode=["values","updates"]` (리스트) | `(mode, payload)` tuple yield |
| `subgraphs=True` + 리스트 | `(namespace, mode, payload)` tuple yield |
| `version="v2"` | `{"type": mode, "ns": ns, "data": payload}` dict yield |

---

## stream_events v3 내부 구현

```
stream_events(version="v3", ...)
    → _pregel_stream_v3()
        → StreamMux 구성 (4개 기본 Transformer + compile-time + call-site)
        → self.stream(
               stream_mode=_collect_stream_modes(mux),  # Transformer들의 required_stream_modes 합집합
               subgraphs=True,
               version="v2"
           )
        → GraphRunStream (또는 AsyncGraphRunStream) 반환
```

**핵심:** v3는 Pregel `stream()`을 직접 사용하는 레이어다. `stream_mode`와 `subgraphs`는 내부에서 결정되므로 호출자가 전달하면 `TypeError`.

Source: `langgraph/pregel/main.py`

---

## v3 기본 Transformer 4개

| Transformer | required_stream_modes | 제공 projection |
|------------|----------------------|----------------|
| `ValuesTransformer` | `("values",)` | `run.values` |
| `MessagesTransformer` | `("messages",)` | `run.messages` |
| `LifecycleTransformer` | `("tasks",)` | `run.lifecycle` |
| `SubgraphTransformer` | `("tasks",)` | `run.subgraphs` |

추가: compile-time `stream_transformers` (예: `ToolCallTransformer`) + call-site `transformers=`

Source: `langgraph/pregel/main.py:3500-3507`

---

## stream_events v1 / v2 / v3 비교

| 버전 | 반환 타입 | 특징 |
|-----|---------|------|
| v1 | `Iterator[StreamEvent]` | 구버전 호환. `parent_ids` 빈 리스트. deprecated 예정 |
| v2 | `Iterator[StreamEvent]` | 기본값. custom events, `parent_ids` 지원 |
| v3 | `GraphRunStream` | typed projection. `BaseChatModel`·`CompiledGraph`만 지원. **현재 베타** |

Source: `langchain_core/runnables/base.py`

---

## astream_log 및 astream_events

- `astream_log` → **deprecated since langchain-core 1.3.3, 제거 예정 2.0.0**. 대체: `astream` 사용 권장.
  - `astream_log`는 `RunLogPatch`/`RunLog` (JSON Patch 형식) yield — 구형 API
- `astream_events` → `StreamEvent` dict yield — 현재 API

Source: `langchain_core/runnables/base.py`

---

## MessagesTransformer V1 AIMessageChunk 제한

- V1 `AIMessageChunk` tuples (`on_llm_new_token`) → `run.messages`에서 **무시됨**
- content-block 스트리밍을 `run.messages`에서 받으려면 `stream_events(version="v3")` 필수
- 레거시 `stream()` 호출 모델의 `on_chain_end`에서 반환된 최종 `AIMessage`는 노출됨

---

## Deep Agents create_deep_agent의 stream_events v3 지원

**YES — 지원됨.**

- `create_deep_agent` → `create_agent` → `CompiledStateGraph` 반환
- `CompiledStateGraph`는 `Pregel`을 상속 → `stream_events(version="v3")` 그대로 지원
- `create_agent` compile 시 `ToolCallTransformer` + middleware transformers 등록 → `run.tool_calls` 자동 제공
- ⚠️ `create_deep_agent`가 `_subagent_factory` transformer를 `transformers=`로 전달하는지 여부는 미확인

Source: `langgraph/pregel/main.py`, `deepagents-source-graph-2026-05-19`

---

## 미확인 사항

- `_collect_stream_modes(mux)` 함수 구현 상세 — Needs Source
- `ToolCallTransformer` 전체 구현 — Needs Source
- `SubgraphTransformer`가 `stream.subgraphs`에서 subagent handle을 어떻게 식별하는지 — Needs Source
