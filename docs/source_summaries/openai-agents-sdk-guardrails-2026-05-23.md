---
source_id: openai-agents-sdk-guardrails-2026-05-23
type: source_summary
framework: OpenAI Agents SDK
status: verified
confidence: high
retrieved_at: 2026-05-23
---

# Source Summary: OpenAI Agents SDK — Guardrails

## Key Facts

- 가드레일은 **사용자 입력**과 **에이전트 출력**에 대한 검사/검증을 수행한다.
- 세 종류: `InputGuardrail`, `OutputGuardrail`, `Tool Guardrail`.
- **워크플로우 경계**:
  - Input guardrail → 체인의 **첫 번째 에이전트**에서만 실행.
  - Output guardrail → **최종 출력 에이전트**에서만 실행.
  - Tool guardrail → **모든 function tool 호출마다** 실행.
- Input guardrail 실행 모드:
  - `run_in_parallel=True` (기본): 에이전트와 동시 실행. 지연 최소화.
  - `run_in_parallel=False`: 에이전트 **시작 전** 완료. 트리거 시 에이전트 미실행. 비용 최적화.
- Output guardrail은 항상 에이전트 완료 후 실행 → `run_in_parallel` 미지원.
- Tripwire 발동 시 즉시 `{Input,Output}GuardrailTripwireTriggered` 예외 → 에이전트 실행 중단.
- 가드레일은 `@input_guardrail` / `@output_guardrail` 데코레이터로 구현.
- 반환 타입: `GuardrailFunctionOutput(output_info=..., tripwire_triggered=bool)`.
- Tool guardrail은 `function_tool`로 생성한 도구에만 적용. 핸드오프/hosted tool/built-in tool에는 미적용.

## Interpretation

- 가드레일은 에이전트 레벨에 직접 부착되어(colocated) 가독성이 높다.
- 병렬 실행(기본값)은 지연을 줄이지만 비용 낭비 가능성 있음.
- 차단 실행(`run_in_parallel=False`)은 안전하지만 레이턴시 증가.
- 가드레일 자체가 LLM 에이전트(`guardrail_agent`)로 구현될 수 있다 → 분류/정책 판단.

## Open Questions

- LangGraph/LangChain에서 동등한 가드레일 패턴은 무엇인가?
- Deep Agents의 middleware와 OpenAI Agents SDK 가드레일 간 역할 비교는?

## Sources
- `openai-agents-sdk-guardrails-2026-05-23`
