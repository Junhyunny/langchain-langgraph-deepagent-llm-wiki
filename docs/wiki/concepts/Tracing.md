---
type: concept
framework:
  - OpenAI Agents SDK
  - LangChain
  - LangGraph
  - Deep Agents
status: verified
confidence: medium
last_reviewed: 2026-06-06
sources:
  - openai-agents-sdk-tracing-2026-05-23
  - langsmith-sdk-readme-2026-06-06
  - langgraph-source-streaming-2026-05-23
  - deepagents-source-backends-sandbox-2026-06-06
---

# Tracing

## Summary

트레이싱은 에이전트 실행 흐름을 기록하고 시각화하여 디버깅 및 성능 최적화에 활용하는 메커니즘이다. LLM 생성, 도구 호출, 핸드오프, 가드레일 등 각 스텝의 input/output을 추적한다.

## Why It Matters

에이전트 시스템은 여러 LLM 호출, 도구 호출, 에이전트 전환이 중첩되어 동작한다. 트레이싱 없이는 어느 단계에서 무엇이 일어났는지 파악하기 어렵다. 트레이싱은 디버깅, 성능 최적화, 이상 감지, 비용 분석에 필수다.

## Key Concepts

- **Trace** — 단일 엔드투엔드 워크플로우 단위
- **Span / Run** — 시작/종료 시각이 있는 개별 작업 단위
- **Run Types** — `llm`, `chain`, `tool` (기본 분류)
- **Trace Processor** — trace를 목적지(대시보드, 외부 시스템)로 전송하는 컴포넌트

---

## OpenAI Agents SDK

*Source: `openai-agents-sdk-tracing-2026-05-23`*

### 트레이싱 기본 활성화

기본적으로 켜져 있으며 `platform.openai.com/traces` 대시보드로 전송된다.

**비활성화 방법:**
```python
# 환경 변수
OPENAI_AGENTS_DISABLE_TRACING=1

# 코드
from agents import set_tracing_disabled
set_tracing_disabled(True)

# 단일 실행
from agents import RunConfig
config = RunConfig(tracing_disabled=True)
```

### Trace 구조

```
Trace (전체 워크플로우)
├── workflow_name: str
├── trace_id: str  ("trace_" + 32 alphanumeric)
├── group_id: str  (동일 대화 묶음용)
└── metadata: dict

  └── Span (개별 작업)
      ├── started_at / ended_at
      ├── trace_id
      ├── parent_id  (중첩 span 지원)
      └── span_data  (AgentSpanData, GenerationSpanData, ...)
```

### 자동 트레이싱 대상

| 이벤트 | Span 타입 |
|--------|-----------|
| `Runner.run()` 전체 | `trace()` |
| 에이전트 실행 | `agent_span()` |
| LLM 생성 | `generation_span()` |
| function tool 호출 | `function_span()` |
| 가드레일 | `guardrail_span()` |
| 핸드오프 | `handoff_span()` |
| 음성 인식 | `transcription_span()` |
| 음성 합성 | `speech_span()` |

### 여러 실행을 하나의 Trace로 묶기

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")
    with trace("Joke workflow"):
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
```

### BatchTraceProcessor

- 기본 export: 백그라운드에서 몇 초마다 또는 큐 크기 도달 시
- 프로세스 종료 시 자동 flush
- 즉시 전달 보장 필요 시: `flush_traces()` 명시 호출

---

## LangChain / LangGraph — LangSmith

*Source: `langsmith-sdk-readme-2026-06-06`*

LangChain/LangGraph 생태계는 **LangSmith**를 트레이싱 플랫폼으로 사용한다.

### 활성화 환경 변수

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=ls_...
export LANGSMITH_PROJECT="my-project"     # 생략 시 "default"
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # 기본값
```

**주의:** 기존 `LANGCHAIN_TRACING_V2=true` 환경 변수도 지원될 수 있으나 현재 권장 변수는 `LANGSMITH_TRACING=true`.

Source: `langsmith-sdk-readme-2026-06-06`

### LangChain Runnable 자동 tracing

환경 변수 설정만으로 LangChain Runnable 전체가 자동 trace된다. 추가 코드 불필요.

```python
# 환경 변수만 설정하면 invoke/stream/batch 모두 자동 trace
chain = prompt | model | output_parser
chain.invoke({"topic": "AI"})  # → LangSmith에 자동 기록
```

### Run types

| Run type | 해당 항목 |
|---------|----------|
| `llm` | LLM 호출 |
| `chain` | Runnable, graph, agent 실행 |
| `tool` | 도구 호출 |

