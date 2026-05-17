---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Memory

## 요약

Memory는 LLM agent가 여러 턴, 세션, 작업에 걸쳐 정보를 유지하고 다시 불러올 수 있게 하는 메커니즘을 뜻한다. Memory는 단기적일 수도 있고(세션 내), 장기적일 수도 있다(세션 간).

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

Memory가 없으면 모든 agent 턴은 무상태다. Memory는 연속성, 개인화, 누적된 지식을 가능하게 한다. 프레임워크가 Memory를 어떻게 구현하는지 이해하면 버그를 추적하고 더 나은 agent를 설계하는 데 도움이 된다.

## 핵심 개념

- **단기 메모리** — 세션 내 컨텍스트에 포함된 메시지 히스토리
- **장기 메모리** — 세션 간에 다시 불러오는 외부 저장소
- **에피소드 메모리** — 특정 과거 사건 또는 상호작용
- **의미 메모리** — 일반적인 사실 또는 지식
- **메모리 저장소** — 장기 메모리를 위한 외부 데이터베이스
- **메모리 검색** — 저장소에서 관련 메모리를 선택하는 것

## 프레임워크별 동작

### LangChain

- `ConversationBufferMemory`, `ConversationSummaryMemory` 등
- 체인 또는 agent에 연결된다
- *소스 필요.*

### LangGraph

- 상태는 스레드 내부에서 단기 메모리 역할을 한다
- 장기 메모리는 외부 저장소(예: `InMemoryStore`, 벡터 저장소)를 통해 제공된다
- *소스 필요.*

### Deep Agents

- 추후 작성
- *소스 필요.*

## 미해결 질문

- LangGraph의 `MemorySaver`는 대화 Memory와 어떤 관련이 있는가?
- LangGraph에서 checkpointer와 메모리 저장소의 차이는 무엇인가?
- 장기 메모리는 어떻게 검색되어 컨텍스트에 주입되는가?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Checkpointing]]
- [[Context Engineering]]

## 소스

*아직 없음.*
