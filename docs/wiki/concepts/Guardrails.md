---
type: concept
framework:
  - OpenAI Agents SDK
  - LangChain
  - LangGraph
  - Deep Agents
status: verified
confidence: high
last_reviewed: 2026-06-06
sources:
  - openai-agents-sdk-guardrails-2026-05-23
  - langchain-source-builtin-middleware-2026-05-25
  - langgraph-prebuilt-tool-node-2026-05-27
  - deepagents-source-filesystem-middleware-2026-06-06
---

# Guardrails

## Summary

가드레일은 에이전트의 **입력과 출력**에 대한 유효성 검사, 정책 준수, 안전성 보장을 위한 안전장치다. 가드레일이 위반을 감지하면 에이전트 실행을 즉시 중단(tripwire)할 수 있다.

## Why It Matters

LLM은 악의적인 입력(예: 금지된 작업 요청)이나 잘못된 출력(예: 스키마 불일치, 유해 콘텐츠)을 스스로 필터링하지 않는다. 가드레일은 이를 별도의 레이어로 분리하여 안전성과 일관성을 보장한다.

## Key Concepts

- **Input Guardrail** — 사용자 입력 검증
- **Output Guardrail** — 에이전트 최종 출력 검증
- **Tool Guardrail** — 함수 도구 호출 전후 검증
- **Tripwire** — 가드레일 위반 신호. 발동 시 에이전트 실행 즉시 중단
- **Parallel vs Blocking** — 가드레일 실행 타이밍 제어

---

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
from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail
from pydantic import BaseModel

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
```

### Tool guardrail 적용 범위

- ✅ `@function_tool` / `function_tool()`으로 생성한 도구
- ❌ 핸드오프
- ❌ Hosted tools (`WebSearchTool`, `FileSearchTool` 등)
- ❌ Built-in tools (`ComputerTool`, `ShellTool` 등)

---

## LangChain

*Source: `langchain-source-builtin-middleware-2026-05-25`*

LangChain에는 전용 `Guardrail` 클래스가 없다. **AgentMiddleware 훅**으로 동등한 기능을 구현한다.

### Input Guardrail — `before_model` 훅

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

# PIIMiddleware: 가장 완성된 Input Guardrail 구현 예시
agent = create_agent(
    "openai:gpt-5",
    middleware=[PIIMiddleware("email", strategy="block")],
)
```

- `before_model(state, runtime)` — 모델 호출 **전** 마지막 HumanMessage + ToolMessage 검사
- `@hook_config(can_jump_to=["end"])` — `strategy="block"` 시 탐지 즉시 에이전트 종료 (tripwire 등가)

### Output Guardrail — `after_model` 훅

```python
PIIMiddleware("email", strategy="redact", apply_to_output=True)
```

- `after_model(state, runtime)` — 모델이 생성한 마지막 AIMessage 검사
- 기본값 `apply_to_output=False` — 출력 필터링은 명시적으로 켜야 함

### Tool Guardrail — `wrap_tool_call` 훅

```python
class AccessControlMiddleware(AgentMiddleware):
    def wrap_tool_call(self, request, handler):
        if request.tool_call["name"] in self.blocked_tools:
            return ToolMessage(content="Access denied", ...)
        return handler(request)
```

- `wrap_tool_call(request, handler)` — tool 실행 **전** 권한 검사 가능
- `wrap_model_call(request, handler)` — 모델 호출 전후 입출력 검사

### 도구 접근 제한 — `LLMToolSelectorMiddleware`

```python
from langchain.agents.middleware import LLMToolSelectorMiddleware
# 모델이 전체 도구 목록에서 현재 쿼리와 관련 있는 도구만 선택
```

- 관련 없는 도구를 모델에서 숨김 → 의도치 않은 tool 호출 방지
- 도구 접근 가드레일의 한 형태

Source: `langchain-source-builtin-middleware-2026-05-25`

### 빌트인 미들웨어 vs 직접 구현 비교

| 패턴 | 미들웨어 | 훅 | 검증 방식 |
|------|---------|-----|----------|
| PII 입력 필터링 | `PIIMiddleware` | `before_model` | regex + Luhn |
| PII 출력 필터링 | `PIIMiddleware` | `after_model` | regex |
| 도구 선택 제한 | `LLMToolSelectorMiddleware` | `wrap_model_call` | LLM 선택 |
| 커스텀 가드레일 | 직접 `AgentMiddleware` 구현 | 모든 훅 | 자유 |

---

## LangGraph

LangGraph에는 전용 Guardrail API가 없다. **그래프 구조**와 **structured output**으로 동등한 패턴을 구현한다.

### Input Guardrail — 첫 노드에서 조건 분기

