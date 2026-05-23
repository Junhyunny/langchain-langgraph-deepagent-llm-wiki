---
source_id: langchain-docs-products-2026-05-23
title: "LangChain — Products (Framework vs Runtime vs Harness)"
type: official_docs
framework: LangChain
status: current
confidence: high
retrieved_at: "2026-05-23"
---

# Source Summary: LangChain — Products

## Overview

LangChain 공식 문서 페이지. AI agent 개발을 위한 세 가지 제품 범주를 공식 정의한다: **Framework**, **Runtime**, **Harness**.

---

## Key Facts

### 세 범주 공식 정의

| 범주 | Value add | 사용 시점 | 예시 |
|------|-----------|----------|------|
| **Framework** | Abstractions, Integrations | 빠른 시작, 팀 표준화 | LangChain, Vercel AI SDK, CrewAI, OpenAI Agents SDK, Google ADK, LlamaIndex |
| **Runtime** | Durable execution, Streaming, HITL, Persistence | 낮은 수준 제어, 장기 실행 상태 기반 워크플로 | LangGraph, Temporal, Inngest |
| **Harness** | Predefined tools, Prompts, Subagents | 더 자율적인 에이전트, 복잡하고 비결정적인 작업 | Deep Agents SDK, Claude Agent SDK, Manus |

### LangChain (Framework)

- 추상화 제공: structured content blocks, agent loop, middleware
- **LangGraph 위에 빌드되어 있음** (단, LangGraph를 몰라도 LangChain 사용 가능)
- 사용 시점: 빠른 agent 빌드, 표준 추상화 필요, 복잡한 오케스트레이션 없는 단순 app

### LangGraph (Runtime)

- 장기 실행 상태 기반 agent를 위한 낮은 수준 오케스트레이션 프레임워크 및 런타임
- 기능: durable execution (실패 시 재개), streaming, human-in-the-loop, thread-level + cross-thread persistence, 낮은 수준 제어
- **LangChain 1.0은 LangGraph 위에 빌드됨**
- 사용 시점: 세밀한 오케스트레이션 제어, 복잡한 결정론적+비결정적 워크플로

### Deep Agents SDK (Harness)

- **Opinionated, batteries-included 프레임워크**
- **LangGraph 위에 빌드됨**
- 기능: planning capabilities (to-do list), task delegation (subagents), file system (pluggable storage backends), token management (대화 히스토리 요약 + 대형 tool result eviction)
- 사용 시점: 장기 실행 에이전트, 복잡한 멀티 스텝 작업, predefined tools (filesystem, bash), predefined prompts + subagents

### Feature Comparison (공식 테이블)

| Feature | LangChain | LangGraph | Deep Agents |
|---------|-----------|-----------|-------------|
| Short-term memory | ✅ | ✅ | `StateBackend` |
| Long-term memory | ✅ | ✅ | ✅ |
| Skills | ✅ (multi-agent skills) | — | ✅ |
| Subagents | ✅ (multi-agent subagents) | Subgraphs | ✅ |
| Human-in-the-loop | middleware | Interrupts | `interrupt_on` parameter |
| Streaming | ✅ | ✅ | ✅ |

---

## Interpretation

- Framework/Runtime/Harness 분류는 LangChain의 **공식 포지셔닝**이다. 외부 분석이 아니다.
- "Harness" 개념은 opinionated scaffold — coding agent처럼 미리 준비된 도구 + 프롬프트 + 서브에이전트를 제공하는 레이어다.
- LangGraph에 "Skills"가 없다는 점은 주목할 만하다. Skills는 LangChain과 Deep Agents에만 존재한다.
- Deep Agents가 LangGraph 위에 빌드됨 = Harness는 Runtime의 추상화 레이어다.
- 세 범주는 계층적이다: Harness → Runtime → (Low-level). Framework는 Runtime과 같은 레벨이거나 위에 있다.

---

## Open Questions

- LangChain multi-agent "skills"와 Deep Agents "skills"는 동일한 개념인가?
- Deep Agents의 "token management" (summarization + eviction)은 LangChain의 short-term memory와 어떻게 다른가?
- "pluggable storage backends"는 어떤 backend를 지원하는가? (S3, local, memory?)
- Temporal, Inngest가 LangGraph와 동일 범주(Runtime)라면 이들과 LangGraph의 차이점은?

---

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Agent Harness]]
- [[LangChain vs LangGraph vs Deep Agents]]
- [[Subagents]]
- [[Memory]]

## Sources

- `langchain-docs-products-2026-05-23`
