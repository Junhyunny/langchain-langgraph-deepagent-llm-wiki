---
type: decision
framework:
  - LangGraph
  - Deep Agents
  - LangChain
status: partial
confidence: high
last_reviewed: 2026-06-06
sources:
  - langchain-docs-products-2026-05-23
  - deepagents-docs-overview-2026-05-18
  - deepagents-source-graph-2026-05-19
  - langchain-agents-factory-2026-05-28
  - deepagents-source-subagents-2026-05-23
---

# When to use LangGraph vs Deep Agents for orchestration

## 결정 사항

초기 구현은 Deep Agents를 우선 사용하고, 체크포인트/재개/분기 제어를 세밀히 다뤄야 하는 구간은 LangGraph 직접 구현으로 내린다.

## 빠른 결정 규칙

```
Q1. 복잡한 멀티 스텝 작업 + 파일시스템 + subagent 위임이 기본으로 필요한가?
  → Yes → Deep Agents

Q2. 그래프 노드 수준의 분기, 체크포인팅, custom state schema, HITL 라우팅이 핵심인가?
  → Yes → LangGraph 직접 구현

Q3. 단순 ReAct 루프 + 도구 호출만 필요한가?
  → Yes → LangChain create_agent (또는 LangGraph create_react_agent)
```

## 계층 관계 이해

```
Deep Agents SDK    ← Harness (opinionated, batteries-included)
      ↕
LangChain          ← Framework (abstractions, integrations)
      ↕
LangGraph          ← Runtime (durable execution, streaming, HITL)
```

Deep Agents는 LangGraph 위에 빌드되었다. Deep Agents를 쓰면 LangGraph 기능(checkpointing, streaming, HITL)을 내부적으로 사용하지만 직접 제어할 수 없다.
LangGraph를 직접 쓰면 더 많은 제어권을 갖지만 설계 비용이 든다.

Source: `langchain-docs-products-2026-05-23`

## 시나리오별 판단 기준

| 시나리오 | 권장 | 이유 |
|---------|------|------|
| 장기 작업, 파일 읽기/쓰기, subagent 위임 | Deep Agents | virtual filesystem + SubAgentMiddleware 기본 제공 |
| 그래프 노드 간 커스텀 분기 로직 | LangGraph | `add_conditional_edges`, path_map 직접 제어 |
| 체크포인트 저장소 커스터마이징 (PostgreSQL, Redis 등) | LangGraph | `BaseCheckpointSaver` 직접 구현 가능 |
| sandbox 환경에서 코드 실행 (`execute` tool) | Deep Agents | `SandboxBackendProtocol` 내장 |
| Subgraph / parent-child graph 경계 직접 설계 | LangGraph | `Command(graph=Command.PARENT)`, `Send` 직접 사용 |
| 모델별 프로필(system prompt, excluded tools) 번들 | Deep Agents | `HarnessProfile`, `register_harness_profile` |
| 이벤트 스트리밍 세밀한 제어 (7가지 stream_mode) | LangGraph | `values/updates/custom/checkpoints/tasks/messages/debug` |
| 빠른 프로토타이핑, 표준 ReAct 루프 | LangChain `create_agent` | 설정 최소화 |

Source: `deepagents-docs-overview-2026-05-18`, `langchain-docs-products-2026-05-23`

## Deep Agents를 선택하는 신호

- 파일 읽기/쓰기/glob/grep이 agent의 핵심 작업이다
- subagent에 작업을 위임하고 parent에는 최종 보고서만 전달하고 싶다
- context window 관리(오프로드, 요약)를 직접 구현하기 싫다
- skills frontmatter로 모델이 관련 지시사항을 동적으로 로드해야 한다
- 하네스 프로파일로 모델별 동작을 선언적으로 설정하고 싶다
- `interrupt_on={"tool_name": True}` 패턴으로 Human-in-the-Loop을 쉽게 설정하고 싶다

