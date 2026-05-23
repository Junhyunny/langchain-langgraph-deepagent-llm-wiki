---
type: source_summary
source_id: langchain-source-runnable-2026-05-23
framework: LangChain
retrieved_at: "2026-05-23"
status: complete
confidence: medium
---

# Source Summary: LangChain — Runnable Interface Source Code (LCEL)

## Source Info
- **Source ID:** `langchain-source-runnable-2026-05-23`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/langchain/tree/master/libs/core/langchain_core/runnables
- **Retrieved At:** 2026-05-23
- **Version / Commit:** main branch (SHA 미확인)
- **Files:** `langchain_core/runnables/base.py` (docstring+시그니처만), `langchain_core/runnables/passthrough.py`
- **⚠️ 주의:** `base.py`는 파일이 매우 커서 전체 구현이 아닌 클래스 docstring + 핵심 메서드 시그니처만 수집됨. 구현 세부는 Needs Verification.

---

## Key Facts

### Runnable — 최소 계약 (추상 기반 클래스)

- `Runnable(Generic[Input, Output], ABC)` — 제네릭 추상 클래스
- **유일한 abstract method: `invoke`** — 나머지는 모두 default 구현 있음
- `invoke(input, config=None, **kwargs) → Output` — **추상 메서드** (반드시 구현)
- `ainvoke(...)` — 기본: `invoke`를 executor thread에서 실행. 진짜 async는 override 필요
- `batch(inputs: list, ...) → list[Output]` — 기본: thread pool로 `invoke` 병렬 실행
- `stream(...) → Iterator[Output]` — 기본: `invoke` 결과 1개를 yield. 진짜 streaming은 override 필요
- `__or__(other) → RunnableSequence` — `|` 연산자 → `RunnableSequence(self, coerce_to_runnable(other))`
- `__ror__(other) → RunnableSequence` — 역방향 `|` 연산자
- `pipe(*others, name=None) → RunnableSequence` — `|` 체이닝과 동일
- `map() → RunnableEach` — `RunnableEach(bound=self)` 반환
- `bind(**kwargs)` — 인자를 고정한 새 Runnable 반환
- `with_config(config)` — 실행 설정 고정
- `with_retry(stop_after_attempt=3, ...)` — 예외 시 재시도 Runnable
- `with_fallbacks(fallbacks)` — 실패 시 대안 Runnable

### RunnableSequence — `|` 연산자 결과 타입

- `|` 연산자가 생성하는 타입: **`RunnableSequence`**
- 내부 구조: `first: Runnable`, `middle: list[Runnable] = []`, `last: Runnable`
- 순차 실행: 각 step의 output이 다음 step의 input
- sync/async/stream/batch 모두 지원

### RunnableLambda — callable → Runnable

- `func: Callable[[Input], Output]` — sync callable
- `afunc: Callable[[Input], Awaitable[Output]] | None = None` — async callable (없으면 func을 thread pool에서 실행)
- generator 함수 → streaming 지원 (yield로 chunk 단위 출력)
- 일반 함수와의 차이: `invoke/batch/stream/ainvoke` 인터페이스 자동 부여 + LCEL 체인 연결 가능

### RunnableParallel — 병렬 실행

- 출력 타입: `dict[str, Any]` — **output keys = input mapping의 keys**
- 입력 mapping의 모든 runnable에 **동일한 input**을 전달
- 실행: thread pool (sync), asyncio (async)로 **동시 실행**
- dict shorthand: chain 내에서 `{"key1": step1, "key2": step2}` → 자동으로 `RunnableParallel`로 변환 (`coerce_to_runnable`)

### RunnableEach — 리스트 입력

- `bound: Runnable[Input, Output]`
- `invoke(inputs: list[Input]) → list[Output]` — 내부적으로 `self.bound.batch(inputs, config)` 호출
- `.map()`으로 생성

### RunnablePassthrough — 입력 통과

- 입력을 그대로 반환 (identity function)
- `invoke(input) → input`
- `.assign(**kwargs) → RunnableAssign` — class method; 입력 dict에 새 키를 추가

### RunnableAssign — dict에 키 추가

- `mapper: RunnableParallel`
- `invoke(input) → {**input, **mapper.invoke(input)}` — 원본 dict에 mapper 결과를 merge

### RunnablePick — dict에서 키 선택

- `keys: str | list[str]`
- 단일 key → 값 직접 반환 (dict 아님)
- 복수 key → 해당 키들의 dict 반환

### coerce_to_runnable — 자동 변환

| 입력 타입 | 변환 결과 |
|----------|----------|
| `Runnable` 인스턴스 | 그대로 |
| `callable` | `RunnableLambda(thing)` |
| `dict` | `RunnableParallel(thing)` |

---

## Important Terms

- [[LangChain]] — LCEL이 속한 프레임워크
- [[Tool Calling]] — RunnableLambda로 tool을 wrapping하는 패턴
- [[LangGraph]] — LangGraph 내부도 Runnable 인터페이스를 사용 (`CompiledStateGraph`가 Runnable)

---

## Interpretation

- `Runnable`의 최소 계약은 `invoke` 하나 — 나머지(batch/stream/async)는 default가 있어 바로 사용 가능하나, 성능 최적화를 위해 override 권장
- `|` 연산자가 `RunnableSequence`를 생성한다는 것은 소스코드로 확인됨 — deprecated 아님
- `RunnableParallel`도 소스코드에 존재 — deprecated 아님 (wiki의 Possible Conflict 해소)
- `RunnableLambda`는 일반 함수를 Runnable로 쓰는 가장 간단한 방법; async def를 넘기면 afunc으로 처리됨
- chain 내 dict literal이 자동으로 `RunnableParallel`로 변환된다는 것은 `coerce_to_runnable`로 확인됨

---

## Implications for My AI Agent Project

- 커스텀 processing step을 체인에 끼워넣으려면 `RunnableLambda`가 가장 간단
- 여러 정보를 병렬로 조회해 dict로 합칠 때: `{"context": retriever, "question": RunnablePassthrough()}` 패턴
- streaming이 필요한 step은 `stream` 메서드를 override하거나 generator 기반 `RunnableLambda` 사용
- `with_retry`, `with_fallbacks`로 견고한 체인 구성 가능

---

## Open Questions

- `RunnableParallel`의 실제 동시 실행 구현: thread pool의 thread 수 제한은? `max_concurrency` 옵션이 있는가? — Needs Verification (base.py 전체 확인 필요)
- `RunnableSequence.invoke`의 내부 구현: 각 step 간 에러 처리는 어떻게 되는가?
- `RunnableLambda`에서 generator가 아닌 일반 함수를 `stream`에 넘기면 어떻게 되는가?
- `astream_events`와 `astream_log`의 차이는? (raw에서 시그니처만 확인, 구현 미확인)
- `RunnableWithFallbacks` 내부 구현은? (raw에서 타입만 확인)
- LCEL 체인에서 `RunnableConfig`를 통해 실행 시간 설정을 주입하는 방법은? (`configurable` 필드)

---

## Used By

- [[LangChain]]

---

## Source Code References
- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files: `libs/core/langchain_core/runnables/base.py` (partial), `libs/core/langchain_core/runnables/passthrough.py`
