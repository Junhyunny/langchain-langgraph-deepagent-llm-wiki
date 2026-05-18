---
type: framework
framework: Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-18
sources:
  - deepagents-docs-overview-2026-05-18
  - deepagents-docs-context-engineering-2026-05-18
---

# Deep Agents

## Summary

`deepagents`는 PyPI에서 설치 가능한 standalone 라이브러리다.
[[LangChain]]의 core building blocks와 [[LangGraph]] runtime 위에서 동작하는 **agent harness**다.
복잡한 multi-step 태스크, 파일 시스템 기반 context 관리, subagent 위임, long-term memory를 내장 기능으로 제공한다.

## Why It Matters

Deep Agents는 LangChain + LangGraph의 조합을 직접 조립하지 않아도 복잡한 에이전트를 빠르게 만들 수 있도록 공통 패턴을 미리 패키지화한 고수준 harness다.
언제 Deep Agents를 쓰고, 언제 LangGraph를 직접 쓸지 판단하기 위해 내부 구조를 이해하는 것이 중요하다.

## Verified Facts
*Source: `deepagents-docs-overview-2026-05-18`*

- **패키지**: `pip install deepagents` — standalone PyPI 패키지
- **저장소**: `github.com/langchain-ai/deepagents`
- **의존성**: [[LangChain]] building blocks + [[LangGraph]] runtime
- **정의**: "agent harness" — 다른 프레임워크와 동일한 core tool calling loop이지만, built-in tools와 capabilities 포함
- **진입점**: `create_deep_agent(model, tools, system_prompt)`
- **저장소 구성**:
  - **Deep Agents SDK** — 어떤 태스크도 처리하는 에이전트 빌딩 패키지
  - **Deep Agents Code** — Deep Agents SDK 위에 만들어진 터미널 코딩 에이전트
  - **ACP integration** — Zed 등 코드 에디터용 Agent Client Protocol 커넥터
- **LangGraph 활용 기능**: durable execution, streaming, human-in-the-loop

## Use Cases (공식 문서 기준)
*Source: `deepagents-docs-overview-2026-05-18`*

Deep Agents SDK를 사용해야 하는 경우:
- 복잡한 multi-step 태스크 (planning and decomposition 필요)
- 대규모 context 관리 (filesystem tools, summarization)
- filesystem backend 교체 (in-memory / local disk / durable store / sandbox / custom)
- shell 명령어 실행 (`execute` tool, sandbox backend)
- interpreter 코드 실행 (subagent orchestration, structured data transformation)
- specialized subagent에 작업 위임 (context isolation)
- 대화/스레드 간 memory 지속
- 파일 접근 권한 제어 (declarative permission rules)
- human-in-the-loop workflows
- 모든 모델 사용 가능 (provider agnostic)

**더 단순한 에이전트를 만들 때** → LangChain의 `create_agent` 또는 custom [[LangGraph]] workflow 권장
*(Source: `deepagents-docs-overview-2026-05-18`)*

## Quick Start
```python
# pip install -qU deepagents langchain-openai
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.4",
    tools=[my_tool],
    system_prompt="You are a helpful assistant",
)

agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

## Public API

- `create_deep_agent(model, tools, system_prompt)` — 검증됨
  Source: `deepagents-docs-overview-2026-05-18`
- `create_deep_agent(model, tools, system_prompt, memory, skills, context_schema, store, backend, middleware, interrupt_on)` — 파라미터 확인됨
  Source: `deepagents-docs-context-engineering-2026-05-18`

## Context Engineering
*Source: `deepagents-docs-context-engineering-2026-05-18`*

Deep Agents는 5가지 context 타입을 체계적으로 관리한다. 자세한 내용: [[Context Engineering]]

**System Prompt 조립 순서:** custom → base(graph.py#L37) → todos → memory → skills → filesystem → subagent → middleware → human-in-the-loop

**핵심 차이:**
- `memory` — 항상 로드 (no progressive disclosure); 필수 규칙/선호도에 사용
- `skills` — frontmatter만 로드, 관련성 판단 시 전체 로드 (progressive disclosure); 특화 워크플로우에 사용

**Context Compression:**
- Offloading: tool call results > 20,000 tokens → backend offload
- Summarization: 컨텍스트 > `max_input_tokens`의 85% → LLM 요약 생성, 원본은 파일시스템 보존

**Runtime Context:** `context_schema` + `context` 인자로 per-run 설정 주입; 서브에이전트로 **자동 전파**

**Long-term Memory:** 기본은 단일 스레드. 스레드 간 영속은 `CompositeBackend` + `StoreBackend` 필요

## Interpretation
- Deep Agents는 LangGraph + LangChain의 기능을 직접 조합하는 대신, 공통 패턴을 미리 구성해 둔 고수준 래퍼로 이해할 수 있다.
- "agent harness"라는 정의는 framework보다 좁은 개념 — 기존 runtime(LangGraph) 위에서 동작하는 조립품이다.
- 세밀한 그래프 제어가 필요할 때는 LangGraph를 직접 쓰는 것이 더 적합할 수 있다.

## Superseded Notes
- **Old:** "Deep Agents는 어떤 저장소에 존재하는가?" — 미확인
- **New:** `github.com/langchain-ai/deepagents` — 확인됨
  Source: `deepagents-docs-overview-2026-05-18`

- **Old:** "상태 관리를 위해 LangGraph에 의존하는가?" — 미확인
- **New:** LangGraph runtime을 사용해 durable execution, streaming, human-in-the-loop 제공 — 확인됨
  Source: `deepagents-docs-overview-2026-05-18`

## Internal Implementation Map

- 소스코드 확인 필요: `create_deep_agent` 내부에서 어떤 LangGraph graph를 생성하는가?
- 추후 작성: [[Deep Agents create_deep_agent flow]]
- 추후 작성: [[Deep Agents Code Map]]

## Related Tests

- 소스코드 확인 필요.

## Open Questions

- `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가?
- filesystem tools는 SDK 내부에 있는가, 별도 패키지인가?
- subagent state는 parent agent와 어떻게 분리되는가?
- ACP integration은 어떤 프로토콜 스펙을 따르는가?
- "durable execution"이 LangGraph의 [[Checkpointing]]과 어떻게 연결되는가?
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가?
- `create_deep_agent`와 LangChain `create_agent`의 내부 구조 차이는 무엇인가?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Subagents]]
- [[Tool Calling]]
- [[Checkpointing]]
- [[Deep Agents Code Map]]
- [[Deep Agents create_deep_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

- `deepagents-docs-overview-2026-05-18`
- `deepagents-docs-context-engineering-2026-05-18`