Source: `langsmith-sdk-readme-2026-06-06`

### `@traceable` 데코레이터 — 비-LangChain 함수 추적

```python
from langsmith import traceable

@traceable
def my_function(text: str) -> str:
    # 이 함수의 입출력이 LangSmith에 자동 기록됨
    return client.chat.completions.create(...)
```

Source: `langsmith-sdk-readme-2026-06-06`

### `wrap_openai` — OpenAI client 자동 추적

```python
from langsmith import wrap_openai
import openai

client = wrap_openai(openai.Client())
# 이후 client 호출이 자동 trace됨
```

### 대시보드

- URL: `https://smith.langchain.com`

---

## LangGraph — 스텝별 디버깅

*Source: `langgraph-source-streaming-2026-05-23`*

LangGraph는 LangSmith와 별도로 `stream_mode="debug"`로 스텝별 상세 정보에 접근할 수 있다.

### stream_mode="debug"

```python
for event in graph.stream(input, stream_mode="debug"):
    # checkpoints + tasks 이벤트 모두 포함
    print(event)
```

- `"debug"` = `"checkpoints"` + `"tasks"` 합집합
- 각 task의 시작/종료, 에러, 체크포인트 저장 시점 추적

### 여러 stream_mode 조합

```python
for namespace, mode, payload in graph.stream(
    input,
    stream_mode=["updates", "debug"],
    subgraphs=True,
):
    print(namespace, mode, payload)
```

### stream_events — LangSmith 연동 대안

```python
async for event in graph.astream_events(input, version="v3"):
    # run.messages, run.values, run.lifecycle 프로젝션
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content)
```

`stream_events`는 LangSmith 없이도 실행 흐름의 typed event를 소비하는 방법이다.
→ [[Event Streaming]] 참조

---

## Deep Agents — tracing

Deep Agents는 LangGraph 기반이므로 **LangSmith 자동 tracing을 상속**한다.
LangSmith 환경 변수 설정 시 `create_deep_agent().invoke()`의 전체 실행이 자동 trace된다.

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=ls_...
```

```python
agent = create_deep_agent(model="anthropic:claude-sonnet-4-6", tools=[...])
agent.invoke({"messages": [...]})  # → LangSmith에 자동 기록
```

**주의:** `deepagents/backends/langsmith.py`는 LangSmith tracing이 아니라 **LangSmith Sandbox** (코드 실행 환경)를 구현한다. tracing과 별개다.

Source: `deepagents-source-backends-sandbox-2026-06-06` (langsmith.py 확인)

### Deep Agents trace 구조 (추정 — 소스 필요)

LangGraph `CompiledStateGraph.invoke()` 호출이기 때문에 다음이 추적될 것으로 예상:
- `chain` run: 전체 graph 실행
- `llm` run: 각 모델 호출
- `tool` run: 각 filesystem tool 호출 + task subagent 호출

⚠️ **미검증**: Deep Agents의 middleware 훅이 LangSmith run 계층 구조에 어떻게 나타나는지 미확인.

---

## 트레이싱 도구 비교

| 도구 | 프레임워크 | 대시보드 | 활성화 |
|------|-----------|----------|--------|
| OpenAI Traces | OpenAI Agents SDK | `platform.openai.com/traces` | 기본 활성화 |
| LangSmith | LangChain / LangGraph / Deep Agents | `smith.langchain.com` | `LANGSMITH_TRACING=true` |
| Langfuse | 범용 | `langfuse.com` | 별도 설치 |
| Arize Phoenix | 범용 | 로컬/클라우드 | 별도 설치 |

---

## Related Pages

- [[Event Streaming]]
- [[Guardrails]]
- [[Evaluation]]
- [[Agent Runtime]]
- [[LangGraph StateGraph compile invoke flow]]

## Open Questions

- LangSmith에서 Deep Agents middleware 훅(before_model, after_model)은 별도 span으로 나타나는가?
- LangSmith run 계층에서 LangGraph subgraph(또는 Deep Agents subagent)는 nested chain run으로 나타나는가?
- `LANGCHAIN_TRACING_V2=true`와 `LANGSMITH_TRACING=true`의 차이 및 현재 권장 변수는?
- `LANGSMITH_PROJECT` 설정 없이 저장되는 기본 프로젝트 이름이 `"default"`인지 확인 필요.

## Sources

- `openai-agents-sdk-tracing-2026-05-23`
- `langsmith-sdk-readme-2026-06-06`
- `langgraph-source-streaming-2026-05-23`
- `deepagents-source-backends-sandbox-2026-06-06`
