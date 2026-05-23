---
type: concept
framework:
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-rag-2026-05-23
---

# RAG (Retrieval-Augmented Generation)

## 요약

RAG는 외부 소스에서 가져온 사실로 생성형 AI 모델의 정확성과 신뢰성을 높이는 기법이다. LLM의 두 가지 핵심 한계인 knowledge cutoff와 hallucination을 완화한다.

## 중요한 이유

RAG는 LLM이 학습 데이터에 없는 최신 정보나 도메인 전용 지식을 다루는 핵심 패턴이다. LangChain은 RAG를 위한 완전한 파이프라인(인덱싱 + 검색 + 생성)을 내장 컴포넌트로 제공한다.

## 핵심 개념

- **Document Loaders** — 다양한 소스(PDF, HTML, CSV, DB 등)에서 문서 로드
- **Text Splitter** — 긴 문서를 context window에 맞는 청크로 분할
- **Vector Store** — 임베딩을 저장하고 의미 유사도 기반 검색 제공
- **Retriever** — 자연어 쿼리로 관련 문서를 반환하는 추상화 계층
- **RAG agent** — LLM이 검색 시점/방법을 동적으로 결정
- **RAG chain** — 항상 검색 후 생성하는 결정적 파이프라인
- **Indirect Prompt Injection** — 악성 지시가 검색 문서에 숨어 프롬프트에 들어오는 보안 위협

## 두 가지 RAG 패턴

| 패턴 | 특징 | 적합한 경우 |
|------|------|------------|
| **RAG agent** | LLM이 지능적으로 검색 시점/방법 결정, 다단계 추론 | 복잡한 쿼리, 여러 번 검색 필요 |
| **RAG chain** | 항상 검색 후 생성하는 결정적 파이프라인 | 단순 쿼리, 예측 가능성 중요 |

Source: `langchain-docs-rag-2026-05-23`

## RAG agent 패턴

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.vectorstores import InMemoryVectorStore
from langchain.embeddings import init_embeddings

embeddings = init_embeddings("openai:text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

agent = create_agent(model, [retrieve])
```

Source: `langchain-docs-rag-2026-05-23`

## RAG chain 패턴

```python
@dynamic_prompt
def rag_prompt(user_query: str) -> list:
    retrieved_docs = vector_store.similarity_search(user_query, k=2)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return [
        SystemMessage(f"Answer using the following context:\n\n{docs_content}"),
        HumanMessage(user_query),
    ]
```

Source: `langchain-docs-rag-2026-05-23`

## 인덱싱 파이프라인

### 1. Document Loaders

```python
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
```

다양한 형식 지원: PDF, Word, CSV, HTML, Markdown, DB, API 등
Source: `langchain-docs-rag-2026-05-23`

### 2. Text Splitting

권장: `RecursiveCharacterTextSplitter`

분할 우선 순서: **단락 → 문장 → 단어 → 문자**

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200  # 청크 경계 문맥 단절 방지
)
splits = text_splitter.split_documents(docs)
```

`chunk_overlap` 이유: 청크 경계에서 문맥 단절 방지. 인접 청크끼리 일부 내용이 겹쳐 문맥 연속성 유지.
Source: `langchain-docs-rag-2026-05-23`

### 3. Vector Stores

```python
embeddings = init_embeddings("openai:text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(splits)
results = vector_store.similarity_search("What is LangChain?", k=3)
```

**지원 벡터 스토어:** `InMemoryVectorStore` (개발용), Chroma, FAISS, Pinecone, Qdrant, pgvector, Weaviate, Elasticsearch 등

Source: `langchain-docs-rag-2026-05-23`

### 4. Retrievers

벡터 스토어(또는 다른 데이터 소스)에 대한 추상화 계층. 자연어 쿼리로 관련 문서 반환:

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
docs = retriever.invoke("What is LangChain?")
```

**추가 리트리버 타입:**
- `MultiQueryRetriever` — 다양한 쿼리 변형으로 recall 향상
- `ContextualCompressionRetriever` — 관련 부분만 압축
- `BM25Retriever` — 전통적 키워드 기반 검색
- `EnsembleRetriever` — 여러 리트리버 결합

Source: `langchain-docs-rag-2026-05-23`

## 보안: Indirect Prompt Injection

RAG의 중요한 보안 위협: 악성 지시가 문서에 포함되어 검색 후 프롬프트에 들어오는 공격.

**완화 방법:**
- 검색된 콘텐츠 정제 후 프롬프트 포함
- 검색 컨텍스트와 지시 사이 명시적 구분자 사용
- 이상 출력 모니터링
- 입출력 가드레일 구현

Source: `langchain-docs-rag-2026-05-23`

## Interpretation

- LangChain의 RAG는 단순한 "검색 후 붙여넣기"가 아니라 에이전트(동적) vs 체인(결정적) 두 가지 패턴을 명확히 구분한다.
- 공식 docs는 FAISS보다 `InMemoryVectorStore`를 권장 — 개발/테스트는 in-memory, 프로덕션은 Chroma/Pinecone 등으로 교체한다.
- `RecursiveCharacterTextSplitter`가 범용 텍스트 분할의 공식 권장 방법이다.

## 미해결 질문

- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? 구버전 `OpenAIEmbeddings()`와의 차이는? — Source: `langchain-docs-rag-2026-05-23`
- `@dynamic_prompt` 데코레이터는 무엇인가? LCEL chain을 대체하는 새 패턴인가? — Source: `langchain-docs-rag-2026-05-23`
- `response_format="content_and_artifact"` 옵션의 정확한 의미는? — Source: `langchain-docs-rag-2026-05-23`
- FAISS `similarity_search`의 내부 알고리즘은? (L2 거리 기본값인가?) — Needs Source
- `as_retriever()`의 `search_type` 옵션: `similarity`, `mmr`, `similarity_score_threshold` 차이는? — Needs Source
- MMR(Maximal Marginal Relevance)의 구체적인 작동 방식은? — Needs Source
- `BaseRetriever`의 `get_relevant_documents` 메서드 계약은? — Needs Source

## 관련 페이지

- [[LangChain]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]
- [[LangChain Code Map]]

## 소스

- `langchain-docs-rag-2026-05-23`
