---
type: concept
framework:
  - OpenAI Agents SDK
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - openai-agents-sdk-tracing-2026-05-23
---

# Tracing

## Summary

트레이싱은 에이전트 실행 흐름을 기록하고 시각화하여 디버깅 및 성능 최적화에 활용하는 메커니즘이다. LLM 생성, 도구 호출, 핸드오프, 가드레일 등 각 스텝의 input/output을 추적한다.

## Why It Matters

에이전트 시스템은 여러 LLM 호출, 도구 호출, 에이전트 전환이 중첩되어 동작한다. 트레이싱 없이는 어느 단계에서 무엇이 일어났는지 파악하기 어렵다. 트레이싱은 디버깅, 성능 최적화, 이상 감지, 비용 분석에 필수다.

## Key Concepts

- **Trace** — 단일 엔드투엔드 워크플로우 단위
- **Span** — 시작/종료 시각이 있는 개별 작업 단위
- **Span Types** — agent, generation, tool, guardrail, handoff 등
- **Trace Processor** — trace를 목적지(대시보드, 외부 시스템)로 전송하는 컴포넌트

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

### Custom Span

```python
from agents import custom_span

with custom_span("my_custom_operation"):
    # 커스텀 작업
    pass
```

## LangGraph / LangChain (LangSmith)

*Source: Needs Source*

LangChain/LangGraph 생태계는 **LangSmith**를 트레이싱 플랫폼으로 사용한다.

**알려진 사항:**
- `LANGCHAIN_TRACING_V2=true` 환경 변수로 활성화 (⚠️ 미검증)
- LangGraph `stream_mode="debug"`로 스텝별 상세 정보 접근 가능 (⚠️ Needs Source)
- LangSmith는 LangChain/LangGraph와 자동 instrumentation

**미확인 사항:**
- LangSmith span 타입 목록
- Deep Agents와의 통합 방식

## Deep Agents

*Source: Needs Source*

Deep Agents는 LangGraph 기반이므로 LangSmith 트레이싱을 상속할 가능성 높음 (⚠️ 가설).
OpenAI Agents SDK 트레이싱 사용 여부는 미확인.

## 트레이싱 도구 비교

| 도구 | 프레임워크 | 대시보드 |
|------|-----------|----------|
| OpenAI Traces | OpenAI Agents SDK | `platform.openai.com/traces` |
| LangSmith | LangChain / LangGraph | `smith.langchain.com` |
| Langfuse | 범용 | `langfuse.com` |
| Arize Phoenix | 범용 | 로컬/클라우드 |

## Related Pages

- [[Agent Runtime]]
- [[Guardrails]]
- [[Handoffs]]
- [[Event Streaming]]
- [[Evaluation]]

## Open Questions

- LangGraph의 스텝별 input/output을 프로그래밍 방식으로 접근하는 API는? — Needs Source
- Deep Agents는 LangSmith와 OpenAI SDK 트레이싱 중 어느 것을 사용하는가? — Needs Source
- LangSmith trace의 span 타입 목록은? — Needs Source

## Sources

- `openai-agents-sdk-tracing-2026-05-23`
