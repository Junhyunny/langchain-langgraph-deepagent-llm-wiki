---
source_id: langchain-source-memory-api-2026-05-23
title: "LangChain — Memory API 현황 (RunnableWithMessageHistory deprecated, SummarizationMiddleware)"
type: source_code
framework: LangChain
url: "https://github.com/langchain-ai/langchain/tree/master/libs"
retrieved_at: "2026-05-23"
status: current
used_by:
  - "docs/wiki/concepts/Memory.md"
---

# Summary

LangChain v1.x의 메모리 API 현황 — deprecated API 확인, 현재 권장 패턴 정리.

---

## 확인된 사실 (소스 기반)

### RunnableWithMessageHistory — deprecated

- **deprecated since: langchain-core 1.3.3** (2026-05-05)
- **제거 예정: 2.0.0**
- 대체: **LangGraph's built-in persistence** (checkpointer)
- 경고 메시지 (소스 확인):
  `"RunnableWithMessageHistory is deprecated. Use LangGraph's built-in persistence instead."`
- Source: `libs/core/langchain_core/runnables/history.py`

### MessageGraph — deprecated

- **deprecated since: langgraph 1.0.0**
- **제거 예정: 2.0.0**
- 대체: `StateGraph` with `MessagesState` (messages key + add_messages reducer)
- Source: `langgraph/graph/message.py`

### ConversationBufferMemory / ConversationSummaryMemory

- `langchain/memory/buffer.py`, `langchain/memory/summary.py` → **경로 404 (파일 없음)**
- `langchain-community` 패키지 **2026-05-22 sunset 선언** (issue #674)
- 명시적 deprecated 선언 문서는 미발견 — 파일 자체가 현재 LangChain 1.x에 존재하지 않음
- ⚠️ 공식 마이그레이션 가이드 URL (python.langchain.com/docs/versions/migrating_memory/)는 403으로 접근 불가

### SummarizationMiddleware — 현재 메모리 요약 API

```python
# langchain.agents.middleware에 정의됨
# 토큰 한도 접근 시 자동 요약 트리거
from langchain.agents.middleware.summarization import SummarizationMiddleware

middleware = SummarizationMiddleware(
    trigger=("tokens", 3000),  # 또는 ("messages", 50), ("fraction", 0.8)
    keep=5,                    # 보존할 최근 메시지 수
)
```

- `before_model()` hook에서 threshold 초과 시 트리거
- 레거시 파라미터 `max_tokens_before_summary`, `messages_to_keep`은 deprecated
- 대체: `trigger`, `keep` 파라미터

---

## 현재 권장 패턴

### 단기 메모리 (thread-scoped)

```python
from langgraph.graph import StateGraph, MessagesState
from langchain.agents import create_agent

# MessagesState: messages: Annotated[list[AnyMessage], add_messages]
agent = create_agent(
    model="...",
    checkpointer=InMemorySaver(),  # thread-scoped state 영속
)
# same thread_id로 재호출하면 이전 대화 히스토리 유지
```

### 장기 메모리 (cross-session)

```python
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
agent = create_agent(
    model="...",
    store=store,  # cross-thread 공유 메모리
)
# ToolRuntime.store로 tool 내부에서 store 접근
```

### 대화 히스토리 자동 요약

```python
from langchain.agents.middleware.summarization import SummarizationMiddleware

agent = create_agent(
    model="...",
    middleware=[SummarizationMiddleware(trigger=("fraction", 0.8), keep=10)],
    checkpointer=InMemorySaver(),
)
```

---

## 결론

LangChain 1.x (2026년 기준)에서 레거시 메모리 API(`ConversationBufferMemory`, `RunnableWithMessageHistory`, `MessageGraph`)는 사실상 제거 또는 deprecated 상태다. 현재 권장 패턴은 **LangGraph checkpointer** (단기) + **BaseStore** (장기) + **SummarizationMiddleware** (컨텍스트 압축)이다.

---

## 미확인 사항

- `ConversationBufferMemory`의 명시적 deprecated 선언 문서 위치 — Needs Source
- `langchain-community` sunset 이후 공식 마이그레이션 가이드 접근 방법 (현재 403)
- `SummarizationMiddleware` 내부 요약 모델 선택 방법 — Needs Source
