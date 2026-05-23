"""create_agent: full agent loop without an LLM API key.

Shows:
- create_agent (langchain.agents) wires a model + tools into a CompiledStateGraph
- FakeToolChatModel simulates: tool call -> tool execution -> final answer
- messages list in state accumulates every turn (add_messages reducer)
- compile(checkpointer=...) + thread_id enables multi-turn memory

Fake LLM script for this example:
  Turn 1 user input -> model returns tool_call(add, a=3, b=4)
  Tool executes        -> ToolMessage(content="7", ...)
  Model sees result    -> returns final AIMessage("3 + 4 = 7")

Note: FakeToolChatModel overrides bind_tools() as a no-op because the fake
      model ignores tool schemas — it just returns the pre-scripted responses.
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.memory import InMemorySaver


class FakeToolChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel that accepts bind_tools() without error."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeToolChatModel":
        return self  # no-op: pre-scripted responses ignore tool schemas


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def build_agent(responses: list, checkpointer=None):
    model = FakeToolChatModel(responses=responses)
    return create_agent(model=model, tools=[add], checkpointer=checkpointer)


def main() -> None:
    # --- 1. Basic agent invocation ---
    agent = build_agent(responses=[
        AIMessage(
            content="",
            tool_calls=[ToolCall(name="add", args={"a": 3, "b": 4}, id="call_1")],
        ),
        AIMessage(content="3 + 4 = 7"),
    ])
    print("=== Basic invocation ===")
    result = agent.invoke({"messages": [HumanMessage(content="What is 3 + 4?")]})
    print(f"Total messages in state: {len(result['messages'])}")
    for msg in result["messages"]:
        label = type(msg).__name__
        content = msg.content or f"[tool_calls: {msg.tool_calls}]"
        print(f"  {label}: {content}")

    # --- 2. What create_agent actually returns ---
    print("\n=== Graph type ===")
    print("type:", type(agent).__name__)  # CompiledStateGraph

    # --- 3. Multi-turn with checkpointing ---
    print("\n=== Multi-turn with memory ===")
    agent2 = build_agent(
        responses=[
            AIMessage(
                content="",
                tool_calls=[ToolCall(name="add", args={"a": 1, "b": 2}, id="c1")],
            ),
            AIMessage(content="1 + 2 = 3"),
            AIMessage(content="Yes, I remember: 1 + 2 = 3"),
        ],
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "demo"}}

    r1 = agent2.invoke({"messages": [HumanMessage("What is 1 + 2?")]}, config=config)
    print("Turn 1 final:", r1["messages"][-1].content)

    r2 = agent2.invoke({"messages": [HumanMessage("Do you remember?")]}, config=config)
    print("Turn 2 final:", r2["messages"][-1].content)
    print("Accumulated messages:", len(r2["messages"]))


if __name__ == "__main__":
    main()
