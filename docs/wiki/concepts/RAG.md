---
type: concept
framework:
  - LangChain
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-docs-rag-2026-05-23
  - langchain-source-text-splitters-2026-05-23
  - langchain-source-dynamic-prompt-2026-05-23
  - langchain-source-vectorstore-embeddings-2026-05-23
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

> ⚠️ **Possible Conflict — @dynamic_prompt 서명 불일치**
>
> 공식 RAG 문서는 아래 패턴을 보여줬지만, 실제 소스코드(`langchain-source-dynamic-prompt-2026-05-23`)의 `@dynamic_prompt` API는 다른 서명을 요구한다.
>
> - **RAG 문서 예제:** `(user_query: str) -> list[SystemMessage, HumanMessage]`
> - **실제 소스 API:** `(request: ModelRequest) -> str | SystemMessage`
>
> 두 패턴은 다르다. RAG 문서 예제가 오래됐거나, 다른 decorator/패턴을 가리킬 가능성이 있다. 확인 전까지 아래 코드를 그대로 사용하지 말 것.

```python
# ⚠️ 아래 서명은 실제 @dynamic_prompt API와 불일치 — 검증 필요
@dynamic_prompt
def rag_prompt(user_query: str) -> list:
    retrieved_docs = vector_store.similarity_search(user_query, k=2)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return [
        SystemMessage(f"Answer using the following context:\n\n{docs_content}"),
        HumanMessage(user_query),
    ]
```

**실제 `@dynamic_prompt` 올바른 사용법** (소스코드 기준):
```python
from langchain.agents.middleware import dynamic_prompt
from langchain.agents.middleware.types import ModelRequest

@dynamic_prompt
def rag_system_prompt(request: ModelRequest) -> str:
    # state나 runtime에서 쿼리를 가져와야 함
    # retrieve + context 주입 → str 반환
    docs = vector_store.similarity_search(request.state["messages"][-1].content, k=2)
    context = "\n\n".join(doc.page_content for doc in docs)
    return f"Answer using the following context:\n\n{context}"

agent = create_agent(model, middleware=[rag_system_prompt])
```

Source (RAG 문서 패턴): `langchain-docs-rag-2026-05-23`
Source (실제 API): `langchain-source-dynamic-prompt-2026-05-23`

## 인덱싱 파이프라인

### 1. Document Loaders

```python
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
```

다양한 형식 지원: PDF, Word, CSV, HTML, Markdown, DB, API 등
Source: `langchain-docs-rag-2026-05-23`

### 2. Text Splitting

권장: `RecursiveCharacterTextSplitter`

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,  # 청크 경계 문맥 단절 방지
    # separators 기본값: ["\n\n", "\n", " ", ""]
)
splits = text_splitter.split_documents(docs)
```

**내부 알고리즘 (소스 기반):**
- separators 리스트를 순서대로 순회 — 첫 번째로 텍스트에서 매칭되는 구분자 선택
- 선택된 구분자로 분할 → `chunk_size` 초과 조각은 남은 구분자로 **재귀** 분할
- `_merge_splits()`로 작은 조각들을 `chunk_overlap`을 지키며 병합
- 기본 분할 우선순위: **단락(`\n\n`) → 줄(`\n`) → 단어(` `) → 문자(`""`)**

Source (동작 설명): `langchain-docs-rag-2026-05-23`
Source (내부 구현): `langchain-source-text-splitters-2026-05-23`

**TextSplitter 공통 파라미터:**

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `chunk_size` | `4000` | 청크 최대 크기 |
| `chunk_overlap` | `200` | 청크 간 겹치는 문자 수 |
| `keep_separator` | `True` (Recursive) | 구분자 유지 위치 |
| `add_start_index` | `False` | 메타데이터에 시작 인덱스 추가 |

**언어별 최적 설정:**
```python
from langchain_text_splitters import Language

