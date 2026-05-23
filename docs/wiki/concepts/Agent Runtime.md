---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
  - OpenAI Agents SDK
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - openai-agents-sdk-agent-overview-2026-05-23
  - openai-agents-sdk-running-agents-2026-05-23
---

# Agent Runtime

## Summary

에이전트 런타임은 **모델(Model)**, **오케스트레이션(Orchestration)**, **도구(Tools)** 세 가지를 묶은 실행 환경이다. LLM 단독으로는 에이전트가 아니다 — 이 세 요소가 결합되어야 에이전트로서 동작할 수 있다.

## Why It Matters

런타임이 무엇인지 이해하면 각 프레임워크가 어떤 문제를 해결하고, 어떤 부분을 개발자에게 위임하는지 파악할 수 있다. 프레임워크를 선택하거나 성능/안전성 이슈를 디버깅할 때 런타임 구조를 알아야 한다.

## Key Concepts

- [[모델 (Model)]]
- [[오케스트레이션 (Orchestration)]]
- [[Tool Calling]]
- [[Memory]]
- [[Reasoning and Planning]]
- [[Guardrails]]
- [[Handoffs]]

## 에이전트 런타임 구성 요소

### 1. 모델 (Model)

에이전트의 두뇌. 추론, 계획, 도구 선택, 최종 응답 생성을 담당한다.

- 어떤 LLM을 사용하는가 (GPT, Claude, Gemini 등)
- 모델 설정 (`temperature`, `top_p`, `tool_choice` 등)
- 에이전트 프레임워크는 모델을 직접 호출하지 않고 추상화 레이어를 통해 호출한다

### 2. 오케스트레이션 (Orchestration)

여러 시스템, 서비스, 에이전트를 조율하고 실행 흐름을 관리하는 레이어다.

오케스트레이션 레이어의 주요 구성 요소:

| 구성 요소 | 설명 |
|----------|------|
| **인스트럭션 (Instructions)** | 개발자가 LLM에게 역할과 동작 방식을 지시하는 프롬프트. 기존의 "시스템 프롬프트"와 동일한 개념. |
| **메모리 (Memory)** | 에이전트의 경험/지식 저장소. 수행 이력, 컨텍스트, 과거 대화 유지. 이전 작업의 맥락을 다음 작업에 전달. |
| **리즈닝/플래닝 (Reasoning/Planning)** | LLM이 현재 상황을 추론하고 요청 해결 계획을 세우는 단계. |
| **가드레일 (Guardrails)** | 입출력 필터링으로 안전성과 일관성 보장. |
| **핸드오프 (Handoffs)** | 상황에 따라 다른 에이전트로 제어를 이전. |
| **트레이싱 (Tracing)** | 실행 흐름 기록 및 시각화. |

### 3. 도구 (Tools)

코드 실행, 웹 브라우저, API 호출 등 **외부 기능**과 LLM을 연결한다.

- 도구 없이는 LLM이 외부 세계에 영향을 미치거나 정보를 가져올 수 없다
- 각 도구는 이름, 설명, 입력 스키마를 가지며 LLM이 선택적으로 호출한다

## 프레임워크별 구현

### OpenAI Agents SDK

*Source: `openai-agents-sdk-agent-overview-2026-05-23`, `openai-agents-sdk-running-agents-2026-05-23`*

| 런타임 요소 | 구현 |
|------------|------|
| 모델 | `Agent.model` + `Agent.model_settings` |
| 오케스트레이션 | `Runner` 클래스 (agent loop: LLM → final_output / handoff / tool_calls) |
| 인스트럭션 | `Agent.instructions` (str 또는 동적 콜백) |
| 도구 | `Agent.tools` |
| 가드레일 | `Agent.input_guardrails` / `Agent.output_guardrails` |
| 핸드오프 | `Agent.handoffs` |
| 메모리 | `context` DI 객체 (세션 내), 외부 저장소 (세션 간) |
| 실행 설정 | `RunConfig` (model, tracing, handoff history 등) |

**Agent loop (Runner):**
```
1. LLM 호출
2. 출력 분기:
   - final_output → 루프 종료
   - handoff → 다음 에이전트로 제어 이전 후 재실행
   - tool_calls → 도구 실행 → 결과 추가 → 재실행
3. max_turns 초과 → MaxTurnsExceeded 예외
```

### LangGraph

*Source: 별도 탐구 필요*

| 런타임 요소 | 구현 |
|------------|------|
| 모델 | `ChatModel` (LangChain provider) |
| 오케스트레이션 | `StateGraph` + `Pregel` 실행 엔진 |
| 인스트럭션 | `SystemMessage` 또는 `@dynamic_prompt` 미들웨어 |
| 도구 | `@tool` 데코레이터 또는 `StructuredTool` |
| 가드레일 | 표준 API 없음 (⚠️ Needs Source) |
| 핸드오프 | `Command(goto=...)` 또는 subgraph 전환 |
| 메모리 | Checkpointer (단기) + Store (장기) |

### Deep Agents

*Source: 별도 탐구 필요*

| 런타임 요소 | 구현 |
|------------|------|
| 모델 | LangGraph 위임 |
| 오케스트레이션 | `create_deep_agent()` → `langchain.agents.create_agent` 위임 |
| 인스트럭션 | `BASE_AGENT_PROMPT` + `HarnessProfile.base_system_prompt` |
| 도구 | filesystem tools + custom tools (harness 기반) |
| 가드레일 | Middleware 기반 (⚠️ 전용 가드레일 API 미확인) |
| 핸드오프 | subagent tool call 방식 |
| 메모리 | `MemoryMiddleware`, `CompositeBackend` |

## Source Code References

- OpenAI Agents SDK: `agents/agent.py`, `agents/run.py`
- LangGraph: `libs/langgraph/langgraph/graph/state.py`, `libs/langgraph/langgraph/pregel/__init__.py`
- Deep Agents: `src/deepagents/graph.py`

## Tests

- Needs Source

## Related Pages

- [[Tool Calling]]
- [[Memory]]
- [[Checkpointing]]
- [[Guardrails]]
- [[Handoffs]]
- [[Tracing]]
- [[Reasoning and Planning]]
- [[Agent Harness]]
- [[Subagents]]

## Open Questions

- LangGraph에서 에이전트 런타임의 가드레일은 어떻게 구현하는가?
- Deep Agents의 `create_deep_agent`에서 Reasoning/Planning 단계는 별도로 존재하는가?
- 에이전트 런타임의 세 구성요소(모델+오케스트레이션+도구)는 각 프레임워크에서 어떤 클래스에 매핑되는가?

## Sources

- `openai-agents-sdk-agent-overview-2026-05-23`
- `openai-agents-sdk-running-agents-2026-05-23`
