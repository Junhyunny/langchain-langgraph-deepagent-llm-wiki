"""
08_toolnode_direct.py — ToolNode 직접 실행과 wrap_tool_call 관찰

이 파일이 보여주는 것:
  1. ToolNode의 세 가지 입력 형태: state dict, message list, direct tool_calls
  2. tools_condition() 라우팅: tool_calls 있으면 "tools", 없으면 "__end__"
  3. wrap_tool_call로 도구 실행 직전 request를 수정하는 방법
  4. LangChain create_agent가 ToolNode(wrap_tool_call=...)를 내부에서 쓰는 이유

실행:
  python examples/langgraph_core/08_toolnode_direct.py
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.tools import tool
from langgraph._internal._constants import CONF, CONFIG_KEY_RUNTIME
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime


TOOLNODE_CONFIG = {CONF: {CONFIG_KEY_RUNTIME: Runtime()}}


@tool
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def print_tool_messages(value: Any) -> None:
    if isinstance(value, dict):
        messages = value["messages"]
        print("  output shape: dict {'messages': [...]}")
    else:
        messages = value
        print("  output shape: list [...]")

    for msg in messages:
        assert isinstance(msg, ToolMessage)
        print(
            f"    ToolMessage name={msg.name!r}, "
            f"tool_call_id={msg.tool_call_id!r}, content={msg.content!r}"
        )


def make_ai_message(call_id: str, a: int, b: int) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[ToolCall(name="add_numbers", args={"a": a, "b": b}, id=call_id)],
    )


def experiment_1_input_shapes() -> None:
    print("=== 1. ToolNode input/output shapes ===")
    node = ToolNode([add_numbers])

    state_result = node.invoke(
        {"messages": [make_ai_message("state-call", 2, 3)]},
        config=TOOLNODE_CONFIG,
    )
    print("[state dict input]")
    print_tool_messages(state_result)
    print()

    list_result = node.invoke(
        [make_ai_message("list-call", 4, 5)],
        config=TOOLNODE_CONFIG,
    )
    print("[message list input]")
    print_tool_messages(list_result)
    print()

    direct_result = node.invoke(
        [
            {
                "type": "tool_call",
                "name": "add_numbers",
                "args": {"a": 6, "b": 7},
                "id": "direct-call",
            }
        ],
        config=TOOLNODE_CONFIG,
    )
    print("[direct tool_calls input]")
    print_tool_messages(direct_result)
    print()


def experiment_2_tools_condition() -> None:
    print("=== 2. tools_condition routing ===")
    with_tool = {"messages": [make_ai_message("route-call", 1, 1)]}
    without_tool = {"messages": [AIMessage(content="No tools needed.")]}

    print(f"  with tool_calls: {tools_condition(with_tool)!r}")
    print(f"  without tool_calls: {tools_condition(without_tool)!r}")
    print()


def experiment_3_wrap_tool_call() -> None:
    print("=== 3. wrap_tool_call modifies request before execution ===")
    events: list[str] = []

    def wrapper(
        request: ToolCallRequest,
        execute: Any,
    ) -> ToolMessage:
        original = request.tool_call["args"]
        events.append(f"before: {original}")
        modified_call = {
            **request.tool_call,
            "args": {
                **request.tool_call["args"],
                "b": request.tool_call["args"]["b"] * 10,
            },
        }
        result = execute(request.override(tool_call=modified_call))
        events.append(f"after: content={result.content!r}")
        return result

    node = ToolNode([add_numbers], wrap_tool_call=wrapper)
    result = node.invoke(
        {"messages": [make_ai_message("wrapped-call", 2, 3)]},
        config=TOOLNODE_CONFIG,
    )

    print_tool_messages(result)
    print("  wrapper events:")
    for event in events:
        print(f"    {event}")
    print()
    print("What to notice:")
    print("  - wrapper는 ToolCallRequest를 직접 mutate하지 않고 override()로 새 request를 만듦")
    print("  - add_numbers(2, 3)이 아니라 add_numbers(2, 30)이 실행되어 32가 반환됨")
    print("  - LangChain create_agent는 AgentMiddleware.wrap_tool_call을 이 ToolNode wrapper로 연결")


def main() -> None:
    experiment_1_input_shapes()
    experiment_2_tools_condition()
    experiment_3_wrap_tool_call()


if __name__ == "__main__":
    main()
