---
type: concept
framework:
  - LangChain
status: verified
confidence: medium
last_reviewed: 2026-05-31
sources:
  - langchain-source-runnable-2026-05-23
---

# RunnableParallel

## Summary

`RunnableParallel`은 여러 [[Runnable]]에 동일한 입력을 동시에 전달하고 결과를 dict로 모으는 [[Runnable]] 구현체다. LCEL 체인에서 dict literal을 쓰면 `coerce_to_runnable`이 자동으로 `RunnableParallel`로 변환한다.

## Why It Matters

LLM 호출 전에 여러 소스에서 정보를 병렬로 조회해야 할 때 사용한다. RAG 패턴에서 retriever 결과와 원본 question을 동시에 downstream으로 전달하는 핵심 패턴이다.

## Key Concepts

- 동일한 input → 모든 runnable에 동시 전달
- 출력: `dict[str, Any]` — key = mapping의 key
- sync: thread pool, async: asyncio 동시 실행
- dict literal 자동 변환 → `coerce_to_runnable`

## Details

### 기본 사용법

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

parallel = RunnableParallel({
    "context": retriever,
    "question": RunnablePassthrough(),
})

result = parallel.invoke("What is LangChain?")
# result = {
#   "context": [Document(...)],
#   "question": "What is LangChain?"
# }
```

### dict literal 단축 문법

LCEL 체인 안에서 `|`로 연결할 때 dict literal은 자동으로 `RunnableParallel`로 변환된다:

```python
# 아래 두 표현은 동일
chain = RunnableParallel({"context": retriever, "question": RunnablePassthrough()}) | prompt | llm
chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
```

`coerce_to_runnable(dict)` → `RunnableParallel(dict)` 변환이 `__or__` 내부에서 발생한다.

### 동시 실행 메커니즘

**검증됨 (source summary 기준):**
- sync `invoke`: thread pool로 동시 실행
- async `ainvoke`: asyncio로 동시 실행

**Needs Verification:**
- thread pool의 thread 수 제한 (max_concurrency 옵션 여부)
- 개별 step 실패 시 동작 (다른 step 취소 여부)

### 전형적인 패턴

**RAG 패턴 — retriever + passthrough**:
```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)
```

**다중 LLM 호출 병렬화**:
```python
from langchain_core.runnables import RunnableParallel

multi_chain = RunnableParallel({
    "summary": summarize_chain,
    "keywords": keyword_chain,
    "sentiment": sentiment_chain,
})
result = multi_chain.invoke(document)
# result = {"summary": "...", "keywords": [...], "sentiment": "positive"}
```

**RunnablePassthrough.assign으로 dict 확장**:
```python
# 입력 dict를 그대로 유지하면서 새 키 추가
chain = RunnablePassthrough.assign(
    context=lambda x: retriever.invoke(x["question"])
)
result = chain.invoke({"question": "What is LangGraph?"})
# result = {"question": "What is LangGraph?", "context": [...]}
```

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files:
  - `libs/core/langchain_core/runnables/base.py` — `RunnableParallel` 클래스
  - `libs/core/langchain_core/runnables/passthrough.py` — `RunnablePassthrough`, `RunnableAssign`

## Tests

- TBD — Needs Source

## Related Pages

- [[Runnable]]
- [[RunnableSequence]]
- [[RunnableConfig]]
- [[LangChain]]
- [[RAG]]

## Open Questions

- thread pool의 thread 수 제한은? `max_concurrency` 옵션이 있는가? — Needs Verification (`base.py` 전체 확인 필요)
- 개별 step 실패 시 다른 step이 취소되는가? — Needs Verification
- `RunnableParallel`을 async로 실행할 때 asyncio gather의 동작은? — Needs Source

## Sources

- `langchain-source-runnable-2026-05-23`
