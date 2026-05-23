"""
Reproduction: LangGraph pending writes resume behavior
=====================================================
이 스크립트는 두 노드가 병렬로 실행될 때 한 노드가 실패해도
성공한 노드의 쓰기가 pending writes로 보존되어
재개(resume) 시 성공한 노드는 재실행되지 않음을 검증한다.

관련 테스트: libs/langgraph/tests/test_pregel.py::test_pending_writes_resume
LangGraph 버전: 1.2.1
"""

import operator
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

# NOTE: ERROR was previously importable from langgraph.constants but is now
# deprecated in v1.0 (to be removed in v2.0). We use the string directly.
_ERROR_CHANNEL = "__error__"


class State(TypedDict):
    value: Annotated[int, operator.add]


class CountingNode:
    """호출 횟수를 추적하는 노드."""

    def __init__(self, name: str, rtn: dict | Exception):
        self.name = name
        self.rtn = rtn
        self.calls = 0

    def __call__(self, state: State) -> Any:
        self.calls += 1
        if isinstance(self.rtn, Exception):
            raise self.rtn
        return self.rtn


def build_graph(node_one: CountingNode, node_two: CountingNode) -> Any:
    builder = StateGraph(State)
    builder.add_node("one", node_one)
    builder.add_node("two", node_two)
    builder.add_edge(START, "one")
    builder.add_edge(START, "two")
    builder.add_edge("one", END)
    builder.add_edge("two", END)
    return builder.compile(checkpointer=MemorySaver())


def main():
    node_one = CountingNode("one", {"value": 2})
    node_two = CountingNode("two", ConnectionError("node two failed"))
    graph = build_graph(node_one, node_two)

    config = {"configurable": {"thread_id": "1"}}

    # ── Phase 1: 첫 실행 → node_two 실패 ─────────────────────────────────────
    print("=== Phase 1: Initial invoke (node_two will fail) ===")
    try:
        graph.invoke({"value": 1}, config)
    except ConnectionError as e:
        print(f"Expected error: {e}")

    print(f"node_one calls: {node_one.calls}  (expected 1)")
    print(f"node_two calls: {node_two.calls}  (expected 1)")

    # ── 체크포인트 검사 ────────────────────────────────────────────────────────
    state = graph.get_state(config)
    print(f"\nState after failure:")
    print(f"  values = {state.values}  (expected {{'value': 3}} = 1+2 from node_one)")
    print(f"  next   = {state.next}    (expected ('two',))")

    checkpoint_tuple = graph.checkpointer.get_tuple(config)
    pending = checkpoint_tuple.pending_writes
    print(f"\nPending writes count: {len(pending)}  (expected 2)")
    for w in pending:
        if w[1] == _ERROR_CHANNEL:
            print(f"  ERROR write: {w[2][:40]}")
        else:
            print(f"  value write: channel={w[1]}, value={w[2]}")

    # ── Phase 2: 재개 → node_one은 재실행 안 됨 ──────────────────────────────
    print("\n=== Phase 2: Resume (node_two still fails) ===")
    node_two.rtn = ConnectionError("still failing")
    try:
        graph.invoke(None, config)
    except ConnectionError as e:
        print(f"Expected error: {e}")

    print(f"node_one calls: {node_one.calls}  (expected 1 — NOT re-executed)")
    print(f"node_two calls: {node_two.calls}  (expected 2)")

    # ── Phase 3: 재개 → node_two 성공 ────────────────────────────────────────
    print("\n=== Phase 3: Resume (node_two now succeeds) ===")
    node_two.rtn = {"value": 3}
    result = graph.invoke(None, config)
    print(f"Final result: {result}  (expected {{'value': 6}} = 1+2+3)")
    print(f"node_one calls: {node_one.calls}  (expected 1 — still not re-executed)")
    print(f"node_two calls: {node_two.calls}  (expected 3)")

    # ── 검증 ──────────────────────────────────────────────────────────────────
    print("\n=== Assertions ===")
    assert node_one.calls == 1, f"node_one should run once, got {node_one.calls}"
    assert node_two.calls == 3, f"node_two should run 3 times, got {node_two.calls}"
    assert result == {"value": 6}, f"Final value should be 6, got {result}"
    print("All assertions passed ✓")
    print()
    print("Key finding: 성공한 노드(one)의 pending write가 체크포인트에 보존되어")
    print("재개 시 재실행 없이 그 결과가 적용됨을 확인했다.")


if __name__ == "__main__":
    main()
