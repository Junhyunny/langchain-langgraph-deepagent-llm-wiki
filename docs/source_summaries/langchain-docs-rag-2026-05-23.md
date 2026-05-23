---
type: source_summary
source_id: langchain-docs-rag-2026-05-23
framework:
  - LangChain
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://docs.langchain.com/oss/python/langchain/rag"
---

# Source Summary: LangChain RAG

## Key Facts

### RAG의 목적

RAG는 외부 소스에서 가져온 사실로 생성형 AI 모델의 정확성과 신뢰성을 높이는 기법이다.

RAG가 해결하는 LLM의 두 가지 한계:
1. **Knowledge cutoff** — 학습 데이터 이후 정보 없음
2. **Hallucinations** — 그럴듯하지만 부정확한 정보 생성

### 두 가지 RAG 패턴

| 패턴 | 특징 | 적합한 경우 |
|------|------|------------|
| RAG agent | 지능적으로 검색 시점/방법 결정, 다단계 추론 | 복잡한 쿼리, 여러 번 검색 필요 |
| RAG chain | 항상 검색 후 생성하는 결정적 파이프라인 | 단순 쿼리, 항상 검색 필요한 경우 |

### RAG agent 패턴

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

### RAG chain 패턴

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

### 인덱싱 파이프라인

#### 1. Document Loaders

다양한 형식(PDF, Word, CSV, HTML, Markdown, DB, API 등) 지원:
```python
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
```

#### 2. Text Splitting

대형 문서를 context window에 맞는 청크로 분할. **권장: `RecursiveCharacterTextSplitter`**

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200  # 앞뒤 문맥 보존을 위한 오버랩
)
splits = text_splitter.split_documents(docs)
```

RecursiveCharacterTextSplitter 분할 우선 순서: 단락 → 문장 → 단어 → 문자

**청크 오버랩(chunk_overlap) 이유:** 청크 경계에서 문맥 단절 방지. 인접 청크끼리 일부 내용이 겹쳐 문맥 연속성 유지.

#### 3. Vector Stores

임베딩을 사용한 의미 기반 유사도 검색:
```python
embeddings = init_embeddings("openai:text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(splits)
results = vector_store.similarity_search("What is LangChain?", k=3)
```

**지원 벡터 스토어:** InMemoryVectorStore, Chroma, FAISS, Pinecone, Qdrant, pgvector, Weaviate, Elasticsearch 등

#### 4. Retrievers

벡터 스토어(또는 다른 데이터 소스)에 대한 추상화 계층. 자연어 쿼리로 관련 문서 반환:

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
docs = retriever.invoke("What is LangChain?")
```

**추가 리트리버 타입:**
- `MultiQueryRetriever` — 다양한 쿼리 변형 생성으로 recall 향상
- `ContextualCompressionRetriever` — 관련 부분만 압축
- `BM25Retriever` — 전통적 키워드 기반 검색
- `EnsembleRetriever` — 여러 리트리버 결합

### 보안: Indirect Prompt Injection

RAG의 중요한 보안 위협: 악성 지시가 문서에 포함되어 검색 후 프롬프트에 들어오는 공격.

**완화 방법:**
- 검색된 콘텐츠 정제 후 프롬프트 포함
- 검색 컨텍스트와 지시 사이 명시적 구분자 사용
- 이상 출력 모니터링
- 입출력 가드레일 구현

## Interpretation

- LangChain의 RAG는 단순한 "검색 후 붙여넣기"가 아니라 에이전트(동적) vs 체인(결정적) 두 가지 패턴을 명확히 구분한다. 복잡도와 예측 가능성 요구사항에 따라 선택한다.
- FAISS가 사라지고 `InMemoryVectorStore`가 기본값이 됨 — 공식 docs는 이제 FAISS보다 InMemoryVectorStore 권장.
- `RecursiveCharacterTextSplitter`가 범용 텍스트 분할의 공식 권장 방법이다.

## Open Questions

- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? 구버전 `OpenAIEmbeddings()`와의 차이는?
- `@dynamic_prompt` 데코레이터는 무엇인가? LCEL chain을 대체하는 새 패턴인가?
- `response_format="content_and_artifact"` 옵션의 정확한 의미는?

## Related Wiki Pages

- [[LangChain]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]

## Sources

- `langchain-docs-rag-2026-05-23`
