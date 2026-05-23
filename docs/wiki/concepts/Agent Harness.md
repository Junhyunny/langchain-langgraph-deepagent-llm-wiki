---
type: concept
framework:
  - Deep Agents
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-products-2026-05-23
---

# Agent Harness

## Summary

Agent Harness는 AI agent 개발을 위한 세 가지 제품 범주 중 하나다. **Opinionated, batteries-included** 프레임워크로, 미리 정의된 도구·프롬프트·서브에이전트를 제공한다.

Source: `langchain-docs-products-2026-05-23`

## Why It Matters

- [[LangChain]](Framework)과 [[LangGraph]](Runtime)만으로는 복잡하고 비결정적인 장기 작업을 위해 많은 boilerplate가 필요하다.
- Harness는 그 위에 context engineering, planning, file system, token management를 **미리 조립**해 제공한다.
- "Harness를 쓴다" = Runtime의 낮은 수준 제어를 포기하는 대신 즉시 사용 가능한 에이전트 역량을 얻는 트레이드오프다.

## Key Concepts

- [[Deep Agents]] — 대표적인 Harness 구현체
- [[LangGraph]] — Harness가 올라가는 Runtime 레이어
- [[Subagents]] — Harness의 핵심 기능 중 하나
- [[Context Engineering]] — token management, 히스토리 요약 등
- [[Memory]] — long-term memory 지원

## Harness의 특성 (Verified)

| 기능 | 설명 |
|------|------|
| **Planning capabilities** | to-do list 기반 멀티 태스크 추적 |
| **Task delegation** | subagents로 작업을 위임하고 컨텍스트를 격리 |
| **File system** | pluggable storage backends를 통한 파일 읽기/쓰기 |
| **Token management** | 대화 히스토리 요약 + 대형 tool result eviction |

Source: `langchain-docs-products-2026-05-23`

## 현존하는 Harness 구현체 (Verified)

| 이름 | 제공사 |
|------|--------|
| Deep Agents SDK | LangChain (langchain-ai) |
| Claude Agent SDK | Anthropic |
| Manus | Manus |

Source: `langchain-docs-products-2026-05-23`

## Deep Agents SDK 구체 특성

- [[LangGraph]] 위에 빌드됨 (Runtime의 durable execution 상속)
- LangGraph의 `checkpointer` + `_DeepAgentState` (`DeltaChannel`) 활용
- `create_deep_agent()` 함수로 harness 조립
- middleware 기반 구성: planning, filesystem, permissions, subagents, context, code execution, HITL, profiles

*Source: `deepagents-source-graph-2026-05-19`, `deepagents-docs-harness-2026-05-19`*

## Framework vs Runtime vs Harness 위치

```
Harness (Deep Agents SDK)
    └── Runtime (LangGraph)
Framework (LangChain)
    └── Runtime (LangGraph)
```

- Harness와 Framework 모두 Runtime 위에 올라간다.
- 단, Harness는 Runtime의 낮은 수준 API를 직접 노출하지 않고 opinionated 추상화로 감싼다.

## Related Pages

- [[Deep Agents]]
- [[LangChain]]
- [[LangGraph]]
- [[LangChain vs LangGraph vs Deep Agents]]
- [[Subagents]]
- [[Context Engineering]]
- [[Memory]]

## Open Questions

- "pluggable storage backends"는 어떤 backend를 지원하는가? (S3, local, memory?)
- Harness 범주에서 Claude Agent SDK와 Deep Agents SDK의 설계 철학 차이는?
- Harness가 Runtime의 `interrupt` / checkpoint를 어떻게 추상화하는가?
- 미래에 새로운 Harness가 LangGraph 없이 다른 Runtime 위에 올라갈 수 있는가?

## Sources

- `langchain-docs-products-2026-05-23`
- `deepagents-source-graph-2026-05-19`
- `deepagents-docs-harness-2026-05-19`
