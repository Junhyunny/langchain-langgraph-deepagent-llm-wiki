# Reproduction: LangGraph Checkpoint Pending Writes Resume

## 목적

병렬 노드 실행 중 한 노드가 실패했을 때, 성공한 노드의 쓰기(write)가
체크포인트에 pending writes로 보존되고, 재개(resume) 시 성공한 노드가
**재실행되지 않음**을 검증한다.

## 핵심 동작

```
invoke({"value": 1})
  ├── node_one → {"value": 2}  ✓ 성공 (pending write로 저장)
  └── node_two → ConnectionError  ✗ 실패

checkpoint.pending_writes = [
    (task_id_one, "value", 2),       # node_one의 성공 결과
    (task_id_two, "__error__", ...),  # node_two의 오류
]

resume invoke(None)  # node_one은 재실행 안 됨
  └── node_two → 재시도
```

## 실행 방법

```bash
# 프로젝트 루트에서
source .venv/bin/activate
python reproductions/langgraph_checkpoint_pending_writes/pending_writes_resume.py
```

## 관련 LangGraph 테스트

- `libs/langgraph/tests/test_pregel.py::test_pending_writes_resume`
- `libs/langgraph/tests/test_pregel.py::test_run_from_checkpoint_id_retains_previous_writes`

## 검증된 사실 (LangGraph 1.2.1)

- 성공한 노드의 pending write는 체크포인트에 보존된다 ✓
- 재개 시 성공한 노드는 재실행되지 않는다 (멱등성 보장 불필요) ✓
- 최종 값은 초기값 + 성공노드 기여 + 재개노드 기여 = 1+2+3=6 ✓
- `ERROR` 채널명은 v1.0에서 `langgraph.constants.ERROR` public export 폐기됨 ✓

## PR 관련성

→ `docs/wiki/prs/LangGraph checkpoint pending writes tests documentation PR candidate.md`
