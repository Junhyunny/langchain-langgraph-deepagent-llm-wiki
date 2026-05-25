---
type: issue
framework:
  - LangGraph
status: verified
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-venv-fields-py-2026-05-25
---

# LangGraph Issue #5225 — Pydantic BaseModel default_factory + reducer 버그

**이슈 URL**: https://github.com/langchain-ai/langgraph/issues/5225  
**레이블**: `bug`, `help wanted`, `external`  
**상태**: Open (2026-05-25 기준)

---

## Summary

Pydantic `BaseModel`을 상태 스키마로 사용할 때, `Field(default_factory=...)`로 지정된 기본값이 `graph.invoke({})` 호출 시 무시된다.

---

## Why It Matters

Pydantic은 LangGraph에서 상태 스키마로 공식 지원되는 방식이다. `TypedDict`와 달리 필드 유효성 검사와 `default_factory` 지원이 장점인데, reducer(`Annotated`)와 함께 사용 시 기본값이 동작하지 않으면 사용자 기대와 실제 동작이 불일치한다.

---

## 재현 코드

```python
from typing import Annotated
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

def extend_list(original: list, new: list):
    original.extend(new)
    return original

class OverallState(BaseModel):
    variable: Annotated[list[str], extend_list] = Field(
        default_factory=lambda: ['default']
    )

def node(s: OverallState):
    return {'variable': ['added']}

graph = StateGraph(OverallState)
graph.add_node('node', node)
graph.add_edge(START, 'node')
graph.add_edge('node', END)
app = graph.compile()
```

### 기대 동작

```python
app.invoke({})
# 기대: {'variable': ['default', 'added']}
# 이유: invoke({})는 OverallState()와 동등하게 처리되어야 함
#       OverallState().variable == ['default']
```

### 실제 동작 (버그)

```python
app.invoke({})
# 실제: {'variable': ['added']}
# 이유: default_factory가 무시되어 변수가 [] (빈 리스트)로 초기화됨
```

### 정상 동작 케이스

```python
app.invoke({'variable': ['start']})  # → {'variable': ['start', 'added']}  ✅
app.invoke(OverallState())           # → {'variable': ['default', 'added']} ✅
```

---

## 근본 원인 분석

**검증됨** (`.venv` 직접 소스 읽기, 2026-05-25)

### 호출 경로

```
StateGraph(OverallState)
  → _get_channels(OverallState)           # state.py line 1801
      → _get_channel("variable", Annotated[list[str], extend_list])
          → _is_field_binop()             # callable 감지
          → BinaryOperatorAggregate(list[str], extend_list)
              → self.value = list()       # binop.py line 76 ← 버그 위치
```

### 문제 코드

**`langgraph/channels/binop.py`, line 63–78:**

```python
def __init__(self, typ: type[Value], operator: Callable[[Value, Value], Value]):
    super().__init__(typ)
    self.operator = operator
    typ = _strip_extras(typ)
    # ... (list, set, dict 치환)
    try:
        self.value = typ()   # 항상 빈 생성자 호출 → list() = []
    except Exception:
        self.value = MISSING
```

`BinaryOperatorAggregate.__init__`은 `typ()` (= `list()` = `[]`)로 초기화하며, 스키마의 Pydantic 필드 default를 전혀 참조하지 않는다.

### 보조 문제: `get_field_default()`

**`langgraph/_internal/_fields.py`, line 79–122:**

```python
def get_field_default(name: str, type_: Any, schema: type[Any]) -> Any:
    # TypedDict optional_keys 처리 있음 ✅
    # dataclasses.field.default_factory 처리 있음 ✅
    if dataclasses.is_dataclass(schema):
        field_info = ...
        if field_info.default_factory is not dataclasses.MISSING:
            return field_info.default_factory()  # ✅
    # Pydantic BaseModel 처리 없음 ❌
    if _is_optional_type(type_):
        return None
    return ...  # MISSING
```

