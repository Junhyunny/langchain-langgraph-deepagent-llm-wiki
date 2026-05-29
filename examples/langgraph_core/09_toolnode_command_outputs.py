"""
09_toolnode_command_outputs.py — ToolNode가 Command를 반환할 때의 상태/라우팅

이 파일이 보여주는 것:
  1. 도구가 Command(update=...)를 반환하면 ToolNode가 Command를 그대로 내보냄
  2. compiled graph 안에서는 Command.update가 실제 state update로 적용됨
  3. wrap_tool_call도 Command(update=..., goto=...)를 반환해 라우팅을 바꿀 수 있음
  4. 현재 graph에 대한 Command.update에는 matching ToolMessage가 필요함

실행:
  python examples/langgraph_core/09_toolnode_command_outputs.py
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Any

from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph._internal._constants import CONF, CONFIG_KEY_RUNTIME
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command
from typing_extensions import TypedDict


TOOLNODE_CONFIG = {CONF: {CONFIG_KEY_RUNTIME: Runtime()}}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    audit: Annotated[list[str], add]
    route: str


@tool
def command_note(
    topic: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Record a note by returning a LangGraph Command."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"noted:{topic}",
                    tool_call_id=tool_call_id,
                )
            ],
            "audit": [f"tool-command:{topic}"],
        }
    )


@tool
def plain_note(topic: str) -> str:
    """Return a plain note."""
    return f"plain:{topic}"


@tool
def invalid_command(
    topic: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Return an invalid Command missing the required ToolMessage terminator."""
    return Command(update={"audit": [f"invalid:{topic}"]})


def make_ai_message(tool_name: str, call_id: str, topic: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            ToolCall(
                name=tool_name,
                args={"topic": topic},
                id=call_id,
            )
        ],
    )


def print_messages(messages: list[Any]) -> None:
    for msg in messages:
        if isinstance(msg, ToolMessage):
            print(f"    ToolMessage id={msg.tool_call_id!r}, content={msg.content!r}")
        elif isinstance(msg, AIMessage) and msg.tool_calls:
            calls = [f"{call['name']}({call['args']})" for call in msg.tool_calls]
            print(f"    AIMessage tool_calls={calls}")
        else:
            print(f"    {type(msg).__name__}: {getattr(msg, 'content', msg)!r}")


def experiment_1_standalone_command_output() -> None:
    print("=== 1. standalone ToolNode returns Command ===")
    node = ToolNode([command_note])
    result = node.invoke(
        {
            "messages": [make_ai_message("command_note", "standalone-call", "standalone")],
            "audit": [],
            "route": "",
        },
        config=TOOLNODE_CONFIG,
    )

    print(f"  output type: {type(result).__name__}")
    print(f"  output: {result}")
    print("  notice: standalone ToolNode does not apply the Command; it returns it.")
    print()


def experiment_2_command_update_in_graph() -> None:
    print("=== 2. compiled graph applies Command.update ===")

    def model_node(state: AgentState) -> dict:
        return {"messages": [make_ai_message("command_note", "graph-call", "graph")]}

    def after_node(state: AgentState) -> dict:
        return {"route": "after", "audit": ["after-node"]}

    graph = StateGraph(AgentState)
    graph.add_node("model", model_node)
    graph.add_node("tools", ToolNode([command_note]))
    graph.add_node("after", after_node)
    graph.add_edge(START, "model")
    graph.add_edge("model", "tools")
    graph.add_edge("tools", "after")
    graph.add_edge("after", END)
    app = graph.compile()

    result = app.invoke({"messages": [], "audit": [], "route": ""})

    print("  messages:")
    print_messages(result["messages"])
    print(f"  audit: {result['audit']}")
    print(f"  route: {result['route']!r}")
    print("  notice: Command.update merged messages/audit before the static tools -> after edge.")
    print()


def experiment_3_wrapper_command_goto() -> None:
    print("=== 3. wrap_tool_call returns Command(goto='after') ===")

    def wrapper(request: ToolCallRequest, execute: Any) -> Command:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="wrapper-skipped-tool",
                        tool_call_id=request.tool_call["id"],
                    )
                ],
                "audit": ["wrapper-command"],
            },
            goto="after",
        )

    def model_node(state: AgentState) -> dict:
        return {"messages": [make_ai_message("plain_note", "wrapper-call", "wrapped")]}

    def after_node(state: AgentState) -> dict:
        return {"route": "after", "audit": ["after-node"]}

    graph = StateGraph(AgentState)
    graph.add_node("model", model_node)
    graph.add_node("tools", ToolNode([plain_note], wrap_tool_call=wrapper))
    graph.add_node("after", after_node)
    graph.add_edge(START, "model")
    graph.add_edge("model", "tools")
    graph.add_edge("after", END)
    app = graph.compile()

    result = app.invoke({"messages": [], "audit": [], "route": ""})

    print("  messages:")
    print_messages(result["messages"])
    print(f"  audit: {result['audit']}")
    print(f"  route: {result['route']!r}")
    print("  notice: no static tools -> after edge is needed; Command.goto routes to after.")
    print()


def experiment_4_invalid_command_requires_tool_message() -> None:
    print("=== 4. current-graph Command requires matching ToolMessage ===")
    node = ToolNode([invalid_command])
    try:
        node.invoke(
            {
                "messages": [make_ai_message("invalid_command", "bad-call", "missing-tool-message")],
                "audit": [],
                "route": "",
            },
            config=TOOLNODE_CONFIG,
        )
    except ValueError as exc:
        first_line = str(exc).splitlines()[0]
        print(f"  ValueError: {first_line}")
    print("  notice: ToolNode validates that every tool call has a matching ToolMessage.")
    print()


def main() -> None:
    experiment_1_standalone_command_output()
    experiment_2_command_update_in_graph()
    experiment_3_wrapper_command_goto()
    experiment_4_invalid_command_requires_tool_message()


if __name__ == "__main__":
    main()
