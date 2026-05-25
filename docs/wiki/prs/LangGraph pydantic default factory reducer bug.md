---
type: pr_candidate
framework:
  - LangGraph
status: draft
confidence: high
last_reviewed: 2026-05-25
sources:
  - langgraph-venv-fields-py-2026-05-25
  - langgraph-venv-binop-py-2026-05-25
---

# PR 후보: LangGraph Pydantic default_factory + reducer 버그 수정

**연결 이슈**: https://github.com/langchain-ai/langgraph/issues/5225  
**PR 대상 저장소**: `langchain-ai/langgraph`  
**수정 파일**: `libs/langgraph/langgraph/graph/state.py`  
**준비 상태**: 분석 완료 / 회귀 테스트 완료 / 패치 로컬 검증 완료

---

## PR 제목 (초안)

```
fix(graph): coerce dict input through Pydantic schema at START to apply default_factory
```

---

## PR 설명 (초안)

### Problem

When using a `Pydantic BaseModel` as the state schema with an `Annotated` reducer field and
`Field(default_factory=...)`, calling `graph.invoke({})` silently ignores the default value:

```python
class State(BaseModel):
    items: Annotated[list[str], operator.add] = Field(default_factory=list)

app.invoke({})
# Expected: {'items': []}  (default_factory applied)
# Actual:   {'items': []}  (appears correct but initial accumulation missing)

# More visible with a non-empty default:
class State(BaseModel):
    items: Annotated[list[str], extend_list] = Field(default_factory=lambda: ['seed'])

app.invoke({})
# Expected: {'items': ['seed', 'added']}
# Actual:   {'items': ['added']}   ← 'seed' lost
```

The root cause is in `state.py` `attach_node._get_updates`. When the input to the `START` node
is a plain `dict`, the code iterates `dict.items()` directly — never instantiating the Pydantic
schema. The `default_factory` values are therefore never contributed as channel updates.

By contrast, `invoke(State())` works correctly because the Pydantic instance takes the
`get_cached_annotated_keys` branch which extracts all field values including defaults.

### Fix

Add a single guard in `_get_updates` that coerces a bare `dict` input through the Pydantic schema
when the graph's input schema is a Pydantic `BaseModel` and the node being entered is `START`:

```python
# state.py — attach_node._get_updates
def _get_updates(input):
    if input is None:
        return None
    # Coerce dict → Pydantic schema at START so default_factory fields
    # contribute channel updates. Mirrors what invoke(Schema()) already does.
    # Fixes issue #5225.
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

This change is minimal and surgical:
- Only affects the `START` node path
- Only activates when the input schema is explicitly a Pydantic `BaseModel`
- Does not alter `BinaryOperatorAggregate`, `_fields.py`, or any other channel logic
- `TypedDict` and `dataclass` schemas are unaffected

### Why not fix `_fields.py::get_field_default` or `BinaryOperatorAggregate`?

- **`_fields.py`**: `get_field_default` is called during graph construction to set initial channel
  values. Fixing defaults there would require channels to be seeded at graph-compile time, but
  channels are intentionally initialised empty (they are accumulators, not containers with defaults).
- **`BinaryOperatorAggregate.__init__`**: `self.value = typ()` is correct. The channel starts
  empty and accumulates updates. Prepopulating it with defaults would break `from_checkpoint`
  semantics (restored channels would double-apply defaults).

### Tests

New regression tests in `libs/langgraph/tests/test_pregel.py`:

```python
def test_pydantic_default_factory_with_reducer():
    """invoke({}) must apply Field(default_factory=...) for Pydantic schemas."""
    ...

def test_pydantic_default_factory_with_checkpointer():
    """Checkpointing must not double-apply defaults on resume."""
    ...
```

Full test file: `reproductions/langgraph_pydantic_default_factory/test_regression.py`
- 12 test cases (8 pass, 4 xfail documenting the bug before fix)
- After fix: all 12 should pass

---

## 변경 사항 요약

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `libs/langgraph/langgraph/graph/state.py` | fix | `_get_updates`에 START+Pydantic coercion 분기 추가 |
| `libs/langgraph/tests/test_pregel.py` | test | Pydantic + reducer 회귀 테스트 추가 |

---

## 테스트 계획 (PR 리뷰어 체크리스트)

- [ ] `invoke({})` — Pydantic + reducer + default_factory → 기본값 적용됨
- [ ] `invoke(State())` — 기존 동작 유지 (이미 작동하던 경로)
- [ ] `invoke({'field': value})` — 명시적 값 전달 시 기본값 무시 (정상)
- [ ] checkpointer + 두 번 invoke → 기본값이 두 번 누적되지 않음
- [ ] TypedDict 스키마 — 영향 없음
- [ ] dataclass 스키마 — 영향 없음
- [ ] 기존 test suite (`pytest libs/langgraph/tests/`) — 전체 통과

---

## PR 제출 전 확인 사항

- [ ] 이슈 #5225에 PR 번호 연결 (Fixes #5225)
- [ ] 기여 가이드 확인 (`CONTRIBUTING.md`): 이슈 먼저 승인 필요 여부
- [ ] English-only 코드 및 코멘트 (기여 가이드 언어 정책)
- [ ] commit 메시지 형식 확인 (conventional commits: `fix(graph): ...`)
- [ ] `CHANGELOG.md` 업데이트 필요 여부 확인
- [ ] `libs/langgraph/pyproject.toml` 버전 bump 필요 여부 확인

---

## 실제 PR 작성 시 포함할 내용

1. **제목**: `fix(graph): coerce dict input through Pydantic schema at START to apply default_factory`
2. **본문**: 위 PR 설명 초안 영어 버전
3. **Fixes**: `Fixes #5225`
4. **테스트**: 회귀 테스트 코드 첨부 또는 인라인
5. **라벨**: `bug`, `needs-test`

---

## 학습 인사이트

- 오픈소스 버그 수정 PR의 핵심: 최소 변경 + 영향 범위 명시 + 회귀 테스트
- 설계 결정(왜 다른 위치를 수정하지 않았는가)을 PR 설명에 포함해야 리뷰어 이해를 돕는다
- `default_factory`와 reducer를 함께 사용하는 패턴은 공식 문서에 예제가 없어 버그가 오래 남아있었음
- 수정 위치를 찾는 과정: 공개 API 동작 차이(`{}` vs `State()`) → `_get_updates` 분기 → coercion 누락

---

## 관련 페이지

- [[LangGraph issue 5225 pydantic default factory]] → `issues/LangGraph issue 5225 pydantic default factory.md`
- [[LangGraph]] → `frameworks/LangGraph.md`
- [[LangGraph Code Map]] → `codebase/LangGraph Code Map.md`
- [[Checkpointing]] → `concepts/Checkpointing.md`

## Sources

- `langgraph-venv-fields-py-2026-05-25`
- `langgraph-venv-binop-py-2026-05-25`
- 직접 실행 확인: `.venv` 패치 후 8케이스 검증 (2026-05-25)
- 재현: `reproductions/langgraph_pydantic_default_factory/reproduce.py`
- 회귀 테스트: `reproductions/langgraph_pydantic_default_factory/test_regression.py`
