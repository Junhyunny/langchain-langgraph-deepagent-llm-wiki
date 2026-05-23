---
source_id: openai-agents-sdk-handoffs-2026-05-23
type: source_summary
framework: OpenAI Agents SDK
status: verified
confidence: high
retrieved_at: 2026-05-23
---

# Source Summary: OpenAI Agents SDK — Handoffs

## Key Facts

- 핸드오프는 에이전트가 다른 에이전트에게 작업을 **위임**할 수 있게 한다.
- **핸드오프는 LLM에게 도구(tool)로 표현된다.** `Refund Agent`로의 핸드오프는 `transfer_to_refund_agent` 도구가 된다.
- `Agent.handoffs` 파라미터로 설정 — `Agent` 직접 전달 또는 `Handoff` 객체.
- `handoff()` 함수 주요 파라미터:
  - `agent`: 대상 에이전트
  - `tool_name_override`: 기본값 `transfer_to_<agent_name>`
  - `on_handoff`: 핸드오프 호출 시 콜백 (로깅, 데이터 페칭 등)
  - `input_type`: 핸드오프 tool call 인수 스키마 (model-generated metadata)
  - `input_filter`: 수신 에이전트가 받는 입력 필터링
  - `is_enabled`: boolean 또는 함수 — 런타임에 동적 활성화/비활성화
- `input_type`은 model이 핸드오프 시 생성하는 소규모 메타데이터용 (reason, language, priority 등).
- `input_type`은 수신 에이전트의 메인 입력을 교체하지 않는다 — 히스토리는 `input_filter`로 제어.
- 히스토리 제어: `RunConfig.nest_handoff_history`, `RunConfig.handoff_history_mapper`.

## Interpretation

- 핸드오프는 "특별한 tool call"로 구현된다 — LLM이 명시적으로 선택해야 함.
- 서브에이전트 호출(`Agent.as_tool()`)과의 차이: 핸드오프는 단방향 제어 이전, as_tool은 결과 반환.
- LangGraph의 `Command(goto=...)` 패턴과 유사하나, OpenAI SDK는 LLM이 tool call로 핸드오프를 트리거한다.

## Open Questions

- LangGraph / LangChain에서 동등한 핸드오프 구현은 무엇인가?
- Deep Agents에서 핸드오프는 어떻게 구현되는가? subagent tool과 동일한가?
- `input_filter`의 구체적인 사용 패턴은?

## Sources
- `openai-agents-sdk-handoffs-2026-05-23`
