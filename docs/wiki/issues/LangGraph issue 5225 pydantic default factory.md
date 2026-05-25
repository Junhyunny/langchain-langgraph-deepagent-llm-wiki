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

**검증됨** (`.venv` 직접 소스 읽기 + 실행 확인, 2026-05-25)

### 호출 경로 (올바른 분석)

`invoke({})` 시:
```
invoke({})
  → __start__ channel = {}
  → attach_node(START) → _get_updates({})
      → isinstance({}, dict) → [k, v for {}.items()] = []   ← 빈 리스트
          → 아무 channel도 업데이트 안 됨 → 채널 초기값 [] 유지 (버그)
```

`invoke(OverallState())` 시 (정상 동작):
```
invoke(OverallState())
  → __start__ channel = OverallState(variable=['default'])
  → _get_updates(OverallState(...))
      → get_cached_annotated_keys(OverallState) → ['variable']
          → get_update_as_tuples → [('variable', ['default'])]
              → extend_list([], ['default']) = ['default'] ✅
```

**핵심**: `invoke({})` 시 `{}` → `OverallState(**{})` = `OverallState(variable=['default'])` coercion이 없는 것이 문제.

`_get_channels`의 `BinaryOperatorAggregate.__init__`은 항상 `typ()` = `[]`로 초기화하지만, 이는 **채널 초기 상태** 설정의 문제가 아니다. 채널 초기값은 `[]`이어야 정상 — reducer는 누산기로 설계되어 있다.

### 근본 원인 요약

`state.py` `attach_node`의 `_get_updates` 함수가 `START` 노드 + Pydantic BaseModel 스키마 + `dict` 입력 시, Pydantic 스키마로 coerce하지 않아 `Field(default_factory=...)` 기본값을 포함한 channel update가 생성되지 않음.

---

## 제안된 수정 방향

### ✅ 채택된 방법: `_get_updates` 내 START+Pydantic coercion

`langgraph/graph/state.py`의 `attach_node` 내 `_get_updates` 함수에 분기 추가:

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
    ...
```

**장점:**
- 최소 변경 (`binop.py`, `_fields.py` 변경 없음)
- TypedDict / dataclass 경로 영향 없음
- `BinaryOperatorAggregate` 의미론 변경 없음 (채널은 항상 `[]`로 시작하는 것이 올바름)

**검증됨 (2026-05-25):**
```
invoke({})                       → ['default', 'added'] ✅
invoke(OverallState())           → ['default', 'added'] ✅
invoke({'variable': ['start']})  → ['start', 'added']   ✅
checkpointer + resume 케이스      → 정상 누산 ✅
TypedDict 케이스                  → 변경 없음 ✅
```

### 기각된 방법들

- **방법 A** (`_fields.py::get_field_default()` Pydantic 분기): `get_field_default`는 채널 초기값에 직접 연결되지 않음. 채널 초기값 `[]`는 올바른 설계
- **방법 B** (`BinaryOperatorAggregate`에 `default` 파라미터): `from_checkpoint(MISSING)` 시 새 `__init__` 호출로 무력화됨
- **방법 C** (`_get_channels`에서 초기값 오버라이드): `from_checkpoint(MISSING)` 시 `self.__class__(self.typ, self.operator)` 새 인스턴스 생성으로 무력화됨

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

- [x] `reproductions/langgraph_pydantic_default_factory/reproduce.py` 실행 확인 (2026-05-25)
- [x] 수정 방향 확정: `_get_updates` START+Pydantic coercion (2026-05-25)
- [x] `.venv` 로컬 fix 검증 완료 — 8개 케이스 통과 (2026-05-25)
- [ ] LangGraph 저장소 fork 후 공식 fix + 회귀 테스트 작성
- [ ] PR 제출

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
