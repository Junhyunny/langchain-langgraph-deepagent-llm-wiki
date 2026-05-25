---
type: pr_candidate
framework:
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-venv-fields-py-2026-05-25
---

# PR Candidate — LangGraph Pydantic BaseModel default_factory + reducer 버그 (#5225)

**관련 이슈**: https://github.com/langchain-ai/langgraph/issues/5225  
**레이블**: `bug`, `help wanted`, `external`  
**난이도**: 낮음 (isolated fix, 변경 범위 좁음)

---

## Problem

Pydantic `BaseModel` 상태 스키마에서 `Field(default_factory=...)` + `Annotated[..., reducer]` 조합을 사용할 때, `graph.invoke({})` 호출 시 `default_factory`가 무시되어 빈 값(`[]`)으로 초기화된다.

```python
class OverallState(BaseModel):
    variable: Annotated[list[str], extend_list] = Field(
        default_factory=lambda: ['default']
    )

app.invoke({})
# 기대: {'variable': ['default', 'added']}
# 실제: {'variable': ['added']}  ← 버그
```

---

## Root Cause

`BinaryOperatorAggregate.__init__` (`langgraph/channels/binop.py`, line 63-78) 이 채널 초기값을 `typ()` (= `[]`)로 설정하며, 스키마의 Pydantic `Field(default_factory=...)` 정보를 참조하지 않는다.

호출 경로:
```
_get_channels(OverallState)
  → _get_channel("variable", Annotated[list[str], extend_list])
      → _is_field_binop() → BinaryOperatorAggregate(list[str], extend_list)
          → self.value = list()  ← 항상 빈 리스트 (버그)
```

비교: `dataclass`의 경우 `get_field_default()`에서 `field.default_factory` 처리가 있으나, `Pydantic BaseModel`의 `model_fields[name].default_factory`는 처리되지 않음.

---

## Fix

`langgraph/_internal/_fields.py::get_field_default()`에 Pydantic 분기를 추가하고, 이를 채널 초기값 설정 경로에 연결한다.

### `_fields.py` 변경 (Pydantic support 추가)

```python
# 기존
if dataclasses.is_dataclass(schema):
    ...
# 추가
from pydantic.fields import PydanticUndefined

if isinstance(schema, type) and issubclass(schema, BaseModel):
    if name in schema.model_fields:
        field_info = schema.model_fields[name]
        if field_info.default is not PydanticUndefined:
            return field_info.default
        elif field_info.default_factory is not None:
            return field_info.default_factory()
```

### `binop.py` 또는 `state.py` 연결 확인 필요

`get_field_default`가 채널 초기값에 연결되는 경로를 확인하고, 연결이 없으면 `_get_channels`에서 Pydantic default를 추출해 `BinaryOperatorAggregate`에 `default=` 파라미터로 전달.

---

## Tests

### 현재 없는 것

- Pydantic BaseModel + `Annotated[..., reducer]` + `Field(default_factory=...)` 조합 테스트

### 추가할 회귀 테스트 (예시)

```python
def test_pydantic_default_factory_with_reducer():
    """invoke({}) should respect Pydantic Field(default_factory=...)."""
    from pydantic import BaseModel, Field
    
    def extend_list(a, b):
        return a + b
    
    class State(BaseModel):
        items: Annotated[list[str], extend_list] = Field(
            default_factory=lambda: ['default']
        )
    
    def node(s: State):
        return {'items': ['added']}
    
    builder = StateGraph(State)
    builder.add_node('node', node)
    builder.add_edge(START, 'node')
    builder.add_edge('node', END)
    app = builder.compile()
    
    result = app.invoke({})
    assert result['items'] == ['default', 'added'], (
        f"Expected ['default', 'added'], got {result['items']!r}"
    )
```

---

## Risk

- **낮음**: `_fields.py`의 `get_field_default()`는 독립적인 헬퍼 함수
- **확인 필요**: Pydantic v1 vs v2 API 차이 (`model_fields` vs `__fields__`)
  - Pydantic v2: `schema.model_fields[name]` (현재 버전 기준)
  - Pydantic v1: `schema.__fields__[name]` — 지원 여부 확인 필요
- **사이드 이펙트 위험 낮음**: TypedDict / dataclass 경로는 변경 없음

---

## Status

- [x] 이슈 확인 및 레이블 검토 (2026-05-25)
- [x] 재현 코드 작성 및 확인 (2026-05-25)
- [x] 근본 원인 소스 분석 (2026-05-25)
- [ ] 수정 코드 작성
- [ ] 회귀 테스트 작성
- [ ] 로컬에서 테스트 실행 확인
- [ ] PR 제출

---

## Related Issue

- https://github.com/langchain-ai/langgraph/issues/5225

## Related Pages

- [[LangGraph issue 5225 pydantic default factory]]
- [[LangGraph]]
- [[LangGraph Code Map]]

## Sources

- Source Code References:
  - `langgraph/channels/binop.py` line 63-78
  - `langgraph/_internal/_fields.py` line 79-122
  - `langgraph/graph/state.py` line 1801-1859
- 직접 실행 확인: `graph.invoke({})` → 버그 확인됨 (2026-05-25)
