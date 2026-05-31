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

# Runnable

## Summary

`Runnable`은 LangChain에서 모든 실행 가능한 컴포넌트의 공통 인터페이스다. 채팅 모델, 프롬프트 템플릿, 출력 파서, 커스텀 함수를 동일한 방식으로 체인에 연결할 수 있게 해준다. LCEL(LangChain Expression Language)의 기반 추상화다.

## Why It Matters

`|` 연산자로 서로 다른 컴포넌트를 체이닝할 수 있는 이유가 이 인터페이스 때문이다. `invoke`만 구현하면 나머지(batch/stream/async)는 자동으로 제공된다. LangGraph의 `CompiledStateGraph`도 Runnable이므로, LangGraph 그래프를 LCEL 체인에 직접 연결할 수 있다.

## Key Concepts

- `invoke` — 유일한 abstract method. 나머지는 모두 default 구현
- `|` 연산자 → [[RunnableSequence]]
- 병렬 실행 → [[RunnableParallel]]
- 실행 설정 주입 → [[RunnableConfig]]
- `coerce_to_runnable` — dict/callable을 자동으로 Runnable로 변환

## Details

### 최소 계약

```python
class Runnable(Generic[Input, Output], ABC):
    @abstractmethod
    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        ...
```

**유일한 abstract method:** `invoke`  
나머지 메서드는 모두 `invoke` 기반 default 구현이 있어 `invoke`만 구현하면 즉시 사용 가능하다.

### 핵심 메서드

| 메서드 | 기본 동작 | Override 이유 |
|--------|----------|--------------|
| `invoke(input)` | **abstract** — 반드시 구현 | — |
| `ainvoke(input)` | `invoke`를 executor thread에서 실행 | 진짜 async I/O가 있는 경우 |
| `batch(inputs)` | thread pool로 `invoke` 병렬 실행 | 배치 최적화 |
| `stream(input)` | `invoke` 결과 1개를 yield | 토큰 단위 streaming |
| `__or__(other)` | `RunnableSequence(self, other)` 반환 | — |
| `pipe(*others)` | `|` 체이닝과 동일 | — |
| `bind(**kwargs)` | 인자를 고정한 새 Runnable 반환 | — |
| `with_config(config)` | 실행 설정 고정 → [[RunnableConfig]] | — |
| `with_retry(stop_after_attempt=3)` | 예외 시 재시도 | — |
| `with_fallbacks(fallbacks)` | 실패 시 대안 Runnable | — |
| `map()` | `RunnableEach(bound=self)` 반환 | — |

### RunnableLambda — callable을 Runnable로

일반 함수를 LCEL 체인에 끼워 넣는 가장 간단한 방법:

```python
from langchain_core.runnables import RunnableLambda

double = RunnableLambda(lambda x: x * 2)
double.invoke(5)         # → 10
double.batch([1, 2, 3])  # → [2, 4, 6]
```

- `afunc` 없으면 `func`를 thread pool에서 실행 (비동기 호출 시)
- **generator 함수**를 넘기면 streaming 지원 (yield로 chunk 단위 출력)

```python
def word_streamer(text: str):
    for word in text.split():
        yield word + " "

runnable = RunnableLambda(word_streamer)
for chunk in runnable.stream("hello world"):
    print(chunk, end="")
```

### RunnablePassthrough / RunnableAssign / RunnablePick

| 클래스 | 동작 | 전형적인 용도 |
|--------|------|-------------|
| `RunnablePassthrough()` | 입력을 그대로 반환 (identity) | RAG 체인에서 question을 downstream으로 전달 |
| `RunnablePassthrough.assign(key=fn)` | 입력 dict에 새 키 추가 → `RunnableAssign` 반환 | context enrichment |
| `RunnablePick("key")` | dict에서 단일 키 값 반환 | 필요한 필드만 추출 |
| `RunnablePick(["k1", "k2"])` | dict에서 복수 키 dict 반환 | 다중 필드 선택 |

```python
from langchain_core.runnables import RunnablePassthrough

# RAG 패턴: retriever 결과와 원본 question을 함께 downstream으로 전달
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
)
```

### coerce_to_runnable — 자동 변환

`|` 연산자 내부에서 동작하는 변환 함수:

| 입력 타입 | 변환 결과 |
|----------|----------|
| `Runnable` 인스턴스 | 그대로 |
| `callable` | `RunnableLambda(thing)` |
| `dict` | `RunnableParallel(thing)` |

체인 내 dict literal이 자동으로 [[RunnableParallel]]로 변환되는 이유다:
```python
# 아래 두 표현은 동일하다
chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
chain = RunnableParallel({"context": retriever, "question": RunnablePassthrough()}) | prompt | llm
```

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files:
  - `libs/core/langchain_core/runnables/base.py` (partial — docstring + 핵심 시그니처)
  - `libs/core/langchain_core/runnables/passthrough.py`

## Tests

- TBD — Needs Source

## Related Pages

- [[LangChain]]
- [[RunnableSequence]]
- [[RunnableParallel]]
- [[RunnableConfig]]
- [[LangChain create_agent flow]]
- [[StateGraph]] — `CompiledStateGraph`도 Runnable 구현체

## Open Questions

- `RunnableSequence.invoke` 내부: step 간 에러 처리는? — Needs Verification
- `astream_events`와 `astream_log`의 차이는? — Needs Source
- `with_retry`의 retry 조건 커스터마이징 (retry_if_exception_type 등)은? — Needs Source
- `RunnableWithFallbacks` 내부 구현은? — Needs Source

## Sources

- `langchain-source-runnable-2026-05-23`
