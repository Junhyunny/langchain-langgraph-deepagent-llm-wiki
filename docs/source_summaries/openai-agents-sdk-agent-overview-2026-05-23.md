---
source_id: openai-agents-sdk-agent-overview-2026-05-23
type: source_summary
framework: OpenAI Agents SDK
status: verified
confidence: high
retrieved_at: 2026-05-23
---

# Source Summary: OpenAI Agents SDK — Agent Overview

## Key Facts

- `Agent`는 LLM + instructions + tools + handoffs/guardrails/output_type 등 선택적 런타임 동작을 설정한 객체다.
- `Runner` 클래스가 turns, tools, guardrails, handoffs, sessions를 관리한다.
- `instructions`는 시스템 프롬프트 또는 동적 콜백이다. 강력히 권장됨.
- `handoffs` 파라미터로 Agent 직접 전달 또는 `Handoff` 객체를 전달할 수 있다.
- `input_guardrails` / `output_guardrails` 파라미터가 에이전트에 직접 부착된다.
- `output_type`으로 구조화 출력(Pydantic, dataclass, TypedDict 등)을 지정할 수 있다.
- `context`는 의존성 주입(DI) 도구로, `Runner.run()`에 전달하면 모든 agent/tool/handoff에 전달된다.
- `tool_use_behavior`로 tool 결과가 모델에 다시 전달되는지 제어한다.
- `reset_tool_choice=True`(기본값): tool 호출 후 `tool_choice` 리셋 → tool 루프 방지.

## Interpretation

- `Agent` 객체는 에이전트 런타임의 "설정 명세서"에 해당한다. `Runner`가 실제 실행 루프를 담당한다.
- `instructions`가 오케스트레이션 레이어에서 개발자가 LLM에게 주는 프롬프트(인스트럭션)에 해당한다.
- `context`는 LangGraph의 `State`와 유사하지만, 상태 그래프가 아닌 DI 패턴으로 구현된 차이가 있다.

## Open Questions

- Deep Agents는 `Agent` 클래스를 어떻게 확장하거나 래핑하는가?
- `SandboxAgent`는 `Agent`와 어떤 추가 속성을 가지는가?

## Sources
- `openai-agents-sdk-agent-overview-2026-05-23`
