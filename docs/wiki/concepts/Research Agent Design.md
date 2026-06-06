---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: partial
confidence: medium
last_reviewed: 2026-06-06
sources:
  - openai-agents-sdk-running-agents-2026-05-23
  - langchain-docs-products-2026-05-23
  - langgraph-prebuilt-chat-agent-executor-2026-05-28
  - deepagents-source-subagents-2026-05-23
---

# Research Agent Design

## Summary

리서치 에이전트는 사용자 질의에 답하기 위해 검색 도구를 반복 호출하고 결과를 종합하는 에이전트다.
LangChain, LangGraph, Deep Agents 세 프레임워크 모두 동일한 4-메시지 루프 구조
(`HumanMessage → AIMessage(tool_calls) → ToolMessage → AIMessage(final)`)를 기반으로 구현하지만,
오케스트레이션 방식, 코드 구조, 확장 패턴이 다르다.

## Why It Matters

같은 요구사항을 세 프레임워크로 구현해 비교하면 각 프레임워크의 추상화 수준,
제어 방식, 확장 패턴의 차이를 가장 명확하게 볼 수 있다.
리서치 에이전트는 AI 에이전트의 가장 대표적인 실전 사례이기도 하다.

## 공통 요구사항

| 요구사항 | 내용 |
|---------|------|
| **검색 도구** | 웹 검색 또는 내부 문서 검색 tool |
| **ReAct 루프** | 검색 → 결과 관찰 → 다음 행동 결정 반복 |
| **컨텍스트 관리** | 검색 결과 누적으로 늘어나는 메시지 히스토리 처리 |
| **최종 답변 생성** | 수집된 정보를 종합한 응답 |
| **(선택) 병렬 검색** | 여러 주제를 동시에 검색해 latency 감소 |
| **(선택) 체크포인팅** | 장시간 실행 에이전트의 상태 저장 및 재개 |

## 메시지 흐름 (모든 프레임워크 공통)

*Source: 실험 `examples/research_agent_comparison/` (2026-05-24 검증됨)*

```
HumanMessage("질문")
  → AIMessage(tool_calls=[search("검색어")])     ← LLM 1번째 호출
  → ToolMessage(content="검색 결과")             ← ToolNode 실행
  → AIMessage(content="최종 답변")               ← LLM 2번째 호출 (종료)
```

LangChain `create_agent`, LangGraph `create_react_agent`, LangGraph `StateGraph` 수동
세 가지 모두 동일한 4-메시지 루프 패턴을 사용한다.

## 프레임워크별 접근 방식

### LangChain `create_agent`

*Source: `langchain-docs-products-2026-05-23`, [[LangChain create_agent flow]]*

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool],
    system_prompt="You are a research assistant.",
    checkpointer=InMemorySaver(),
)
result = agent.invoke({"messages": [HumanMessage("질문")]})
```

- `bind_tools()`를 내부에서 자동 호출 (`factory.py` `_get_bound_model()` 확인됨)
- ReAct 루프가 암묵적 — 개발자에게 노출되지 않음
- `middleware=`로 `SummarizationMiddleware` 등 컨텍스트 관리 확장
- 파라미터: `system_prompt=` (LangGraph `create_react_agent`의 `prompt=`와 다름 — 실험 확인)
- 초기화 시간: ~0.26s (LangGraph 버전 대비 약 65배 — 원인 미확인)

### LangGraph `create_react_agent`

*Source: `langgraph-prebuilt-chat-agent-executor-2026-05-28`, [[LangGraph create_react_agent flow]]*

```python
from langgraph.prebuilt import create_react_agent

graph = create_react_agent(
    model,
    tools=[search_tool],
    prompt="You are a research assistant.",
    checkpointer=MemorySaver(),
)
result = graph.invoke({"messages": [HumanMessage("질문")]})
```

- StateGraph + ToolNode를 내부에서 조립 — LangGraph 런타임 직접 사용
- `pre_model_hook` / `post_model_hook`으로 커스터마이징 가능
- `bind_tools()`는 수동 처리 필요 (또는 model 자체가 지원)
- 파라미터: `prompt=` (`create_agent`의 `system_prompt=`와 다름)
- 초기화 시간: ~0.004s

### LangGraph `StateGraph` 수동

*Source: `langgraph-docs-graph-api-2026-05-23`, [[LangGraph StateGraph compile invoke flow]]*

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode([search_tool]))
builder.set_entry_point("agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=MemorySaver())
```

- 오케스트레이션이 코드에 명시적으로 드러남 — 분기 로직을 개발자가 직접 제어
- 추가 노드(Planner, Evaluator, Replanner) 삽입 용이
- 코드량 ~33 LOC — `create_react_agent` 대비 약 35% 많음 (실험 기준)

