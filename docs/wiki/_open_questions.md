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

- `StateGraph.compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `libs/langgraph/langgraph/pregel/_checkpoint.py`의 `create_checkpoint`, `channels_from_checkpoint`, delta-channel reconstruction은 어떻게 구현되어 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- pending writes recovery를 정의하는 canonical test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `DeltaChannel` reconstruction/pruning/copying safety를 검증하는 test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `exit` durability에서 `_put_exit_delta_writes()`를 검증하는 test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- checkpoint schema migration 또는 state schema 변경 대응은 공식적으로 어떻게 권장되는가? — Source: `langgraph-docs-persistence-2026-05-20`
- `interrupt_before` / `interrupt_after`는 그래프 수준에서 어떻게 동작하는가?
- `MemorySaver`와 persistent saver의 운영상 차이는 무엇인가? async behavior, serialization, retention/pruning API의 버전 차이를 확인해야 한다. — Source: `langgraph-reference-checkpoint-2026-05-20`
- `astream_events`와 함께 스트리밍은 어떻게 동작하는가?
- LangGraph package version과 reference docs version의 관계는? GitHub page는 `langgraph==1.2.0`, `StateGraph.compile` reference는 v1.1.10으로 보였다. — Source: `langgraph-reference-stategraph-compile-2026-05-20`

**해소됨 (2026-05-20):**
- ✅ 체크포인팅은 무엇을 저장하고 무엇을 버릴지 어떻게 결정하는가? → LangGraph는 super-step boundary마다 `StateSnapshot` checkpoint를 저장하고, super-step 내부의 task-level writes도 pending writes로 저장한다. State에 포함되지 않은 외부 side effect나 thread 간 memory는 자동 저장 대상이 아니다. (Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-checkpoint-2026-05-20`)
- ✅ `StateGraph.compile(checkpointer=...)`에서 checkpointer는 어디에 attach되는가? → `state.py`에서 `CompiledStateGraph(..., checkpointer=checkpointer, ...)`에 전달되고, `CompiledStateGraph`는 `Pregel`을 상속한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `InMemorySaver`의 내부 자료구조는? → `storage`, `writes`, `blobs`로 checkpoint record, pending writes, channel-version blobs를 분리한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `exit` / `async` / `sync` durability mode는 runtime source에서 어디에 구현되는가? → `_defaults()` 기본값은 `"async"`, `"sync"`는 tick 뒤 checkpoint future를 기다리고, `"exit"`는 `put_writes()` immediate persistence를 건너뛰고 loop exit에서 checkpoint/writes를 저장한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)

## Deep Agents

- subagent state isolation의 구체적 메커니즘은? (`SubagentTransformer`, `SubAgentMiddleware` 내부 확인 필요) — Source: `deepagents-source-graph-2026-05-19`
- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 어떻게 조립하나? — Source: `deepagents-source-graph-2026-05-19`
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- `PatchToolCallsMiddleware`는 어떤 tool call 패치를 수행하나? — Source: `deepagents-source-graph-2026-05-19`
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나? — Source: `deepagents-source-graph-2026-05-19`
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`

- `HarnessProfile`의 전체 필드 목록은? (`base_system_prompt`, `system_prompt_suffix` 외에 더 있는가?) — Source: `deepagents-docs-harness-2026-05-19`
- Provider-level vs model-level HarnessProfile의 merge 우선순위는? — Source: `deepagents-docs-harness-2026-05-19`
- `register_harness_profile` entry points 패키징 방법은? — Source: `deepagents-docs-harness-2026-05-19`
- Sandbox backend 없을 때 `execute` tool은 error 반환인가, tool 목록에서 제외되는가? — Source: `deepagents-docs-harness-2026-05-19`
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가? — Source: `deepagents-docs-harness-2026-05-19`

**해소됨 (2026-05-19):**
- ✅ `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가? → `langchain.agents.create_agent`에 위임 → `CompiledStateGraph` 반환 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `create_deep_agent`와 LangChain `create_agent`의 내부 구조 차이는? → middleware 조립 후 `create_agent` 위임 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `graph.py`의 base agent prompt는 어떤 내용인가? → `BASE_AGENT_PROMPT` 상수, graph.py 직접 정의 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ "durable execution"이 LangGraph checkpointing과 어떻게 연결되는가? → `checkpointer` 파라미터 + `_DeepAgentState` `DeltaChannel` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ Offloading backend 기본값은? → `StateBackend()` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ filesystem tools 목록 확인: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ `HarnessProfile` 등록 방법: `register_harness_profile(key, HarnessProfile(...))` (Source: `deepagents-docs-harness-2026-05-19`)

## 프레임워크 간 비교

- 세 프레임워크는 병렬 도구 호출 처리에서 어떻게 비교되는가?
- human-in-the-loop 지원이 가장 좋은 프레임워크는 무엇인가?
- 각 프레임워크는 컨텍스트 윈도우 한계를 어떻게 처리하는가?
- 한 프레임워크의 체크포인트를 다른 프레임워크로 이식할 수 있는가?

## PR 기회

- 세 저장소에 테스트 없는 문서화된 이슈가 존재하는가?
- 체크포인팅 구현에 빠진 엣지 케이스 테스트가 있는가?
