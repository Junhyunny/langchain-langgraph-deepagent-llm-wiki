# Source Summary: LangChain VectorStore / Embeddings / Document

**Source ID:** `langchain-source-vectorstore-embeddings-2026-05-23`
**Type:** source_code
**Framework:** LangChain
**URLs:**
- `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/base.py`
- `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/vectorstores/in_memory.py`
- `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/embeddings/embeddings.py`
- `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/documents/base.py`
**Retrieved:** 2026-05-23

**참고:** FAISS vectorstore는 `langchain_community` 패키지에 있으며 GitHub raw URL 접근 실패. FAISS 관련 항목은 ⚠️ 가설로 표시.

---

## Document 클래스

```python
class Document(BaseMedia):
    page_content: str       # 문서 텍스트 내용
    type: Literal["Document"] = "Document"
    # BaseMedia에서 상속:
    id: str | None          # 선택적 식별자
    metadata: dict          # 임의 메타데이터
```

- `Document`는 retrieval workflow용. 대화용 텍스트 전달에는 Message 타입 사용.
- `str(doc)` → `"page_content='...' metadata={...}"` 형식.

---

## Embeddings 추상 클래스

```python
class Embeddings(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """문서 목록 → 벡터 목록"""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """쿼리 텍스트 → 단일 벡터"""

    # 기본 구현 (async):
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def aembed_query(self, text: str) -> list[float]: ...
```

**핵심 계약:**
- `embed_documents` vs `embed_query`: 대부분의 모델에서 동일한 구현을 사용하지만, 일부 asymmetric 모델(ex: E5)은 쿼리와 문서 임베딩이 다를 수 있어 추상화로 분리됨.
- async 버전은 기본적으로 sync wrapper (`run_in_executor`). 고성능 구현체는 native async 제공.

---

## VectorStore 추상 클래스

### 핵심 추상 메서드

```python
class VectorStore(ABC):
    @abstractmethod
    def similarity_search(self, query: str, k: int = 4, **kwargs) -> list[Document]: ...

    def similarity_search_with_score(self, *args, **kwargs) -> list[tuple[Document, float]]:
        """문서 + 거리/유사도 점수 반환."""

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        *,
        ids: list[str] | None = None,
        **kwargs,
    ) -> list[str]:
        """텍스트를 임베딩해 벡터 스토어에 추가. 반환: document ID 목록."""
```

### as_retriever — search_type 옵션

```python
def as_retriever(self, **kwargs) -> VectorStoreRetriever:
    """VectorStore → BaseRetriever 변환."""
    # search_type 옵션:
    # 1. "similarity" (기본값): k개의 가장 유사한 문서 반환
    # 2. "mmr": 관련성 + 다양성 균형 (Maximal Marginal Relevance)
    # 3. "similarity_score_threshold": score_threshold 이상인 문서만 반환
```

| search_type | 핵심 파라미터 | 내부 호출 |
|-------------|-------------|----------|
| `"similarity"` | `k=4` | `vectorstore.similarity_search(query, **kwargs)` |
| `"mmr"` | `k=4`, `fetch_k=20`, `lambda_mult=0.5` | `vectorstore.max_marginal_relevance_search(query, **kwargs)` |
| `"similarity_score_threshold"` | `score_threshold` | `vectorstore.similarity_search_with_relevance_scores(query, **kwargs)` |

**사용 예시:**
```python
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.5}
)
docs = retriever.invoke("query")
```

---

## InMemoryVectorStore (내장 구현체)

**거리 메트릭: cosine similarity** (높을수록 유사)

```python
class InMemoryVectorStore(VectorStore):
    """In-memory vector store. Uses cosine similarity for search using numpy."""

    def similarity_search_with_score_by_vector(self, embedding, k):
        similarity = cosine_similarity([embedding], [doc["vector"] for doc in docs])[0]
        # 높을수록 유사 (0~1)
```

**MMR 구현 (InMemoryVectorStore 기준):**
```python
def max_marginal_relevance_search(self, query, k=4, fetch_k=20, lambda_mult=0.5):
    # 1. fetch_k개 후보 추출 (similarity search)
    # 2. maximal_marginal_relevance(embedding, candidate_vectors, k, lambda_mult)
    # lambda_mult 범위: 0.0 ~ 1.0
    # - 1.0: 순수 관련성 우선 (diversity 없음)
    # - 0.0: 순수 다양성 우선 (relevance 없음)
    # - 0.5: 균형 (기본값)
```

---

## FAISS VectorStore ⚠️ 가설

**소스 미확인**: `langchain_community` 패키지의 FAISS 파일 접근 실패. 이하는 문서 기반 추론 + 기존 지식.

⚠️ **거리 메트릭: L2 (Euclidean) 기본값** (`IndexFlatL2`)
- `distance_strategy` 파라미터로 변경 가능: `DistanceStrategy.EUCLIDEAN_DISTANCE` (기본), `COSINE`, `MAX_INNER_PRODUCT`
- `similarity_search_with_score` 반환: `(Document, float)`. float은 **L2 거리** → **낮을수록 더 유사**.
- `similarity_search_with_relevance_scores` 반환: **높을수록 더 유사** (정규화된 점수).

⚠️ L2 거리와 cosine similarity 관계:
- 벡터가 정규화되어 있는 경우: `L2_distance² = 2 - 2*cosine_similarity`
- 완전 동일: L2=0, cosine=1
- 완전 반대: L2=2, cosine=-1

**Needs Source**: FAISS `distance_strategy` 파라미터 정확한 타입과 기본값 확인 필요.

---

## BaseRetriever 계약

```python
class BaseRetriever(ABC):
    # 반드시 구현:
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs,
    ) -> list[Document]: ...

    # 공개 API (위를 호출):
    def invoke(self, input: str, config: RunnableConfig | None = None) -> list[Document]: ...
```

`get_relevant_documents()`는 deprecated. 현재 공개 API는 `invoke()`.

---

## 해소된 Open Questions

- ✅ `LangChain의 Document 객체 구조` → `page_content: str`, `metadata: dict`, `id: str | None`, `type: Literal["Document"]`. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `LangChain Embeddings 기반 클래스 인터페이스` → `Embeddings(ABC)`: `embed_documents`, `embed_query` abstract. async 버전은 기본 sync wrapper. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `as_retriever()` 3가지 search_type → `similarity`(k), `mmr`(k/fetch_k/lambda_mult), `similarity_score_threshold`(score_threshold). (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `MMR 작동 방식` → fetch_k 후보 → `maximal_marginal_relevance(embedding, candidates, k, lambda_mult)`. lambda_mult 1.0=관련성 우선, 0.0=다양성 우선, 0.5=기본. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `BaseRetriever.get_relevant_documents` 계약 → deprecated. 현재 `invoke()` 사용. 내부 구현은 `_get_relevant_documents()` override. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)

---

## 잔여 Open Questions

- ⚠️ FAISS `distance_strategy` 파라미터 정확한 기본값 — Needs Source (파일 접근 실패)
- ⚠️ FAISS `similarity_search_with_score` 반환 float의 정확한 의미 (L2 거리 확인) — Needs Source
- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? — Needs Source
- `_merge_splits()`의 `chunk_overlap` 구현 방식은? — Source: `langchain-source-text-splitters-2026-05-23`
