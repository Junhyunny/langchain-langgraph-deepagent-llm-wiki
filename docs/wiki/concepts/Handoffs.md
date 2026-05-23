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
  - openai-agents-sdk-handoffs-2026-05-23
---

# Handoffs

## Summary

핸드오프는 한 에이전트가 다른 에이전트에게 **제어를 이전**하는 메커니즘이다. 핸드오프를 받은 에이전트는 남은 작업을 이어서 처리한다. 이는 서브에이전트 도구 호출(결과를 반환)과 달리 **단방향 제어 이전**이다.

## Why It Matters

복잡한 멀티 에이전트 시스템에서 각 에이전트가 전문화된 역할을 맡는다. 핸드오프는 오케스트레이터 에이전트가 적절한 전문 에이전트로 작업을 넘기는 패턴이다. 핸드오프 vs 서브에이전트 호출의 차이를 이해하면 올바른 패턴을 선택할 수 있다.

## Key Concepts

- **Handoff** — 에이전트 간 단방향 제어 이전
- **Tool as Handoff** — 핸드오프가 LLM에게 도구로 노출됨
- **Input Filter** — 수신 에이전트가 받는 히스토리/컨텍스트 필터링
- **on_handoff callback** — 핸드오프 발생 시 실행되는 콜백

## Handoff vs Subagent Tool Call

| 특성 | 핸드오프 | 서브에이전트 도구 호출 |
|------|----------|----------------------|
| 제어 흐름 | 단방향 이전 (돌아오지 않음) | 결과를 부모에게 반환 |
| 구현 방식 | 특별한 tool call | 일반 tool call |
| 사용 시점 | 전체 대화를 다른 전문가에게 넘길 때 | 하위 작업만 위임할 때 |
| 히스토리 | 기본적으로 이전됨 (`input_filter`로 제어) | 부모-자식 간 상태 격리 |

## OpenAI Agents SDK

*Source: `openai-agents-sdk-handoffs-2026-05-23`*

### 핵심 구현

**핸드오프는 LLM에게 tool로 표현된다:**
- `Refund Agent`로의 핸드오프 → `transfer_to_refund_agent` 도구
- LLM이 이 도구를 선택하면 핸드오프 실행

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

# 간단한 방식: Agent 직접 전달
# 커스텀 방식: handoff() 함수 사용
triage_agent = Agent(
    name="Triage agent",
    handoffs=[billing_agent, handoff(refund_agent)]
)
```

### `handoff()` 함수 파라미터

| 파라미터 | 설명 |
|----------|------|
| `agent` | 대상 에이전트 |
| `tool_name_override` | 기본값: `transfer_to_<agent_name>` |
| `tool_description_override` | 도구 설명 override |
| `on_handoff` | 핸드오프 호출 시 콜백 |
| `input_type` | 핸드오프 tool call 인수 스키마 |
| `input_filter` | 수신 에이전트가 받는 입력 필터 |
| `is_enabled` | 런타임 활성화/비활성화 (bool 또는 함수) |

### 핸드오프 시 메타데이터 전달 (`input_type`)

모델이 핸드오프 시 생성하는 소규모 메타데이터 (reason, priority 등):

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str
    priority: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalating because: {input_data.reason} (priority: {input_data.priority})")

handoff_obj = handoff(
    agent=Agent(name="Escalation agent"),
    on_handoff=on_handoff,
    input_type=EscalationData,
)
```

### 히스토리 제어

- 기본적으로 수신 에이전트는 이전 대화 히스토리를 받는다
- `input_filter`로 히스토리 필터링 가능
- `RunConfig.nest_handoff_history` / `RunConfig.handoff_history_mapper`로 전역 제어

## LangGraph

*Source: Needs Source*

LangGraph에서 핸드오프에 해당하는 패턴:

- **`Command(goto="node_name")`**: 다른 노드로 제어를 이전. 현재 노드에서 직접 goto 지정.
- **`add_conditional_edges`**: 조건에 따라 다음 에이전트 노드를 선택.
- **서브그래프 전환**: 컴파일된 그래프를 다른 그래프의 노드로 추가.

⚠️ LangGraph의 핸드오프는 OpenAI SDK처럼 LLM이 tool call로 트리거하는 것이 아니라, 노드 반환값이나 조건 에지로 구현된다.

## Deep Agents

*Source: Needs Source*

Deep Agents의 subagent는 도구 호출 방식이므로 OpenAI SDK의 "서브에이전트 도구 호출"에 가깝다. 진정한 핸드오프(단방향 제어 이전)와의 차이 탐구 필요.

- `_EXCLUDED_STATE_KEYS`로 입출력 상태를 격리함 → 히스토리 전달 제한적
- 결과(`AIMessage` 또는 `structured_response`)를 부모에게 반환함 → 핸드오프보다 도구 호출에 가까움

## Related Pages

- [[Agent Runtime]]
- [[Subagents]]
- [[StateGraph]]
- [[Tool Calling]]

## Open Questions

- LangGraph에서 LLM이 tool call로 핸드오프를 트리거하는 패턴은 존재하는가? — Needs Source
- Deep Agents에서 진정한 핸드오프(단방향 제어 이전)를 구현하는 방법은? — Needs Source
- `input_filter`의 구체적인 사용 패턴과 예시는? — Needs Source

## Sources

- `openai-agents-sdk-handoffs-2026-05-23`
