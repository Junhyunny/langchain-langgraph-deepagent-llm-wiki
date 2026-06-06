---
type: comparison
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: partial
confidence: high
last_reviewed: 2026-06-06
sources:
  - langchain-docs-products-2026-05-23
  - deepagents-docs-overview-2026-05-18
  - langgraph-docs-durable-execution-2026-05-20
  - deepagents-source-subagents-2026-05-23
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
- Durable execution: 실패 후 재개, 장기 실행. 3가지 durability 모드 지원:
  - `exit` — 그래프 종료 시점에만 저장. 성능 최적, 프로세스 크래시 복구 불가
  - `async` — 다음 스텝 실행 중 비동기 저장. 성능/내구성 균형, 소규모 크래시 윈도우 존재
  - `sync` — 다음 스텝 시작 전 동기 저장. 최강 내구성, 오버헤드 있음
- Resume은 동일 Python call stack을 재개하지 않음. 중단 노드 시작점부터 replay
- Thread-level + cross-thread persistence
- 사용 시점: 세밀한 제어, durable execution, 결정론적+비결정론적 스텝 혼합

Source: `langgraph-docs-durable-execution-2026-05-20`

### Deep Agents SDK (Harness — [[Agent Harness]])
- Opinionated, batteries-included
- Planning: to-do list 기반 멀티 태스크 추적
- Task delegation: subagents로 컨텍스트 격리
- File system: pluggable storage backends (in-memory / local disk / durable store / sandbox / custom)
- Token management: 히스토리 요약 + 대형 tool result eviction
- LangGraph runtime 위에서 durable execution, streaming, HITL 상속
- 저장소 구성: Deep Agents SDK (에이전트 패키지) + Deep Agents Code (터미널 코딩 에이전트) + ACP integration (코드 에디터 커넥터)
- 사용 시점 (공식 문서):
  - 복잡한 multi-step 태스크 (planning and decomposition 필요)
  - 대규모 context 관리 (filesystem tools, summarization)
  - shell 명령어 실행 (`execute` tool)
  - specialized subagent에 작업 위임 (context isolation)
  - 대화/스레드 간 memory 지속
  - human-in-the-loop workflows (sensitive operations 승인)
  - 더 단순한 에이전트 → LangChain `create_agent` 또는 직접 LangGraph 사용 권장

Source: `langchain-docs-products-2026-05-23`, `deepagents-docs-overview-2026-05-18`

## Subagent 상태 격리 비교 (Verified)

각 프레임워크가 subagent(하위 에이전트)에게 상태를 전달하는 방식이 다르다.

| | LangChain | LangGraph | Deep Agents |
|---|---|---|---|
| **Subagent 단위** | 없음 (단일 agent loop) | Subgraph (별도 StateGraph) | `task` tool + `SubAgentMiddleware` |
| **상태 격리 방식** | 해당 없음 | 별도 state schema 정의 | `_EXCLUDED_STATE_KEYS` 필터 |
| **격리 대상** | — | schema가 다른 key | `messages`, `todos`, `structured_response`, `skills_metadata` 등 |
| **결과 전달 방식** | — | parent ↔ child schema 호환 key | subagent 마지막 AIMessage → ToolMessage |
| **병렬 실행** | RunnableParallel | Send API | 단일 AIMessage 내 다중 task call |

### Deep Agents `_EXCLUDED_STATE_KEYS` 동작 (Verified)

```python
_EXCLUDED_STATE_KEYS = {
    "messages", "todos", "structured_response",
    "skills_metadata", "skills_load_errors", "memory_contents",
}
```

- **입력 필터링:** parent의 메시지 히스토리 대신 단일 `HumanMessage(task description)`만 subagent에 전달
- **출력 필터링:** subagent의 마지막 비어있지 않은 AIMessage text만 `ToolMessage`로 parent에 반환
- **로컬 검증 완료 (2026-05-30):** `messages`, `todos`는 subagent 입력에서 제외됨, 일반 state key(`project_id` 등)는 전달됨

Source: `deepagents-source-subagents-2026-05-23`

---

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
- `deepagents-docs-overview-2026-05-18`
- `langgraph-docs-durable-execution-2026-05-20`
- `deepagents-source-subagents-2026-05-23`
