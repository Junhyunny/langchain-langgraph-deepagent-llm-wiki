---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-31
sources:
  - langchain-source-runnable-2026-05-23
---

# RunnableSequence

## Summary

`RunnableSequence`는 `|` 연산자의 결과 타입이다. 여러 [[Runnable]]을 순서대로 연결해 각 step의 output이 다음 step의 input으로 전달된다. LCEL 체인의 실체다.

## Why It Matters

LangChain의 `prompt | llm | parser` 패턴이 가능한 이유가 `RunnableSequence`다. 내부적으로 `first`, `middle`, `last` 세 구간으로 저장되며 sync/async/stream/batch 모두 지원한다.

## Key Concepts

- `|` 연산자 → [[Runnable]] 참조
- 내부 구조: `first / middle / last` 분리
- `coerce_to_runnable` — dict/callable 자동 변환 후 연결

## Details

### `|` 연산자가 RunnableSequence를 만드는 방식

소스코드로 확인:
```python
# Runnable.base.py
def __or__(self, other):
    return RunnableSequence(self, coerce_to_runnable(other))
```

`|`로 연결할 때 오른쪽 값이 자동으로 Runnable로 변환된다:
- `callable` → `RunnableLambda`
- `dict` → `RunnableParallel`

### 내부 구조

```python
class RunnableSequence(Runnable[Input, Output]):
    first: Runnable
    middle: list[Runnable] = []
    last: Runnable
```

`a | b | c | d`는 `RunnableSequence(first=a, middle=[b, c], last=d)`로 저장된다.

### 실행 흐름

```
input → first.invoke(input) → middle[0].invoke(output0) → ... → last.invoke(outputN-1) → final_output
```

각 step의 출력이 다음 step의 입력이 된다. 타입 호환성은 런타임에만 검사된다.

### 전형적인 패턴

```python
from langchain_core.runnables import RunnablePassthrough

# 기본 패턴: prompt | llm | parser
chain = prompt | llm | output_parser

# RAG 패턴: dict → RunnableParallel → 병렬 실행 후 merge
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)

# 커스텀 함수 삽입
from langchain_core.runnables import RunnableLambda

chain = prompt | llm | RunnableLambda(lambda msg: msg.content.upper())
```

### 복잡한 체인 조립

`pipe()` 메서드는 `|` 연산자와 동일하다:

```python
# 동일한 결과
chain1 = prompt | llm | parser
chain2 = prompt.pipe(llm, parser)
```

여러 체인을 조합할 수 있다:

```python
retrieval_chain = retriever | format_docs     # → RunnableSequence
full_chain = {"context": retrieval_chain, "question": RunnablePassthrough()} | prompt | llm
```

### Streaming 지원

`RunnableSequence.stream()`은 **마지막 step의 streaming 출력만 전달**한다:

```python
for chunk in chain.stream("What is LangChain?"):
    print(chunk.content, end="", flush=True)
```

중간 step의 streaming은 `astream_events`로 확인 가능하다. → [[Event Streaming]]

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files:
  - `libs/core/langchain_core/runnables/base.py` — `Runnable.__or__`, `RunnableSequence` 클래스

## Tests

- TBD — Needs Source

## Related Pages

- [[Runnable]]
- [[RunnableParallel]]
- [[RunnableConfig]]
- [[LangChain]]
- [[Event Streaming]]

## Open Questions

- `RunnableSequence.invoke` 내부: step 간 에러 처리 방식은? (`with_retry`와의 관계) — Needs Source
- 중간 step의 출력을 streaming으로 받으려면 어떻게 해야 하는가? — Needs Source
- `RunnableSequence`가 중첩될 때 (sequence 안에 sequence) flatten되는가? — Needs Verification

## Sources

- `langchain-source-runnable-2026-05-23`
