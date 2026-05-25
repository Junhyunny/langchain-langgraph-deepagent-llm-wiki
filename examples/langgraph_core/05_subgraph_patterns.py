"""LangGraph 서브그래프 패턴 실험.

학습 목표:
1. 서브그래프-as-노드: 상태 스키마 호환성 요구사항 확인
2. Send API: map-reduce 패턴에서 worker 결과 집계 방법
3. Command(goto=PARENT): 서브그래프에서 부모로 제어 반환
"""

from __future__ import annotations

from operator import add
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send


# ─────────────────────────────────────────
# 실험 1: 서브그래프-as-노드 — 공유 키 호환성
# ─────────────────────────────────────────

class ParentState(TypedDict):
    query: str
    result: str       # 부모와 서브그래프 양쪽에 존재하는 키


class SubgraphState(TypedDict):
    query: str        # 부모와 공유 — 값이 상속됨
    result: str       # 부모와 공유 — 반환 시 부모 상태에 병합됨
    internal_step: str  # 서브그래프 전용 — 부모에 없어도 됨


def subgraph_process(state: SubgraphState) -> dict:
    return {
        "internal_step": f"processed: {state['query']}",
        "result": f"[subgraph answer] {state['query'].upper()}",
    }


def build_subgraph() -> StateGraph:
    sg = StateGraph(SubgraphState)
    sg.add_node("process", subgraph_process)
    sg.add_edge(START, "process")
    sg.add_edge("process", END)
    return sg.compile()


def experiment_1_subgraph_as_node():
    print("\n=== 실험 1: 서브그래프-as-노드 ===")
    subgraph = build_subgraph()

    parent = StateGraph(ParentState)
    # 컴파일된 서브그래프를 노드로 직접 추가
    parent.add_node("sub", subgraph)
    parent.add_edge(START, "sub")
    parent.add_edge("sub", END)
    app = parent.compile()

    result = app.invoke({"query": "hello world", "result": ""})
    print(f"결과: {result}")
    # 확인 포인트: internal_step은 ParentState에 없으므로 출력에서 제외됨
    print(f"internal_step 존재 여부: {'internal_step' in result}")


# ─────────────────────────────────────────
# 실험 2: Send API — map-reduce 패턴
# ─────────────────────────────────────────

class OverallState(TypedDict):
    items: list[str]
    results: Annotated[list[str], add]  # Reducer: 각 worker 결과를 누적


class WorkerState(TypedDict):
    item: str


def dispatch(state: OverallState) -> list[Send]:
    return [Send("worker", {"item": item}) for item in state["items"]]


def worker(state: WorkerState) -> dict:
    return {"results": [f"DONE:{state['item']}"]}


def experiment_2_send_map_reduce():
    print("\n=== 실험 2: Send API map-reduce ===")
    graph = StateGraph(OverallState)
    graph.add_node("dispatcher", lambda s: {})  # dispatcher 노드 (아무것도 안 함)
    graph.add_node("worker", worker)
    graph.add_edge(START, "dispatcher")
    graph.add_conditional_edges("dispatcher", dispatch)
    graph.add_edge("worker", END)
    app = graph.compile()

    result = app.invoke({"items": ["a", "b", "c"], "results": []})
    print(f"결과: {result}")
    # 확인 포인트: 3개 worker 결과가 Reducer(add)로 병합됨


# ─────────────────────────────────────────
# 실험 3: 서브그래프에서 공유 키 없으면 어떻게 되나?
# ─────────────────────────────────────────

class ParentStateB(TypedDict):
    msg: str


class SubgraphStateB(TypedDict):
    internal: str   # 부모와 공유 키 없음


def subgraph_b_node(state: SubgraphStateB) -> dict:
    return {"internal": "done"}


def experiment_3_no_shared_keys():
    print("\n=== 실험 3: 공유 키 없는 서브그래프 ===")
    sg = StateGraph(SubgraphStateB)
    sg.add_node("n", subgraph_b_node)
    sg.add_edge(START, "n")
    sg.add_edge("n", END)
    subgraph = sg.compile()

    parent = StateGraph(ParentStateB)
    parent.add_node("sub", subgraph)
    parent.add_edge(START, "sub")
    parent.add_edge("sub", END)
    app = parent.compile()

    try:
        result = app.invoke({"msg": "test"})
        print(f"결과: {result}")
        print("공유 키 없어도 에러 없음 — 서브그래프 출력이 부모 상태에 병합되지 않음")
    except Exception as e:
        print(f"에러: {type(e).__name__}: {e}")


# ─────────────────────────────────────────
# 실험 4: input_schema / output_schema 분리
# ─────────────────────────────────────────

class FullState(TypedDict):
    query: str
    result: str
    debug_info: str   # 내부용


class InputSchema(TypedDict):
    query: str        # 입력에서는 query만 필요


class OutputSchema(TypedDict):
    result: str       # 출력은 result만 노출


def process_node(state: FullState) -> dict:
    return {
        "result": f"processed: {state['query']}",
        "debug_info": "step=1",
    }


def experiment_4_input_output_schema():
    print("\n=== 실험 4: input_schema / output_schema 분리 ===")
    graph = StateGraph(FullState, input_schema=InputSchema, output_schema=OutputSchema)
    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)
    app = graph.compile()

    result = app.invoke({"query": "what is LangGraph?"})
    print(f"결과: {result}")
    print(f"debug_info 노출 여부: {'debug_info' in result}")
    # 확인 포인트: output_schema 때문에 debug_info가 제외됨


if __name__ == "__main__":
    experiment_1_subgraph_as_node()
    experiment_2_send_map_reduce()
    experiment_3_no_shared_keys()
    experiment_4_input_output_schema()
