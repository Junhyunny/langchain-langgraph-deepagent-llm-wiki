---
type: concept
framework:
  - LangChain
status: needs_source
confidence: low
last_reviewed: 2026-05-31
sources:
  - langchain-source-runnable-2026-05-23
---

# RunnableConfig

## Summary

`RunnableConfig`는 [[Runnable]]의 모든 메서드(`invoke`, `batch`, `stream`, `ainvoke`)에 전달할 수 있는 실행 시간 설정 객체다. 콜백, 메타데이터, 태그, 재귀 제한 등을 실행 시점에 주입하는 수단이다.

> ⚠️ **소스 미수집:** 현재 이 페이지는 시그니처 수준 정보만 있다. `RunnableConfig` 전체 필드 및 `configurable` 패턴의 동작은 소스 코드 추가 확인이 필요하다.

## Why It Matters

동일한 체인을 환경(dev/prod), 사용자, 세션에 따라 다르게 실행할 때 `RunnableConfig`를 활용한다. `configurable` 필드를 통해 런타임에 모델, 파라미터, 프롬프트를 교체하는 패턴이 가능하다.

## Key Concepts

- 모든 Runnable 메서드의 `config` 파라미터
- `configurable` 필드 — 런타임 설정 주입 패턴
- `with_config()` — 설정을 미리 고정한 Runnable 반환
- 콜백, 태그, 메타데이터 주입

## Details

### 기본 사용법 (검증됨: 시그니처 수준)

`RunnableConfig`는 `Runnable.invoke`의 두 번째 인자:

```python
from langchain_core.runnables import RunnableConfig

result = chain.invoke(
    input,
    config=RunnableConfig(
        callbacks=[...],
        tags=["production"],
        metadata={"user_id": "123"},
        recursion_limit=25,
    )
)
```

### with_config() — 설정 고정

```python
# 설정을 미리 고정한 새 Runnable 반환
configured_chain = chain.with_config(
    RunnableConfig(tags=["production"], metadata={"env": "prod"})
)
result = configured_chain.invoke(input)  # config 없이 호출
```

### configurable 패턴 ⚠️ Needs Source

`configurable_fields()` 또는 `configurable_alternatives()`를 통해 체인의 특정 컴포넌트를 런타임에 교체할 수 있다고 알려져 있으나, 내부 동작 미확인.

```python
# ⚠️ 가설 — Needs Source
llm = ChatOpenAI(model="gpt-4o").configurable_alternatives(
    ConfigurableField(id="llm"),
    default_key="gpt-4o",
    claude=ChatAnthropic(model="claude-3-5-sonnet"),
)
chain = prompt | llm | parser

# 런타임에 모델 교체
result = chain.invoke(input, config={"configurable": {"llm": "claude"}})
```

### RunnableConfig 주요 필드 ⚠️ Needs Verification

| 필드 | 타입 | 용도 |
|------|------|------|
| `callbacks` | `list` | LangSmith 등 콜백 핸들러 |
| `tags` | `list[str]` | 실행 식별 태그 |
| `metadata` | `dict` | 실행 관련 메타데이터 |
| `recursion_limit` | `int` | LangGraph 재귀 제한 |
| `max_concurrency` | `int` | 병렬 실행 제한 (Needs Verification) |
| `configurable` | `dict` | 런타임 설정 (configurable 패턴) |
| `run_name` | `str` | 실행 이름 (LangSmith 추적) |

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files:
  - `libs/core/langchain_core/runnables/config.py` — **미수집**
  - `libs/core/langchain_core/runnables/base.py` — `with_config` 메서드 시그니처만 확인

## Tests

- TBD — Needs Source

## Related Pages

- [[Runnable]]
- [[RunnableSequence]]
- [[RunnableParallel]]
- [[LangChain]]
- [[Tracing]]

## Open Questions

- `RunnableConfig.configurable` 필드를 통해 런타임 설정을 주입하는 전체 메커니즘은? — **Needs Source** (`config.py` 수집 필요)
- `configurable_fields()` vs `configurable_alternatives()`의 차이는? — Needs Source
- `max_concurrency`가 `RunnableConfig`에 있는가, `RunnableParallel`에 있는가? — Needs Verification
- `recursion_limit`는 LangGraph에서만 의미가 있는가? — Needs Source

## Sources

- `langchain-source-runnable-2026-05-23` (시그니처 수준만 — `config.py` 미수집)
