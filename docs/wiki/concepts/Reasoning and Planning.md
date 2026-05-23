---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
  - OpenAI Agents SDK
status: draft
confidence: low
last_reviewed: 2026-05-23
sources: []
---

# Reasoning and Planning

## Summary

리즈닝(Reasoning)은 LLM이 현재 상황을 이해하고 추론하는 능력이고, 플래닝(Planning)은 주어진 요청을 해결하기 위한 계획을 세우는 능력이다. 이 두 능력은 에이전트가 단순한 질답을 넘어 복잡한 다단계 문제를 해결할 수 있게 한다.

*상태: 개념 스텁. 소스 탐구 필요.*

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

*Source: Needs Source*

- `Runner` agent loop 자체가 암묵적 ReAct 구조: LLM → tool call → observation → LLM...
- 명시적 CoT는 `instructions`에 "step by step" 유도 프롬프트로 구현
- `o1`, `o3` 같은 reasoning 모델은 내장 CoT를 수행

### LangGraph

*Source: Needs Source*

- `create_react_agent` (LangGraph prebuilt): 암묵적 ReAct 패턴
- Plan-and-Execute: `StateGraph`로 Planner/Executor/Replanner 노드를 명시적으로 구성
- Reflection: 자기 평가 노드를 그래프에 추가하는 패턴

### LangChain

*Source: Needs Source*

- `create_agent` (현재 권장): LangGraph 기반 ReAct
- 구버전 `AgentExecutor`: ReAct 루프를 while loop로 구현 (deprecated)

### Deep Agents

*Source: Needs Source*

- `create_deep_agent`에서 reasoning/planning 전용 노드가 별도로 있는지 미확인 (⚠️ Needs Source)
- `BASE_AGENT_PROMPT`에 ReAct 유도 지시가 있을 가능성 (⚠️ 가설)

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

- Deep Agents `create_deep_agent`에서 planning 단계는 별도 노드로 존재하는가? — Needs Source
- `BASE_AGENT_PROMPT`에 ReAct 유도 지시가 있는가? — Needs Source (관련: `deepagents-source-graph-2026-05-19`)
- Reasoning 모델(o1, o3)을 에이전트 프레임워크에서 사용할 때 특별한 설정이 필요한가? — Needs Source
- LangGraph `create_react_agent`의 내부 구현은 어떻게 되는가? — Needs Source

## Sources

*(소스 없음 — 개념 스텁)*
