---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
  - OpenAI Agents SDK
status: partial
confidence: medium
last_reviewed: 2026-06-06
sources:
  - langgraph-prebuilt-chat-agent-executor-2026-05-28
  - langchain-agents-factory-2026-05-28
  - openai-agents-sdk-running-agents-2026-05-23
  - openai-agents-sdk-agent-overview-2026-05-23
  - deepagents-source-graph-2026-05-19
  - deepagents-docs-harness-2026-05-19
---

# Reasoning and Planning

## Summary

리즈닝(Reasoning)은 LLM이 현재 상황을 이해하고 추론하는 능력이고, 플래닝(Planning)은 주어진 요청을 해결하기 위한 계획을 세우는 능력이다. 이 두 능력은 에이전트가 단순한 질답을 넘어 복잡한 다단계 문제를 해결할 수 있게 한다.

## Why It Matters

에이전트가 단순히 도구를 호출하는 것과 실제로 "생각하고 계획을 세우는" 것의 차이가 리즈닝/플래닝에 있다. 이 메커니즘을 이해하면 에이전트가 복잡한 작업에서 왜 실패하는지, 어떻게 개선할 수 있는지 파악할 수 있다.

## Key Concepts

- **Reasoning** — 현재 상황 파악, 가능한 행동 평가, 최적 선택
- **Planning** — 목표 달성을 위한 단계별 계획 수립
- **ReAct** — Reasoning + Acting의 반복 패턴
- **Chain-of-Thought (CoT)** — 단계별 추론 과정을 명시적으로 생성
- **Plan-and-Execute** — 먼저 전체 계획 수립 후 순서대로 실행
- **Reflection** — 자신의 출력을 검토하고 수정하는 능력

## 주요 패턴

### ReAct (Reasoning + Acting)

가장 널리 사용되는 에이전트 패턴:

```
Thought: 현재 상황을 파악하고 다음 행동을 결정
Action: 도구 호출 또는 행동
Observation: 행동 결과 관찰
... 반복 ...
Final Answer: 최종 답변
```

LLM에게 `Thought:` → `Action:` → `Observation:` 형식을 따르도록 유도하여 reasoning 과정을 명시화한다.

*참고: ReAct 패턴의 원본 논문은 Yao et al. (2022). 소스 미수집.* — **Needs Source**

### Chain-of-Thought (CoT)

```
문제를 단계별로 생각해 보자:
1. 먼저 ...
2. 그다음 ...
3. 따라서 ...
→ 최종 답변
```

도구 없이 순수한 추론만으로 복잡한 문제를 해결할 때 사용.

### Plan-and-Execute

```
1단계: Planner가 전체 계획 수립
         ↓
2단계: Executor가 각 단계를 순서대로 실행
         ↓
3단계: 결과 집계
```

복잡한 다단계 작업에 적합. LangGraph에서 `Planner node` → `Executor node` → `Replanner node` 패턴으로 구현.

## 프레임워크별 지원

### OpenAI Agents SDK

*Source: `openai-agents-sdk-running-agents-2026-05-23`, `openai-agents-sdk-agent-overview-2026-05-23`*

- `Runner` 클래스가 실제 실행 루프를 담당한다. `Agent` 객체는 설정 명세서에 해당하고, `Runner`가 turns, tools, guardrails, handoffs, sessions를 관리한다.
- **암묵적 ReAct 구조**: LLM 호출 → `final_output` | `handoff` | `tool_calls` 결과에 따라 분기 → 반복. 명시적 Thought/Action/Observation 포맷은 없으나 루프 구조가 ReAct와 동일하다.
- `reset_tool_choice=True`(기본값): tool 호출 후 `tool_choice` 리셋 → tool 루프 방지.
- 명시적 CoT는 `instructions`에 "step by step" 유도 프롬프트로 구현.
- `o1`, `o3` 같은 reasoning 모델은 내장 CoT를 수행.

### LangGraph

*Source: `langgraph-prebuilt-chat-agent-executor-2026-05-28` (verified)*

