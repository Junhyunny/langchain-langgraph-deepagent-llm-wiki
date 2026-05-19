---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-19
sources:
  - deepagents-docs-harness-2026-05-19
  - deepagents-source-graph-2026-05-19
---

# Subagents

## 요약

Subagents는 더 큰 워크플로의 일부로 부모(오케스트레이션) agent에 의해 호출되는 agent다. 각 서브에이전트는 자신만의 도구, 상태, 프롬프트를 가질 수 있다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

서브에이전트 오케스트레이션은 복잡한 멀티 에이전트 시스템의 핵심 패턴이다. 부모 agent가 서브에이전트에 어떻게 위임하는지, 컨텍스트가 어떻게 전달되는지, 결과가 어떻게 수집되는지를 이해하는 것은 확장 가능한 agent 파이프라인을 구축하는 데 필수적이다.

## 핵심 개념

- **Orchestrator** — 계획하고 위임하는 최상위 agent
- **Subagent** — 하위 작업을 수행하는 특화된 agent
- **위임** — 부모에서 서브에이전트로 작업 또는 컨텍스트를 전달함
- **집계** — 여러 서브에이전트의 결과를 수집하고 병합함
- **Handoff** — agent 간 제어를 넘김

## 프레임워크별 동작

### LangChain

- 서브에이전트는 도구로 감싸서 [[Tool Calling]]을 통해 호출할 수 있다
- *소스 필요.*

### LangGraph

- 서브에이전트는 노드로 호출되는 별도의 `StateGraph` 인스턴스일 수 있다
- 또는 병렬 디스패치를 위해 `Send`로 구현할 수 있다
- *소스 필요.*

### Deep Agents
*Source: `deepagents-docs-harness-2026-05-19`, `deepagents-source-graph-2026-05-19`*

**Verified Facts:**
- Main agent는 `task` tool로 subagent를 위임한다
- Subagent: **fresh context**로 실행, 자율적으로 완료 후 **단일 최종 보고서만** 반환
- Subagent는 **stateless** — 여러 메시지를 main agent에 돌려보낼 수 없다
- 3가지 타입:
  - `SubAgent` — declarative sync (name, description, system_prompt 지정)
  - `CompiledSubAgent` — pre-compiled runnable
  - `AsyncSubAgent` — remote/background (`graph_id` 필요)
- 기본 `general-purpose` subagent 자동 추가 (비활성화 가능)
- Subagent는 parent의 `interrupt_on` 상속; `CompiledSubAgent`·`AsyncSubAgent`는 상속 안 함
- Subagent는 parent의 `permissions` 상속; 자체 선언 시 대체

**이점 (원문 기준):**
- Context isolation — subagent 작업이 main context를 오염시키지 않음
- 병렬 실행 가능
- Specialization — tool/설정을 subagent별로 다르게 구성
- Token efficiency — 무거운 작업 context가 단일 결과로 압축됨

**task tool 제거 방법:** HarnessProfile로 auto-added GP subagent 비활성화 + `subagents=`에 sync subagent 없음.
`excluded_middleware`로 `SubAgentMiddleware` 제거 시도 → **ValueError**

## 미해결 질문

- LangChain / LangGraph에서 orchestrator → subagent 컨텍스트 전달 방식은? (소스 필요)
- Deep Agents: `SubagentTransformer`의 scope 활용 방식은? (`_subagent_transformer.py` 확인 필요)
- Deep Agents: subagent가 실패할 때 main agent는 어떻게 처리하는가?
- Deep Agents: `SubAgentMiddleware` 내부에서 context isolation이 구체적으로 어떻게 구현되는가?

**해소됨:**
- ✅ Deep Agents subagent 상태는 격리됨 — stateless, fresh context로 실행 (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ 결과 집계: 단일 최종 보고서만 반환 (Source: `deepagents-docs-harness-2026-05-19`)

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Context Engineering]]
- [[Deep Agents create_deep_agent flow]]

## 소스

- `deepagents-docs-harness-2026-05-19`
- `deepagents-source-graph-2026-05-19`
