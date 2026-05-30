"""
05_subagent_parallel_tasks.py — Deep Agents multiple task tool calls

This example shows:
  1. one parent AIMessage can request multiple `task` tool calls
  2. ToolNode runs those tool calls concurrently
  3. parent state merge order follows tool call/output order, not finish time
  4. repeated updates to the same state key need a reducer

Run:
  python examples/deepagents_core/05_subagent_parallel_tasks.py
"""

from __future__ import annotations

from collections.abc import Sequence
from operator import add
from threading import get_ident
from time import monotonic, sleep
from typing import Annotated, Any
from typing_extensions import NotRequired

from deepagents.backends import StateBackend
from deepagents.middleware import SubAgentMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from pydantic import Field


class MainState(AgentState):
    """Parent state with a reducer for many subagent report updates."""

    reports: NotRequired[Annotated[list[str], add]]
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
            ids = [f"{call['id']}:{call['args']['description']}" for call in tool_calls]
            print(f"     tool_calls={ids}")
        if isinstance(message, ToolMessage):
            print(f"     tool_call_id={message.tool_call_id}")


def main() -> None:
    events: list[tuple[float, str, str, int]] = []
    started_at = monotonic()

    def record(label: str, phase: str) -> None:
        events.append((monotonic() - started_at, label, phase, get_ident()))

    def compiled_researcher(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        description = state["messages"][0].content
        label = "slow" if "slow" in description else "fast"
        delay = 0.25 if label == "slow" else 0.05

        record(label, "start")
        sleep(delay)
        record(label, "end")

        return {
            "messages": [AIMessage(content=f"{label} report finished after {delay:.2f}s")],
            "reports": [f"{label}-report"],
            "todos": [f"{label}-child-todo should not merge"],
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
                            "description": "slow: research LangGraph checkpointing",
                            "subagent_type": "researcher",
                        },
                        "id": "call-slow",
                    },
                    {
                        "name": "task",
                        "args": {
                            "description": "fast: research Deep Agents context isolation",
                            "subagent_type": "researcher",
                        },
                        "id": "call-fast",
                    },
                ],
            ),
            AIMessage(content="Final: I used both researcher reports."),
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
            "messages": [{"role": "user", "content": "Compare two agent runtime details."}],
            "reports": [],
            "todos": ["parent todo stays parent-owned"],
        }
    )

    print("=== Deep Agents parallel task tool calls ===")
    print("bound tools:")
    print(f"  {model.bound_tool_names}")
    print()
    print("subagent timeline:")
    for elapsed, label, phase, thread_id in sorted(events):
        print(f"  {elapsed:0.3f}s {label:<4} {phase:<5} thread={thread_id}")
    print()
    print("parent messages:")
    print_messages(result["messages"])
    print()
    print("parent state:")
    print(f"  reports: {result.get('reports')!r}")
    print(f"  todos: {result.get('todos')!r}")
    print()
    print("What to notice:")
    print("  - both tasks start before the slow task finishes, so calls ran concurrently")
    print("  - fast finishes first, but ToolMessages follow the original tool call order")
    print("  - reports use a reducer, so both child updates merge into parent state")
    print("  - child todos are excluded and do not overwrite parent todos")


if __name__ == "__main__":
    main()
