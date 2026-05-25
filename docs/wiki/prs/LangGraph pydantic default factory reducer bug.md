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

`START` 노드 writer(`attach_node`)의 `_get_updates` 함수가 `dict` 입력을 Pydantic 스키마로 coerce하지 않아, `Field(default_factory=...)` 기본값이 무시된다.

호출 경로:
```
invoke({})
  → __start__ channel = {}
  → attach_node START → _get_updates({})
      → isinstance({}, dict) → [(k, v) for k, v in {}.items()] = []
          → 아무 channel도 업데이트 안 됨 → 채널 초기값 [] 유지 (버그)
```

올바른 경로 (`invoke(OverallState())`):
```
invoke(OverallState())
  → __start__ channel = OverallState(variable=['default'])
  → _get_updates(OverallState(...))
      → get_cached_annotated_keys(OverallState) → ['variable']
          → get_update_as_tuples → [('variable', ['default'])]
              → extend_list([], ['default']) = ['default'] ✅
```

`invoke({})` 시 `{}` → `OverallState(**{})` = `OverallState(variable=['default'])` coercion이 없는 것이 핵심 원인.

---

## Fix

`langgraph/graph/state.py`의 `attach_node` 내 `_get_updates` 함수 — `START` 노드에서 Pydantic dict 입력을 스키마로 coerce하는 분기 추가.

### `state.py` 변경 (`_get_updates` 내)

```python
def _get_updates(input):
    if input is None:
        return None
    # For the START node with a Pydantic BaseModel input schema, coerce
    # the user-provided dict through the schema to apply field defaults
    # (e.g. Field(default_factory=...)). This ensures invoke({}) behaves
    # the same as invoke(Schema()) — issue #5225.
    if (
        key == START
        and isinstance(input, dict)
        and isclass(self.builder.input_schema)
        and issubclass(self.builder.input_schema, BaseModel)
    ):
        input = self.builder.input_schema(**input)
    if isinstance(input, dict):
        return [(k, v) for k, v in input.items() if k in output_keys]
    elif isinstance(input, Command):
        ...
```

**핵심 설계 결정:**
- `BinaryOperatorAggregate` / `_get_channels` / `_fields.py` 변경 없음 → 최소 변경
- `TypedDict` / `dataclass` 경로 영향 없음 (조건에 `issubclass(schema, BaseModel)` 가드)
- `invoke(OverallState())` 경로는 기존 `get_cached_annotated_keys` 분기가 처리 (변경 불필요)

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
- [x] 수정 코드 작성 (2026-05-25) — `state.py` `_get_updates` 내 START+Pydantic coercion
- [x] 로컬에서 테스트 실행 확인 (2026-05-25) — 3가지 케이스 + 8개 엣지케이스 통과
- [ ] 회귀 테스트 작성 (실제 PR 준비 시)
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
