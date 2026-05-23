---
type: pr_candidate
framework:
  - LangGraph
status: in_progress
confidence: high
last_reviewed: 2026-05-24
sources:
  - langgraph-tests-checkpoint-recovery-2026-05-23
  - langgraph-source-checkpoint-internals-2026-05-23
---

# LangGraph checkpoint pending writes tests documentation PR candidate

## 문제
`ERROR` 상수(`langgraph.constants.ERROR`)가 LangGraph v1.0에서 deprecated되었으나,
공식 테스트 파일(`test_pregel.py`)이 여전히 이 상수를 직접 import해 사용하고 있다.
이 상수는 v2.0에서 제거될 예정이다.

또한 pending writes resume 동작은 강력하지만 공식 문서에 설명이 없어 기여자가 동작을 파악하기 어렵다.

## 소스 근거
- `test_pending_writes_resume`(line 876): `from langgraph.constants import ERROR` 사용
- `test_run_from_checkpoint_id_retains_previous_writes`(line 577): checkpoint 시간 여행 동작 검증
- 로컬 재현 결과: `langgraph.constants.ERROR` import 시 DeprecationWarning 발생 (v1.2.1 기준)

## 재현 (검증됨 ✓)
- 로컬 파일: `reproductions/langgraph_checkpoint_pending_writes/pending_writes_resume.py`
- 실행 결과: LangGraph 1.2.1에서 `ERROR` import 시 deprecation warning 발생
- 검증된 동작:
  - 병렬 노드 중 성공 노드의 쓰기 → pending_writes에 보존됨
  - 재개 시 성공 노드 재실행 없음 (호출 횟수 1회 유지)
  - 최종 값: 1+2+3=6 (정상)

## 의심되는 근본 원인
- `ERROR` 상수가 내부용으로 전환되었으나 테스트에서 public import 패턴이 남아 있음
- `test_pregel.py`의 해당 테스트들이 아직 private API 전환을 반영하지 않음

## 제안된 변경

### Option A: 테스트 코드 패치 (작고 명확)
`libs/langgraph/tests/test_pregel.py`에서 `ERROR` 직접 import를 제거하고
내부 상수나 `__error__` 문자열로 대체:

```python
# Before (deprecated)
from langgraph.constants import ERROR
...
assert w[1] == ERROR

# After (private constant 또는 문자열 리터럴)
_ERROR = "__error__"
...
assert w[1] == _ERROR
```

### Option B: 문서 추가 (보완적)
LangGraph 기여자 가이드에 "checkpoint pending writes" 섹션 추가:
- 동작 설명
- 회귀 테스트 위치 명시

## 테스트 계획
- `test_pregel.py::test_pending_writes_resume` — 수정 후 통과 확인
- `test_pregel.py::test_run_from_checkpoint_id_retains_previous_writes` — 연관 테스트 통과 확인
- deprecation warning 없이 실행되는지 확인

## 위험
- Option A는 테스트 내부 로직 변경 없음. `__error__` 채널명이 실제로 사용되는 값인지 최종 확인 필요.
- 채널명은 내부 구현이므로 버전 간 변경 가능성 있음 → 적절한 fixture 또는 enum 사용 검토

## 다음 행동
- [x] `__error__` 채널명이 실제로 쓰이는 값인지 `_internal/_constants.py`에서 확인 → `ERROR = sys.intern("__error__")` (line 13) ✓
- [x] `langgraph.constants`의 `__getattr__` 패턴 확인 — private 상수 접근 시 deprecation warning 발생 ✓
- [ ] 기존 LangGraph 이슈/PR에서 `ERROR` deprecation 관련 패치 언급 여부 검색
- [ ] `test_pregel.py` 패치: `from langgraph.constants import ERROR` → `from langgraph._internal._constants import ERROR` 또는 `_ERROR = "__error__"` 사용
- [ ] 패치 초안 작성 후 PR 메모 완성

## 확인된 소스 코드 참조
- Repo: langgraph
- Commit: UNKNOWN (main branch 기준)
- Files:
  - `libs/langgraph/langgraph/_internal/_constants.py` line 13: `ERROR = sys.intern("__error__")`
  - `libs/langgraph/langgraph/constants.py` line 50-62: `__getattr__` deprecation warning 패턴
  - `libs/langgraph/tests/test_pregel.py` line 876: `test_pending_writes_resume` (ERROR import 사용)

## PR 메모 초안

```
## Problem
`langgraph.constants.ERROR` was deprecated in v1.0 with a warning that it
will be removed in v2.0, but test_pregel.py still imports it directly.

## Root Cause
The `ERROR` constant was made private but the test files were not updated.

## Fix
Replace `from langgraph.constants import ERROR` in test_pregel.py with the
private constant or a string literal.

## Tests
Existing tests pass without change to test logic.

## Risk
Low — test-only change, no runtime behavior modified.
```

## 상태
in_progress — 재현 완료, 코드 패치 확인 진행 중

## Sources
- `langgraph-tests-checkpoint-recovery-2026-05-23`
- `langgraph-source-checkpoint-internals-2026-05-23`