```python
from langgraph.graph import StateGraph, END

def validate_input(state):
    if contains_pii(state["messages"][-1].content):
        return Command(update={"error": "PII detected"}, goto=END)
    return state

builder = StateGraph(State)
builder.add_node("validate", validate_input)
builder.add_node("agent", run_agent)
builder.set_entry_point("validate")
builder.add_conditional_edges("validate", route_after_validation)
```

### Output Guardrail — `with_structured_output`

```python
class SafeResponse(BaseModel):
    content: str
    safe: bool = True

# 스키마를 강제해 구조 외 출력 방지
model = ChatAnthropic(...).with_structured_output(SafeResponse)
```

### Tool Guardrail — 커스텀 ToolNode 래핑

```python
# ToolNode에 wrap_tool_call= 파라미터로 커스텀 래퍼 주입 가능
from langgraph.prebuilt import ToolNode

def guardrail_wrapper(request, handler):
    # 실행 전 권한 검사
    return handler(request)

tool_node = ToolNode(tools, wrap_tool_call=guardrail_wrapper)
```

*Source: `langgraph-prebuilt-tool-node-2026-05-27` (소스 코드 기준 — 공식 문서 예제 미확인)*

---

## Deep Agents

*Source: `langchain-source-builtin-middleware-2026-05-25`, `deepagents-source-filesystem-middleware-2026-06-06`*

Deep Agents는 LangChain middleware 시스템을 직접 사용하므로, LangChain의 모든 가드레일 패턴이 그대로 적용된다.

### 빌트인 가드레일

| 미들웨어 | 가드레일 역할 |
|---------|-------------|
| `PIIMiddleware` | 입출력 PII 필터링, `strategy="block"` 시 에이전트 중단 |
| `FilesystemPermission` | 경로 접근 제어 (`allow/deny/interrupt`) |
| `LLMToolSelectorMiddleware` | 모델에 노출되는 도구 동적 제한 |

### FilesystemPermission — 파일 접근 가드레일

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    permissions=[
        {"operations": ["write"], "paths": ["**/*.secret", ".env"], "mode": "deny"},
        {"operations": ["read", "write"], "paths": ["/workspace/**"], "mode": "allow"},
    ],
)
```

- first-match-wins, 기본 allow
- `mode: "interrupt"` — Human-in-the-Loop 승인 요청

Source: `deepagents-source-filesystem-middleware-2026-06-06`

### 커스텀 가드레일 미들웨어

```python
class ContentPolicyMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        # 모델 호출 전 입력 검사
        last_message = request.messages[-1]
        if violates_policy(last_message.content):
            raise PolicyViolationError("Content policy violated")
        response = handler(request)
        # 모델 출력 검사
        if violates_policy(response.messages[-1].content):
            raise PolicyViolationError("Output policy violated")
        return response

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    middleware=[ContentPolicyMiddleware()],
)
```

---

## 프레임워크 비교

| 항목 | OpenAI Agents SDK | LangChain | LangGraph | Deep Agents |
|------|-----------------|-----------|-----------|-------------|
| 전용 Guardrail API | ✅ `@input_guardrail` | ❌ (middleware로 구현) | ❌ (graph로 구현) | ❌ (middleware로 구현) |
| Input 가드레일 | `@input_guardrail` | `before_model` hook | 첫 노드 조건 분기 | `before_model` hook |
| Output 가드레일 | `@output_guardrail` | `after_model` hook | `with_structured_output` | `after_model` hook |
| Tool 가드레일 | `@tool_guardrail` | `wrap_tool_call` hook | `ToolNode(wrap_tool_call=...)` | `wrap_tool_call` hook |
| 파일 접근 제어 | ❌ | ❌ | ❌ | `FilesystemPermission` |
| 병렬 실행 | `run_in_parallel=True` | N/A | N/A | N/A |
| Tripwire | `tripwire_triggered=True` | `strategy="block"` + `can_jump_to` | `goto=END` | 동일 |

---

## Related Pages

- [[PIIMiddleware]]
- [[FilesystemMiddleware]]
- [[Agent Runtime]]
- [[Tool Calling]]
- [[HumanInTheLoop]]
- [[LangChain create_agent flow]]

## Open Questions

- LangGraph에서 `ToolNode(wrap_tool_call=...)` 패턴으로 실제 guardrail을 구현한 공식 예제가 있는가?
- Deep Agents에 `PIIMiddleware` 외의 전용 가드레일 미들웨어가 있는가?
- LangSmith에서 가드레일 위반을 별도 run type으로 추적하는 방법이 있는가?

## Sources

- `openai-agents-sdk-guardrails-2026-05-23`
- `langchain-source-builtin-middleware-2026-05-25`
- `langgraph-prebuilt-tool-node-2026-05-27`
- `deepagents-source-filesystem-middleware-2026-06-06`
