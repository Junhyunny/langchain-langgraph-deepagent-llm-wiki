---
type: comparison
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-products-2026-05-23
---

# LangChain vs LangGraph vs Deep Agents

## 요약

LangChain은 세 제품을 **Framework / Runtime / Harness** 세 범주로 공식 분류한다.
Source: `langchain-docs-products-2026-05-23`

빠른 의사결정 규칙:
- 빠르게 agent를 만들고 싶거나 표준 추상화가 필요하면 **LangChain** (Framework)
- 세밀한 제어, 장기 실행, 체크포인팅이 필요하면 **LangGraph** (Runtime)
- 복잡하고 비결정적인 작업, 자율적인 에이전트가 필요하면 **Deep Agents SDK** (Harness)

## 공식 범주 분류 (Verified)

| | Framework | Runtime | Harness |
|---|---|---|---|
| **Value add** | Abstractions, Integrations | Durable execution, Streaming, HITL, Persistence | Predefined tools, Prompts, Subagents |
| **사용 시점** | 빠른 시작, 팀 표준화 | 낮은 수준 제어, 장기 실행 상태 기반 워크플로 | 더 자율적인 에이전트, 복잡·비결정적 작업 |
| **대표 제품** | LangChain, CrewAI, OpenAI Agents SDK, Google ADK | LangGraph, Temporal, Inngest | Deep Agents SDK, Claude Agent SDK, Manus |

Source: `langchain-docs-products-2026-05-23`

## Feature Comparison (공식 테이블, Verified)

| Feature | LangChain | LangGraph | Deep Agents |
|---------|-----------|-----------|-------------|
| Short-term memory | ✅ | ✅ | `StateBackend` |
| Long-term memory | ✅ | ✅ | ✅ |
| Skills | ✅ (multi-agent skills) | — | ✅ |
| Subagents | ✅ (multi-agent subagents) | Subgraphs | ✅ |
| Human-in-the-loop | middleware | Interrupts | `interrupt_on` parameter |
| Streaming | ✅ | ✅ | ✅ |

Source: `langchain-docs-products-2026-05-23`

## 계층 관계 (Verified)

- [[LangChain]] 1.0은 [[LangGraph]] 위에 빌드됨
- [[Deep Agents]] SDK는 [[LangGraph]] 위에 빌드됨
- Harness → Runtime 순서의 계층 구조

Source: `langchain-docs-products-2026-05-23`

## 각 제품의 핵심 특성 (Verified)

### LangChain (Framework)
- 추상화: structured content blocks, agent loop, middleware
- LangGraph를 몰라도 사용 가능
- 사용 시점: 단순 agent app, 표준 추상화, 복잡한 오케스트레이션 불필요 시

### LangGraph (Runtime)
- 낮은 수준 오케스트레이션 프레임워크
- Durable execution: 실패 후 재개, 장기 실행
- Thread-level + cross-thread persistence
- 사용 시점: 세밀한 제어, durable execution, 결정론적+비결정론적 스텝 혼합

### Deep Agents SDK (Harness — [[Agent Harness]])
- Opinionated, batteries-included
- Planning: to-do list 기반 멀티 태스크 추적
- Task delegation: subagents로 컨텍스트 격리
- File system: pluggable storage backends
- Token management: 히스토리 요약 + 대형 tool result eviction
- 사용 시점: 장기 실행, 복잡한 멀티 스텝, predefined tools (filesystem, bash), predefined prompts

Source: `langchain-docs-products-2026-05-23`

## 트레이드오프

### LangChain

**장점:**
- 단순하고 문서화가 잘 되어 있다
- 생태계가 넓다 (CrewAI, OpenAI SDK 등과 같은 범주)
- 시작하기 쉽다

**단점:**
- Framework 수준의 추상화 — 낮은 수준 제어가 필요하면 LangGraph 직접 사용 필요
- Skills는 multi-agent 패턴에서만 존재 (단일 agent에서는 미지원)

### LangGraph

**장점:**
- Durable execution, streaming, HITL, persistence 내장
- 낮은 수준 제어: 오케스트레이션을 직접 구성
- Checkpointing + 재개 내장

**단점:**
- 높은 복잡도, 보일러플레이트 많음
- Skills 개념 없음 (LangChain / Deep Agents에만 존재)
- 초기 학습 비용이 높음

### Deep Agents SDK

**장점:**
- opinionated scaffold — 도구/프롬프트/서브에이전트 즉시 사용 가능
- token management 자동화 (context engineering 내장)
- LangGraph의 durable execution 상속

**단점:**
- 높은 수준의 추상화 → 내부 구현이 가려짐
- 생태계가 상대적으로 작음 ⚠️ (소스 검증 필요)
- opinionated 설계 → 커스터마이징 제약 가능

## 예시 사용 사례

- **LangChain**: 도구를 사용하는 단순 agent, RAG 파이프라인, 빠른 프로토타입
- **LangGraph**: 재개 가능한 상태 기반 리서치 agent, human escalation이 필요한 고객 지원 봇, 복잡한 결정론적+비결정적 워크플로
- **Deep Agents SDK**: 장기 실행되는 자율 agent, 파일 시스템 작업 + 서브에이전트 위임이 필요한 coding agent 류

## Superseded Notes

기존 비교 표(가설)가 공식 문서로 대체된 항목:

| 기존 (가설) | 업데이트 (공식) | Source |
|---|---|---|
| "관계: LangChain 확장" → LangGraph | LangChain 1.0이 LangGraph 위에 빌드됨 | `langchain-docs-products-2026-05-23` |
| Deep Agents "추후 작성" 셀 다수 | HITL: `interrupt_on`, Subagents, Skills 모두 지원 | `langchain-docs-products-2026-05-23` |
| confidence: low | confidence: high (공식 소스 확보) | `langchain-docs-products-2026-05-23` |

## 실험

*아직 없음. 계획된 비교는 `docs/wiki/experiments/`를 참조한다.*

## 의사결정 시사점

- LangGraph 내부 구조 학습이 핵심이다 (LangChain과 Deep Agents 모두 LangGraph 위에 빌드됨)
- Deep Agents를 이해하려면 LangGraph를 먼저 이해해야 한다
- Framework 선택은 추상화 수준과 제어 필요성의 트레이드오프다

## 미해결 질문

- LangGraph의 체크포인트를 Deep Agents 런타임에서 사용할 수 있는가?
- 세 프레임워크는 병렬 도구 호출에서 어떻게 비교되는가?
- LangChain "Skills"와 Deep Agents "Skills"는 동일한 개념인가?
- Temporal, Inngest가 LangGraph와 같은 Runtime 범주라면, 이들과 LangGraph의 실질적 차이는?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Agent Harness]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Subagents]]
- [[Memory]]

## Sources

- `langchain-docs-products-2026-05-23`
