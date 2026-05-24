"""Human-in-the-Loop: 순차 interrupt / streaming / interrupt_before 비교.

Shows:
- 단일 노드 내 interrupt() 순차 호출: 매번 별도 invoke 필요
  (각 interrupt() 즉시 실행 중단 → pending interrupt 항상 1개)
- {interrupt_id: value} dict 방식은 병렬 노드에서 각각 interrupt 걸릴 때 사용
- stream() 으로 interrupt 이벤트 관찰
- compile(interrupt_before=["node"]) vs interrupt() 비교

내부 동작 (HumanInTheLoop.md에서 검증):
  interrupt() 첫 호출 → GraphInterrupt 발생 + checkpoint 저장
  Command(resume=value) → is_resuming=True + scratchpad.resume 배열 주입
  노드 처음부터 재실행 → interrupt() 재호출 시 resume 배열에서 순서대로 반환

중요:
  단일 노드의 sequential interrupt() 2개 → invoke 2회 필요
  병렬 노드 각각 interrupt() → 동시에 pending → {id: v} dict 로 1회 resume 가능
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# ---------------------------------------------------------------------------
# 공통 상태
# ---------------------------------------------------------------------------


class ReviewState(TypedDict):
    code: str
    security_ok: bool
    style_ok: bool
    merged: bool


# ---------------------------------------------------------------------------
# 1. 다중 interrupt: 단일 노드에서 두 번 interrupt()
# ---------------------------------------------------------------------------


def code_review_node(state: ReviewState) -> dict[str, Any]:
    """두 가지 관점(보안, 스타일)을 각각 확인한다."""
    # 첫 번째 interrupt: 보안 검토
    security_result = interrupt(
        {"question": "보안 관점에서 이 코드를 승인하시겠습니까?", "code": state["code"]}
    )
    # 두 번째 interrupt: 스타일 검토
    style_result = interrupt(
        {"question": "스타일 관점에서 이 코드를 승인하시겠습니까?", "code": state["code"]}
    )
    return {
        "security_ok": bool(security_result),
        "style_ok": bool(style_result),
    }


def merge_node(state: ReviewState) -> dict[str, bool]:
    return {"merged": state["security_ok"] and state["style_ok"]}


def build_multi_interrupt_graph():
    g = StateGraph(ReviewState)
    g.add_node("review", code_review_node)
    g.add_node("merge", merge_node)
    g.add_edge(START, "review")
    g.add_edge("review", "merge")
    g.add_edge("merge", END)
    return g.compile(checkpointer=InMemorySaver())


def demo_multi_interrupt() -> None:
    print("\n" + "=" * 60)
    print("1. 순차 interrupt 데모 (노드 내 2번 interrupt)")
    print("=" * 60)
    print("  핵심: 각 interrupt()는 즉시 실행 중단 → pending 항상 1개")
    print("  노드 재실행 시 scratchpad.resume[idx] 에서 순서대로 반환")
    app = build_multi_interrupt_graph()
    config = {"configurable": {"thread_id": "multi-interrupt-demo"}}

    # [invoke 1] 첫 번째 interrupt에서 중단
    print("\n[invoke 1] 그래프 실행 시작 → 첫 번째 interrupt에서 중단")
    app.invoke(
        {"code": "def foo(): pass", "security_ok": False, "style_ok": False, "merged": False},
        config=config,
    )
    paused = app.get_state(config)
    interrupts1 = paused.tasks[0].interrupts if paused.tasks else []
    print(f"  next: {paused.next}, pending interrupts: {len(interrupts1)}")
    for intr in interrupts1:
        print(f"  → interrupt.value: {intr.value['question']}")

    # [invoke 2] 첫 번째 interrupt resume → 두 번째 interrupt에서 다시 중단
    print("\n[invoke 2] Command(resume=True) → 노드 재실행, 두 번째 interrupt에서 중단")
    app.invoke(Command(resume=True), config=config)
    paused2 = app.get_state(config)
    interrupts2 = paused2.tasks[0].interrupts if paused2.tasks else []
    print(f"  next: {paused2.next}, pending interrupts: {len(interrupts2)}")
    for intr in interrupts2:
        print(f"  → interrupt.value: {intr.value['question']}")

    # [invoke 3] 두 번째 interrupt resume → 노드 완료
    print("\n[invoke 3] Command(resume=True) → 노드 완료")
    result = app.invoke(Command(resume=True), config=config)
    print(f"  security_ok={result['security_ok']}, style_ok={result['style_ok']}, merged={result['merged']}")
    print("\n  ✅ 노드 내 interrupt() 2개 = invoke 3회 (초기 + resume×2)")


# ---------------------------------------------------------------------------
# 2. stream() 으로 interrupt 이벤트 관찰
# ---------------------------------------------------------------------------


class SimpleState(TypedDict):
    value: str
    confirmed: bool


def confirm_node(state: SimpleState) -> dict[str, bool]:
    answer = interrupt(f"'{state['value']}' 을(를) 확인하시겠습니까?")
    return {"confirmed": answer is True}


def done_node(state: SimpleState) -> dict[str, str]:
    status = "confirmed" if state["confirmed"] else "cancelled"
    return {"value": f"{state['value']} [{status}]"}


def build_stream_demo_graph():
    g = StateGraph(SimpleState)
    g.add_node("confirm", confirm_node)
    g.add_node("done", done_node)
    g.add_edge(START, "confirm")
    g.add_edge("confirm", "done")
    g.add_edge("done", END)
    return g.compile(checkpointer=InMemorySaver())


def demo_stream_interrupt() -> None:
    print("\n" + "=" * 60)
    print("2. stream() 으로 interrupt 이벤트 관찰")
    print("=" * 60)
    app = build_stream_demo_graph()
    config = {"configurable": {"thread_id": "stream-demo"}}

    # stream_mode="updates" 로 확인: interrupt 이벤트가 어떻게 보이는지
    print("[stream updates] 첫 번째 실행:")
    for chunk in app.stream(
        {"value": "hello", "confirmed": False},
        config=config,
        stream_mode="updates",
    ):
        print(f"  chunk: {chunk}")

    print("\n[stream updates] resume 실행:")
    for chunk in app.stream(
        Command(resume=True),
        config=config,
        stream_mode="updates",
    ):
        print(f"  chunk: {chunk}")

    final = app.get_state(config)
    print(f"\n  최종 상태: {final.values}")


# ---------------------------------------------------------------------------
# 3. compile(interrupt_before=...) vs interrupt() 비교
# ---------------------------------------------------------------------------


class PipelineState(TypedDict):
    step: int
    output: str


def step_a(state: PipelineState) -> dict[str, Any]:
    print(f"    step_a 실행 (step={state['step']})")
    return {"step": state["step"] + 1, "output": "step_a done"}


def step_b(state: PipelineState) -> dict[str, Any]:
    print(f"    step_b 실행 (step={state['step']})")
    return {"step": state["step"] + 1, "output": "step_b done"}


def step_b_with_interrupt(state: PipelineState) -> dict[str, Any]:
    """interrupt_before 대신 interrupt()를 직접 사용하는 버전."""
    answer = interrupt("step_b 진입을 허용하시겠습니까?")
    if not answer:
        return {"output": "step_b skipped"}
    print(f"    step_b_with_interrupt 실행 (step={state['step']})")
    return {"step": state["step"] + 1, "output": "step_b done"}


def demo_interrupt_before() -> None:
    print("\n" + "=" * 60)
    print("3. compile(interrupt_before=...) vs interrupt()")
    print("=" * 60)

    # 방법 A: compile(interrupt_before=["step_b"])
    print("\n[방법 A] compile(interrupt_before=['step_b'])")
    g = StateGraph(PipelineState)
    g.add_node("step_a", step_a)
    g.add_node("step_b", step_b)
    g.add_edge(START, "step_a")
    g.add_edge("step_a", "step_b")
    g.add_edge("step_b", END)
    app_a = g.compile(
        checkpointer=InMemorySaver(),
        interrupt_before=["step_b"],
    )
    cfg_a = {"configurable": {"thread_id": "ib-demo"}}
    app_a.invoke({"step": 0, "output": ""}, config=cfg_a)
    state_a = app_a.get_state(cfg_a)
    print(f"  중단 후 next: {state_a.next}")
    print(f"  interrupt 객체: {state_a.tasks[0].interrupts if state_a.tasks else '없음'}")
    # resume: Command 없이 input=None 또는 상태 업데이트만 가능
    result_a = app_a.invoke(None, config=cfg_a)
    print(f"  resume 후 output: {result_a['output']}")

    # 방법 B: 노드 내부에서 interrupt()
    print("\n[방법 B] 노드 내부 interrupt()")
    g2 = StateGraph(PipelineState)
    g2.add_node("step_a", step_a)
    g2.add_node("step_b", step_b_with_interrupt)
    g2.add_edge(START, "step_a")
    g2.add_edge("step_a", "step_b")
    g2.add_edge("step_b", END)
    app_b = g2.compile(checkpointer=InMemorySaver())
    cfg_b = {"configurable": {"thread_id": "intr-demo"}}
    app_b.invoke({"step": 0, "output": ""}, config=cfg_b)
    state_b = app_b.get_state(cfg_b)
    print(f"  중단 후 next: {state_b.next}")
    if state_b.tasks:
        for intr in state_b.tasks[0].interrupts:
            print(f"  interrupt.value: {intr.value}")
    # resume=False: step_b skipped
    result_b = app_b.invoke(Command(resume=False), config=cfg_b)
    print(f"  resume(False) 후 output: {result_b['output']}")

    print("\n[비교 요약]")
    print("  interrupt_before: 중단만 가능, resume에 값 전달 불가")
    print("  interrupt():       조건부 중단, resume 값 전달 가능, 다중 지원")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    demo_multi_interrupt()
    demo_stream_interrupt()
    demo_interrupt_before()


if __name__ == "__main__":
    main()