### Deep Agents `create_deep_agent`

*Source: `deepagents-source-subagents-2026-05-23`, [[Deep Agents create_deep_agent flow]]*

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search_tool],
    system_prompt="You are a research assistant.",
)
result = agent.invoke({"messages": [HumanMessage("질문")]})
```

- LangChain `create_agent` 위에 미들웨어 스택이 자동으로 조립됨
- `FilesystemMiddleware`: 검색 결과 대용량 자동 오프로드 (20,000 토큰 초과 시)
- `SummarizationMiddleware`: 컨텍스트 85% 도달 시 자동 요약
- `SubAgentMiddleware`: `task` tool로 병렬 리서치 subagent 실행 가능
- boilerplate 코드 최소화, 컨텍스트 관리 자동화

## 비교 표

*Source: 실험 `examples/research_agent_comparison/` (2026-05-24), [[LangChain vs LangGraph vs Deep Agents]]*

| 기준 | LangChain `create_agent` | LangGraph `create_react_agent` | LangGraph `StateGraph` 수동 | Deep Agents |
|------|--------------------------|--------------------------------|-----------------------------|------------|
| LOC (단순 에이전트) | 25 | 24 | 33 | 미측정 |
| 오케스트레이션 | 암묵적 | 암묵적 | **명시적** | 암묵적 |
| 초기화 시간 | ~0.26s | ~0.004s | ~0.004s | 미측정 |
| `bind_tools` 자동 | ✅ | ❌ 수동 | ❌ 수동 | ✅ |
| 컨텍스트 압축 | middleware로 추가 | 직접 구현 | 직접 구현 | 자동 (`SummarizationMiddleware`) |
| 파일 오프로드 | ❌ | ❌ | ❌ | 자동 (`FilesystemMiddleware`) |
| 병렬 subagent 검색 | ❌ (별도 구현) | `Send` API | `Send` API | `task` tool 자동 병렬 |
| 체크포인팅 | `checkpointer=` | `checkpointer=` | `checkpointer=` | 내장 |

## 프레임워크 선택 가이드

| 상황 | 권장 |
|------|------|
| 단순 Q&A / 단일 검색 루프 | LangGraph `create_react_agent` — 최소 코드, 빠른 초기화 |
| 분기 제어 필요 (Planner-Executor, Reflection) | LangGraph `StateGraph` 수동 |
| 장시간 리서치 + 대용량 컨텍스트 자동 관리 | Deep Agents |
| 병렬 주제 리서치 | Deep Agents `SubAgentMiddleware` 또는 LangGraph `Send` |

## 관련 섹션 (Part 5 Chapter 24)

- **24.2** LangChain 버전 → [[LangChain create_agent flow]]
- **24.3** LangGraph 버전 → [[LangGraph StateGraph compile invoke flow]], [[LangGraph ToolNode flow]]
- **24.4** Deep Agents 버전 → [[Deep Agents create_deep_agent flow]], [[Deep Agents SubAgentMiddleware task tool flow]]
- **24.5** 코드 비교 → [[LangChain vs LangGraph vs Deep Agents]]

## Source Code References

- `langchain/agents/factory.py` — `_get_bound_model()`, `model_node` (실험에서 확인)
- `langgraph/prebuilt/chat_agent_executor.py` — `create_react_agent`
- `deepagents/middleware/subagents.py` — `SubAgentMiddleware`

## Tests

- 실험 코드: `examples/research_agent_comparison/` (Mock LLM + Mock search tool 기반)

## Related Pages

- [[LangChain vs LangGraph vs Deep Agents]]
- [[Tool Calling]]
- [[Agent Runtime]]
- [[Reasoning and Planning]]
- [[Context Engineering]]
- [[Subagents]]
- [[LangChain create_agent flow]]
- [[LangGraph create_react_agent flow]]
- [[Deep Agents create_deep_agent flow]]

## Open Questions

- LangChain `create_agent` 초기화 시간이 LangGraph보다 긴 정확한 원인 (`factory.py` 내부 분석 필요)
- Deep Agents 리서치 에이전트의 초기화 시간과 코드량 — 패키지 설치 후 실측 필요
- 실제 웹 검색 도구(SerpAPI, Tavily 등) 연결 시 세 프레임워크의 실행 시간 차이
- `create_react_agent`의 `pre_model_hook`과 `create_agent`의 `middleware`의 실질적 차이

## Sources

- `openai-agents-sdk-running-agents-2026-05-23`
- `langchain-docs-products-2026-05-23`
- `langgraph-prebuilt-chat-agent-executor-2026-05-28`
- `deepagents-source-subagents-2026-05-23`
- 실험 코드: `examples/research_agent_comparison/` (2026-05-24 검증)
