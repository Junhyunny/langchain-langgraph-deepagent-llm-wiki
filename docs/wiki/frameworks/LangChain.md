---
type: framework
framework: LangChain
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-docs-event-streaming-2026-05-18
  - langchain-docs-messages-2026-05-23
  - langchain-docs-rag-2026-05-23
  - langchain-docs-tools-2026-05-23
---

# LangChain

## 요약

LangChain은 LLM 기반 애플리케이션을 구축하기 위한 프레임워크다. 채팅 모델, 메시지, 도구, RAG 파이프라인을 위한 추상화를 제공한다. LangGraph와 Deep Agents는 모두 LangChain 추상화 위에 구축된다.

## 중요한 이유

LangChain은 이 생태계의 기반 프레임워크다. LangGraph와 Deep Agents는 모두 LangChain 추상화 위에 구축되므로, 이를 이해하기 전에 LangChain을 이해하는 것이 필요하다.

---

## 메시지 시스템
*Source: `langchain-docs-messages-2026-05-23`*

### 메시지의 정의

메시지는 LangChain에서 **채팅 모델과 소통하는 기본 단위**다. 채팅 모델은 메시지 리스트를 입력으로 받고, AIMessage를 출력으로 반환한다.

메시지의 3가지 요소:
- **Role** — 메시지 유형 식별 (system / human / ai / tool)
- **Content** — 텍스트, 이미지, 오디오 등 멀티모달 지원
- **Metadata** — 응답 정보, 메시지 ID, 토큰 사용량

### 주요 메시지 타입 4종

| 클래스 | Role | 용도 |
|--------|------|------|
| `SystemMessage` | `system` | 모델의 동작 방식/페르소나 지정 |
| `HumanMessage` | `human` | 사용자 입력 (텍스트, 이미지 등) |
| `AIMessage` | `ai` | 모델 응답 (텍스트 + tool_calls) |
| `ToolMessage` | `tool` | tool 실행 결과를 모델에 전달 |

### AIMessage 주요 속성

- `content` — 응답 텍스트
- `tool_calls` — 모델이 호출한 도구 목록 (`[{"name": ..., "args": ..., "id": ...}]`)
- `usage_metadata` — 토큰 사용량 (input_tokens, output_tokens, total_tokens)

### ToolMessage 핵심 계약

`ToolMessage.tool_call_id`는 반드시 `AIMessage.tool_calls[i]['id']`와 일치해야 한다.

```python
# tool call 흐름
messages = [HumanMessage("What's the weather?")]
ai_message = model_with_tools.invoke(messages)
# ai_message.tool_calls = [{"name": "get_weather", "args": {...}, "id": "call_123"}]

tool_message = ToolMessage(
    content="Sunny, 72°F",
    tool_call_id="call_123",  # AIMessage의 id와 매칭 필수
    name="get_weather"
)
messages = messages + [ai_message, tool_message]
final = model.invoke(messages)
```

### 스트리밍: AIMessageChunk

```python
for chunk in model.stream("Hi"):
    chunks.append(chunk)
    full_message = chunk if full_message is None else full_message + chunk
```

---

## 도구(Tool)
*Source: `langchain-docs-tools-2026-05-23`*

### @tool 데코레이터

가장 간단한 도구 생성 방법. **함수의 docstring이 모델에게 보이는 도구 설명이 된다.**

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

**필수 규칙:**
- **타입 힌트 필수** — 도구의 입력 스키마를 정의
- **Docstring이 핵심** — 모델이 언제 이 도구를 사용할지 판단하는 근거

### ToolRuntime — 도구 내 컨텍스트 접근

| 컴포넌트 | 설명 | 사용 사례 |
|---------|------|---------|
| **State** | 현재 대화의 단기 메모리 | 대화 이력 접근 |
| **Context** | 호출 시 전달된 불변 설정 | 사용자 ID 기반 개인화 |
| **Store** | 대화 간 영속적 장기 메모리 | 사용자 선호도 저장 |
| **Stream Writer** | 실시간 업데이트 발행 | 진행 상황 표시 |
| **Execution Info** | Thread ID, run ID | 스레드/런 식별 |

### 도구 반환값 3가지

| 반환 타입 | 용도 |
|---------|------|
| `string` | 평문 결과 → ToolMessage 자동 변환 |
| `object` | 구조화 데이터 → 직렬화 후 모델 전달 |
| `Command` | 상태 업데이트 필요 시 |

### 도구 실행 흐름

LangChain에서 도구는 `create_agent`로 에이전트에 등록. LangGraph에서는 `ToolNode`가 실행 처리.

### ⚠️ LCEL 상태 (중요)

> 2026년 기준 새 LangChain docs에 LCEL/Runnable 전용 페이지가 없다.
> 새 docs는 `create_agent` + `AgentMiddleware` + `ToolRuntime` 패턴 중심으로 재편됨.