- `create_react_agent` (LangGraph prebuilt): **LLM + ToolNode + StateGraph**를 조립해 ReAct 루프를 구성한다. `agent` 노드(call_model) → `should_continue` 조건부 엣지 → `tools` 노드(ToolNode) → 다시 `agent` 노드의 반복이 암묵적 ReAct 구조다. 소스: `langgraph/prebuilt/chat_agent_executor.py`
- `pre_model_hook` / `post_model_hook`: 모델 호출 전후 커스터마이징 포인트. CoT 유도 프롬프트 주입이나 출력 검토(Reflection) 패턴을 여기에 연결할 수 있다.
- ⚠️ v1.0부터 `langchain.agents.create_agent`로 이동. `langgraph.prebuilt.create_react_agent`는 하위 호환용.
- Plan-and-Execute: `StateGraph`로 Planner/Executor/Replanner 노드를 명시적으로 구성. (*Needs Source — 공식 예제 미확인*)
- Reflection: 자기 평가 노드를 그래프에 추가하는 패턴. (*Needs Source*)

### LangChain

*Source: `langchain-agents-factory-2026-05-28`*

- `create_agent`: `StateGraph`를 동적으로 조립한다. `model_node`(L1318) + `ToolNode` + `conditional edges`로 암묵적 ReAct 루프를 구성. 명시적 Thought/Action/Observation 포맷 없이 LLM ↔ tool 반복 구조.
- `recursion_limit=9999`(L1665): LangGraph 기본값(25)을 override하여 긴 에이전트 루프를 허용.
- Middleware hook nodes: `entry` / `loop_entry` / `loop_exit` / `exit_node` 구조로 각 루프 진입·종료 시점에 커스터마이징 가능.
- 구버전 `AgentExecutor`: ReAct 루프를 while loop로 구현 (deprecated).

### Deep Agents

*Source: `deepagents-source-graph-2026-05-19`, `deepagents-docs-harness-2026-05-19`*

- `create_deep_agent`는 내부적으로 `langchain.agents.create_agent`에 위임하므로, LangChain의 StateGraph 기반 암묵적 ReAct 루프를 그대로 사용한다.
- **Planning 컴포넌트** (공식 하네스 8가지 구성요소 중 하나): `write_todos` 도구를 에이전트에 제공한다. 태스크 상태(`pending` / `in_progress` / `completed`)가 agent state에 영속된다. `TodoListMiddleware`가 이를 담당.
- `BASE_AGENT_PROMPT`: `graph.py` 내 상수로 직접 정의됨 (클래스·외부 파일 아님). System prompt 조립 순서: `USER` → `BASE`(또는 HarnessProfile의 `CUSTOM`) → `SUFFIX`. ReAct 유도 지시 포함 여부는 내용 미확인 — **Needs Source**
- Planning 전용 reasoning 노드가 별도로 존재하는지는 소스에서 미확인 — **Needs Source**

## Reasoning 모델 vs Prompting 방식

| 방식 | 설명 | 예시 |
|------|------|------|
| **Reasoning 모델** | LLM 자체가 내장 CoT 수행 | OpenAI `o1`, `o3` |
| **CoT 프롬프팅** | "단계별로 생각해보자" 유도 | `instructions`에 CoT 프롬프트 |
| **ReAct 프롬프팅** | Thought/Action/Observation 형식 | `create_react_agent` |
| **Plan-and-Execute** | 명시적 플래닝 노드 | LangGraph 멀티 노드 그래프 |

## Related Pages

- [[Agent Runtime]]
- [[Agent Harness]]
- [[StateGraph]]
- [[Subagents]]
- [[Context Engineering]]

## Open Questions

- `BASE_AGENT_PROMPT` 내용에 ReAct 유도 지시가 있는가? — Needs Source
- Deep Agents `create_deep_agent`에서 planning 전용 reasoning 노드가 별도로 존재하는가? — Needs Source
- Reasoning 모델(o1, o3)을 에이전트 프레임워크에서 사용할 때 특별한 설정이 필요한가? — Needs Source
- LangGraph Plan-and-Execute 공식 예제 패턴 — Needs Source

## Sources

- `langgraph-prebuilt-chat-agent-executor-2026-05-28` (LangGraph ReAct 구현 확인)
- `langchain-agents-factory-2026-05-28` (LangChain create_agent StateGraph 기반 ReAct 구조)
- `openai-agents-sdk-running-agents-2026-05-23` (OpenAI Agents SDK Runner loop)
- `openai-agents-sdk-agent-overview-2026-05-23` (OpenAI Agents SDK Agent 구조)
- `deepagents-source-graph-2026-05-19` (Deep Agents BASE_AGENT_PROMPT 위치, create_agent 위임 구조)
- `deepagents-docs-harness-2026-05-19` (Deep Agents planning 컴포넌트: write_todos, TodoListMiddleware)
