# 미해결 질문

학습 중 수집한 질문이다. 해결되면 관련 페이지로 옮기거나 삭제한다.

---

## LangChain

- agent executor는 언제 도구 호출을 멈출지 어떻게 결정하는가?
- `AgentExecutor`와 `create_react_agent`의 차이는 무엇인가?
- 메시지 히스토리는 내부적으로 어디에서 관리되는가?
- `stream_events` v3와 이전 버전의 차이는 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- LangGraph의 Pregel stream mode와 Event Streaming(`stream_events`)의 정확한 관계는? — Source: `langchain-docs-event-streaming-2026-05-18`
- Custom stream transformer의 계약(contract)은 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- Deep Agents의 `create_deep_agent`도 `stream_events`를 동일하게 지원하는가? — Source: `langchain-docs-event-streaming-2026-05-18`

## LangGraph

- `StateGraph.compile()`은 runnable을 내부적으로 어떻게 생성하는가?
- 체크포인팅은 무엇을 저장하고 무엇을 버릴지 어떻게 결정하는가?
- `interrupt_before` / `interrupt_after`는 그래프 수준에서 어떻게 동작하는가?
- `MemorySaver`와 영속적 checkpointer의 차이는 무엇인가?
- `astream_events`와 함께 스트리밍은 어떻게 동작하는가?

## Deep Agents

- filesystem tools의 구체적 구현 및 tool 목록은? (`deepagents/middleware/filesystem.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- subagent state isolation의 구체적 메커니즘은? (`SubagentTransformer`, `SubAgentMiddleware` 내부 확인 필요) — Source: `deepagents-source-graph-2026-05-19`
- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 어떻게 조립하나? — Source: `deepagents-source-graph-2026-05-19`
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- `PatchToolCallsMiddleware`는 어떤 tool call 패치를 수행하나? — Source: `deepagents-source-graph-2026-05-19`
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나? — Source: `deepagents-source-graph-2026-05-19`
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`

**해소됨 (2026-05-19):**
- ✅ `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가? → `langchain.agents.create_agent`에 위임 → `CompiledStateGraph` 반환 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `create_deep_agent`와 LangChain `create_agent`의 내부 구조 차이는? → middleware 조립 후 `create_agent` 위임 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `graph.py`의 base agent prompt는 어떤 내용인가? → `BASE_AGENT_PROMPT` 상수, graph.py 직접 정의 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ "durable execution"이 LangGraph checkpointing과 어떻게 연결되는가? → `checkpointer` 파라미터 + `_DeepAgentState` `DeltaChannel` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ Offloading backend 기본값은? → `StateBackend()` (Source: `deepagents-source-graph-2026-05-19`)

## 프레임워크 간 비교

- 세 프레임워크는 병렬 도구 호출 처리에서 어떻게 비교되는가?
- human-in-the-loop 지원이 가장 좋은 프레임워크는 무엇인가?
- 각 프레임워크는 컨텍스트 윈도우 한계를 어떻게 처리하는가?
- 한 프레임워크의 체크포인트를 다른 프레임워크로 이식할 수 있는가?

## PR 기회

- 세 저장소에 테스트 없는 문서화된 이슈가 존재하는가?
- 체크포인팅 구현에 빠진 엣지 케이스 테스트가 있는가?