Source: `deepagents-docs-overview-2026-05-18`, `deepagents-source-graph-2026-05-19`

## LangGraph를 선택하는 신호

- state schema를 완전히 커스터마이징해야 한다 (특정 TypedDict 필드, custom reducer)
- 그래프 노드 수준에서 분기/합류/fan-out을 직접 설계해야 한다
- `MemorySaver` 외의 checkpointer를 직접 주입해야 한다 (PostgresSaver, RedisSaver)
- HITL에서 `interrupt_before`/`interrupt_after` 노드를 명시적으로 지정해야 한다
- subagent 결과를 parent message history에 직접 병합해야 한다 (`_EXCLUDED_STATE_KEYS` 우회 불가)
- Deep Agents가 제거를 금지한 `FilesystemMiddleware`나 `SubAgentMiddleware` 없이 minimal graph가 필요하다
- 스트리밍 모드(`stream_mode`) 조합을 세밀하게 제어해야 한다

Source: `langchain-agents-factory-2026-05-28`, `deepagents-source-graph-2026-05-19`

## 혼합 전략 (실전 권장)

```python
# Deep Agents harness + LangGraph CompiledSubAgent 조합
from deepagents import create_deep_agent
from deepagents.middleware import CompiledSubAgent

# LangGraph로 직접 설계한 specialist graph
specialist_graph = build_my_langgraph_graph()

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    subagents=[
        CompiledSubAgent(
            name="specialist",
            description="Handles complex orchestration tasks",
            runnable=specialist_graph,   # ← LangGraph 직접 구현
        )
    ],
)
```

- parent: Deep Agents harness (파일시스템, context 관리)
- specialist: LangGraph 직접 구현 (세밀한 그래프 제어)
- `CompiledSubAgent.runnable`의 상태 스키마에는 `messages` key 필수

Source: `deepagents-source-subagents-2026-05-23`

## 트레이드오프 요약

| | Deep Agents | LangGraph 직접 |
|---|---|---|
| **초기 설정 비용** | 낮음 (기본 harness 제공) | 높음 (state schema, edge, node 설계) |
| **제어 수준** | 중간 (middleware API로 제한) | 높음 (모든 primitive 직접 접근) |
| **내부 추적 용이성** | 낮음 (harness 추상화가 가림) | 높음 (소스 코드 1:1 대응) |
| **filesystem/subagent** | 기본 제공 | 직접 구현 필요 |
| **custom checkpointer** | `checkpointer=` 파라미터 | `StateGraph.compile(checkpointer=...)` |
| **학습 비용** | 낮음 | 높음 |

## 컨텍스트 (이 저장소)

이 위키의 목표는 오픈소스 PR 기여가 가능한 수준의 이해다.
- 초기 실험: Deep Agents로 빠르게 동작 확인
- 소스 추적/이슈 분석: LangGraph 직접 구현으로 내려가 확인

Deep Agents 추상화가 원인 파악을 지연시킬 때만 LangGraph 직접 구현으로 전환한다.

## 재검토 기준

- 실패 사례의 50% 이상이 harness 추상화에서 원인 파악 지연을 유발하면 LangGraph 비중을 높인다
- 특정 subagent가 반복적으로 세밀한 graph 제어를 요구하면 `CompiledSubAgent`로 분리한다

## Related Pages

- [[LangChain vs LangGraph vs Deep Agents]]
- [[create_agent vs create_deep_agent]]
- [[Deep Agents SubAgentMiddleware task tool flow]]
- [[LangGraph ToolNode Command vs Deep Agents task tool]]
- [[Agent Harness]]
- [[Checkpointing]]
- [[HumanInTheLoop]]

## Sources

- `langchain-docs-products-2026-05-23`
- `deepagents-docs-overview-2026-05-18`
- `deepagents-source-graph-2026-05-19`
- `langchain-agents-factory-2026-05-28`
- `deepagents-source-subagents-2026-05-23`