`get_field_default()`는 dataclass `default_factory`는 처리하지만, **Pydantic `model_fields[name].default_factory`는 처리하지 않는다.** (단, `get_field_default`는 JSON 스키마 용도로 호출되며, 채널 초기값 설정과 직접 연결은 추가 확인 필요)

### 핵심 원인 요약

1. `BinaryOperatorAggregate.__init__` → `self.value = typ()` (스키마 default 무시)
2. `_get_channels(schema)` → `_get_channel(name, typ)` 호출 시 스키마를 전달하지 않음
3. `_get_channel` → channel 생성 시 Pydantic field default 조회 경로 없음

---

## 영향 범위

- Pydantic `BaseModel` + `Annotated[..., reducer]` + `Field(default_factory=...)` 조합
- `invoke({})` 또는 초기 상태 없이 그래프를 시작할 때
- `TypedDict` 또는 `dataclass` 스키마는 영향받지 않음 (별도 코드 경로)
- `invoke(OverallState())` 처럼 명시적 객체 전달 시는 정상 동작

---

## 제안된 수정 방향

### 방법 A: `_fields.py::get_field_default()`에 Pydantic 분기 추가

```python
# 기존 dataclasses 처리 뒤에 추가
from pydantic import BaseModel
from pydantic.fields import PydanticUndefined

if isinstance(schema, type) and issubclass(schema, BaseModel):
    if name in schema.model_fields:
        field_info = schema.model_fields[name]
        if field_info.default is not PydanticUndefined:
            return field_info.default
        elif field_info.default_factory is not None:
            return field_info.default_factory()
```

단, `get_field_default`가 채널 초기값에 실제로 연결되는지 확인 필요.

### 방법 B: `BinaryOperatorAggregate`에 `default` 파라미터 추가

```python
def __init__(self, typ, operator, default=MISSING):
    ...
    if default is not MISSING:
        self.value = default
    else:
        try:
            self.value = typ()
        except Exception:
            self.value = MISSING
```

그리고 `_get_channel` 또는 `_get_channels`에서 Pydantic default를 추출해 전달.

### 방법 C: `_get_channels`에서 Pydantic default 추출 + 채널 초기값 설정

`_get_channels(schema)` 내에서 `BaseModel` 체크 후 각 필드의 `default_factory`를 추출하여 채널 초기값을 오버라이드.

---

## 관련 코드 파일

```
# 버그 발생 위치
.venv/lib/.../langgraph/channels/binop.py
  - BinaryOperatorAggregate.__init__() : line 63-78

.venv/lib/.../langgraph/_internal/_fields.py
  - get_field_default() : line 79-122

.venv/lib/.../langgraph/graph/state.py
  - _get_channels() : line 1801-1821
  - _get_channel() : line 1836-1859
```

---

## 관련 테스트 (탐색 필요)

- `test_pregel.py`에서 Pydantic BaseModel 상태 + reducer 조합 테스트 존재 여부 확인 필요
- 현재 이 조합에 대한 회귀 테스트가 없을 가능성이 높음 (버그가 열려 있으므로)

---

## 다음 행동

- [ ] `reproductions/langgraph_pydantic_default_factory/reproduce.py` 실행 확인
- [ ] 수정 방향 확정 (A/B/C 중 선택)
- [ ] 회귀 테스트 작성
- [ ] `docs/wiki/prs/` PR candidate 페이지로 이동

---

## Sources

- Source Code References:
  - Repo: langgraph (`.venv` 직접 읽기)
  - Files:
    - `langgraph/channels/binop.py` (line 63-78)
    - `langgraph/_internal/_fields.py` (line 79-122)
    - `langgraph/graph/state.py` (line 1801-1859)
- 직접 실행 확인: `graph.invoke({})` → `['added']` (버그 확인됨, 2026-05-25)

## Related Pages

- [[LangGraph]]
- [[Checkpointing]]
- [[LangGraph Code Map]]
