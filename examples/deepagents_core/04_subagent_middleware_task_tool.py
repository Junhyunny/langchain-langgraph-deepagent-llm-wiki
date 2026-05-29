"""
04_subagent_middleware_task_tool.py — Deep Agents SubAgentMiddleware task flow

This example shows:
  1. SubAgentMiddleware adds a `task` tool to a LangChain agent
  2. the parent model calls `task(description, subagent_type)`
  3. the compiled subagent receives an isolated message list
  4. selected subagent state updates are merged back into the parent state

Run:
  python examples/deepagents_core/04_subagent_middleware_task_tool.py
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing_extensions import NotRequired

from deepagents.backends import StateBackend
from deepagents.middleware import SubAgentMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from pydantic import Field


class MainState(AgentState):
    """Parent agent state with one forwarded key and one returned key."""

    project_id: NotRequired[str]
    summary: NotRequired[str]
    todos: NotRequired[list[str]]


class ToolCallingFakeModel(FakeMessagesListChatModel):
    """Fake model that records tool binding done by create_agent()."""

    bound_tool_names: list[str] = Field(default_factory=list)

    def bind_tools(
        self,
        tools: Sequence[BaseTool | dict[str, Any] | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "ToolCallingFakeModel":
        self.bound_tool_names = [
            getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else str(t))
            for t in tools
        ]
        return self


def print_messages(messages: list[BaseMessage]) -> None:
    for i, message in enumerate(messages, start=1):
        tool_calls = getattr(message, "tool_calls", None)
        print(f"  {i}. {type(message).__name__}: content={message.content!r}")
        if tool_calls:
            print(f"     tool_calls={tool_calls}")


def main() -> None:
    observed_child: dict[str, Any] = {}

    def compiled_researcher(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        observed_child["state_keys"] = sorted(state)
        observed_child["message_contents"] = [message.content for message in state["messages"]]
        observed_child["ls_agent_type"] = config.get("configurable", {}).get("ls_agent_type")
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Subagent report: project="
                        f"{state.get('project_id')}, task={state['messages'][0].content}"
                    )
                )
            ],
            "summary": "researcher completed one isolated task",
            "todos": ["child-only todo should not merge into parent"],
        }

    subagent = {
        "name": "researcher",
        "description": "Research one isolated topic and return a concise report.",
        "runnable": RunnableLambda(compiled_researcher),
    }
    middleware = SubAgentMiddleware(
        backend=StateBackend(),
        subagents=[subagent],
        system_prompt="Use `task` for isolated research work.",
    )

    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "task",
                        "args": {
                            "description": "Explain why checkpointing matters in LangGraph.",
                            "subagent_type": "researcher",
                        },
                        "id": "call-task-1",
                    }
                ],
            ),
            AIMessage(content="Final: I used the researcher report."),
        ]
    )

    agent = create_agent(
        model=model,
        tools=[],
        middleware=[middleware],
        state_schema=MainState,
    )

    result = agent.invoke(
        {
            "messages": [{"role": "user", "content": "Research LangGraph checkpointing."}],
            "project_id": "llm-wiki",
            "todos": ["parent todo should stay private from the subagent"],
        }
    )

    print("=== Deep Agents SubAgentMiddleware task tool ===")
    print("bound tools:")
    print(f"  {model.bound_tool_names}")
    print()
    print("parent messages:")
    print_messages(result["messages"])
    print()
    print("parent state updates:")
    print(f"  summary: {result.get('summary')!r}")
    print(f"  todos: {result.get('todos')!r}")
    print()
    print("subagent observed:")
    print(f"  state keys: {observed_child['state_keys']}")
    print(f"  messages: {observed_child['message_contents']}")
    print(f"  ls_agent_type: {observed_child['ls_agent_type']!r}")
    print()
    print("What to notice:")
    print("  - SubAgentMiddleware exposes a normal `task` tool to the parent model")
    print("  - the child receives only the task description as its message history")
    print("  - parent `project_id` is forwarded, but excluded keys like `todos` are not")
    print("  - child `summary` merges into parent state; child `todos` does not")


if __name__ == "__main__":
    main()
