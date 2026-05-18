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

- `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가? — Source: `deepagents-docs-overview-2026-05-18`
- filesystem tools는 SDK 내부에 있는가, 별도 패키지인가? — Source: `deepagents-docs-overview-2026-05-18`
- subagent state는 parent agent와 어떻게 분리되는가? — Source: `deepagents-docs-overview-2026-05-18`
- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`
- "durable execution"이 LangGraph의 checkpointing과 어떻게 연결되는가? — Source: `deepagents-docs-overview-2026-05-18`
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `create_deep_agent`와 LangChain `create_agent`의 내부 구조 차이는 무엇인가? — 소스코드 확인 필요
- `graph.py#L37`의 base agent prompt는 어떤 내용인가? 커스터마이징 가능한가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- Offloading backend (`StateBackend`, `StoreBackend` 등)는 어떤 구현이 기본값인가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`

## 프레임워크 간 비교

- 세 프레임워크는 병렬 도구 호출 처리에서 어떻게 비교되는가?
- human-in-the-loop 지원이 가장 좋은 프레임워크는 무엇인가?
- 각 프레임워크는 컨텍스트 윈도우 한계를 어떻게 처리하는가?
- 한 프레임워크의 체크포인트를 다른 프레임워크로 이식할 수 있는가?

## PR 기회

- 세 저장소에 테스트 없는 문서화된 이슈가 존재하는가?
- 체크포인팅 구현에 빠진 엣지 케이스 테스트가 있는가?