# 코드 분할
py_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1000, chunk_overlap=200,
)
# Python separators: ["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""]
```

Source: `langchain-source-text-splitters-2026-05-23`

`chunk_overlap` 이유: 청크 경계에서 문맥 단절 방지. 인접 청크끼리 일부 내용이 겹쳐 문맥 연속성 유지.

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

**search_type 옵션 (소스 검증됨):**

| search_type | 파라미터 | 내부 메서드 | 설명 |
|-------------|----------|------------|------|
| `"similarity"` (기본) | `k=4` | `similarity_search()` | 상위 k개 유사 문서 |
| `"mmr"` | `k=4`, `fetch_k=20`, `lambda_mult=0.5` | `max_marginal_relevance_search()` | 관련성 + 다양성 균형 |
| `"similarity_score_threshold"` | `score_threshold` | `similarity_search_with_relevance_scores()` | 임계값 이상인 문서만 |

**MMR (Maximal Marginal Relevance):**
- `fetch_k`개 후보 검색 → `maximal_marginal_relevance()` 알고리즘으로 `k`개 선택
- `lambda_mult`: 1.0 = 순수 관련성, 0.0 = 순수 다양성, 0.5 = 균형 (기본)
- 유사하지만 서로 다른 문서를 선택해 검색 결과 다양성 향상

Source: `langchain-source-vectorstore-embeddings-2026-05-23`

**BaseRetriever 계약:**
```python
# 구현 시 필요한 메서드:
def _get_relevant_documents(self, query: str, *, run_manager, **kwargs) -> list[Document]: ...
# 공개 API: retriever.invoke(query)  (get_relevant_documents는 deprecated)
```

Source: `langchain-source-vectorstore-embeddings-2026-05-23`

**추가 리트리버 타입:**
- `MultiQueryRetriever` — 다양한 쿼리 변형으로 recall 향상
- `ContextualCompressionRetriever` — 관련 부분만 압축
- `BM25Retriever` — 전통적 키워드 기반 검색
- `EnsembleRetriever` — 여러 리트리버 결합

Source: `langchain-docs-rag-2026-05-23`

### Document 구조

```python
class Document:
    page_content: str       # 문서 텍스트
    metadata: dict          # 임의 메타데이터 (source, page 등)
    id: str | None          # 선택적 식별자
```

Source: `langchain-source-vectorstore-embeddings-2026-05-23`

### Embeddings 인터페이스

```python
class Embeddings(ABC):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
    # async 버전은 기본적으로 sync wrapper (native async 구현체도 있음)
```

`InMemoryVectorStore`의 기본 거리 메트릭: **cosine similarity** (높을수록 유사)

Source: `langchain-source-vectorstore-embeddings-2026-05-23`

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

**해소됨 (2026-05-23):**
- ✅ `RecursiveCharacterTextSplitter` 내부 알고리즘: separators 리스트를 순서대로 시도 → 첫 매칭 구분자로 분할 → 초과 청크 재귀 분할 → `_merge_splits()`로 병합. (Source: `langchain-source-text-splitters-2026-05-23`)
- ✅ `@dynamic_prompt` 정체: `langchain.agents.middleware.types`의 AgentMiddleware 생성 데코레이터. 서명은 `(request: ModelRequest) -> str | SystemMessage`. (Source: `langchain-source-dynamic-prompt-2026-05-23`)

**잔여 질문:**
- ⚠️ RAG 문서의 `@dynamic_prompt(user_query: str) -> list` 패턴 — 실제 API `(request: ModelRequest) -> str | SystemMessage`와 불일치. 문서 오류인가, 다른 decorator인가? — Source: `langchain-docs-rag-2026-05-23`, `langchain-source-dynamic-prompt-2026-05-23`
- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? 구버전 `OpenAIEmbeddings()`와의 차이는? — Source: `langchain-docs-rag-2026-05-23`
- `response_format="content_and_artifact"` 옵션의 정확한 의미는? — Source: `langchain-docs-rag-2026-05-23`
- FAISS `similarity_search`의 내부 알고리즘은? (L2 거리 기본값인가?) — Needs Source
- `as_retriever()`의 `search_type` 옵션: `similarity`, `mmr`, `similarity_score_threshold` 차이는? — Needs Source
- MMR(Maximal Marginal Relevance)의 구체적인 작동 방식은? — Needs Source
- `BaseRetriever`의 `get_relevant_documents` 메서드 계약은? — Needs Source
- `_merge_splits()`의 `chunk_overlap` 구현 방식 — 슬라이딩 윈도우 방식인가? — Source: `langchain-source-text-splitters-2026-05-23`

## 관련 페이지

- [[LangChain]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]
- [[LangChain Code Map]]

## 소스 코드 참조

- 패키지: `langchain-text-splitters` (별도 패키지)
- 파일: `libs/text-splitters/langchain_text_splitters/character.py`, `base.py`
- 커밋: UNKNOWN (2026-05-23 기준)

## 소스

- `langchain-docs-rag-2026-05-23`
- `langchain-source-text-splitters-2026-05-23`
- `langchain-source-dynamic-prompt-2026-05-23`
