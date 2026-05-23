---
source_id: openai-agents-sdk-tracing-2026-05-23
type: source_summary
framework: OpenAI Agents SDK
status: verified
confidence: high
retrieved_at: 2026-05-23
---

# Source Summary: OpenAI Agents SDK — Tracing

## Key Facts

- 트레이싱은 **기본 활성화**됨. 3가지 비활성화 방법: env var, 코드(`set_tracing_disabled`), `RunConfig.tracing_disabled`.
- **Trace**: 단일 엔드투엔드 워크플로우 단위. 속성: `workflow_name`, `trace_id`, `group_id`, `disabled`, `metadata`.
- **Span**: 시작/종료 시각이 있는 작업 단위. 속성: `started_at`, `ended_at`, `trace_id`, `parent_id`, `span_data`.
- 기본 자동 트레이싱 대상:
  - `Runner.run()` 전체 → `trace()`
  - 에이전트 실행 → `agent_span()`
  - LLM 생성 → `generation_span()`
  - 함수 tool 호출 → `function_span()`
  - 가드레일 → `guardrail_span()`
  - 핸드오프 → `handoff_span()`
  - 음성 인식 → `transcription_span()` / `speech_span()`
- `BatchTraceProcessor`(기본): 백그라운드에서 몇 초마다 또는 큐 크기 도달 시 export. 프로세스 종료 시 flush.
- 즉시 전달 보장: `flush_traces()` 호출.
- 여러 `run()` 호출을 하나의 trace로 묶으려면 `with trace("name"):` 사용.
- `custom_span()`으로 커스텀 span 추가 가능.
- Custom trace processor로 다른 목적지에 trace 전송 가능.

## Interpretation

- OpenAI Agents SDK의 트레이싱은 `platform.openai.com/traces` 대시보드 전용.
- LangChain/LangGraph는 LangSmith를 사용하는 다른 트레이싱 체계를 가진다.
- Deep Agents가 LangGraph 기반이라면 LangSmith 통합이 기본일 수 있음 (가설).

## Open Questions

- LangGraph/LangChain의 트레이싱은 어떤 span 타입을 기본 지원하는가?
- Deep Agents는 OpenAI SDK 트레이싱을 사용하는가, LangSmith를 사용하는가?

## Sources
- `openai-agents-sdk-tracing-2026-05-23`
