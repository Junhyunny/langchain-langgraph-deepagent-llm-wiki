"""
10_toolnode_parent_command_send.py — ToolNode Command.PARENT + Send

이 파일이 보여주는 것:
  1. child graph 안의 ToolNode가 Command(graph=Command.PARENT, goto=[Send(...)]) 반환
  2. parent graph의 collector 노드가 Send 입력으로 여러 번 실행됨
  3. ToolNode._combine_tool_outputs()가 여러 parent Send command를 병합함
  4. parent command는 current graph Command와 달리 matching ToolMessage가 필요하지 않음

실행:
  python examples/langgraph_core/10_toolnode_parent_command_send.py
"""

from __future__ import annotations

from operator import add
from typing import Annotated

from langchain_core.messages import AIMessage, ToolCall
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, Send
from typing_extensions import TypedDict


class ChildState(TypedDict):
    messages: Annotated[list, add_messages]


class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    collected: Annotated[list[str], add]


class CollectorInput(TypedDict):
    item: str
    source: str


@tool
def send_to_parent(item: str) -> Command:
    """Send an item to the parent graph collector."""
    return Command(
        graph=Command.PARENT,
        goto=[Send("collector", {"item": item, "source": "child-tool"})],
    )


def child_model_node(state: ChildState) -> dict:
    """Script two tool calls so ToolNode emits two parent Send commands."""
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    ToolCall(
                        name="send_to_parent",
                        args={"item": "alpha"},
                        id="send-alpha",
                    ),
                    ToolCall(
                        name="send_to_parent",
                        args={"item": "beta"},
                        id="send-beta",
                    ),
                ],
            )
        ]
    }


def build_child_graph():
    child = StateGraph(ChildState)
    child.add_node("child_model", child_model_node)
    child.add_node("child_tools", ToolNode([send_to_parent]))
    child.add_edge(START, "child_model")
    child.add_edge("child_model", "child_tools")
    return child.compile()


def collector_node(state: CollectorInput) -> dict:
    print(f"  collector input: {state}")
    return {"collected": [f"{state['source']}:{state['item']}"]}


def experiment_parent_send_fanout() -> None:
    print("=== Command.PARENT + Send fan-out ===")
    child_graph = build_child_graph()

    parent = StateGraph(ParentState)
    parent.add_node("child", child_graph)
    parent.add_node("collector", collector_node)
    parent.add_edge(START, "child")
    parent.add_edge("collector", END)
    app = parent.compile()

    result = app.invoke({"messages": [], "collected": []})

    print("  parent result:")
    print(f"    messages: {result['messages']}")
    print(f"    collected: {result['collected']}")
    print()
    print("What to notice:")
    print("  - parent graph has no static child -> collector edge")
    print("  - child ToolNode returned parent Send commands that invoked collector twice")
    print("  - parent messages stayed empty because the parent Command carried goto only")
    print("  - no matching ToolMessage was required for Command.PARENT")


if __name__ == "__main__":
    experiment_parent_send_fanout()
