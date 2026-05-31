---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-31
sources:
  - langchain-source-runnable-2026-05-23
  - langchain-source-runnableconfig-2026-05-31
---

# RunnableConfig

## Summary

`RunnableConfig`는 [[Runnable]]의 모든 실행 메서드(`invoke`, `batch`, `stream`, `ainvoke`)에 전달할 수 있는 실행 시간 설정 TypedDict다. 콜백, 태그, 재귀 제한, 병렬 제한, 런타임 설정 주입 등을 실행 시점에 지정한다.

## Why It Matters

동일한 체인을 환경(dev/prod), 사용자, 세션에 따라 다르게 실행할 때 `RunnableConfig`를 사용한다. `configurable` 필드를 통해 모델, 파라미터, 프롬프트를 런타임에 교체하는 패턴이 가능하다. LangGraph의 `recursion_limit`도 이 객체를 통해 전달된다.

## Key Concepts

- `TypedDict(total=False)` — 모든 필드 선택적
- `configurable` — 런타임 설정 교체 진입점
- `recursion_limit` — 기본값 25 (LangGraph에서도 이 값 사용)
- `max_concurrency` — batch/parallel 동시 실행 제한
- Helper 함수: `merge_configs`, `ensure_config`, `patch_config`

## Details

### 전체 필드 (검증됨: config.py 소스)

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `tags` | `list[str]` | — | 이 호출 및 하위 호출 필터링 태그 |
| `metadata` | `dict[str, Any]` | — | JSON 직렬화 가능한 메타데이터 |
| `callbacks` | `Callbacks` | — | 콜백 핸들러 (LangSmith 등) |
| `run_name` | `str` | 클래스 이름 | 추적기 실행 이름 |
| `run_id` | `uuid.UUID \| None` | — | 추적기 실행 고유 ID |
| `max_concurrency` | `int \| None` | None | 최대 병렬 호출 수 (None = ThreadPoolExecutor 기본값) |
| `recursion_limit` | `int` | 25 | 최대 재귀 횟수 (`DEFAULT_RECURSION_LIMIT = 25`) |
| `configurable` | `dict[str, Any]` | — | 런타임 설정 가능한 속성 값 |

`total=False`이므로 모든 필드가 선택적이다.

### 기본 사용법

```python
from langchain_core.runnables import RunnableConfig

result = chain.invoke(
    input_data,
    config=RunnableConfig(
        tags=["production"],
        metadata={"user_id": "u-123"},
        recursion_limit=10,
        max_concurrency=4,
    )
)
```

### with_config() — 설정을 고정한 Runnable 반환

```python
# 실행마다 config를 넘기는 대신, 미리 고정
prod_chain = chain.with_config(
    RunnableConfig(tags=["prod"], metadata={"env": "production"})
)
result = prod_chain.invoke(input_data)  # config 없이 호출
```

### configurable 필드 — 런타임 설정 교체

`configurable_fields()` 또는 `configurable_alternatives()`로 교체 가능하도록 선언한 속성을 런타임에 바꿀 수 있다:

```python
from langchain_core.runnables import ConfigurableField

llm = ChatOpenAI(model="gpt-4o").configurable_alternatives(
    ConfigurableField(id="llm"),
    default_key="gpt4o",
    claude=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
)
chain = prompt | llm | parser

# 런타임에 모델 교체
result = chain.invoke(
    input_data,
    config={"configurable": {"llm": "claude"}}
)
```

> ⚠️ `configurable_fields()`와 `configurable_alternatives()`는 `config.py`가 아닌 `Runnable` 클래스(base.py)에 정의됨. — Needs Verification (base.py 전체 미수집)

### Helper 함수 (내부 구현)

| 함수 | 역할 |
|------|------|
| `ensure_config(config)` | 기본값으로 완전한 config 생성. 컨텍스트 변수의 설정 상속 |
| `merge_configs(*configs)` | 여러 config 병합. `metadata`, `tags`, `configurable`은 merge, `callbacks`는 타입에 따라 다르게 처리 |
| `patch_config(config, **kwargs)` | 특정 필드만 업데이트. `callbacks` 변경 시 `run_name`, `run_id` 제거 |
| `get_config_list(config, length)` | 단일 config 또는 config 리스트를 입력 길이 맞춤 리스트로 변환 |

이 함수들은 내부적으로 Runnable 실행 시 자동으로 호출된다. 직접 사용할 일은 드물다.

### LangGraph에서의 recursion_limit

`recursion_limit`은 LangGraph의 Pregel 런타임이 그대로 읽어 사용한다:

```python
graph.invoke(
    input_data,
    config={"recursion_limit": 50}  # 기본값 25를 50으로 늘림
)
```

→ [[Checkpointing]], [[StateGraph]] 참조

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (master branch)
- Files:
  - `libs/core/langchain_core/runnables/config.py` — `RunnableConfig` TypedDict, helper 함수 전체

## Tests

- TBD — Needs Source

## Related Pages

- [[Runnable]]
- [[RunnableSequence]]
- [[RunnableParallel]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Tracing]]

## Open Questions

- `configurable_fields()`와 `configurable_alternatives()`는 base.py 어디에 정의되는가? — Needs Verification
- `merge_configs`에서 `callbacks` 타입에 따른 처리 분기의 구체적 내용은? — Needs Source
- `ensure_config`가 상속하는 "컨텍스트 변수의 설정"이란 무엇인가? (async context var?) — Needs Source

## Sources

- `langchain-source-runnableconfig-2026-05-31`
- `langchain-source-runnable-2026-05-23`
