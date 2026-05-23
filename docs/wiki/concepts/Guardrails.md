---
type: concept
framework:
  - OpenAI Agents SDK
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - openai-agents-sdk-guardrails-2026-05-23
---

# Guardrails

## Summary

가드레일은 에이전트의 **입력과 출력**에 대한 유효성 검사, 정책 준수, 안전성 보장을 위한 안전장치다. 가드레일이 위반을 감지하면 에이전트 실행을 즉시 중단(tripwire)할 수 있다.

## Why It Matters

LLM은 악의적인 입력(예: 금지된 작업 요청)이나 잘못된 출력(예: 스키마 불일치, 유해 콘텐츠)을 스스로 필터링하지 않는다. 가드레일은 이를 별도의 레이어로 분리하여 안전성과 일관성을 보장한다. 비용이 큰 모델을 빠른 가드레일 모델로 사전 필터링하면 토큰 낭비도 방지할 수 있다.

## Key Concepts

- **Input Guardrail** — 사용자 입력 검증
- **Output Guardrail** — 에이전트 최종 출력 검증
- **Tool Guardrail** — 함수 도구 호출 전후 검증
- **Tripwire** — 가드레일 위반 신호. 발동 시 에이전트 실행 즉시 중단
- **Parallel vs Blocking** — 가드레일 실행 타이밍 제어

## OpenAI Agents SDK

*Source: `openai-agents-sdk-guardrails-2026-05-23`*

### 세 가지 가드레일 종류

| 종류 | 시점 | 위치 |
|------|------|------|
| Input Guardrail | 사용자 입력 도착 시 | 체인의 **첫 번째 에이전트**에서만 실행 |
| Output Guardrail | 에이전트 출력 생성 후 | **최종 출력 에이전트**에서만 실행 |
| Tool Guardrail | function tool 호출 전/후 | **모든 function tool 호출마다** 실행 |

### 실행 모드 (Input Guardrail)

```
run_in_parallel=True (기본)
  → 에이전트와 동시 실행
  → 지연 최소화
  → 단점: 가드레일 실패 시 에이전트가 이미 토큰 소비

run_in_parallel=False (blocking)
  → 가드레일 완료 후 에이전트 시작
  → tripwire 시 에이전트 미실행 → 비용 절약
  → 단점: 레이턴시 증가
```

### Tripwire 메커니즘

```
GuardrailFunctionOutput(tripwire_triggered=True)
     ↓
InputGuardrailTripwireTriggered / OutputGuardrailTripwireTriggered 예외
     ↓
에이전트 실행 즉시 중단
```

### 구현 패턴

```python
from pydantic import BaseModel
from agents import Agent, GuardrailFunctionOutput, Runner, RunContextWrapper, input_guardrail

class PolicyCheck(BaseModel):
    violation: bool
    reason: str

check_agent = Agent(
    name="Policy checker",
    instructions="Check if the request violates our content policy.",
    output_type=PolicyCheck,
)

@input_guardrail
async def policy_guardrail(ctx, agent, input) -> GuardrailFunctionOutput:
    result = await Runner.run(check_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.violation,
    )

agent = Agent(
    name="Main agent",
    instructions="Help users with their requests.",
    input_guardrails=[policy_guardrail],
)
```

### Tool guardrail 적용 범위

- ✅ `@function_tool` / `function_tool()` 로 생성한 도구
- ❌ 핸드오프
- ❌ Hosted tools (`WebSearchTool`, `FileSearchTool` 등)
- ❌ Built-in tools (`ComputerTool`, `ShellTool` 등)

## LangGraph

*Source: Needs Source*

LangGraph에는 전용 Guardrail API가 없다. ⚠️ 동등한 패턴으로는:

- **입력 검증**: 첫 번째 노드에서 조건 체크 후 `Command(goto=END)` 또는 오류 상태 반환
- **출력 검증**: `with_structured_output`으로 스키마 강제
- **미들웨어 패턴**: 노드 앞뒤에 validation 노드 삽입

*정확한 구현 패턴은 소스 탐구 필요*

## Deep Agents

*Source: Needs Source*

Deep Agents는 Middleware 기반 아키텍처를 사용한다.
- `PatchToolCallsMiddleware`처럼 전처리/후처리 미들웨어로 가드레일 역할을 수행할 가능성 있음 (⚠️ 가설)
- 전용 `InputGuardrail` / `OutputGuardrail` 클래스 존재 여부는 미확인

## 다른 가드레일 패턴들

| 패턴 | 설명 |
|------|------|
| **키워드 필터링** | 금칙어 포함 여부 검사 |
| **JSON 스키마 검증** | 출력 구조 강제 (`with_structured_output`) |
| **LLM-as-Judge 가드레일** | 별도 LLM이 입출력을 검사 (비용이 큰 패턴) |
| **RAG Prompt Injection 방어** | 검색 문서 내 악성 지시 필터링 |

## Related Pages

- [[Agent Runtime]]
- [[Tool Calling]]
- [[RAG]]
- [[Subagents]]

## Open Questions

- LangGraph에서 표준 가드레일 패턴은 무엇인가? — Needs Source
- Deep Agents에 전용 가드레일 API가 있는가? — Needs Source
- 가드레일로 구현한 LLM-as-Judge 패턴의 비용/지연 트레이드오프는?

## Sources

- `openai-agents-sdk-guardrails-2026-05-23`