---

## RAG (Retrieval-Augmented Generation)
*Source: `langchain-docs-rag-2026-05-23`*

### RAG의 목적

RAG는 외부 소스에서 가져온 사실로 LLM의 정확성을 높이는 기법이다.

해결하는 LLM 한계:
1. **Knowledge cutoff** — 학습 데이터 이후 정보 없음
2. **Hallucinations** — 그럴듯하지만 부정확한 정보 생성

### 두 가지 RAG 패턴

| 패턴 | 특징 | 적합한 경우 |
|------|------|------------|
| RAG agent | 지능적으로 검색 시점 결정 | 복잡한 쿼리 |
| RAG chain | 항상 검색 후 생성 (결정적) | 단순 쿼리 |

### 인덱싱 파이프라인 4단계

**1. Document Loaders** — PDF, Word, CSV, HTML, Markdown, DB 등:
```python
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
```

**2. Text Splitting** — 권장: `RecursiveCharacterTextSplitter` (단락→문장→단어→문자 순):
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200  # 앞뒤 문맥 보존
)
splits = text_splitter.split_documents(docs)
```

**3. Vector Stores** — 임베딩 기반 의미 유사도 검색:
```python
from langchain.embeddings import init_embeddings
from langchain.vectorstores import InMemoryVectorStore

embeddings = init_embeddings("openai:text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(splits)
results = vector_store.similarity_search("What is LangChain?", k=3)
```

지원 벡터 스토어: InMemoryVectorStore, Chroma, FAISS, Pinecone, Qdrant, pgvector, Weaviate, Elasticsearch

**4. Retrievers** — 벡터 스토어에 대한 추상화 계층:
```python
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
docs = retriever.invoke("What is LangChain?")
```

추가 리트리버: `MultiQueryRetriever`, `ContextualCompressionRetriever`, `BM25Retriever`, `EnsembleRetriever`

### 보안: Indirect Prompt Injection

RAG의 주요 보안 위협 — 악성 지시가 문서에 포함되어 검색 후 프롬프트에 삽입되는 공격.

완화: 검색 콘텐츠 정제, 명시적 구분자, 입출력 가드레일

---

## Event Streaming
*Source: `langchain-docs-event-streaming-2026-05-18`*

- 권장: `stream_events(..., version="v3")`
- 리턴: 타입화된 프로젝션이 있는 run object

| 프로젝션 | 용도 |
|---|---|
| `stream.messages` | LLM 호출별 메시지 스트림 |
| `stream.tool_calls` | tool 실행 라이프사이클 |
| `stream.values` | agent state 스냅샷 |
| `stream.output` | 최종 agent state |
| `stream.subgraphs` | 중첩 그래프 실행 |
| `stream.extensions` | 커스텀 transformer 프로젝션 |

---

## LangGraph와의 관계 (확인됨)

> "LangChain agents are built on LangGraph, so they support the same streaming stack"
> *Source: `langchain-docs-event-streaming-2026-05-18`*

LangChain의 `create_agent`는 LangGraph 위에 구축됨.

---

## 핵심 추상화

- `BaseChatModel` — 모든 LLM 통합의 기본 클래스
- `BaseMessage` / 4종 메시지 클래스 — 표준 메시지 타입 계층
- `BaseRetriever` — 문서 검색 추상화
- `Tool` / `@tool` 데코레이터 — LLM에 노출되는 외부 기능
- `create_agent()` — LangGraph 기반 에이전트 생성

## Possible Conflict

기존 문서에서 `Runnable`, `AgentExecutor`, `LCEL |` 연산자를 핵심 추상화로 정리했지만,
2026년 공식 docs는 `create_agent` + `AgentMiddleware` 패턴으로 재편됨.
LCEL이 여전히 지원되는지 여부는 추가 확인 필요.
Source: `langchain-docs-tools-2026-05-23`

---

## 미해결 질문

- `create_agent`의 내부 구현은 어떻게 동작하는가?
- `AgentMiddleware`로 에러 핸들링을 구성하는 방법은?
- LCEL `RunnableLambda` / `RunnableParallel`은 완전히 deprecated인가?
- `init_embeddings("openai:...")` 형식은 구버전 `OpenAIEmbeddings()`와 어떤 차이가 있는가?
- `@dynamic_prompt` 데코레이터는 어떤 API인가?
- `AgentExecutor`는 도구 호출 루프를 언제 멈출지 어떻게 결정하는가?

## 관련 페이지

- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Memory]]
- [[LangChain Code Map]]
- [[LangChain create_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

- `langchain-docs-event-streaming-2026-05-18`
- `langchain-docs-messages-2026-05-23`
- `langchain-docs-rag-2026-05-23`
- `langchain-docs-tools-2026-05-23`
